# from aiogram import types
# from aiogram.dispatcher import FSMContext
# from aiogram.types import ContentType, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
#
# from handlers.menu.settings import filter_recipes
# from .vip import check_vip
from loader import dp, connection, cursor, bot
# from states import Search
# from handlers.menu.menu import get_recipe
#
#
# @dp.callback_query_handler(text='по ингредиентам')
# async def search_by_ingredients(call: CallbackQuery):
#     user_id = call.from_user.id
#
#     if not check_vip(user_id):
#         await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
#                                         show_alert=True)
#     else:
#         await bot.answer_callback_query(str(call.id))
#
#         ikb_menu = InlineKeyboardMarkup(row_width=1,
#                                         inline_keyboard=[
#                                             [
#                                                 InlineKeyboardButton(text='❌ Выход',
#                                                                      callback_data='Выход из поиска по тегам')
#                                             ]
#                                         ],
#                                         )
#         await call.message.delete()
#         await call.message.answer("🥕 Введите название ингредиента (или часть названия):", reply_markup=ikb_menu)
#         await Search.enter_ingredients.set()
#
#
# @dp.message_handler(state=Search.enter_ingredients)
# async def start_search_by_ingredients(message: types.Message, state: FSMContext):
#     answer = message.text
#     user_id = message.from_user.id
#
#     data = await state.get_data()
#     t = data.get('enter_tags')
#
#     ikb_menu = InlineKeyboardMarkup(row_width=1,
#                                     inline_keyboard=[
#                                         [
#                                             InlineKeyboardButton(text='❌ Выход',
#                                                                  callback_data='Выход из поиска по тегам')
#                                         ]
#                                     ],
#                                     )
#
#     if not t:
#         await state.update_data(enter_tags=[answer])
#     else:
#         await state.update_data(enter_tags=t + [answer])
#
#     data = await state.get_data()
#     t = data.get('enter_tags')
#
#     if t and len(t) == 5:
#         await state.finish()
#         recipes = []
#         recipes_by_ings = cursor.execute("SELECT ingredients FROM recipes").fetchall()
#         for rec in recipes_by_ings:
#             add = True
#             for i in t:
#                 if i.lower().replace('ё', 'е') not in rec[0].lower().replace('ё', 'е'):
#                     add = False
#             if add:
#                 r = cursor.execute("SELECT id FROM recipes WHERE ingredients = ?", (rec[0],)).fetchone()[0]
#                 recipes.append(r)
#
#         await state.finish()
#         if not recipes:
#             ikb_menu = InlineKeyboardMarkup(row_width=1,
#                                             inline_keyboard=[
#                                                 [
#                                                     InlineKeyboardButton(text='↩️ Назад',
#                                                                          callback_data='НазаД из поиска по ингредиентам'),
#                                                     InlineKeyboardButton(text='❌ Выход',
#                                                                          callback_data='Выход из поиска по тегам')
#                                                 ],
#
#                                             ],
#                                             )
#             await message.answer("⛔️ Нет рецептов с такими ингредиентами", reply_markup=ikb_menu)
#         else:
#             filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()
#
#             recipes = filter_recipes(recipes, filters[0], filter_type=int(filters[1]))
#             await get_recipe(message, recipes, recipes[0])
#     else:
#         ikb_menu = InlineKeyboardMarkup(row_width=1,
#                                         inline_keyboard=[
#                                             [
#                                                 InlineKeyboardButton(text='✅ Применить',
#                                                                      callback_data='Применить ингредиенты'),
#                                                 InlineKeyboardButton(text='❌ Выход',
#                                                                      callback_data='Выход из поиска по тегам')
#                                             ],
#
#                                         ],
#                                         )
#
#         await message.answer(f"Ингредиент добавлен. Если хотите добавить больше ингредиентов, "
#                              f"вводите их дальше (максимум ингредиентов - 5)\n\n"
#                              f"Текущие ингредиенты: <i>{', '.join(t)}</i>",
#                              reply_markup=ikb_menu)
#
#
# # @dp.callback_query_handler(text='Применить ингредиенты', state=Search.enter_ingredients)
# # async def apply_ingredients(call: CallbackQuery, state: FSMContext):
# #     await bot.answer_callback_query(str(call.id))
# #
# #     user_id = call.from_user.id
# #
# #     if not check_vip(user_id):
# #         await state.finish()
# #         await bot.answer_callback_query(str(call.id), text='Этот раздел доступен только VIP-пользователям!',
# #                                         show_alert=True)
# #     else:
# #         data = await state.get_data()
# #         t = data.get('enter_tags')
# #         recipes = []
# #         recipes_by_tags = cursor.execute("SELECT ingredients FROM recipes").fetchall()
# #         for rec in recipes_by_tags:
# #             add = True
# #             for tag in t:
# #                 if tag.lower().replace('ё', 'е') not in rec[0].lower().replace('ё', 'е'):
# #                     add = False
# #             if add:
# #                 r = cursor.execute("SELECT id FROM recipes WHERE ingredients = ?", (rec[0],)).fetchone()[0]
# #                 recipes.append(r)
# #
# #         await state.finish()
# #         if not recipes:
# #             ikb_menu = InlineKeyboardMarkup(row_width=1,
# #                                             inline_keyboard=[
# #                                                 [
# #                                                     InlineKeyboardButton(text='↩️ Назад',
# #                                                                          callback_data='НазаД из поиска по ингредиентам'),
# #                                                     InlineKeyboardButton(text='❌ Выход',
# #                                                                          callback_data='Выход из поиска по тегам')
# #                                                 ],
# #
# #                                             ],
# #                                             )
# #             await call.message.answer("⛔️ Нет рецептов с такими ингредиентами", reply_markup=ikb_menu)
# #         else:
# #             filters = cursor.execute("SELECT filters FROM profiles WHERE id = ?", (user_id,)).fetchone()[0].split()
# #
# #             recipes = filter_recipes(recipes, filters[0], filter_type=int(filters[1]))
# #             await get_recipe(call, recipes, recipes[0], call=True)
#
#
# @dp.callback_query_handler(text='НазаД из поиска по ингредиентам')
# async def back_from_search_by_ingredients(call: CallbackQuery):
#     await bot.answer_callback_query(str(call.id))
#
#     ikb_menu = InlineKeyboardMarkup(row_width=1,
#                                     inline_keyboard=[
#                                         [
#                                             InlineKeyboardButton(text='❌ Выход',
#                                                                  callback_data='Выход из поиска по тегам')
#                                         ]
#                                     ],
#                                     )
#     chat_id = call.message.chat.id
#     await call.message.delete()
#     await call.message.answer("🥕 Введите название ингредиента (или часть названия):", reply_markup=ikb_menu)
#     await Search.enter_ingredients.set()
#
#
#
#
#
#
#
#
