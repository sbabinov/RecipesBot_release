import os

from PIL import Image, ImageFont, ImageDraw
from aiogram.types import InputFile

from loader import cursor, connection


def paste_checkbox(image: Image, checkboxes_amount: int):
    checkbox = Image.open(os.path.join('images/exercises/checkbox.png'))
    checkbox.thumbnail((80, 80))
    image = image.convert(mode='RGBA')

    count = 0
    x = 715
    y = 335
    for c in range(checkboxes_amount):
        if count % 7 == 0 and count != 0:
            x = 715
            y += 70
        image.alpha_composite(checkbox, (x, y))
        count += 1
        x += 55

    return image

# image = Image.open(os.path.join('../images/exercises/template2.jpg'))
# image = paste_checkbox(image, 28)
# image.show()


def make_exercises(user_id: int = 1, program_id: int = 1, if_ration: bool = False, if_exercises: bool = False,
                   day: int = 1):
    # program = 'Сжигание жира'
    # difficulty = 'сложная'
    # sex = 'ж'
    # ration = 'фрукты и овощи, мясо, рыба, фасоль'
    # exercises = '1, 2, 3; 2, 1, 2, 3; 1, 2, 5, 6, 2'
    # image_id = 1
    program = cursor.execute("SELECT title FROM health_programs WHERE id = ?", (program_id,)).fetchone()[0]
    difficulty = cursor.execute("SELECT difficulty FROM health_programs WHERE id = ?", (program_id,)).fetchone()[0]
    sex = cursor.execute("SELECT gender FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    ration = cursor.execute("SELECT ration FROM health_programs WHERE id = ?", (program_id,)).fetchone()[0]
    exercises = cursor.execute("SELECT exercises FROM health_programs WHERE id = ?", (program_id,)).fetchone()[0]
    image_id = cursor.execute("SELECT image_id FROM health_programs WHERE id = ?", (program_id,)).fetchone()[0]

    day = int(day)

    if not if_ration and not if_exercises:
        main_image = Image.open(os.path.join('images/exercises/template2.jpg'))
        main_image = paste_checkbox(main_image, day - 1)
    else:
        main_image = Image.open(os.path.join('images/exercises/template.jpg'))
    # 1 page

    # exercise_image = Image.open(os.path.join('../images/exercises/stretch.jpg'))
    if not if_exercises:
        exercise_image = Image.open(os.path.join(f'images/exercises/{image_id}.jpg'))

        exercise_image.thumbnail((400, 400))
        exercise_image_y = int(447 - exercise_image.height)
        main_image.paste(exercise_image, (185, exercise_image_y))

    idraw = ImageDraw.Draw(main_image)

    handwritten_font = ImageFont.truetype(os.path.join('fonts/handwritten.ttf'), size=40)
    handwritten_bold_font = ImageFont.truetype(os.path.join('fonts/handwritten_bold.ttf'), size=45)

    if not if_exercises:
        if len(program) > 16:
            text = ''
            row = ''
            count = 0
            for word in program.split():
                if len(row + ' ' + word) <= 16:
                    if row:
                        row = row + ' ' + word
                    else:
                        row += word
                    if count + 1 >= len(program.split()):
                        text += f'{row}\n'
                else:
                    text += f'{row}\n'
                    row = word
                count += 1
        else:
            text = program

        text = text.capitalize()
        print(text)

        row_y = 460
        for row in text.split('\n'):
            row_x = (465 - (len(row) * 25)) // 2 + 150
            idraw.text((row_x, row_y), font=handwritten_bold_font, text=row, fill='blue')
            row_y += 40

        if difficulty:
            idraw.text((180, 650), font=handwritten_font, text='Сложность :', fill='black')

            if difficulty == 'легкая':
                color = 'green'
            elif difficulty == 'умеренная':
                color = 'yellow'
            else:
                color = 'red'

            idraw.text((390, 650), font=handwritten_font, text=difficulty, fill=color)
        if sex:
            idraw.text((180, 590), font=handwritten_font, text='Программа :', fill='black')
            idraw.text((390, 590), font=handwritten_font, text='женская' if sex == 'ж' else 'мужская', fill='black')

        # page 2

        if not if_ration:
            idraw.text((760, 150), font=handwritten_bold_font, text='Выполнение:', fill='black')
            idraw.rounded_rectangle((720, 280, 1095, 300), fill="white", outline="black",
                                    radius=7)

            progress = 100 * (day - 1) // 28
            weight = 375 * progress // 100
            if weight:
                idraw.rounded_rectangle((720, 280, 720 + weight, 300), fill="#32CD32", outline="black",
                                        radius=7)
        else:
            ration = ration.split('; ')[0].split(', ')

            idraw.text((790, 150), font=handwritten_bold_font, text='Питание:', fill='black')

            y = 250
            for i in ration:
                idraw.text((710, y), font=handwritten_font, text=f'- {i}', fill='black')
                y += 40
    else:
        exercises = exercises.split('; ')[day - 1].split(', ')
        exercises = [e.split('-')[0] for e in exercises]
        day_exercises = []
        for i in exercises:
            i = i.replace(';', '')
            print(i)
            exercise = cursor.execute("SELECT name FROM exercises WHERE id = ?", (i,)).fetchone()[0]
            day_exercises.append(exercise)

        idraw.text((325, 125), font=handwritten_bold_font, text=f'День {day}', fill='black')
        x = 180
        y = 225
        ex_num = 1
        for ex in day_exercises:
            text = ''
            for word in ex.split():
                if len(text.split('\n')[-1] + ' ' + word) <= 20:
                    text += word + ' '
                else:
                    text += '\n' + word + ' '
            count = 0
            for row in text.split('\n'):
                if y > 680:
                    x = 710
                    y = 120
                if not count:
                    idraw.text((x, y), font=handwritten_font, text=f'{ex_num}. {row.capitalize()}', fill='black')
                    ex_num += 1
                    count += 1
                else:
                    idraw.text((x, y), font=handwritten_font, text=f'{row}', fill='black')
                y += 40



            #     count += 1
            #     if len(text + word) > 20:
            #         if if_new_line:
            #             idraw.text((180, y), font=handwritten_font, text=f'{text}', fill='black')
            #         else:
            #             idraw.text((180, y), font=handwritten_font, text=f'- {text}', fill='black')
            #         text = word
            #         y += 40
            #         if_new_line = True
            #     else:
            #             # idraw.text((180, y), font=handwritten_font, text=f'{text}', fill='black')
            #         # else:
            #
            #             # idraw.text((180, y), font=handwritten_font, text=f'- {text}', fill='black')
            #         text += word + ' '
            #         if count == len(ex.split()):
            #             if if_new_line:
            #                 idraw.text((180, y), font=handwritten_font, text=f'{text}', fill='black')
            #             else:
            #                 idraw.text((180, y), font=handwritten_font, text=f'- {text}', fill='black')
            #         if if_new_line:
            #             if_new_line = False
            # y += 40

    # main_image.show()
    path = os.path.join(f'images/exercises/users/{user_id}.jpg')

    main_image = main_image.convert(mode='RGB')

    main_image.save(path)
    photo = InputFile(path)

    return photo, path


def get_statistic(user_id: int):
    finished_programs = \
        cursor.execute("SELECT finished_programs FROM health_statistic WHERE user_id = ?", (user_id,)).fetchone()[0]
    exercises_amount = \
        cursor.execute("SELECT exercises_amount FROM health_statistic WHERE user_id = ?", (user_id,)).fetchone()[0]
    days = \
        cursor.execute("SELECT days FROM health_statistic WHERE user_id = ?", (user_id,)).fetchone()[0]
    days_in_a_row = \
        cursor.execute("SELECT days_in_a_row FROM health_statistic WHERE user_id = ?", (user_id,)).fetchone()[0]

    main_image = Image.open(os.path.join('images/exercises/template.jpg'))
    main_image = main_image.convert('RGBA')

    handwritten_font = ImageFont.truetype(os.path.join('fonts/handwritten.ttf'), size=40)
    handwritten_bold_font = ImageFont.truetype(os.path.join('fonts/handwritten_bold.ttf'), size=45)

    checkbox = Image.open(os.path.join('images/exercises/checkbox.png'))
    checkbox.thumbnail((80, 80))

    cell = Image.open(os.path.join('images/exercises/cell.png'))
    cell.thumbnail((90, 90))

    idraw = ImageDraw.Draw(main_image)
    idraw.text((240, 110), font=handwritten_bold_font, text='Статистика', fill='black')

    idraw.text((220, 300), font=handwritten_font, text='Выполнено', fill='black')
    idraw.text((250, 350), font=handwritten_font, text='программ :', fill='black')
    idraw.text((420, 350), font=handwritten_font, text=str(finished_programs), fill='green')
    idraw.text((220, 400), font=handwritten_font, text='Выполнено', fill='black')
    idraw.text((250, 450), font=handwritten_font, text='упражнений :', fill='black')
    idraw.text((450, 450), font=handwritten_font, text=str(exercises_amount), fill='green')
    # idraw.text((220, 500), font=handwritten_font, text='Дней подряд', fill='black')
    # idraw.text((250, 550), font=handwritten_font, text='без перерыва :', fill='black')
    # idraw.text((470, 550), font=handwritten_font, text=str(days_in_a_row), fill='green')

    # page 2
    days_of_the_week = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    days_programs_amounts = [0, 0, 0, 0, 0, 0, 0]
    days = days.split()
    for d in days:
        days_programs_amounts[int(d[0])] = int(d.split('-')[-1])

    y = 100
    count = 0
    for d in days_of_the_week:
        idraw.text((700, y + 10), font=handwritten_font, text=d, fill='black')
        main_image.alpha_composite(cell, (750, y))

        if days_programs_amounts[count]:
            main_image.alpha_composite(checkbox, (770, y - 10))

            idraw.text((850, y + 10), font=handwritten_font,
                       text=f'Программ : {days_programs_amounts[count]}', fill='black')

        y += 90
        count += 1

    path = os.path.join(f'images/exercises/users/{user_id}.jpg')

    main_image = main_image.convert(mode='RGB')

    main_image.save(path)
    photo = InputFile(path)

    return photo

# get_statistic()
