import os

from PIL import Image, ImageFont, ImageDraw
from aiogram.types import InputFile

from loader import cursor


def make_guide(guide_id: int, title: str = None, text: str = None):
    if not title:
        title = cursor.execute("SELECT title FROM handbook WHERE id = ?", (guide_id,)).fetchone()[0]
    if not text:
        text = cursor.execute("SELECT text FROM handbook WHERE id = ?", (guide_id,)).fetchone()[0]

    handbook = Image.open(os.path.join('images/guides/handbook/handbook.jpg'))
    product = Image.open(os.path.join(f'images/guides/{guide_id}.jpg'))

    product.thumbnail((500, 500))
    handbook.thumbnail((1500, 1500))

    font = ImageFont.truetype(os.path.join('fonts/woodstick.ttf'), size=60)

    idraw = ImageDraw.Draw(handbook)

    x = (660 - product.width) // 2 + 90
    handbook.paste(product, (x, 200))

    if len(title) > 13:
        title = title.split()

        length = len(title[0]) * 47
        x1 = (660 - length) // 2 + 90
        # y1 = 550
        y1 = 200 + product.height + 30

        idraw.text((x1, y1), title[0], font=font, fill='black')

        length = len(title[1]) * 47
        x1 = (660 - length) // 2 + 90
        y1 = 200 + product.height + 100

        idraw.text((x1, y1), title[1], font=font, fill='black')
    else:
        length = len(title) * 47
        x1 = (660 - length) // 2 + 90
        y1 = 200 + product.height + 30

        idraw.text((x1, y1), title, font=font, fill='black')

    if len(text) > 29:
        text = text.split()
        row = ''
        new_text = ''
        row_count = 1

        for word in text:
            if len(row + ' ' + word) <= 29:
                row += word
                row += ' '
            else:
                new_text += f"{row}\n"

                row = word + ' '
                row_count += 1

        new_text += row

        if row_count > 14:
            return False
        else:
            font = ImageFont.truetype(os.path.join('fonts/mavka.ttf'), size=40)
            idraw.text((800, 100), new_text, font=font, fill='black')

            save_path = os.path.join(f'images/guides/{guide_id}-handbook.jpg')

            handbook.save(save_path)

            photo = InputFile(save_path)

            return photo
