import os.path
import datetime

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, CallbackQuery
from aiogram.dispatcher.filters import Command
from aiogram import types

from ..menu.functions_loader import get_user_theme_picture
from loader import dp, connection, cursor, bot, storage
from data import admins
from states import Moderation


@dp.message_handler(Command('admin'))
async def show_admin_menu(message: types.Message):
    user_id = message.from_user.id

    if user_id in admins:
        image = get_user_theme_picture(user_id, 'admin_menu')

        rec_ids = cursor.execute("SELECT id FROM recipes_on_moder").fetchall()
        art_ids = cursor.execute("SELECT id FROM articles_on_moder").fetchall()

        amount_rec = 0 if not rec_ids else len(rec_ids)
        amount_art = 0 if not art_ids else len(art_ids)

        amount_to_moder = amount_rec + amount_art
        on_moder = f"({amount_to_moder})" if amount_to_moder else ""

        help_requests_ids = cursor.execute("SELECT id FROM help").fetchall()
        requests_amount = len(help_requests_ids)

        requests_text = f"({requests_amount})" if requests_amount else ""

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='📊 Статистика', callback_data='статистика'),
                                                InlineKeyboardButton(text=f'📌 Модерация {on_moder}',
                                                                     callback_data='модерация')
                                            ],
                                            [
                                                InlineKeyboardButton(text='➕ Добавить', callback_data='админ-добавить'),
                                                InlineKeyboardButton(text=f'📞 Помощь {requests_text}',
                                                                     callback_data='помощь')
                                            ]

                                        ],
                                        )
        chat_id = message.chat.id

        await bot.send_photo(chat_id=chat_id, photo=image, reply_markup=ikb_menu)


@dp.callback_query_handler(text='модерация')
async def moderation(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    rec_ids = cursor.execute("SELECT id FROM recipes_on_moder").fetchall()
    art_ids = cursor.execute("SELECT id FROM articles_on_moder").fetchall()

    amount_rec = "" if not rec_ids else f"({len(rec_ids)})"
    amount_art = "" if not art_ids else f"({len(art_ids)})"

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text=f'📚 Рецепты {amount_rec}',
                                                                 callback_data='рецепты на модерации'),
                                            InlineKeyboardButton(text=f'📒 Статьи {amount_art}',
                                                                 callback_data='статьи на модерации')
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


@dp.callback_query_handler(text='назад из модерации')
async def back_from_moderation(call: CallbackQuery):
    rec_ids = cursor.execute("SELECT id FROM recipes_on_moder").fetchall()
    art_ids = cursor.execute("SELECT id FROM articles_on_moder").fetchall()

    amount_rec = 0 if not rec_ids else len(rec_ids)
    amount_art = 0 if not art_ids else len(art_ids)

    amount = amount_rec + amount_art
    on_moder = f"({amount})" if amount else ""

    help_requests_ids = cursor.execute("SELECT id FROM help").fetchall()
    requests_amount = len(help_requests_ids)

    requests_text = f"({requests_amount})" if requests_amount else ""

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='📊 Статистика', callback_data='статистика'),
                                            InlineKeyboardButton(text=f'📌 Модерация {on_moder}',
                                                                 callback_data='модерация')
                                        ],
                                        [
                                            InlineKeyboardButton(text='➕ Добавить', callback_data='админ-добавить'),
                                            InlineKeyboardButton(text=f'📞 Помощь {requests_text}',
                                                                 callback_data='помощь')
                                        ]

                                    ],
                                    )
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text='рецепты на модерации')
async def recipes_moderation(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    rec_ids = cursor.execute("SELECT id FROM recipes_on_moder").fetchall()

    if rec_ids:
        rec_id = rec_ids[0][0]
        ingredients = cursor.execute("SELECT ingredients FROM recipes_on_moder WHERE id = ?", (rec_id,)).fetchone()[0]
        description = cursor.execute("SELECT description FROM recipes_on_moder WHERE id = ?", (rec_id,)).fetchone()[0]
        title = cursor.execute("SELECT title FROM recipes_on_moder WHERE id = ?", (rec_id,)).fetchone()[0]
        author_id = cursor.execute("SELECT author_id FROM recipes_on_moder WHERE id = ?", (rec_id,)).fetchone()[0]

        author_name = cursor.execute("SELECT name FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]

        photo = InputFile(os.path.join(f'images/recipes in moderation/{rec_id}.jpg'))
        chat_id = call.message.chat.id

        caption = f"<b>{title}</b>\n\n" \
             f"<i><b>Ингредиенты:</b></i>\n" \
             f"{ingredients.capitalize()}.\n\n" \
             f"<code>{author_id}</code>  |  <code>{author_name}</code>\n" \

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='❌ Удалить',
                                                                     callback_data=f'Удалить рецепт_{rec_id}'),
                                                InlineKeyboardButton(text='✏️ Написать автору',
                                                                     callback_data=f'написать автору рецепта_{rec_id}')
                                            ]
                                        ],
                                        )

        await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
        await call.message.answer(description, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Удалить рецепт')
async def delete_recipe_on_moderation(call: CallbackQuery):
    rec_id = int(call.data.split('_')[1])

    cursor.execute("DELETE FROM recipes_on_moder WHERE id = ?", (rec_id,))
    connection.commit()

    try:
        os.remove(os.path.join(f'images/recipes in moderation/{rec_id}.jpg'))
    except Exception as e:
        print(e)

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    await bot.answer_callback_query(str(call.id), text='Успешно удалено', show_alert=True)


@dp.callback_query_handler(text='статьи на модерации')
async def articles_moderation(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    art_ids = cursor.execute("SELECT id FROM articles_on_moder").fetchall()

    if art_ids:
        art_ids = art_ids[0][0]
        description = cursor.execute("SELECT description FROM articles_on_moder WHERE id = ?", (art_ids,)).fetchone()[0]
        title = cursor.execute("SELECT title FROM articles_on_moder WHERE id = ?", (art_ids,)).fetchone()[0]
        author_id = cursor.execute("SELECT author_id FROM articles_on_moder WHERE id = ?", (art_ids,)).fetchone()[0]

        author_name = cursor.execute("SELECT name FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]

        photo = InputFile(os.path.join(f'images/articles in moderation/{art_ids}.jpg'))
        chat_id = call.message.chat.id

        caption = f'<b>{title}</b>\n\n' \
                  f'{description}\n\n' \
                  f'<i>Автор: <code>{author_name}</code> <code>{author_id}</code></i>'

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='❌ Удалить',
                                                                     callback_data=f'Удалить статью_{art_ids}'),
                                                InlineKeyboardButton(text='✏️ Написать автору',
                                                                     callback_data=f'написать автору статьи_{art_ids}')
                                            ]
                                        ],
                                        )

        await bot.send_photo(chat_id=chat_id, photo=photo)
        await call.message.answer(caption, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Удалить статью')
async def delete_article_on_moderation(call: CallbackQuery):
    art_id = int(call.data.split('_')[1])

    cursor.execute("DELETE FROM articles_on_moder WHERE id = ?", (art_id,))
    connection.commit()

    try:
        os.remove(os.path.join(f'images/articles in moderation/{art_id}.jpg'))
    except Exception as e:
        print(e)

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    await bot.answer_callback_query(str(call.id), text='Успешно удалено', show_alert=True)


@dp.callback_query_handler(text_contains='написать автору статьи')
async def write_to_art_author(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    art_id = int(call.data.split('_')[1])
    print(art_id)

    chat_id = call.message.chat.id
    user_id = call.from_user.id

    state = FSMContext(storage, chat_id, user_id)

    await state.update_data(art_id=art_id)
    await Moderation.write_to_author.set()
    await call.message.answer("Напишите сообщение для пользователя:")


@dp.message_handler(state=Moderation.write_to_author)
async def message_to_author(message: types.Message, state: FSMContext):
    answer = message.text

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [
            InlineKeyboardButton(text='Да', callback_data='отправить автору'),
            InlineKeyboardButton(text='Нет', callback_data='не отправлять автору'),
        ]
    ])

    await state.update_data(write_to_author=answer)
    await Moderation.confirm.set()
    await message.answer("Отправить пользователю?", reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='отправить автору', state=Moderation.confirm)
async def confirm_write(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    data = await state.get_data()
    art_id = data.get('art_id')
    write_to_author = data.get('write_to_author')

    author_id = cursor.execute("SELECT author_id FROM articles_on_moder WHERE id = ?", (art_id,)).fetchone()[0]
    title = cursor.execute("SELECT title FROM articles_on_moder WHERE id = ?", (art_id,)).fetchone()[0]
    description = cursor.execute("SELECT description FROM articles_on_moder WHERE id = ?", (art_id,)).fetchone()[0]

    photo = InputFile(os.path.join(f'images/articles in moderation/{art_id}.jpg'))

    article_text = f"<b>{title}</b>\n\n" \
                   f"{description}"
    moder_text = f"<b>Ответ от модератора:</b>\n\n" \
                 f"{write_to_author}"

    try:
        await bot.send_photo(chat_id=author_id, photo=photo)
        await bot.send_message(chat_id=author_id, text=article_text)
        await bot.send_message(chat_id=author_id, text=moder_text)
    except:
        pass

    await state.finish()
    await call.message.answer("Успешно отправлено пользователю")


@dp.callback_query_handler(text_contains='не отправлять автору', state=Moderation.confirm)
async def not_confirm_write(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    await state.finish()
    await call.message.answer("Отменено")


@dp.callback_query_handler(text_contains='написать автору рецепта')
async def write_to_art_author(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    rec_id = int(call.data.split('_')[1])
    print(rec_id)

    chat_id = call.message.chat.id
    user_id = call.from_user.id

    state = FSMContext(storage, chat_id, user_id)

    await state.update_data(rec_id=rec_id)
    await Moderation.message_text.set()
    await call.message.answer("Напишите сообщение для пользователя:")


@dp.message_handler(state=Moderation.message_text)
async def message_to_author(message: types.Message, state: FSMContext):
    answer = message.text

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [
            InlineKeyboardButton(text='Да', callback_data='отправить автору'),
            InlineKeyboardButton(text='Нет', callback_data='не отправлять автору'),
        ]
    ])

    await state.update_data(message_text=answer)
    await Moderation.confirm_recipe.set()
    await message.answer("Отправить пользователю?", reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='отправить автору', state=Moderation.confirm_recipe)
async def confirm_write(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    data = await state.get_data()
    rec_id = data.get('rec_id')
    message_text = data.get('message_text')

    author_id = cursor.execute("SELECT author_id FROM recipes_on_moder WHERE id = ?", (rec_id,)).fetchone()[0]
    title = cursor.execute("SELECT title FROM recipes_on_moder WHERE id = ?", (rec_id,)).fetchone()[0]
    ingredients = cursor.execute("SELECT ingredients FROM recipes_on_moder WHERE id = ?", (rec_id,)).fetchone()[0]
    description = cursor.execute("SELECT description FROM recipes_on_moder WHERE id = ?", (rec_id,)).fetchone()[0]

    photo = InputFile(os.path.join(f'images/recipes in moderation/{rec_id}.jpg'))

    caption = f"<b>{title}</b>\n\n" \
              f"<b><i>Ингредиенты:</i></b>\n" \
              f"{ingredients.capitalize()}"
    description = f"<b><i>Приготовление:</i></b>\n" \
                  f"{description}"

    moder_text = f"<b>Ответ от модератора:</b>\n\n" \
                 f"{message_text}"

    try:
        await bot.send_photo(chat_id=author_id, photo=photo, caption=caption)
        await bot.send_message(chat_id=author_id, text=description)
        await bot.send_message(chat_id=author_id, text=moder_text)
    except:
        pass

    await state.finish()
    await call.message.answer("Успешно отправлено пользователю")


@dp.callback_query_handler(text_contains='не отправлять автору', state=Moderation.confirm_recipe)
async def not_confirm_write(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    await state.finish()
    await call.message.answer("Отменено")




