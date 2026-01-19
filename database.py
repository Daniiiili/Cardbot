import json
import os
import threading
import time
import atexit

DATA_FILE = "players_data.json"
SAVE_EVERY_SECONDS = 30

pending_payments = {}
players_data = {}
used_nicks = set()
waiting_for_nick = set()   # временное, не сохраняем
active_fights = {}        # временное, не сохраняем

_dirty = False


def mark_dirty():
    global _dirty
    _dirty = True


def load_all():
    global players_data, used_nicks

    if not os.path.exists(DATA_FILE):
        print("💾 База данных не найдена — стартуем с пустой.")
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)

        players_raw = raw.get("players_data", {})
        pending_payments = raw.get("pending_payments", {})
        players_data = {int(uid): pdata for uid, pdata in players_raw.items()}
        used_nicks = set(raw.get("used_nicks", []))

        print(f"💾 Загружено игроков: {len(players_data)}")
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")


def save_all(force=False):
    global _dirty
    if not force and not _dirty:
        return

    try:
        data = {
            "players_data": {str(uid): pdata for uid, pdata in players_data.items()},
            "used_nicks": list(used_nicks),
            "pending_payments": pending_payments
        }

        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        os.replace(tmp, DATA_FILE)
        _dirty = False
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")


def _autosave():
    while True:
        time.sleep(SAVE_EVERY_SECONDS)
        save_all()


load_all()
threading.Thread(target=_autosave, daemon=True).start()
atexit.register(lambda: save_all(force=True))
