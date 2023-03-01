import os.path
import datetime

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.dispatcher.filters import Command
from aiogram import types

from loader import dp, connection, cursor, bot
from data import admins
from states import AddGuide
from utils.make_guide import make_guide

from PIL import Image

from ..menu.settings import check_notifications_settings
from ..users.experience import give_experience
from ..menu.articles import get_inline_menu_for_article


@dp.callback_query_handler(text='добавить гайд админ')
async def add_guide(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    if call.from_user.id in admins:
        await call.message.answer('Введите название гайда:')
        await AddGuide.title.set()


@dp.message_handler(state=AddGuide.title)
async def enter_title(message: types.Message, state: FSMContext):
    answer = message.text

    await state.update_data(title=answer)
    await AddGuide.photo.set()
    await message.answer("Отправьте фото для гайда:")


@dp.message_handler(state=AddGuide.photo, content_types=ContentType.DOCUMENT)
async def enter_photo(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file = await bot.get_file(file_id=file_id)
    last_id = cursor.execute("SELECT id FROM handbook").fetchall()
    if not last_id:
        guide_id = 1
    else:
        guide_id = last_id[-1][0] + 1

    await state.update_data(guide_id=guide_id)
    await file.download(destination_file=os.path.join('images/guides/' + str(guide_id) + '.jpg'))

    file = Image.open(os.path.join('images/guides/' + str(guide_id) + '.jpg'))
    file.thumbnail((600, 600))
    file.save(os.path.join('images/guides/' + str(guide_id) + '.jpg'))

    await AddGuide.text.set()
    await message.answer("Введите текст гайда:")


@dp.message_handler(state=AddGuide.text)
async def enter_text(message: types.Message, state: FSMContext):
    answer = message.text

    await state.update_data(text=answer)

    data = await state.get_data()
    title = data.get('title')
    g_id = data.get('guide_id')

    photo = make_guide(g_id, title=title, text=answer)
    if not photo:
        await message.answer("Слишком много рядов!")
    else:
        chat_id = message.chat.id

        await AddGuide.confirm.set()
        await bot.send_photo(chat_id=chat_id, photo=photo)
        await message.answer("Оставляем?")


@dp.message_handler(state=AddGuide.confirm)
async def confirm(message: types.Message, state: FSMContext):
    answer = message.text

    data = await state.get_data()
    guide_id = data.get('guide_id')

    if answer == 'да':
        title = data.get('title')
        text = data.get('text')

        try:
            os.remove(os.path.join(f'images/guides/{guide_id}.jpg'))
        except Exception as e:
            print(e)

        cursor.execute("INSERT INTO handbook VALUES (?, ?, ?)", (guide_id, title.lower(), text))
        connection.commit()

        await state.finish()
        await message.answer("Успешно добавлено!")

    if answer == 'нет':
        try:
            os.remove(os.path.join(f'images/guides/{guide_id}.jpg'))
        except Exception as e:
            print(e)

        await state.finish()
        await message.answer('Отменено')
