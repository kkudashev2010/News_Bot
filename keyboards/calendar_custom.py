# keyboards/calendar_custom.py
import calendar
import datetime
from telebot import types

# Возвращает InlineKeyboardMarkup календаря для указанного года/месяца.
# role: 'checkin' или 'checkout' - чтобы понимать, какой выбор обрабатываем
# min_date: datetime.date - минимальная доступная дата (включительно)
def build_month_markup(year: int, month: int, role: str = "checkin", min_date: datetime.date = None):
    kb = types.InlineKeyboardMarkup(row_width=7)
    # Заголовок: месяц и навигация
    month_name = datetime.date(year, month, 1).strftime("%B %Y")
    prev_month = (datetime.date(year, month, 1) - datetime.timedelta(days=1)).replace(day=1)
    next_month = (datetime.date(year, month, calendar.monthrange(year, month)[1]) + datetime.timedelta(days=1)).replace(day=1)
    nav_row = [
        types.InlineKeyboardButton("«", callback_data=f"cal:{role}:{prev_month.year}:{prev_month.month}"),
        types.InlineKeyboardButton(month_name, callback_data="cal:noop"),
        types.InlineKeyboardButton("»", callback_data=f"cal:{role}:{next_month.year}:{next_month.month}"),
    ]
    kb.add(*nav_row)

    # Дни недели
    # week_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    # for wd in week_days:
    #     kb.add(types.InlineKeyboardButton(wd, callback_data="cal:noop"))

    # Вывод дней месяца в сетке
    cal = calendar.Calendar(firstweekday=0)  # Monday
    for week in cal.monthdayscalendar(year, month):
        buttons = []
        for day in week:
            if day == 0:
                # пустая клетка
                buttons.append(types.InlineKeyboardButton(" ", callback_data="cal:noop"))
            else:
                d = datetime.date(year, month, day)
                # проверка min_date (если установлена), недоступные даты делаем "неактивными"
                if min_date and d < min_date:
                    # неактивная дата — показываем как зачёркнутую (или просто как текст) и callback noop
                    buttons.append(types.InlineKeyboardButton(str(day), callback_data="cal:noop"))
                else:
                    # допустимая дата — callback cal_select:role:YYYY-MM-DD
                    buttons.append(types.InlineKeyboardButton(str(day), callback_data=f"cal_select:{role}:{d.isoformat()}"))
        # добавляем весь ряд
        kb.add(*buttons)
    # Кнопка "Отмена"
    kb.add(types.InlineKeyboardButton("Отмена", callback_data="cal:cancel"))
    return kb
