import os.path
import datetime

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton, InputFile, CallbackQuery
from aiogram.dispatcher.filters import Command
from aiogram import types

from loader import dp, connection, cursor, bot, storage
from data import admins
from states import Help


@dp.callback_query_handler(text='помощь')
async def admin_help(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_report_id = cursor.execute("SELECT id FROM help").fetchone()

    if user_report_id:
        user_report_id = user_report_id[0]

        user_report_text = cursor.execute("SELECT text FROM help WHERE id = ?", (user_report_id,)).fetchone()[0]
        user_report_type = cursor.execute("SELECT type FROM help WHERE id = ?", (user_report_id,)).fetchone()[0]
        user_id = cursor.execute("SELECT user_id FROM help WHERE id = ?", (user_report_id,)).fetchone()[0]
        user_name = cursor.execute("SELECT name FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]

        if user_report_type == 'question':
            type_text = '❓ Вопрос'
        elif user_report_type == 'suggestion':
            type_text = '✏️ Предложение'
        else:
            type_text = '🔊 Проблема'

        text = f"<b>{type_text}</b>\n\n" \
               f"<i><b>Пользователь</b>: <code>{user_name}</code></i>\n\n" \
               f"<b><i>Сообщение:</i></b>\n" \
               f"{user_report_text}"

        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                InlineKeyboardButton(text='💬', callback_data=f'ответить админ_{user_report_id}'),
                InlineKeyboardButton(text='❌', callback_data=f'удалить админ_{user_report_id}')
            ]
        ])

        await call.message.answer(text, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='ответить админ')
async def admin_answer(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    report_id = int(call.data.split('_')[1])
    state = FSMContext(storage=storage, chat=call.message.chat.id, user=call.from_user.id)

    await state.update_data(report_id=report_id)
    await Help.report_id.set()
    await call.message.answer("Введите ответ для пользователя:")


@dp.message_handler(state=Help.report_id)
async def send_answer_to_user(message: types.Message, state: FSMContext):
    answer = message.text

    data = await state.get_data()
    report_id = data.get('report_id')

    user_id = cursor.execute("SELECT user_id FROM help WHERE id = ?", (report_id,)).fetchone()[0]
    report_text = cursor.execute("SELECT text FROM help WHERE id = ?", (report_id,)).fetchone()[0]

    text = f"{report_text}\n\n" \
               f"<b>Ответ администрации:</b>\n" \
               f"<i>{answer}</i>"

    try:
        await bot.send_message(user_id, text=text)
    except Exception as e:
        print(e)

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [
            InlineKeyboardButton(text='➡️ Дальше', callback_data='помощь')
        ]
    ])

    await state.finish()
    await message.answer("Успешно отправлено пользователю!", reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='удалить админ')
async def admin_delete(call: CallbackQuery):
    report_id = int(call.data.split('_')[1])

    cursor.execute("DELETE FROM help WHERE id = ?", (report_id,))
    connection.commit()

    await bot.answer_callback_query(str(call.id), text='Успешно удалено', show_alert=True)
    await call.message.delete()




