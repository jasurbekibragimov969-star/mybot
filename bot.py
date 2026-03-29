import telebot
import json
import threading
import time
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup

TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"

bot = telebot.TeleBot(TOKEN)
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
def menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📅 Bugungi ishlar", "📆 Ertangi ishlar")
    markup.add("📋 Hammasi", "💸 Xarajatlar")
    markup.add("🗑 Tozalash")
    return markup

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Assalomu alaykum!\n\n"
        "🤖 Men *Jasurbek tomonidan yaratilgan aqlli yordamchi botman*\n\n"
        "💡 Nimalar qila olaman:\n"
        "• 📝 Ishlaringni eslab qolaman\n"
        "• ⏰ Vaqt bilan eslataman\n"
        "• 💸 Xarajatlaringni hisoblayman\n"
        "• 📊 Statistikani ko‘rsataman\n\n"
        "👇 Boshlash uchun yoz!",
        parse_mode="Markdown",
        reply_markup=menu()
    )

# ===== REMINDER =====
def reminder_loop():
    while True:
        data = load_data()
        now = datetime.now().strftime("%H:%M")

        for user_id in data:
            for date in data[user_id]:
                for task in data[user_id][date]:
                    if now in task:
                        bot.send_message(user_id, f"⏰ Eslatma:\n👉 {task}")

        time.sleep(60)

threading.Thread(target=reminder_loop).start()

# ===== MAIN =====
@bot.message_handler(func=lambda message: True)
def handle(message):
    text = message.text.lower()
    user_id = str(message.chat.id)
    data = load_data()

    if user_id not in data:
        data[user_id] = {"tasks": {}, "money": []}

    # BUTTONS
    if text == "📅 bugungi ishlar":
        show_tasks(message, 0)
        return

    if text == "📆 ertangi ishlar":
        show_tasks(message, 1)
        return

    if text == "📋 hammasi":
        show_all(message)
        return

    if text == "💸 xarajatlar":
        show_money(message)
        return

    if text == "🗑 tozalash":
        data[user_id] = {"tasks": {}, "money": []}
        save_data(data)
        bot.send_message(message.chat.id, "🧹 Tozalandi")
        return

    # 💸 MONEY
    if any(char.isdigit() for char in text):
        parts = text.split()
        if parts[0].isdigit():
            amount = int(parts[0])
            data[user_id]["money"].append(amount)
            save_data(data)
            bot.send_message(message.chat.id, f"💸 Qo‘shildi: {amount} so‘m")
            return

    # DATE
    if "ertaga" in text:
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        date = datetime.now().strftime("%Y-%m-%d")

    if date not in data[user_id]["tasks"]:
        data[user_id]["tasks"][date] = []

    data[user_id]["tasks"][date].append(message.text)
    save_data(data)

    bot.send_message(message.chat.id, f"✅ Saqlandi:\n👉 {message.text}")

# ===== SHOW =====
def show_tasks(message, days):
    data = load_data()
    user_id = str(message.chat.id)
    date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    tasks = data[user_id]["tasks"]

    if date in tasks:
        text = "\n".join([f"• {t}" for t in tasks[date]])
        bot.send_message(message.chat.id, f"📅 {date}:\n\n{text}")
    else:
        bot.send_message(message.chat.id, "📭 Hech narsa yo‘q")

def show_all(message):
    data = load_data()
    user_id = str(message.chat.id)

    tasks = data[user_id]["tasks"]

    if tasks:
        text = "📋 Barcha ishlar:\n\n"
        for date, t in tasks.items():
            text += f"📅 {date}:\n"
            for i in t:
                text += f"   • {i}\n"
            text += "\n"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "📭 Hech narsa yo‘q")

def show_money(message):
    data = load_data()
    user_id = str(message.chat.id)

    money = data[user_id]["money"]

    if money:
        total = sum(money)
        bot.send_message(message.chat.id, f"💸 Jami xarajat:\n{total} so‘m")
    else:
        bot.send_message(message.chat.id, "📭 Xarajat yo‘q")

print("🚀 JASURBEK SUPER BOT ISHLAYAPTI...")
bot.polling()