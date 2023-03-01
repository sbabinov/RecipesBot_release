import os.path
import time
import random

from aiogram.types import InputFile

from loader import cursor, connection
from data.config import admins


def get_ids(entry_id: int, ids_type: str = 'recipes'):
    data = cursor.execute("SELECT ids FROM user_ids WHERE (id, type) = (?, ?)", (entry_id, ids_type)).fetchone()[0]
    # ids = [int(i) for i in data.split()]
    ids = data.split()

    return ids


def create_ids_entry(ids: list, ids_type: str):

    entry_id = int(f'{int(time.time())}{random.randint(1, 99999)}')
    str_ids = ' '.join([str(i) for i in ids])
    time_now = int(time.time())

    cursor.execute("INSERT INTO user_ids VALUES (?, ?, ?, ?)", (entry_id, str_ids, time_now, ids_type))
    connection.commit()

    return entry_id


def check_vip(user_id: int) -> int:
    if user_id == admins[0]:
        return 200000000

    user_vip_time = cursor.execute("SELECT VIP FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    now_time = int(time.time())

    if now_time >= user_vip_time:
        return 0
    return user_vip_time - now_time


def get_profile(user_id: int) -> str:
    data = cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,)).fetchone()
    print(data)
    user_id, username, gender, emoji, favorites, recipes, subscriptions, subscribers, likes, create_date, exp, vip, \
        get_vip_date, filters, achievements, articles = data

    lvl = 0
    progress = exp * 100 // 10
    rank = 'Новичок'

    if exp >= 10:
        lvl = 1
        progress = exp * 100 // 20
        rank = 'Стажер'
    if exp >= 20:
        lvl = 2
        progress = exp * 100 // 40
        rank = 'Доставщик'
    if exp >= 40:
        lvl = 3
        progress = exp * 100 // 60
        rank = 'Официант'
    if exp >= 60:
        lvl = 4
        progress = exp * 100 // 100
        rank = 'Мойщик продуктов'
    if exp >= 100:
        lvl = 5
        progress = exp * 100 // 150
        rank = 'Картофельных дел мастер'
    if exp >= 150:
        lvl = 6
        progress = exp * 100 // 210
        rank = 'Кондитер'
    if exp >= 210:
        lvl = 7
        progress = exp * 100 // 270
        rank = 'Повар'
    if exp >= 270:
        lvl = 8
        progress = exp * 100 // 350
        rank = 'Помощник шефа'
    if exp >= 350:
        lvl = 9
        progress = exp * 100 // 420
        rank = 'Шеф-повар'
    if exp >= 420:
        lvl = 10
        progress = exp * 100 // 500
        rank = 'Повар всех времен и народов'

    if exp >= 500:
        lvl = (exp // 50) + 4
        progress = (lvl - 4) * 50

    user_recipes = recipes.split()
    amount_likes = 0
    for r in user_recipes:
        likes = cursor.execute("SELECT likes FROM feedback WHERE rec_id = ?", (int(r),)).fetchone()[0]
        amount_likes += len(likes.split())

    bar = ''

    if progress > 12:
        bar += '🟩'
    if progress > 24:
        bar += '🟩'
    if progress > 37:
        bar += '🟩'
    if progress > 49:
        bar += '🟩'
    if progress > 62:
        bar += '🟩'
    if progress > 74:
        bar += '🟩'
    if progress > 87:
        bar += '🟩'

    bar += f'{"⬜️" * (8 - len(bar))}'

    profile = f"{emoji} <b>{username}</b> {emoji}\n\n" \
              f"    {'👑 VIP-пользователь' if check_vip(user_id) else ''}\n" \
              f"<b>{lvl} {bar} {lvl + 1}</b>\n" \
              f"<i>{rank} ({lvl} лвл)</i>\n" \
              f"--------------------------------------------\n" \
              f"📚 Написано рецептов: {len(recipes.split())}\n" \
              f"--------------------------------------------\n" \
              f"👤 Подписчики: {len(subscribers.split())}\n" \
              f"--------------------------------------------\n" \
              f"❤️ Лайки: {amount_likes}\n" \
              f"--------------------------------------------\n" \
              f"🕓 Профиль создан: {create_date}\n" \
              f"--------------------------------------------\n"

    return profile


def get_user_theme_picture(user_id: int, picture_name: str):
    if not check_vip(user_id):
        user_theme = 'light-classic'
    else:
        user_theme = cursor.execute("SELECT theme FROM users_themes WHERE user_id = ?", (user_id,)).fetchone()
        if not user_theme:
            user_theme = 'light-classic'

            cursor.execute("INSERT INTO users_themes VALUES (?, ?)", (user_id, user_theme))
            connection.commit()
        else:
            user_theme = user_theme[0]

    theme_type = user_theme.split('-')[0]
    theme_color = user_theme.split('-')[1]

    path = os.path.join(f'images/design/{theme_type}/{theme_color}/{picture_name}.jpg')
    picture = InputFile(path)

    return picture


def delete_file(path: str) -> None:
    try:
        os.remove(path)
    except Exception as e:
        print(e)


def check_username(username: str):
    russian_letters = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    english_letters = 'abcdefghijklmnopqrstuvwxyz'

    if ' ' in username:
        return "В имени пользователя не должно быть пробелов!"
    if len(username) > 25:
        return "Слишком длинное имя пользователя! Придумайте покороче (максимум 25 символов):"
    if len(username) < 5:
        return "Слишком короткое имя пользователя! Придумайте подлиннее (минимум 5 символов):"

    if username[0].lower() not in russian_letters and username[0].lower() not in english_letters:
        return "Имя пользователя должно начинаться с русской или английской буквы!"

    return True
