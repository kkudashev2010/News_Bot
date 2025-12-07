from loader import bot
from telebot import types
from database.models import HotelSearchHistory


@bot.message_handler(commands=["history"])
def cmd_history(message):
    chat_id = message.chat.id
    rows = (
        HotelSearchHistory.select()
        .where(HotelSearchHistory.user_id == str(chat_id))
        .order_by(HotelSearchHistory.date.desc())
        .limit(10)
    )
    if not rows:
        bot.send_message(chat_id, "История пуста.")
        return
    for r in rows:
        text = f"📅 {r.date.strftime('%Y-%m-%d %H:%M')}\n🏨 {r.hotel_name}\n💰 {r.price}$\n📍 {r.latitude},{r.longitude}\n<a href='{r.link}'>Ссылка</a>\n{r.description}"
        bot.send_message(
            chat_id, text, disable_web_page_preview=False, parse_mode="HTML"
        )
