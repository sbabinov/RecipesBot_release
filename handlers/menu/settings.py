import asyncio
import types

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InputMedia
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .functions_loader import get_user_theme_picture, check_vip, check_username
from loader import dp, connection, cursor, bot, storage
from states import Settings


def filter_recipes(ids: list, filter_: str, filter_type: int = 1) -> list:
    user_recipes_ids = []
    other_ids = []
    for i in ids:
        author_id = cursor.execute("SELECT author_id FROM recipes WHERE id = ?", (int(i),)).fetchone()[0]
        if author_id:
            user_recipes_ids.append(i)
        else:
            other_ids.append(i)

    if filter_ == '1':
        if not filter_type:
            return user_recipes_ids + other_ids
        user_recipes_ids.reverse()
        other_ids.reverse()
        return user_recipes_ids + other_ids

    if filter_ == '2':
        result = []
        amounts = []

        for ids in [user_recipes_ids, other_ids]:
            for recipe_id in ids:
                likes = cursor.execute("SELECT likes FROM feedback WHERE rec_id = ?",
                                       (recipe_id,)).fetchone()[0]
                likes_amount = len(likes.split())

                amount = likes_amount
                amounts.append(amount)
                if not filter_type:
                    amounts.sort()
                else:
                    amounts.sort(reverse=True)

            sorted_ids = []

            for a in amounts:
                for recipe_id in ids:
                    likes = cursor.execute("SELECT likes FROM feedback WHERE rec_id = ?",
                                           (recipe_id,)).fetchone()[0]
                    likes_amount = len(likes.split())

                    amount = likes_amount
                    if a == amount:
                        sorted_ids.append(recipe_id)

            new_sorted_ids = []
            for i in sorted_ids:
                if i not in new_sorted_ids:
                    new_sorted_ids.append(i)

            result += new_sorted_ids

        return result


async def check_notifications_settings(user_id: int, text: str, reply_markup: InlineKeyboardMarkup = None):
    if_turn_up = cursor.execute("SELECT if_turn_on FROM notifications WHERE user_id = ?", (user_id,)).fetchone()
    if not if_turn_up or if_turn_up[0]:
        try:
            await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
        except Exception as e:
            print(e)


@dp.callback_query_handler(text='настройки')
async def settings(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'settings')

    if_turn_on = cursor.execute("SELECT if_turn_on FROM notifications WHERE user_id = ?", (user_id,)).fetchone()
    if not if_turn_on:
        emoji = '🔔'
    else:
        if not if_turn_on[0]:
            emoji = '🔕'
        else:
            emoji = '🔔'

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='ℹ️ Сортировка', callback_data=f'фильтры'),
                                            InlineKeyboardButton(text=f'{emoji} Уведомления',
                                                                 callback_data=f'уведомления'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='🎨 Тема', callback_data=f'тема'),
                                            InlineKeyboardButton(text='✏️ Профиль', callback_data=f'изменить'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data=f'назад'),
                                        ]
                                    ],
                                    )
    media = InputMedia(media=image)
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    # await bot.send_photo(chat_id, photo=image, reply_markup=ikb_menu)

    await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text='фильтры')
async def filters(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🕒 По дате', callback_data=f'по дате'),
                                            InlineKeyboardButton(text='📈 По популярности',
                                                                 callback_data=f'по популярности'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data=f'настройки'),
                                        ]
                                    ],
                                    )
    # await call.message.delete()
    caption = "Выберите предпочтительный тип сортировки рецептов и статей:"

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption, reply_markup=ikb_menu)

    # await call.message.answer(, reply_markup=ikb_menu)


@dp.callback_query_handler(text='по популярности')
async def by_popularity(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='⬆️ По возрастанию',
                                                                 callback_data=f'по возрастанию_2'),
                                            InlineKeyboardButton(text='⬇️ По убыванию',
                                                                 callback_data=f'по убыванию_2'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data=f'фильтры'),
                                        ]
                                    ],
                                    )
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)

    # user_id = call.from_user.id
    # cursor.execute("UPDATE profiles SET filters = ? WHERE id = ?", ('by popularity', user_id))
    # connection.commit()


@dp.callback_query_handler(text='по дате')
async def by_popularity(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='⬆️ Сначала старые',
                                                                 callback_data=f'по возрастанию_1'),
                                            InlineKeyboardButton(text='⬇️ Сначала новые',
                                                                 callback_data=f'по убыванию_1'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data=f'фильтры'),
                                        ]
                                    ],
                                    )
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)

    # user_id = call.from_user.id
    # cursor.execute("UPDATE profiles SET filters = ? WHERE id = ?", ('', user_id))
    # connection.commit()


@dp.callback_query_handler(text_contains='по возрастанию')
async def by_popularity(call: CallbackQuery):

    user_id = call.from_user.id
    if call.data.split('_')[1] == '1':
        cursor.execute("UPDATE profiles SET filters = ? WHERE id = ?", ('1 0', user_id))
    else:
        cursor.execute("UPDATE profiles SET filters = ? WHERE id = ?", ('2 0', user_id))

    connection.commit()

    await bot.answer_callback_query(str(call.id), text="✅ Сохранено!", show_alert=True)


@dp.callback_query_handler(text_contains='по убыванию')
async def by_popularity(call: CallbackQuery):

    user_id = call.from_user.id
    if call.data.split('_')[1] == '1':
        cursor.execute("UPDATE profiles SET filters = ? WHERE id = ?", ('1 1', user_id))
    else:
        cursor.execute("UPDATE profiles SET filters = ? WHERE id = ?", ('2 1', user_id))

    connection.commit()

    await bot.answer_callback_query(str(call.id), text="✅ Сохранено!", show_alert=True)


@dp.callback_query_handler(text='Назад из фильтров')
async def back_from_filters(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    if_turn_on = cursor.execute("SELECT if_turn_on FROM notifications WHERE user_id = ?", (user_id,)).fetchone()
    if not if_turn_on:
        emoji = '🔔'
    else:
        if not if_turn_on[0]:
            emoji = '🔕'
        else:
            emoji = '🔔'

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='ℹ️ Сортировка', callback_data=f'фильтры'),
                                            InlineKeyboardButton(text=f'{emoji} Уведомления',
                                                                 callback_data=f'уведомления'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='🎨 Тема', callback_data=f'тема'),
                                            InlineKeyboardButton(text='✏️ Профиль', callback_data=f'изменить'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data=f'назад'),
                                        ]
                                    ],
                                    )

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption='', reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='уведомления')
async def notifications(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    if_turn_on = cursor.execute("SELECT if_turn_on FROM notifications WHERE user_id = ?", (user_id,)).fetchone()
    if if_turn_on:
        if if_turn_on[0]:
            turn_on = 0
        else:
            turn_on = 1
    else:
        turn_on = 0

        cursor.execute("INSERT INTO notifications VALUES (?, ?)", (user_id, turn_on))
        connection.commit()

    emoji = '🔔' if turn_on else '🔕'

    cursor.execute("UPDATE notifications SET if_turn_on = ? WHERE user_id = ?", (turn_on, user_id))
    connection.commit()

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='ℹ️ Сортировка', callback_data=f'фильтры'),
                                            InlineKeyboardButton(text=f'{emoji} Уведомления',
                                                                 callback_data=f'уведомления'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='🎨 Тема', callback_data=f'тема'),
                                            InlineKeyboardButton(text='✏️ Профиль', callback_data=f'изменить'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data=f'назад'),
                                        ]
                                    ],
                                    )

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text='тема')
async def theme(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await call.answer('Эта функция доступна только для VIP-пользователей!', show_alert=True)
    else:
        await call.answer()

        image = get_user_theme_picture(user_id, 'theme')

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='⚪️ Светлая', callback_data=f'светлая тема'),
                                                InlineKeyboardButton(text=f'⚫️ Темная', callback_data=f'темная тема'),
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад', callback_data=f'настройки'),
                                            ]
                                        ],
                                        )
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        media = InputMedia(media=image)

        await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text='светлая тема')
async def light_theme(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await call.answer('Эта функция доступна только для VIP-пользователей!', show_alert=True)
    else:
        await call.answer()

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='⚪️⚫️', callback_data=f'light-classic'),
                                                InlineKeyboardButton(text=f'⚪️🟣', callback_data=f'light-purple'),
                                                InlineKeyboardButton(text=f'⚪️🔵', callback_data=f'light-blue'),
                                                InlineKeyboardButton(text=f'🔵🟣', callback_data=f'light-pink'),
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад', callback_data=f'тема'),
                                            ]
                                        ],
                                        )
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text='темная тема')
async def light_theme(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await call.answer('Эта функция доступна только для VIP-пользователей!', show_alert=True)
    else:
        await call.answer()

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='⚫️⚪️', callback_data=f'dark-classic'),
                                                InlineKeyboardButton(text=f'⚫️🟠', callback_data=f'dark-orange'),
                                                InlineKeyboardButton(text=f'⚫️🟡', callback_data=f'dark-yellow'),
                                                InlineKeyboardButton(text=f'⚫️🟣', callback_data=f'dark-purple'),
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад', callback_data=f'тема'),
                                            ]
                                        ],
                                        )
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='light')
async def light_theme(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await call.answer('Эта функция доступна только для VIP-пользователей!', show_alert=True)
    else:
        await call.answer()

        theme_color = call.data

        user_theme = cursor.execute("SELECT theme FROM users_themes WHERE user_id = ?", (user_id,)).fetchone()
        if not user_theme:
            cursor.execute("INSERT INTO users_themes VALUES (?, ?)", (user_id, theme_color))
        else:
            cursor.execute("UPDATE users_themes SET theme = ? WHERE user_id = ?", (theme_color, user_id))
        connection.commit()

        image = get_user_theme_picture(user_id, 'theme')

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='⚪️⚫️', callback_data=f'light-classic'),
                                                InlineKeyboardButton(text=f'⚪️🟣', callback_data=f'light-purple'),
                                                InlineKeyboardButton(text=f'⚪️🔵', callback_data=f'light-blue'),
                                                InlineKeyboardButton(text=f'🔵🟣', callback_data=f'light-pink'),
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад', callback_data=f'тема'),
                                            ]
                                        ],
                                        )
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        media = InputMedia(media=image)

        await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='dark')
async def dark_theme(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await call.answer('Эта функция доступна только для VIP-пользователей!', show_alert=True)
    else:
        await call.answer()

        theme_color = call.data

        user_theme = cursor.execute("SELECT theme FROM users_themes WHERE user_id = ?", (user_id,)).fetchone()
        if not user_theme:
            cursor.execute("INSERT INTO users_themes VALUES (?, ?)", (user_id, theme_color))
        else:
            cursor.execute("UPDATE users_themes SET theme = ? WHERE user_id = ?", (theme_color, user_id))
        connection.commit()

        image = get_user_theme_picture(user_id, 'theme')

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='⚫️⚪️', callback_data=f'dark-classic'),
                                                InlineKeyboardButton(text=f'⚫️🟠', callback_data=f'dark-orange'),
                                                InlineKeyboardButton(text=f'⚫️🟡', callback_data=f'dark-yellow'),
                                                InlineKeyboardButton(text=f'⚫️🟣', callback_data=f'dark-purple'),
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад', callback_data=f'тема'),
                                            ]
                                        ],
                                        )
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        media = InputMedia(media=image)

        await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text='изменить')
async def change_profile(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id

    profile_emoji = cursor.execute("SELECT emoji FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    sex = cursor.execute("SELECT gender FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]

    sex_emoji = '🚹' if sex == 'м' else '🚺'

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🔤 Имя', callback_data=f'изменить имя'),
                                            InlineKeyboardButton(text=f'{sex_emoji} Пол', callback_data=f'изменить пол')
                                        ],
                                        # [
                                        #     InlineKeyboardButton(text=f'{profile_emoji} Эмодзи профиля',
                                        #                          callback_data=f'dark-yellow'),
                                        # ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data=f'настройки'),
                                        ]
                                    ],
                                    )
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text='изменить имя')
async def change_username(call: CallbackQuery):
    await call.answer()

    chat = call.message.chat.id
    user = call.from_user.id

    await Settings.enter_username.set()
    msg = await call.message.answer("Введите новый юзернейм:")
    state = FSMContext(storage, chat, user)
    await state.update_data(message_id=msg.message_id)


@dp.message_handler(state=Settings.enter_username)
async def enter_username(message: types.Message, state: FSMContext):
    answer = message.text
    user_id = message.from_user.id

    data = await state.get_data()
    msg_id = data.get('message_id')
    chat_id = message.chat.id

    permission = check_username(answer)
    if isinstance(permission, str):
        await message.delete()
        await bot.delete_message(chat_id, msg_id)
        msg = await message.answer(permission)
        await state.update_data(message_id=msg.message_id)
    else:
        cursor.execute("UPDATE profiles SET name = ? WHERE id = ?", (answer, user_id))
        connection.commit()

        await state.finish()
        await message.delete()
        await bot.delete_message(chat_id, msg_id)
        msg = await message.answer("✅ Имя пользователя успешно изменено!")
        await asyncio.sleep(2)
        await msg.delete()


@dp.callback_query_handler(text='изменить пол')
async def change_sex(call: CallbackQuery):
    user_id = call.from_user.id

    user_sex = cursor.execute("SELECT gender FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    new_user_sex = 'м' if user_sex == 'ж' else 'ж'

    sex_emoji = '🚹' if new_user_sex == 'м' else '🚺'

    cursor.execute("UPDATE profiles SET gender = ? WHERE id = ?", (new_user_sex, user_id))
    connection.commit()

    profile_emoji = cursor.execute("SELECT emoji FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🔤 Имя', callback_data=f'изменить имя'),
                                            InlineKeyboardButton(text=f'{sex_emoji} Пол', callback_data=f'изменить пол')
                                        ],
                                        # [
                                        #     InlineKeyboardButton(text=f'{profile_emoji} Эмодзи профиля',
                                        #                          callback_data=f'dark-yellow'),
                                        # ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data=f'настройки'),
                                        ]
                                    ],
                                    )
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)





