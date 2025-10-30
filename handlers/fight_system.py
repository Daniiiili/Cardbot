from loader import bot
from database import active_fights, players_data
from threading import Timer
import time
import random
from main import bot
from telebot import types

@bot.message_handler(commands=['флип'])
@bot.message_handler(func=lambda message: message.text.lower() == "флип")
def flip_coin(message):
    # 50/50 шанс
    result = random.choice(["Ходит первый игрок ⚔️", "Ходит второй игрок ⚔️"])

    # Добавим немного атмосферы
    bot.send_message(
        message.chat.id,
        "🪙 Бросаем монетку...",
    )

    # Через короткую паузу — результат
    import time
    time.sleep(1)
    bot.send_message(
        message.chat.id,
        f"🎲 {result}"
    )

# 🧑 Судья запускает бой
@bot.message_handler(func=lambda m: m.text.lower() == "судьябот")
def start_judge(message):
    chat_id = message.chat.id
    thread_id = message.message_thread_id
    user_id = message.from_user.id

    # Проверка — нет ли боя уже
    for f in active_fights.values():
        if f["chat_id"] == chat_id and f["thread_id"] == thread_id:
            bot.reply_to(message, "⚠️ В этой теме уже идёт бой.")
            return

    fight_id = f"fight_{chat_id}_{thread_id}_{int(time.time())}"
    active_fights[fight_id] = {
        "chat_id": chat_id,
        "thread_id": thread_id,
        "players": [],
        "score": [0, 0],
        "round": 1,
        "ready": set(),
        "state": "waiting_ready",
        "judge": user_id
    }

    bot.send_message(chat_id, "⚔️ Судейство запущено!\nГотовы? Два игрока напишите 'да' 👊", message_thread_id=thread_id)

# 📥 Готовность игроков
@bot.message_handler(func=lambda m: m.text.lower() == "да")
def player_ready(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    thread_id = message.message_thread_id

    for fight_id, fight in active_fights.items():
        if fight["chat_id"] != chat_id or fight["thread_id"] != thread_id:
            continue

        if user_id not in fight["players"] and len(fight["players"]) < 2:
            fight["players"].append(user_id)

        fight["ready"].add(user_id)

        if len(fight["ready"]) == 2 and len(fight["players"]) == 2:
            p1_id, p2_id = fight["players"]
            nick1 = players_data.get(p1_id, {}).get("nick", f"Игрок {p1_id}")
            nick2 = players_data.get(p2_id, {}).get("nick", f"Игрок {p2_id}")
            bot.send_message(chat_id, f"⚔️ Бой начался!\n👤 {nick1}\n👤 {nick2}", message_thread_id=thread_id)
            start_round(fight_id)
        return

# 🚀 Старт раунда
def start_round(fight_id):
    fight = active_fights[fight_id]
    fight["state"] = "preparing"
    bot.send_message(fight["chat_id"], f"⚔️ Раунд {fight['round']}: подготовка...", message_thread_id=fight["thread_id"])
    Timer(5, announce_throw, args=[fight_id]).start()

# 🃏 Начало кидания карт
def announce_throw(fight_id):
    fight = active_fights.get(fight_id)
    if not fight or fight["state"] != "preparing":
        return
    fight["state"] = "waiting_cards"
    bot.send_message(fight["chat_id"], "🃏 Кидаем карты!", message_thread_id=fight["thread_id"])

# 🧑‍⚖️ Судья указывает победителя
@bot.message_handler(func=lambda m: m.text.lower().startswith("победил"))
def judge_round(message):
    parts = message.text.lower().split()
    if len(parts) != 2 or parts[1] not in ["1", "2"]:
        return

    chat_id = message.chat.id
    thread_id = message.message_thread_id
    user_id = message.from_user.id

    for fight_id, fight in active_fights.items():
        if fight["chat_id"] != chat_id or fight["thread_id"] != thread_id:
            continue

        if user_id != fight["judge"]:
            bot.reply_to(message, "⛔ Только судья может указывать победителя.")
            return

        if fight["state"] != "waiting_cards":
            bot.reply_to(message, "⚠️ Сейчас нельзя указывать победителя.")
            return

        winner_index = int(parts[1]) - 1
        fight["score"][winner_index] += 1
        fight["round"] += 1

        p1_id, p2_id = fight["players"]
        nick1 = players_data.get(p1_id, {}).get("nick", f"Игрок {p1_id}")
        nick2 = players_data.get(p2_id, {}).get("nick", f"Игрок {p2_id}")

        bot.send_message(
            chat_id,
            f"✅ Победил игрок {winner_index+1} ({nick1 if winner_index == 0 else nick2})\n"
            f"📊 Счёт: {fight['score'][0]} – {fight['score'][1]}",
            message_thread_id=thread_id
        )

        if fight["score"][winner_index] == 2:
            winner_nick = nick1 if winner_index == 0 else nick2
            bot.send_message(chat_id, f"🏆 Победитель: {winner_nick}!", message_thread_id=thread_id)
            del active_fights[fight_id]
        else:
            start_round(fight_id)
        return

# ⛔ Стоп боя
@bot.message_handler(func=lambda m: m.text.lower() == "стоп")
def stop_fight(message):
    chat_id = message.chat.id
    thread_id = message.message_thread_id
    user_id = message.from_user.id

    for fight_id, fight in list(active_fights.items()):
        if fight["chat_id"] == chat_id and fight["thread_id"] == thread_id and user_id in fight["players"]:
            bot.send_message(chat_id, "⛔ Бой остановлен.", message_thread_id=thread_id)
            del active_fights[fight_id]
            return
