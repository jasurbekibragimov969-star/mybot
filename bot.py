import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask
from datetime import datetime, timedelta
import json
import os
import hashlib

# CONFIG
TOKEN = "TOKENINGNI_QO'Y"
TZ_OFFSET = 5

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is running"

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()

sessions = {}

# ===================== DATA =====================

TEACHERS = {
    "dilara_abdullayeva": "Dilara Abdullayeva",
    "nigora_abdurahmonova": "Nigora Abdurahmonova",
    "gulxon_abduraxmonova": "Gulxon Abduraxmonova",
    "sharofiddin_ahmedov": "Sharofiddin Ahmedov",
    "nafisa_akkulova": "Nafisa Akkulova",
    "rano_aliyeva": "Ra'no Aliyeva",
    "feruza_alloberdiyeva": "Feruza Alloberdiyeva",
    "gulpari_asrayeva": "Gulpari Asrayeva",
    "orzugul_bekmuradova": "Orzugul Bekmuradova",
    "maftuna_egamberdiyeva": "Maftuna Egamberdiyeva",
    "nargiz_hakimova": "Nargiz Hakimova",
    "mavluda_ibragimjonova": "Mavluda Ibragimjonova",
    "olmasoy_karimova": "O‘lmasoy Karimova",
    "dilshoda_mamatqulova": "Dilshoda Mamatqulova",
    "zulfiya_mamedova": "Zulfiya Mamedova",
    "muhayyo_maxsudova": "Muhayyo Maxsudova",
    "izatulla_mirzakulov": "Izatulla Mirzakulov",
    "dilbarbibi_nishonova": "Dilbarbibi Nishonova",
    "gulandom_qurolova": "Gulandom Qurolova",
    "robiya_rayimova": "Robiya Rayimova",
    "nadira_rustamova": "Nadira Rustamova",
    "shoxsanam_subanova": "Shoxsanam Subanova",
    "lobar_sulaymanova": "Lobar Sulaymanova",
    "muslim_turgunbayev": "Muslim Turgunbayev",
    "gulnoza_xalmanova": "Gulnoza Xalmanova",
    "olmasoy_shabazova": "O‘lmasoy Shabazova"
}

CLASSES = [
    "1-A", "2-A", "3-A", "3-B", "4-A", "5-A",
    "6-A", "6-B", "7-A", "8-A", "9-A", "9-B",
    "10-A", "11-A"
]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_today():
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET)).strftime("%Y-%m-%d")

def get_time_now():
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET)).strftime("%H:%M")

# ===================== ATTENDANCE =====================

def load_attendance():
    if not os.path.exists("att.json"):
        return {}
    return json.load(open("att.json"))

def save_attendance(data):
    json.dump(data, open("att.json", "w"))

def record_attendance(username):
    db = load_attendance()
    today = get_today()
    db.setdefault(today, [])
    db[today].append({"user": username, "time": get_time_now()})
    save_attendance(db)

# ===================== KEYBOARDS =====================

def kb_main():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🏫 Maktabim", callback_data="school"),
        InlineKeyboardButton("📚 Sinflar", callback_data="classes"),
    )
    kb.add(
        InlineKeyboardButton("👨‍🏫 O'qituvchilar", callback_data="teachers"),
        InlineKeyboardButton("🔐 Kabinet", callback_data="login"),
    )
    kb.add(InlineKeyboardButton("📩 Murojaat", callback_data="contact"))
    return kb

def kb_teacher_panel():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Keldim", callback_data="att_keldi"))
    kb.add(InlineKeyboardButton("📊 Statistika", callback_data="att_stat"))
    kb.add(InlineKeyboardButton("← Chiqish", callback_data="logout"))
    return kb

def kb_back():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("← Orqaga", callback_data="back"))
    return kb

# ===================== START =====================

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, "🏫 10-MAKTAB BOSHQARUV TIZIMI", reply_markup=kb_main())

# ===================== CALLBACK =====================

@bot.callback_query_handler(func=lambda call: True)
def call_handler(call):
    uid = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    # BACK
    if data == "back":
        bot.send_message(uid, "🏫 Asosiy menyu", reply_markup=kb_main())
        return

    # SCHOOL
    if data == "school":
        text = "\n".join([
            "1-qator malumot",
            "2-qator malumot",
            "3-qator malumot",
            "4-qator malumot",
            "5-qator malumot",
            "6-qator malumot",
        ])
        bot.send_message(uid, text, reply_markup=kb_back())
        return

    # CLASSES
    if data == "classes":
        kb = InlineKeyboardMarkup(row_width=2)
        for c in CLASSES:
            kb.add(InlineKeyboardButton(c, callback_data=f"class_{c}"))
        kb.add(InlineKeyboardButton("← Orqaga", callback_data="back"))
        bot.send_message(uid, "📚 Sinflar", reply_markup=kb)
        return

    if data.startswith("class_"):
        sinf = data.split("_")[1]
        bot.send_message(uid, f"📚 {sinf}\n\nO'quvchi soni: ---\nSinf rahbari: ---", reply_markup=kb_back())
        return

    # TEACHERS
    if data == "teachers":
        kb = InlineKeyboardMarkup(row_width=1)
        for key, name in TEACHERS.items():
            kb.add(InlineKeyboardButton(name, callback_data=f"teacher_{key}"))
        kb.add(InlineKeyboardButton("← Orqaga", callback_data="back"))
        bot.send_message(uid, "👨‍🏫 O'qituvchilar", reply_markup=kb)
        return

    if data.startswith("teacher_"):
        key = data.split("_")[1]
        name = TEACHERS.get(key, "Noma'lum")
        bot.send_message(uid, f"{name}\nFan: ---\nToifa: ---\nAloqa: ---", reply_markup=kb_back())
        return

    # CONTACT
    if data == "contact":
        bot.send_message(uid, "📩 Murojaat uchun: @zkurtuve", reply_markup=kb_back())
        return

    # LOGIN
    if data == "login":
        sessions[uid] = {"step": "user"}
        bot.send_message(uid, "Username kiriting")
        return

    if data == "logout":
        sessions.pop(uid, None)
        bot.send_message(uid, "Chiqdingiz", reply_markup=kb_main())
        return

    # ATTENDANCE
    if data == "att_keldi":
        record_attendance(sessions[uid]["username"])
        bot.send_message(uid, "✅ Keldi belgilandi")

    if data == "att_stat":
        db = load_attendance()
        today = get_today()
        marked = {r["user"]: r for r in db.get(today, [])}

        text = f"📊 {today}\n\n"

        for user, name in TEACHERS.items():
            if user in marked:
                text += f"🟢 {name} — keldi\n"
            else:
                text += f"🔴 {name} — belgilanmadi\n"

        bot.send_message(uid, text)

# ===================== LOGIN =====================

@bot.message_handler(func=lambda m: True)
def login(m):
    uid = m.chat.id
    if uid not in sessions:
        return

    if sessions[uid]["step"] == "user":
        sessions[uid]["username"] = m.text
        sessions[uid]["step"] = "done"
        bot.send_message(uid, "Kabinetga kirdingiz", reply_markup=kb_teacher_panel())

print("BOT ISHLADI")
bot.infinity_polling()