from telebot import types
from loader import bot
import os
import config
import random
from database import players_data, mark_dirty
from config import ARTIFACT_PRICE, ARTIFACTS_FOLDER
from handlers.card_names import pretty_card_name



# 🏆 Победа
@bot.message_handler(func=lambda m: m.text.lower() in ["победа", "🏆 победа"])
def handle_victory(message):
    user_id = message.from_user.id
    data = players_data.get(user_id)
    if not data or not data["nick"]:
        bot.reply_to(message, "⚠️ Сначала получи стартовые карты и зарегистрируйся!")
        return
    if data["battles"] >= config.BATTLE_LIMIT:
        bot.reply_to(message, "⚠️ Ты достиг лимита боёв на сегодня.")
        return
    data["yen"] += 10
    data["crystals"] += 2
    data["wins"] += 1
    data["battles"] += 1
    bot.reply_to(message, f"Поздравляю, {data['nick']}!\n+10 йен 💴\n+2 кристалла 💎\n📊 Осталось боёв: {config.BATTLE_LIMIT - data['battles']}")
    mark_dirty()

# 💀 Поражение
@bot.message_handler(func=lambda m: m.text.lower() in ["поражение", "💀 поражение"])
def handle_defeat(message):
    user_id = message.from_user.id
    data = players_data.get(user_id)
    if not data or not data["nick"]:
        bot.reply_to(message, "⚠️ Сначала зарегистрируйся!")
        return
    if data["battles"] >= config.BATTLE_LIMIT:
        bot.reply_to(message, "⚠️ Ты достиг лимита боёв на сегодня.")
        return
    data["yen"] += 5
    data["crystals"] += 1
    data["losses"] += 1
    data["battles"] += 1
    bot.reply_to(message, f"{data['nick']}, не отчаивайся!\n+5 йен 💴\n+1 кристалл 💎\n📊 Осталось боёв: {config.BATTLE_LIMIT - data['battles']}")
    mark_dirty()

# 🃏 Инвентарь
@bot.message_handler(func=lambda m: m.text.lower() in ["инвентарь", "🃏 инвентарь"])
def show_inventory(message):
    user_id = message.from_user.id
    data = players_data.get(user_id)

    if not data:
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйся.")
        return

    # 🃏 Обычные карты
    if data.get("cards"):
        cards = list(data["cards"].items())
        max_per_batch = 10
        for i in range(0, len(cards), max_per_batch):
            batch = cards[i:i+max_per_batch]
            media_group = []
            for card_file, count in batch:
                folder = card_folder_by_filename(card_file)
                file_path = os.path.join(folder, card_file)
                if not os.path.exists(file_path):
                    continue
                media_group.append(types.InputMediaPhoto(open(file_path, 'rb')))
            bot.send_media_group(message.chat.id, media_group)

        caption_lines = ["Твои карты:"]
        for card_file, count in cards:
            caption_lines.append(f"{pretty_card_name(card_file)} x{count}")
        bot.send_message(message.chat.id, "\n".join(caption_lines))

    # 🪄 Артефакты
    artifacts = data.get("artifacts", {})
    if artifacts:
        artifact_list = list(artifacts.items())
        max_per_batch = 10
        for i in range(0, len(artifact_list), max_per_batch):
            batch = artifact_list[i:i+max_per_batch]
            media_group = []
            for artifact_file, count in batch:
                file_path = os.path.join(ARTIFACTS_FOLDER, artifact_file)
                media_group.append(types.InputMediaPhoto(open(file_path, 'rb')))
            bot.send_media_group(message.chat.id, media_group)

        caption_lines = ["Артефакты:"]
        for artifact_file, count in artifact_list:
            name = os.path.splitext(artifact_file)[0]
            caption_lines.append(f"{name} x{count}")
        bot.send_message(message.chat.id, "\n".join(caption_lines))
    else:
        bot.send_message(message.chat.id, "У тебя пока нет артефактов.")
def card_folder_by_filename(card_file: str) -> str:
    name = os.path.splitext(card_file)[0].lower()  # base
    # 2 уровень определяется по _2 в конце базы
    is_lvl2 = name.endswith("_2")

    if name.startswith("akatsuki_"):
        return "card_akatsuki_2" if is_lvl2 else "card_akatsuki"
    if name.startswith("biju_"):
        return "card_biju_2" if is_lvl2 else "card_biju"

    return "cards_2" if is_lvl2 else config.CARDS_FOLDER


# 💬 Беседа
@bot.message_handler(func=lambda m: m.text.lower() in ["беседа", "💬 беседа"])
def chat_link(message):
    bot.send_message(
        message.chat.id,
        "💬 Наша беседа тут:",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Перейти в чат", url=config.CHAT_LINK)
        )
    )



# 🛍 Магазин
@bot.message_handler(func=lambda m: m.text.lower() in ["магазин", "🛍 магазин"])
def shop(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Купить пак"), types.KeyboardButton("Купить артефакт"))
    markup.add(types.KeyboardButton("Назад"))
    bot.send_message(message.chat.id, "Магазин:\nПаки — 100 йен, артефакты — 300 йен.", reply_markup=markup)


# 🎁 Покупка артефакта
@bot.message_handler(func=lambda m: m.text.lower() in ["купить артефакт", "🪄 купить артефакт"])
def buy_artifact(message):
    user_id = message.from_user.id
    data = players_data.get(user_id)

    if not data or not data["nick"]:
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйся.")
        return
    if data["yen"] < ARTIFACT_PRICE:
        bot.send_message(message.chat.id, f"❌ Недостаточно йен (нужно {ARTIFACT_PRICE}).")
        return

    all_artifacts = os.listdir(ARTIFACTS_FOLDER)
    artifact = random.choice(all_artifacts)
    data["yen"] -= ARTIFACT_PRICE
    data["artifacts"][artifact] = data["artifacts"].get(artifact, 0) + 1

    artifact_name = os.path.splitext(artifact)[0]
    file_path = os.path.join(ARTIFACTS_FOLDER, artifact)
    with open(file_path, "rb") as art:
        bot.send_photo(message.chat.id, art, caption=f"✨ Ты получил артефакт: {artifact_name}")
    mark_dirty()

# 🎁 Покупка пака
@bot.message_handler(func=lambda m: m.text.lower() in ["купить пак", "🎁 купить пак"])
def buy_pack(message):
    user_id = message.from_user.id
    data = players_data.get(user_id)

    if not data or not data["nick"]:
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйся!")
        return
    if data["yen"] < config.PACK_PRICE:
        bot.send_message(message.chat.id, f"❌ Нужно {config.PACK_PRICE} йен.")
        return

    data["yen"] -= config.PACK_PRICE
    all_cards = os.listdir(config.CARDS_FOLDER)
    new_card = random.choice(all_cards)
    data["cards"][new_card] = data["cards"].get(new_card, 0) + 1

    pretty = pretty_card_name(new_card)

    with open(os.path.join(config.CARDS_FOLDER, new_card), "rb") as card:
        bot.send_photo(
            message.chat.id,
            card,
            caption=f"🎉 Новая карта: {pretty} (x{data['cards'][new_card]})"
        )

