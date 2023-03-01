from aiogram.dispatcher.filters.state import StatesGroup, State


class AddGuide(StatesGroup):
    guide_id = State()
    title = State()
    photo = State()
    text = State()

    confirm = State()
