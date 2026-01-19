from loader import bot
from handlers import start_profile, inventory_shop, admin_commands, fight_system, upgrade_cards
from handlers import donate
from handlers.daily_reset import daily_reset_loop
import threading

if __name__ == "__main__":
    print("✅ Бот запущен")
    threading.Thread(target=daily_reset_loop, daemon=True).start()
    bot.polling(none_stop=True)
