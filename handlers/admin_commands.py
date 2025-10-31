from loader import bot
from database import players_data
import os
from config import ADMIN_ID, CARDS_FOLDER, ARTIFACTS_FOLDER

CARDS2_FOLDER = "cards_2"  # вторая папка для прокачанных карт


# 🔍 Универсальный поиск файла (поддержка пробелов, нижних подчёркиваний и регистра)
def resolve_file(name_raw: str, folders: list[str], default_ext=".jpg") -> str | None:
    base = name_raw.strip()
    candidates = []

    # разные варианты имени файла
    if not os.path.splitext(base)[1]:
        candidates.append(base + default_ext)
    candidates.append(base)
    base_us = base.replace(" ", "_")
    if not os.path.splitext(base_us)[1]:
        candidates.append(base_us + default_ext)
    candidates.append(base_us)

    for folder in folders:
        if not os.path.isdir(folder):
            continue
        try:
            files = os.listdir(folder)
        except Exception:
            continue
        lower_map = {f.lower(): f for f in files}
        for cand in candidates:
            real = lower_map.get(cand.lower())
            if real:
                return os.path.join(folder, real)
    return None


# 🧩 Поиск игрока по нику
def find_user_by_nick(nick):
    for uid, data in players_data.items():
        if data.get("nick") == nick:
            return uid, data
    return None, None


# 🔒 Проверка на админа
def admin_only(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ У вас нет прав использовать эту команду.")
        return False
    return True


# 💴 ЙЕНЫ
@bot.message_handler(commands=['add_yen'])
def add_yen(message):
    if not admin_only(message): return
    try:
        _, nick, amount = message.text.split()
        amount = int(amount)
        _, data = find_user_by_nick(nick)
        if not data:
            bot.reply_to(message, "⚠️ Игрок не найден.")
            return
        data["yen"] += amount
        bot.reply_to(message, f"💴 {nick} теперь имеет {data['yen']} йен.")
    except:
        bot.reply_to(message, "❌ Формат: /add_yen ник число")

@bot.message_handler(commands=['remove_yen'])
def remove_yen(message):
    if not admin_only(message): return
    try:
        _, nick, amount = message.text.split()
        amount = int(amount)
        _, data = find_user_by_nick(nick)
        if not data:
            bot.reply_to(message, "⚠️ Игрок не найден.")
            return
        data["yen"] = max(0, data["yen"] - amount)
        bot.reply_to(message, f"💴 {nick} теперь имеет {data['yen']} йен.")
    except:
        bot.reply_to(message, "❌ Формат: /remove_yen ник число")


# 💎 КРИСТАЛЛЫ
@bot.message_handler(commands=['add_crystals'])
def add_crystals(message):
    if not admin_only(message): return
    try:
        _, nick, amount = message.text.split()
        amount = int(amount)
        _, data = find_user_by_nick(nick)
        if not data:
            bot.reply_to(message, "⚠️ Игрок не найден.")
            return
        data["crystals"] += amount
        bot.reply_to(message, f"💎 {nick} теперь имеет {data['crystals']} кристаллов.")
    except:
        bot.reply_to(message, "❌ Формат: /add_crystals ник число")

@bot.message_handler(commands=['remove_crystals'])
def remove_crystals(message):
    if not admin_only(message): return
    try:
        _, nick, amount = message.text.split()
        amount = int(amount)
        _, data = find_user_by_nick(nick)
        if not data:
            bot.reply_to(message, "⚠️ Игрок не найден.")
            return
        data["crystals"] = max(0, data["crystals"] - amount)
        bot.reply_to(message, f"💎 {nick} теперь имеет {data['crystals']} кристаллов.")
    except:
        bot.reply_to(message, "❌ Формат: /remove_crystals ник число")


# 🏆 ПОБЕДЫ / ПОРАЖЕНИЯ
@bot.message_handler(commands=['add_wins'])
def add_wins(message):
    if not admin_only(message): return
    try:
        _, nick, amount = message.text.split()
        amount = int(amount)
        _, data = find_user_by_nick(nick)
        if not data:
            bot.reply_to(message, "⚠️ Игрок не найден.")
            return
        data["wins"] += amount
        bot.reply_to(message, f"🏆 {nick} теперь имеет {data['wins']} побед.")
    except:
        bot.reply_to(message, "❌ Формат: /add_wins ник число")

@bot.message_handler(commands=['remove_wins'])
def remove_wins(message):
    if not admin_only(message): return
    try:
        _, nick, amount = message.text.split()
        amount = int(amount)
        _, data = find_user_by_nick(nick)
        if not data:
            bot.reply_to(message, "⚠️ Игрок не найден.")
            return
        data["wins"] = max(0, data["wins"] - amount)
        bot.reply_to(message, f"🏆 {nick} теперь имеет {data['wins']} побед.")
    except:
        bot.reply_to(message, "❌ Формат: /remove_wins ник число")

@bot.message_handler(commands=['add_losses'])
def add_losses(message):
    if not admin_only(message): return
    try:
        _, nick, amount = message.text.split()
        amount = int(amount)
        _, data = find_user_by_nick(nick)
        if not data:
            bot.reply_to(message, "⚠️ Игрок не найден.")
            return
        data["losses"] += amount
        bot.reply_to(message, f"💀 {nick} теперь имеет {data['losses']} поражений.")
    except:
        bot.reply_to(message, "❌ Формат: /add_losses ник число")

@bot.message_handler(commands=['remove_losses'])
def remove_losses(message):
    if not admin_only(message): return
    try:
        _, nick, amount = message.text.split()
        amount = int(amount)
        _, data = find_user_by_nick(nick)
        if not data:
            bot.reply_to(message, "⚠️ Игрок не найден.")
            return
        data["losses"] = max(0, data["losses"] - amount)
        bot.reply_to(message, f"💀 {nick} теперь имеет {data['losses']} поражений.")
    except:
        bot.reply_to(message, "❌ Формат: /remove_losses ник число")


# 🃏 ДОБАВИТЬ / УДАЛИТЬ КАРТУ (включая 2 лвл)
@bot.message_handler(commands=['add_card'])
def add_card(message):
    if not admin_only(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❌ Формат: /add_card ник имя_карты")
        return
    _, nick, card_name = parts

    _, data = find_user_by_nick(nick)
    if not data:
        bot.reply_to(message, "⚠️ Игрок не найден.")
        return

    path = resolve_file(card_name, [CARDS_FOLDER, CARDS2_FOLDER])
    if not path:
        bot.reply_to(message, f"❌ Карта не найдена в {CARDS_FOLDER} или {CARDS2_FOLDER}.")
        return

    file = os.path.basename(path)
    data.setdefault("cards", {})
    data["cards"][file] = data["cards"].get(file, 0) + 1
    bot.reply_to(message, f"🃏 Добавлена карта {os.path.splitext(file)[0]} игроку {nick}.")

@bot.message_handler(commands=['remove_card'])
def remove_card(message):
    if not admin_only(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❌ Формат: /remove_card ник имя_карты")
        return
    _, nick, card_name = parts

    _, data = find_user_by_nick(nick)
    if not data or "cards" not in data:
        bot.reply_to(message, "⚠️ У игрока нет карт.")
        return

    # поддержка пробелов и регистраa
    candidates = [card_name.strip(), card_name.strip() + ".jpg", card_name.replace(" ", "_")]
    candidates += [card_name.replace(" ", "_") + ".jpg"]
    inv_lower = {k.lower(): k for k in data["cards"].keys()}
    file_key = None
    for c in candidates:
        file_key = inv_lower.get(c.lower())
        if file_key:
            break

    if not file_key:
        bot.reply_to(message, "⚠️ У игрока нет такой карты.")
        return

    data["cards"][file_key] -= 1
    if data["cards"][file_key] <= 0:
        del data["cards"][file_key]
    bot.reply_to(message, f"🃏 Карта удалена: {os.path.splitext(file_key)[0]} у {nick}.")


# 💠 ДОБАВИТЬ / УДАЛИТЬ АРТЕФАКТ
@bot.message_handler(commands=['add_artifact'])
def add_artifact(message):
    if not admin_only(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❌ Формат: /add_artifact ник название_артефакта")
        return
    _, nick, art_name = parts

    _, data = find_user_by_nick(nick)
    if not data:
        bot.reply_to(message, "⚠️ Игрок не найден.")
        return

    path = resolve_file(art_name, [ARTIFACTS_FOLDER])
    if not path:
        bot.reply_to(message, f"❌ Артефакт не найден в {ARTIFACTS_FOLDER}.")
        return

    file = os.path.basename(path)
    data.setdefault("artifacts", {})
    data["artifacts"][file] = data["artifacts"].get(file, 0) + 1
    bot.reply_to(message, f"💠 Добавлен артефакт {os.path.splitext(file)[0]} игроку {nick}.")

@bot.message_handler(commands=['remove_artifact'])
def remove_artifact(message):
    if not admin_only(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "❌ Формат: /remove_artifact ник название_артефакта")
        return
    _, nick, art_name = parts

    _, data = find_user_by_nick(nick)
    if not data or "artifacts" not in data:
        bot.reply_to(message, "⚠️ У игрока нет артефактов.")
        return

    candidates = [art_name.strip(), art_name.strip() + ".jpg", art_name.replace(" ", "_")]
    candidates += [art_name.replace(" ", "_") + ".jpg"]
    inv_lower = {k.lower(): k for k in data["artifacts"].keys()}
    file_key = None
    for c in candidates:
        file_key = inv_lower.get(c.lower())
        if file_key:
            break

    if not file_key:
        bot.reply_to(message, "⚠️ У игрока нет такого артефакта.")
        return

    data["artifacts"][file_key] -= 1
    if data["artifacts"][file_key] <= 0:
        del data["artifacts"][file_key]
    bot.reply_to(message, f"💠 Артефакт удалён: {os.path.splitext(file_key)[0]} у {nick}.")
