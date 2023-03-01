import asyncio
import os.path

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InputFile, InputMedia

from loader import dp, connection, cursor, bot, storage
from aiogram.dispatcher.filters import Command
from aiogram import types
from states import Search
from .settings import filter_recipes
from .achievements import give_achievements
from ..users.experience import give_experience
from .functions_loader import get_ids, create_ids_entry, get_user_theme_picture
from .menu import get_recipe


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_inline_menu_for_categories(user_id: int):
    current_categories = \
        cursor.execute("SELECT categories FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()[0].split(',')

    categories = ['супы', '2-е блюда', 'закуски', 'салаты', 'выпечка', 'соусы', 'заготовки', 'десерты', 'напитки']
    dict_categories = {
        'супы': '🫕',
        '2-е блюда': '🍛',
        'закуски': '🥪',
        'салаты': '🥗',
        'выпечка': '🍕',
        'соусы': '🫖',
        'заготовки': '🥒',
        'десерты': '🍩',
        'напитки': '🍹'
    }

    inline_keyboard = []
    row = []
    for c in categories:
        if c in current_categories:
            emoji = '✅'
        else:
            emoji = dict_categories[c]
        button = InlineKeyboardButton(text=f'{emoji} {c.capitalize()}', callback_data=f'кат_{c}')
        row.append(button)
        if len(row) == 3:
            inline_keyboard.append(row)
            row = []

    inline_keyboard.append([InlineKeyboardButton(text='↩️ Назад', callback_data='критерии')])

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=inline_keyboard)

    return ikb_menu


def get_inline_menu_for_tags(user_id: int):
    current_tags = \
        cursor.execute("SELECT tags FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()[0].split(',')

    tags = [
        'быстрое',
        'полезное',
        'сладкое',
        'для жары',
        'для семьи',
        'вегетарианское',
        'постное',
        'питательное',
        'острое'
    ]

    inline_keyboard = []
    row = []
    for t in tags:
        if t in current_tags:
            emoji = '✅'
        else:
            emoji = '#️⃣'
        button = InlineKeyboardButton(text=f'{emoji} {t.capitalize()}', callback_data=f'тег_{t}')
        row.append(button)
        if len(row) == 3:
            inline_keyboard.append(row)
            row = []

    inline_keyboard.append([InlineKeyboardButton(text='↩️ Назад', callback_data='критерии')])

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=inline_keyboard)

    return ikb_menu


def get_inline_menu_for_ingredients(user_id: int):
    current_ingredients = \
        cursor.execute("SELECT ingredients FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()[0].split(',')

    dict_ingredients = {
        'яйца': '🥚',
        'сыр': '🧀',
        'рыба': '🐟',
        'молоко': '🥛',
        'грибы': '🍄',
        'картофель': '🥔',
        # '': '',
        # '': '',
        # '': '',
        # '': '',
        # '': '',

    }

    inline_keyboard = []
    row = []
    for t in [i for i in dict_ingredients.keys()]:
        if t in current_ingredients:
            emoji = '✅'
        else:
            emoji = dict_ingredients[t]
        button = InlineKeyboardButton(text=f'{emoji} {t.capitalize()}', callback_data=f'инг_{t}')
        row.append(button)
        if len(row) == 3:
            inline_keyboard.append(row)
            row = []

    inline_keyboard.append([InlineKeyboardButton(text='❇️ Добавить', callback_data='добавить-инг')])
    inline_keyboard.append([InlineKeyboardButton(text='↩️ Назад', callback_data='критерии')])

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=inline_keyboard)

    return ikb_menu


@dp.callback_query_handler(text='поиск')
async def search(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    if_exists = cursor.execute("SELECT * FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()
    if not if_exists:
        cursor.execute("INSERT INTO search_criteria VALUES (?, ?, ?, ?, ?)", (user_id, '', '', '', ''))
        connection.commit()

        r_title, categories, ingredients, tags = '', '', '', ''
    else:
        user_id, r_title, ingredients, tags, categories = if_exists

    if not r_title and not categories and not ingredients and not tags:
        emoji = '📝'
    else:
        emoji = '✅'

    image = get_user_theme_picture(user_id, 'search')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🔍 Найти',
                                                                 callback_data=f'найти'),
                                            InlineKeyboardButton(text=f'{emoji} Критерии', callback_data='критерии'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='❌ Сбросить критерии',
                                                                 callback_data='Сбросить критерии'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='Оецепты'),
                                        ]
                                    ]
                                    )

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    media = InputMedia(media=image)
    await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='критерии')
async def search_criteria(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id

    if_exists = cursor.execute("SELECT * FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()
    if not if_exists:
        cursor.execute("INSERT INTO search_criteria VALUES (?, ?, ?, ?, ?)", (user_id, '', '', '', ''))
        connection.commit()

        r_title, categories, ingredients, tags = '', '', '', ''
    else:
        user_id, r_title, ingredients, tags, categories = if_exists

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text=f'{"🔤" if not r_title else "✅"} Название',
                                                                 callback_data=f'название'),
                                            InlineKeyboardButton(text=f'{"📜" if not categories else "✅"} Категории',
                                                                 callback_data='категории'),
                                        ],
                                        [
                                            InlineKeyboardButton(text=f'{"🌶" if not ingredients else "✅"} Ингредиенты',
                                                                 callback_data=f'ингредиенты'),
                                            InlineKeyboardButton(text=f'{"#️⃣" if not tags else "✅"} Теги',
                                                                 callback_data='теги'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='поиск'),
                                        ]
                                    ]
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='название')
async def title(call: CallbackQuery):
    await call.answer()

    await Search.enter_title.set()
    msg = await call.message.answer("🔤 Введите название (или часть названия) нужного блюда:")

    state = FSMContext(storage, call.message.chat.id, call.from_user.id)
    await state.update_data(message_to_edit=msg.message_id)


@dp.message_handler(state=Search.enter_title)
async def enter_title(message: types.Message, state: FSMContext):
    answer = message.text

    user_id = message.from_user.id
    data = await state.get_data()
    msg_id = data.get('message_to_edit')

    cursor.execute("UPDATE search_criteria SET title = ? WHERE user_id = ?", (answer, user_id))
    connection.commit()

    chat_id = message.chat.id

    await state.finish()
    await message.delete()
    await bot.delete_message(chat_id, msg_id)
    msg = await message.answer("✅ Успешно изменено!")
    await asyncio.sleep(2)
    await msg.delete()


@dp.callback_query_handler(text='категории')
async def change_categories(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id

    ikb_menu = get_inline_menu_for_categories(user_id)

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='кат_')
async def change_categories(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id
    category = call.data.split('_')[1]

    current_categories = \
        cursor.execute("SELECT categories FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()[0]
    if not current_categories:
        current_categories = []
    else:
        current_categories = current_categories.split(',')

    if category in current_categories:
        current_categories.remove(category)
    else:
        current_categories.append(category)

    new_categories = ','.join(current_categories)

    cursor.execute("UPDATE search_criteria SET categories = ? WHERE user_id = ?", (new_categories, user_id))
    connection.commit()

    ikb_menu = get_inline_menu_for_categories(user_id)

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='теги')
async def change_categories(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id

    ikb_menu = get_inline_menu_for_tags(user_id)

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='тег_')
async def change_categories(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id
    category = call.data.split('_')[1]

    current_tags = \
        cursor.execute("SELECT tags FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()[0]
    if not current_tags:
        current_tags = []
    else:
        current_tags = current_tags.split(',')

    if category in current_tags:
        current_tags.remove(category)
    else:
        current_tags.append(category)

    new_tags = ','.join(current_tags)

    cursor.execute("UPDATE search_criteria SET tags = ? WHERE user_id = ?", (new_tags, user_id))
    connection.commit()

    ikb_menu = get_inline_menu_for_tags(user_id)

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='ингредиенты')
async def change_categories(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id

    ikb_menu = get_inline_menu_for_ingredients(user_id)

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='инг_')
async def change_categories(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id
    ingredient = call.data.split('_')[1]

    current_ingredients = \
        cursor.execute("SELECT ingredients FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()[0]
    if not current_ingredients:
        current_ingredients = []
    else:
        current_ingredients = current_ingredients.split(',')

    if ingredient in current_ingredients:
        current_ingredients.remove(ingredient)
    else:
        current_ingredients.append(ingredient)

    new_ingredients = ','.join(current_ingredients)

    cursor.execute("UPDATE search_criteria SET ingredients = ? WHERE user_id = ?", (new_ingredients, user_id))
    connection.commit()

    ikb_menu = get_inline_menu_for_ingredients(user_id)

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='добавить-инг')
async def add_ingredient(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id
    chat_id = call.message.chat.id

    state = FSMContext(storage, chat_id, user_id)

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='выйти из добавления ингредиентов')
                                        ],
                                    ]
                                    )

    msg = await call.message.answer("🌶 Напишите название (или часть названия) ингредиента, "
                                    "который хотите включить в критерии поиска (максимум 5 ингредиентов):",
                                    reply_markup=ikb_menu)
    await state.update_data(message_to_edit=msg.message_id)
    await Search.enter_ingredients.set()


@dp.message_handler(state=Search.enter_ingredients)
async def enter_ingredients(message: types.Message, state: FSMContext):
    answer = message.text
    user_id = message.from_user.id
    chat_id = message.chat.id

    data = await state.get_data()
    current_ingredients = data.get('enter_ingredients')
    msg_id = data.get('message_to_edit')
    if not current_ingredients:
        current_ingredients = []

    current_ingredients.append(answer)
    current_ingredients = [i.lower() for i in current_ingredients]

    await message.delete()
    await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    if len(current_ingredients) >= 5:
        current_ingredients = ','.join(current_ingredients)

        cursor.execute("UPDATE search_criteria SET ingredients = ? WHERE user_id = ?", (current_ingredients, user_id))
        connection.commit()

        await state.finish()
        msg = await message.answer("✅ Ингредиенты успешно добавлены!")
        await asyncio.sleep(1.5)
        await msg.delete()
    else:
        await state.update_data(enter_ingredients=current_ingredients)

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='✅ Применить',
                                                                     callback_data='применить ингредиенты'),
                                                InlineKeyboardButton(text='❌ Выход',
                                                                     callback_data='выйти из добавления ингредиентов')
                                            ],

                                        ],
                                        )

        msg = await message.answer(f"🌶 Напишите название (или часть названия) ингредиента, "
                                   f"который хотите включить в критерии поиска:\n\n"
                                   f"<i>Текущие ингредиенты: {', '.join(current_ingredients)}</i>",
                                   reply_markup=ikb_menu)
        await state.update_data(message_to_edit=msg.message_id)


@dp.callback_query_handler(text='применить ингредиенты', state=Search.enter_ingredients)
async def add_ingredient(call: CallbackQuery, state: FSMContext):
    await call.answer()

    user_id = call.from_user.id

    data = await state.get_data()
    ingredients = data.get('enter_ingredients')
    ingredients = ','.join(ingredients)

    cursor.execute("UPDATE search_criteria SET ingredients = ? WHERE user_id = ?", (ingredients, user_id))
    connection.commit()

    await call.message.delete()
    await state.finish()
    msg = await call.message.answer("✅ Ингредиенты успешно добавлены!")
    await asyncio.sleep(1.5)
    await msg.delete()


@dp.callback_query_handler(text='выйти из добавления ингредиентов', state=Search.enter_ingredients)
async def exit_from_adding_ingredients(call: CallbackQuery, state: FSMContext):
    await call.answer("❌ Отменено", show_alert=True)

    await state.finish()
    await call.message.delete()


@dp.callback_query_handler(text='найти')
async def start_search(call: CallbackQuery):
    user_id = call.from_user.id

    data = cursor.execute("SELECT * FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()
    if not data:
        user_id, r_title, ingredients, tags, categories = user_id, '', '', '', ''
    else:
        user_id, r_title, ingredients, tags, categories = data

    if not r_title and not ingredients and not tags and not categories:
        await call.answer("🔍 Задайте критерии поиска", show_alert=True)
    else:
        count = 0
        categories = categories.replace('2-е блюда', 'вторые блюда')
        categories = categories.split(',')
        ingredients = ingredients.replace('яйца', 'яйц').replace('сыр', 'сыр ').replace('рыба', 'рыб')
        ingredients = ingredients.split(',')
        tags = tags.split(',')

        for t in tags:
            if t == 'для семьи':
                tags[count] = 'для всей семьи'
            count += 1

        recipes = []
        data = cursor.execute("SELECT title, ingredients, tags, type, id FROM recipes").fetchall()
        for entry in data:
            add = True
            for tag in tags:
                if tag not in entry[2] and tag != '':
                    add = False
                    break
            if add:
                if r_title.lower().replace('ё', 'е') not in entry[0].lower().replace('ё', 'е'):
                    add = False
                if add:
                    if entry[3] not in categories and categories != ['']:
                        add = False
                    if add:
                        for ingredient in ingredients:
                            if ingredient.lower().replace('ё', 'е') not in \
                                    entry[1].lower().replace('ё', 'е') and ingredient != '':
                                if 'грибы' in ingredients:
                                    if 'гриб' not in entry[0].lower():
                                        add = False
                                        break
                                elif 'картофель' in ingredient:
                                    if 'картофель' not in entry[1].lower().replace('ё', 'е') and 'картошка' not in \
                                            entry[1].lower().replace('ё', 'е'):
                                        add = False
                                        break
                                else:
                                    add = False
                                    break
            if add:
                recipes.append(entry[4])
        if recipes:
            await call.answer()

            filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()

            recipes = filter_recipes(recipes, filters[0], filter_type=int(filters[1]))
            await get_recipe(call, recipes, recipes[0], call=True)
        else:
            await call.answer("❌ Нет рецептов с такими критериями!", show_alert=True)


@dp.callback_query_handler(text='Сбросить критерии')
async def reset_criteria(call: CallbackQuery):
    user_id = call.from_user.id

    cursor.execute("DELETE FROM search_criteria WHERE user_id = ?", (user_id,))
    cursor.execute("INSERT INTO search_criteria VALUES (?, ?, ?, ?, ?)", (user_id, '', '', '', ''))
    connection.commit()

    data = cursor.execute("SELECT * FROM search_criteria WHERE user_id = ?", (user_id,)).fetchone()
    user_id, r_title, ingredients, tags, categories = data

    if not r_title and not categories and not ingredients and not tags:
        emoji = '📝'
    else:
        emoji = '✅'

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🔍 Найти',
                                                                 callback_data=f'найти'),
                                            InlineKeyboardButton(text=f'{emoji} Критерии', callback_data='критерии'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='❌ Сбросить критерии',
                                                                 callback_data='Сбросить критерии'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='Оецепты'),
                                        ]
                                    ]
                                    )

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await call.answer("✅ Критерии успешно сброшены", show_alert=True)
    await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=ikb_menu)





