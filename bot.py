import telebot
import json
import re
import random
from flask import Flask, request
from datetime import datetime
import threading
import time
from telebot.types import ReplyKeyboardMarkup

TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
ADMIN_ID = 6344661867

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
def main_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📅 Vazifalar", "➕ Qo‘shish")
    m.add("💰 Xarajat", "📊 Statistika")
    m.add("💧 Sog‘liq", "🔥 Motivatsiya")
    m.add("📞 Admin")
    return m

def health_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("💧 Suv ichish", "🏃 Yugurish")
    m.add("🍎 Ovqatlanish", "😴 Uyqu")
    m.add("🩺 Kasalliklar")
    m.add("🔙 Orqaga")
    return m

def illness_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🤕 Bosh og‘riq", "🤧 Shamollash")
    m.add("🤒 Isitma", "😖 Oshqozon")
    m.add("😵 Bosh aylanish", "😫 Stress")
    m.add("😴 Uyqusizlik", "🤢 Ko‘ngil aynish")
    m.add("🔙 Orqaga")
    return m

# ===== MOTIVATION =====
motivations = [
"🔥 Bugun boshlamasang, ertaga ham boshlamaysan!",
"💪 Harakat qil — natija keladi!",
"🚀 Kichik qadamlar katta natija beradi!",
"😎 Sen uddalaysan!",
"🏆 O‘zingni yeng!",
"🔥 Intizom = muvaffaqiyat",
"💯 Bugun ishlasang ertaga dam olasan",
"⚡ Harakatda baraka bor",
"🔥 Orzular harakatni talab qiladi",
"💪 Taslim bo‘lma!",
"🚀 Har kun yangi imkoniyat",
"😎 Sen kuchlisan!",
"🏆 Maqsad sari bor!",
"🔥 Bugun zo‘r kun!",
"💯 O‘zingga ishoning",
"⚡ Harakat qil!",
"🔥 Yengil yo‘l yo‘q",
"💪 Ishla va natijani ko‘r",
"🚀 Boshlash — eng muhim qadam",
"😎 Sen uddalaysan!"
]

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id,
    "👋 Assalomu alaykum!\n\n🤖 SUPER YORDAMCHI BOT\n\n👇 Men sizga hamma narsada yordam beraman!",
    reply_markup=main_menu())

# ===== MAIN =====
@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text
    user_id = str(m.chat.id)

    data = load_data()
    if user_id not in data:
        data[user_id] = {"tasks": [], "money": []}

    # ===== MENU =====
    if text == "💧 Sog‘liq":
        bot.send_message(m.chat.id, "💧 Sog‘liq bo‘limi", reply_markup=health_menu())
        return

    if text == "🩺 Kasalliklar":
        bot.send_message(m.chat.id, "🩺 Kasalliklar", reply_markup=illness_menu())
        return

    if text == "🔙 Orqaga":
        bot.send_message(m.chat.id, "🔙 Asosiy menu", reply_markup=main_menu())
        return

    # ===== HEALTH INFO =====
    if text == "💧 Suv ichish":
        bot.send_message(m.chat.id,
        "💧 Kuniga 2-3 litr suv iching.\n\n"
        "• Ertalab 1 stakan\n"
        "• Ovqatdan oldin\n"
        "• Kun davomida bo‘lib iching\n\n"
        "❌ Juda ko‘p birdan ichmang!")
        return

    if text == "🏃 Yugurish":
        bot.send_message(m.chat.id,
        "🏃 Yugurish:\n\n"
        "• Haftasiga 3-4 marta\n"
        "• 15-30 minut\n"
        "• Sekin boshlang\n"
        "• Nafasni tekis oling\n\n"
        "🔥 Juda foydali!")
        return

    if text == "🍎 Ovqatlanish":
        bot.send_message(m.chat.id,
        "🍎 To‘g‘ri ovqat:\n\n"
        "• Ko‘proq sabzavot\n"
        "• Kam shakar\n"
        "• Fast food kamroq\n\n"
        "💪 Sog‘lom hayot!")
        return

    if text == "😴 Uyqu":
        bot.send_message(m.chat.id,
        "😴 Uyqu:\n\n"
        "• 7-8 soat\n"
        "• Bir vaqtda uxlang\n"
        "• Telefon kamroq ishlating")
        return

    # ===== ILLNESS =====
    if text == "🤕 Bosh og‘riq":
        bot.send_message(m.chat.id,
        "🤕 Bosh og‘riq:\n\nDam oling, suv iching\nParacetamol mumkin")
        return

    if text == "🤧 Shamollash":
        bot.send_message(m.chat.id,
        "🤧 Shamollash:\n\nIssiq choy, asal, limon\nDam oling")
        return

    if text == "🤒 Isitma":
        bot.send_message(m.chat.id,
        "🤒 Isitma:\n\nKo‘p suv iching\nParacetamol")
        return

    if text == "😖 Oshqozon":
        bot.send_message(m.chat.id,
        "😖 Oshqozon:\n\nYengil ovqat\nGazli ichimlik yo‘q")
        return

    if text == "😵 Bosh aylanish":
        bot.send_message(m.chat.id,
        "😵 Dam oling, suv iching")
        return

    if text == "😫 Stress":
        bot.send_message(m.chat.id,
        "😫 Dam oling, sayr qiling")
        return

    if text == "😴 Uyqusizlik":
        bot.send_message(m.chat.id,
        "😴 Telefonni kam ishlating, dam oling")
        return

    if text == "🤢 Ko‘ngil aynish":
        bot.send_message(m.chat.id,
        "🤢 Yengil ovqat, dam oling")
        return

    # ===== MOTIVATION =====
    if text == "🔥 Motivatsiya":
        bot.send_message(m.chat.id, random.choice(motivations))
        return

    # ===== ADMIN =====
    if text == "📞 Admin":
        bot.send_message(m.chat.id, "Admin: @zkurtuve")
        return

    bot.send_message(m.chat.id, "🤖 Tugmalardan foydalaning!")

print("🚀 SUPER BOT ISHLAYAPTI")
bot.infinity_polling()
