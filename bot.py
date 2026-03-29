import telebot
import json
import re
from flask import Flask, request
from datetime import datetime, timedelta
import threading
import time
import random
from telebot.types import ReplyKeyboardMarkup

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

# ===== MENU =====
def menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📅 Bugungi ishlar", "➕ Vazifa qo‘shish")
    markup.add("🗑 O‘chirish", "📊 Statistika")
    markup.add("💧 Sog‘liq", "🔥 Motivatsiya")
    return markup

# ===== MOTIVATION =====
motivations = [
    "🔥 Bugun boshlamasang, ertaga ham boshlamaysan!",
    "💪 Harakat qil — natija keladi!",
    "🚀 Kichik qadamlar katta natija beradi!",
    "😎 Sen uddalaysan!",
    "🏆 Bugun o‘zingni yeng!"
]

# ===== WEBHOOK =====
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "SUPER BOT ishlayapti!"

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Assalomu alaykum!\n\n"
        "🤖 *Bu oddiy bot emas...*\n\n"
        "🔥 Men sizning shaxsiy yordamchingizman:\n\n"
        "📝 Vazifalarni boshqaraman\n"
        "⏰ O‘zim eslataman\n"
        "💧 Sog‘liqni nazorat qilaman\n"
        "📊 Natijani ko‘rsataman\n"
        "🔥 Motivatsiya beraman\n\n"
        "👇 Boshlash uchun tugmani bosing!",
        parse_mode="Markdown",
        reply_markup=menu()
    )

# ===== REMINDER =====
def reminder_loop():
    while True:
        data = load_data()
        now = datetime.now().strftime("%H:%M %d.%m.%Y")

        for user_id in data:
            for task in data[user_id]["tasks"]:
                if task["time"] == now:
                    bot.send_message(
                        user_id,
                        f"⏰ VAQT KELDI!\n\n👉 {task['text']}\n\n🔥 Hozir bajarish kerak!"
                    )

        time.sleep(60)

threading.Thread(target=reminder_loop, daemon=True).start()

# ===== MAIN =====
@bot.message_handler(func=lambda message: True)
def handle(message):
    text = message.text.lower()
    user_id = str(message.chat.id)

    data = load_data()

    if user_id not in data:
        data[user_id] = {"tasks": []}

    # ===== BUTTONS =====
    if text == "📅 bugungi ishlar":
        today = datetime.now().strftime("%d.%m.%Y")
        tasks = [t["text"] for t in data[user_id]["tasks"] if today in t["time"]]

        if tasks:
            msg = "📅 Bugungi ishlar:\n\n"
            for i, t in enumerate(tasks, 1):
                msg += f"{i}. {t}\n"
        else:
            msg = "📭 Bugun vazifa yo‘q"

        bot.send_message(message.chat.id, msg)
        return

    if text == "📊 statistika":
        count = len(data[user_id]["tasks"])
        bot.send_message(message.chat.id, f"📊 Jami vazifalar: {count}")
        return

    if text == "💧 sog‘liq":
        bot.send_message(
            message.chat.id,
            "💧 Suv iching!\n🚶 10 minut yurib keling!\n😴 Dam oling!"
        )
        return

    if text == "🔥 motivatsiya":
        bot.send_message(message.chat.id, random.choice(motivations))
        return

    if text == "➕ vazifa qo‘shish":
        bot.send_message(
            message.chat.id,
            "✍️ Vazifani yozing:\n\n"
            "Masalan:\n"
            "👉 yugurish 18:00 30.03.2026\n\n"
            "Men sizga o‘zim eslataman 😉"
        )
        return

    if text == "🗑 o‘chirish":
        tasks = data[user_id]["tasks"]
        if tasks:
            msg = "🗑 Qaysi birini o‘chirasiz?\n\n"
            for i, t in enumerate(tasks, 1):
                msg += f"{i}. {t['text']}\n"
            msg += "\n✍️ o'chir 1 deb yozing"
        else:
            msg = "📭 Hech narsa yo‘q"

        bot.send_message(message.chat.id, msg)
        return

    if text.startswith("o'chir"):
        try:
            index = int(text.split()[1]) - 1
            removed = data[user_id]["tasks"].pop(index)
            save_data(data)
            bot.send_message(message.chat.id, f"🗑 O‘chirildi:\n{removed['text']}")
        except:
            bot.send_message(message.chat.id, "❌ Format: o'chir 1")
        return

    # ===== SMART PARSE =====
    time_match = re.search(r"\d{1,2}:\d{2}", text)
    date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", text)

    if time_match and date_match:
        task_time = f"{time_match.group()} {date_match.group()}"

        data[user_id]["tasks"].append({
            "text": message.text,
            "time": task_time
        })

        save_data(data)

        bot.send_message(
            message.chat.id,
            f"✅ Saqlandi!\n⏰ {task_time} da eslataman\n\n🔥 Unutmang — bajarish kerak!"
        )
        return

    # ===== DEFAULT =====
    bot.send_message(
        message.chat.id,
        "🤖 Tushunmadim...\n\n👉 Tugmalardan foydalaning yoki to‘g‘ri formatda yozing"
    )

# ===== RUN =====
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://mybot-4k74.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=10000)
