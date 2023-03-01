import os
import time
import datetime

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InputFile, InputMedia, InputMediaVideo
from PIL import Image, ImageFont, ImageDraw

from loader import dp, connection, cursor, bot
from aiogram.dispatcher.filters import Command
from aiogram import types
from states import Search
from .settings import filter_recipes
from .achievements import give_achievements
from ..users.experience import give_experience
from .menu import get_recipe
from .functions_loader import check_vip, get_user_theme_picture, delete_file
from utils.make_exercises import make_exercises, get_statistic

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


numbers = {
    '0': '0️⃣',
    '1': '1️⃣',
    '2': '2️⃣',
    '3': '3️⃣',
    '4': '4️⃣',
    '5': '5️⃣',
    '6': '6️⃣',
    '7': '7️⃣',
    '8': '8️⃣',
    '9': '9️⃣',
}


def update_statistic(user_id: int, column: str, value: any):
    data = cursor.execute(f"SELECT {column} FROM health_statistic WHERE user_id = ?", (user_id,)).fetchone()[0]
    if column == 'finished_programs' or column == 'exercises_amount':
        data = int(data) + value
        cursor.execute(f"UPDATE health_statistic SET '{column}' = ? WHERE user_id = ?", (data, user_id))
        connection.commit()
    else:
        days = data.split()
        weekday = datetime.datetime.today().weekday()
        now_time = int(time.time())

        if days:
            # last_day_time = int(days[-1].split('-')[1])
            if weekday != int(days[-1][0]):
                day = f'{weekday}-{now_time}-1'
                days.append(day)
            else:
                programs_amount = int(days[-1].split('-')[-1]) + 1
                day = f'{weekday}-{now_time}-{programs_amount}'
                days.append(day)
            # else:
            #     new_value = int(days[-1].split('-')[-1]) + 1
            #     day = f'{weekday}-{now_time}-{new_value}'
            #     days[-1] = day
        else:
            days = [f'{weekday}-{now_time}-1']

        days = ' '.join(days)

        cursor.execute("UPDATE health_statistic SET days = ? WHERE user_id = ?", (days, user_id))
        connection.commit()


def check_program_day(user_id: int, program_id: int):
    user_programs = cursor.execute("SELECT programs_ids FROM users_health_programs WHERE user_id = ?",
                                   (user_id,)).fetchone()[0]
    if_exists = False
    now_weekday = datetime.datetime.today().weekday()
    for p in user_programs.split('  '):
        if int(p.split('-')[0]) == program_id:
            data = p.split('-')[1].split(',')
            day = data[0]
            if_exists = True
            if len(data) < 2:
                return int(day), True, 0
            wait_time, weekday = data[1].split(':')
            if int(weekday) != now_weekday or time.time() >= int(wait_time) + 24 * 60 * 60:
                return int(day), True, 0

    if not if_exists:
        return 0, True, 0
    return int(day), False, int(wait_time)


def update_program_day(user_id: int, program_id: int):
    user_programs = cursor.execute("SELECT programs_ids FROM users_health_programs WHERE user_id = ?",
                                   (user_id,)).fetchone()[0]
    now_time = int(time.time())
    now_weekday = datetime.datetime.today().weekday()

    if_exists = False
    l_user_programs = user_programs.split('  ')
    for p in user_programs.split('  '):
        if int(p.split('-')[0]) == program_id:
            data = p.split('-')[1].split(',')
            day = int(data[0])

            new_data = f'{program_id}-{(day + 1)},{now_time}:{now_weekday}-0:0-0'

            l_user_programs.remove(p)
            l_user_programs.append(new_data)

            new_user_programs = '  '.join(l_user_programs)

            if_exists = True

            cursor.execute("UPDATE users_health_programs SET programs_ids = ? WHERE user_id = ?",
                           (new_user_programs, user_id))
            connection.commit()

    if not if_exists:
        day = 1


def get_exercise(user_id: int, program_id: int, exercise: str, day: int, skip: bool = False):
    user_programs = cursor.execute("SELECT programs_ids FROM users_health_programs WHERE user_id = ?",
                                   (user_id,)).fetchone()[0]
    for p in user_programs.split('  '):
        if int(p.split('-')[0]) == program_id:
            day = check_program_day(user_id, program_id)[0]
            ready_exercises_amount = int(p.split('-')[3])
            ready_exercises = p.split('-')[2].split(':')[0]
            skipped_exercises = p.split('-')[2].split(':')[1]
            # if continue_exercises:
            #     updated_ready_exercises_amount = len(ready_exercises.split(",")) if ready_exercises != '0' else 0
            #     updated_user_program = f'{program_id}-{day}-{ready_exercises}-{updated_ready_exercises_amount}'
            #
            #     updated_user_programs = user_programs.split()
            #     updated_user_programs.remove(p)
            #     updated_user_programs.append(updated_user_program)
            #
            #     cursor.execute("UPDATE users_health_programs SET programs_ids = ? WHERE user_id = ?",
            #                    (' '.join(updated_user_programs), user_id))
            #     connection.commit()

    exercises = cursor.execute("SELECT exercises FROM health_programs WHERE id = ?", (program_id,)).fetchone()[0]
    day_exercises = exercises.split('; ')[day - 1].split(', ')

    ready_exercises = ready_exercises.split(',') if ready_exercises != '0' else []
    skipped_exercises = skipped_exercises.split(',') if skipped_exercises != '0' else []
    remaining_exercises = []

    for ex in day_exercises:
        ex = ex.replace('-', '|')
        if ex in ready_exercises:
            ready_exercises.remove(ex)
        elif ex not in skipped_exercises:
            remaining_exercises.append(ex)

    if exercise == 'start':
        exercise = remaining_exercises[0]

        # exercise_id = day_exercises[len(ready_exercises.split(',')) if ready_exercises != '0' else 0]
        # exercise_id, repeats_amount = int(exercise_id.split('-')[0]), exercise_id.split('-')[1].replace(';', '')
    #     exercise_id = int(remaining_exercises[0].split('-')[0])
    #     repeats_amount = remaining_exercises[0].split('-')[1]
    # else:
    #     if exercise_id == 0:
    #         exercise_id = int(day_exercises[0].split('-')[0].replace(';', ''))
    #         repeats_amount = day_exercises[0].split('-')[1].replace(';', '')
    #     else:
    #         repeats_amount = day_exercises[int(exercise_id)].split('-')[1].replace(';', '')
    #         exercise_id = day_exercises[int(exercise_id)].split('-')[0]

    exercise_id = int(exercise.split('|')[0])
    repeats_amount = exercise.split('|')[1]

    exercise_title = cursor.execute("SELECT name FROM exercises WHERE id = ?", (exercise_id,)).fetchone()[0]
    exercise_text = cursor.execute("SELECT text FROM exercises WHERE id = ?", (exercise_id,)).fetchone()[0]

    global numbers
    if not skip:
        number_emoji = ''.join([numbers[i] for i in str(ready_exercises_amount + 1)])
    else:
        number_emoji = '*️⃣'

    if 'раз' in repeats_amount:
        repeats_amount = f'<i>Выполните упражнение <b>{repeats_amount}</b></i>'
    else:
        repeats_amount = f'<i>Выполняйте упражнение <b>{repeats_amount}</b></i>'

    caption = f"<b>{number_emoji} {exercise_title.capitalize()}</b>\n\n" \
              f"{repeats_amount}\n\n" \
              f"{exercise_text}"

    inline_keyboard = [InlineKeyboardButton(text='✅ Готово', callback_data=f'готово_{program_id}_{exercise}')]
    if ready_exercises_amount != len(day_exercises) and not skip:
        inline_keyboard.append(InlineKeyboardButton(text='➡️ Пропустить', callback_data=f'готово-пропустить_'
                                                                                        f'{program_id}_{exercise}'))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[

                                        inline_keyboard,

                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data=f'начать-программу_{program_id}'),
                                        ]
                                    ]
                                    )

    video = InputFile(os.path.join(f'videos/exercises/{exercise_id}.mp4'))
    # video = InputFile(os.path.join(f'images/exercises/1.jpg'))

    return caption, video, ikb_menu


# def create_health_program():
#     last_id = cursor.execute("SELECT id FROM health_programs").fetchall()
#     if not last_id:
#         last_id = 1
#     else:
#         last_id = last_id[-1][0]
#
#     title = 'сжигание веса'
#     difficulty = ''
#     sex = 'ж'
#     ration = 'фрукты и овощи, мясо, рыба, фасоль'
#     exercises = '1'
#     image_id = 1
#
#     cursor.execute("INSERT INTO health_programs VALUES (?, ?, ?, ?, ?, ?, ?)",
#                    (last_id, title, difficulty, sex, ration, exercises, image_id))
#     connection.commit()


# create_health_program()

async def show_health_program(call: CallbackQuery, send_new_message: bool = False):
    user_id = call.from_user.id

    program_id = int(call.data.split('_')[1])

    user_programs = cursor.execute("SELECT programs_ids FROM users_health_programs WHERE user_id = ?",
                                   (user_id,)).fetchone()

    if not user_programs:
        day = 1
        days_amount = 28
        cursor.execute("INSERT INTO users_health_programs VALUES (?, ?)", (user_id, f'{program_id}-1-0:0-0'))
        connection.commit()
    else:
        user_programs = user_programs[0]
        program_exists = False
        for p in user_programs.split('  '):
            if int(p.split('-')[0]) == program_id:
                program_exercises = cursor.execute("SELECT exercises FROM health_programs WHERE id = ?",
                                                   (program_id,)).fetchone()[0]

                days_amount = len(program_exercises.split('; '))
                day = check_program_day(user_id, program_id)[0]
                program_exists = True
        if not program_exists:
            day = 1
            days_amount = 28
            if user_programs:
                user_programs += f'  {program_id}-1-0:0-0'
            else:
                user_programs = f'{program_id}-1-0:0-0'
            cursor.execute("UPDATE users_health_programs SET programs_ids = ? WHERE user_id = ?",
                           (user_programs, user_id))
            connection.commit()

    data = ''
    if days_amount < day:
        text = '✅ Завершить'
        data = '-завершено'
    else:
        if day < 2:
            text = '✴️ Начать'
        else:
            text = '✴️ Продолжить'

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🍎 Рацион',
                                                                 callback_data=f'Рацион_{program_id}'),
                                            InlineKeyboardButton(text=text,
                                                                 callback_data=f'начать-программу{data}_{program_id}'),

                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data=f'программы'),
                                        ]
                                    ]
                                    )

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    image, path = make_exercises(user_id, program_id, day=day)
    media = InputMedia(media=image)

    delete_file(path)

    if not send_new_message:
        await bot.edit_message_media(chat_id=chat_id, message_id=message_to_edit, media=media,
                                     reply_markup=ikb_menu)
    else:
        await bot.send_photo(chat_id=chat_id, photo=image, reply_markup=ikb_menu)


@dp.callback_query_handler(text='здоровье')
async def health(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id

    finished_programs = \
        cursor.execute("SELECT finished_programs FROM health_statistic WHERE user_id = ?", (user_id,)).fetchone()
    if not finished_programs:
        cursor.execute("INSERT INTO health_statistic VALUES (?, ?, ?, ?, ?)", (user_id, 0, 0, '', 0))
        connection.commit()

    image = get_user_theme_picture(user_id, 'health')

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🏋🏻 Программы', callback_data=f'программы'),
                                            InlineKeyboardButton(text='📆 Моя статистика', callback_data='Статистика'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='назад'),
                                        ]
                                    ]
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    media = InputMedia(media=image)
    await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='программы')
async def programs(call: CallbackQuery):
    user_id = call.from_user.id
    if check_vip(user_id):
        await call.answer()

        user_sex = cursor.execute("SELECT gender FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
        if user_sex == 'м':
            user_sex = 0
        else:
            user_sex = 1

        image = get_user_theme_picture(user_id, 'programs')

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='🧘🏻 Поясница',
                                                                     callback_data=f'программа_2'),

                                                InlineKeyboardButton(text='⏰ Утр. зарядка',
                                                                     callback_data='программа_5'),
                                            ],
                                            [
                                                InlineKeyboardButton(text='🏃🏻‍♂️ Сжигание жира',
                                                                     callback_data=f'программа_1{user_sex}'),

                                                InlineKeyboardButton(text='🤸🏻 Разработка мышц',
                                                                     callback_data='разработка мышц'),
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад', callback_data='здоровье'),
                                            ]
                                        ]
                                        )
        message_to_edit = call.message.message_id
        chat_id = call.message.chat.id
        media = InputMedia(media=image)
        if call.data == 'программы_':
            await call.message.delete()
            await bot.send_photo(chat_id=chat_id, photo=image, reply_markup=ikb_menu)
        else:
            await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_to_edit,
                                         reply_markup=ikb_menu)
    else:
        await call.answer("Этот раздел доступен только VIP-пользователям!", show_alert=True)


@dp.callback_query_handler(text_contains='программа')
async def health_program(call: CallbackQuery):
    user_id = call.from_user.id

    if check_vip(user_id):
        await call.answer()
        await show_health_program(call)
    else:
        await call.answer("Этот раздел доступен только VIP-пользователям!")


@dp.callback_query_handler(text_contains='начать-программу')
async def start_health_program(call: CallbackQuery):
    user_id = call.from_user.id
    program_id = int(call.data.split('_')[1])

    if check_vip(user_id):
        await call.answer()
        if len(call.data.split('-')) > 2:
            user_programs = cursor.execute("SELECT programs_ids FROM users_health_programs WHERE user_id = ?",
                                           (user_id,)).fetchone()[0].split('  ')
            for p in user_programs:
                if int(p.split('-')[0]) == program_id:
                    user_programs.remove(p)
                    break

            user_programs = '  '.join(user_programs)
            cursor.execute("UPDATE users_health_programs SET programs_ids = ? WHERE user_id = ?",
                           (user_programs, user_id))
            connection.commit()

            update_statistic(user_id, 'finished_programs', 1)

            program_title = cursor.execute("SELECT title FROM health_programs WHERE id = ?", (program_id,)).fetchone()[0]
            text = f"<b>🎉 Поздравляем!</b>\n\n" \
                   f"Вы успешно завершили программу <i><b>{program_title.lower()}</b></i>\n\n" \
                   f"Советуем не останавливаться на достигнутом и пройти другие программы, либо повторить эту."

            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                [
                                                    InlineKeyboardButton(text='↩️ К программам',
                                                                         callback_data=f'программы_')

                                                ]
                                            ]
                                            )

            await call.message.delete()
            await call.message.answer(text, reply_markup=ikb_menu)

        else:
            day, permission, wait_time = check_program_day(user_id, program_id)
            user_programs = cursor.execute("SELECT programs_ids FROM users_health_programs WHERE user_id = ?",
                                           (user_id,)).fetchone()[0]
            ready_exercises_amount = 0
            for p in user_programs.split('  '):
                if int(p.split('-')[0]) == program_id:
                    ready_exercises_amount = int(p.split('-')[3])

            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                [
                                                    InlineKeyboardButton(text=
                                                                         '▶️ Приступить' if not ready_exercises_amount
                                                                         else '▶️ Продолжить',
                                                                         callback_data=f'приступить_{program_id}'),
                                                    InlineKeyboardButton(text='❌ Сбросить',
                                                                         callback_data=f'сбросить_{program_id}'),

                                                ],
                                                [
                                                    InlineKeyboardButton(text='↩️ Назад',
                                                                         callback_data=f'программа_{program_id}'),
                                                ]
                                            ]
                                            )

            message_to_edit = call.message.message_id
            chat_id = call.message.chat.id
            media, path = make_exercises(user_id, program_id, if_exercises=True, day=day)
            media = InputMedia(media=media)

            delete_file(path)

            await bot.edit_message_media(chat_id=chat_id, message_id=message_to_edit, media=media,
                                         reply_markup=ikb_menu)
    else:
        await call.answer("Этот раздел доступен только VIP-пользователям!")


@dp.callback_query_handler(text_contains='приступить')
async def start_health_program_exercises(call: CallbackQuery):
    user_id = call.from_user.id
    program_id = int(call.data.split('_')[1])

    if check_vip(user_id):
        day, permission, wait_time = check_program_day(user_id, program_id)

        if permission:
            await call.answer()

            caption, video, ikb_menu = get_exercise(user_id, program_id, 'start', day)
            chat_id = call.message.chat.id

            await call.message.delete()
            msg = await call.message.answer("Загрузка...")
            await bot.send_video(chat_id=chat_id, video=video, caption=caption, reply_markup=ikb_menu)
            await bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
        else:
            await call.answer(f"⏰ Откроется завтра", show_alert=True)
    else:
        await call.answer("Этот раздел доступен только VIP-пользователям!")


@dp.callback_query_handler(text_contains='готово')
async def exercise_ready(call: CallbackQuery):
    user_id = call.from_user.id
    program_id = int(call.data.split('_')[1])
    exercise = call.data.split('_')[2]

    chat_id = call.message.chat.id

    skip = False
    if len(call.data.split('-')) > 1:
        skip = True

    user_programs = cursor.execute("SELECT programs_ids FROM users_health_programs WHERE user_id = ?",
                                   (user_id,)).fetchone()[0]
    new_users_program = []
    for program in user_programs.split('  '):
        if int(program.split('-')[0]) == program_id:
            day = check_program_day(user_id, program_id)[0]
            ready_exercises = program.split('-')[2].split(':')[0]
            skipped_exercises = program.split('-')[2].split(':')[1]

            ready_exercises_amount = int(program.split('-')[3]) + 1
            if not skip:
                if ready_exercises == '0':
                    ready_exercises = str(exercise)
                else:
                    ready_exercises += ',' + str(exercise)
            else:
                if skipped_exercises == '0':
                    skipped_exercises = str(exercise)
                else:
                    skipped_exercises += ',' + str(exercise)

            program = f'{program_id}-{day}-{ready_exercises}:{skipped_exercises}-{ready_exercises_amount}'

        new_users_program.append(program)

    new_users_program = '  '.join(new_users_program)

    cursor.execute("UPDATE users_health_programs SET programs_ids = ? WHERE user_id = ?", (new_users_program, user_id))
    connection.commit()

    program_exercises = cursor.execute("SELECT exercises FROM health_programs WHERE id = ?",
                                       (program_id,)).fetchone()[0]
    day_exercises = program_exercises.split('; ')[day - 1].split(', ')

    # next_exercise_index = int(day_exercises[int(ready_exercises_amount)].replace(';', ''))
    # next_exercise_index = len(ready_exercises.split(','))
    # next_exercise_index = int(ready_exercises_amount)
    ready_exercises = ready_exercises.split(',') if ready_exercises != '0' else []
    ready_exercises_ = ready_exercises.copy()
    skipped_exercises = skipped_exercises.split(',') if skipped_exercises != '0' else []
    remaining_exercises = []

    for ex in day_exercises:
        ex = ex.replace('-', '|')
        if ex in ready_exercises:
            ready_exercises.remove(ex)
        elif ex not in skipped_exercises:
            remaining_exercises.append(ex)

    if not remaining_exercises and not skipped_exercises:
        update_statistic(user_id, 'exercises_amount', 1)
        update_statistic(user_id, 'days', '')
        update_program_day(user_id, program_id)

        await call.answer('Поздравляем! Программа на сегодня выполнена!', show_alert=True)
        await show_health_program(call)
    elif not remaining_exercises and skipped_exercises:
        caption, video, ikb_menu = get_exercise(user_id, program_id, skipped_exercises[0], day, skip=True)

        new_users_program = []
        for program in user_programs.split('  '):
            if int(program.split('-')[0]) == program_id:
                day = check_program_day(user_id, program_id)[0]
                # ready_exercises = program.split('-')[2].split(':')[0]
                # skipped_exercises = program.split('-')[2].split(':')[1]
                ready_exercises_.append(skipped_exercises[0])
                skipped_exercises = skipped_exercises[1:]

                ready_exercises = ','.join(ready_exercises_)
                skipped_exercises = ','.join(skipped_exercises) if skipped_exercises else '0'

                program = f'{program_id}-{day}-{ready_exercises}:{skipped_exercises}-{ready_exercises_amount}'
                print(program)

            new_users_program.append(program)

        new_users_program = '  '.join(new_users_program)

        cursor.execute("UPDATE users_health_programs SET programs_ids = ? WHERE user_id = ?",
                       (new_users_program, user_id))
        connection.commit()

        update_statistic(user_id, 'exercises_amount', 1)

        await call.answer("Немного отдохните и приступайте к следующему упражнению", show_alert=True)
        await call.message.delete()
        msg = await call.message.answer("Загрузка...")
        await bot.send_video(chat_id=chat_id, video=video, caption=caption, reply_markup=ikb_menu)
        await msg.delete()
    else:
        if skip:
            await call.answer("Вернемся к этому упражнению в конце программы", show_alert=True)
        else:
            update_statistic(user_id, 'exercises_amount', 1)
            await call.answer("Немного отдохните и приступайте к следующему упражнению", show_alert=True)

        caption, video, ikb_menu = get_exercise(user_id, program_id, remaining_exercises[0], day)

        await call.message.delete()
        msg = await call.message.answer("Загрузка...")

        await bot.send_video(chat_id=chat_id, video=video, caption=caption, reply_markup=ikb_menu)
        await msg.delete()



    #     if not skip:
    #         update_statistic(user_id, 'exercises_amount', 1)
    #         await call.answer("Немного отдохните и приступайте к следующему упражнению", show_alert=True)
    #     else:
    #         await call.answer("Вернемся к этому упражнению в конце программы", show_alert=True)
    # except IndexError:
    #     print(day_exercises, ready_exercises.split(','))
    #     if len(day_exercises) != len(ready_exercises.split(',')):
    #         skip_exercises = []
    #         ready_exercises = ready_exercises.split(',')
    #         ind = 0
    #         for p in day_exercises:
    #             if p.split('-')[0] in ready_exercises:
    #                 ready_exercises.remove(p.split('-')[0])
    #             else:
    #                 if p != '0':
    #                     skip_exercises.append(p)
    #                     skip_index = ind
    #                     break
    #             ind += 1
    #
    #         try:
    #             caption, video, ikb_menu = get_exercise(user_id, program_id, skip_index, day,
    #                                                     skip=True)
    #             media = InputMediaVideo(media=video, caption=caption)
    #             message_to_edit = call.message.message_id
    #             chat_id = call.message.chat.id
    #
    #             update_statistic(user_id, 'exercises_amount', 1)
    #
    #             await call.message.delete()
    #             msg = await call.message.answer("Загрузка...")
    #             await call.answer("Немного отдохните и приступайте к следующему упражнению", show_alert=True)
    #             await bot.send_video(chat_id=chat_id, video=video, caption=caption, reply_markup=ikb_menu)
    #             await msg.delete()
    #         except IndexError:
    #             update_statistic(user_id, 'exercises_amount', 1)
    #             update_statistic(user_id, 'days', '')
    #             update_program_day(user_id, program_id)
    #
    #             await call.answer('Поздравляем! Программа на сегодня выполнена!', show_alert=True)
    #             await show_health_program(call)
    #     else:
    #         # day, permission, wait_time = check_program_day(user_id, program_id)
    #         # cursor.execute("UPDATE users_health_programs SET programs_ids = ? WHERE user_id = ?",
    #         #                (f'{program_id}-{day}-0-0', user_id))
    #         # connection.commit()
    #         update_statistic(user_id, 'exercises_amount', 1)
    #         update_statistic(user_id, 'days', '')
    #         update_program_day(user_id, program_id)
    #
    #         await call.answer('Поздравляем! Программа на сегодня выполнена!', show_alert=True)
    #         await show_health_program(call)
    # else:
    #     caption, video, ikb_menu = get_exercise(user_id, program_id, next_exercise_index, day)
    #
    #     media = InputMediaVideo(media=video, caption=caption)
    #     message_to_edit = call.message.message_id
    #     chat_id = call.message.chat.id
    #
    #     await call.message.delete()
    #     msg = await call.message.answer("Загрузка...")
    #     await bot.send_video(chat_id=chat_id, video=video, caption=caption, reply_markup=ikb_menu)
    #     await msg.delete()


















# мыщцы
@dp.callback_query_handler(text='разработка мышц')
async def muscle_building(call: CallbackQuery):
    await call.answer("🛠 В разработке", show_alert=True)

    # user_id = call.from_user.id
    #
    # user_sex = cursor.execute("SELECT gender FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    # if user_sex == 'м':
    #     user_sex = 0
    # else:
    #     user_sex = 1
    #
    # ikb_menu = InlineKeyboardMarkup(row_width=1,
    #                                 inline_keyboard=[
    #                                     [
    #                                         InlineKeyboardButton(text='1️⃣ Грудь',
    #                                                              callback_data=f'Разработка_1{user_sex}'),
    #
    #                                         InlineKeyboardButton(text='3️⃣ Пресс',
    #                                                              callback_data=f'Разработка_3{user_sex}'),
    #                                     ],
    #                                     [
    #                                         InlineKeyboardButton(text='2️⃣ Руки',
    #                                                              callback_data=f'Разработка_2{user_sex}'),
    #
    #                                         InlineKeyboardButton(text='4️⃣ Ноги',
    #                                                              callback_data=f'Разработка_4{user_sex}'),
    #                                     ],
    #                                     [
    #                                         InlineKeyboardButton(text='↩️ Назад', callback_data='программы'),
    #                                     ]
    #                                 ]
    #                                 )
    # message_to_edit = call.message.message_id
    # chat_id = call.message.chat.id
    #
    # await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Растяжка')
async def stretch(call: CallbackQuery):
    user_id = call.from_user.id

    user_sex = cursor.execute("SELECT gender FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    if user_sex == 'м':
        user_sex = 0
    else:
        user_sex = 1

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='1️⃣ Всё тело',
                                                                 callback_data=f'программа_1'),

                                            InlineKeyboardButton(text='3️⃣ Верх. часть',
                                                                 callback_data=f'программа_3'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='2️⃣ Поясница',
                                                                 callback_data=f'программа_2'),

                                            InlineKeyboardButton(text='4️⃣ Ниж. часть',
                                                                 callback_data=f'программа_4'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='программы'),
                                        ]
                                    ]
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='быстрое')
async def speedy(call: CallbackQuery):
    await call.answer()

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='1️⃣ Утр. зарядка',
                                                                 callback_data=f'программа_5'),
                                            InlineKeyboardButton(text='2️⃣ Сжиг. жира',
                                                                 callback_data=f'программа_6'),
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='программы'),
                                        ]
                                    ]
                                    )
    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text='сжигание веса')
async def stretch(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🍎 Рацион',
                                                                 callback_data=f'Рацион_сжигание веса'),
                                            InlineKeyboardButton(text='✅ Начать',
                                                                 callback_data=f'начать_программу'),

                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data=f'программы'),
                                        ]
                                    ]
                                    )

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    media, path = make_exercises(user_id, if_ration=False)
    media = InputMedia(media=media)

    delete_file(path)

    await bot.edit_message_media(chat_id=chat_id, message_id=message_to_edit, media=media,
                                 reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Разработка')
async def building(call: CallbackQuery):
    body_part = call.data.split('_')[1]

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='🟢 Легко',
                                                                     callback_data=f'программа_{body_part + "1"}'),
                                                InlineKeyboardButton(text='🟡 Умеренно',
                                                                     callback_data=f'программа_{body_part + "2"}'),
                                                InlineKeyboardButton(text='🔴 Сложно',
                                                                     callback_data=f'программа_{body_part + "3"}'),
                                            ],
                                            [
                                                InlineKeyboardButton(text='↩️ Назад',
                                                                     callback_data='разработка мышц'),
                                            ]
                                        ]
                                    )

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Рацион')
async def ration(call: CallbackQuery):
    user_id = call.from_user.id

    if check_vip(user_id):
        program_id = int(call.data.split('_')[1])
        program_ration = cursor.execute("SELECT ration FROM health_programs WHERE id = ?", (program_id,)).fetchone()[0]
        if not program_ration:
            await call.answer("Для этой программы не предусмотрено специального питания", show_alert=True)
        else:
            await call.answer()
            ikb_menu = InlineKeyboardMarkup(row_width=1,
                                            inline_keyboard=[
                                                    [
                                                        InlineKeyboardButton(text='🚴🏻‍♂️ Упражнения',
                                                                             callback_data=f'программа_{program_id}'),
                                                        InlineKeyboardButton(text='📚 Рецепты',
                                                                             callback_data=f'Рецепты рациона_{program_id}'),

                                                    ],
                                                    [
                                                        InlineKeyboardButton(text='↩️ Назад',
                                                                             callback_data=f'программы'),
                                                    ]
                                                ]
                                            )

            message_to_edit = call.message.message_id
            chat_id = call.message.chat.id
            media, path = make_exercises(user_id, program_id, if_ration=True)
            media = InputMedia(media=media)

            delete_file(path)

            await bot.edit_message_media(chat_id=chat_id, message_id=message_to_edit, media=media, reply_markup=ikb_menu)
    else:
        await call.answer("Этот раздел доступен только VIP-пользователям!")


@dp.callback_query_handler(text_contains='Рецепты рациона')
async def ration_recipes(call: CallbackQuery):
    await call.answer()

    program_id = int(call.data.split('_')[1])

    recipes = cursor.execute("SELECT ration FROM health_programs WHERE id = ?", (program_id,)).fetchone()[0]
    ids = recipes.split('; ')[1].split()

    await get_recipe(call, ids, ids[0], call=True)


@dp.callback_query_handler(text_contains='сбросить')
async def reset_program(call: CallbackQuery):
    user_id = call.from_user.id
    program_id = int(call.data.split('_')[1])

    await call.message.delete()
    if len(call.data.split('_')) > 2:
        confirm = call.data.split('_')[2]
        if confirm == 'подтвердить':
            user_programs = cursor.execute("SELECT programs_ids FROM users_health_programs WHERE user_id = ?",
                                           (user_id,)).fetchone()[0].split()
            for p in user_programs:
                if int(p.split('-')[0]) == program_id:
                    user_programs.remove(p)
                    break

            user_programs = ' '.join(user_programs)
            cursor.execute("UPDATE users_health_programs SET programs_ids = ? WHERE user_id = ?",
                           (user_programs, user_id))
            connection.commit()

            await call.answer("Ваш прогресс успешно сброшен", show_alert=True)
        if confirm == 'отклонить':
            await call.answer()

        await show_health_program(call, send_new_message=True)
    else:
        await call.answer()

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='✅ Да',
                                                                     callback_data=f'сбросить_{program_id}_подтвердить'),
                                                InlineKeyboardButton(text='❌ Нет',
                                                                     callback_data=f'сбросить_{program_id}_отклонить'),

                                            ]
                                        ]
                                        )

        await call.message.answer("❓ Вы действительно хотите сбросить прогресс? "
                                  "Придется начать программу с 1-го дня.",
                                  reply_markup=ikb_menu)


@dp.callback_query_handler(text='Статистика')
async def statistic(call: CallbackQuery):
    await call.answer()

    user_id = call.from_user.id

    # update_statistic(user_id, 'days', 0)
    photo = get_statistic(user_id)

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data=f'здоровье'),
                                        ]
                                    ]
                                    )

    media = InputMedia(media=photo)
    chat_id = call.from_user.id
    message_id = call.message.message_id

    await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


async def update_week_statistics():
    ids = [i[0] for i in cursor.execute("SELECT user_id FROM health_statistic").fetchall()]
    for i in ids:
        cursor.execute("UPDATE health_statistic SET days = ? WHERE user_id = ?", ('', i))
        connection.commit()

    ids = [i[0] for i in cursor.execute("SELECT user_id FROM questions_time").fetchall()]
    for i in ids:
        cursor.execute("UPDATE questions_time SET questions_amount = ? WHERE user_id = ?", (0, i))
        connection.commit()
