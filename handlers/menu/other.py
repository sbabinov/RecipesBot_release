import os

from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InputFile, InputMedia

from .functions_loader import get_user_theme_picture
from loader import dp, bot


@dp.callback_query_handler(text='прочее')
async def other(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'other')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='✏️ Статьи', callback_data=f'статьи'),
                                            InlineKeyboardButton(text='🧩 Викторины', callback_data='викторины'),

                                        ],
                                        [
                                            # InlineKeyboardButton(text='⏰ Таймер', callback_data='таймер'),
                                            InlineKeyboardButton(text='❤️ Здоровье', callback_data='здоровье'),
                                            InlineKeyboardButton(text='📢 Новости', callback_data='новости'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='назад'),
                                        ]
                                    ],
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    media = InputMedia(media=image)
    await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)

