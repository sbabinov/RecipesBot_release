import os

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, InputMedia

from handlers.menu.settings import filter_recipes
from loader import dp, bot, connection, cursor
from handlers.menu.menu import get_recipe
from states import Subscription, Search
from .experience import give_experience
from ..menu.achievements import give_achievements
from ..menu.functions_loader import get_ids, get_user_theme_picture
from ..menu.vip import check_vip


def get_profile(user_id: int) -> str:
    data = cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,)).fetchone()
    print(data)
    user_id, username, gender, emoji, favorites, recipes, subscriptions, subscribers, likes, create_date, exp, vip, \
        get_vip_date, filters, achievements, articles = data

    lvl = 0
    progress = exp * 100 // 10
    rank = 'Новичок'

    if exp >= 10:
        lvl = 1
        progress = exp * 100 // 20
        rank = 'Стажер'
    if exp >= 20:
        lvl = 2
        progress = exp * 100 // 40
        rank = 'Доставщик'
    if exp >= 40:
        lvl = 3
        progress = exp * 100 // 60
        rank = 'Официант'
    if exp >= 60:
        lvl = 4
        progress = exp * 100 // 100
        rank = 'Мойщик продуктов'
    if exp >= 100:
        lvl = 5
        progress = exp * 100 // 150
        rank = 'Картофельных дел мастер'
    if exp >= 150:
        lvl = 6
        progress = exp * 100 // 210
        rank = 'Кондитер'
    if exp >= 210:
        lvl = 7
        progress = exp * 100 // 270
        rank = 'Повар'
    if exp >= 270:
        lvl = 8
        progress = exp * 100 // 350
        rank = 'Помощник шефа'
    if exp >= 350:
        lvl = 9
        progress = exp * 100 // 420
        rank = 'Шеф-повар'
    if exp >= 420:
        lvl = 10
        progress = exp * 100 // 500
        rank = 'Повар всех времен и народов'

    if exp >= 500:
        lvl = (exp // 50) + 4
        progress = (lvl - 4) * 50

    user_recipes = recipes.split()
    amount_likes = 0
    for r in user_recipes:
        likes = cursor.execute("SELECT likes FROM feedback WHERE rec_id = ?", (int(r),)).fetchone()[0]
        amount_likes += len(likes.split())

    bar = ''

    if progress > 12:
        bar += '🟩'
    if progress > 24:
        bar += '🟩'
    if progress > 37:
        bar += '🟩'
    if progress > 49:
        bar += '🟩'
    if progress > 62:
        bar += '🟩'
    if progress > 74:
        bar += '🟩'
    if progress > 87:
        bar += '🟩'

    bar += f'{"⬜️" * (8 - len(bar))}'

    profile = f"{emoji} <b>{username}</b> {emoji}\n\n" \
              f"    {'👑 VIP-пользователь' if check_vip(user_id) else ''}\n" \
              f"<b>{lvl} {bar} {lvl + 1}</b>\n" \
              f"<i>{rank} ({lvl} лвл)</i>\n" \
              f"--------------------------------------------\n" \
              f"📚 Написано рецептов: {len(recipes.split())}\n" \
              f"--------------------------------------------\n" \
              f"👤 Подписчики: {len(subscribers.split())}\n" \
              f"--------------------------------------------\n" \
              f"❤️ Лайки: {amount_likes}\n" \
              f"--------------------------------------------\n" \
              f"🕓 Профиль создан: {create_date}\n" \
              f"--------------------------------------------\n"

    return profile


@dp.callback_query_handler(text='профиль')
async def my_profile(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id
    profile = get_profile(user_id)

    subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    if not subscriptions:
        amount_subs = 0
    else:
        amount_subs = len(subscriptions.split())

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🍪 Мои рецепты', callback_data='мои рецепты'),
                                            # InlineKeyboardButton(text='🖌 Изменить', callback_data='изменить профиль')
                                            InlineKeyboardButton(text='🏆 Достижения', callback_data='достижения')
                                        ],
                                        [
                                            InlineKeyboardButton(text=f'🖇 Подписки ({amount_subs})',
                                                                 callback_data='мои подписки'),
                                            InlineKeyboardButton(text='👑 VIP', callback_data='настройки вип')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='назад_')
                                        ]
                                    ])
    await call.message.delete()
    await call.message.answer(profile, reply_markup=ikb_menu)


@dp.callback_query_handler(text='назад_')
async def back_from_my_profile(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'main_menu')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='📚 Рецепты', callback_data=f'Оецепты'),
                                            InlineKeyboardButton(text='👤 Мой профиль', callback_data='профиль'),

                                        ],
                                        [
                                            InlineKeyboardButton(text='❇️ Прочее', callback_data='прочее'),
                                            InlineKeyboardButton(text='⚙️ Настройки', callback_data='настройки'),
                                        ],
                                    ],
                                    )
    chat_id = call.message.chat.id
    await call.message.delete()
    await bot.send_photo(chat_id, photo=image, reply_markup=ikb_menu)


@dp.callback_query_handler(text='мои рецепты')
async def my_recipes(call: CallbackQuery):
    user_id = call.from_user.id

    recipes = cursor.execute("SELECT id FROM recipes WHERE author_id = ?", (user_id,)).fetchall()
    ids = []
    for i in recipes:
        ids.append(i[0])

    if not ids:
        await bot.answer_callback_query(str(call.id), text='У вас пока нет собственных рецептов!', show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))
        filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()

        ids = filter_recipes(ids, filters[0], filter_type=int(filters[1]))
        await get_recipe(call, ids, ids[0], call=True, from_profile=True)


@dp.callback_query_handler(text='назад из моих рецептов')
async def back_from_my_recipes(call: CallbackQuery):
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


@dp.callback_query_handler(text_contains='к автору')
async def to_author_profile(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    author_id = int(call.data.split('_')[1])
    ids_id = call.data.split('_')[2]
    now_id = call.data.split('_')[3]
    user_id = call.from_user.id
    profile = get_profile(author_id)
    try:
        from_subs = call.data.split('_')[4]
    except IndexError:
        from_subs = 1

    user_subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    user_subscriptions = user_subscriptions.split()

    if str(author_id) in user_subscriptions:
        if_sub = 1
    else:
        if_sub = 0

    if not int(from_subs):
        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text=
                                                                     f'{"🔴 Отписаться" if if_sub else "🟢 Подписаться"}',
                                                                     callback_data=
                                                                     f'подписаться_{author_id}_{1}_{if_sub}_{ids_id}_{now_id}'),
                                                InlineKeyboardButton(text='📚 Рецепты',
                                                                     callback_data=
                                                                     f'рецепты автора_{author_id}_{from_subs}_{ids_id}_{now_id}')
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад',
                                                                     callback_data=
                                                                     f'назад из профиля автора_{ids_id}_{now_id}'),
                                            ],
                                        ])
    else:
        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text=
                                                                     f'{"🔴 Отписаться" if if_sub else "🟢 Подписаться"}',
                                                                     callback_data=
                                                                     f'подписаться_{author_id}_{1}_{if_sub}_{ids_id}_{now_id}'),
                                                InlineKeyboardButton(text='📚 Рецепты',
                                                                     callback_data=
                                                                     f'рецепты автора_{author_id}_{from_subs}_{ids_id}_{now_id}')
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад',
                                                                     callback_data=
                                                                     f'назад из профиля автора_-_-'),
                                            ],
                                        ])

    await call.message.delete()
    await call.message.answer(profile, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='назад из профиля автора')
async def back_from_author_profile(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    if call.data.split('_')[1] == '-':
        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='❌ Выход',
                                                                     callback_data='выход из поиска подписок')
                                            ]
                                        ])
        await call.message.delete()
        await call.message.answer("<i>Скопируйте и отправьте юзернейм автора, "
                                  "профиль которого хотите посмотреть:</i>", reply_markup=ikb_menu)
        await Subscription.enter_author_username.set()
    else:
        ids_id = int(call.data.split('_')[1])
        ids = get_ids(ids_id)
        now_id = call.data.split('_')[2]

        await get_recipe(call, ids, now_id, call=True)
        await call.message.delete()


@dp.callback_query_handler(text_contains='подписаться')
async def subscribe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    try:
        a = call.data.split('_')[6]
        from_author_search = True
    except IndexError:
        from_author_search = False
    print(from_author_search)

    user_id = call.from_user.id
    author_id = int(call.data.split('_')[1])
    # ids = call.data.split('_')[4]
    # now_id = call.data.split('_')[5]

    user_subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    user_subscriptions = user_subscriptions.split()

    author_subscribers = cursor.execute("SELECT subscribers FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]
    author_subscribers = author_subscribers.split()

    if str(author_id) in user_subscriptions:
        if_sub = 1
    else:
        if_sub = 0

    if from_author_search:
        callback_data = f'подписаться_{author_id}_{0}_{1}___1'
        callback_data_2 = f'Назад из поиска автора'
        callback_data_3 = f'рецепты автора_{author_id}_1_0__1'
    elif int(call.data.split('_')[2]):
        ids_id = int(call.data.split('_')[1])

        now_id = call.data.split('_')[5]
        callback_data = f'подписаться_{author_id}_{1}_{if_sub}_{ids_id}_{now_id}'
        callback_data_2 = f'назад из профиля автора_{ids_id}_{now_id}'
        callback_data_3 = f'рецепты автора_{author_id}_0_{ids_id}_{now_id}'
    else:
        callback_data = f'подписаться_{author_id}_{0}_{1}'
        callback_data_2 = f'назад из профиля автора_-_-'
        callback_data_3 = f'рецепты автора_{author_id}_1_0'

    if not if_sub:
        user_subscriptions.append(str(author_id))
        author_subscribers.append(str(user_id))
        if_sub = 1
        if len(author_subscribers) >= 20:
            await give_achievements(author_id, '📈')
        give_experience(user_id, 3, for_sub=author_id)
    else:
        user_subscriptions.remove(str(author_id))
        author_subscribers.remove(str(user_id))
        if_sub = 0

    user_subscriptions = ' '.join(user_subscriptions)
    author_subscribers = ' '.join(author_subscribers)

    cursor.execute("UPDATE profiles SET subscriptions = ? WHERE id = ?", (user_subscriptions, user_id))
    cursor.execute("UPDATE profiles SET subscribers = ? WHERE id = ?", (author_subscribers, author_id))
    connection.commit()

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text=f'{"🔴 Отписаться" if if_sub else "🟢 Подписаться"}',
                                                                 callback_data=callback_data),
                                            InlineKeyboardButton(text='📚 Рецепты',
                                                                 callback_data=callback_data_3)
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data=
                                                                 callback_data_2)
                                        ] if not from_author_search else []
                                    ])

    profile = get_profile(author_id)

    await bot.edit_message_text(profile, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='подписаться', state=Search.author_profile)
async def subscribe(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id
    author_id = int(call.data.split('_')[1])

    user_subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    user_subscriptions = user_subscriptions.split()

    author_subscribers = cursor.execute("SELECT subscribers FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]
    author_subscribers = author_subscribers.split()

    if str(author_id) in user_subscriptions:
        if_sub = 1
    else:
        if_sub = 0

    callback_data = f'подписаться_{author_id}_{0}_{1}___1'
    callback_data_2 = f'Назад из поиска автора'
    callback_data_3 = f'рецепты автора_{author_id}_1_0__1'

    if not if_sub:
        user_subscriptions.append(str(author_id))
        author_subscribers.append(str(user_id))
        if_sub = 1
        if len(author_subscribers) >= 20:
            await give_achievements(author_id, '📈')
        give_experience(user_id, 3, for_sub=author_id)
    else:
        user_subscriptions.remove(str(author_id))
        author_subscribers.remove(str(user_id))
        if_sub = 0

    user_subscriptions = ' '.join(user_subscriptions)
    author_subscribers = ' '.join(author_subscribers)

    cursor.execute("UPDATE profiles SET subscriptions = ? WHERE id = ?", (user_subscriptions, user_id))
    cursor.execute("UPDATE profiles SET subscribers = ? WHERE id = ?", (author_subscribers, author_id))
    connection.commit()

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text=f'{"🔴 Отписаться" if if_sub else "🟢 Подписаться"}',
                                                                 callback_data=callback_data),
                                            InlineKeyboardButton(text='📚 Рецепты',
                                                                 callback_data=callback_data_3)
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data=
                                                                 callback_data_2)
                                        ]
                                    ])

    profile = get_profile(author_id)

    await bot.edit_message_text(profile, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='рецепты автора')
async def to_author_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id
    author_id = int(call.data.split('_')[1])
    from_subs = int(call.data.split('_')[2])

    try:
        a = call.data.split('_')[6]
        from_author_search = False
    except IndexError:
        from_author_search = True

    from_author_search = False

    recipes = cursor.execute("SELECT id FROM recipes WHERE author_id = ?", (author_id,)).fetchall()
    ids = []
    for i in recipes:
        ids.append(i[0])

    if not ids:
        await call.message.answer('У этого пользователя еще нет своих рецептов!')
    else:
        filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()

        ids = filter_recipes(ids, filters[0], filter_type=int(filters[1]))
        if from_author_search:
            await get_recipe(call, ids, ids[0], call=True, from_subs=from_subs, from_author_search=author_id)
        elif not call.data.split('_')[3] or call.data.split('_')[3] == '0':
            await get_recipe(call, ids, ids[0], call=True, from_subs=from_subs)
        else:
            await get_recipe(call, ids, ids[0], call=True, from_subs=from_subs, save_back=[call.data.split('_')[3],
                                                                                           call.data.split('_')[4]])
        await call.message.delete()


@dp.callback_query_handler(text_contains='рецепты автора', state=Search.author_profile)
async def to_author_recipe(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id
    author_id = int(call.data.split('_')[1])
    from_subs = int(call.data.split('_')[2])

    recipes = cursor.execute("SELECT id FROM recipes WHERE author_id = ?", (author_id,)).fetchall()
    ids = []
    for i in recipes:
        ids.append(i[0])

    if not ids:
        await call.message.answer('У этого пользователя еще нет своих рецептов!')
    else:
        filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()

        ids = filter_recipes(ids, filters[0], filter_type=int(filters[1]))
        await get_recipe(call, ids, ids[0], call=True, from_subs=from_subs, from_author_search=author_id)
        await call.message.delete()


@dp.callback_query_handler(text='мои подписки')
async def my_subscriptions(call: CallbackQuery):
    user_id = call.from_user.id
    subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='выход из поиска подписок')
                                        ]
                                    ])
    str_of_subs = ''
    num = 1
    for s in subscriptions:
        author_username = cursor.execute("SELECT name FROM profiles WHERE id = ?", (int(s),)).fetchone()[0]
        emoji = cursor.execute("SELECT emoji FROM profiles WHERE id = ?", (int(s),)).fetchone()[0]
        str_of_subs += f'{num}. {emoji} <code>{author_username}</code>\n'
        num += 1

    if not str_of_subs:
        await bot.answer_callback_query(str(call.id), text="У вас пока нет ни одной подписки!", show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))
        message = f"<b>🖇 Ваши подписки:</b>\n\n" \
                  f"{str_of_subs}"

        await call.message.answer(message)
        await call.message.answer("<i>Скопируйте и отправьте юзернейм автора, "
                                  "профиль которого хотите посмотреть:</i>", reply_markup=ikb_menu)
        await Subscription.enter_author_username.set()


@dp.message_handler(state=Subscription.enter_author_username)
async def enter_author_username(message: types.Message, state: FSMContext):
    answer = message.text
    user_id = message.from_user.id

    subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    author_id = cursor.execute("SELECT id FROM profiles WHERE name = ?", (answer,)).fetchone()

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='выход из поиска подписок')
                                        ]
                                    ])
    if author_id is None:
        await message.answer("Такого пользователя нет в ваших подписках! Введите другой юзернейм:",
                             reply_markup=ikb_menu)
    else:
        if str(author_id[0]) not in subscriptions:
            await message.answer("Такого пользователя нет в ваших подписках! Введите другой юзернейм:",
                                 reply_markup=ikb_menu)
        else:
            await state.finish()
            author_id = author_id[0]
            author_profile = get_profile(author_id)
            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                [
                                                    InlineKeyboardButton(
                                                        text='🔴 Отписаться',
                                                        callback_data=f'подписаться_{author_id}_{0}_{1}'),
                                                    InlineKeyboardButton(text='📚 Рецепты',
                                                                         callback_data=f'рецепты автора_{author_id}_1_0')
                                                ],
                                                [
                                                    InlineKeyboardButton(text='↩️ Назад',
                                                                         callback_data=f'назад из профиля автора_-_-'),
                                                ],
                                            ])
            # f'рецепты автора_{author_id}_{from_subs}_{ids}_{now_id}
            await message.answer(author_profile, reply_markup=ikb_menu)


@dp.callback_query_handler(text='выход из поиска подписок', state=Subscription.enter_author_username)
async def exit_from_subs(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id
    profile = get_profile(user_id)

    subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    if not subscriptions:
        amount_subs = 0
    else:
        amount_subs = len(subscriptions.split())

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🍪 Мои рецепты', callback_data='мои рецепты'),
                                            InlineKeyboardButton(text='🏆 Достижения', callback_data='достижения')
                                        ],
                                        [
                                            InlineKeyboardButton(text=f'🖇 Подписки ({amount_subs})',
                                                                 callback_data='мои подписки'),
                                            InlineKeyboardButton(text='👑 VIP', callback_data='настройки вип')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='назад_')
                                        ]
                                    ])

    await state.finish()
    await call.message.delete()
    await call.message.answer(profile, reply_markup=ikb_menu)
