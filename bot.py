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

    # KASALLIK
    if text == "🤕 Bosh og‘riq":
        bot.send_message(m.chat.id, "Dam oling, suv iching, paracetamol mumkin.")
        return

    if text == "🦷 Tish og‘riq":
        bot.send_message(m.chat.id, "Tuzli suv bilan chaying, dori ichish mumkin.")
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