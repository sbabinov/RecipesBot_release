import os.path
import datetime

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types

from loader import dp, connection, cursor, bot
from data import admins
from states import AddRecipe
from ..menu.achievements import give_achievements
from ..menu.settings import check_notifications_settings
from ..menu.menu import get_recipe
from ..menu.search_by_tags import tags
from ..menu.categories import categories

from PIL import Image

from ..users.experience import give_experience


@dp.callback_query_handler(text='добавить рецепт админ')
async def add_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    if call.from_user.id in admins:
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[[InlineKeyboardButton(text='❌ Выход',
                                                                                            callback_data=
                                                                                            'выход из добавления')]])
        await call.message.answer('Введите автора блюда:', reply_markup=ikb_menu)
        await AddRecipe.author_id.set()


@dp.message_handler(state=AddRecipe.author_id)
async def enter_author_id(message: types.Message, state: FSMContext):
    answer = int(message.text)
    await state.update_data(author_id=answer)
    await AddRecipe.title.set()
    await message.answer('Введите название блюда:')


@dp.message_handler(state=AddRecipe.title)
async def enter_title(message: types.Message, state: FSMContext):
    answer = message.text
    str_categories = ' '.join([f"<code>{c}</code>" for c in categories])
    await state.update_data(title=answer)
    await AddRecipe.type.set()
    await message.answer(str_categories)
    await message.answer('Введите категорию блюда:')


@dp.message_handler(state=AddRecipe.type)
async def enter_type(message: types.Message, state: FSMContext):
    answer = message.text
    await state.update_data(type=answer)
    await AddRecipe.img.set()
    await message.answer('Отправьте фото блюда:')


@dp.message_handler(state=AddRecipe.img, content_types=ContentType.DOCUMENT)
async def enter_img(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file = await bot.get_file(file_id=file_id)
    last_id = cursor.execute("SELECT id FROM recipes").fetchall()
    if not last_id:
        rec_id = 1
    else:
        rec_id = last_id[-1][0] + 1
    print(rec_id)
    await state.update_data(rec_id=rec_id)
    await file.download(destination_file=os.path.join('images/recipes/' + str(rec_id) + '.jpg'))

    file = Image.open('images/recipes/' + str(rec_id) + '.jpg')
    file.thumbnail((600, 600))
    file.save('images/recipes/' + str(rec_id) + '.jpg')

    await AddRecipe.ingredients.set()
    await message.answer('Введите ингредиент:')


@dp.message_handler(state=AddRecipe.ingredients)
async def enter_ingredients(message: types.Message, state: FSMContext):
    answer = message.text
    if answer.lower() == 'стоп':
        str_tags = ' '.join([f"<code>{t}</code>" for t in tags])
        await AddRecipe.tags.set()
        await message.answer(str_tags)
        await message.answer('Введите теги:')
    else:
        data = await state.get_data()
        ingredients: list = data.get('ingredients')
        if not ingredients:
            await state.update_data(ingredients=[answer])
        else:
            await state.update_data(ingredients=ingredients + [answer])
        await message.answer('Введите ингредиент:')


@dp.message_handler(state=AddRecipe.tags)
async def enter_tags(message: types.Message, state: FSMContext):
    answer = message.text
    if answer.lower() == 'стоп':
        await AddRecipe.description.set()
        await message.answer('Опишите процесс приготовления блюда:')
    else:
        data = await state.get_data()
        tags: list = data.get('tags')
        if not tags:
            await state.update_data(tags=[answer])
        else:
            await state.update_data(tags=tags + [answer])
        await message.answer('Введите теги:')


@dp.message_handler(state=AddRecipe.description)
async def enter_descriptions(message: types.Message, state: FSMContext):
    answer = message.text
    await state.update_data(description=answer)

    data = await state.get_data()
    title: str = data.get('title')
    type_: str = data.get('type')
    rec_id = data.get('rec_id')
    ingredients: list = data.get('ingredients')
    description = data.get('description')
    author_id = data.get('author_id')

    path = os.path.join('images/recipes/' + str(rec_id) + '.jpg')

    caption = f"<b><i>{title}</i></b> (<i>{type_.lower()}</i>)\n\n" \
              f"<b>Ингредиенты:</b>\n" \
              f"{', '.join(ingredients).capitalize()}.\n\n" \
              f"{f'<i>Автор: {author_id}</i>' if author_id != 0 else ''}"

    await bot.send_photo(photo=types.InputFile(path), caption=caption, chat_id=message.chat.id)
    await message.answer('Оставляем?')

    await AddRecipe.confirm.set()


@dp.message_handler(state=AddRecipe.confirm)
async def confirm(message: types.Message, state: FSMContext):
    answer = message.text
    data = await state.get_data()
    rec_id = data.get('rec_id')

    if answer == 'да':
        title: str = data.get('title')
        type_: str = data.get('type')
        ingredients = data.get('ingredients')
        description = data.get('description')
        tags = data.get('tags')
        author_id = data.get('author_id')
        ingredients = ', '.join(ingredients)
        if tags:
          tags = ' '.join(tags)
        else:
          tags = ''

        date = str(datetime.date.today())

        cursor.execute("INSERT INTO recipes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (rec_id, title, type_, description,
                                                                               ingredients, tags, author_id, date))

        cursor.execute("INSERT INTO feedback VALUES (?, ?, ?)", (rec_id, '', ''))

        if author_id:
            recipes: str = cursor.execute("SELECT recipes FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]
            if not recipes:
                await give_achievements(author_id, '📗')
            recipes: list = recipes.split()
            if len(recipes) == 9:
                await give_achievements(author_id, '📒')
            if len(recipes) == 24:
                await give_achievements(author_id, '📚')
            recipes.append(str(rec_id))
            recipes = ' '.join(recipes)
            cursor.execute("UPDATE profiles SET recipes = ? WHERE id = ?", (recipes, author_id))

            give_experience(author_id, 7, rec_id=int(rec_id))

            author_subscribers = \
                cursor.execute("SELECT subscribers FROM profiles WHERE id = ?", (author_id,)).fetchone()[0].split()

            try:
                text = f"Ваш рецепт <b>{title}</b> успешно прошел модерацию, теперь он виден всем пользователям"
                await bot.send_message(chat_id=author_id, text=text)
            except:
                pass

            for s in author_subscribers:
                author_name = cursor.execute("SELECT name FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]
                emoji = cursor.execute("SELECT emoji FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]

                notification_text = f"{emoji} <b>{author_name}</b> опубликовал(а) новый рецепт!"
                ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                    [
                        InlineKeyboardButton(text=f'👁‍🗨 Посмотреть', callback_data=f'посмотреть рецепт_{rec_id}')
                    ]
                ])

                await check_notifications_settings(int(s), notification_text, reply_markup=ikb_menu)

        connection.commit()

        await state.finish()

    if answer == 'нет':
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[[InlineKeyboardButton(text='❌ Выход',
                                                                                            callback_data=
                                                                                            'выход из добавления')]])
        try:
            os.remove(os.path.join(f'images/recipes/{rec_id}.jpg'))
        except Exception as e:
            print(e)

        await AddRecipe.author_id.set()
        await state.update_data(ingredients=None)
        await state.update_data(tags=None)
        await message.answer('Введите автора блюда:', reply_markup=ikb_menu)


@dp.callback_query_handler(state=AddRecipe.author_id, text='выход из добавления')
async def enter_author_id(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.answer_callback_query(str(call.id), text='Успешно', show_alert=True)


@dp.callback_query_handler(text_contains='посмотреть рецепт')
async def show_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    rec_id = int(call.data.split('_')[1])
    await get_recipe(call, [str(rec_id)], str(rec_id), call=True)



