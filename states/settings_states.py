from aiogram.dispatcher.filters.state import StatesGroup, State


class Settings(StatesGroup):
    enter_username = State()
    message_id = State()
