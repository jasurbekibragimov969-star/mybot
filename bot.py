import telebot
import json
import re
from flask import Flask, request
from datetime import datetime, timedelta
import threading
import time

TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "data.json"

# ===== DATA =====
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ===== WEBHOOK =====
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Jasurbek super bot ishlayapti!"

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Assalomu alaykum!\n\n"
        "🤖 Men *Jasurbekning aqlli yordamchi botiman*\n\n"
        "💡 Qila olaman:\n"
        "• 📝 Vazifalarni saqlayman\n"
        "• ⏰ Eslataman\n"
        "• 💧 Sog‘liq maslahatlari beraman\n\n"
        "✍️ Shunchaki yozing (masalan: *ertaga 18:00 uchrashuv*)",
        parse_mode="Markdown"
    )

# ===== REMINDER LOOP =====
def reminder_loop():
    while True:
        data = load_data()
        now = datetime.now().strftime("%H:%M")
        for user_id in data:
            for task in data[user_id]["tasks"]:
                if task["time"] == now:
                    bot.send_message(user_id, f"⏰ Eslatma:\n👉 {task['text']}")
        time.sleep(60)

threading.Thread(target=reminder_loop, daemon=True).start()

# ===== HEALTH LOOP =====
def health_loop():
    while True:
        data = load_data()
        for user_id in data:
            bot.send_message(user_id, "💧 Suv ichishni unutmang!")
        time.sleep(3600)

threading.Thread(target=health_loop, daemon=True).start()

# ===== MESSAGE =====
@bot.message_handler(func=lambda message: True)
def handle(message):
    text = message.text.lower()
    user_id = str(message.chat.id)

    data = load_data()

    if user_id not in data:
        data[user_id] = {"tasks": []}

    # ===== SHOW TODAY =====
    if "bugun" in text and "nima" in text:
        today = datetime.now().strftime("%Y-%m-%d")
        tasks = [t["text"] for t in data[user_id]["tasks"] if t["date"] == today]
        if tasks:
            bot.send_message(message.chat.id, "📅 Bugungi ishlar:\n" + "\n".join(tasks))
        else:
            bot.send_message(message.chat.id, "📭 Hech narsa yo‘q")
        return

    # ===== DATE =====
    if "ertaga" in text:
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        date = datetime.now().strftime("%Y-%m-%d")

    # ===== TIME =====
    time_match = re.search(r"\d{1,2}:\d{2}", text)
    task_time = time_match.group() if time_match else ""

    # ===== SAVE =====
    data[user_id]["tasks"].append({
        "text": message.text,
        "date": date,
        "time": task_time
    })

    save_data(data)

    # ===== RESPONSE =====
    msg = "✅ Saqlandi!"

    if task_time:
        msg += f"\n⏰ {task_time} da eslataman"

    if "sport" in text or "yur" in text:
        msg += "\n💪 Zo‘r! Sog‘liq muhim"

    bot.send_message(message.chat.id, msg)

# ===== RUN =====
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://mybot-4k74.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=10000)
