from aiogram.dispatcher.filters.state import StatesGroup, State


class AddNews(StatesGroup):
    news_id = State()
    title = State()
    photo = State()
    text = State()

    confirm = State()
