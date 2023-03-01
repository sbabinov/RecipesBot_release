from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from loader import dp, connection, cursor, bot

from .settings import check_notifications_settings
from .functions_loader import get_profile


achievements = {
    '📗': ['Первый рецепт', 'Опубликуйте свой первый рецепт'],
    '📒': ['Первый десяток', 'Опубликуйте 10 рецептов'],
    '📚': ['Книга рецептов', 'Опубликуйте 25 рецептов'],
    '😍': ['Валентин', 'Лайкните 40 рецептов'],
    '📈': ['Популярный', 'Наберите 20 подписчиков'],
    '✏️': ['Писатель', 'Напишите 3 статьи'],
    '👑': ['Вклад', 'Купите свой первый VIP'],
    '🤴🏻': ['Король', '5 раз купите VIP'],
    '❓': ['Что Где Когда', 'Ответьте на 10 вопросов'],
    '🧑🏻‍🎓': ['Магистр наук', 'Ответьте на 50 вопросов'],
    '🧩': ['Всё сошлось', 'Ответьте правильно на все вопросы викторины']
}


async def give_achievements(user_id: int, achievement: str) -> None:
    global achievements
    user_achievements = cursor.execute("SELECT achievements FROM profiles "
                                       "WHERE id = ?", (user_id,)).fetchone()[0].split()

    if achievement not in user_achievements:
        user_achievements.append(achievement)

        new_user_achievements = ' '.join(user_achievements)
        cursor.execute("UPDATE profiles SET achievements = ? WHERE id = ?", (new_user_achievements, user_id))
        connection.commit()

        text = f'Поздравляем! Вы получили достижение ' \
               f'{achievement} <i><b>{achievements[achievement][0]}</b></i>\n\n' \
               f'<i>Чтобы узнать подробнее, зайдите в профиль -> достижения</i>'

        await check_notifications_settings(user_id, text=text)


@dp.callback_query_handler(text='достижения')
async def show_achievements(call: CallbackQuery):
    user_id = call.from_user.id

    user_achievements = cursor.execute("SELECT achievements FROM profiles "
                                       "WHERE id = ?", (user_id,)).fetchone()[0]

    if not user_achievements:
        await bot.answer_callback_query(str(call.id), text="У вас пока нет достижений!", show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))

        user_achievements = user_achievements.split()

        global achievements
        ach_amount = len(achievements)

        message = f'<b>Ваши достижения:</b> <i>({len(user_achievements)} / {ach_amount})</i>\n\n'
        for a in user_achievements:
            message += f'{a} <code>{achievements[a][0]}</code> - <i>{achievements[a][1].lower()}</i>\n' \
                       f'-------------------------------------------------------\n'

        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                InlineKeyboardButton(text='↩️ Назад', callback_data='закрыть достижения')
            ]
        ])
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=ikb_menu)
        # await call.message.answer(message, reply_markup=ikb_menu)


@dp.callback_query_handler(text='закрыть достижения')
async def close_achievements(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    user_profile = get_profile(user_id)

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
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=user_profile, reply_markup=ikb_menu)