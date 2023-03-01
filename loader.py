from aiogram import Bot, types, Dispatcher
import sqlite3

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from pyqiwip2p import QiwiP2P

from data import config

# бот
bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)

storage = MemoryStorage()

# диспетчер
dp = Dispatcher(bot, storage=storage)

# киви
p2p = QiwiP2P(auth_key=config.QIWI_TOKEN)

# дб
connection = sqlite3.connect('server.db')
cursor = connection.cursor()
