from aiogram.dispatcher.filters.state import StatesGroup, State


class UserAddArticle(StatesGroup):
    title = State()
    rec_id = State()
    img = State()
    ingredients = State()
    description = State()
    author_id = State()

    confirm = State()
    change = State()
