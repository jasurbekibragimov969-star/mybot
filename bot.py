import telebot
import json
import re
import random
import threading
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup
from flask import Flask

# ===== TOKEN =====
TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
bot = telebot.TeleBot(TOKEN)

# ===== WEB SERVER (503 FIX) =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

# ===== DATA =====
DATA_FILE = "data.json"

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
    m.add("💧 Sog‘liq", "🩺 Kasalliklar")
    m.add("🔥 Motivatsiya")
    return m

def health_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("💧 Suv ichish", "🏃 Yugurish")
    m.add("🍎 Ovqatlanish", "😴 Uyqu")
    m.add("🔙 Orqaga")
    return m

def illness_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🤕 Bosh og‘riq", "🦷 Tish og‘riq")
    m.add("🤧 Shamollash", "🤒 Isitma")
    m.add("😖 Oshqozon og‘riq", "🦵 Oyoq og‘riq")
    m.add("🧍 Bel og‘riq", "🙆‍♂️ Bo‘yin og‘riq")
    m.add("😵 Bosh aylanish", "😫 Stress")
    m.add("😴 Uyqusizlik", "🤢 Ko‘ngil aynish")
    m.add("🔙 Orqaga")
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id,
    "👋 Assalomu alaykum!\n\n🤖 SUPER YORDAMCHI BOT",
    reply_markup=main_menu())

# ===== MAIN =====
@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text
    user_id = str(m.chat.id)

    data = load_data()
    if user_id not in data:
        data[user_id] = {"tasks": [], "money": []}

    # MENU
    if text == "💧 Sog‘liq":
        bot.send_message(m.chat.id, "💧 Sog‘liq", reply_markup=health_menu())
        return

    if text == "🩺 Kasalliklar":
        bot.send_message(m.chat.id, "🩺 Kasalliklar", reply_markup=illness_menu())
        return

    if text == "🔙 Orqaga":
        bot.send_message(m.chat.id, "🔙 Menu", reply_markup=main_menu())
        return

    # SOG‘LIQ
    if text == "💧 Suv ichish":
        bot.send_message(m.chat.id, "Kuniga 2-3 litr suv iching.")
        return

    if text == "🏃 Yugurish":
        bot.send_message(m.chat.id, "Haftasiga 3-4 marta yuguring.")
        return

 # ===== KASALLIKLAR FULL =====

if text == "🤕 Bosh og‘riq":
    bot.send_message(m.chat.id,
    "🤕 Bosh og‘rig‘i ko‘pincha charchoq va stressdan keladi. Dam olish muhim. "
    "Suv ichish yordam beradi. Iliq choy iching. "
    "Massaj ham foydali. Paracetamol ichish mumkin. "
    "Ko‘p telefon ishlatmang. Agar davom etsa shifokorga boring.")
    return

if text == "🦷 Tish og‘riq":
    bot.send_message(m.chat.id,
    "🦷 Tish og‘rig‘ida tuzli suv bilan og‘izni chayish foydali. "
    "Issiq-sovuq ovqatdan saqlaning. "
    "Og‘riq bo‘lsa ibuprofen ichish mumkin. "
    "Tish tozaligiga e’tibor bering. "
    "Qo‘l tekkizmang. "
    "Agar ketmasa stomatologga boring.")
    return

if text == "🤧 Shamollash":
    bot.send_message(m.chat.id,
    "🤧 Shamollashda issiq choy iching. Limon va asal foydali. "
    "Dam olish muhim. "
    "Burunni tozalang. "
    "Issiq kiyining. "
    "Dori ichish mumkin. "
    "Agar og‘irlashsa shifokorga boring.")
    return

if text == "🤒 Isitma":
    bot.send_message(m.chat.id,
    "🤒 Isitmada ko‘p suv ichish kerak. Dam oling. "
    "Issiq kiyimdan saqlaning. "
    "Paracetamol ichish mumkin. "
    "Vitaminlar iste’mol qiling. "
    "Haroratni kuzating. "
    "Uzoq davom etsa shifokorga boring.")
    return

if text == "😖 Oshqozon og‘riq":
    bot.send_message(m.chat.id,
    "😖 Oshqozon og‘rig‘ida yengil ovqat yeyish kerak. "
    "Gazli ichimliklardan saqlaning. "
    "Iliq choy iching. "
    "Ko‘p ovqat yemang. "
    "Dori ichish mumkin. "
    "Agar davom etsa shifokorga boring.")
    return

if text == "🦵 Oyoq og‘riq":
    bot.send_message(m.chat.id,
    "🦵 Oyoq og‘rig‘ida dam olish muhim. "
    "Iliq suvga soling. "
    "Massaj qiling. "
    "Qulay oyoq kiyim kiying. "
    "Dori ichish mumkin. "
    "Agar ketmasa shifokorga boring.")
    return

if text == "🧍 Bel og‘riq":
    bot.send_message(m.chat.id,
    "🧍 Bel og‘rig‘ida dam olish kerak. "
    "To‘g‘ri o‘tirish muhim. "
    "Massaj yordam beradi. "
    "Iliq kompress qo‘ying. "
    "Dori ichish mumkin. "
    "Agar ketmasa shifokorga boring.")
    return

if text == "🙆‍♂️ Bo‘yin og‘riq":
    bot.send_message(m.chat.id,
    "🙆‍♂️ Bo‘yin og‘rig‘ida telefonni kam ishlating. "
    "Massaj qiling. "
    "Iliq kompress qo‘ying. "
    "To‘g‘ri yostiq ishlating. "
    "Dori ichish mumkin. "
    "Agar ketmasa shifokorga boring.")
    return

if text == "😵 Bosh aylanish":
    bot.send_message(m.chat.id,
    "😵 Bosh aylanishda dam olish kerak. "
    "Suv iching. "
    "Sekin harakat qiling. "
    "Toza havo foydali. "
    "Kamqonlikni tekshiring. "
    "Agar davom etsa shifokorga boring.")
    return

if text == "😫 Stress":
    bot.send_message(m.chat.id,
    "😫 Stressda dam olish muhim. "
    "Sayr qiling. "
    "Sport bilan shug‘ullaning. "
    "Yaxshi uxlang. "
    "Telefonni kamaytiring. "
    "Agar kuchli bo‘lsa mutaxassisga murojaat qiling.")
    return

if text == "😴 Uyqusizlik":
    bot.send_message(m.chat.id,
    "😴 Uyqusizlikda telefonni kamaytiring. "
    "Har kuni bir vaqtda uxlang. "
    "Qahva ichmang kechqurun. "
    "Xonani qorong‘i qiling. "
    "Dam oling. "
    "Agar davom etsa shifokorga boring.")
    return

if text == "🤢 Ko‘ngil aynish":
    bot.send_message(m.chat.id,
    "🤢 Ko‘ngil aynishda yengil ovqat yeying. "
    "Suv iching. "
    "Dam oling. "
    "Yog‘li ovqat yemang. "
    "Zanjabil foydali. "
    "Agar davom etsa shifokorga boring.")
    return

    # XARAJAT
    if text == "💰 Xarajat":
        bot.send_message(m.chat.id, "Summani yozing")
        return

    if text.isdigit():
        data[user_id]["money"].append(int(text))
        save_data(data)
        bot.send_message(m.chat.id, "Qo‘shildi")
        return

    # STAT
    if text == "📊 Statistika":
        total = sum(data[user_id]["money"])
        bot.send_message(m.chat.id, f"Jami: {total}")
        return

    # VAZIFA
    if text == "📅 Vazifalar":
        bot.send_message(m.chat.id, "\n".join(data[user_id]["tasks"]) if data[user_id]["tasks"] else "Yo‘q")
        return

    if text == "➕ Qo‘shish":
        bot.send_message(m.chat.id, "Vazifa yozing")
        return

    if ":" in text:
        data[user_id]["tasks"].append(text)
        save_data(data)
        bot.send_message(m.chat.id, "Saqlandi")
        return

    # MOTIVATSIYA
    if text == "🔥 Motivatsiya":
        bot.send_message(m.chat.id, random.choice([
            "🔥 Harakat qil!",
            "💪 Taslim bo‘lma!",
            "🚀 Oldinga yur!"
        ]))
        return

    bot.send_message(m.chat.id, "🤖 Tugmalardan foydalaning!")

print("🚀 BOT ISHLAYAPTI")
bot.infinity_polling()
