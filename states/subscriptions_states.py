from aiogram.dispatcher.filters.state import StatesGroup, State


class Subscription(StatesGroup):
    enter_author_username = State()
