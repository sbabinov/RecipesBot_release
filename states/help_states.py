from aiogram.dispatcher.filters.state import StatesGroup, State


class Help(StatesGroup):
    question_text = State()

    report_id = State()
    report_type = State()

    confirm = State()
