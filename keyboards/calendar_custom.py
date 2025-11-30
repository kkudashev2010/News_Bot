# # keyboards/calendar_custom.py
# import calendar
# import datetime
# from telebot import types
#
# # Возвращает InlineKeyboardMarkup календаря для указанного года/месяца.
# # role: 'checkin' или 'checkout' - чтобы понимать, какой выбор обрабатываем
# # min_date: datetime.date - минимальная доступная дата (включительно)
# def build_month_markup(year: int, month: int, role: str = "checkin", min_date: datetime.date = None):
#     kb = types.InlineKeyboardMarkup(row_width=7)
#     # Заголовок: месяц и навигация
#     month_name = datetime.date(year, month, 1).strftime("%B %Y")
#     prev_month = (datetime.date(year, month, 1) - datetime.timedelta(days=1)).replace(day=1)
#     next_month = (datetime.date(year, month, calendar.monthrange(year, month)[1]) + datetime.timedelta(days=1)).replace(day=1)
#     print('->', next_month)
#     nav_row = [
#         types.InlineKeyboardButton("«", callback_data=f"cal:{role}:{prev_month.year}:{prev_month.month}"),
#         types.InlineKeyboardButton(month_name, callback_data="cal:noop"),
#         types.InlineKeyboardButton("»", callback_data=f"cal_next:{role}:{next_month.year}:{next_month.month}"),
#     ]
#     kb.add(*nav_row)
#
#     # Дни недели
#     # week_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
#     # for wd in week_days:
#     #     kb.add(types.InlineKeyboardButton(wd, callback_data="cal:noop"))
#
#     # Вывод дней месяца в сетке
#     cal = calendar.Calendar(firstweekday=0)  # Monday
#     for week in cal.monthdayscalendar(year, month):
#         print('week')
#         buttons = []
#         for day in week:
#             if day == 0:
#                 # пустая клетка
#                 buttons.append(types.InlineKeyboardButton(" ", callback_data="cal:noop"))
#             else:
#                 d = datetime.date(year, month, day)
#                 # проверка min_date (если установлена), недоступные даты делаем "неактивными"
#                 if min_date and d < min_date:
#                     print('min_date and d < min_date сработало')
#                     # неактивная дата — показываем как зачёркнутую (или просто как текст) и callback noop
#                     buttons.append(types.InlineKeyboardButton(str(day), callback_data="cal:noop"))
#                 else:
#                     print('min_date and d < min_date несработало')
#                     # допустимая дата — callback cal_select:role:YYYY-MM-DD
#                     buttons.append(types.InlineKeyboardButton(str(day), callback_data=f"cal_select:{role}:{d.isoformat()}"))
#         # добавляем весь ряд
#         kb.add(*buttons)
#     # Кнопка "Отмена"
#     kb.add(types.InlineKeyboardButton("Отмена", callback_data="cal:cancel"))
#     return kb


import calendar
import datetime
from telebot import types


def build_month_markup(year: int, month: int, role: str = "checkin", min_date: datetime.date = None):
    """
    Рабочий календарь с листанием месяцев:
    ← prev | Month Year | next →
    """
    print('внутри функции',month)
    kb = types.InlineKeyboardMarkup(row_width=7)

    # Находим прошлый и следующий месяцы
    current = datetime.date(year, month, 1)
    # предыдущий месяц
    if month == 1:
        prev_month = datetime.date(year - 1, 12, 1)
        print('if prev', prev_month)
    else:
        prev_month = datetime.date(year, month - 1, 1)
        print('else prev',prev_month)

    # следующий месяц
    if month == 12:
        next_month = datetime.date(year + 1, 1, 1)
        print('if next',next_month)
    else:
        next_month = datetime.date(year, month + 1, 1)
        print('else next',next_month)

    # Заголовок
    month_name = current.strftime("%B %Y")
    kb.row(
        types.InlineKeyboardButton("«", callback_data=f"cal_prev:{role}:{prev_month.year}:{prev_month.month}"),
        types.InlineKeyboardButton(month_name, callback_data="cal_noop"),
        types.InlineKeyboardButton("»", callback_data=f"cal_next:{role}:{next_month.year}:{next_month.month}")
    )

    # Дни недели
    week_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    kb.row(*[types.InlineKeyboardButton(d, callback_data="cal_noop") for d in week_days])

    # Календарная сетка
    cal = calendar.Calendar(firstweekday=0)
    today = datetime.date.today()

    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="cal_noop"))
                continue

            d = datetime.date(year, month, day)

            # Проверка минимальной даты (выезд > заезда)
            if min_date and d < min_date:
                row.append(types.InlineKeyboardButton("·", callback_data="cal_noop"))
                continue

            # Прошлые даты нельзя нажимать
            if d < today and role == "checkin":
                row.append(types.InlineKeyboardButton("·", callback_data="cal_noop"))
                continue

            row.append(
                types.InlineKeyboardButton(
                    str(day),
                    callback_data=f"cal_select:{role}:{d.isoformat()}"
                )
            )

        kb.row(*row)

    kb.row(types.InlineKeyboardButton("Отмена", callback_data="cal_cancel"))
    return kb
