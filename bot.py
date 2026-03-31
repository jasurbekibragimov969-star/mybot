import telebot
from telebot.types import ReplyKeyboardMarkup
import threading
from flask import Flask
from datetime import datetime, timedelta
import json

TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 6344661867

# ===== WEB =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running"

def run():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run).start()

# ===== DATA =====
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "teachers": {},
            "school": "Maktab haqida ma’lumot yo‘q",
            "classes": {},
            "attendance": {}
        }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

logged_users = {}

# ===== MENU =====
def main_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🏫 Maktab", "👨‍🏫 O‘qituvchilar")
    m.add("📚 Sinflar", "📩 Murojaat")
    m.add("👨‍💼 Kabinet")
    return m

def admin_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("➕ O‘qituvchi qo‘shish")
    m.add("🏫 Maktab ma’lumot")
    m.add("📚 Sinf qo‘shish")
    m.add("📊 Ko‘rish")
    m.add("🔙 Chiqish")
    return m

def teacher_panel():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("✅ Keldim", "❌ Ketdim")
    m.add("⚠️ Uzrli", "📊 Statistika")
    m.add("🔙 Chiqish")
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "👋 Xush kelibsiz", reply_markup=main_menu())

# ===== ADMIN =====
@bot.message_handler(commands=['admin'])
def admin(m):
    if m.chat.id == ADMIN_ID:
        bot.send_message(m.chat.id, "🔐 Admin panel", reply_markup=admin_menu())
    else:
        bot.send_message(m.chat.id, "❌ Ruxsat yo‘q")

# ===== MAIN =====
@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text
    user_id = m.chat.id
    data = load_data()

    # ADMIN PANEL
    if user_id == ADMIN_ID:

        if text == "➕ O‘qituvchi qo‘shish":
            bot.send_message(user_id, "username va parol yoz:\nmisol: ali_01 1234")
            logged_users[user_id] = {"step": "add_teacher"}
            return

        if text == "🏫 Maktab ma’lumot":
            bot.send_message(user_id, "Maktab haqida yoz:")
            logged_users[user_id] = {"step": "school"}
            return

        if text == "📚 Sinf qo‘shish":
            bot.send_message(user_id, "misol: 5A sinf haqida matn")
            logged_users[user_id] = {"step": "class"}
            return

        if text == "📊 Ko‘rish":
            bot.send_message(user_id, str(data))
            return

    # ADMIN INPUT
    if user_id in logged_users:

        step = logged_users[user_id]["step"]

        if step == "add_teacher":
            u, p = text.split()
            data["teachers"][u] = p
            save_data(data)
            bot.send_message(user_id, "✅ Qo‘shildi")
            logged_users.pop(user_id)
            return

        if step == "school":
            data["school"] = text
            save_data(data)
            bot.send_message(user_id, "✅ Saqlandi")
            logged_users.pop(user_id)
            return

        if step == "class":
            parts = text.split(" ", 1)
            data["classes"][parts[0]] = parts[1]
            save_data(data)
            bot.send_message(user_id, "✅ Saqlandi")
            logged_users.pop(user_id)
            return

    # USER
    if text == "🏫 Maktab":
        bot.send_message(user_id, data["school"])
        return

    if text == "👨‍🏫 O‘qituvchilar":
        if data["teachers"]:
            bot.send_message(user_id, "\n".join(data["teachers"].keys()))
        else:
            bot.send_message(user_id, "Yo‘q")
        return

    if text == "📚 Sinflar":
        if data["classes"]:
            bot.send_message(user_id, "\n".join(data["classes"].keys()))
        else:
            bot.send_message(user_id, "Yo‘q")
        return

    if text == "👨‍💼 Kabinet":
        bot.send_message(user_id, "Username:")
        logged_users[user_id] = {"step": "login_user"}
        return

    # LOGIN
    if user_id in logged_users:

        step = logged_users[user_id]["step"]

        if step == "login_user":
            logged_users[user_id]["username"] = text
            logged_users[user_id]["step"] = "login_pass"
            bot.send_message(user_id, "Parol:")
            return

        if step == "login_pass":
            username = logged_users[user_id]["username"]

            if username in data["teachers"] and data["teachers"][username] == text:
                logged_users[user_id] = {"step": "done", "username": username}
                bot.send_message(user_id, "Kirdingiz", reply_markup=teacher_panel())
            else:
                bot.send_message(user_id, "Xato")
                logged_users.pop(user_id)
            return

        if step == "done":
            username = logged_users[user_id]["username"]

            now = datetime.utcnow() + timedelta(hours=5)
            date = now.strftime("%Y-%m-%d")
            time = now.strftime("%H:%M")

            if date not in data["attendance"]:
                data["attendance"][date] = []

            if text == "✅ Keldim":
                data["attendance"][date].append({"user": username, "status": "Keldi", "time": time})
                save_data(data)
                bot.send_message(user_id, "OK")
                return

            if text == "📊 Statistika":
                bot.send_message(user_id, str(data["attendance"]))
                return

    bot.send_message(user_id, "🤖 Tugmalarni ishlating")

print("RUNNING")
bot.infinity_polling()