import asyncio
import os
import random
import time

from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InputFile, InputMedia, Message

from data import admins
from loader import dp, connection, cursor, bot
from ..users.experience import give_experience
from .achievements import give_achievements
from .functions_loader import check_vip, get_user_theme_picture


@dp.callback_query_handler(text='викторины')
async def show_quizzes(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'quizzes')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❓ Случайный вопрос', callback_data=f'вопросы'),
                                            InlineKeyboardButton(text='🎲 Викторина недели',
                                                                 callback_data='викторина недели')

                                        ],
                                        [
                                            InlineKeyboardButton(text='📊 Список лидеров', callback_data=f'лидеры'),
                                            InlineKeyboardButton(text='ℹ️ Информация',
                                                                 callback_data=f'информация вопросы')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='прочее'),
                                        ]
                                    ]
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    media = InputMedia(media=image)
    await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='вопросы')
async def questions(call: CallbackQuery):
    user_id = call.from_user.id
    questions_for_user = []

    questions_amount = \
        cursor.execute("SELECT questions_amount FROM questions_time WHERE user_id = ?", (user_id,)).fetchone()
    if not questions_amount:
        questions_amount = 0

        cursor.execute("INSERT INTO questions_time VALUES (?, ?)", (user_id, 0))
        connection.commit()
    else:
        questions_amount = questions_amount[0]

    if not check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
                                        show_alert=True)
    elif questions_amount >= 5:
        await bot.answer_callback_query(str(call.id), text='❓ Новые вопросы откроются завтра!', show_alert=True)
    else:
        all_questions = cursor.execute("SELECT id FROM questions WHERE if_for_quiz = ?", (0,)).fetchall()
        for q in all_questions:
            users_ask = cursor.execute("SELECT users FROM questions WHERE id = ?", (q[0],)).fetchone()[0].split()
            if str(user_id) not in users_ask:
                questions_for_user.append(q[0])

        if not questions_for_user:
            await bot.answer_callback_query(str(call.id), text='Кажется вы ответили на все существующие вопросы! '
                                                               'Так держать!', show_alert=True)
        else:
            question_for_user = random.choice(questions_for_user)

            text = cursor.execute("SELECT text FROM questions WHERE id = ?", (question_for_user,)).fetchone()[0]
            variants = cursor.execute("SELECT variants FROM questions WHERE id = ?", (question_for_user,)).fetchone()[0]

            question_text = f"---<b>❓ Случайный вопрос</b> ---\n\n" \
                            f"{text}\n\n" \
                            f"-                                       -"
            question_variants = variants.split('  ')

            ikb_menu = InlineKeyboardMarkup(row_width=1)
            emoji = ['1️⃣', '2️⃣', '3️⃣']
            count = 0
            for v in question_variants:
                button = InlineKeyboardButton(text=f"{emoji[count]} {v}",
                                              callback_data=f"вариант_{v}_{question_for_user}")
                ikb_menu.add(button)
                count += 1

            ikb_menu.add(InlineKeyboardButton(text='↩️ Назад', callback_data='Назад из вопросов'))

            await call.message.delete()
            await call.message.answer(text=question_text, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='вариант')
async def answer_to_question(call: CallbackQuery):
    user_id = call.from_user.id
    answer = call.data.split('_')[1]
    question_id = int(call.data.split('_')[2])

    questions_amount = cursor.execute("SELECT questions_amount FROM questions_time WHERE user_id = ?",
                                      (user_id,)).fetchone()[0]

    if not check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Эта функция доступна только VIP-пользователям!',
                                        show_alert=True)
    elif questions_amount >= 5:
        await bot.answer_callback_query(str(call.id), text='❓ Новые вопросы откроются завтра!', show_alert=True)
    else:
        users_ask = cursor.execute("SELECT users FROM questions WHERE id = ?", (question_id,)).fetchone()[0].split()
        if str(user_id) in users_ask:
            await bot.answer_callback_query(str(call.id))
        else:
            questions_amount += 1
            cursor.execute("UPDATE questions_time SET questions_amount = ? WHERE user_id = ?",
                           (questions_amount, user_id))
            connection.commit()

            users_answers = cursor.execute("SELECT all_answers FROM users_answers WHERE user_id = ?",
                                           (user_id,)).fetchone()
            if not users_answers:
                cursor.execute("INSERT INTO users_answers VALUES (?, ?, ?, ?)", (user_id, 0, 0, 0))
                users_answers = 0
            else:
                users_answers = users_answers[0]

            cursor.execute("UPDATE users_answers SET all_answers = ? WHERE user_id = ?", (users_answers + 1, user_id))
            connection.commit()

            users_ask = cursor.execute("SELECT users FROM questions WHERE id = ?", (question_id,)).fetchone()[0].split()
            users_ask.append(str(user_id))
            users_ask = ' '.join(users_ask)

            cursor.execute("UPDATE questions SET users = ? WHERE id = ?", (users_ask, question_id))
            connection.commit()

            variants = cursor.execute("SELECT variants FROM questions WHERE id = ?",
                                      (question_id,)).fetchone()[0].split('  ')
            right_variant = cursor.execute("SELECT right_variant FROM questions WHERE id = ?",
                                           (question_id,)).fetchone()[0]

            # ikb_menu = InlineKeyboardMarkup(row_width=1)
            inline_keyboard = []
            emoji = ['1️⃣', '2️⃣', '3️⃣']
            count = 0
            for v in variants:
                if v == right_variant:
                    text = f'✅ '
                elif answer == v and answer != right_variant:
                    text = f'❌ '
                else:
                    text = ''

                button = InlineKeyboardButton(text=f"{text} {emoji[count]} {v}", callback_data=f"none")
                # ikb_menu.add(button)
                inline_keyboard.append([button])

                count += 1

            if answer == right_variant:
                users_right_answers = cursor.execute("SELECT right_answers FROM users_answers "
                                                     "WHERE user_id = ?", (user_id,)).fetchone()
                if not users_right_answers:
                    users_right_answers = 0
                else:
                    users_right_answers = users_right_answers[0]

                if users_right_answers >= 9:
                    await give_achievements(user_id, '❓')
                if users_right_answers >= 49:
                    await give_achievements(user_id, '🧑🏻‍🎓')

                cursor.execute("UPDATE users_answers SET right_answers = ? "
                               "WHERE user_id = ?", (users_right_answers + 1, user_id))
                connection.commit()

                give_experience(user_id, 3)

            questions_for_user = []
            all_questions = cursor.execute("SELECT id FROM questions WHERE if_for_quiz = ?", (0,)).fetchall()
            for q in all_questions:
                users_ask = cursor.execute("SELECT users FROM questions WHERE id = ?", (q[0],)).fetchone()[0].split()
                if str(user_id) not in users_ask:
                    questions_for_user.append(q[0])

            if not questions_for_user:
                await bot.answer_callback_query(str(call.id), text='Кажется вы ответили на все существующие вопросы! '
                                                                   'Так держать!', show_alert=True)
            else:
                await bot.answer_callback_query(str(call.id))

                back_button = InlineKeyboardButton(text='↩️ Назад', callback_data='Назад из вопросов')
                next_button = InlineKeyboardButton(text='ДАЛЬШЕ ➡️', callback_data=f"вопросы")
                # ikb_menu.add(next_button)
                inline_keyboard.append([back_button, next_button])

            chat_id = call.message.chat.id
            message_id = call.message.message_id

            ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=inline_keyboard)

            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text='none')
async def none(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))


@dp.callback_query_handler(text_contains='Назад из вопросов')
async def back_from_questions(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'quizzes')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❓ Случайный вопрос', callback_data=f'вопросы'),
                                            InlineKeyboardButton(text='🎲 Викторина недели',
                                                                 callback_data='викторина недели')

                                        ],
                                        [
                                            InlineKeyboardButton(text='📊 Список лидеров', callback_data=f'лидеры'),
                                            InlineKeyboardButton(text='ℹ️ Информация',
                                                                 callback_data=f'информация вопросы')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='прочее'),
                                        ]
                                    ]
                                    )
    chat_id = call.message.chat.id
    await call.message.delete()
    await bot.send_photo(chat_id=chat_id, photo=image, reply_markup=ikb_menu)


@dp.message_handler(text='/add-quiz')
async def add_quiz(message: Message):
    last_quiz_questions = cursor.execute("SELECT questions_ids FROM quiz").fetchone()
    if last_quiz_questions:
        cursor.execute("DELETE FROM quiz")
        for q in last_quiz_questions[0].split():
            cursor.execute("DELETE FROM questions WHERE id = ?", (int(q),))
            connection.commit()

    new_quiz_questions = cursor.execute("SELECT id FROM questions WHERE if_for_quiz = ?", (1,)).fetchmany(10)
    new_quiz_questions = ' '.join([str(i[0]) for i in new_quiz_questions])

    cursor.execute("INSERT INTO quiz VALUES (?, ?)", (new_quiz_questions, ''))
    connection.commit()

    try:
        await bot.send_message(chat_id=admins[0], text='Обновлена викторина недели')
    except Exception as e:
        print(e)


async def new_quiz():
    last_quiz_questions = cursor.execute("SELECT questions_ids FROM quiz").fetchone()
    if last_quiz_questions:
        cursor.execute("DELETE FROM quiz")
        for q in last_quiz_questions[0].split():
            cursor.execute("DELETE FROM questions WHERE id = ?", (int(q),))
            connection.commit()

    new_quiz_questions = cursor.execute("SELECT id FROM questions WHERE if_for_quiz = ?", (1,)).fetchmany(10)
    new_quiz_questions = ' '.join([str(i[0]) for i in new_quiz_questions])

    cursor.execute("INSERT INTO quiz VALUES (?, ?)", (new_quiz_questions, ''))
    connection.commit()

    try:
        await bot.send_message(chat_id=admins[0], text='Обновлена викторина недели')
    except Exception as e:
        print(e)


async def delete_user_ids():
    print('ok')
    data = cursor.execute("SELECT id FROM user_ids").fetchall()
    if data:
        for i in data:
            create_time = cursor.execute("SELECT create_time FROM user_ids WHERE id = ?", (i[0],)).fetchone()[0]
            now_time = time.time()

            if now_time - create_time >= 2 * 60 * 60:
                cursor.execute("DELETE FROM user_ids WHERE id = ?", (i[0],))
                connection.commit()


@dp.callback_query_handler(text='викторина недели')
async def week_quiz(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
                                        show_alert=True)
    else:
        quiz_users = cursor.execute("SELECT users FROM quiz").fetchone()[0]
        if str(user_id) in quiz_users:
            await bot.answer_callback_query(str(call.id), text='Вы уже прошли викторину! Дождитесь следующей недели 😁',
                                            show_alert=True)
        else:
            await bot.answer_callback_query(str(call.id))

            questions_for_quiz = cursor.execute("SELECT questions_ids FROM quiz").fetchone()[0].split()

            text = cursor.execute("SELECT text FROM questions WHERE id = ?",
                                  (int(questions_for_quiz[0]),)).fetchone()[0]
            variants = cursor.execute("SELECT variants FROM questions WHERE id = ?",
                                      (int(questions_for_quiz[0]),)).fetchone()[0].split('  ')

            question_text = f"--- <b>🎲 ВИКТОРИНА НЕДЕЛИ</b> ---\n\n" \
                            f"<b><i>Вопрос 1 из 10:</i></b>\n\n" \
                            f"{text}\n\n" \
                            f"-                                -"

            ikb_menu = InlineKeyboardMarkup(row_width=1)
            emoji = ['1️⃣', '2️⃣', '3️⃣']
            count = 0
            for v in variants:
                button = InlineKeyboardButton(text=f"{emoji[count]} {v}",
                                              callback_data=f"викторина_{questions_for_quiz[0]}_{count + 1}")
                ikb_menu.add(button)
                count += 1

            await call.message.delete()
            await call.message.answer(question_text, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='викторина')
async def quiz_answer(call: CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if not check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
                                        show_alert=True)
    else:
        quiz_users = cursor.execute("SELECT users FROM quiz").fetchone()[0].split()
        if str(user_id) in quiz_users:
            await bot.answer_callback_query(str(call.id), text='Вы уже прошли эту викторину!', show_alert=True)
        else:
            answers = call.data.split('_')[2]
            question_id = int(call.data.split('_')[1])

            users_quizzes = cursor.execute("SELECT all_answers FROM users_answers WHERE user_id = ?",
                                           (user_id,)).fetchone()
            if not users_quizzes:
                cursor.execute("INSERT INTO users_answers VALUES (?, ?, ?, ?)", (user_id, 0, 0, 0))

            questions_for_quiz: list = cursor.execute("SELECT questions_ids FROM quiz").fetchone()[0].split()
            if str(question_id) not in questions_for_quiz:
                await bot.answer_callback_query(str(call.id), text='Эта викторина уже недоступна, пройдите новую',
                                                show_alert=True)
            else:
                await bot.answer_callback_query(str(call.id))
                if str(question_id) == questions_for_quiz[-1]:
                    user_answers = answers.split()
                    right_answers = 0
                    count = 1

                    answer_right_text = ''
                    for q in questions_for_quiz:
                        all_variants = cursor.execute("SELECT variants FROM questions WHERE id = ?",
                                                      (q,)).fetchone()[0].split('  ')
                        right_answer = cursor.execute("SELECT right_variant FROM questions WHERE id = ?",
                                                      (q,)).fetchone()[0]
                        user_answer = all_variants[int(user_answers[count - 1]) - 1]

                        if user_answer == right_answer:
                            t = f"✅ <i><b>Вопрос {count}:</b>  {right_answer}</i>\n"
                            give_experience(user_id, 3)
                            right_answers += 1
                        else:
                            t = f"<i><b>❌ Вопрос {count}:</b>  {right_answer}</i>\n"

                        answer_right_text = answer_right_text + t
                        count += 1

                    quiz_users.append(str(user_id))
                    quiz_users = ' '.join(quiz_users)

                    cursor.execute("UPDATE quiz SET users = ?", (quiz_users,))
                    connection.commit()

                    user_quizzes = cursor.execute("SELECT quizzes FROM users_answers WHERE user_id = ?",
                                                  (user_id,)).fetchone()[0]
                    cursor.execute("UPDATE users_answers SET quizzes = ? WHERe user_id = ?",
                                   (user_quizzes + 1, user_id))
                    connection.commit()

                    if right_answers == 10:
                        await give_achievements(user_id, '🧩')

                    text = f"--- <b>🎲 ВИКТОРИНА НЕДЕЛИ</b> ---\n\n" \
                           f"<b><i>Ваш результат:</i></b>\n\n" \
                           f"Решено верно: {right_answers} / 10\n\n" \
                           f"<b><i>Правильные ответы:</i></b>\n\n" \
                           f"{answer_right_text}\n\n" \
                           f"/menu"

                    loading_lst = ['⬜️'] * 6
                    for c in range(1, len(loading_lst) + 1):
                        if c != 1:
                            loading_lst[c - 2] = '🟩'

                        loading_text = ''.join(loading_lst)
                        loading_text = f"--- <b>🎲 ВИКТОРИНА НЕДЕЛИ</b> ---\n\n" \
                                       f"<b><i>Подводим итоги...</i></b>\n\n" \
                                       f"{loading_text}"

                        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=loading_text,
                                                    reply_markup=None)
                        await asyncio.sleep(0.5)

                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=None)
                else:
                    last_question_index = questions_for_quiz.index(str(question_id))
                    question_id = questions_for_quiz[last_question_index + 1]

                    text = cursor.execute("SELECT text FROM questions WHERE id = ?",
                                          (question_id,)).fetchone()[0]
                    variants = cursor.execute("SELECT variants FROM questions WHERE id = ?",
                                              (question_id,)).fetchone()[0].split('  ')

                    question_text = f"--- <b>🎲 ВИКТОРИНА НЕДЕЛИ</b> ---\n\n" \
                                    f"<b><i>Вопрос {last_question_index + 2} из 10:</i></b>\n\n" \
                                    f"{text}\n\n" \
                                    f"-                                -"

                    ikb_menu = InlineKeyboardMarkup(row_width=1)
                    emoji = ['1️⃣', '2️⃣', '3️⃣']
                    count = 0
                    for v in variants:
                        callback_data = f"викторина_{question_id}_{answers + ' ' + str(count + 1)}"
                        button = InlineKeyboardButton(text=f"{emoji[count]} {v}", callback_data=callback_data)
                        ikb_menu.add(button)
                        count += 1

                    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=question_text,
                                                reply_markup=ikb_menu)


@dp.callback_query_handler(text='лидеры')
async def show_leaderboard(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id
    text = f'<b>---📊 Список лидеров---</b>\n\n'

    data = cursor.execute("SELECT * FROM users_answers").fetchall()

    for i in data:
        user_id_, right_answers, all_answers, quizzes = i
        user_score = right_answers + quizzes * 10

        cursor.execute("INSERT INTO users_scores VALUES (?, ?)", (user_id_, user_score))
        connection.commit()

    leaders = cursor.execute("SELECT * FROM users_scores ORDER BY score DESC").fetchall()
    count = 1
    print(leaders)
    for leader in leaders:
        leader_id = leader[0]
        score = leader[1]

        user_name = cursor.execute("SELECT name FROM profiles WHERE id = ?", (leader_id,)).fetchone()[0]
        # user_emoji = cursor.execute("SELECT emoji FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]

        if count == 1:
            place = '🥇'
        elif count == 2:
            place = '🥈'
        elif count == 3:
            place = '🥉'
        elif count <= 10:
            place = f"<b>{count}.</b>"
        elif leader_id == user_id:
            place = f"-----------------------------\n" \
                    f"<b>{count}.</b>"
        else:
            place = ''

        if place:
            leaderboard = f'{place} <code>{user_name}</code>: <i><b>{score}</b></i> очк.\n'
            text += leaderboard

        count += 1

    cursor.execute("DELETE FROM users_scores")
    connection.commit()

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data='Назад из лидеров')
        ]
    ])

    await call.message.delete()
    await call.message.answer(text, reply_markup=ikb_menu)


@dp.callback_query_handler(text='Назад из лидеров')
async def back_from_leaderboard(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'quizzes')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❓ Случайный вопрос', callback_data=f'вопросы'),
                                            InlineKeyboardButton(text='🎲 Викторина недели',
                                                                 callback_data='викторина недели'),

                                        ],
                                        [
                                            InlineKeyboardButton(text='📊 Список лидеров', callback_data=f'лидеры'),
                                            InlineKeyboardButton(text='ℹ️ Информация',
                                                                 callback_data=f'информация вопросы')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='прочее'),
                                        ]
                                    ]
                                    )

    chat_id = call.message.chat.id

    await call.message.delete()
    await bot.send_photo(chat_id=chat_id, photo=image, reply_markup=ikb_menu)


@dp.callback_query_handler(text='информация вопросы')
async def quiz_info(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    text = f"<b>---ℹ️ ИНФОРМАЦИЯ---</b>\n\n" \
           f"<b><i>❓ Случайный вопрос</i></b> - каждый день вам предлагается ответить на 5 случайных вопросов из " \
           f"большого списка. Ответив на один вопрос, вы сможете перейти к следующему (за правильный ответ " \
           f"начисляется опыт). Повторно одни и те же вопросы не попадаются.\n\n" \
           f"<b><i>🎲 Викторина недели</i></b> - пользователь может пройти специальную викторину, " \
           f"состоящую из 10 различных вопросов. Каждую неделю вопросы викторины обновляются.\n\n" \
           f"<b><i>📊 Список лидеров</i></b> - в списке отображаются 10 пользователей, набравшие наибольшее " \
           f"количество очков за правильные ответы на вопросы. Если вы не в топ-десятке, то ваша позиция покажется " \
           f"отдельно."

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data='Назад из лидеров')
        ]
    ])

    await call.message.delete()
    await call.message.answer(text, reply_markup=ikb_menu)
