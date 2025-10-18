from telebot import types

def make_city_kb(cities):
    kb = types.InlineKeyboardMarkup()
    for c in cities:
        kb.add(types.InlineKeyboardButton(c, callback_data=f'confirm_city:{c}'))
    return kb
