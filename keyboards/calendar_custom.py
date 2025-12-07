import calendar
import datetime
from telebot import types
from loguru import logger


def build_month_markup(
    year: int, month: int, role: str = "checkin", min_date: datetime.date = None
):
    """
    Рабочий календарь с листанием месяцев:
    ← prev | Month Year | next →
    """
    logger.info("внутри функции", month)
    kb = types.InlineKeyboardMarkup(row_width=7)

    current = datetime.date(year, month, 1)

    if month == 1:
        prev_month = datetime.date(year - 1, 12, 1)
        logger.info("if prev", prev_month)
    else:
        prev_month = datetime.date(year, month - 1, 1)
        logger.info("else prev", prev_month)

    if month == 12:
        next_month = datetime.date(year + 1, 1, 1)
        logger.info("if next", next_month)
    else:
        next_month = datetime.date(year, month + 1, 1)
        logger.info("else next", next_month)

    month_name = current.strftime("%B %Y")
    kb.row(
        types.InlineKeyboardButton(
            "«", callback_data=f"cal_prev:{role}:{prev_month.year}:{prev_month.month}"
        ),
        types.InlineKeyboardButton(month_name, callback_data="cal_noop"),
        types.InlineKeyboardButton(
            "»", callback_data=f"cal_next:{role}:{next_month.year}:{next_month.month}"
        ),
    )

    week_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    kb.row(
        *[types.InlineKeyboardButton(d, callback_data="cal_noop") for d in week_days]
    )

    cal = calendar.Calendar(firstweekday=0)
    today = datetime.date.today()

    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="cal_noop"))
                continue

            d = datetime.date(year, month, day)

            if min_date and d < min_date:
                row.append(types.InlineKeyboardButton("·", callback_data="cal_noop"))
                continue

            if d < today and role == "checkin":
                row.append(types.InlineKeyboardButton("·", callback_data="cal_noop"))
                continue

            row.append(
                types.InlineKeyboardButton(
                    str(day), callback_data=f"cal_select:{role}:{d.isoformat()}"
                )
            )

        kb.row(*row)

    kb.row(types.InlineKeyboardButton("Отмена", callback_data="cal_cancel"))
    return kb
