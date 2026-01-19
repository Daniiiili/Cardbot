from telebot import types
from loader import bot
import os
import config
import random
from database import players_data, mark_dirty
from config import ARTIFACT_PRICE, ARTIFACTS_FOLDER


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

# 🧍 Профиль
@bot.message_handler(func=lambda m: m.text.lower() in ["профиль", "🧍 профиль"])
def show_profile(message):
    user_id = message.from_user.id
    data = players_data.get(user_id)
    if not data or not data["nick"]:
        bot.send_message(message.chat.id, "⚠️ Ты ещё не зарегистрировал профиль.")
        return

    nick = data["nick"]
    text = (
        f"Профиль: {nick}\n"
        f"Йены: {data['yen']}\n"
        f"Кристаллы: {data['crystals']}\n"
        f"Победы: {data['wins']}\n"
        f"Поражения: {data['losses']}\n"
        f"Боев сегодня: {data['battles']}/{config.BATTLE_LIMIT}"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Инвентарь"), types.KeyboardButton("Прокачка карт"))
    markup.add(types.KeyboardButton("Назад"))
    bot.send_message(message.chat.id, text, reply_markup=markup)


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
                file_path = os.path.join("cards", card_file)
                media_group.append(types.InputMediaPhoto(open(file_path, 'rb')))
            bot.send_media_group(message.chat.id, media_group)

        caption_lines = ["Твои карты:"]
        for card_file, count in cards:
            name = os.path.splitext(card_file)[0].capitalize()
            caption_lines.append(f"{name} x{count}")
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


# 🪙 Донат
@bot.message_handler(func=lambda m: m.text.lower() in ["донат", "🪙 донат"])
def donate(message):
    bot.send_message(message.chat.id, "🪙 Донат — текст добавим позже.")


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

    card_name = os.path.splitext(new_card)[0]
    with open(os.path.join(config.CARDS_FOLDER, new_card), "rb") as card:
        bot.send_photo(message.chat.id, card, caption=f"🎉 Новая карта: {card_name} (x{data['cards'][new_card]})")
    mark_dirty()

# Назад
@bot.message_handler(func=lambda m: m.text.lower() in ["назад", "⬅ назад"])
def back_to_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Профиль"), types.KeyboardButton("Беседа"))
    markup.add(types.KeyboardButton("Донат"), types.KeyboardButton("Магазин"))
    bot.send_message(message.chat.id, "📲 Главное меню", reply_markup=markup)
