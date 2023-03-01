import os.path

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InputFile, InputMedia

from loader import dp, connection, cursor, bot
from aiogram.dispatcher.filters import Command
from aiogram import types
from states import Search
from .settings import filter_recipes
from .achievements import give_achievements
from ..users.experience import give_experience
from .functions_loader import get_ids, create_ids_entry, get_user_theme_picture

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@dp.message_handler(Command('menu'))
async def show_menu(message: types.Message):
    user_id = message.from_user.id

    if_exists = cursor.execute("SELECT name FROM profiles WHERE id = ?", (user_id,)).fetchone()
    if not if_exists:
        await message.answer("Сначала зарегистрируйтесь!\n"
                             "/start")

    image = get_user_theme_picture(user_id, 'main_menu')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='📚 Рецепты', callback_data=f'Оецепты'),
                                            InlineKeyboardButton(text='👤 Мой профиль', callback_data='профиль'),

                                        ],
                                        [
                                            # InlineKeyboardButton(text='❤️ Здоровье', callback_data='здоровье'),
                                            InlineKeyboardButton(text='❇️ Прочее', callback_data='прочее'),
                                            InlineKeyboardButton(text='⚙️ Настройки', callback_data='настройки'),
                                        ],
                                        # [
                                        #     InlineKeyboardButton(text='⚙️ Настройки', callback_data='настройки'),
                                        # ]
                                    ],
                                    )
    chat_id = message.chat.id
    await bot.send_photo(chat_id, photo=image, reply_markup=ikb_menu)


@dp.callback_query_handler(text='Оецепты')
async def recipes(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'recipes')
    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🔍 Поиск', callback_data=f'поиск'),
                                            # InlineKeyboardButton(text='📜 Категории', callback_data='категории'),
                                            InlineKeyboardButton(text='🏅 Топ', callback_data='топ'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='📕 Добавить рецепт',
                                                                 callback_data='добавить рецепт'),
                                            InlineKeyboardButton(text='💾 Избранное', callback_data='все fav')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='назад'),
                                        ]
                                    ],
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    media = InputMedia(media=image)
    await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='назад')
async def back(call: CallbackQuery):
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
                                    ]
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    media = InputMedia(media=image)
    await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='по названию')
async def back(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    await call.message.answer('<i>Введите название нужного блюда (или часть названия):</i>')
    await Search.enter_title.set()


async def get_recipe(message, ids: list, now_id: str, change: bool = False, call: bool = False, next_rec: bool = None,
                     msg_to_edit=None, from_profile: bool = False, from_subs: int = 0, save_back: list = None,
                     from_author_search: int = 0):
    user_id: int = message.from_user.id

    str_ids = ' '.join([str(i) for i in ids])
    if not cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)", (str_ids, 'recipes')).fetchone():
        ids_id = create_ids_entry(ids, 'recipes')
    else:
        ids_id = cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)",
                                (str_ids, 'recipes')).fetchone()[0]

    if next_rec is not None:
        if next_rec:
            try:
                now_id = ids[ids.index(now_id) + 1]
            except IndexError:
                now_id = ids[0]
        else:
            try:
                now_id = ids[ids.index(now_id) - 1]
            except IndexError:
                now_id = ids[-1]

    ind = ids.index(now_id)

    title = cursor.execute("SELECT title FROM recipes WHERE id = ?", (ids[ind],)).fetchone()[0]
    type_ = cursor.execute("SELECT type FROM recipes WHERE id = ?", (ids[ind],)).fetchone()[0]
    ingredients = cursor.execute("SELECT ingredients FROM recipes WHERE id = ?", (ids[ind],)).fetchone()[0]
    description = cursor.execute("SELECT description FROM recipes WHERE id = ?", (ids[ind],)).fetchone()[0]
    author_id = cursor.execute("SELECT author_id FROM recipes WHERE id = ?", (ids[ind],)).fetchone()[0]

    likes = cursor.execute("SELECT likes FROM feedback WHERE rec_id = ?", (ids[ind],)).fetchone()[0]
    if not likes:
        count_likes = 0
    else:
        likes = likes.split(' ')
        count_likes = len(likes)

    like_color = '❤️' if str(message.from_user.id) in likes else '🤍'

    favorites: str = cursor.execute("SELECT favorites FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    favorites: list = favorites.split(' ')

    if_favorite = '💾✅' if str(now_id) in favorites else '💾'

    first_raw = [
        InlineKeyboardButton(text=f'{like_color} {count_likes if count_likes else ""}',
                             callback_data=f'лайк_{ids_id}_{now_id}_{from_subs}'
                                           f'_{f"{save_back[0]}_{save_back[1]}" if save_back else "0"}'),
        InlineKeyboardButton(text=f'{if_favorite}',
                             callback_data=f'избранное_{ids_id}_{now_id}_{from_subs}'
                                           f'_{f"{save_back[0]}_{save_back[1]}" if save_back else "0"}')
    ]
    second_raw = []

    if author_id and not from_profile and author_id != user_id:
        if from_author_search:
            second_raw = [InlineKeyboardButton(text='👤 Профиль автора',
                                               callback_data=f'Назад в профиль автора_{from_author_search}')]
        elif not save_back:
            second_raw = [InlineKeyboardButton(text='👤 Профиль автора',
                                               callback_data=f'к автору_{author_id}_{ids_id}_{now_id}_{from_subs}')]
        else:
            second_raw = [InlineKeyboardButton(text='👤 Профиль автора',
                                               callback_data=f'к автору_{author_id}_{save_back[0]}_{save_back[1]}_'
                                                             f'{from_subs}')]
    if from_profile:
        amount_favorites = cursor.execute("SELECT favorites FROM feedback WHERE rec_id = ?", (now_id,)).fetchone()[0]
        amount_favorites = len(amount_favorites.split())
        second_raw = [InlineKeyboardButton(text='↩️ Назад', callback_data='назад из моих рецептов')]
        first_raw = [
            InlineKeyboardButton(text=f'{like_color} {count_likes if count_likes else ""}',
                                 callback_data=f'лайк_{ids_id}_{now_id}_{from_subs}'
                                               f'_{f"{save_back[0]}_{save_back[1]}" if save_back else "0"}'),
            InlineKeyboardButton(text=f'{if_favorite} {amount_favorites if amount_favorites else ""}',
                                 callback_data=f'избранное_{ids_id}_{now_id}_{from_subs}'
                                               f'_{f"{save_back[0]}_{save_back[1]}" if save_back else "0"}')
        ]
    from_profile = 1 if from_profile else 0
    if len(ids) > 1:
        if save_back:
            callback_data = \
                f'влево_{ids_id}_{now_id}_{from_subs}_{from_profile}_{save_back[0]}_{save_back[1]}'
            callback_data_2 = \
                f'вправо_{ids_id}_{now_id}_{from_subs}_{from_profile}_{save_back[0]}_{save_back[1]}'
        else:
            callback_data = f'влево_{ids_id}_{now_id}_{from_subs}_{from_profile}_0'
            callback_data_2 = f'вправо_{ids_id}_{now_id}_{from_subs}_{from_profile}_0'
        first_raw += [
                InlineKeyboardButton(text='⬅️',
                                     callback_data=callback_data),
                InlineKeyboardButton(text='➡️',
                                     callback_data=callback_data_2),
        ]

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[

                                            first_raw,
                                            [
                                                InlineKeyboardButton(text='📖 Открыть рецепт',
                                                                     callback_data=f'открыть рецепт_{now_id}')
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
                                                                     callback_data=f'открыть рецепт_{now_id}')
                                            ],
                                            second_raw,

                                        ],
                                        )
    date_ = cursor.execute("SELECT date FROM recipes WHERE id = ?", (now_id,)).fetchone()[0]
    date = f'  |  {date_}'
    if author_id == user_id:
        author = '|  <i>Это ваш рецепт!</i>'
    elif author_id:
        author = cursor.execute("SELECT name FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]
        author = f'|  <i>Автор: <code>{author}</code></i>'
    else:
        author = ''
        date = f'|  {date_}'
    rec_number = ids.index(now_id) + 1

    text_ingredients = ''
    for i in ingredients.split(', '):
        if i.startswith('*'):
            text_ingredients += f"\n<i>{i[1:].capitalize()}:</i>\n"
        else:
            text_ingredients += f"- {i.lower()}\n"

    recipe = f"<b>{title}</b> (<i>{type_.lower()}</i>)\n\n" \
             f"<i><b>Ингредиенты:</b></i>\n" \
             f"{text_ingredients}\n" \
             f"{rec_number} / {len(ids)}  {author}{date}\n" \

    if not call:
        chat_id = message.chat.id
    else:
        chat_id = message.message.chat.id

    if not change:
        path = os.path.join('images/recipes/' + str(ids[ind]) + '.jpg')
        await bot.send_photo(photo=types.InputFile(path), caption=recipe, chat_id=chat_id,
                             reply_markup=ikb_menu)
    else:
        print(ids, ind)
        path = os.path.join('images/recipes/' + str(ids[ind]) + '.jpg')
        edit_message_id = msg_to_edit.message_id
        photo = types.InputMedia(media=types.InputFile(path), caption=recipe)
        await bot.edit_message_media(media=photo, chat_id=chat_id, message_id=edit_message_id, reply_markup=ikb_menu)

    return ids, now_id


@dp.callback_query_handler(text_contains='открыть рецепт')
async def open_recipe(call: CallbackQuery):
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
    text = f"<b><i>Приготовление:</i></b>\n\n" \
           f"{description}"
    await call.message.answer(text, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Закрыть рецепт')
async def close_recipe(call: CallbackQuery):
    await call.message.delete()


# @dp.message_handler(state=Search.enter_title)
# async def start_search(message: types.Message, state: FSMContext):
#     answer = message.text
#     user_id = message.from_user.id
#
#     if len(answer) < 1:
#         await message.answer("Минимальная длина запроса - 3 символа. Повторите попытку:")
#     else:
#         results = cursor.execute("SELECT title FROM recipes").fetchall()
#         titles = [i[0] for i in results if answer.lower().replace('ё', 'е') in i[0].lower().replace('ё', 'е')]
#         await state.finish()
#
#         if not titles:
#             ikb_menu = InlineKeyboardMarkup(row_width=1,
#                                             inline_keyboard=[
#                                                 [
#                                                     InlineKeyboardButton(text='✏️ Изменить название для поиска',
#                                                                          callback_data='изменить название'),
#                                                 ],
#                                                 [
#                                                     InlineKeyboardButton(text='❌ Выйти из поиска',
#                                                                          callback_data='выйти из поиска'),
#                                                 ]
#
#                                             ],
#                                             )
#             await message.answer('📂 Мы не нашли подходящих рецептов', reply_markup=ikb_menu)
#         else:
#             # global pages
#             ids = []
#             for title in titles:
#                 rec_ids = cursor.execute("SELECT id FROM recipes WHERE title = ?", (title, )).fetchall()
#                 for i in rec_ids:
#                     ids.append(str(i[0]))
#             # pages[str(message.from_user.id)] = [ids[0], ids]
#             filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()
#
#             ids = filter_recipes(ids, filters[0], filter_type=int(filters[1]))
#             await get_recipe(message, ids, ids[0])
#             # await bot.answer_callback_query(str(call.id))


@dp.callback_query_handler(text_contains='вправо')
async def next_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ids_id = int(call.data.split('_')[1])
    ids = get_ids(ids_id)

    now_id = call.data.split('_')[2]
    from_subs = int(call.data.split('_')[3])
    from_profile = bool(int(call.data.split('_')[4]))
    if call.data.split('_')[5] == '0' or not call.data.split('_'):
        save_back = []
    else:
        save_back = [call.data.split('_')[5], call.data.split('_')[6]]

    await get_recipe(call, ids, now_id, change=True, call=True, next_rec=True,
                     msg_to_edit=call.message, from_subs=from_subs, from_profile=from_profile, save_back=save_back)


@dp.callback_query_handler(text_contains='влево')
async def previous_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ids_id = int(call.data.split('_')[1])
    ids = get_ids(ids_id)

    now_id = call.data.split('_')[2]
    from_subs = int(call.data.split('_')[3])
    from_profile = int(call.data.split('_')[4])
    if call.data.split('_')[5] == '0' or not call.data.split('_'):
        save_back = []
    else:
        save_back = [call.data.split('_')[5], call.data.split('_')[6]]

    await get_recipe(call, ids, now_id, change=True, call=True, next_rec=False,
                     msg_to_edit=call.message, from_subs=from_subs, from_profile=from_profile, save_back=save_back)


@dp.callback_query_handler(text_contains='лайк')
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
        # await bot.answer_callback_query(str(call.id))


@dp.callback_query_handler(text='изменить название')
async def continue_search(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    await call.message.answer('<i>Введите название нужного блюда (или часть названия):</i>')
    await Search.enter_title.set()


@dp.callback_query_handler(text_contains='избранное')
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

    if call.data.split('_')[4] != '0' and call.data.split('_')[4]:
        save_back = f'_{call.data.split("_")[4]}_{call.data.split("_")[5]}'
    else:
        save_back = '_0'

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
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=edit_message, reply_markup=ikb_menu)
        # await bot.answer_callback_query(str(call.id))

        favorites = ' '.join(favorites)

        cursor.execute("UPDATE profiles SET favorites = ? WHERE id = ?", (favorites, user_id))
        cursor.execute("UPDATE feedback SET favorites = ? WHERE rec_id = ?", (users_favorites, rec_id))
        connection.commit()


@dp.callback_query_handler(text='выйти из поиска')
async def exit_from_search(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    await call.message.answer('Вы вышли из режима поиска.')


