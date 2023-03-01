from aiogram.dispatcher.filters.state import StatesGroup, State


class Registration(StatesGroup):
    username = State()
    gender = State()
    emoji = State()
