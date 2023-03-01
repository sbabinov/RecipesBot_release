from aiogram.dispatcher.filters.state import StatesGroup, State


class AddRecipe(StatesGroup):
    title = State()
    type = State()
    rec_id = State()
    img = State()
    ingredients = State()
    tags = State()
    description = State()
    author_id = State()

    confirm = State()
    change = State()
