from telebot import TeleBot
from telebot.storage import StateMemoryStorage
from config_data import config
import os

RAPIDAPI_KEY = os.getenv('API_KEY')
storage = StateMemoryStorage()
bot = TeleBot(token=config.BOT_TOKEN, state_storage=storage)
