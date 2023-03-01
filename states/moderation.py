from aiogram.dispatcher.filters.state import StatesGroup, State


class Moderation(StatesGroup):
    art_id = State()
    write_to_author = State()

    rec_id = State()
    message_text = State()

    confirm = State()
    confirm_recipe = State()
