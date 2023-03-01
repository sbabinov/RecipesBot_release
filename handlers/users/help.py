import os

from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import types

from loader import dp, bot, cursor, connection, storage
from handlers.menu.functions_loader import get_user_theme_picture
from states import Help
from data.config import admins


@dp.message_handler(text="/help")
async def command_help(message: types.Message):
    user_id = message.from_user.id

    image = get_user_theme_picture(user_id, 'help')

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


@dp.callback_query_handler(text_contains='репорт')
async def ask_question(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    report_type = call.data.split('_')[1]

    if report_type == 'вопрос':
        await call.message.answer("Напишите вопрос о боте, который вы хотите задать администрации:")
    if report_type == 'предложение':
        await call.message.answer("Напишите ваше предложение для улучшения бота:")
    if report_type == 'проблема':
        await call.message.answer("Опишите проблему, с которой вы столкнулись при использовании бота:")

    state = FSMContext(storage, call.message.chat.id, call.from_user.id)

    await state.update_data(report_type=report_type)
    await Help.question_text.set()


@dp.message_handler(state=Help.question_text)
async def enter_question_text(message: types.Message, state: FSMContext):
    answer = message.text

    data = await state.get_data()
    report_type = data.get('report_type')

    if report_type == 'вопрос' and len(answer) > 1000:
        await message.answer("Слишком длинный вопрос! Максимальная длина - 1000 символов. Попробуйте еще раз:")
    if (report_type == 'предложение' or report_type == 'проблема') and (len(answer) > 1800):
        await message.answer("Слишком большой объем сообщения! Максимальная длина - 1800 символов. Попробуйте еще раз:")
    else:
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Да', callback_data='оставить'),
                InlineKeyboardButton(text='❌ Нет', callback_data='не оставлять'),
            ]
        ])

        await state.update_data(question_text=answer)

        await Help.confirm.set()
        await message.answer("Отправляем?", reply_markup=ikb_menu)


@dp.callback_query_handler(text='оставить', state=Help.confirm)
async def confirm_question(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    data = await state.get_data()
    question_text = data.get('question_text')
    report_type = data.get('report_type')

    last_id = cursor.execute("SELECT id FROM help").fetchall()
    if last_id:
        last_id = last_id[-1][0]
    else:
        last_id = 0

    question_id = last_id + 1

    if report_type == 'вопрос':
        db_report_type = 'question'
    elif report_type == 'предложение':
        db_report_type = 'suggestion'
    else:
        db_report_type = 'problem'

    cursor.execute("INSERT INTO help VALUES (?, ?, ?, ?)", (question_id, user_id, question_text, db_report_type))
    connection.commit()

    try:
        await bot.send_message(chat_id=admins[0], text='Новый фидбек от пользователя!')
    except Exception as e:
        print(e)

    await state.finish()

    if report_type == 'вопрос':
        await call.message.answer("Ваш вопрос успешно отправлен администрации бота!")
    elif report_type == 'предложение':
        await call.message.answer("Ваше предложение успешно отправлено администрации бота!")
    else:
        await call.message.answer("Описание вашей проблемы успешно отправлено администрации бота!")


@dp.callback_query_handler(text='не оставлять', state=Help.confirm)
async def not_confirm_question(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    await state.finish()
    await call.message.answer("Отменено")

