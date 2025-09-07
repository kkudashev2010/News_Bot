from telebot.types import Message

from loader import bot


@bot.message_handler(commands=["low"])
def bot_low(message: Message):
    bot.reply_to(
        message,
        f"Отображение самых доступных отелей в указанном городе: {message.text}",
    )
