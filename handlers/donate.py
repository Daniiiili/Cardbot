import os
import time
import random
from telebot import types

from loader import bot
from config import DONATE_PHONE, DONATE_BANKS, DONATE_ADMIN_USERNAME, AKATSUKI_PRICE_RUB, AKATSUKI_FOLDER, ADMIN_ID
from database import players_data, pending_payments, mark_dirty


# кто сейчас в процессе отправки чека
waiting_receipt = set()


def _new_payment_id(user_id: int) -> str:
    return f"pay_{user_id}_{int(time.time())}"


def _pick_random_akatsuki_card() -> str | None:
    if not os.path.isdir(AKATSUKI_FOLDER):
        return None
    files = [f for f in os.listdir(AKATSUKI_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    if not files:
        return None
    return random.choice(files)


@bot.message_handler(func=lambda m: m.text.lower() in ["донат", "🪙 донат"])
def donate_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(f"🟥 Купить пак Акацуки ({AKATSUKI_PRICE_RUB}₽)"))
    kb.add(types.KeyboardButton("⬅️ Главное меню"))
    bot.send_message(
        message.chat.id,
        "🪙 *Донат*\n\n"
        "Выбирай пакет доната ниже 👇",
        parse_mode="Markdown",
        reply_markup=kb
    )


@bot.message_handler(func=lambda m: m.text.lower().startswith("🟥 купить пак акацуки"))
def buy_akatsuki(message):
    user_id = message.from_user.id
    data = players_data.get(user_id)

    if not data or not data.get("nick"):
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйся через /start.")
        return

    payment_id = _new_payment_id(user_id)
    pending_payments[payment_id] = {
        "user_id": user_id,
        "nick": data.get("nick"),
        "status": "waiting_receipt",
        "created_at": int(time.time()),
        "product": "akatsuki_pack",
        "price_rub": AKATSUKI_PRICE_RUB,
    }
    mark_dirty()

    waiting_receipt.add(user_id)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Я оплатил — отправить чек", callback_data=f"paid:{payment_id}"))

    bot.send_message(
        message.chat.id,
        "🟥 *Пак Акацуки*\n\n"
        f"Цена: *{AKATSUKI_PRICE_RUB}₽*\n\n"
        f"1) Переведи по СБП на номер: `{DONATE_PHONE}`\n"
        f"2) Банк: *{DONATE_BANKS}*\n"
        f"3) Нажми кнопку ниже и отправь *скрин операции*.\n\n"
        f"Админ для связи: {DONATE_ADMIN_USERNAME}",
        parse_mode="Markdown",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("paid:"))
def paid_callback(call):
    user_id = call.from_user.id
    payment_id = call.data.split(":", 1)[1]

    p = pending_payments.get(payment_id)
    if not p or p.get("user_id") != user_id:
        bot.answer_callback_query(call.id, "Заявка не найдена.")
        return

    waiting_receipt.add(user_id)
    bot.answer_callback_query(call.id, "Ок! Теперь пришли скрин операции сюда в чат.")
    bot.send_message(call.message.chat.id, f"📎 Отправь сюда *скрин/фото* оплаты.\nID заявки: `{payment_id}`", parse_mode="Markdown")


@bot.message_handler(content_types=["photo", "document"])
def receipt_handler(message):
    user_id = message.from_user.id
    if user_id not in waiting_receipt:
        return

    # находим последнюю активную заявку этого юзера в статусе waiting_receipt
    payment_id = None
    for pid, p in pending_payments.items():
        if p.get("user_id") == user_id and p.get("status") == "waiting_receipt":
            payment_id = pid

    if not payment_id:
        bot.send_message(message.chat.id, "⚠️ Не нашёл активную заявку. Нажми Донат → купить пак снова.")
        waiting_receipt.discard(user_id)
        return

    # меняем статус
    pending_payments[payment_id]["status"] = "pending_admin"
    mark_dirty()
    waiting_receipt.discard(user_id)

    # отправляем админу заявку + сам чек (форвардом)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"adm_ok:{payment_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"adm_no:{payment_id}")
    )

    info = pending_payments[payment_id]
    text = (
        "🧾 *Новая заявка на донат*\n\n"
        f"ID: `{payment_id}`\n"
        f"Ник: *{info.get('nick','-')}*\n"
        f"UserID: `{info.get('user_id')}`\n"
        f"Товар: *Акацуки пак*\n"
        f"Сумма: *{info.get('price_rub')}₽*\n\n"
        "Ниже чек от игрока 👇"
    )

    bot.send_message(ADMIN_ID, text, parse_mode="Markdown", reply_markup=kb)
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

    bot.send_message(message.chat.id, "✅ Заявка отправлена админу. Как подтвердят — я выдам награду.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_ok:") or c.data.startswith("adm_no:"))
def admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Нет прав.")
        return

    action, payment_id = call.data.split(":", 1)
    p = pending_payments.get(payment_id)
    if not p:
        bot.answer_callback_query(call.id, "Заявка не найдена.")
        return
    if p.get("status") not in ("pending_admin", "waiting_receipt"):
        bot.answer_callback_query(call.id, f"Статус заявки: {p.get('status')}")
        return

    user_id = p["user_id"]

    if action == "adm_no":
        p["status"] = "rejected"
        mark_dirty()
        bot.answer_callback_query(call.id, "Отклонено.")
        bot.send_message(user_id, "❌ Донат не подтверждён. Если это ошибка — напиши админу.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        return

    # approve
    card_file = _pick_random_akatsuki_card()
    if not card_file:
        bot.answer_callback_query(call.id, "Нет карт в папке card_akatsuki.")
        return

    players_data.setdefault(user_id, {}).setdefault("cards", {})
    players_data[user_id]["cards"][card_file] = players_data[user_id]["cards"].get(card_file, 0) + 1

    p["status"] = "approved"
    p["reward"] = card_file
    mark_dirty()

    # уведомления
    bot.answer_callback_query(call.id, "Подтверждено, награда выдана.")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    card_name = os.path.splitext(card_file)[0]
    try:
        with open(os.path.join(AKATSUKI_FOLDER, card_file), "rb") as photo:
            bot.send_photo(user_id, photo, caption=f"🟥 Донат подтверждён!\n🎴 Ты получил карту: *{card_name}*", parse_mode="Markdown")
    except Exception:
        bot.send_message(user_id, f"🟥 Донат подтверждён!\n🎴 Ты получил карту: {card_name}")

    bot.send_message(ADMIN_ID, f"✅ Выдано: {p.get('nick')} получил {card_name} (ID {payment_id})")
