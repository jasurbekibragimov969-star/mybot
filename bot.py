import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask
from datetime import datetime, timedelta
import json
import os
import hashlib
import time

# CONFIG
TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
ADMIN_ID = 6344661867
TZ_OFFSET = 5

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is running"

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()

sessions = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

DEFAULT_TEACHERS = {
    "dilara_abdullayeva": hash_password("dilara452"),
    "nigora_abdurahmonova": hash_password("nigora879"),
    "gulxon_abduraxmonova": hash_password("gulxon098"),
    "sharofiddin_ahmedov": hash_password("sharofiddin321"),
    "nafisa_akkulova": hash_password("nafisa654"),
    "rano_aliyeva": hash_password("rano111"),
    "feruza_alloberdiyeva": hash_password("feruza222"),
    "gulpari_asrayeva": hash_password("gulpari333"),
    "orzugul_bekmuradova": hash_password("orzugul444"),
    "maftuna_egamberdiyeva": hash_password("maftuna555"),
    "nargiz_hakimova": hash_password("nargiz666"),
    "mavluda_ibragimjonova": hash_password("mavluda777"),
    "olmasoy_karimova": hash_password("olmasoy888"),
    "dilshoda_mamatqulova": hash_password("dilshoda999"),
    "zulfiya_mamedova": hash_password("zulfiya147"),
    "muhayyo_maxsudova": hash_password("muhayyo258"),
    "izatulla_mirzakulov": hash_password("izatulla369"),
    "dilbarbibi_nishonova": hash_password("dilbarbibi159"),
    "gulandom_qurolova": hash_password("gulandom753"),
    "robiya_rayimova": hash_password("robiya852"),
    "nadira_rustamova": hash_password("nadira951"),
    "shoxsanam_subanova": hash_password("shoxsanam357"),
    "lobar_sulaymanova": hash_password("lobar258"),
    "muslim_turgunbayev": hash_password("muslim654"),
    "gulnoza_xalmanova": hash_password("gulnoza741"),
    "olmasoy_shabazova": hash_password("olmasoy852"),
    "jaxongir_isroilov": hash_password("jaxongir963"),
}

def load_teachers():
    return DEFAULT_TEACHERS

def load_attendance():
    if not os.path.exists("att.json"):
        return {}
    return json.load(open("att.json"))

def save_attendance(data):
    json.dump(data, open("att.json", "w"))

def get_today():
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET)).strftime("%Y-%m-%d")

def get_time_now():
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET)).strftime("%H:%M")

def record_attendance(username, status):
    db = load_attendance()
    today = get_today()
    db.setdefault(today, [])
    db[today].append({"user": username, "status": status, "time": get_time_now()})
    save_attendance(db)

def kb_main(uid):
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

def kb_teacher_panel():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Keldim", callback_data="att_keldi"),
        InlineKeyboardButton("📊 Bugungi holat", callback_data="att_stat"),
    )
    kb.add(InlineKeyboardButton("← Chiqish", callback_data="logout"))
    return kb

def send_main(uid):
    bot.send_message(uid, "🏫 10-MAKTAB BOSHQARUV TIZIMI", reply_markup=kb_main(uid))

@bot.message_handler(commands=["start"])
def start(m):
    sessions.pop(m.chat.id, None)
    send_main(m.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def call_handler(call):
    uid = call.message.chat.id
    data = call.data

    bot.answer_callback_query(call.id)

    # 🔐 LOGIN
    if data == "login":
        sessions[uid] = {"step": "user"}
        bot.send_message(uid, "Username kiriting")
        return

    if data == "logout":
        sessions.pop(uid, None)
        send_main(uid)
        return

    # 🏫 MAKTAB
    if data == "school":
        bot.send_message(uid, "🏫 10-maktab haqida ma'lumot...")
        return

    # 👨‍🏫 O‘QITUVCHILAR
    if data == "teachers":
        teachers = load_teachers()
        text = "👨‍🏫 O'qituvchilar:\n\n"
        for t in teachers:
            text += f"• {t}\n"
        bot.send_message(uid, text)
        return

    # 📚 SINFLAR
    if data == "classes":
        bot.send_message(uid, "📚 Sinflar: 1-A, 5-B, 11-A")
        return

    # 📰 YANGILIK
    if data == "news":
        bot.send_message(uid, "📰 Hozircha yangilik yo'q")
        return

    # 📩 MUROJAAT
    if data == "contact":
        bot.send_message(uid, "📩 Admin bilan bog‘lanish: @username")
        return

    # ✅ KELDI
    if data == "att_keldi":
        record_attendance(sessions[uid]["username"], "Keldi")
        bot.send_message(uid, "✅ Keldi belgilandi")

    # 📊 STAT
    if data == "att_stat":
        db = load_attendance()
        today = get_today()
        teachers = load_teachers()

        msg = f"📊 {today}\n\n"
        marked = {r["user"]: r for r in db.get(today, [])}

        for t in teachers:
            if t in marked:
                msg += f"🟢 {t} — {marked[t]['status']}\n"
            else:
                msg += f"🔴 {t} — belgilanmadi\n"

        bot.send_message(uid, msg)

@bot.message_handler(func=lambda m: True)
def login(m):
    uid = m.chat.id
    if uid not in sessions:
        return

    if sessions[uid]["step"] == "user":
        sessions[uid]["username"] = m.text
        sessions[uid]["step"] = "pass"
        bot.send_message(uid, "Parol kiriting")

    elif sessions[uid]["step"] == "pass":
        teachers = load_teachers()
        user = sessions[uid]["username"]
        if teachers.get(user) == hash_password(m.text):
            sessions[uid]["step"] = "done"
            bot.send_message(uid, "Kabinetga xush kelibsiz", reply_markup=kb_teacher_panel())
        else:
            bot.send_message(uid, "Xato parol")

print("BOT ISHLADI")
bot.infinity_polling()
