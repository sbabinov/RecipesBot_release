from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogram import types
from loader import dp, connection, cursor, bot
from states import AddQuestion


@dp.callback_query_handler(text='добавить вопрос админ')
async def add_question(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    questions_for_quiz = cursor.execute("SELECT id FROM questions WHERE if_for_quiz = ?", (1,)).fetchall()

    await call.message.answer(f'Всего вопросов для викторины: {len(questions_for_quiz)}')
    await AddQuestion.if_for_quiz.set()
    await call.message.answer("Вопрос для викторины?")


@dp.message_handler(state=AddQuestion.if_for_quiz)
async def enter_if_for_quiz(message: types.Message, state: FSMContext):
    answer = message.text
    if answer == 'да':
        await state.update_data(if_for_quiz=1)
        await AddQuestion.text.set()
        await message.answer("Введите текст вопроса:")
    if answer == 'нет':
        await state.update_data(if_for_quiz=0)
        await AddQuestion.text.set()
        await message.answer("Введите текст вопроса:")


@dp.message_handler(state=AddQuestion.text)
async def enter_question_text(message: types.Message, state: FSMContext):
    answer = message.text

    last_id = cursor.execute("SELECT id FROM questions").fetchall()
    if not last_id:
        last_id = 0
    else:
        last_id = last_id[-1][0]

    q_id = last_id + 1

    await state.update_data(q_id=q_id)
    await state.update_data(text=answer)

    await AddQuestion.variants.set()
    await message.answer("Отправьте варианты ответа (через два пробела):")
    # await message.answer("Отправьте фото для вопроса:")


# @dp.message_handler(state=AddQuestion.photo, content_types=ContentType.DOCUMENT)
# async def enter_question_photo(message: types.Message, state: FSMContext):
#     file_id = message.document.file_id
#     file = await bot.get_file(file_id=file_id)
#
#     data = await state.get_data()
#     q_id = data.get('q_id')
#
#     await file.download(destination_file=os.path.join('images/questions/' + str(q_id) + '.jpg'))
#
#     file = Image.open('images/questions/' + str(q_id) + '.jpg')
#     file.thumbnail((400, 400))
#     file.save('images/questions/' + str(q_id) + '.jpg')
#
#     await AddQuestion.variants.set()
#     await message.answer("Отправьте варианты ответа (через пробел):")


@dp.message_handler(state=AddQuestion.variants)
async def enter_question_variants(message: types.Message, state: FSMContext):
    answer = message.text

    variants = answer.split('  ')
    if len(variants) < 2:
        await message.answer("Некорректные данные!")
    else:
        await state.update_data(variants=variants)
        await AddQuestion.right_variant.set()
        await message.answer("Введите правильный вариант ответа:")


@dp.message_handler(state=AddQuestion.right_variant)
async def enter_question_right_variant(message: types.Message, state: FSMContext):
    answer = message.text

    data = await state.get_data()
    variants = data.get('variants')

    if answer not in variants:
        await message.answer("Такого варианта нет в списке!")
    else:
        await state.update_data(right_variant=answer)

        text = data.get('text')
        q_id = data.get('q_id')

        question_text = f"❓ {text}"

        ikb_menu = InlineKeyboardMarkup(row_width=1)
        for v in variants:
            button = InlineKeyboardButton(text=v, callback_data=f"вариант_{v}")
            ikb_menu.add(button)

        # t = '-' * (len(question_text) - 4 if len(question_text))

        question_text = f"-                                       -\n\n" \
                        f"{text}\n\n" \
                        f"-                                       -"

        # photo = InputFile(os.path.join('images/questions/' + str(q_id) + '.jpg'))
        chat_id = message.chat.id

        # await message.answer(text=text, reply_markup=ikb_menu)
        # await bot.send_photo(chat_id=chat_id, photo=photo, caption=question_text, reply_markup=ikb_menu)
        await message.answer(question_text, reply_markup=ikb_menu)
        await AddQuestion.confirm.set()
        await message.answer("Оставляем?")


@dp.message_handler(state=AddQuestion.confirm)
async def confirm(message: types.Message, state: FSMContext):
    answer = message.text

    if answer == 'нет':
        await state.finish()
        await message.answer("Отменено")

    if answer == 'да':
        data = await state.get_data()

        text = data.get('text')
        q_id = data.get('q_id')
        variants = '  '.join(data.get('variants'))
        right_variant = data.get('right_variant')
        if_for_quiz = data.get('if_for_quiz')

        cursor.execute("INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?)", (q_id, text, variants, right_variant,
                                                                           if_for_quiz, ''))
        connection.commit()

        await state.finish()
        await message.answer("Вопрос успешно добавлен!")


