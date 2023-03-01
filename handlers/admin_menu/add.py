from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, CallbackQuery
from aiogram.dispatcher.filters import Command
from aiogram import types

from loader import dp, connection, cursor, bot
from data import admins
from states import AddArticle
from handlers.menu.achievements import give_achievements

from PIL import Image


@dp.callback_query_handler(text='админ-добавить')
async def add(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text=f'📚 Рецепт',
                                                                 callback_data='добавить рецепт админ'),
                                            InlineKeyboardButton(text=f'📒 Статья',
                                                                 callback_data='добавить статью админ'),

                                        ],
                                        [
                                            InlineKeyboardButton(text=f'❓ Вопрос',
                                                                 callback_data='добавить вопрос админ'),
                                            InlineKeyboardButton(text=f'📢 Новость',
                                                                 callback_data='добавить новость админ'),
                                        ],
                                        [
                                            InlineKeyboardButton(text=f'📘 Гайд',
                                                                 callback_data='добавить гайд админ'),
                                            InlineKeyboardButton(text=f'🏋🏻 Упражнение',
                                                                 callback_data='добавить упражнение админ'),
                                        ],
                                        [
                                            InlineKeyboardButton(text=f'↩️ Назад',
                                                                 callback_data='назад из модерации')
                                        ]
                                    ],
                                    )

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)

