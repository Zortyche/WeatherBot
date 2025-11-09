import os
import json
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

# ====== Настройки ======
TELEGRAM_TOKEN = "8318591890:AAFI1wld9Ip-NIa6OVcxO0udFUlEmvSXrlQ"  # токен от BotFather
WEATHER_API_KEY = "eee49e70307f2f9bfca6496ec6a219ce"               # ключ OpenWeather
USER_DATA_FILE = "users.json"

# ====== Flask сервер ======
app = Flask(__name__)

# ====== Загрузка/Сохранение пользователей ======
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False)

users = load_users()

# ====== Шуточные советы ======
def funny_advice(temp: float):
    if temp <= -20:
        return "🥶 Дубак! Лучше дома с пледом и горячим шоколадом!"
    elif temp <= -10:
        return "🥶 Терпимо! Если по кайфу — иди на улицу!"
    elif temp <= 0:
        return "❄️ Снег и мороз. Приготовь калготы!"
    elif temp <= 10:
        return "🧥 Прохладно. Возьми накидку с капюшоном!"
    elif temp <= 20:
        return "🌤️ Погода норм. Можно погулять, если есть монета."
    elif temp <= 30:
        return "😎 Отличная погода для прогулки, но не забудь воду."
    else:
        return "🔥 Жара! Лучше кондиционер, мороженое и прохлада дома."

# ====== Получение погоды ======
def get_weather(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        emoji_map = {
            "дождь": "🌧️",
            "снег": "❄️",
            "облачно": "☁️",
            "ясно": "☀️",
            "туман": "🌫️",
        }
        weather_emoji = next((e for k, e in emoji_map.items() if k in description.lower()), "🌡️")
        advice = funny_advice(temp)
        return (
            f"{weather_emoji} Прогноз для {city}:\n"
            f"🌡️ Температура: {temp}°C\n"
            f"🌤 Состояние: {description}\n"
            f"💧 Влажность: {humidity}%\n\n"
            f"💡 Совет: {advice}"
        )
    else:
        return "❌ Не могу найти этот город, попробуй другой."

# ====== Команды бота ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здарова! Я бот-прогноз погоды 😎\n"
        "Пропиши /setcity <город>, чтобы установить ваш город.\n"
        "Пример: /setcity Moscow"
    )

async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not context.args:
        await update.message.reply_text("❌ Пожалуйста, укажите город: /setcity Moscow")
        return
    city = " ".join(context.args)
    users[chat_id] = city
    save_users(users)
    await update.message.reply_text(f"✅ Город установлен: {city}")

async def weather_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    city = users.get(chat_id)
    if not city:
        await update.message.reply_text("❌ Сначала установите город: /setcity Moscow")
        return
    weather_info = get_weather(city)
    await update.message.reply_text(weather_info)

# ====== Telegram Application ======
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("setcity", set_city))
application.add_handler(CommandHandler("weather", weather_now))

# ====== Webhook endpoint для Render ======
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    # Вместо asyncio.run используем create_task
    asyncio.create_task(application.process_update(update))
    return "OK", 200

# ====== Health check ======
@app.route("/")
def home():
    return "Bot is alive!", 200

# ====== Запуск ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
