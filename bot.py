import telebot
from telebot.types import ReplyKeyboardMarkup
import threading
from flask import Flask
from datetime import datetime, timedelta
import json

TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
bot = telebot.TeleBot(TOKEN)

# ===== WEB =====
app = Flask(__name__)

@app.route('/')
def home():
    return "School Bot Running"

def run():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run).start()

# ===== DATA FILE =====
DATA_FILE = "attendance.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ===== LOGIN =====
teachers_login = {
    "feruza_01": "feruza1234",
    "feruza_02": "feruza1234"
}

logged_users = {}

ADMIN_ID = 6344661867

# ===== MENU =====
def main_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🏫 Mening maktabim")
    m.add("👨‍🏫 O‘qituvchilar", "📚 Sinflar")
    m.add("📰 Yangiliklar", "📩 Murojaat")
    m.add("👨‍💼 O‘qituvchi kabineti")
    return m

def teacher_panel():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("✅ Keldim", "❌ Ketdim")
    m.add("⚠️ Uzrli", "📊 Statistika")
    m.add("📅 Sana bo‘yicha")
    m.add("🔙 Chiqish")
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(
        m.chat.id,
        "👋 Assalomu alaykum!\n\n🏫 *10-maktab tizimi*\n\n👇 Tanlang:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ===== MAIN =====
@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text
    user_id = m.chat.id

    # ORQAGA
    if text == "🔙 Chiqish":
        logged_users.pop(user_id, None)
        bot.send_message(user_id, "🔙 Asosiy menyu", reply_markup=main_menu())
        return

    # LOGIN START
    if text == "👨‍💼 O‘qituvchi kabineti":
        bot.send_message(user_id, "👤 Username kiriting:")
        logged_users[user_id] = {"step": "user"}
        return

    if user_id in logged_users:

        step = logged_users[user_id]["step"]

        if step == "user":
            logged_users[user_id]["username"] = text
            logged_users[user_id]["step"] = "pass"
            bot.send_message(user_id, "🔒 Parol kiriting:")
            return

        if step == "pass":
            username = logged_users[user_id]["username"]
            if username in teachers_login and teachers_login[username] == text:
                logged_users[user_id] = {"step": "done", "username": username}
                bot.send_message(user_id, "✅ Xush kelibsiz", reply_markup=teacher_panel())
            else:
                bot.send_message(user_id, "❌ Login xato")
                logged_users.pop(user_id)
            return

        # ===== KABINET =====
        if step == "done":

            username = logged_users[user_id]["username"]

            now = datetime.utcnow() + timedelta(hours=5)
            date = now.strftime("%Y-%m-%d")
            time = now.strftime("%H:%M")

            data = load_data()

            if date not in data:
                data[date] = []

            if text == "✅ Keldim":
                data[date].append({"user": username, "status": "Keldi", "time": time})
                save_data(data)
                bot.send_message(user_id, "🟢 Keldi belgilandi")
                return

            if text == "❌ Ketdim":
                data[date].append({"user": username, "status": "Ketdi", "time": time})
                save_data(data)
                bot.send_message(user_id, "🔴 Ketdi belgilandi")
                return

            if text == "⚠️ Uzrli":
                data[date].append({"user": username, "status": "Uzrli", "time": time})
                save_data(data)
                bot.send_message(user_id, "🟡 Uzrli belgilandi")
                return

            # ===== BUGUNGI STAT =====
            if text == "📊 Statistika":
                show_stat(user_id, date)
                return

            # ===== SANALAR =====
            if text == "📅 Sana bo‘yicha":
                dates = list(data.keys())
                if dates:
                    msg = "📅 Mavjud sanalar:\n\n" + "\n".join(dates)
                else:
                    msg = "📭 Ma’lumot yo‘q"
                bot.send_message(user_id, msg)
                return

            # AGAR USER SANA YOZSA
            if text in data:
                show_stat(user_id, text)
                return

def show_stat(user_id, date):
    data = load_data()

    if date not in data:
        bot.send_message(user_id, "📭 Ma’lumot yo‘q")
        return

    keldi, ketdi, uzrli = [], [], []

    for a in data[date]:
        line = f"{a['user']} | {a['time']}"
        if a["status"] == "Keldi":
            keldi.append(line)
        elif a["status"] == "Ketdi":
            ketdi.append(line)
        else:
            uzrli.append(line)

    msg = f"📊 *{date} DAVOMAT*\n\n"

    if keldi:
        msg += "🟢 *Keldi:*\n" + "\n".join(keldi) + "\n\n"
    if ketdi:
        msg += "🔴 *Ketdi:*\n" + "\n".join(ketdi) + "\n\n"
    if uzrli:
        msg += "🟡 *Uzrli:*\n" + "\n".join(uzrli)

    bot.send_message(user_id, msg, parse_mode="Markdown")

print("🚀 SYSTEM READY")
bot.infinity_polling()