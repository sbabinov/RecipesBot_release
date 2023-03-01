import time
import random

from aiogram.types import CallbackQuery

from loader import dp, connection, cursor, bot, p2p

from ..menu.search_author import get_profile
from ..users.experience import give_experience
from .achievements import give_achievements
from data.config import admins

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


vip_price = 150


def check_vip(user_id: int) -> int:
    if user_id == admins[0]:
        return 200000000

    user_vip_time = cursor.execute("SELECT VIP FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    now_time = int(time.time())

    if now_time >= user_vip_time:
        return 0
    return user_vip_time - now_time


@dp.callback_query_handler(text='настройки вип')
async def vip_settings(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❓ Что дает VIP?', callback_data='что дает вип'),
                                            InlineKeyboardButton(text='🤴🏻 Мой VIP', callback_data='вип')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data='назад из настроек випа')
                                        ]
                                    ])
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text='что дает вип')
async def vip_info(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    global vip_price
    text = f"<b>ℹ️ Информация о VIP-подписке</b>\n\n" \
           f"Благодаря подписке вам станут доступны такие функции, как:\n\n" \
           f"<i>- 🎨 изменение цветового оформления бота\n" \
           f"- 📒 доступ к статьям и возможность написать свои\n" \
           f"(пользовательские рецепты и статьи в поиске всегда показываются перед стандартными)\n" \
           f"- 📘 возможность читать справочник\n" \
           f"- 🧩 участие в викторинах\n" \
           f"- 🏋🏻 доступ к программам упражнений</i>\n\n" \
           f"Также в вашем профиле отобразится статус <b><i>👑 VIP-пользователь</i></b>.\n\n" \
           f"Актуальная стоимость подписки - {vip_price} рублей за 30 дней.\n" \
           f"По дополнительным вопросам обращайтесь в /help"

    ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data='назад из вип')
        ]
    ])

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=ikb_menu)


@dp.callback_query_handler(text='вип')
async def vip(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    ikb_menu = InlineKeyboardMarkup(row_width=1)

    end_time = check_vip(user_id)
    if end_time:
        end_time = int(end_time / 24 / 60 / 60)
        vip_status = '✅ Активен'
        if end_time < 1:
            end_vip_time = 'меньше дня'
        elif 21 > end_time > 10:
            end_vip_time = f'{end_time} дней'
        elif str(end_time).endswith('2') or str(end_time).endswith('3') or str(end_time).endswith('4'):
            end_vip_time = f'{end_time} дня'
        elif str(end_time).endswith('1'):
            end_vip_time = f'{end_time} день'
        else:
            end_vip_time = f'{end_time} дней'

        text = f'Оставшееся время подписки: <i>{end_vip_time}</i>\n' \
               f'------------------------------------\n'
    else:
        ikb_menu.add(InlineKeyboardButton(text='🤴🏻 Купить VIP', callback_data='купить вип'))
        vip_status = '❌ Неактивен'

        text = ''

    user_vips_amount = cursor.execute("SELECT get_VIP_date FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    if not user_vips_amount:
        user_vips_amount = 0
    else:
        user_vips_amount = int(user_vips_amount)

    text += f"Всего купленных VIP: <i>{user_vips_amount}</i>"

    message_text = f"<b>👑 Настройки VIP</b>\n\n" \
                   f"VIP статус: <i>{vip_status}</i>\n" \
                   f"------------------------------------\n" \
                   f"{text}"

    ikb_menu.add(InlineKeyboardButton(text='↩️ Назад', callback_data='назад из вип'))

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text, reply_markup=ikb_menu)


@dp.callback_query_handler(text='купить вип')
async def buy_vip(call: CallbackQuery):

    user_id = call.from_user.id

    global vip_price

    if check_vip(user_id):
        await bot.answer_callback_query(str(call.id), text='Вы уже VIP пользователь!', show_alert=True)
    else:
        await bot.answer_callback_query(str(call.id))

        if_bill_exists = cursor.execute("SELECT bill_id FROM bills WHERE user_id = ?", (user_id,)).fetchone()
        if if_bill_exists:
            cursor.execute("DELETE FROM bills WHERE user_id = ?", (user_id,))
            connection.commit()

        comment = f"{user_id}_{random.randint(1000, 9999)}"
        bill = p2p.bill(amount=vip_price, lifetime=15, comment=comment)

        bill_id = bill.bill_id
        pay_url = bill.pay_url

        cursor.execute("INSERT INTO bills VALUES (?, ?, ?)", (user_id, bill_id, pay_url))
        connection.commit()

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='↗️ Оплатить',
                                                                     url=pay_url),
                                                InlineKeyboardButton(text='❇️ Проверить оплату',
                                                                     callback_data=f'проверить оплату')
                                            ]
                                        ])

        await call.message.answer(f"💵 Актуальная стоимость VIP на 30 дней - {vip_price} рублей. "
                                  f"Больше информации о VIP статусе можно узнать "
                                  f"в <i>Мой профиль -> VIP -> Что дает VIP?</i>", reply_markup=ikb_menu)


@dp.callback_query_handler(text='проверить оплату')
async def check_pay(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    if_bill_exists = cursor.execute("SELECT * FROM bills WHERE user_id = ?", (user_id,)).fetchmany(1)
    if if_bill_exists:
        bill_id = cursor.execute("SELECT bill_id FROM bills WHERE user_id = ?", (user_id,)).fetchone()[0]

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='❇️ Проверить оплату',
                                                                     callback_data=f'проверить оплату')
                                            ]
                                        ])

        if str(p2p.check(bill_id=bill_id).status) == 'PAID':

            now_time = int(time.time())
            end_vip_time = now_time + 30 * 24 * 60 * 60

            cursor.execute("UPDATE profiles SET VIP = ? WHERE id = ?", (end_vip_time, user_id))
            cursor.execute("DELETE FROM bills WHERE user_id = ?", (user_id,))

            user_vips_amount = \
                cursor.execute("SELECT get_VIP_date FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
            if not user_vips_amount:
                user_vips_amount = 0
            else:
                user_vips_amount = int(user_vips_amount)

            cursor.execute("UPDATE profiles SET get_VIP_date = ? WHERE id = ?", (str(user_vips_amount + 1), user_id))
            connection.commit()

            give_experience(user_id, 12)
            await give_achievements(user_id, '👑')

            if user_vips_amount >= 4:
                await give_achievements(user_id, '🤴🏻')

            await call.message.answer("✅ Поздравляем! Вы успешно приобрели <b>👑 VIP подписку</b> на 30 дней. "
                                      "Со всеми бонусами можно ознакомиться в "
                                      "<i>Мой профиль -> VIP -> Что дает VIP?</i>\n"
                                      "/menu")

        else:
            await call.message.answer("❌ Похоже, вы не оплатили счет. Если это не так, подождите несколько минут и "
                                      "проверьте еще раз. Если проблема осталась, пожалуйста, обратитесь в поддержку: "
                                      "<i>/help -> проблема</i>", reply_markup=ikb_menu)
    else:
        await call.message.answer("Счет не найден")


@dp.callback_query_handler(text='назад из настроек випа')
async def back_from_vip_settings(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    subscriptions = cursor.execute("SELECT subscriptions FROM profiles WHERE id = ?", (user_id,)).fetchone()[0]
    if not subscriptions:
        amount_subs = 0
    else:
        amount_subs = len(subscriptions.split())

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='🍪 Мои рецепты', callback_data='мои рецепты'),
                                            # InlineKeyboardButton(text='🖌 Изменить', callback_data='изменить профиль')
                                            InlineKeyboardButton(text='🏆 Достижения', callback_data='достижения')
                                        ],
                                        [
                                            InlineKeyboardButton(text=f'🖇 Подписки ({amount_subs})',
                                                                 callback_data='мои подписки'),
                                            InlineKeyboardButton(text='👑 VIP', callback_data='настройки вип')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад', callback_data='назад_')
                                        ]
                                    ])
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=ikb_menu)


@dp.callback_query_handler(text='назад из вип')
async def back_from_vip(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    user_id = call.from_user.id

    user_profile = get_profile(user_id)

    ikb_menu = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(text='❓ Что дает VIP?', callback_data='что дает вип'),
                                            InlineKeyboardButton(text='🤴🏻 Мой VIP', callback_data='вип')
                                        ],
                                        [
                                            InlineKeyboardButton(text='↩️ Назад',
                                                                 callback_data='назад из настроек випа')
                                        ]
                                    ])
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=user_profile, reply_markup=ikb_menu)






