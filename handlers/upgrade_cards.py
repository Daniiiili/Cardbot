from telebot import types
from loader import bot
import os
from database import players_data, mark_dirty
import config
from handlers.card_names import pretty_card_name

WAITING_FOR_UPGRADE = set()

ALLOWED_EXTS = (".png", ".jpg", ".jpeg", ".webp")

def find_owned_card_filename(inv: dict, typed_name: str) -> str | None:
    """
    typed_name: "naruto" или "akatsuki_kakuzu" или "kakuzu"
    ищем в инвентаре ключ (реальное имя файла), сравнивая по базе без расширения
    """
    wanted = typed_name.strip().lower().replace(" ", "_")
    for file_key in inv.keys():
        base, ext = os.path.splitext(file_key)
        if ext.lower() not in ALLOWED_EXTS:
            continue
        if base.lower() == wanted:
            return file_key
    return None

def find_file_in_folder_by_base(folder: str, base_no_ext: str) -> str | None:
    """
    folder: "cards_2" / "card_akatsuki_2" / ...
    base_no_ext: "naruto_2", "akatsuki_kakuzu_2"
    вернёт полный путь к файлу с любым разрешённым расширением
    """
    if not os.path.isdir(folder):
        return None
    wanted = base_no_ext.lower()
    for f in os.listdir(folder):
        b, ext = os.path.splitext(f)
        if b.lower() == wanted and ext.lower() in ALLOWED_EXTS:
            return os.path.join(folder, f)
    return None

def get_card_type_by_base(base_no_ext: str):
    if base_no_ext.startswith("akatsuki_"):
        return "akatsuki"
    if base_no_ext.startswith("biju_"):
        return "biju"
    return "normal"

@bot.message_handler(func=lambda m: m.text.lower() in ["прокачка карт", "⚡ прокачка карт"])
def upgrade_menu(message):
    """Открывает меню прокачки карт"""
    user_id = message.from_user.id
    data = players_data.get(user_id)

    if not data or not data.get("nick"):
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйся и получи стартовые карты!")
        return

    # Проверяем, есть ли вообще дубли

    bot.send_message(
        message.chat.id,
        "⚡ Прокачка до 2 уровня\n\n"
        "🟩 Обычные: 2 копии + 70💎\n"
        "🟥 Акацуки: 100💎 + 50🎯\n"
        "🟨 Биджу: 2 копии + 70💎 + 30🎯\n\n"
        "✍️ Введи имя карты (пример: Наруто / akatsuki_kakuzu / biju_kurama)",
    )
    WAITING_FOR_UPGRADE.add(user_id)


@bot.message_handler(func=lambda message: message.from_user.id in WAITING_FOR_UPGRADE)
def process_upgrade(message):
    """Обрабатывает введённое имя карты для прокачки"""
    user_id = message.from_user.id
    data = players_data.get(user_id)
    card_name = message.text.strip()
    inv = data.get("cards", {})

    # ищем реальный файл в инвентаре по базе (без расширения)
    card_filename = find_owned_card_filename(inv, card_name)
    if not card_filename:
        bot.send_message(message.chat.id, "❌ Такой карты нет в твоём инвентаре.")
        WAITING_FOR_UPGRADE.discard(user_id)
        return

    base_no_ext, _ext = os.path.splitext(card_filename)
    card_type = get_card_type_by_base(base_no_ext)

    # Папки с картами
    base_folder = config.CARDS_FOLDER
    upgrade_folder = "cards_2"

    if not data:
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйся.")
        WAITING_FOR_UPGRADE.discard(user_id)
        return

    # 🟥 АКАЦУКИ: 100💎 + 50🎯 exp (без повторки)
    if card_type == "akatsuki":
        if data.get("crystals", 0) < 100:
            bot.send_message(message.chat.id, "❌ Для прокачки Акацуки нужно 100💎 кристаллов.")
            WAITING_FOR_UPGRADE.discard(user_id)
            return

        if data.get("exp", 0) < 50:
            bot.send_message(message.chat.id, "❌ Для прокачки Акацуки нужно 50🎯 турнирного опыта.")
            WAITING_FOR_UPGRADE.discard(user_id)
            return

        upgrade_folder = "card_akatsuki_2"
        upgraded_base = base_no_ext + "_2"
        upgraded_path = find_file_in_folder_by_base(upgrade_folder, upgraded_base)
        if not upgraded_path:
            bot.send_message(message.chat.id, f"⚠️ Карта {card_name} не имеет версии 2 уровня.")
            WAITING_FOR_UPGRADE.discard(user_id)
            return

        upgraded_filename = os.path.basename(upgraded_path)

        data["crystals"] -= 100
        data["exp"] -= 50

        data.setdefault("cards", {})
        data["cards"][upgraded_filename] = data["cards"].get(upgraded_filename, 0) + 1

        mark_dirty()

        with open(upgraded_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f"🟥 {card_name} прокачан до 2 уровня!")

        WAITING_FOR_UPGRADE.discard(user_id)
        return
    # 🟨 БИДЖУ: 2 копии + 70💎 + 30🎯 exp
    if card_type == "biju":
        if data.get("cards", {}).get(card_filename, 0) < 2:
            bot.send_message(message.chat.id, f"❌ Нужна повторная карта {card_name} (2 копии).")
            WAITING_FOR_UPGRADE.discard(user_id)
            return

        if data.get("crystals", 0) < 70:
            bot.send_message(message.chat.id, "❌ Для прокачки Биджу нужно 70💎 кристаллов.")
            WAITING_FOR_UPGRADE.discard(user_id)
            return

        if data.get("exp", 0) < 30:
            bot.send_message(message.chat.id, "❌ Для прокачки Биджу нужно 30🎯 турнирного опыта.")
            WAITING_FOR_UPGRADE.discard(user_id)
            return

        upgrade_folder = "card_biju_2"
        upgraded_base = base_no_ext + "_2"
        upgraded_path = find_file_in_folder_by_base(upgrade_folder, upgraded_base)
        if not upgraded_path:
            bot.send_message(message.chat.id, f"⚠️ Карта {card_name} не имеет версии 2 уровня.")
            WAITING_FOR_UPGRADE.discard(user_id)
            return

        upgraded_filename = os.path.basename(upgraded_path)
        # списываем 2 копии
        data["cards"][card_filename] -= 2
        if data["cards"][card_filename] <= 0:
            del data["cards"][card_filename]

        data["crystals"] -= 70
        data["exp"] -= 30

        data.setdefault("cards", {})
        data["cards"][upgraded_filename] = data["cards"].get(upgraded_filename, 0) + 1

        mark_dirty()

        with open(upgraded_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f"🟨 {card_name} прокачан до 2 уровня!")

        WAITING_FOR_UPGRADE.discard(user_id)
        return

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
    upgrade_folder = "cards_2"
    upgraded_base = base_no_ext + "_2"  # например naruto_2 или akatsuki_kakuzu_2
    upgraded_path = find_file_in_folder_by_base(upgrade_folder, upgraded_base)
    if not upgraded_path:
        bot.send_message(message.chat.id, f"⚠️ Карта {card_name} не имеет версии 2 уровня.")
        WAITING_FOR_UPGRADE.discard(user_id)
        return

    # имя файла берём из найденного пути (чтобы добавить в инвентарь)
    upgraded_filename = os.path.basename(upgraded_path)

    # Удаляем две карты 1 уровня
    data["cards"][card_filename] -= 2
    if data["cards"][card_filename] <= 0:
        del data["cards"][card_filename]

    # Списываем кристаллы
    data["crystals"] -= 70

    # Добавляем новую карту 2 уровня
    data["cards"][upgraded_filename] = data["cards"].get(upgraded_filename, 0) + 1
    mark_dirty()
    with open(upgraded_path, "rb") as photo:
        pretty = pretty_card_name(upgraded_filename)
        bot.send_photo(
            message.chat.id,
            photo,
            caption=f"⚡ {pretty} прокачан до 2 уровня!"
        )

    WAITING_FOR_UPGRADE.discard(user_id)
