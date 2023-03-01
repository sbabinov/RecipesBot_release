from aiogram.dispatcher.filters.state import StatesGroup, State


class AddArticle(StatesGroup):
    title = State()
    rec_id = State()
    img = State()
    description = State()
    author_id = State()

    confirm = State()
    change = State()
