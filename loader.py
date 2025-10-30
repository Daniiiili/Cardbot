from telebot import TeleBot
from dotenv import load_dotenv
import os

load_dotenv()  # загружаем .env файл

TOKEN = os.getenv("TOKEN")  # берём токен из окружения
bot = TeleBot(TOKEN)