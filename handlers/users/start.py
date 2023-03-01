from aiogram import types
from aiogram.dispatcher import FSMContext
import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from loader import dp, connection, cursor, bot
from states import Registration
from handlers.menu.functions_loader import check_username, get_user_theme_picture


emoji = "🍏🍎🍐🍊🍋🍌🍉🍇🍓🫐🍈🍒🍑🥭🍍🥥🥝🍅🍆🥑🥦🥬🥒🌶🫑🌽🥕🫒🧄🧅🥔🍠🥐🥯🍞🥖🥨🧀🥚🍳🧈🥞" \
                                 "🧇🥓🥩🍗🍖🌭🍔🍟🍕🫓🥪🥙🧆🌮🌯🫔🥗🥘🫕🥫🍝🍜🍲🍛🍣🍱🥟🦪🍤🍚🍘🍥🥠🥮🍢🍡🍧🍨🍦🥧🧁" \
                                 "🍰🎂🍮🍭🍬🍫🍿🍩🍪🌰🥜🍯🥛☕️🍵🧃🥤🧋🍺🍷🍹🧉"


@dp.message_handler(text="/start")
async def command_start(message: types.Message):
    ids = cursor.execute("SELECT id FROM profiles").fetchall()

    permission = True

    for i in ids:
        if i[0] == message.from_user.id:
            await message.answer("Вы уже зарегистрированы!")
            permission = False

    if permission:
        await message.answer("Приветствуем в нашем кулинарном боте! Для начала Вам нужно зарегистрироваться. Введите "
                             "никнейм, который хотите использовать*:\n\n"
                             "<i>*никнейм будет использоваться для подписи рецептов, а также в отображении списка "
                             "лидеров викторин</i>")

        await Registration.username.set()


@dp.message_handler(state=Registration.username)
async def get_username(message: types.Message, state: FSMContext):
    answer = message.text

    usernames: str = cursor.execute("SELECT name FROM profiles").fetchall()

    permission = True
    for n in usernames:
        if n[0] == answer:
            await message.answer("Пользователь с таким юзернеймом уже существует! Придумайте другой:")
            permission = False

    if permission:
        permission = check_username(answer)
        if isinstance(permission, str):
            await message.answer(permission)
        else:
            ikb_menu = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
                [
                    InlineKeyboardButton(text='Мужской', callback_data='пол_м'),
                    InlineKeyboardButton(text='Женский', callback_data='пол_ж')
                ]
            ])

            await state.update_data(username=answer)
            await Registration.gender.set()
            await message.answer("Укажите ваш пол:", reply_markup=ikb_menu)


@dp.callback_query_handler(text_contains='пол', state=Registration.gender)
async def get_gender(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(str(call.id))

    gender = call.data.split('_')[1]

    global emoji
    new_emoji = ''.join([f"<code>{e}</code>" for e in emoji])

    await state.update_data(gender=gender)
    await Registration.emoji.set()
    await call.message.answer("Выберите эмодзи для профиля (одно), скопируйте его и пришлите в чат:\n\n"
                              f"{new_emoji}")


@dp.message_handler(state=Registration.emoji)
async def get_emoji(message: types.Message, state: FSMContext):
    answer = message.text
    user_id = message.from_user.id

    global emoji
    if len(answer) != 1 or answer not in emoji:
        await message.answer('Выберите эмодзи из предложенных!')
    else:
        author_id = message.from_user.id
        create_date = str(datetime.date.today())
        data = await state.get_data()
        username = data.get('username')
        gender = data.get('gender')

        cursor.execute("INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (author_id, username, gender, answer, '', '', '', '', '', create_date, 0, 0, '', '1 0', '', ''))

        connection.commit()
        await message.answer("Поздравляем, вы успешно зарегистрировались!")
        await state.finish()

        image = get_user_theme_picture(user_id, 'main_menu')

        ikb_menu = InlineKeyboardMarkup(row_width=1,
                                        inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text='📚 Рецепты', callback_data=f'Оецепты'),
                                                InlineKeyboardButton(text='👤 Мой профиль', callback_data='профиль'),

                                            ],
                                            [
                                                # InlineKeyboardButton(text='❤️ Здоровье', callback_data='здоровье'),
                                                InlineKeyboardButton(text='❇️ Прочее', callback_data='прочее'),
                                                InlineKeyboardButton(text='⚙️ Настройки', callback_data='настройки'),
                                            ],
                                            # [
                                            #     InlineKeyboardButton(text='⚙️ Настройки', callback_data='настройки'),
                                            # ]
                                        ],
                                        )
        chat_id = message.chat.id
        await bot.send_photo(chat_id, photo=image, reply_markup=ikb_menu)
