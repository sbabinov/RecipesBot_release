import time

from aiogram import types
from aiogram.dispatcher import FSMContext
import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from loader import dp, connection, cursor, bot
from states import Promo
from ..menu.functions_loader import check_vip


promos = ['START']


@dp.message_handler(text_contains="/promo")
async def command_promo(message: types.Message):
    await Promo.enter_promo.set()
    await message.answer("Введите ваш промокод:")


@dp.message_handler(state=Promo.enter_promo)
async def enter_promo(message: types.Message, state: FSMContext):
    answer = message.text
    user_id = message.from_user.id

    global promos
    if answer not in promos:
        await state.finish()
        await message.answer("Такого промокода не существует!")
    else:
        user_promo = cursor.execute("SELECT user_promo FROM promo WHERE user_id = ?", (user_id,)).fetchone()
        if not user_promo:
            cursor.execute("INSERT INTO promo VALUES (?, ?)", (user_id, ''))
            connection.commit()

            user_promo = []
        else:
            user_promo = user_promo[0].split()

        if answer in user_promo:
            await state.finish()
            await message.answer("Вы уже активировали этот промокод!")
        else:
            user_promo.append(answer)
            user_promo = ' '.join(user_promo)

            if answer == 'START':
                if check_vip(user_id):
                    await state.finish()
                    await message.answer("У вас уже есть VIP! Активируйте промокод после истечения подписки")
                else:
                    now_time = int(time.time())
                    end_vip_time = now_time + 30 * 24 * 60 * 60

                    cursor.execute("UPDATE profiles SET VIP = ? WHERE id = ?", (end_vip_time, user_id))
                    connection.commit()

                    await state.finish()
                    await message.answer("✅ Поздравляем! Теперь у вас есть <b>👑 VIP подписка</b> на 30 дней. "
                                         "Со всеми бонусами можно ознакомиться в "
                                         "<i>Мой профиль -> VIP -> Что дает VIP?</i>\n"
                                         "/menu")

            cursor.execute("UPDATE promo SET user_promo = ? WHERE user_id = ?", (user_promo, user_id))
            connection.commit()
