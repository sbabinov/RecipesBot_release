import os.path
import datetime

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.dispatcher.filters import Command
from aiogram import types

from loader import dp, connection, cursor, bot
from data import admins
from states import AddArticle
from ..menu.achievements import give_achievements

from PIL import Image

from ..menu.settings import check_notifications_settings
from ..users.experience import give_experience
from ..menu.articles import get_inline_menu_for_article


@dp.callback_query_handler(text='добавить статью админ')
async def add_article(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    if call.from_user.id in admins:
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[[InlineKeyboardButton(text='❌ Выход',
                                                                                            callback_data=
                                                                                            'выход из добавления')]])

        await call.message.answer('Введите автора статьи:', reply_markup=ikb_menu)
        await AddArticle.author_id.set()


@dp.message_handler(state=AddArticle.author_id)
async def enter_author_id(message: types.Message, state: FSMContext):
    answer = int(message.text)

    await state.update_data(author_id=answer)
    await AddArticle.title.set()
    await message.answer('Введите название статьи:')


@dp.message_handler(state=AddArticle.title)
async def enter_type(message: types.Message, state: FSMContext):
    answer = message.text
    await state.update_data(title=answer)
    await AddArticle.img.set()
    await message.answer('Отправьте фото статьи:')


@dp.message_handler(state=AddArticle.img, content_types=ContentType.DOCUMENT)
async def enter_photo(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file = await bot.get_file(file_id=file_id)
    last_id = cursor.execute("SELECT id FROM articles").fetchall()
    if not last_id:
        rec_id = 1
    else:
        rec_id = last_id[-1][0] + 1
    print(rec_id)
    await state.update_data(rec_id=rec_id)
    await file.download(destination_file=os.path.join('images/articles/' + str(rec_id) + '.jpg'))

    file = Image.open('images/articles/' + str(rec_id) + '.jpg')
    file.thumbnail((600, 600))
    file.save('images/articles/' + str(rec_id) + '.jpg')

    await AddArticle.description.set()
    await message.answer("Введите текст статьи:")


@dp.message_handler(state=AddArticle.description)
async def enter_description(message: types.Message, state: FSMContext):
    answer = message.text
    await state.update_data(description=answer)

    data = await state.get_data()
    title: str = data.get('title')
    rec_id = data.get('rec_id')
    description = data.get('description')
    author_id = data.get('author_id')

    path = os.path.join('images/articles/' + str(rec_id) + '.jpg')

    caption = f"<b><i>{title}</i></b>\n\n" \
              f"{description}\n\n" \
              f"{f'<i>Автор: {author_id}</i>' if author_id != 0 else ''}"

    await bot.send_photo(photo=types.InputFile(path), chat_id=message.chat.id)
    await message.answer(caption)
    await message.answer('Оставляем?')

    await AddArticle.confirm.set()


@dp.message_handler(state=AddArticle.confirm)
async def confirm(message: types.Message, state: FSMContext):
    answer = message.text
    data = await state.get_data()
    rec_id = data.get('rec_id')

    if answer == 'да':
        title: str = data.get('title')
        description = data.get('description')
        author_id = data.get('author_id')

        date = str(datetime.date.today())

        cursor.execute("INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)", (rec_id, title, description, author_id,
                                                                             date, '', ''))

        if author_id:
            recipes: str = cursor.execute("SELECT articles FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]
            recipes: list = recipes.split()
            recipes.append(str(rec_id))

            if len(recipes) >= 3:
                await give_achievements(author_id, '✏️')

            recipes = ' '.join(recipes)
            cursor.execute("UPDATE profiles SET articles = ? WHERE id = ?", (recipes, author_id))

            give_experience(author_id, 10, rec_id=int(rec_id))

            author_subscribers = \
                cursor.execute("SELECT subscribers FROM profiles WHERE id = ?", (author_id,)).fetchone()[0].split()

            try:
                text = f"Ваша статья <b>{title}</b> успешно прошла модерацию, теперь она видна всем пользователям"
                await bot.send_message(chat_id=author_id, text=text)
            except:
                pass

            for s in author_subscribers:
                author_name = cursor.execute("SELECT name FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]
                emoji = cursor.execute("SELECT emoji FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]

                notification_text = f"{emoji} <b>{author_name}</b> опубликовал(а) новую статью!"
                ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                    [
                        InlineKeyboardButton(text=f'👁‍🗨 Посмотреть', callback_data=f'посмотреть статью_{rec_id}')
                    ]
                ])

                await check_notifications_settings(int(s), notification_text, reply_markup=ikb_menu)

        connection.commit()

        await state.finish()
    if answer == 'нет':
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[[InlineKeyboardButton(text='❌ Выход',
                                                                                            callback_data=
                                                                                            'выход из добавления')]])
        try:
            os.remove(os.path.join(f'images/articles/{rec_id}.jpg'))
        except Exception as e:
            print(e)

        await AddArticle.author_id.set()
        await message.answer('Введите автора статьи:', reply_markup=ikb_menu)


@dp.callback_query_handler(state=AddArticle.author_id, text='выход из добавления')
async def enter_author_id(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.answer_callback_query(str(call.id), text='Успешно', show_alert=True)


@dp.callback_query_handler(text_contains='посмотреть статью')
async def show_recipe(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id
    article_id = int(call.data.split('_')[1])

    title = cursor.execute("SELECT title FROM articles WHERE id = ?", (article_id,)).fetchone()[0]
    description = cursor.execute("SELECT description FROM articles WHERE id = ?", (article_id,)).fetchone()[0]
    image = InputFile(os.path.join(f'images/articles/{article_id}.jpg'))

    # article_likes = cursor.execute("SELECT likes FROM articles WHERE id = ?", (article_id,)).fetchone()[0].split()
    # if str(user_id) not in article_likes:
    #     like_color = '🤍'
    # else:
    #     like_color = '❤️'

    # comments = cursor.execute("SELECT id FROM comments WHERE article_id = ?", (article_id,)).fetchall()
    # comments_amount = 0
    # for i in comments:
    #     comments_amount += 1

    chat_id = call.message.chat.id
    photo_id = await bot.send_photo(chat_id=chat_id, photo=image)
    photo_id = photo_id.message_id

    print(photo_id)

    ikb_menu = get_inline_menu_for_article(article_id, user_id)

    # ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
    #     [
    #         InlineKeyboardButton(text=f'{like_color} {len(article_likes) if article_likes else ""}',
    #                              callback_data=f'Лайк_{article_id}_{photo_id}'),
    #         InlineKeyboardButton(text=f'💬 {comments_amount}', callback_data=f'Комментарий_{article_id}'),
    #     ]
    # ])

    author_id = cursor.execute("SELECT author_id FROM articles WHERE id = ?", (article_id,)).fetchone()[0]
    if not author_id:
        author = ''
    elif author_id == user_id:
        author = '<i>Это ваша статья!</i>'
    else:
        author = cursor.execute("SELECT name FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]
        author = f'<i>Автор: <code>{author}</code></i>'

    article = f'<b>{title}</b>\n\n' \
              f'{description}\n\n' \
              f'{author}'

    await call.message.delete()
    await call.message.answer(article, reply_markup=ikb_menu)
