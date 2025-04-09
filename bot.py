
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import datetime
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

user_data = {}

def analyze_coeffs(coeffs, timestamps):
    last10 = coeffs[-10:]
    low_series = 0
    for coef in reversed(last10):
        if coef <= 1.5:
            low_series += 1
        else:
            break
    recent_max = max(last10)

    last_high_time = None
    for coef, ts in reversed(list(zip(coeffs, timestamps))):
        if coef >= 10:
            last_high_time = ts
            break
    time_diff_text = "—"
    if last_high_time:
        delta = datetime.datetime.now() - last_high_time
        minutes = int(delta.total_seconds() // 60)
        time_diff_text = f"{minutes} мин назад"

    if low_series >= 5:
        advice = "Ожидается высокий коэффициент! Можно рискнуть."
    elif recent_max >= 10 and last_high_time and minutes <= 10:
        advice = "Недавно был x10+, подожди немного."
    else:
        advice = "Играй осторожно на x1.5."

    return advice, low_series, recent_max, time_diff_text

def main_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить коэффициенты", callback_data='add')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton("♻️ Сбросить", callback_data='reset')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать! Используй кнопки ниже:", reply_markup=main_menu())

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_data:
        user_data[user_id] = {"coeffs": [], "timestamps": []}

    if query.data == 'add':
        await query.edit_message_text("Отправь коэффициенты через пробел, например:\n`1.2 2.5 3.1`", parse_mode='Markdown')
    elif query.data == 'reset':
        user_data[user_id] = {"coeffs": [], "timestamps": []}
        await query.edit_message_text("История сброшена.", reply_markup=main_menu())
    elif query.data == 'stats':
        coeffs = user_data[user_id]["coeffs"]
        timestamps = user_data[user_id]["timestamps"]
        if not coeffs:
            await query.edit_message_text("Нет данных. Сначала добавь коэффициенты.", reply_markup=main_menu())
            return
        _, low_series, recent_max, last_high = analyze_coeffs(coeffs, timestamps)
        msg = (
            f"Всего раундов: {len(coeffs)}\n"
            f"Низких подряд: {low_series}\n"
            f"Максимум за 10 игр: x{recent_max}\n"
            f"Последний x10+: {last_high}"
        )
        await query.edit_message_text(msg, reply_markup=main_menu())

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    try:
        coeffs = list(map(float, text.split()))
        now = datetime.datetime.now()

        if user_id not in user_data:
            user_data[user_id] = {"coeffs": [], "timestamps": []}
        user_data[user_id]["coeffs"].extend(coeffs)
        user_data[user_id]["timestamps"].extend([now] * len(coeffs))

        user_data[user_id]["coeffs"] = user_data[user_id]["coeffs"][-50:]
        user_data[user_id]["timestamps"] = user_data[user_id]["timestamps"][-50:]

        advice, _, _, _ = analyze_coeffs(user_data[user_id]["coeffs"], user_data[user_id]["timestamps"])
        await update.message.reply_text(advice, reply_markup=main_menu())
    except:
        await update.message.reply_text("Ошибка! Введи коэффициенты через пробел, например: 1.2 2.5 3.1", reply_markup=main_menu())

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    app.run_polling()
