import os

from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InputFile, InputMedia

from loader import dp, connection, cursor, bot
from .menu import get_recipe
from .settings import filter_recipes
from .functions_loader import get_user_theme_picture


categories = ['супы', '2-е блюда', 'закуски', 'салаты', 'выпечка', 'соусы', 'заготовки', 'десерты', 'напитки']


def get_category(recipe_id: int) -> str:
    category = cursor.execute("SELECT type FROM recipes WHERE id = ?", (recipe_id,)).fetchone()[0]
    return category


@dp.callback_query_handler(text='категории11')
async def open_categories(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'categories')
    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🫕 Супы', callback_data=f'тип_супы'),
                                            InlineKeyboardButton(text='🍛 2-е блюда', callback_data='тип_вторые блюда'),
                                            InlineKeyboardButton(text='🥪 Закуски', callback_data='тип_закуски'),

                                        ],
                                        [
                                            InlineKeyboardButton(text='🥗 Салаты', callback_data='тип_салаты'),
                                            InlineKeyboardButton(text='🍕 Выпечка', callback_data='тип_выпечка'),
                                            InlineKeyboardButton(text='🫖 Соусы', callback_data='тип_соусы'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='🥒 Заготовки', callback_data='тип_заготовки'),
                                            InlineKeyboardButton(text='🍩 Десерты', callback_data='тип_десерты'),
                                            InlineKeyboardButton(text='🍹 Напитки', callback_data='тип_напитки'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='Оецепты'),
                                        ]
                                    ],
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    media = InputMedia(media=image)
    await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='тип')
async def show_recipes_from_category(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id
    category = call.data.split('_')[1]
    recipes_ids = cursor.execute("SELECT id FROM recipes WHERE type = ?", (category,)).fetchall()

    ids = []
    for i in recipes_ids:
        ids.append(i[0])

    if not ids:
        await call.message.answer("В этой категории пока нет рецептов!")
    else:
        user_filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()
        ids = filter_recipes(ids, user_filters[0], filter_type=int(user_filters[1]))

        await get_recipe(call, ids, ids[0], call=True)





