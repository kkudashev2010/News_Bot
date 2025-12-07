# handlers/lowprice.py
import os
from loader import bot
from telebot import types
import keyboards.calendar_custom as calendar_custom
from utils.date_validator import parse_iso_date, check_range
from api_hotels import search_hotels
from database.models import HotelSearchHistory
import threading
import datetime
import json

RAPIDAPI_KEY = os.getenv("API_KEY")
USER_STATE = {}
STATE_LOCK = threading.Lock()
# возможные step: await_city, await_checkin, await_checkout, await_price, showing_results


def set_state(chat_id, **kwargs):
    with STATE_LOCK:
        st = USER_STATE.get(chat_id, {})
        st.update(kwargs)
        USER_STATE[chat_id] = st


def get_state(chat_id):
    with STATE_LOCK:
        return USER_STATE.get(chat_id, {}).copy()


def clear_state(chat_id):
    with STATE_LOCK:
        if chat_id in USER_STATE:
            USER_STATE.pop(chat_id, None)


# Запуск сценария
@bot.message_handler(commands=["lowprice"])
def cmd_lowprice(message):
    chat_id = message.chat.id
    clear_state(chat_id)
    set_state(chat_id, step="await_city")
    msg = bot.send_message(chat_id, "Введите город для поиска (например: Москва):")
    bot.register_next_step_handler(msg, process_city)


def process_city(message):
    chat_id = message.chat.id
    city = message.text.strip()
    if not city:
        msg = bot.send_message(
            chat_id, "Название города не распознано. Введите город (пример: Москва):"
        )
        bot.register_next_step_handler(msg, process_city)
        return
    set_state(chat_id, city=city, step="await_checkin")
    # Показываем календарь для выбора даты заезда начиная с сегодняшнего дня
    today = datetime.date.today()
    kb = calendar_custom.build_month_markup(
        today.year, today.month, role="checkin", min_date=today
    )
    bot.send_message(
        chat_id,
        f"Город: <b>{city}</b>\nВыберите дату заезда:",
        parse_mode="HTML",
        reply_markup=kb,
    )


# Обработка callback'ов календаря и цен и пагинации
@bot.callback_query_handler(
    func=lambda call: call.data
    and (
        call.data.startswith("cal:")
        or call.data.startswith("cal_select:")
        or call.data.startswith("price:")
        or call.data.startswith("page:")
        or call.data == "cal:cancel"
    )
)
def cb_calendar(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "cal:noop":
        bot.answer_callback_query(call.id)
        return

    if data == "cal:cancel":
        clear_state(chat_id)
        bot.edit_message_text("Операция отменена.", chat_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    # Навигация по месяцам: cal:role:YYYY:MM
    if data.startswith("cal:") and not data.startswith("cal_select:"):
        parts = data.split(":")
        # форматы: ['cal','role','YYYY','MM'] или 'cal:noop'
        if len(parts) >= 4:
            _, role, yyyy, mm = parts[:4]
            try:
                y = int(yyyy)
                m = int(mm)
            except Exception:
                bot.answer_callback_query(call.id, "Ошибка навигации")
                return
            # min_date для checkin = сегодня, для checkout = checkin+1 (если задан)
            st = get_state(chat_id)
            min_date = datetime.date.today() if role == "checkin" else None
            if role == "checkout":
                checkin = parse_iso_date(st.get("checkin")) if st else None
                if checkin:
                    min_date = checkin + datetime.timedelta(days=1)
                else:
                    # если нет checkin — не показываем календарь для checkout, просим сначала выбрать заезд
                    bot.answer_callback_query(call.id, "Сначала выберите дату заезда.")
                    return
            kb = calendar_custom.build_month_markup(y, m, role=role, min_date=min_date)
            try:
                bot.edit_message_reply_markup(
                    chat_id, call.message.message_id, reply_markup=kb
                )
            except Exception:
                # иногда edit_message_reply_markup может не сработать (например, если был отправлен текст без markup)
                bot.edit_message_text(
                    call.message.text or "Выберите дату:",
                    chat_id,
                    call.message.message_id,
                    reply_markup=kb,
                )
            bot.answer_callback_query(call.id)
            return

    # Выбор конкретной даты: cal_select:role:YYYY-MM-DD
    if data.startswith("cal_select:"):
        # пример: cal_select:checkin:2025-10-05
        parts = data.split(":", 2)
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "Ошибка выбора даты")
            return
        _, role, datestr = parts
        sel_date = parse_iso_date(datestr)
        if not sel_date:
            bot.answer_callback_query(call.id, "Неверный формат даты")
            return

        st = get_state(chat_id)
        if role == "checkin":
            # сохраняем заезд, переходим к выбору выезда
            set_state(chat_id, checkin=sel_date.isoformat(), step="await_checkout")
            # показываем календарь для выезда, min_date = checkin + 1 day
            min_date = sel_date + datetime.timedelta(days=1)
            kb = calendar_custom.build_month_markup(
                min_date.year, min_date.month, role="checkout", min_date=min_date
            )
            try:
                bot.edit_message_text(
                    f"Выбрана дата заезда: {sel_date.isoformat()}\nТеперь выберите дату выезда:",
                    chat_id,
                    call.message.message_id,
                    reply_markup=kb,
                )
            except Exception:
                bot.send_message(
                    chat_id,
                    f"Выбрана дата заезда: {sel_date.isoformat()}\nТеперь выберите дату выезда:",
                    reply_markup=kb,
                )
            bot.answer_callback_query(call.id)
            return

        elif role == "checkout":
            # сохраняем выезд и проверяем валидность
            checkin_str = st.get("checkin") if st else None
            if not checkin_str:
                bot.answer_callback_query(call.id, "Сначала выберите дату заезда.")
                return
            checkin = parse_iso_date(checkin_str)
            checkout = sel_date
            ok, msg = check_range(checkin, checkout)
            if not ok:
                # ошибка — не принимаем, просим выбрать корректную дату
                bot.answer_callback_query(call.id, msg)
                # повторно показываем календарь для checkout с min_date = checkin+1
                min_date = checkin + datetime.timedelta(days=1)
                kb = calendar_custom.build_month_markup(
                    min_date.year, min_date.month, role="checkout", min_date=min_date
                )
                try:
                    bot.edit_message_text(
                        f"Неверная дата выезда: {checkout.isoformat()}\n{msg}\nВыберите другую дату выезда:",
                        chat_id,
                        call.message.message_id,
                        reply_markup=kb,
                    )
                except Exception:
                    bot.send_message(
                        chat_id,
                        f"Неверная дата выезда: {checkout.isoformat()}\n{msg}\nВыберите другую дату выезда:",
                        reply_markup=kb,
                    )
                return
            # ok -> продолжаем к выбору цен
            set_state(chat_id, checkout=checkout.isoformat(), step="await_price")
            # Предлагаем диапазоны цен (можно расширить)
            kb_price = types.InlineKeyboardMarkup()
            kb_price.add(
                types.InlineKeyboardButton("0 - 50 $", callback_data="price:0:50")
            )
            kb_price.add(
                types.InlineKeyboardButton("50 - 150 $", callback_data="price:50:150")
            )
            kb_price.add(
                types.InlineKeyboardButton(
                    "150 - 9999 $", callback_data="price:150:9999"
                )
            )
            kb_price.add(
                types.InlineKeyboardButton(
                    "Ввести вручную", callback_data="price:custom"
                )
            )
            try:
                bot.edit_message_text(
                    f"Выбрана дата выезда: {checkout.isoformat()}\nТеперь выберите диапазон цен:",
                    chat_id,
                    call.message.message_id,
                    reply_markup=kb_price,
                )
            except Exception:
                bot.send_message(
                    chat_id,
                    f"Выбрана дата выезда: {checkout.isoformat()}\nТеперь выберите диапазон цен:",
                    reply_markup=kb_price,
                )
            bot.answer_callback_query(call.id)
            return

    # Цена
    if data.startswith("price:"):
        parts = data.split(":")
        if parts[1] == "custom":
            # попросим ввести текстовый диапазон min-max
            msg = bot.send_message(
                chat_id, "Введите диапазон цен в формате min-max (например: 20-100):"
            )
            bot.register_next_step_handler(msg, process_custom_price)
            bot.answer_callback_query(call.id)
            return
        try:
            pmin = int(parts[1])
            pmax = int(parts[2])
        except Exception:
            bot.answer_callback_query(call.id, "Неверный диапазон цен")
            return
        # запускаем поиск
        st = get_state(chat_id)
        city = st.get("city")
        checkin = st.get("checkin")
        checkout = st.get("checkout")
        if not city or not checkin or not checkout:
            bot.answer_callback_query(
                call.id, "Внутренняя ошибка состояния. Начните /lowprice заново."
            )
            return
        bot.edit_message_text(
            "Ищу отели... пожалуйста, подождите", chat_id, call.message.message_id
        )
        hotels = search_hotels(city, checkin, checkout, pmin, pmax, limit=5)
        if not hotels:
            bot.send_message(chat_id, "К сожалению, отели не найдены или ошибка API.")
            clear_state(chat_id)
            bot.answer_callback_query(call.id)
            return
        # сохраним результаты в состояние и покажем первую страницу
        set_state(chat_id, results=hotels, page=0, step="showing_results")
        show_result_page(chat_id)
        bot.answer_callback_query(call.id)
        return


def process_custom_price(message):
    chat_id = message.chat.id
    txt = message.text.strip()
    try:
        parts = txt.split("-")
        pmin = int(parts[0])
        pmax = int(parts[1])
    except Exception:
        msg = bot.send_message(
            chat_id, "Неверный формат. Введите в формате min-max, например: 20-100"
        )
        bot.register_next_step_handler(msg, process_custom_price)
        return
    st = get_state(chat_id)
    city = st.get("city")
    checkin = st.get("checkin")
    checkout = st.get("checkout")
    if not city or not checkin or not checkout:
        bot.send_message(
            chat_id, "Внутренняя ошибка состояния. Начните /lowprice заново."
        )
        return
    bot.send_message(chat_id, "Ищу отели... пожалуйста, подождите")
    hotels = search_hotels(city, checkin, checkout, pmin, pmax, limit=5)
    if not hotels:
        bot.send_message(chat_id, "К сожалению, отели не найдены или ошибка API.")
        clear_state(chat_id)
        return
    set_state(chat_id, results=hotels, page=0, step="showing_results")
    show_result_page(chat_id)


# Показываем страницу результатов (с простой пагинацией)
def show_result_page(chat_id):
    st = get_state(chat_id)
    hotels = st.get("results", [])
    page = st.get("page", 0)
    if page < 0 or page >= len(hotels):
        bot.send_message(chat_id, "Страница вне диапазона.")
        return
    h = hotels[page]
    name = h.get("name") or h.get("hotel_name") or "—"
    price = (
        h.get("price") or h.get("ratePlan", {}).get("price", {}).get("current") or "N/A"
    )
    link = h.get("link") or h.get("urls", {}).get("hotelInfositeUrl") or "#"
    descr = h.get("description") or h.get("address", {}).get("streetAddress", "")
    coords_lat = h.get("latitude") or (h.get("coordinate") or {}).get("lat")
    coords_lon = h.get("longitude") or (h.get("coordinate") or {}).get("lon")
    checkin = st.get("checkin")
    checkout = st.get("checkout")
    photos = h.get("photos") or h.get("images") or []
    # текст вывода
    text = (
        f"🏨 <b>{name}</b>\n"
        f"💵 {price}\n"
        f"📅 {checkin} — {checkout}\n"
        f"📍 {coords_lat},{coords_lon}\n"
        f"🔗 {link}\n\n"
        f"{descr}"
    )
    # клавиатура пагинации
    kb = types.InlineKeyboardMarkup()
    if page > 0:
        kb.add(types.InlineKeyboardButton("⬅️ Пред", callback_data=f"page:{page-1}"))
    kb.add(
        types.InlineKeyboardButton(f"{page+1}/{len(hotels)}", callback_data="page:noop")
    )
    if page < len(hotels) - 1:
        kb.add(types.InlineKeyboardButton("След ➡️", callback_data=f"page:{page+1}"))
    # Отправляем фото (если есть) с подписью
    try:
        if photos:
            bot.send_photo(
                chat_id, photos[0], caption=text, parse_mode="HTML", reply_markup=kb
            )
        else:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
    # Сохраняем просмотренный отель в БД
    try:
        HotelSearchHistory.create(
            user_id=str(chat_id),
            city=st.get("city"),
            hotel_name=name,
            link=link,
            description=descr,
            price=(
                float(str(price).replace("$", "").replace(",", ""))
                if isinstance(price, (str, int, float))
                else 0
            ),
            checkin=checkin,
            checkout=checkout,
            photos=",".join(photos) if isinstance(photos, list) else (photos or ""),
            latitude=str(coords_lat) if coords_lat is not None else None,
            longitude=str(coords_lon) if coords_lon is not None else None,
        )
    except Exception as e:
        print("DB save error:", e)


# Обработка нажатия пагинации
@bot.callback_query_handler(
    func=lambda call: call.data and call.data.startswith("page:")
)
def cb_page(call):
    chat_id = call.message.chat.id
    data = call.data
    parts = data.split(":")
    if len(parts) >= 2:
        try:
            page = int(parts[1])
        except Exception:
            bot.answer_callback_query(call.id)
            return
        set_state(chat_id, page=page)
        show_result_page(chat_id)
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id)
