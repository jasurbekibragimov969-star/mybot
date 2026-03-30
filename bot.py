import telebot
from telebot.types import ReplyKeyboardMarkup
import threading
from flask import Flask
from datetime import datetime, timedelta

TOKEN = "SENING_TOKENING"
bot = telebot.TeleBot(TOKEN)

# ===== WEB =====
app = Flask(__name__)

@app.route('/')
def home():
    return "School Bot Running"

def run():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run).start()

# ===== DATA =====
teachers_login = {
    "feruza_01": "feruza1234",
    "feruza_02": "feruza1234"
}

logged_users = {}
attendance = []

ADMIN_ID = 6344661867

# ===== MENU =====
def main_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🏫 Mening maktabim")
    m.add("👨‍🏫 O‘qituvchilar", "📚 Sinflar")
    m.add("📰 Yangiliklar", "📩 Murojaat")
    m.add("👨‍💼 O‘qituvchi kabineti")
    return m

def teachers_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(1, 28):
        m.add(f"👨‍🏫 O‘qituvchi {i}")
    m.add("🔙 Orqaga")
    return m

def class_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(1, 12):
        m.add(f"📚 {i}-sinf")
    m.add("🔙 Orqaga")
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
    bot.send_message(
        m.chat.id,
        "👋 Assalomu alaykum!\n\n"
        "🏫 *10-maktab online tizimiga xush kelibsiz!*\n\n"
        "👇 Kerakli bo‘limni tanlang:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ===== MAIN =====
@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text
    user_id = m.chat.id

    # 🔙 ORQAGA
    if text == "🔙 Orqaga":
        bot.send_message(user_id, "🔙 Asosiy menyu", reply_markup=main_menu())
        return

    # 🔙 CHIQISH
    if text == "🔙 Chiqish":
        if user_id in logged_users:
            logged_users.pop(user_id)
        bot.send_message(user_id, "🔙 Chiqdingiz", reply_markup=main_menu())
        return

    # ===== MAKTAB =====
    if text == "🏫 Mening maktabim":
        bot.send_message(user_id, "🏫 Maktab haqida ma’lumot (keyin qo‘shiladi)")
        return

    # ===== O‘QITUVCHILAR =====
    if text == "👨‍🏫 O‘qituvchilar":
        bot.send_message(user_id, "👨‍🏫 O‘qituvchilar ro‘yxati", reply_markup=teachers_menu())
        return

    if text.startswith("👨‍🏫 O‘qituvchi"):
        bot.send_message(user_id,
        "👨‍🏫 O‘qituvchi haqida ma’lumot:\n\nIsm: ---\nFan: ---\nToifa: ---")
        return

    # ===== SINFLAR =====
    if text == "📚 Sinflar":
        bot.send_message(user_id, "📚 Sinflar", reply_markup=class_menu())
        return

    if "sinf" in text:
        bot.send_message(user_id, "📚 Sinf haqida ma’lumot")
        return

    # ===== YANGILIK =====
    if text == "📰 Yangiliklar":
        bot.send_message(user_id, "📰 Yangiliklar keyin qo‘shiladi")
        return

    # ===== MUROJAAT =====
    if text == "📩 Murojaat":
        bot.send_message(user_id, "📩 Yozing:")
        logged_users[user_id] = {"step": "feedback"}
        return

    if user_id in logged_users and logged_users[user_id].get("step") == "feedback":
        bot.send_message(ADMIN_ID, f"📩 Yangi murojaat:\n\n{text}")
        bot.send_message(user_id, "✅ Yuborildi")
        logged_users.pop(user_id)
        return

    # ===== O‘QITUVCHI KABINETI =====
    if text == "👨‍💼 O‘qituvchi kabineti":
        bot.send_message(user_id, "👤 Username kiriting:")
        logged_users[user_id] = {"step": "login_user"}
        return

    if user_id in logged_users:

        step = logged_users[user_id].get("step")

        # USERNAME
        if step == "login_user":
            logged_users[user_id]["username"] = text
            logged_users[user_id]["step"] = "login_pass"
            bot.send_message(user_id, "🔒 Parol kiriting:")
            return

        # PASSWORD
        if step == "login_pass":
            username = logged_users[user_id]["username"]

            if username in teachers_login and teachers_login[username] == text:
                logged_users[user_id] = {"step": "done", "username": username}
                bot.send_message(user_id, f"✅ Xush kelibsiz {username}", reply_markup=teacher_panel())
            else:
                bot.send_message(user_id, "❌ Login xato")
                logged_users.pop(user_id)
            return

        # ===== KABINET =====
        if step == "done":
            username = logged_users[user_id]["username"]

            # 🇺🇿 O‘zbekiston vaqti
            now = (datetime.utcnow() + timedelta(hours=5)).strftime("%d-%m %H:%M")

            if text == "✅ Keldim":
                attendance.append({"user": username, "status": "Keldi", "time": now})
                bot.send_message(user_id, "🟢 Belgilandi")
                return

            if text == "❌ Ketdim":
                attendance.append({"user": username, "status": "Ketdi", "time": now})
                bot.send_message(user_id, "🔴 Belgilandi")
                return

            if text == "⚠️ Uzrli":
                attendance.append({"user": username, "status": "Uzrli", "time": now})
                bot.send_message(user_id, "🟡 Belgilandi")
                return

            if text == "📊 Statistika":
                if attendance:

                    keldi = []
                    ketdi = []
                    uzrli = []

                    for a in attendance:
                        line = f"{a['user']} | {a['time']}"
                        if a["status"] == "Keldi":
                            keldi.append(line)
                        elif a["status"] == "Ketdi":
                            ketdi.append(line)
                        elif a["status"] == "Uzrli":
                            uzrli.append(line)

                    msg = "📊 *BUGUNGI DAVOMAT*\n\n"

                    if keldi:
                        msg += "🟢 *Keldi:*\n" + "\n".join(keldi) + "\n\n"
                    if ketdi:
                        msg += "🔴 *Ketdi:*\n" + "\n".join(ketdi) + "\n\n"
                    if uzrli:
                        msg += "🟡 *Uzrli:*\n" + "\n".join(uzrli)

                    bot.send_message(user_id, msg, parse_mode="Markdown")

                else:
                    bot.send_message(user_id, "📭 Hali ma’lumot yo‘q")

                return

    # DEFAULT
    bot.send_message(user_id, "🤖 Tugmalardan foydalaning!")

print("🚀 SCHOOL BOT ISHLAYAPTI")
bot.infinity_polling()