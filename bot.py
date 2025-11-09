import json
import os
import requests
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# ====== Настройки ======
TELEGRAM_TOKEN = os.environ.get("eee49e70307f2f9bfca6496ec6a219ce")
WEATHER_API_KEY = os.environ.get("8318591890:AAFI1wld9Ip-NIa6OVcxO0udFUlEmvSXrlQ")
USER_DATA_FILE = "users.json"

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

# ====== Шуточные советы в зависимости от температуры ======
def funny_advice(temp: float):
    if temp <= -20:
        return "🥶 Дубак ! Лучше дома с пледом и горячим шоколадом!"
    elif temp <= -10:
        return "🥶 Терпимо! Если по кайфу иди на улицу!"
    elif temp <= 0:
        return "❄️ Снег и мороз. Приготовь калгоки!"
    elif temp <= 10:
        return "🧥 Прохладно. Возьми накидку с капюшоном!"
    elif temp <= 20:
        return "🌤️ Погода норм. Можно погулять, если есть монета."
    elif temp <= 30:
        return "😎 Заебись! Отличная погода для прогулки, но не забудь воду."
    else:
        return "🔥 Жара! Лучше кондиционер, мороженое и прохлада дома."

# ====== Функция получения погоды ======
def get_weather(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200:
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        emoji_map = {
            "дождь": "🌧️",
            "снег": "❄️",
            "облачно": "☁️",
            "ясно": "☀️",
            "туман": "🌫️",
        }
        weather_emoji = next((e for k, e in emoji_map.items() if k in description.lower()), "🌡️")
        advice = funny_advice(temp)
        return f"{weather_emoji} Прогноз для {city}:\n" \
               f"🌡️ Температура: {temp}°C\n" \
               f"🌤 Состояние: {description}\n" \
               f"💧 Влажность: {humidity}%\n\n" \
               f"💡 Совет: {advice}"
    else:
        return "❌ Город хуйня не могу найти, переезжай."

# ====== Команды бота ======
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Здарова Слоняра! Я бот-прогноз погоды 😎\n"
        "Пропиши /setcity <город>, чтобы установить ваш город.\n"
        "Пример: /setcity Moscow"
    )

def set_city(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    if not context.args:
        update.message.reply_text("❌ Пожалуйста, укажите город: /setcity Moscow")
        return
    city = " ".join(context.args)
    users[chat_id] = city
    save_users(users)
    update.message.reply_text(f"✅ Город установлен: {city}")

def weather_now(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    city = users.get(chat_id)
    if not city:
        update.message.reply_text("❌ Сначала установите город: /setcity Moscow")
        return
    update.message.reply_text(get_weather(city))

# ====== Инициализация бота ======
updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("setcity", set_city))
dispatcher.add_handler(CommandHandler("weather", weather_now))

# ====== Запуск бота ======
updater.start_polling()
print("Бот фурычит, можно рабоать")
updater.idle()
