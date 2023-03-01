from aiogram.dispatcher.filters.state import StatesGroup, State


class Search(StatesGroup):
    enter_title = State()
    enter_tags = State()
    enter_ingredients = State()
    enter_author = State()
    enter_author_username = State()
    author_profile = State()

    guide_ingredient = State()
    message_to_delete = State()
    message_to_edit = State()
