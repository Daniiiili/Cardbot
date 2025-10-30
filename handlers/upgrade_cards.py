from telebot import types
from loader import bot
import os
from database import players_data
import config

WAITING_FOR_UPGRADE = set()


@bot.message_handler(func=lambda m: m.text.lower() in ["прокачка карт", "⚡ прокачка карт"])
def upgrade_menu(message):
    """Открывает меню прокачки карт"""
    user_id = message.from_user.id
    data = players_data.get(user_id)

    if not data or not data.get("nick"):
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйся и получи стартовые карты!")
        return

    # Проверяем, есть ли вообще дубли
    has_duplicates = any(count >= 2 for count in data.get("cards", {}).values())
    if not has_duplicates:
        bot.send_message(message.chat.id, "⚠️ У тебя пока нет дублей для прокачки карт.")
        return

    bot.send_message(
        message.chat.id,
        "✨ Введите имя персонажа, которого хотите прокачать до 2 уровня.\n"
        "📌 Пример: Наруто\n"
        "⚠️ Требуется: 2 одинаковые карты 1 уровня и 70 💎 кристаллов",
        parse_mode="Markdown"
    )
    WAITING_FOR_UPGRADE.add(user_id)


@bot.message_handler(func=lambda message: message.from_user.id in WAITING_FOR_UPGRADE)
def process_upgrade(message):
    """Обрабатывает введённое имя карты для прокачки"""
    user_id = message.from_user.id
    data = players_data.get(user_id)
    card_name = message.text.strip()

    # Папки с картами
    base_folder = config.CARDS_FOLDER
    upgrade_folder = "cards_2"

    if not data:
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйся.")
        WAITING_FOR_UPGRADE.discard(user_id)
        return

    # Проверяем наличие карты 1 уровня
    card_filename = f"{card_name}.jpg"
    if card_filename not in data["cards"] or data["cards"][card_filename] < 2:
        bot.send_message(message.chat.id, f"❌ Недостаточно дублей карты {card_name}. Нужно 2 одинаковые.")
        WAITING_FOR_UPGRADE.discard(user_id)
        return

    # Проверяем кристаллы
    if data["crystals"] < 70:
        bot.send_message(message.chat.id, "💎 Недостаточно кристаллов (нужно 70).")
        WAITING_FOR_UPGRADE.discard(user_id)
        return

    # Проверяем, есть ли версия карты 2 уровня
    upgraded_filename = f"{card_name}_2.jpg"
    upgraded_path = os.path.join(upgrade_folder, upgraded_filename)
    if not os.path.exists(upgraded_path):
        bot.send_message(message.chat.id, f"⚠️ Карта {card_name} не имеет версии 2 уровня.")
        WAITING_FOR_UPGRADE.discard(user_id)
        return

    # Удаляем две карты 1 уровня
    data["cards"][card_filename] -= 2
    if data["cards"][card_filename] <= 0:
        del data["cards"][card_filename]

    # Списываем кристаллы
    data["crystals"] -= 70

    # Добавляем новую карту 2 уровня
    data["cards"][upgraded_filename] = data["cards"].get(upgraded_filename, 0) + 1

    with open(upgraded_path, "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption=f"⚡ {card_name} успешно прокачан до 2 уровня!")

    WAITING_FOR_UPGRADE.discard(user_id)
