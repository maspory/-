
import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import ccxt
import asyncio
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# حافظه تنظیمات کاربر
user_settings = {}

# کیبورد انتخاب تایم‌فریم
timeframes = ["1h", "2h", "3h", "4h"]
markup = ReplyKeyboardMarkup.from_column(timeframes, resize_keyboard=True)

# شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ دسترسی ندارید.")
        return
    user_settings[update.effective_user.id] = {"tf": "1h", "shift": 3, "percent": 2}
    await update.message.reply_text("✅ ربات فعال شد.

دستور /set برای تنظیمات بیشتر.
/startalerts برای شروع پایش.", reply_markup=markup)

# تغییر تنظیمات
async def set_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = "لطفاً مقادیر جدید را با فرمت زیر بفرست:

`tf=1h shift=3 percent=2`"
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = update.message.text
    try:
        parts = dict(part.split("=") for part in msg.split())
        tf = parts["tf"]
        shift = int(parts["shift"])
        percent = float(parts["percent"])
        user_settings[update.effective_user.id] = {"tf": tf, "shift": shift, "percent": percent}
        await update.message.reply_text("✅ تنظیمات به‌روزرسانی شد.")
    except:
        await update.message.reply_text("❌ فرمت اشتباه بود.")

# شروع پایش
async def start_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    settings = user_settings.get(update.effective_user.id, {"tf": "1h", "shift": 3, "percent": 2})
    await update.message.reply_text(f"🔎 پایش آغاز شد:
Timeframe: {settings['tf']}
Shift: {settings['shift']}
%: {settings['percent']}")
    await monitor_market(update, settings)

# پایش بازار
async def monitor_market(update: Update, settings):
    binance = ccxt.binance()
    markets = binance.load_markets()
    symbols = [s for s in markets if "/USDT" in s and ".e" not in s]

    results = []
    for symbol in symbols:
        try:
            ohlcv = binance.fetch_ohlcv(symbol, timeframe=settings["tf"])
            if len(ohlcv) < settings["shift"] + 1:
                continue
            past = sum([x[4] for x in ohlcv[-settings["shift"]-1:-1]]) / settings["shift"]
            current = ohlcv[-1][4]
            change = ((current - past) / past) * 100
            if change >= settings["percent"]:
                results.append(f"{symbol}: {round(change, 2)}% ↑")
        except:
            continue

    if results:
        await update.message.reply_text("🚀 پامپ‌های شناسایی‌شده:
" + "
".join(results))
    else:
        await update.message.reply_text("❌ پامپی یافت نشد.")

# شروع برنامه
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_settings))
    app.add_handler(CommandHandler("startalerts", start_alerts))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings))
    app.run_polling()
