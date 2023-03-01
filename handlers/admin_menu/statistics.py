from aiogram.types import CallbackQuery

from loader import dp, connection, cursor, bot
from ..menu.vip import check_vip


@dp.callback_query_handler(text_contains='статистика')
async def bot_statistics(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    current_users_amount = len(cursor.execute("SELECT id FROM profiles").fetchall())
    current_vip_users_amount = 0
    for user_id in cursor.execute("SELECT id FROM profiles").fetchall():
        if check_vip(user_id[0]):
            current_vip_users_amount += 1
    current_recipes_amount = len(cursor.execute("SELECT id FROM recipes").fetchall())
    current_articles_amount = len(cursor.execute("SELECT id FROM articles").fetchall())
    current_timers_amount = len(cursor.execute("SELECT user_id FROM timers").fetchall())
    current_work_timers_amount = len(cursor.execute("SELECT timer_id FROM timers_work WHERE if_works = ?",
                                                    (1,)).fetchall())
    current_comments_amount = len(cursor.execute("SELECT id FROM comments").fetchall())
    current_questions_amount = len(cursor.execute("SELECT id FROM questions").fetchall())

    if_exists = cursor.execute("SELECT users FROM statistics WHERE id = ?", (1,)).fetchone()
    if not if_exists:
        cursor.execute("INSERT INTO statistics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (1, current_users_amount, current_vip_users_amount, current_recipes_amount,
                        current_articles_amount, current_timers_amount, current_work_timers_amount,
                        current_comments_amount, current_questions_amount))
        connection.commit()

    old_users_amount = cursor.execute("SELECT users FROM statistics WHERE id = ?", (1,)).fetchone()[0]
    old_users_amount = f"(+{current_users_amount - old_users_amount})"\
        if current_users_amount > old_users_amount else ''

    old_vip_users_amount = cursor.execute("SELECT vip_users FROM statistics WHERE id = ?", (1,)).fetchone()[0]
    old_vip_users_amount = f"(+{current_vip_users_amount - old_vip_users_amount})" \
        if current_vip_users_amount > old_vip_users_amount else ''

    old_recipes_amount = cursor.execute("SELECT recipes FROM statistics WHERE id = ?", (1,)).fetchone()[0]
    old_recipes_amount = f"(+{current_recipes_amount - old_recipes_amount})" \
        if current_recipes_amount > old_recipes_amount else ''

    old_articles_amount = cursor.execute("SELECT articles FROM statistics WHERE id = ?", (1,)).fetchone()[0]
    old_articles_amount = f"(+{current_articles_amount - old_articles_amount})" \
        if current_articles_amount > old_articles_amount else ''

    old_timers_amount = cursor.execute("SELECT timers FROM statistics WHERE id = ?", (1,)).fetchone()[0]
    old_timers_amount = f"(+{current_timers_amount - old_timers_amount})" \
        if current_timers_amount > old_timers_amount else ''

    old_work_timers_amount = cursor.execute("SELECT timers_work FROM statistics WHERE id = ?", (1,)).fetchone()[0]
    old_work_timers_amount = f"(+{current_work_timers_amount - old_work_timers_amount})" \
        if current_work_timers_amount > old_work_timers_amount else ''

    old_comments_amount = cursor.execute("SELECT comments FROM statistics WHERE id = ?", (1,)).fetchone()[0]
    old_comments_amount = f"(+{current_comments_amount - old_comments_amount})" \
        if current_comments_amount > old_comments_amount else ''

    old_questions_amount = cursor.execute("SELECT questions FROM statistics WHERE id = ?", (1,)).fetchone()[0]
    old_questions_amount = f"(+{current_questions_amount - old_questions_amount})" \
        if current_questions_amount > old_questions_amount else ''

    cursor.execute("UPDATE statistics SET (users, vip_users, recipes, articles, timers, timers_work, comments) = "
                   "(?, ?, ?, ?, ?, ?, ?) WHERE id = ?", (current_users_amount, current_vip_users_amount,
                                                          current_recipes_amount, current_articles_amount,
                                                          current_timers_amount, current_work_timers_amount,
                                                          current_comments_amount, 1))
    connection.commit()

    text = f"📊 <b>Статистика</b>\n\n" \
           f"👤 Пользователи: <code>{current_users_amount}</code> <i>{old_users_amount}</i>\n" \
           f"👑 VIP-пользователи: <code>{current_vip_users_amount}</code> <i>{old_vip_users_amount}</i>\n" \
           f"📚 Рецепты: <code>{current_recipes_amount}</code> <i>{old_recipes_amount}</i>\n" \
           f"📓 Статьи: <code>{current_articles_amount}</code> <i>{old_articles_amount}</i>\n" \
           f"⏱ Таймеры: <code>{current_timers_amount}</code> <i>{old_timers_amount}</i>\n" \
           f"⏰ Работающие таймеры: <code>{current_work_timers_amount}</code> <i>{old_work_timers_amount}</i>\n" \
           f"💬 Комментарии: <code>{current_comments_amount}</code> <i>{old_comments_amount}</i>\n" \
           f"❓ Вопросы: <code>{current_questions_amount}</code> <i>{old_questions_amount}</i>"

    await call.message.answer(text)




