import datetime
import os.path

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types

from loader import dp, connection, cursor, bot
from states import UserAddRecipe
from data.config import admins
from .vip import check_vip

from PIL import Image


@dp.callback_query_handler(text='добавить рецепт')
async def user_add_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id), text='Рецепт будет проверен модератором перед опубликованием',
                                    show_alert=True)

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [
                InlineKeyboardButton(text='❌ Выход', callback_data='выход из написания рецепта')
        ]
    ])

    await UserAddRecipe.title.set()
    await call.message.answer("Введите название вашего блюда:", reply_markup=ikb_menu)


@dp.callback_query_handler(text='выход из написания рецепта', state=UserAddRecipe.title)
async def exit_from_add_article(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    await state.finish()
    await call.message.answer("Отменено")


@dp.message_handler(state=UserAddRecipe.title)
async def enter_title(message: types.Message, state: FSMContext):
    answer = message.text

    if len(answer) > 100:
        await message.answer("Слишком длинное название! Сократите до 100 символов:")
    else:
        await state.update_data(title=answer)
        await UserAddRecipe.img.set()
        await message.answer('Отправьте фотографию блюда:')


@dp.message_handler(state=UserAddRecipe.img, content_types=ContentType.PHOTO)
async def enter_img(message: types.Message, state: FSMContext):
    try:
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id=file_id)
        last_id = cursor.execute("SELECT id FROM recipes_on_moder").fetchall()
        if not last_id:
            rec_id = 1
        else:
            rec_id = last_id[-1][0] + 1

        cursor.execute("INSERT INTO recipes_on_moder (id) VALUES (?)", (rec_id,))
        connection.commit()

        await state.update_data(rec_id=rec_id)
        await file.download(destination_file=os.path.join('images/recipes in moderation/' + str(rec_id) + '.jpg'))
      
        file = Image.open('images/recipes in moderation/' + str(rec_id) + '.jpg')
        file.thumbnail((600, 600))
        file.save('images/recipes in moderation/' + str(rec_id) + '.jpg')

        await UserAddRecipe.ingredients.set()
        await message.answer('Введите ингредиенты (одним сообщением, через запятую; не забудьте указать, '
                             'в каком количестве их следует брать):')
    except:
        await message.answer('Некорректное фото')


@dp.message_handler(state=UserAddRecipe.img, content_types=ContentType.DOCUMENT)
async def enter_img(message: types.Message, state: FSMContext):
    try:
        file_id = message.document.file_id
        file = await bot.get_file(file_id=file_id)
        last_id = cursor.execute("SELECT id FROM recipes_on_moder").fetchall()
        if not last_id:
            rec_id = 1
        else:
            rec_id = last_id[-1][0] + 1

        cursor.execute("INSERT INTO recipes_on_moder (id) VALUES (?)", (rec_id,))
        connection.commit()

        await state.update_data(rec_id=rec_id)
        await file.download(destination_file=os.path.join('images/recipes in moderation/' + str(rec_id) + '.jpg'))

        file = Image.open('images/recipes in moderation/' + str(rec_id) + '.jpg')
        file.thumbnail((600, 600))
        file.save('images/recipes in moderation/' + str(rec_id) + '.jpg')

        await UserAddRecipe.ingredients.set()
        await message.answer('Введите ингредиенты (одним сообщением, через запятую; не забудьте указать, '
                             'в каком количестве их следует брать):')
    except:
        await message.answer('Некорректное фото')


@dp.message_handler(state=UserAddRecipe.ingredients)
async def enter_ingredients(message: types.Message, state: FSMContext):
    answer = message.text

    if len(answer) > 600:
        await message.answer("Слишком много символов! Сократите до 600:")
    else:
        await state.update_data(ingredients=answer)
        await UserAddRecipe.description.set()
        await message.answer("Опишите процесс приготовления (одним сообщением):")


@dp.message_handler(state=UserAddRecipe.description)
async def enter_description(message: types.Message, state: FSMContext):
    answer = message.text

    if len(answer) > 3500:
        await message.answer("Слишком длинное описание! Сократите до 3500 символов:")
    else:
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Да', callback_data='отправить на модерацию рецепт'),
                InlineKeyboardButton(text='❌ Нет', callback_data='не отправлять на модерацию рецепт'),
            ]
        ])

        await state.update_data(description=answer)
        await UserAddRecipe.confirm.set()
        await message.answer("Опубликовать рецепт?", reply_markup=ikb_menu)


@dp.callback_query_handler(text='отправить на модерацию рецепт', state=UserAddRecipe.confirm)
async def send_on_moderation(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    data = await state.get_data()
    title = data.get('title')
    ingredients = data.get('ingredients')
    rec_id = data.get('rec_id')
    description = data.get('description')

    date = str(datetime.date.today())
    author_id = call.from_user.id

    cursor.execute("UPDATE recipes_on_moder SET (title, description, ingredients, author_id, date) = "
                   "(?, ?, ?, ?, ?) WHERE id = ?",
                   (title, description, ingredients, author_id, date, rec_id))
    connection.commit()

    await bot.send_message(chat_id=admins[0], text='Новый рецепт на модерацию!')

    await state.finish()
    await call.message.answer("Ваш рецепт успешно отправлен на модерацию!\n"
                         "<i>/menu</i>")


@dp.callback_query_handler(text='не отправлять на модерацию рецепт', state=UserAddRecipe.confirm)
async def not_send_on_moderation(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    data = await state.get_data()
    rec_id = data.get('rec_id')

    try:
        cursor.execute("DELETE FROM recipes_on_moder WHERE id = ?", (rec_id,))
        connection.commit()
    except Exception as e:
        print(e)

    await state.finish()
    await call.message.answer("❌ Отменено\n/menu")
