import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask
from datetime import datetime, timedelta
import json
import os
import hashlib

TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
DATA_FILE = "attendance.json"
TZ_OFFSET = 5

TEACHERS = {
    "feruza_01": hashlib.sha256("feruza1234".encode()).hexdigest(),
    "feruza_02": hashlib.sha256("feruza1234".encode()).hexdigest(),
}

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot ishlayapti"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask, daemon=True).start()

sessions = {}

# ===== DATA =====
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_now():
    return datetime.utcnow() + timedelta(hours=TZ_OFFSET)

def get_today():
    return get_now().strftime("%Y-%m-%d")

def get_time():
    return get_now().strftime("%H:%M")

def record_attendance(username, status):
    db = load_data()
    today = get_today()
    if today not in db:
        db[today] = []
    db[today].append({
        "user": username,
        "status": status,
        "time": get_time()
    })
    save_data(db)

# ===== KEYBOARDS =====
def kb_main():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🏫 Maktab haqida", callback_data="school"),
        InlineKeyboardButton("👨‍🏫 O'qituvchilar", callback_data="teachers"),
    )
    kb.add(
        InlineKeyboardButton("📚 Sinflar", callback_data="classes"),
        InlineKeyboardButton("📰 Yangiliklar", callback_data="news"),
    )
    kb.add(InlineKeyboardButton("📩 Murojaat", callback_data="contact"))
    kb.add(InlineKeyboardButton("🔐 O'qituvchi kabineti", callback_data="login"))
    return kb

def kb_teacher():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Keldim", callback_data="keldi"),
        InlineKeyboardButton("🚪 Ketdim", callback_data="ketdi"),
    )
    kb.add(
        InlineKeyboardButton("📋 Uzrli sabab", callback_data="uzrli"),
        InlineKeyboardButton("📊 Statistika", callback_data="stat"),
    )
    kb.add(InlineKeyboardButton("🗓 Sanalar", callback_data="dates"))
    kb.add(InlineKeyboardButton("← Chiqish", callback_data="logout"))
    return kb

def kb_back():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("← Orqaga", callback_data="back"))
    return kb

# ===== TEXT =====
MSG_WELCOME = (
    "👋 Assalomu alaykum!\n\n"
    "🏫 10-MAKTAB BOSHQARUV TIZIMI\n\n"
    "Quyidagilardan birini tanlang:"
)

INFO_TEXTS = {
    "school": "🏫 Maktab haqida ma'lumot",
    "teachers": "👨‍🏫 O'qituvchilar ro'yxati",
    "classes": "📚 Sinflar",
    "news": "📰 Yangiliklar",
    "contact": "📩 Admin bilan bog'laning"
}

# ===== UTILS =====
def is_logged_in(user_id):
    return sessions.get(user_id, {}).get("step") == "done"

def get_username(user_id):
    return sessions.get(user_id, {}).get("username", "")

def send_main(chat_id):
    bot.send_message(chat_id, MSG_WELCOME, reply_markup=kb_main())

def send_panel(chat_id):
    username = get_username(chat_id)
    now = get_now()
    text = f"🟢 Kabinet: {username}\n📅 {now.strftime('%d.%m.%Y')} | 🕐 {now.strftime('%H:%M')}"
    bot.send_message(chat_id, text, reply_markup=kb_teacher())

# ===== START =====
@bot.message_handler(commands=["start"])
def start(m):
    sessions.pop(m.chat.id, None)
    send_main(m.chat.id)

# ===== LOGIN (FIXED) =====
@bot.message_handler(func=lambda m: True)
def login_handler(m):
    user_id = m.chat.id
    session = sessions.get(user_id)

    # ❗ faqat login jarayonida ishlaydi
    if not session:
        return

    if session.get("step") == "done":
        return

    if session["step"] == "user":
        if m.text not in TEACHERS:
            bot.send_message(user_id, "❌ User topilmadi")
            return
        sessions[user_id]["temp"] = m.text
        sessions[user_id]["step"] = "pass"
        bot.send_message(user_id, "🔒 Parol kiriting")

    elif session["step"] == "pass":
        username = session.get("temp")
        hashed = hashlib.sha256(m.text.encode()).hexdigest()

        if TEACHERS.get(username) == hashed:
            sessions[user_id] = {"step": "done", "username": username}
            send_panel(user_id)
        else:
            sessions.pop(user_id)
            bot.send_message(user_id, "❌ Login xato")

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: True)
def call_handler(call):
    user_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    if data == "back":
        sessions.pop(user_id, None)
        send_main(user_id)
        return

    if data == "logout":
        sessions.pop(user_id, None)
        send_main(user_id)
        return

    if data == "login":
        sessions[user_id] = {"step": "user"}
        bot.send_message(user_id, "👤 Username kiriting")
        return

    if data in INFO_TEXTS:
        bot.send_message(user_id, INFO_TEXTS[data], reply_markup=kb_back())
        return

    if not is_logged_in(user_id):
        bot.send_message(user_id, "❗ Avval login qiling", reply_markup=kb_main())
        return

    username = get_username(user_id)

    if data == "keldi":
        record_attendance(username, "Keldi")
        bot.send_message(user_id, "🟢 Keldi belgilandi")

    elif data == "ketdi":
        record_attendance(username, "Ketdi")
        bot.send_message(user_id, "🔴 Ketdi belgilandi")

    elif data == "uzrli":
        record_attendance(username, "Uzrli")
        bot.send_message(user_id, "🟡 Uzrli belgilandi")

    elif data == "stat":
        db = load_data()
        today = get_today()

        if today not in db:
            bot.send_message(user_id, "📭 Bugun ma'lumot yo'q")
            return

        msg = f"📊 {today} DAVOMAT\n\n"
        for r in db[today]:
            msg += f"{r['user']} | {r['status']} | {r['time']}\n"

        bot.send_message(user_id, msg)

    elif data == "dates":
        db = load_data()
        if not db:
            bot.send_message(user_id, "📭 Ma'lumot yo'q")
            return

        msg = "📅 Sanalar:\n\n"
        for d in db:
            msg += d + "\n"

        bot.send_message(user_id, msg)

print("🚀 BOT ISHLAYAPTI")
bot.infinity_polling()