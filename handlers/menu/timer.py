import os
import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InputFile, InputMedia

from .functions_loader import get_user_theme_picture
from loader import dp, connection, cursor, bot, storage
from states import Timer


@dp.callback_query_handler(text='таймер')
async def timer(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'timer')

    if_works = cursor.execute("SELECT if_works FROM timers_work WHERE user_id = ?", (user_id,)).fetchone()

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text="🟢 Запуск" if not if_works else "🔴 Стоп",
                                                                 callback_data=
                                                                 'запуск таймера' if not if_works else 'стоп таймера'),
                                            InlineKeyboardButton(text='⚙️ Настройка',
                                                                 callback_data='настройка таймера'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='прочее'),
                                        ]
                                    ],
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    media = InputMedia(media=image)
    await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='настройка таймера')
async def timer_settings(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🕓 Длительность',
                                                                 callback_data=f'длительность таймера'),
                                            InlineKeyboardButton(text='🔤 Пометка',
                                                                 callback_data='пометка таймера'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='таймер'),
                                        ]
                                    ],
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='длительность таймера')
async def timer_time(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    await Timer.enter_amount_of_minutes.set()
    await call.message.answer("Введите количество минут, по истечении которого таймер отправит вам уведомление:")


@dp.message_handler(state=Timer.enter_amount_of_minutes)
async def enter_amount_of_minutes(message: types.Message, state: FSMContext):
    answer = message.text
    user_id = message.from_user.id

    try:
        answer = int(answer)
        if answer < 1 or answer > 60:
            await message.answer("Число должно быть в диапазоне от 3 до 60. Попробуйте еще раз:")
        else:
            user_timer_time = cursor.execute("SELECT timer_time FROM timers WHERE user_id = ?", (user_id,)).fetchone()
            if not user_timer_time:
                cursor.execute("INSERT INTO timers VALUES (?, ?, ?)", (user_id, answer, ''))
            else:
                cursor.execute("UPDATE timers SET timer_time = ? WHERE user_id = ?", (answer, user_id))
            connection.commit()

            if str(answer).endswith('1'):
                word = 'минута'
            elif str(answer).endswith('2') or str(answer).endswith('3') or str(answer).endswith('4'):
                word = 'минуты'
            else:
                word = 'минут'

            ikb_menu = InlineKeyboardMarkup(row_width=1)
            ikb_menu.add(InlineKeyboardButton(text='✅ Ок', callback_data='ОК'))

            await state.finish()
            await message.answer(f"Настройка успешно изменена. Время срабатывания таймера - {answer} {word}.",
                                 reply_markup=ikb_menu)
            # await asyncio.sleep(answer * 60)
            # await message.answer("Таймер сработал!")
    except:
        await message.answer("Введите целое число минут!")


@dp.callback_query_handler(text='пометка таймера')
async def timer_note(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    await Timer.enter_note.set()
    await call.message.answer("Введите сообщение, которое бот должен отправить вам по истечении времени:")


@dp.message_handler(state=Timer.enter_note)
async def enter_note(message: types.Message, state: FSMContext):
    answer = message.text
    user_id = message.from_user.id

    user_timer_note = cursor.execute("SELECT timer_note FROM timers WHERE user_id = ?", (user_id,)).fetchone()
    if not user_timer_note:
        cursor.execute("INSERT INTO timers VALUES (?, ?, ?)", (user_id, 0, answer))
    else:
        cursor.execute("UPDATE timers SET timer_note = ? WHERE user_id = ?", (answer, user_id))
    connection.commit()

    ikb_menu = InlineKeyboardMarkup(row_width=1)
    ikb_menu.add(InlineKeyboardButton(text='✅ Ок', callback_data='ОК'))

    await state.finish()
    await message.answer("Пометка таймера успешно изменена!", reply_markup=ikb_menu)


@dp.callback_query_handler(text='ОК')
async def to_timer_menu(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    image = InputFile(os.path.join('images/design/timer.jpg'))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🕓 Длительность',
                                                                 callback_data=f'длительность таймера'),
                                            InlineKeyboardButton(text='🔤 Пометка',
                                                                 callback_data='пометка таймера'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='таймер'),
                                        ]
                                    ],
                                    )
    chat_id = call.message.chat.id

    await bot.send_photo(chat_id=chat_id, photo=image, reply_markup=ikb_menu)


@dp.callback_query_handler(text='запуск таймера')
async def start_timer(call: CallbackQuery):
    # await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    t_time = cursor.execute("SELECT timer_time FROM timers WHERE user_id = ?", (user_id,)).fetchone()
    t_note = cursor.execute("SELECT timer_note FROM timers WHERE user_id = ?", (user_id,)).fetchone()

    if not t_time or t_time[0] == 0:
        await bot.answer_callback_query(str(call.id), text='Установите время срабатывания таймера в настройках',
                                        show_alert=True)
    elif not t_note or not t_note[0]:
        await bot.answer_callback_query(str(call.id), text='Установите пометку для таймера в настройках',
                                        show_alert=True)
    else:
        t_time = t_time[0]
        t_note = f'<b>Таймер</b>\n\n' \
                 f'{t_note[0]}'

        timers_ids = cursor.execute("SELECT timer_id FROM timers_work").fetchall()
        if not timers_ids:
            timer_id = 0
        else:
            timer_id = timers_ids[-1][0] + 1

        cursor.execute("INSERT INTO timers_work VALUES (?, ?, ?)", (timer_id, 1, user_id))
        connection.commit()

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='🔴 Стоп',
                                                                     callback_data=f'стоп таймера_{timer_id}'),
                                                InlineKeyboardButton(text='⚙️ Настройка',
                                                                     callback_data='настройка таймера'),
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад', callback_data='прочее'),
                                            ]
                                        ],
                                        )
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)
        await asyncio.sleep(t_time * 60)

        if_works = cursor.execute("SELECT if_works FROM timers_work WHERE timer_id = ?", (timer_id,)).fetchone()
        if if_works and if_works[0]:
            for i in 0, 1, 2:
                await call.message.answer(t_note)
                await asyncio.sleep(5)

        cursor.execute("DELETE FROM timers_work WHERE timer_id = ?", (timer_id,))
        connection.commit()


@dp.callback_query_handler(text_contains='стоп таймера')
async def stop_timer(call: CallbackQuery):
    user_id = call.from_user.id
    timer_id = int(call.data.split('_')[1])

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🟢 Запуск',
                                                                 callback_data=f'запуск таймера'),
                                            InlineKeyboardButton(text='⚙️ Настройка',
                                                                 callback_data='настройка таймера'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='прочее'),
                                        ]
                                    ],
                                    )

    if_works = cursor.execute("SELECT if_works FROM timers_work WHERE timer_id = ?", (timer_id,)).fetchone()

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if not if_works:
        await bot.answer_callback_query(str(call.id), text='У вас нет работающих таймеров', show_alert=True)
    else:
        cursor.execute("UPDATE timers_work SET if_works = ? WHERE timer_id = ?", (0, timer_id))
        connection.commit()

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)



