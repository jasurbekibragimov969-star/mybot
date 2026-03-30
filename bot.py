import telebot
from telebot.types import ReplyKeyboardMarkup
import threading
from flask import Flask

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

# ===== MENU =====
def main_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🏫 Mening maktabim")
    m.add("👨‍🏫 O‘qituvchilar", "📚 Sinflar")
    m.add("📰 Yangiliklar", "📩 Murojaat")
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

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(
        m.chat.id,
        "👋 Assalomu alaykum!\n\n"
        "🏫 *10-maktab rasmiy online tizimiga xush kelibsiz!*\n\n"
        "📌 Bu bot orqali siz:\n"
        "• Maktab haqida ma’lumot olishingiz\n"
        "• O‘qituvchilar bilan tanishishingiz\n"
        "• Sinflar haqida bilishingiz\n"
        "• Yangiliklarni kuzatishingiz\n"
        "• Murojaat yuborishingiz mumkin\n\n"
        "👇 Kerakli bo‘limni tanlang:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ===== MAIN =====
@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text

    # BACK
    if text == "🔙 Orqaga":
        bot.send_message(m.chat.id, "🔙 Asosiy menyu", reply_markup=main_menu())
        return

    # MAKTAB
    if text == "🏫 Mening maktabim":
        bot.send_message(m.chat.id,
        "🏫 Maktab haqida ma’lumot (keyin to‘ldiriladi)")
        return

    # TEACHERS
    if text == "👨‍🏫 O‘qituvchilar":
        bot.send_message(m.chat.id,
        "👨‍🏫 O‘qituvchilar ro‘yxati",
        reply_markup=teachers_menu())
        return

    if "O‘qituvchi" in text:
        bot.send_message(m.chat.id,
        "👨‍🏫 O‘qituvchi haqida ma’lumot:\n\n"
        "Ism: ---\n"
        "Fan: ---\n"
        "Toifa: ---\n"
        "Qisqacha: ---")
        return

    # CLASSES
    if text == "📚 Sinflar":
        bot.send_message(m.chat.id,
        "📚 Sinflar ro‘yxati",
        reply_markup=class_menu())
        return

    if "sinf" in text:
        bot.send_message(m.chat.id,
        "📚 Sinf haqida ma’lumot (keyin to‘ldiriladi)")
        return

    # NEWS
    if text == "📰 Yangiliklar":
        bot.send_message(m.chat.id,
        "📰 Tadbirlar va yangiliklar (keyin qo‘shiladi)")
        return

    # MUROJAAT
    if text == "📩 Murojaat":
        bot.send_message(m.chat.id,
        "📩 Hurmatli foydalanuvchi!\n\n"
        "Siz bu yer orqali maktabga taklif, savol yoki muammo yuborishingiz mumkin.\n"
        "Agar muammo yoki noqulay holat bo‘lsa ham yozishingiz mumkin.\n\n"
        "✍️ Marhamat, murojaatingizni yozing:")
        return

    # SEND TO ADMIN
    bot.send_message(6344661867,
    f"📩 Yangi murojaat:\n\n{text}")

    bot.send_message(m.chat.id,
    "✅ Murojaatingiz yuborildi!")
    
print("🚀 SCHOOL BOT ISHLAYAPTI")
bot.infinity_polling()