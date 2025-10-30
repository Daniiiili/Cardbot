from loader import bot
from handlers import start_profile, inventory_shop, admin_commands, fight_system, upgrade_cards
if __name__ == "__main__":
    print("✅ Бот запущен")
    bot.polling(none_stop=True)

