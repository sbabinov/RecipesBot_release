import os
import time

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InputFile

from loader import dp, connection, cursor, bot
from states import Search
from handlers.menu.menu import get_recipe
from .achievements import give_achievements
from .functions_loader import get_ids, get_user_theme_picture
from ..users.experience import give_experience


def check_vip(user_id: int) -> int:
    user_vip_time = cursor.execute("SELECT VIP FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    now_time = int(time.time())

    if now_time >= user_vip_time:
        return 0
    return user_vip_time - now_time


def get_profile(user_id: int) -> str:
    data = cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,)).fetchone()

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
        progress = exp * 100 // 90
        rank = 'Мойщик продуктов'
    if exp >= 90:
        lvl = 5
        progress = exp * 100 // 120
        rank = 'Картофельных дел мастер'
    if exp >= 120:
        lvl = 6
        progress = exp * 100 // 160
        rank = 'Кондитер'
    if exp >= 160:
        lvl = 7
        progress = exp * 100 // 200
        rank = 'Повар'
    if exp >= 200:
        lvl = 8
        progress = exp * 100 // 250
        rank = 'Помощник шефа'
    if exp >= 250:
        lvl = 9
        progress = exp * 100 // 300
        rank = 'Шеф-повар'
    if exp >= 300:
        lvl = 10
        progress = exp * 100 // 350
        rank = 'Повар всех времен и народов'

    if exp >= 350:
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


@dp.callback_query_handler(text='поиск автора')
async def search_author(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='Выход из поиска по тегам')
                                        ]
                                    ],
                                    )
    await Search.enter_author.set()
    await call.message.delete()
    await call.message.answer("Введите юзернейм или часть юзернейма автора (минимум 3 символа):", reply_markup=ikb_menu)


@dp.message_handler(state=Search.enter_author)
async def start_search_author(message: types.Message, state: FSMContext):
    answer = message.text

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data='Назад из поиска автора')
                                        ]
                                    ],
                                    )
    if len(answer) < 3:
        await message.answer("Минимум 3 символа!", reply_markup=ikb_menu)
    else:
        user_username = cursor.execute("SELECT name FROM profiles WHERE id = ?", (message.from_user.id,)).fetchone()[0]
        authors_usernames = cursor.execute("SELECT name FROM profiles").fetchall()
        authors = []
        for u in authors_usernames:
            if answer.lower() in u[0].lower():
                recipes = cursor.execute("SELECT recipes FROM profiles WHERE name = ?", (u[0],)).fetchone()[0]
                if recipes and user_username != u[0]:
                    authors.append(u[0])

        if not authors:
            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                [
                                                    InlineKeyboardButton(text='❌ Выход',
                                                                         callback_data='Выход из поиска по тегам')
                                                ]
                                            ],
                                            )
            await message.answer("⛔️ Нет авторов с таким юзернеймом", reply_markup=ikb_menu)
        else:
            a = ''
            for author in authors:
                emoji = cursor.execute("SELECT emoji FROM profiles WHERE name = ?", (author,)).fetchone()[0]
                a += f"{emoji} <code>{author}</code>\n"
            message_text = f"<b>Найденные авторы:</b>\n\n" \
                           f"{a}"
            await message.answer(message_text)
            await message.answer("<i>Чтобы перейти в профиль автора, скопируйте и отправьте его юзернейм:</i>",
                                 reply_markup=ikb_menu)
            await Search.enter_author_username.set()


@dp.message_handler(state=Search.enter_author_username)
async def to_author_profile(message: types.Message, state: FSMContext):
    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data='Назад из поиска автора')
                                        ]
                                    ],
                                    )
    answer = message.text
    author_id = cursor.execute("SELECT id FROM profiles WHERE name = ?", (answer,)).fetchone()
    if not author_id:
        await message.answer("Нет пользователя с таким юзернеймом! Попробуйте другое имя:", reply_markup=ikb_menu)
    else:
        await state.finish()
        user_id = message.from_user.id
        user_subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
        user_subscriptions = user_subscriptions.split()

        if str(author_id[0]) in user_subscriptions:
            if_sub = 1
        else:
            if_sub = 0
        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(
                                                    text=f'{"🔴 Отписаться" if if_sub else "🟢 Подписаться"}',
                                                    callback_data=f'подписаться_{author_id[0]}_{0}_{1}___1'),
                                                InlineKeyboardButton(text='📚 Рецепты',
                                                                     callback_data=f'рецепты автора_'
                                                                                   f'{author_id[0]}_1_0__1')
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад',
                                                                     callback_data='Назад из поиска автора')
                                            ]
                                        ])
        profile = get_profile(author_id[0])
        await Search.author_profile.set()
        await message.answer(profile, reply_markup=ikb_menu)


@dp.callback_query_handler(text='Назад из поиска автора', state=Search.enter_author_username)
async def back_from_search_author(call: CallbackQuery, state: FSMContext):
    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='Выход из поиска по тегам')
                                        ]
                                    ],
                                    )
    await call.message.delete()
    await Search.enter_author.set()
    await call.message.answer("Введите юзернейм автора (часть юзернейма):", reply_markup=ikb_menu)


@dp.callback_query_handler(text='Назад из поиска автора', state=Search.enter_author)
async def back_from_search_author(call: CallbackQuery, state: FSMContext):
    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='Выход из поиска по тегам')
                                        ]
                                    ],
                                    )
    await call.message.delete()
    await Search.enter_author.set()
    await call.message.answer("Введите юзернейм автора (часть юзернейма):", reply_markup=ikb_menu)


@dp.callback_query_handler(text='Назад из поиска автора', state=Search.author_profile)
async def back_from_search_author(call: CallbackQuery):
    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Выход',
                                                                 callback_data='Выход из поиска по тегам')
                                        ]
                                    ],
                                    )
    await call.message.delete()
    await Search.enter_author.set()
    await call.message.answer("Введите юзернейм автора (часть юзернейма):", reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Назад в профиль автора', state=Search.author_profile)
async def back_to_author_profile(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    author_id = int(call.data.split('_')[1])
    user_subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    user_subscriptions = user_subscriptions.split()

    if str(author_id) in user_subscriptions:
        if_sub = 1
    else:
        if_sub = 0
    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(
                                                text=f'{"🔴 Отписаться" if if_sub else "🟢 Подписаться"}',
                                                callback_data=f'подписаться_{author_id}_{0}_{1}___1'),
                                            InlineKeyboardButton(text='📚 Рецепты',
                                                                 callback_data=f'рецепты автора_'
                                                                               f'{author_id}_1_0__1')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data='Назад из поиска автора')
                                        ]
                                    ])
    profile = get_profile(author_id)
    await Search.author_profile.set()
    await call.message.delete()
    await call.message.answer(profile, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='лайк', state=Search.author_profile)
async def like(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ids_id = int(call.data.split('_')[1])
    ids = get_ids(ids_id)

    rec_id = call.data.split('_')[2]
    ind = ids.index(rec_id)
    from_subs = call.data.split('_')[3]

    if call.data.split('_')[4] != '0' and call.data.split('_')[4]:
        save_back = f'_{call.data.split("_")[4]}_{call.data.split("_")[5]}'
    else:
        save_back = '_0'
    print(f'SAVE BACK: {save_back}')

    author_id = cursor.execute("SELECT author_id FROM recipes WHERE id = ?", (int(rec_id),)).fetchone()[0]
    if int(author_id) == call.from_user.id:
        await call.answer("Нельзя лайкать свои рецепты!")
    else:

        user_id = call.from_user.id

        likes = cursor.execute("SELECT likes FROM feedback WHERE rec_id = ?", (rec_id,)).fetchone()[0]
        user_likes = cursor.execute("SELECT likes FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()
        if not likes:
            likes = []
            count_likes = 0
        else:
            likes = likes.split(' ')
            count_likes = len(likes)

        if str(user_id) in likes:
            likes.remove(str(user_id))
            user_likes.remove(rec_id)
            new_likes = ' '.join(likes)
            user_likes = ' '.join(user_likes)
            count_likes -= 1
        else:
            likes.append(str(user_id))
            user_likes.append(rec_id)
            if len(user_likes) >= 40:
                await give_achievements(user_id, '😍')
            give_experience(user_id, 1, rec_id=int(rec_id), for_like=True)
            new_likes = ' '.join(likes)
            user_likes = ' '.join(user_likes)
            count_likes += 1

        cursor.execute("UPDATE feedback SET likes = ? WHERE rec_id = ?", (new_likes, rec_id))
        cursor.execute("UPDATE profiles SET likes = ? WHERE id = ?", (user_likes, user_id))
        connection.commit()

        favorites: str = cursor.execute("SELECT favorites FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
        favorites: list = favorites.split(' ')

        if_favorite = '💾✅' if str(rec_id) in favorites else '💾'

        like_color = '❤️' if str(call.from_user.id) in likes else '🤍'
        first_raw = [
            InlineKeyboardButton(text=f'{like_color} {count_likes if count_likes else ""}',
                                 callback_data=f'лайк_{ids_id}_{rec_id}_{from_subs}{save_back}'),
            InlineKeyboardButton(text=f'{if_favorite}',
                                 callback_data=f'избранное_{ids_id}_{rec_id}_{from_subs}{save_back}'),
        ]

        author_id = cursor.execute("SELECT author_id FROM recipes WHERE id = ?", (ids[ind],)).fetchone()[0]
        second_raw = []

        if author_id:
            second_raw = [InlineKeyboardButton(text='👤 Профиль автора',
                                               callback_data=f'к автору_{author_id}_'
                                                             f'{f"{ids_id}_{rec_id}" if save_back == "_0" else save_back[1:]}_{from_subs}')]
        if len(ids) > 1:
            first_raw += [
                InlineKeyboardButton(text='⬅️', callback_data=f'влево_{ids_id}_{rec_id}_{from_subs}_{0}{save_back}'),
                InlineKeyboardButton(text='➡️', callback_data=f'вправо_{ids_id}_{rec_id}_{from_subs}_{0}{save_back}'),
            ]
            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                first_raw,
                                                [
                                                    InlineKeyboardButton(text='📖 Открыть рецепт',
                                                                         callback_data=f'открыть рецепт_{rec_id}')
                                                ],
                                                second_raw,
                                            ],
                                            )
        else:
            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                first_raw,
                                                [
                                                    InlineKeyboardButton(text='📖 Открыть рецепт',
                                                                         callback_data=f'открыть рецепт_{rec_id}')
                                                ],
                                                second_raw,
                                            ],
                                            )
        chat_id = call.message.chat.id
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='избранное', state=Search.author_profile)
async def user_favorite(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id
    favorites: str = cursor.execute("SELECT favorites FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    rec_id = call.data.split('_')[2]

    ids_id = int(call.data.split('_')[1])
    ids = get_ids(ids_id)

    edit_message = call.message.message_id
    ind = ids.index(rec_id)
    from_subs = call.data.split('_')[3]

    author_id = cursor.execute("SELECT author_id FROM recipes WHERE id = ?", (int(rec_id),)).fetchone()[0]
    if int(author_id) == call.from_user.id:
        await call.answer("Нельзя добавлять в избранное свои рецепты!")
    else:
        users_favorites: str = cursor.execute("SELECT favorites FROM feedback WHERE rec_id = ?", (rec_id,)).fetchone()[0]
        users_favorites: list = users_favorites.split()

        favorites: list = favorites.split(' ')
        if str(rec_id) not in favorites:
            favorites.append(str(rec_id))
            users_favorites.append(str(user_id))
            give_experience(user_id, 3, rec_id=int(rec_id), for_favor=True)
            await call.answer("Добавлено в избранное")
        else:
            favorites.remove(str(rec_id))
            users_favorites.remove(str(user_id))
            await call.answer("Удалено из избранного")

        users_favorites = ' '.join(users_favorites)

        likes = cursor.execute("SELECT likes FROM feedback WHERE rec_id = ?", (rec_id,)).fetchone()[0]
        likes = likes.split()
        count_likes = len(likes)

        if_favorite = '💾✅' if str(rec_id) in favorites else '💾'
        like_color = '❤️' if str(call.from_user.id) in likes else '🤍'
        first_raw = [
            InlineKeyboardButton(text=f'{like_color} {count_likes if count_likes else ""}',
                                 callback_data=f'лайк_{ids_id}_{rec_id}_{from_subs}'),
            InlineKeyboardButton(text=f'{if_favorite}',
                                 callback_data=f'избранное_{ids_id}_{rec_id}_{from_subs}'),
        ]

        author_id = cursor.execute("SELECT author_id FROM recipes WHERE id = ?", (ids[ind],)).fetchone()[0]
        second_raw = []
        if author_id:
            str_ids = ' '.join(ids)
            second_raw = [InlineKeyboardButton(text='👤 Профиль автора',
                                               callback_data=f'Назад в профиль автора_{author_id}')]
        if len(ids) > 1:
            first_raw += [
                InlineKeyboardButton(text='⬅️', callback_data=f'влево_{ids_id}_{rec_id}_{from_subs}_{0}'),
                InlineKeyboardButton(text='➡️', callback_data=f'вправо_{ids_id}_{rec_id}_{from_subs}_{0}'),
            ]
            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                first_raw,
                                                [
                                                    InlineKeyboardButton(text='📖 Открыть рецепт',
                                                                         callback_data=f'открыть рецепт_{rec_id}')
                                                ],
                                                second_raw,
                                            ],
                                            )
        else:
            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                first_raw,
                                                [
                                                    InlineKeyboardButton(text='📖 Открыть рецепт',
                                                                         callback_data=f'открыть рецепт_{rec_id}')
                                                ],
                                                second_raw,
                                            ],
                                            )
        chat_id = call.message.chat.id
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message, reply_markup=ikb_menu)
        # await bot.answer_callback_query(str(call.id))

        favorites = ' '.join(favorites)

        cursor.execute("UPDATE profiles SET favorites = ? WHERE id = ?", (favorites, user_id))
        cursor.execute("UPDATE feedback SET favorites = ? WHERE rec_id = ?", (users_favorites, rec_id))
        connection.commit()


@dp.callback_query_handler(text_contains='вправо', state=Search.author_profile)
async def next_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ids_id = int(call.data.split('_')[1])
    ids = get_ids(ids_id)

    now_id = call.data.split('_')[2]
    from_subs = int(call.data.split('_')[3])
    from_profile = bool(int(call.data.split('_')[4]))

    author = cursor.execute("SELECT author_id FROM recipes WHERE id = ?", (now_id,)).fetchone()[0]

    await get_recipe(call, ids, now_id, change=True, call=True, next_rec=True,
                     msg_to_edit=call.message, from_subs=from_subs, from_profile=from_profile,
                     from_author_search=author)


@dp.callback_query_handler(text_contains='влево', state=Search.author_profile)
async def previous_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ids_id = int(call.data.split('_')[1])
    ids = get_ids(ids_id)

    now_id = call.data.split('_')[2]
    from_subs = int(call.data.split('_')[3])
    from_profile = int(call.data.split('_')[4])

    author = cursor.execute("SELECT author_id FROM recipes WHERE id = ?", (now_id,)).fetchone()[0]

    await get_recipe(call, ids, now_id, change=True, call=True, next_rec=False,
                     msg_to_edit=call.message, from_subs=from_subs, from_profile=from_profile,
                     from_author_search=author)


@dp.callback_query_handler(text_contains='открыть рецепт', state=Search.author_profile)
async def show_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❌ Закрыть', callback_data='Закрыть рецепт')
                                        ]
                                    ],
                                    )

    rec_id = int(call.data.split('_')[1])
    description: str = cursor.execute("SELECT description FROM recipes WHERE id = ?", (rec_id,)).fetchone()[0]
    text = f"<b><i>Приготовление:</i></b>\n" \
           f"{description}"
    await call.message.answer(text, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Закрыть рецепт', state=Search.author_profile)
async def close_recipe(call: CallbackQuery):
    await call.message.delete()


@dp.message_handler(state=Search.author_profile)
async def exit_from_state(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if message.text == '/menu':
        await state.finish()

        image = get_user_theme_picture(user_id, 'quizzes')
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
        chat_id = message.chat.id
        await bot.send_photo(chat_id, photo=image, reply_markup=ikb_menu)
    if message.text == '/help':
        await state.finish()

        image = get_user_theme_picture(user_id, 'quizzes')

        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                InlineKeyboardButton(text='❓ Вопрос', callback_data='репорт_вопрос'),
                InlineKeyboardButton(text='✏️ Предложение', callback_data='репорт_предложение'),
            ],
            [
                InlineKeyboardButton(text='🔊 Сообщить о проблеме бота', callback_data='репорт_проблема'),
            ]
        ])

        chat_id = message.chat.id

        await bot.send_photo(chat_id=chat_id, photo=image, reply_markup=ikb_menu)


