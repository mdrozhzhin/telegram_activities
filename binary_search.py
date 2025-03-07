from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os

load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['step'] = 'a1'
    await update.message.reply_text('Введите нижнюю границу (a1):')

async def input_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    text = update.message.text.strip()

    try:
        num = int(text)
    except ValueError:
        await update.message.reply_text("Ошибка! Введите целое число.")
        return

    if user_data.get('step') == 'a1':
        user_data['a1'] =num
        user_data['step'] = 'a2'
        await update.message.reply_text(f"Введите верхнюю границу (a2), которая должна быть больше {num}.")

    user_data['a2'] = num
    user_data['step'] = None
    user_data['d'] = 0

    c = (user_data['a1'] + user_data['a2']) // 2
    user_data['c'] = c

    keyboard = [
        [
        InlineKeyboardButton(">", callback_data='>'),
        InlineKeyboardButton("<", callback_data='<'),
        InlineKeyboardButton("=", callback_data='='),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Возможно это - {c}?", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = context.user_data

    if 'a1' not in user_data or 'a2' not in user_data:
        await query.edit_message_text(text="Начните новую игру с помощью /start")
        return

    b = query.data
    a1 = user_data['a1']
    a2 = user_data['a2']
    d = user_data['d']
    c_prev = user_data['c']

    if b == '>':
        a1 = c_prev
    elif b == '<':
        a2 = c_prev
    elif b == '=':
        await query.edit_message_text(text='Угадал!')
        user_data.clear()
        return

    if a1 >= a2:
        await query.edit_message_text(text='Где-то ошибка или неточные данные.')
        user_data.clear()
        return

    new_c = (a1 + a2) // 2
    if new_c == d:
        new_c -= 1

    user_data['a1'] = a1
    user_data['a2'] = a2
    user_data['d'] = c_prev
    user_data['c'] = new_c

    keyboard = [
        [
            InlineKeyboardButton(">", callback_data='>'),
            InlineKeyboardButton("<", callback_data='<'),
            InlineKeyboardButton("=", callback_data='='),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Возможно это - {new_c}?", reply_markup=reply_markup)

def main():
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, input_range))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()


