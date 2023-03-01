from aiogram.dispatcher.filters.state import StatesGroup, State


class AddQuestion(StatesGroup):
    text = State()
    photo = State()
    q_id = State()
    variants = State()
    right_variant = State()
    if_for_quiz = State()

    confirm = State()
