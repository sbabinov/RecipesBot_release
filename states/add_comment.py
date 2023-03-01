from aiogram.dispatcher.filters.state import StatesGroup, State


class AddComment(StatesGroup):
    enter_comment_text = State()

    article_id = State()