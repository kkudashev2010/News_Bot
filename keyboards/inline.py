from telebot import types

#
#
# def make_city_kb(cities):
#     kb = types.InlineKeyboardMarkup()
#     for c in cities:
#         kb.add(types.InlineKeyboardButton(c, callback_data=f'confirm_city:{c}'))
#     return kb
#


def optional_params_kb():
    """
    Клавиатура уточняющих параметров (что ещё хочет указать пользователь)
    """
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Количество взрослых", callback_data="param:adults"),
        types.InlineKeyboardButton("Возраст детей", callback_data="param:children_age"),
        types.InlineKeyboardButton("Количество комнат", callback_data="param:room_qty"),
        types.InlineKeyboardButton("Диапазон цен", callback_data="param:price"),
        types.InlineKeyboardButton("Показать отели", callback_data="param:show"),
    )
    return kb
