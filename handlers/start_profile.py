from telebot import types
from loader import bot
import os
import random
import config
from database import players_data, used_nicks, waiting_for_nick

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🃏 ННачальные карты"))
    bot.send_message(
        message.chat.id,
        "👋 Приветствую в КБ (Карточных Боях) по Наруто!\n\n"
        "Нажми кнопку ниже, чтобы получить свои стартовые карты:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text.lower() in ["начальные карты", "🃏 начальные карты"])
def send_random_cards(message):
    user_id = message.from_user.id
    if user_id in players_data:
        bot.send_message(message.chat.id, "⚠️ Ты уже получил начальные карты.")
        return

    bot.send_message(message.chat.id, "✨ Вот твои начальные карты:")
    all_cards = os.listdir(config.CARDS_FOLDER)
    random_cards = random.sample(all_cards, 3)
    media_group = [types.InputMediaPhoto(open(os.path.join(config.CARDS_FOLDER, f), 'rb')) for f in random_cards]
    bot.send_media_group(message.chat.id, media_group)

    players_data[user_id] = {
        "nick": None,
        "yen": 0,
        "crystals": 0,
        "wins": 0,
        "losses": 0,
        "battles": 0,
        "exp": 0,
        "cards": {f: 1 for f in random_cards},
        "artifacts": {}
    }
    waiting_for_nick.add(user_id)
    bot.send_message(message.chat.id, "📝 Введите ваш уникальный ник:")


@bot.message_handler(func=lambda message: message.from_user.id in waiting_for_nick)
def set_nick(message):
    user_id = message.from_user.id
    nick = message.text.strip()

    if len(nick) > config.MAX_NICK_LENGTH:
        bot.send_message(message.chat.id, f"⚠️ Ник не может быть длиннее {config.MAX_NICK_LENGTH} символов.")
        return
    if nick in used_nicks:
        bot.send_message(message.chat.id, "❌ Такой ник уже занят.")
        return

    players_data[user_id]["nick"] = nick
    used_nicks.add(nick)
    waiting_for_nick.remove(user_id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Профиль"), types.KeyboardButton("Беседа"))
    markup.add(types.KeyboardButton("Донат"), types.KeyboardButton("Магазин"))
    bot.send_message(message.chat.id, f"✅ Отлично, ваш ник: {nick}", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.lower() in ["профиль", "🧍 профиль"])
def show_profile(message):
    user_id = message.from_user.id
    data = players_data.get(user_id)
    if not data or not data["nick"]:
        bot.send_message(message.chat.id, "⚠️ Ты ещё не зарегистрирован.")
        return

    profile_text = (
        f"🧍 Профиль: {data['nick']}\n"
        f"💴 Йены: {data['yen']}\n"
        f"💎 Кристаллы: {data['crystals']}\n"
        f"🏆 Победы: {data['wins']}\n"
        f"💀 Поражения: {data['losses']}\n"
        f"⚔️ Боев сегодня: {data['battles']}/{config.BATTLE_LIMIT}"
        f"🎯 Турнирный опыт: {data['exp']}"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Инвентарь"), types.KeyboardButton("Прокачка карт"))
    markup.add(types.KeyboardButton("Назад"))
    bot.send_message(message.chat.id, profile_text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.lower() in ["назад", "⬅ назад"])
def back_to_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Профиль"), types.KeyboardButton("Беседа"))
    markup.add(types.KeyboardButton("Донат"), types.KeyboardButton("Магазин"))
    bot.send_message(message.chat.id, "📲 Главное меню", reply_markup=markup)
