import time
from datetime import datetime, timedelta

from loader import bot
from database import players_data, mark_dirty


RESET_HOUR = 20      # 00:00
RESET_MINUTE = 0


def _seconds_until_next_reset() -> int:
    now = datetime.now()
    target = now.replace(hour=RESET_HOUR, minute=RESET_MINUTE, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return int((target - now).total_seconds())


def reset_battles_and_notify():
    # 1) сброс боёв всем зарегистрированным
    changed = 0
    uids = []
    for uid, data in players_data.items():
        if not data or not data.get("nick"):
            continue
        if data.get("battles", 0) != 0:
            data["battles"] = 0
            changed += 1
        uids.append(uid)

    if changed > 0:
        mark_dirty()

    # 2) уведомление всем
    text = "🔄 Ежедневный сброс!\n⚔️ Бои обновлены: у тебя снова доступно 7 боёв на сегодня."
    for uid in uids:
        try:
            bot.send_message(uid, text)
        except Exception:
            # если пользователь запретил бота/удалил чат — просто пропускаем
            pass

        # маленькая пауза, чтобы не словить лимиты Telegram
        time.sleep(0.05)


def daily_reset_loop():
    while True:
        time.sleep(_seconds_until_next_reset())
        reset_battles_and_notify()
        # на всякий случай, чтобы не сработало 2 раза подряд из-за лагов
        time.sleep(2)
