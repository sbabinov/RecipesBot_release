import os.path
import datetime

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.dispatcher.filters import Command
from aiogram import types

from loader import dp, connection, cursor, bot
from data import admins
from states import AddNews
from ..menu.achievements import give_achievements

from PIL import Image

from ..menu.settings import check_notifications_settings
from ..users.experience import give_experience
from ..menu.articles import get_inline_menu_for_article


@dp.callback_query_handler(text='добавить новость админ')
async def add_news(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    if call.from_user.id in admins:
        await call.message.answer('Введите название новости:')
        await AddNews.title.set()


@dp.message_handler(state=AddNews.title)
async def enter_title(message: types.Message, state: FSMContext):
    answer = message.text

    await state.update_data(title=answer)
    await AddNews.photo.set()
    await message.answer("Отправьте фото для новости:")


@dp.message_handler(state=AddNews.photo, content_types=ContentType.DOCUMENT)
async def enter_photo(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file = await bot.get_file(file_id=file_id)
    last_id = cursor.execute("SELECT id FROM news").fetchall()
    if not last_id:
        news_id = 1
    else:
        news_id = last_id[-1][0] + 1

    await state.update_data(news_id=news_id)
    await file.download(destination_file=os.path.join('images/news/' + str(news_id) + '.jpg'))

    file = Image.open('images/news/' + str(news_id) + '.jpg')
    file.thumbnail((600, 600))
    file.save('images/news/' + str(news_id) + '.jpg')

    await AddNews.text.set()
    await message.answer("Введите описание новости:")


@dp.message_handler(state=AddNews.text)
async def enter_text(message: types.Message, state: FSMContext):
    answer = message.text

    await state.update_data(text=answer)

    data = await state.get_data()
    news_id = data.get('news_id')
    title = data.get('title')
    date = str(datetime.date.today())

    text = f"<b>{title}</b>\n\n" \
           f"{answer}\n\n" \
           f"<i>{date}</i>"

    photo = InputFile(os.path.join(f'images/news/{news_id}.jpg'))
    chat_id = message.chat.id

    await bot.send_photo(chat_id=chat_id, photo=photo, caption=text)
    await AddNews.confirm.set()
    await message.answer('Оставляем?')


@dp.message_handler(state=AddNews.confirm)
async def confirm(message: types.Message, state: FSMContext):
    answer = message.text

    if answer == 'да':
        data = await state.get_data()

        news_id = data.get('news_id')
        title = data.get('title')
        text = data.get('text')

        date = str(datetime.date.today())

        cursor.execute("INSERT INTO news VALUES (?, ?, ?, ?)", (news_id, title, text, date))
        connection.commit()

        caption = f"<b>{title}</b>\n\n" \
                  f"{text}\n\n" \
                  f"<i>{date}</i>"

        photo = InputFile(os.path.join(f'images/news/{news_id}.jpg'))

        users_ids = [i[0] for i in cursor.execute("SELECT id FROM profiles").fetchall()]
        for i in users_ids:
            try:
                await bot.send_photo(chat_id=i, photo=photo, caption=caption)
            except Exception as e:
                print(e)

        await state.finish()
        await message.answer("Успешно добавлено!")

    if answer == 'нет':
        await state.finish()
        await message.answer('Отменено')

