from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
import os

from handlers.menu.settings import filter_recipes
from loader import dp, cursor, bot
from states import Search
from handlers.menu.menu import get_recipe
from .functions_loader import get_user_theme_picture


tags = [
    'быстрое',
    'полезное',
    'сладкое',
    'для жары',
    'без духовки',
    'для всей семьи',
    'вегетарианское',
    'постное',
    'питательное',
    'новый год',
    'острое'
]


async def exit_from_tags(call, state=None):
    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'search')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🔤 По названию',
                                                                 callback_data=f'по названию'),
                                            InlineKeyboardButton(text='📝 По тегам', callback_data='по тегам'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='🌶 По ингредиентам',
                                                                 callback_data='по ингредиентам'),
                                            InlineKeyboardButton(text='👤 Поиск автора', callback_data='поиск автора'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='назад'),
                                        ]
                                    ],
                                    )
    if state:
        await state.finish()
    await call.message.delete()
    await bot.send_photo(chat_id=call.message.chat.id, photo=image, reply_markup=ikb_menu)


@dp.callback_query_handler(text='по тегам')
async def search_by_tags(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    global tags
    t = ''
    n = 1
    for tag in tags:
        t += f'{n}. <code>{tag}</code>\n'
        n += 1
    message = f"#️⃣ <b>Список тегов:</b>\n\n" \
              f"{t}"

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='Выход из поиска по тегам')
                                        ]
                                    ],
                                    )
    await call.message.delete()
    await call.message.answer(message)
    await call.message.answer('<i>Введите нужный тег из предложенного списка:</i>', reply_markup=ikb_menu)
    await Search.enter_tags.set()


@dp.message_handler(state=Search.enter_tags)
async def start_search_by_tags(message: types.Message, state: FSMContext):
    global tags
    answer = message.text
    user_id = message.from_user.id

    data = await state.get_data()
    t = data.get('enter_tags')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='Выход из поиска по тегам')
                                        ]
                                    ],
                                    )
    if answer not in tags:
        await message.answer("<i>Выберите тег из списка!</i>", reply_markup=ikb_menu)
    elif t and answer in t:
        await message.answer("Вы уже выбрали такой тег!", reply_markup=ikb_menu)
    else:
        if not t:
            await state.update_data(enter_tags=[answer])
        else:
            await state.update_data(enter_tags=t + [answer])

        data = await state.get_data()
        t = data.get('enter_tags')

        if t and len(t) == 3:
            await state.finish()

            recipes = []
            d = cursor.execute("SELECT tags, id FROM recipes").fetchall()
            for rec_tag in d:
                add = True
                for tag in t:
                    if tag not in rec_tag[0]:
                        add = False
                if add:
                    recipes.append(rec_tag[1])

            recipes = list(set(recipes))
            await state.finish()
            if not recipes:
                ikb_menu = InlineKeyboardMarkup(row_width=1,
                                                inline_keyboard=[
                                                    [
                                                        InlineKeyboardButton(text='↩️ Назад',
                                                                             callback_data='НазаД из поиска по тегам'),
                                                        InlineKeyboardButton(text='❌ Выход',
                                                                             callback_data='Выход из поиска по тегам')
                                                    ],

                                                ],
                                                )
                await message.answer("⛔️ Нет рецептов с такими тегами", reply_markup=ikb_menu)
            else:
                filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()

                recipes = filter_recipes(recipes, filters[0], filter_type=int(filters[1]))
                await get_recipe(message, recipes, recipes[0])
        else:

            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                [
                                                    InlineKeyboardButton(text='✅ Применить',
                                                                         callback_data='Применить теги'),
                                                    InlineKeyboardButton(text='❌ Выход',
                                                                         callback_data='Выход из поиска по тегам')
                                                ],

                                            ],
                                            )

            await message.answer(f"Тег добавлен. Если хотите добавить больше тегов, "
                                 f"вводите их дальше (максимум тегов - 3)\n\n"
                                 f"Текущие теги: <i>{', '.join(t)}</i>",
                                 reply_markup=ikb_menu)


@dp.callback_query_handler(text='Применить теги', state=Search.enter_tags)
async def apply_tags(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    data = await state.get_data()
    t = data.get('enter_tags')
    recipes = []

    d = cursor.execute("SELECT tags, id FROM recipes").fetchall()
    for rec_tag in d:
        add = True
        for tag in t:
            if tag not in rec_tag[0]:
                add = False
        if add:
            recipes.append(rec_tag[1])

    recipes = list(set(recipes))
    print(list(set(recipes)))
    await state.finish()
    if not recipes:
        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='↩️ Назад',
                                                                     callback_data='НазаД из поиска по тегам'),
                                                InlineKeyboardButton(text='❌ Выход',
                                                                     callback_data='Выход из поиска по тегам')
                                            ],

                                        ],
                                        )
        await call.message.answer("⛔️ Нет рецептов с такими тегами", reply_markup=ikb_menu)
    else:
        filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()

        recipes = filter_recipes(recipes, filters[0], filter_type=int(filters[1]))
        await get_recipe(call, recipes, recipes[0], call=True)


@dp.callback_query_handler(text='Выход из поиска по тегам', state=Search.enter_author)
async def exit_from_search_by_tags(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))
    await exit_from_tags(call, state=state)


@dp.callback_query_handler(text='Выход из поиска по тегам', state=Search.enter_tags)
async def exit_from_search_by_tags(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))
    await exit_from_tags(call, state=state)


@dp.callback_query_handler(text='Выход из поиска по тегам', state=Search.enter_ingredients)
async def exit_from_search_by_tags(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))
    await exit_from_tags(call, state=state)


@dp.callback_query_handler(text='Выход из поиска по тегам')
async def exit_from_search_by_tags(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    await exit_from_tags(call)


@dp.callback_query_handler(text='НазаД из поиска по тегам')
async def back_from_search_by_tags(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    global tags
    t = ''
    n = 1
    for tag in tags:
        t += f'{n}. <code>{tag}</code>\n'
        n += 1
    message = f"#️⃣ <b>Список тегов:</b>\n\n" \
              f"{t}"

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='Выход из поиска по тегам')
                                        ]
                                    ],
                                    )

    await call.message.answer(message)
    await call.message.answer('<i>Введите нужный тег из предложенного списка:</i>', reply_markup=ikb_menu)
    await Search.enter_tags.set()







