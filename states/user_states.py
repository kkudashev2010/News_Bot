from telebot.handler_backends import State, StatesGroup

class UserState(StatesGroup):
    city = State()
    dest_id = State()
    arrival_date = State()
    departure_date = State()
    adults = State()
    children_age = State()
    room_qty = State()
    price_min = State()
    price_max = State()
    step = State()
