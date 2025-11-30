from loader import bot
from telebot import types
from api.request import get_dest_id, search_hotels
import keyboards.inline as kb
import datetime
import keyboards.calendar_custom as calendar_custom
from utils.date_validator import parse_iso_date, check_range

USER_STATE = {}


def set_state(chat_id, **kwargs):
    st = USER_STATE.get(chat_id, {})
    st.update(kwargs)
    USER_STATE[chat_id] = st


def get_state(chat_id):
    return USER_STATE.get(chat_id, {})

@bot.message_handler(commands=['search_hotels'])
def start_search(message):
    chat_id = message.chat.id
    set_state(chat_id, step='city')
    msg = bot.send_message(chat_id, "Введите город для поиска:")
    bot.register_next_step_handler(msg, process_city)

def process_city(message):
    chat_id = message.chat.id
    city = message.text.strip()
    dests = get_dest_id(city)
    if not dests or not dests.get("data"):
        bot.send_message(chat_id, "Не удалось найти город.")
        return

    # Фильтруем только CITY
    city_options = [d for d in dests["data"] if d.get("dest_type") == "CITY"]
    if not city_options:
        city_options = dests["data"]

    # Берём первый для упрощения
    dest_id = city_options[0]["dest_id"]

    set_state(chat_id, dest_id=dest_id, city=city, step='arrival_date')

    today = datetime.date.today()
    kb_calendar = calendar_custom.build_month_markup(today.year, today.month, role='checkin', min_date=today)
    print(today)
    bot.send_message(chat_id, f"Выбран город: {city}\nВыберите дату заезда:", reply_markup=kb_calendar)
#
# @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("cal_select:"))
# def callback_calendar(call):
#     print('qwerty')
@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("cal_select:"))
def callback_calendar(call):
    chat_id = call.message.chat.id
    parts = call.data.split(":")
    _, role, date_str = parts

    if role == "checkin":
        set_state(chat_id, arrival_date=date_str)
        min_date = datetime.date.fromisoformat(date_str) + datetime.timedelta(days=1)
        kb_checkout = calendar_custom.build_month_markup(min_date.year, min_date.month, role='checkout', min_date=min_date)
        print('min date', min_date)
        bot.edit_message_text(f"Дата заезда: {date_str}\nТеперь выберите дату выезда:", chat_id, call.message.message_id, reply_markup=kb_checkout)
    elif role == "checkout":
        st = get_state(chat_id)
        checkin = parse_iso_date(st.get("arrival_date"))
        checkout = parse_iso_date(date_str)
        ok, msg = check_range(checkin, checkout)
        if not ok:
            bot.answer_callback_query(call.id, msg)
            return
        set_state(chat_id, departure_date=date_str, step='optional')
        bot.edit_message_text(f"Дата выезда: {date_str}\nТеперь выберите, что хотите уточнить:", chat_id, call.message.message_id, reply_markup=kb.optional_params_kb())

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("param:"))
def callback_params(call):
    chat_id = call.message.chat.id
    param = call.data.split(":")[1]
    st = get_state(chat_id)

    if param == "adults":
        msg = bot.send_message(chat_id, "Введите количество взрослых (например: 2):")
        bot.register_next_step_handler(msg, set_adults)
    elif param == "children_age":
        msg = bot.send_message(chat_id, "Введите возраст детей через запятую (например: 5,12). Если нет — напишите 0:")
        bot.register_next_step_handler(msg, set_children)
    elif param == "room_qty":
        msg = bot.send_message(chat_id, "Введите количество комнат (например: 1):")
        bot.register_next_step_handler(msg, set_rooms)
    elif param == "price":
        msg = bot.send_message(chat_id, "Введите диапазон цен в рублях (например: 1000-5000):")
        bot.register_next_step_handler(msg, set_price)
    elif param == "show":
        show_hotels(call.message, st)
    else:
        bot.answer_callback_query(call.id, "Неизвестный параметр.")


def set_adults(message):
    chat_id = message.chat.id
    try:
        adults = int(message.text.strip())
        set_state(chat_id, adults=adults)
        bot.send_message(chat_id, f"Количество взрослых установлено: {adults}", reply_markup=kb.optional_params_kb())
    except ValueError:
        bot.send_message(chat_id, "Введите целое число, пожалуйста.")


def set_children(message):
    chat_id = message.chat.id
    ages = message.text.strip()
    set_state(chat_id, children_age=ages)
    bot.send_message(chat_id, f"Возраст(а) детей: {ages}", reply_markup=kb.optional_params_kb())


def set_rooms(message):
    chat_id = message.chat.id
    try:
        rooms = int(message.text.strip())
        set_state(chat_id, room_qty=rooms)
        bot.send_message(chat_id, f"Количество комнат: {rooms}", reply_markup=kb.optional_params_kb())
    except ValueError:
        bot.send_message(chat_id, "Введите целое число, пожалуйста.")


def set_price(message):
    chat_id = message.chat.id
    text = message.text.strip()
    if "-" in text:
        try:
            low, high = map(int, text.split("-"))
            set_state(chat_id, price_min=low, price_max=high)
            bot.send_message(chat_id, f"Диапазон цен: от {low}₽ до {high}₽", reply_markup=kb.optional_params_kb())
        except ValueError:
            bot.send_message(chat_id, "Введите числа корректно, например: 1000-5000")
    else:
        bot.send_message(chat_id, "Формат должен быть 1000-5000")


# Листание календаря назад / вперёд
@bot.callback_query_handler(func=lambda call: call.data and (call.data.startswith("cal_prev:") or call.data.startswith("cal_next:")))
def calendar_switch(call):
    parts = call.data.split(":")
    print('parts', parts)
    action = parts[0]       # cal_prev / cal_next
    role = parts[1]
    year = int(parts[2])
    month = int(parts[3])

    if action == "cal_prev":
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    elif action == "cal_next":
        month += 1
        if month > 12:
            month = 1
            year += 1
    print('161',month)

    st = get_state(call.message.chat.id)

    # Минимальная дата — для checkout это checkin + 1 день
    min_date = None
    if role == "checkout" and st.get("arrival_date"):
        min_date = datetime.date.fromisoformat(st["arrival_date"]) + datetime.timedelta(days=1)

    markup = calendar_custom.build_month_markup(year, month, role, min_date)

    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )


def show_hotels(message, st):
    """Запуск поиска отелей"""
    from api.request import search_hotels

    params = {
        "dest_id": st.get("dest_id"),
        "search_type": "CITY",
        "arrival_date": st.get("arrival_date"),
        "departure_date": st.get("departure_date"),
        "adults": st.get("adults", 1),
        "children_age": st.get("children_age", "0"),
        "room_qty": st.get("room_qty", 1),
        "price_min": st.get("price_min", 0),
        "price_max": st.get("price_max", 1000000)
    }

    bot.send_message(message.chat.id, "🔎 Ищу подходящие отели...")

    try:
        result = search_hotels(params)
        print(result)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при запросе: {e}")
        return

    # ✅ исправление: API возвращает список, а не словарь
    data = result.get("data", [])
    if not isinstance(data, list):
        data = [data]  # оборачиваем в список, если вдруг dict

    if not data:
        bot.send_message(message.chat.id, "😞 API не вернул результатов.")
        return

    # ✅ фильтруем реальные отели
    hotels = [item for item in data if item.get("search_type") == "hotel" or item.get("dest_type") == "hotel"]

    if not hotels:
        bot.send_message(message.chat.id, "😞 Не удалось найти отели для выбранного города.")
        return

    # 🏨 выводим первые 5 отелей
    for hotel in hotels[:5]:
        name = hotel.get("name", "Без названия")
        region = hotel.get("region", "")
        country = hotel.get("country", "")
        image = hotel.get("image_url", "")
        dest_id = hotel.get("dest_id")
        url = f"https://www.booking.com/hotel/{dest_id}.html" if dest_id else "https://www.booking.com"

        caption = (
            f"🏨 <b>{name}</b>\n"
            f"📍 {region}, {country}\n"
            f"🔗 <a href='{url}'>Открыть на Booking.com</a>"
        )

        if image:
            try:
                bot.send_photo(message.chat.id, photo=image, caption=caption, parse_mode="HTML")
            except Exception as e:
                print(f"⚠ Ошибка при отправке фото: {e}")
                bot.send_message(message.chat.id, caption, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, caption, parse_mode="HTML")

