from telebot import types


def make_city_kb(cities):
    kb = types.InlineKeyboardMarkup()
    for c in cities:
        kb.add(types.InlineKeyboardButton(c, callback_data=f'confirm_city:{c}'))
    return kb


def optional_params_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Количество взрослых", callback_data="param:adults"))
    kb.add(types.InlineKeyboardButton("Количество детей", callback_data="param:children_age"))
    kb.add(types.InlineKeyboardButton("Количество комнат", callback_data="param:room_qty"))
    kb.add(types.InlineKeyboardButton("Диапазон цен", callback_data="param:price"))
    kb.add(types.InlineKeyboardButton("Показать отели", callback_data="param:show"))
    return kb