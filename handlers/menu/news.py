import os

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InputFile, InputMedia

from handlers.menu.functions_loader import create_ids_entry, get_ids
from loader import dp, cursor, bot


def get_news(ids: list, now_id: int):
    inline_keyboard = []
    str_ids = ' '.join([str(i) for i in ids])
    if not cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)", (str_ids, 'news')).fetchone():
        ids_id = create_ids_entry(ids, 'news')
    else:
        ids_id = cursor.execute("SELECT id FROM user_ids WHERE (ids, type) = (?, ?)",
                                (str_ids, 'news')).fetchone()[0]

    button_back = InlineKeyboardButton(text='↩️ Назад', callback_data='прочее')
    inline_keyboard.append(button_back)

    if len(ids) > 1:
        if now_id != ids[0]:
            button_prev = InlineKeyboardButton(text='⬅️', callback_data=f'пред-новость_{ids_id}_{now_id}')
            inline_keyboard.append(button_prev)
        if now_id != ids[-1]:
            button_next = InlineKeyboardButton(text='➡️', callback_data=f'след-новость_{ids_id}_{now_id}')
            inline_keyboard.append(button_next)

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[inline_keyboard])

    title: str = cursor.execute("SELECT title FROM news WHERE id = ?", (now_id,)).fetchone()[0]
    text: str = cursor.execute("SELECT text FROM news WHERE id = ?", (now_id,)).fetchone()[0]
    date: str = cursor.execute("SELECT date FROM news WHERE id = ?", (now_id,)).fetchone()[0]
    photo = InputFile(os.path.join(f'images/news/{now_id}.jpg'))

    text = f"<b>{title}</b>\n\n" \
           f"{text}\n\n" \
           f"<i>{date}</i>"

    return title, photo, text, ikb_menu


@dp.callback_query_handler(text='новости')
async def news(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    all_news_ids = cursor.execute("SELECT id FROM news").fetchall()
    if all_news_ids:
        all_news_ids = [i[0] for i in all_news_ids]
        all_news_ids.reverse()
        now_id = all_news_ids[0]

        title, photo, text, ikb_menu = get_news(all_news_ids, now_id)

        chat_id = call.message.chat.id
        message_id = call.message.message_id

        media = InputMedia(media=photo, caption=text)

        await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='след-новость')
async def next_news(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ids_id = int(call.data.split('_')[1])
    ids = [int(i) for i in get_ids(ids_id, ids_type='news')]

    now_id = int(call.data.split('_')[2]) - 1

    title, photo, text, ikb_menu = get_news(ids, now_id)

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    media = InputMedia(media=photo, caption=text)

    await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='пред-новость')
async def prev_news(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ids_id = int(call.data.split('_')[1])
    ids = [int(i) for i in get_ids(ids_id, ids_type='news')]

    now_id = int(call.data.split('_')[2]) + 1

    title, photo, text, ikb_menu = get_news(ids, now_id)

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    media = InputMedia(media=photo, caption=text)

    await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=ikb_menu)
