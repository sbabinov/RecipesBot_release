import datetime
import os.path

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types

from loader import dp, connection, cursor, bot
from states import UserAddArticle
from data.config import admins
from .vip import check_vip

from PIL import Image


@dp.callback_query_handler(text='написать статью')
async def user_add_article(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
                                        show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id), text='Статья будет проверена модератором перед опубликованием',
                                        show_alert=True)

        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                InlineKeyboardButton(text='❌ Выход', callback_data='выход из написания статьи')
            ]
        ])

        await UserAddArticle.title.set()
        await call.message.answer("Введите название вашей статьи:", reply_markup=ikb_menu)


@dp.callback_query_handler(text='выход из написания статьи', state=UserAddArticle.title)
async def exit_from_add_article(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    await state.finish()
    await call.message.answer("Отменено")


@dp.message_handler(state=UserAddArticle.title)
async def enter_title(message: types.Message, state: FSMContext):
    answer = message.text

    if len(answer) > 100:
        await message.answer("Слишком длинное название! Сократите до 100 символов:")
    else:
        await state.update_data(title=answer)
        await UserAddArticle.img.set()
        await message.answer('Отправьте картинку для вашей статьи:')


@dp.message_handler(state=UserAddArticle.img, content_types=ContentType.PHOTO)
async def enter_img(message: types.Message, state: FSMContext):
    try:
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id=file_id)
        last_id = cursor.execute("SELECT id FROM articles_on_moder").fetchall()
        if not last_id:
            rec_id = 1
        else:
            rec_id = last_id[-1][0] + 1

        cursor.execute("INSERT INTO articles_on_moder (id) VALUES (?)", (rec_id,))
        connection.commit()

        await state.update_data(rec_id=rec_id)
        await file.download(destination_file=os.path.join('images/articles in moderation/' + str(rec_id) + '.jpg'))

        file = Image.open('images/articles in moderation/' + str(rec_id) + '.jpg')
        file.thumbnail((600, 600))
        file.save('images/articles in moderation/' + str(rec_id) + '.jpg')

        await UserAddArticle.description.set()
        await message.answer("Отправьте текст вашей статьи:")
    except:
        await message.answer('Некорректно фото')


@dp.message_handler(state=UserAddArticle.img, content_types=ContentType.DOCUMENT)
async def enter_img(message: types.Message, state: FSMContext):
    try:
        file_id = message.document.file_id
        file = await bot.get_file(file_id=file_id)
        last_id = cursor.execute("SELECT id FROM articles_on_moder").fetchall()
        if not last_id:
            rec_id = 1
        else:
            rec_id = last_id[-1][0] + 1

        cursor.execute("INSERT INTO articles_on_moder (id) VALUES (?)", (rec_id,))
        connection.commit()

        await state.update_data(rec_id=rec_id)
        await file.download(destination_file=os.path.join('images/articles in moderation/' + str(rec_id) + '.jpg'))

        file = Image.open('images/articles in moderation/' + str(rec_id) + '.jpg')
        file.thumbnail((600, 600))
        file.save('images/articles in moderation/' + str(rec_id) + '.jpg')

        await UserAddArticle.description.set()
        await message.answer("Отправьте текст вашей статьи:")
    except:
        await message.answer('Некорректно фото')


@dp.message_handler(state=UserAddArticle.description)
async def enter_description(message: types.Message, state: FSMContext):
    answer = message.text

    if len(answer) > 3500:
        await message.answer("Слишком длинное описание! Сократите до 3500 символов:")
    else:
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Да', callback_data='отправить на модерацию'),
                InlineKeyboardButton(text='❌ Нет', callback_data='не отправлять на модерацию'),
            ]
        ])

        await state.update_data(description=answer)
        await UserAddArticle.confirm.set()
        await message.answer("Опубликовать статью?", reply_markup=ikb_menu)


@dp.callback_query_handler(text='отправить на модерацию', state=UserAddArticle.confirm)
async def send_on_moderation(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    data = await state.get_data()
    title = data.get('title')
    rec_id = data.get('rec_id')
    description = data.get('description')

    date = str(datetime.date.today())
    author_id = call.from_user.id

    cursor.execute("UPDATE articles_on_moder SET (title, description, author_id) = (?, ?, ?) WHERE id = ?",
                   (title, description, author_id, rec_id))
    connection.commit()

    await bot.send_message(chat_id=admins[0], text='Новая статья на модерацию!')

    await state.finish()
    await call.message.answer("Ваша статья успешно отправлена на модерацию!\n"
                         "<i>/menu</i>")


@dp.callback_query_handler(text='не отправлять на модерацию', state=UserAddArticle.confirm)
async def not_send_on_moderation(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    data = await state.get_data()
    rec_id = data.get('rec_id')

    try:
        cursor.execute("DELETE FROM articles_on_moder WHERE id = ?", (rec_id,))
        connection.commit()
    except Exception as e:
        print(e)

    await state.finish()
    await call.message.answer("❌ Отменено\n/menu")


