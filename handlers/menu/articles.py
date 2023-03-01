import asyncio
import os

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InputFile, InputMedia

from loader import dp, connection, cursor, bot, storage
from states import AddComment, Search
from .functions_loader import create_ids_entry, get_ids, get_user_theme_picture
from .vip import check_vip


def get_inline_menu_for_article(article_id: int, user_id: int, photo_id: int = 0,
                                my_art: int = 0, now_list_index: int = None) -> InlineKeyboardMarkup:

    article_likes = cursor.execute("SELECT likes FROM articles WHERE id = ?", (article_id,)).fetchone()[0].split()
    if str(user_id) not in article_likes:
        like_color = '🤍'
    else:
        like_color = '❤️'

    comments = cursor.execute("SELECT id FROM comments WHERE article_id = ?", (article_id,)).fetchall()
    comments_amount = 0
    for i in comments:
        comments_amount += 1

    inline_keyboard = [
            InlineKeyboardButton(text=f'{like_color} {len(article_likes) if article_likes else ""}',
                                 callback_data=f'Лайк_{article_id}_{photo_id}_{my_art}_{now_list_index}'),
            InlineKeyboardButton(text=f'💬 {comments_amount}', callback_data=f'Комментарий_{article_id}'),
        ]

    if photo_id:
        inline_keyboard.append(InlineKeyboardButton(text='↩️', callback_data=f'Назад из статьи_'
                                                                             f'{photo_id}_{my_art}_{now_list_index}'))

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[inline_keyboard])

    return ikb_menu


def filter_articles(user_id: int, list_of_articles: list, reverse: bool = False):
    user_filter = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()

    user_articles_ids = []
    other_ids = []

    for i in list_of_articles:
        author_id = cursor.execute("SELECT author_id FROM articles WHERE id = ?", (int(i),)).fetchone()[0]
        if author_id:
            user_articles_ids.append(i)
        else:
            other_ids.append(i)

    if user_filter[0] == '1':
        if user_filter[1] == '0':
            return user_articles_ids + other_ids

        if reverse:
            user_articles_ids.reverse()
            other_ids.reverse()
        return user_articles_ids + other_ids
    else:
        result = []
        amounts = []

        for ids in [user_articles_ids, other_ids]:
            for article_id in ids:
                likes = cursor.execute("SELECT likes FROM articles WHERE id = ?",
                                       (article_id,)).fetchone()[0]
                likes_amount = len(likes.split())

                comments = cursor.execute("SELECT id FROM comments WHERE article_id = ?",
                                          (article_id,)).fetchall()
                comments_amount = len(comments)

                amount = likes_amount + comments_amount
                amounts.append(amount)
                if user_filter[1] == '0':
                    amounts.sort()
                else:
                    amounts.sort(reverse=True)

            sorted_ids = []

            for a in amounts:
                for article_id in ids:
                    likes = cursor.execute("SELECT likes FROM articles WHERE id = ?",
                                           (article_id,)).fetchone()[0]
                    likes_amount = len(likes.split())

                    comments = cursor.execute("SELECT id FROM comments WHERE article_id = ?",
                                              (article_id,)).fetchall()
                    comments_amount = len(comments)
                    amount = likes_amount + comments_amount

                    if a == amount:
                        sorted_ids.append(article_id)

            new_sorted_ids = []
            for i in sorted_ids:
                if i not in new_sorted_ids:
                    new_sorted_ids.append(i)

            result += new_sorted_ids

        print(result)
        return result


def to_list_of_lists(lst: list, user_id: int, reverse: bool = False) -> list:
    lst = filter_articles(user_id, lst, reverse=reverse)

    ids = [[]]
    c = 0
    for i in lst:
        ids[c].append(i)
        if len(ids[c]) == 6:
            ids.append([])
            c += 1
    return ids


def get_inline_keyboard_menu(ids: list, now_list_index: int, my_art: int = 0) -> InlineKeyboardMarkup:

    inline_keyboard = []

    for i in ids[now_list_index]:
        title = cursor.execute("SELECT title FROM articles WHERE id = ?", (i,)).fetchone()[0]
        button = InlineKeyboardButton(text=title if len(title) <= 30 else f'{title[:30]}...',
                                      callback_data=f'статья_{i}_{my_art}_{now_list_index}')
        inline_keyboard.append([button])

    button_back = InlineKeyboardButton(text='↩️', callback_data='статьи')
    if len(ids) >= 2:
        full_ids = []
        for i in ids:
            for j in i:
                full_ids.append(str(j))

        str_ids = ' '.join(full_ids)
        if not cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)", (str_ids, 'articles')).fetchone():
            ids_id = create_ids_entry(full_ids, 'articles')
        else:
            ids_id = cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)",
                                    (str_ids, 'articles')).fetchone()[0]

        button_next = InlineKeyboardButton(text='➡️', callback_data=f'след-список_{ids_id}_{now_list_index}')
        button_prev = InlineKeyboardButton(text='⬅️', callback_data=f'пред-список_{ids_id}_{now_list_index}')

        if ids[now_list_index] == ids[-1]:
            inline_keyboard.append([button_back, button_prev])
        elif now_list_index == 0:
            inline_keyboard.append([button_back, button_next])
        else:
            inline_keyboard.append([button_back, button_prev, button_next])
    else:
        inline_keyboard.append([button_back])

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=inline_keyboard)
    return ikb_menu


def get_comment(user_id: int, article_id: int, comments_list: list, now_index: int):

    comment_id = comments_list[now_index]

    str_comments_list = ' '.join(str(i) for i in comments_list)

    if not cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)", (str_comments_list,
                                                                                 'comments')).fetchone():
        ids_id = create_ids_entry(comments_list, 'comments')
    else:
        ids_id = cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)",
                                (str_comments_list, 'comments')).fetchone()[0]

    comment_text = cursor.execute("SELECT text FROM comments WHERE id = ?", (comment_id,)).fetchone()[0]
    author_id = cursor.execute("SELECT author_id FROM comments WHERE id = ?", (comment_id,)).fetchone()[0]
    author_name = cursor.execute("SELECT name FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]
    emoji = cursor.execute("SELECT emoji FROM profiles WHERE id = ?", (author_id,)).fetchone()[0]

    comment = f'<b>{emoji} {author_name} {emoji}</b> {"<i>(Вы)</i>" if user_id == author_id else ""}\n\n' \
              f'{comment_text}'

    first_row = [
        InlineKeyboardButton(text='↩️', callback_data=f'Назад из комментариев'),
        InlineKeyboardButton(text='💬➕', callback_data=f'Добавить комментарий_{article_id}'),

                ]
    second_row = []

    if user_id == author_id:
        first_row.append(InlineKeyboardButton(text='🗑❌', callback_data=f'Удалить комментарий_{comment_id}'),)

    if len(comments_list) > 1:

        second_row.append(InlineKeyboardButton(text='⬅️',
                                               callback_data=
                                               f'Пред-комментарий_{ids_id}_{now_index}_{article_id}'))
        second_row.append(InlineKeyboardButton(text='➡️',
                                               callback_data=
                                               f'След-комментарий_{ids_id}_{now_index}_{article_id}'))

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[first_row, second_row])

    return comment, ikb_menu


@dp.callback_query_handler(text='статьи')
async def to_articles(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'articles')
    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='📒 Читать\nстатьи',
                                                                 callback_data=f'читать статьи'),
                                            InlineKeyboardButton(text='📕 Мои\nстатьи',
                                                                 callback_data='мои статьи'),

                                        ],
                                        [
                                            InlineKeyboardButton(text='🖋 Написать\nстатью',
                                                                 callback_data='написать статью'),
                                            InlineKeyboardButton(text='📘 Справочник', callback_data='справочник')
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


@dp.callback_query_handler(text='читать статьи')
async def read_articles(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
                                        show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))

        user_id = call.from_user.id

        articles = cursor.execute("SELECT id FROM articles").fetchall()
        list_of_articles = []
        for a in articles:
            list_of_articles.append(a[0])

        ids = to_list_of_lists(list_of_articles, user_id, reverse=True)

        ikb_menu = get_inline_keyboard_menu(ids, 0, )

        message_to_edit = call.message.message_id
        chat_id = call.message.chat.id
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='след-список')
async def next_list_of_articles(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    now_index = int(call.data.split('_')[2]) + 1

    ids_id = int(call.data.split('_')[1])
    ids = get_ids(ids_id, 'articles')

    ids = [int(i) for i in ids]
    ids = to_list_of_lists(ids, user_id)

    ikb_menu = get_inline_keyboard_menu(ids, now_index)

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='пред-список')
async def prev_list_of_articles(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    now_index = int(call.data.split('_')[2]) - 1

    ids_id = int(call.data.split('_')[1])
    ids = get_ids(ids_id, 'articles')

    ids = [int(i) for i in ids]
    ids = to_list_of_lists(ids, user_id)

    ikb_menu = get_inline_keyboard_menu(ids, now_index)

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='статья_')
async def show_article(call: CallbackQuery):
    user_id = call.from_user.id
    article_id = int(call.data.split('_')[1])
    now_list_index = int(call.data.split('_')[3])

    author_id = cursor.execute("SELECT author_id FROM articles WHERE id = ?", (article_id,)).fetchone()[0]

    if not check_vip(user_id) and author_id != user_id:
        await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
                                        show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))

        my_art = int(call.data.split('_')[2])

        title = cursor.execute("SELECT title FROM articles WHERE id = ?", (article_id,)).fetchone()[0]
        description = cursor.execute("SELECT description FROM articles WHERE id = ?", (article_id,)).fetchone()[0]
        image = InputFile(os.path.join(f'images/articles/{article_id}.jpg'))

        chat_id = call.message.chat.id
        photo_id = await bot.send_photo(chat_id=chat_id, photo=image)
        photo_id = photo_id.message_id

        ikb_menu = get_inline_menu_for_article(article_id, user_id, photo_id=photo_id, my_art=my_art,
                                               now_list_index=now_list_index)

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


@dp.callback_query_handler(text_contains='Лайк')
async def like_article(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id
    article_id = int(call.data.split('_')[1])
    photo_id = int(call.data.split('_')[2])
    my_art = int(call.data.split('_')[3])
    now_list_index = int(call.data.split('_')[4])

    article_likes: list = cursor.execute("SELECT likes FROM articles WHERE id = ?", (article_id,)).fetchone()[0].split()
    if str(user_id) in article_likes:
        article_likes.remove(str(user_id))
    else:
        article_likes.append(str(user_id))

    cursor.execute("UPDATE articles SET likes = ? WHERE id = ?", (' '.join(article_likes), article_id))
    connection.commit()

    ikb_menu = get_inline_menu_for_article(article_id, user_id, photo_id=photo_id, my_art=my_art,
                                           now_list_index=now_list_index)

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Комментарий')
async def to_comments(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    article_id = int(call.data.split('_')[1])
    user_id = call.from_user.id

    comments = cursor.execute("SELECT id FROM comments WHERE article_id = ?", (article_id,)).fetchall()

    article_comments = []
    for i in comments:
        article_comments.append(i[0])

    if article_comments:
        comment, ikb_menu = get_comment(user_id, article_id, article_comments, 0)
        await call.message.answer(comment, reply_markup=ikb_menu)
    else:
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=
            [
                [
                    InlineKeyboardButton(text='💬➕ Добавить', callback_data=f'Добавить комментарий_{article_id}'),
                    InlineKeyboardButton(text='❌ Выйти', callback_data=f'Назад из комментариев')
                ]
            ]
                                        )
        await call.message.answer('Здесь пока нет комментариев!', reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='След-комментарий')
async def next_comment(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    ids_id = int(call.data.split('_')[1])
    comments_list = get_ids(ids_id, ids_type='comments')

    now_index = int(call.data.split('_')[2]) + 1
    article_id = int(call.data.split('_')[3])

    if now_index >= len(comments_list):
        now_index = 0

    comment, ikb_menu = get_comment(user_id, article_id, comments_list, now_index)
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=comment, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Пред-комментарий')
async def prev_comment(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    ids_id = int(call.data.split('_')[1])
    comments_list = get_ids(ids_id, ids_type='comments')

    now_index = int(call.data.split('_')[2]) - 1
    article_id = int(call.data.split('_')[3])

    if now_index < -(len(comments_list)):
        now_index = len(comments_list) - 1

    comment, ikb_menu = get_comment(user_id, article_id, comments_list, now_index)
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=comment, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Добавить комментарий')
async def add_comment(call: CallbackQuery):
    user_id = call.from_user.id
    article_id = int(call.data.split('_')[1])

    chat_id = call.message.chat.id

    state = FSMContext(storage=storage, chat=chat_id, user=user_id)

    await state.update_data(article_id=article_id)
    await bot.answer_callback_query(str(call.id), text='Введите ваш комментарий (одним текстовым сообщением):',
                                    show_alert=True)
    await AddComment.enter_comment_text.set()
    await call.message.delete()


@dp.message_handler(state=AddComment.enter_comment_text)
async def enter_comment(message: types.Message, state: FSMContext):
    answer = message.text
    user_id = message.from_user.id

    if len(answer) > 350:
        await message.answer("Слишком длинный комментарий! Попробуйте еще раз. (Максимум 350 символов)")
    else:
        last_id = 1
        ids = cursor.execute("SELECT id FROM comments").fetchall()
        if ids:
            last_id = ids[-1][0]

        data = await state.get_data()
        article_id = data.get('article_id')

        cursor.execute("INSERT INTO comments VALUES (?, ?, ?, ?)", (last_id + 1, article_id, user_id, answer))
        connection.commit()

        await state.finish()
        await message.delete()
        msg = await message.answer("Комментарий успешно добавлен!")

        await asyncio.sleep(1)
        await msg.delete()


@dp.callback_query_handler(text_contains='Удалить комментарий')
async def delete_comment(call: CallbackQuery):
    comment_id = int(call.data.split('_')[1])

    cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    connection.commit()

    await bot.answer_callback_query(str(call.id), text="Ваш комментарий успешно удален!", show_alert=True)
    await call.message.delete()


@dp.callback_query_handler(text='Назад из комментариев')
async def back_from_comments(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    await call.message.delete()


@dp.callback_query_handler(text_contains='Назад из статьи')
async def back_from_article(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    photo_id = int(call.data.split('_')[1])
    my_art = int(call.data.split('_')[2])
    now_list_index = int(call.data.split('_')[3])

    image = get_user_theme_picture(user_id, 'articles')

    if not my_art:
        articles = cursor.execute("SELECT id FROM articles").fetchall()
        list_of_articles = []
        for a in articles:
            list_of_articles.append(a[0])
    else:
        user_articles = cursor.execute("SELECT id FROM articles WHERE author_id = ?", (user_id,)).fetchall()

        list_of_articles = [i[0] for i in user_articles]

    ids = to_list_of_lists(list_of_articles, user_id)

    ikb_menu = get_inline_keyboard_menu(ids, now_list_index, my_art)

    chat_id = call.message.chat.id
    media = InputMedia(media=image)
    await call.message.delete()
    await bot.edit_message_media(chat_id=chat_id, media=media, message_id=photo_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text='мои статьи')
async def my_articles(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id
    user_articles = cursor.execute("SELECT id FROM articles WHERE author_id = ?", (user_id,)).fetchall()

    user_articles = [i[0] for i in user_articles]

    # image = InputFile(os.path.join('images/design/articles.jpg'))
    ids = to_list_of_lists(user_articles, user_id, reverse=True)

    ikb_menu = get_inline_keyboard_menu(ids, 0, my_art=1)

    message_to_edit = call.message.message_id
    chat_id = call.message.chat.id
    # media = InputMedia(media=image)
    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_to_edit, reply_markup=ikb_menu)


def get_guide_inline_menu(guides_list: list, now_id: int):

    str_guides = ' '.join([str(i) for i in guides_list])
    if not cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)", (str_guides, 'guides')).fetchone():
        ids_id = create_ids_entry(guides_list, 'guides')
    else:
        ids_id = cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)",
                                (str_guides, 'guides')).fetchone()[0]

    if len(guides_list) > 1:
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                InlineKeyboardButton(text='⬅️', callback_data=f'Гайд_пред_{ids_id}_{now_id}'),
                InlineKeyboardButton(text='➡️', callback_data=f'Гайд_след_{ids_id}_{now_id}')
            ],
            [
                InlineKeyboardButton(text='↩️ Назад', callback_data='справочник'),
            ]
        ])
    else:
        ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
            [
                InlineKeyboardButton(text='↩️ Назад', callback_data='справочник'),
            ]
        ])

    return ikb_menu


@dp.callback_query_handler(text='справочник')
async def handbook(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))
    user_id = call.from_user.id

    image = get_user_theme_picture(user_id, 'handbook')

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [
            InlineKeyboardButton(text='🔤 По алфавиту', callback_data='гайды по алфавиту'),
            InlineKeyboardButton(text='🔍 Поиск', callback_data='поиск гайдов')
        ],
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data='статьи'),
        ]
    ])

    chat_id = call.message.chat.id
    message_id = call.message.message_id
    media = InputMedia(media=image)

    await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text='гайды по алфавиту')
async def alphabetically(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
                                        show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))

        all_titles = cursor.execute("SELECT title FROM handbook").fetchall()
        all_titles = [i[0] for i in all_titles]

        sorted_titles = sorted(all_titles)
        sorted_ids = []
        for t in sorted_titles:
            g_id = cursor.execute("SELECT id FROM handbook WHERE title = ?", (t,)).fetchone()[0]
            sorted_ids.append(g_id)

        ikb_menu = get_guide_inline_menu(sorted_ids, sorted_ids[0])

        photo = InputFile(os.path.join(f'images/guides/{sorted_ids[0]}-handbook.jpg'))
        media = InputMedia(media=photo)
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='Гайд')
async def alphabetically(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
                                        show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))

        if_next = True if call.data.split('_')[1] == 'след' else False

        ids_id = int(call.data.split('_')[2])
        guides_list = get_ids(ids_id, ids_type='guides')

        guides_list = [int(i) for i in guides_list]
        now_id = int(call.data.split('_')[3])

        now_id_index = guides_list.index(now_id)
        if if_next:
            if now_id == guides_list[-1]:
                now_id = guides_list[0]
            else:
                now_id = guides_list[now_id_index + 1]
        else:
            if now_id == guides_list[0]:
                now_id = guides_list[len(guides_list) - 1]
            else:
                now_id = guides_list[now_id_index - 1]

        ikb_menu = get_guide_inline_menu(guides_list, now_id)

        photo = InputFile(os.path.join(f'images/guides/{now_id}-handbook.jpg'))
        media = InputMedia(media=photo)

        chat_id = call.message.chat.id
        message_id = call.message.message_id

        await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text='поиск гайдов')
async def search_guides(call: CallbackQuery):
    user_id = call.from_user.id

    if not check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
                                        show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))

        state = FSMContext(storage, chat=call.message.chat.id, user=call.from_user.id)

        await Search.guide_ingredient.set()
        message_to_delete = await call.message.answer("Введите название (часть названия) нужного ингредиента "
                                                      "(учитытывайте, что название некоторых ингредиентов указано"
                                                      " во множественном числе: <i>сливы, персики и т.д.</i>):")
        await state.update_data(message_to_delete=message_to_delete.message_id)
        await state.update_data(message_to_edit=call.message.message_id)


@dp.message_handler(state=Search.guide_ingredient)
async def enter_ingredient(message: types.Message, state: FSMContext):
    answer = message.text.lower()
    user_id = message.from_user.id

    if not check_vip(user_id):
        await message.answer('Этот раздел доступен только VIP-пользователям!')
        await state.finish()
    else:
        data = await state.get_data()
        message_to_delete = data.get('message_to_delete')
        message_to_edit = data.get('message_to_edit')

        await message.delete()
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message_to_delete)
        except Exception as e:
            print(e)

        if len(answer) < 3:
            ikb_menu = InlineKeyboardMarkup(row_width=1)
            close_button = InlineKeyboardButton(text='❌ Выйти', callback_data='выйти из поиска гайдов')
            ikb_menu.add(close_button)

            message_to_delete = await message.answer("Минимум 3 символа! Попробуйте еще раз:", reply_markup=ikb_menu)
            await state.update_data(message_to_delete=message_to_delete.message_id)
        else:
            all_titles = cursor.execute("SELECT title FROM handbook").fetchall()
            all_titles = [i[0] for i in all_titles]

            result = []
            for title in all_titles:
                if answer in title:
                    g_id = cursor.execute("SELECT id FROM handbook WHERE title = ?", (title,)).fetchone()[0]
                    result.append(g_id)

            if not result:
                ikb_menu = InlineKeyboardMarkup(row_width=1)
                close_button = InlineKeyboardButton(text='❌ Выйти', callback_data='выйти из поиска гайдов')
                ikb_menu.add(close_button)

                message_to_delete = await message.answer("Не нашлось результатов по такому запросу! "
                                                         "Попробуйте еще раз:",
                                                         reply_markup=ikb_menu)
                await state.update_data(message_to_delete=message_to_delete.message_id)
            else:
                ikb_menu = get_guide_inline_menu(result, result[0])

                photo = InputFile(os.path.join(f'images/guides/{result[0]}-handbook.jpg'))
                media = InputMedia(media=photo)

                chat_id = message.chat.id
                message_id = message_to_edit

                await state.finish()
                await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text='выйти из поиска гайдов', state=Search.guide_ingredient)
async def exit_from_search_guides(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id), text='❌ Отменено')

    await call.message.delete()
    await state.finish()
