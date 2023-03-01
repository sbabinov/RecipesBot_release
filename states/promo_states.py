from aiogram.dispatcher.filters.state import StatesGroup, State


class Promo(StatesGroup):
    enter_promo = State()