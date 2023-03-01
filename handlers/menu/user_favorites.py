from aiogram.types import CallbackQuery

from loader import dp, cursor, bot
from handlers.menu.menu import get_recipe


@dp.callback_query_handler(text='все fav')
async def all_user_favorites(call: CallbackQuery):
    user_id = call.from_user.id
    user_favorites = cursor.execute("SELECT favorites FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]

    if not user_favorites:
        await bot.answer_callback_query(str(call.id), text="У вас пока нет рецептов в избранном!", show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))
        ids = user_favorites.split()
        now_id = ids[0]

        await get_recipe(call, ids, now_id, call=True)


