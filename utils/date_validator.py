# utils/date_validator.py
from datetime import date, datetime

def parse_iso_date(s: str):
    """Парсит YYYY-MM-DD -> datetime.date. Возвращает None при ошибке."""
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        try:
            # на всякий случай поддержим date() строки
            return date.fromisoformat(s)
        except Exception:
            return None

def check_range(checkin: date, checkout: date):
    """Проверяет, что обе даты не None, и что checkout > checkin.
    Возвращает (ok: bool, message: str)."""
    if not checkin or not checkout:
        return False, "Обе даты должны быть указаны."
    if checkout <= checkin:
        return False, "Дата выезда должна быть позже даты заезда."
    return True, ""