import os.path

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InputFile, InputMedia

from loader import dp, connection, cursor, bot
from aiogram.dispatcher.filters import Command
from aiogram import types
from states import Search
from .settings import filter_recipes
from .achievements import give_achievements
from ..users.experience import give_experience

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@dp.callback_query_handler(text='топ')
async def top(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id), text='🛠 В разработке', show_alert=True)
