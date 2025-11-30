from . import inline
from telebot import types


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
        types.InlineKeyboardButton("Показать отели", callback_data="param:show")
    )
    return kb