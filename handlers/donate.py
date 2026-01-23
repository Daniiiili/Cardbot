import os
import time
import random
from telebot import types

from loader import bot
from config import (
    DONATE_PHONE, DONATE_BANKS, DONATE_ADMIN_USERNAME, ADMIN_ID,
    AKATSUKI_PRICE_RUB, AKATSUKI_FOLDER,
    CHUNIN_PRICE_RUB, CHUNIN_FOLDER,
    BIJU_PRICE_RUB, BIJU_FOLDER
)
from database import players_data, pending_payments, mark_dirty


# кто сейчас в процессе отправки чека
waiting_receipt = set()
PRODUCTS = {
    "akatsuki_pack": {
        "title": "🟥 Пак Акацуки",
        "price": AKATSUKI_PRICE_RUB,
        "folder": AKATSUKI_FOLDER,
        "button": f"🟥 Купить пак Акацуки ({AKATSUKI_PRICE_RUB}₽)",
    },
    "chunin_pack": {
        "title": "🟦 Пак Чунины",
        "price": CHUNIN_PRICE_RUB,
        "folder": CHUNIN_FOLDER,
        "button": f"🟦 Купить пак Чунины ({CHUNIN_PRICE_RUB}₽)",
    },
    "biju_pack": {
        "title": "🟨 Пак Биджу",
        "price": BIJU_PRICE_RUB,
        "folder": BIJU_FOLDER,
        "button": f"🟨 Купить пак Биджу ({BIJU_PRICE_RUB}₽)",
    },
}

def _new_payment_id(user_id: int) -> str:
    return f"pay_{user_id}_{int(time.time())}"


def _pick_random_card_from(folder: str) -> str | None:
    if not os.path.isdir(folder):
        return None
    files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    if not files:
        return None
    return random.choice(files)


@bot.message_handler(func=lambda m: m.text.lower() in ["донат", "🪙 донат"])
def donate_menu(message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(PRODUCTS["akatsuki_pack"]["button"]))
    kb.add(types.KeyboardButton(PRODUCTS["chunin_pack"]["button"]))
    kb.add(types.KeyboardButton(PRODUCTS["biju_pack"]["button"]))
    kb.add(types.KeyboardButton("⬅️ Главное меню"))

    bot.send_message(
        message.chat.id,
        "🪙 *Донат-магазин*\n\n"
        "Выбери пакет. После оплаты пришли *скрин операции* — заявка уйдёт админу, и после подтверждения бот выдаст награду.",
        parse_mode="Markdown",
        reply_markup=kb
    )

def _find_product_by_button(text: str):
    t = text.strip()
    for key, p in PRODUCTS.items():
        if t == p["button"]:
            return key, p
    return None, None


@bot.message_handler(func=lambda m: _find_product_by_button(m.text or "")[0] is not None)
def buy_product(message):
    user_id = message.from_user.id
    data = players_data.get(user_id)

    if not data or not data.get("nick"):
        bot.send_message(message.chat.id, "⚠️ Сначала зарегистрируйся через /start.")
        return

    product_key, product = _find_product_by_button(message.text)

    payment_id = _new_payment_id(user_id)
    pending_payments[payment_id] = {
        "user_id": user_id,
        "nick": data.get("nick"),
        "status": "waiting_receipt",
        "created_at": int(time.time()),
        "product": product_key,
        "price_rub": product["price"],
    }
    mark_dirty()

    waiting_receipt.add(user_id)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Я оплатил — отправить чек", callback_data=f"paid:{payment_id}"))

    bot.send_message(
        message.chat.id,
        f"{product['title']}\n\n"
        f"Цена: *{product['price']}₽*\n\n"
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
    # только админ
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Нет прав.")
        return

    action, payment_id = call.data.split(":", 1)

    p = pending_payments.get(payment_id)
    if not p:
        bot.answer_callback_query(call.id, "Заявка не найдена.")
        return

    # чтобы не подтверждали повторно
    if p.get("status") not in ("pending_admin", "waiting_receipt"):
        bot.answer_callback_query(call.id, f"Статус заявки: {p.get('status')}")
        return

    user_id = p.get("user_id")
    if not user_id:
        bot.answer_callback_query(call.id, "В заявке нет user_id.")
        return

    # ❌ отклонение
    if action == "adm_no":
        p["status"] = "rejected"
        mark_dirty()

        bot.answer_callback_query(call.id, "Отклонено.")
        try:
            bot.send_message(user_id, "❌ Донат не подтверждён. Если это ошибка — напиши админу.")
        except Exception:
            pass

        # убираем кнопки у админ-сообщения
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception:
            pass
        return

    # ✅ подтверждение
    product_key = p.get("product")
    product = PRODUCTS.get(product_key)
    if not product:
        bot.answer_callback_query(call.id, "❌ Неизвестный товар в заявке.")
        return

    folder = product.get("folder")
    if not folder:
        bot.answer_callback_query(call.id, "❌ У товара не задана папка.")
        return

    # выбрать рандомную карту из нужной папки
    def _pick_random_card_from(folder_path: str):
        if not os.path.isdir(folder_path):
            return None
        files = [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        if not files:
            return None
        return random.choice(files)

    card_file = _pick_random_card_from(folder)
    if not card_file:
        bot.answer_callback_query(call.id, f"❌ Нет карт в папке: {folder}")
        return

    # выдать карту игроку
    players_data.setdefault(user_id, {}).setdefault("cards", {})
    players_data[user_id]["cards"][card_file] = players_data[user_id]["cards"].get(card_file, 0) + 1

    # отметить заявку
    p["status"] = "approved"
    p["reward"] = card_file
    mark_dirty()

    # UI админа
    bot.answer_callback_query(call.id, "✅ Подтверждено, награда выдана.")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception:
        pass

    # уведомить игрока
    card_name = os.path.splitext(card_file)[0]
    try:
        with open(os.path.join(folder, card_file), "rb") as photo:
            bot.send_photo(
                user_id,
                photo,
                caption=(
                    "✅ Донат подтверждён!\n"
                    f"{product['title']}\n"
                    f"🎴 Ты получил карту: *{card_name}*"
                ),
                parse_mode="Markdown"
            )
    except Exception:
        try:
            bot.send_message(
                user_id,
                f"✅ Донат подтверждён!\n{product['title']}\n🎴 Ты получил карту: {card_name}"
            )
        except Exception:
            pass

    # лог админу
    try:
        bot.send_message(
            ADMIN_ID,
            f"✅ Выдано: {p.get('nick')} получил {card_name} ({product['title']}) (ID {payment_id})"
        )
    except Exception:
        pass