from aiogram.dispatcher.filters.state import StatesGroup, State


class Timer(StatesGroup):
    enter_amount_of_minutes = State()
    enter_note = State()
