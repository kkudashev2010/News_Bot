from telebot import types

def optional_params_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Количество взрослых", callback_data="param:adults"))
    kb.add(types.InlineKeyboardButton("Количество детей", callback_data="param:children_age"))
    kb.add(types.InlineKeyboardButton("Количество комнат", callback_data="param:room_qty"))
    kb.add(types.InlineKeyboardButton("Диапазон цен", callback_data="param:price"))
    kb.add(types.InlineKeyboardButton("Показать отели", callback_data="param:show"))
    return kb