import asyncio
import requests
from datetime import timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import numpy as np

# === Configuration ===
TELEGRAM_BOT_TOKEN = "7277864923:AAE04dOSmtbuPzY2G2acYtXxTnoAbjywUqQ"
FOREX_API_KEY = "660eb6cfcada872e7ad01179419c0c79"
FOREX_API_URL = "http://api.currencylayer.com/live"

# === Globals ===
quote_currency = None
base_currency = "USD"
utc_plus_one = timezone(timedelta(hours=1))

# === Fetch Forex Rate ===
def fetch_forex_data():
    try:
        params = {
            'access_key': FOREX_API_KEY,
            'currencies': quote_currency,         # e.g., 'JPY'
            'source': base_currency,              # e.g., 'USD'
            'format': 1
        }
        response = requests.get(FOREX_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get('success', False):
            raise ValueError(f"API Error: {data.get('error', {}).get('info', 'Unknown error')}")

        rate_key = f"{base_currency}{quote_currency}"
        return data['quotes'].get(rate_key, None)
    except Exception as e:
        print(f"[Error] Fetching forex data: {e}")
        return None

# === Action Logic ===
def determine_best_action(rate):
    if not rate:
        return "❌ No valid data to determine action."

    # Simulate movement within ±0.8%
    simulated_rate = rate * (1 + np.random.uniform(-0.008, 0.008))
    pip_diff = (simulated_rate - rate) * 10000

    if abs(pip_diff) >= 7000:  # At least 7000 pips
        action = "SELL 📉" if pip_diff > 0 else "BUY 📈"
        safety = "✅ Safe to act"
    else:
        action = "HOLD ✋"
        safety = "⚠️ Not safe to act yet"

    return (
        f"💱 Pair: {base_currency}/{quote_currency}\n"
        f"🔹 Current Rate: {rate:.5f}\n"
        f"🔸 Simulated Rate: {simulated_rate:.5f}\n"
        f"📊 Pip Change: {pip_diff:.2f} pips\n"
        f"🧠 Action: {action}\n"
        f"🔐 Safety: {safety}"
    )

# === Telegram Bot Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💵 Select Quote Currency", callback_data='select_quote_currency')]]
    await update.message.reply_text("👋 Welcome to Forex Action Bot!\nChoose a quote currency to begin:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global quote_currency
    query = update.callback_query
    await query.answer()

    if query.data == 'select_quote_currency':
        keyboard = [
            [InlineKeyboardButton("EUR", callback_data='EUR'), InlineKeyboardButton("GBP", callback_data='GBP')],
            [InlineKeyboardButton("JPY", callback_data='JPY'), InlineKeyboardButton("AUD", callback_data='AUD')],
            [InlineKeyboardButton("INR", callback_data='INR'), InlineKeyboardButton("CAD", callback_data='CAD')],
            [InlineKeyboardButton("CHF", callback_data='CHF'), InlineKeyboardButton("NZD", callback_data='NZD')],
            [InlineKeyboardButton("IDR", callback_data='IDR'), InlineKeyboardButton("TRY", callback_data='TRY')],
            [InlineKeyboardButton("MXN", callback_data='MXN'), InlineKeyboardButton("CNY", callback_data='CNY')],
            [InlineKeyboardButton("USD", callback_data='USD'), InlineKeyboardButton("CNH", callback_data='CNH')],
        ]
        await query.edit_message_text("🪙 Select a quote currency:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ['EUR', 'GBP', 'JPY', 'AUD', 'INR', 'CAD', 'CHF', 'NZD', 'IDR', 'TRY', 'MXN', 'CNY', 'USD', 'CNH']:
        quote_currency = query.data
        keyboard = [[InlineKeyboardButton("📊 Determine Action", callback_data='determine_action')]]
        await query.edit_message_text(
            text=f"✅ Quote currency set to {quote_currency}\nBase: {base_currency}\nClick below to analyze the market.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == 'determine_action':
        await query.edit_message_text(text="⏳ Analyzing market rate...")
        rate = fetch_forex_data()
        result = determine_best_action(rate)
        await context.bot.send_message(chat_id=query.message.chat_id, text=result)

# === Bot Initialization ===
app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

# === Start Bot ===
print("✅ Forex Action Bot is running...")
app.run_polling()
