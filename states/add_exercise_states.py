from aiogram.dispatcher.filters.state import StatesGroup, State


class AddExercise(StatesGroup):
    exercise_id = State()
    title = State()
    photo = State()
    text = State()

    confirm = State()
