import os.path

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, CallbackQuery
from aiogram import types

from loader import dp, connection, cursor, bot
from data import admins
from states import AddExercise


@dp.callback_query_handler(text='добавить упражнение админ')
async def add_guide(call: CallbackQuery):
    await bot.answer_callback_query(str(call.id))

    if call.from_user.id in admins:
        await call.message.answer('Введите название упражнения:')
        await AddExercise.title.set()


@dp.message_handler(state=AddExercise.title)
async def enter_title(message: types.Message, state: FSMContext):
    answer = message.text

    await state.update_data(title=answer)
    await AddExercise.photo.set()
    await message.answer("Отправьте видео для упражнения:")


@dp.message_handler(state=AddExercise.photo, content_types=ContentType.VIDEO)
async def enter_photo(message: types.Message, state: FSMContext):
    print('ok')
    file_id = message.video.file_id
    file = await bot.get_file(file_id=file_id)
    last_id = cursor.execute("SELECT id FROM exercises").fetchall()
    if not last_id:
        guide_id = 1
    else:
        guide_id = last_id[-1][0] + 1

    await state.update_data(guide_id=guide_id)
    await file.download(destination_file=os.path.join('videos/exercises/' + str(guide_id) + '.mp4'), timeout=None)
    await AddExercise.text.set()
    await message.answer("Введите описание упражнения:")


@dp.message_handler(state=AddExercise.text)
async def enter_text(message: types.Message, state: FSMContext):
    answer = message.text

    await state.update_data(text=answer)

    await AddExercise.confirm.set()
    await message.answer(answer)
    await message.answer("Оставляем?")


@dp.message_handler(state=AddExercise.confirm)
async def confirm(message: types.Message, state: FSMContext):
    answer = message.text

    data = await state.get_data()
    guide_id = data.get('guide_id')

    if answer == 'да':
        title = data.get('title')
        text = data.get('text')

        cursor.execute("INSERT INTO exercises VALUES (?, ?, ?)", (guide_id, title.lower(), text))
        connection.commit()

        await state.finish()
        await message.answer("Успешно добавлено!")

    if answer == 'нет':
        try:
            os.remove(os.path.join(f'videos/exercises/{guide_id}.mp4'))
        except Exception as e:
            print(e)

        await state.finish()
        await message.answer('Отменено')
