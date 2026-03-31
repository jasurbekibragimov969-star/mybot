import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
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
    return "Bot ishlayapti"

def run():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run).start()

# ===== DATA =====
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

# ===== MENU =====
def main_menu():
    m = InlineKeyboardMarkup(row_width=2)
    m.add(
        InlineKeyboardButton("🏫 Maktab", callback_data="school"),
        InlineKeyboardButton("👨‍🏫 O‘qituvchilar", callback_data="teachers")
    )
    m.add(
        InlineKeyboardButton("📚 Sinflar", callback_data="classes"),
        InlineKeyboardButton("📰 Yangiliklar", callback_data="news")
    )
    m.add(
        InlineKeyboardButton("📩 Murojaat", callback_data="contact")
    )
    m.add(
        InlineKeyboardButton("👨‍💼 O‘qituvchi kabineti", callback_data="login")
    )
    return m

def teacher_panel():
    m = InlineKeyboardMarkup(row_width=2)
    m.add(
        InlineKeyboardButton("✅ Keldim", callback_data="keldi"),
        InlineKeyboardButton("❌ Ketdim", callback_data="ketdi")
    )
    m.add(
        InlineKeyboardButton("⚠️ Uzrli", callback_data="uzrli"),
        InlineKeyboardButton("📊 Statistika", callback_data="stat")
    )
    m.add(
        InlineKeyboardButton("📅 Sana bo‘yicha", callback_data="dates")
    )
    m.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="back")
    )
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(
        m.chat.id,
        "👋 Assalomu alaykum!\n\n"
        "🏫 *10-MAKTAB BOSHQARUV TIZIMI*\n\n"
        "✨ Zamonaviy platformaga xush kelibsiz\n\n"
        "👇 Quyidagilardan birini tanlang:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ===== TEXT LOGIN =====
@bot.message_handler(func=lambda m: m.chat.id in logged_users)
def login_process(m):
    user_id = m.chat.id
    step = logged_users[user_id]["step"]

    if step == "user":
        logged_users[user_id]["username"] = m.text
        logged_users[user_id]["step"] = "pass"
        bot.send_message(user_id, "🔒 Parol kiriting:")
        return

    if step == "pass":
        username = logged_users[user_id]["username"]
        if username in teachers_login and teachers_login[username] == m.text:
            logged_users[user_id] = {"step": "done", "username": username}
            bot.send_message(user_id, "✅ Xush kelibsiz", reply_markup=teacher_panel())
        else:
            bot.send_message(user_id, "❌ Login xato")
            logged_users.pop(user_id)
        return

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.message.chat.id
    data = call.data

    # ORQAGA
    if data == "back":
        logged_users.pop(user_id, None)
        bot.edit_message_text("🔙 Asosiy menyu", user_id, call.message.message_id, reply_markup=main_menu())
        return

    # LOGIN
    if data == "login":
        bot.send_message(user_id, "👤 Username kiriting:")
        logged_users[user_id] = {"step": "user"}
        return

    # ===== ODDIY MENU =====
    texts = {
        "school": "🏫 Maktab haqida ma'lumot",
        "teachers": "👨‍🏫 O‘qituvchilar ro‘yxati",
        "classes": "📚 Sinflar ro‘yxati",
        "news": "📰 Yangiliklar",
        "contact": "📩 Bog‘lanish uchun admin"
    }

    if data in texts:
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, texts[data])
        return

    # ===== KABINET =====
    if user_id in logged_users and logged_users[user_id]["step"] == "done":

        username = logged_users[user_id]["username"]

        now = datetime.utcnow() + timedelta(hours=5)
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M")

        db = load_data()
        if date not in db:
            db[date] = []

        if data == "keldi":
            db[date].append({"user": username, "status": "Keldi", "time": time})
            save_data(db)
            bot.answer_callback_query(call.id, "Keldi belgilandi")

        elif data == "ketdi":
            db[date].append({"user": username, "status": "Ketdi", "time": time})
            save_data(db)
            bot.answer_callback_query(call.id, "Ketdi belgilandi")

        elif data == "uzrli":
            db[date].append({"user": username, "status": "Uzrli", "time": time})
            save_data(db)
            bot.answer_callback_query(call.id, "Uzrli belgilandi")

        elif data == "stat":
            show_stat(user_id, date)

        elif data == "dates":
            dates = list(db.keys())
            if dates:
                msg = "📅 Sanalar:\n\n" + "\n".join(dates)
            else:
                msg = "📭 Ma’lumot yo‘q"
            bot.send_message(user_id, msg)

def show_stat(user_id, date):
    db = load_data()

    if date not in db:
        bot.send_message(user_id, "📭 Ma’lumot yo‘q")
        return

    keldi, ketdi, uzrli = [], [], []

    for a in db[date]:
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

print("🚀 BOT ISHLAYAPTI")
bot.infinity_polling()