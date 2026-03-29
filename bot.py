import telebot
import json
import random
import threading
from telebot.types import ReplyKeyboardMarkup
from flask import Flask

# ===== TOKEN =====
TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
bot = telebot.TeleBot(TOKEN)

# ===== WEB SERVER =====
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

# ===== MENUS =====
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
    bot.send_message(
        m.chat.id,
        "👋 Assalomu alaykum!\n\n🤖 Aqlli yordamchi botga xush kelibsiz!",
        reply_markup=main_menu()
    )

# ===== MAIN HANDLER =====
@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text
    user_id = str(m.chat.id)

    data = load_data()
    if user_id not in data:
        data[user_id] = {"tasks": [], "money": []}

    # ===== MENU =====
    if text == "💧 Sog‘liq":
        bot.send_message(m.chat.id, "💧 Sog‘liq", reply_markup=health_menu())
        return

    if text == "🩺 Kasalliklar":
        bot.send_message(m.chat.id, "🩺 Kasalliklar", reply_markup=illness_menu())
        return

    if text == "🔙 Orqaga":
        bot.send_message(m.chat.id, "🔙 Menu", reply_markup=main_menu())
        return

    # ===== SOG‘LIQ =====
    if text == "💧 Suv ichish":
        bot.send_message(m.chat.id, "Kuniga 2-3 litr suv iching. Ertalab suv ichish foydali.")
        return

    if text == "🏃 Yugurish":
        bot.send_message(m.chat.id, "Haftasiga 3-4 marta yugurish sog‘liq uchun foydali.")
        return

    if text == "🍎 Ovqatlanish":
        bot.send_message(m.chat.id, "Ko‘proq sabzavot va foydali ovqat iste’mol qiling.")
        return

    if text == "😴 Uyqu":
        bot.send_message(m.chat.id, "Kuniga 7-8 soat uxlash sog‘liq uchun muhim.")
        return

    # ===== KASALLIKLAR =====
    if text == "🤕 Bosh og‘riq":
        bot.send_message(m.chat.id, "Dam oling, suv iching, massaj qiling va kerak bo‘lsa paracetamol iching.")
        return

    if text == "🦷 Tish og‘riq":
        bot.send_message(m.chat.id, "Tuzli suv bilan og‘izni chaying, issiq-sovuqdan saqlaning va dori iching.")
        return

    if text == "🤧 Shamollash":
        bot.send_message(m.chat.id, "Issiq choy iching, dam oling va issiq kiying.")
        return

    if text == "🤒 Isitma":
        bot.send_message(m.chat.id, "Ko‘p suv iching, dam oling va paracetamol ichish mumkin.")
        return

    if text == "😖 Oshqozon og‘riq":
        bot.send_message(m.chat.id, "Yengil ovqat yeying va gazli ichimliklardan saqlaning.")
        return

    if text == "🦵 Oyoq og‘riq":
        bot.send_message(m.chat.id, "Dam oling, massaj qiling va iliq suv yordam beradi.")
        return

    if text == "🧍 Bel og‘riq":
        bot.send_message(m.chat.id, "Dam oling va to‘g‘ri o‘tirishga e’tibor bering.")
        return

    if text == "🙆‍♂️ Bo‘yin og‘riq":
        bot.send_message(m.chat.id, "Telefonni kam ishlating va massaj qiling.")
        return

    if text == "😵 Bosh aylanish":
        bot.send_message(m.chat.id, "Dam oling va suv iching.")
        return

    if text == "😫 Stress":
        bot.send_message(m.chat.id, "Dam oling, sayr qiling va sport bilan shug‘ullaning.")
        return

    if text == "😴 Uyqusizlik":
        bot.send_message(m.chat.id, "Telefonni kamaytiring va bir vaqtda uxlashga odatlaning.")
        return

    if text == "🤢 Ko‘ngil aynish":
        bot.send_message(m.chat.id, "Yengil ovqat yeying va dam oling.")
        return

    # ===== XARAJAT =====
    if text == "💰 Xarajat":
        bot.send_message(m.chat.id, "Summani yozing:")
        return

    if text.isdigit():
        data[user_id]["money"].append(int(text))
        save_data(data)
        bot.send_message(m.chat.id, "Qo‘shildi")
        return

    # ===== STAT =====
    if text == "📊 Statistika":
        total = sum(data[user_id]["money"])
        bot.send_message(m.chat.id, f"Jami: {total}")
        return

    # ===== VAZIFA =====
    if text == "📅 Vazifalar":
        tasks = data[user_id]["tasks"]
        bot.send_message(m.chat.id, "\n".join(tasks) if tasks else "Yo‘q")
        return

    if text == "➕ Qo‘shish":
        bot.send_message(m.chat.id, "Vazifa yozing (masalan: yugurish 18:00)")
        return

    if ":" in text:
        data[user_id]["tasks"].append(text)
        save_data(data)
        bot.send_message(m.chat.id, "Saqlandi")
        return

    # ===== MOTIVATSIYA =====
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