import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask
from datetime import datetime, timedelta
import json
import os
import hashlib

# CONFIG
TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
ADMIN_ID = 6344661867
TZ_OFFSET = 5

TEACHERS_FILE = "teachers.json"
ATTENDANCE_FILE = "attendance.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot ishlayapti"

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()

sessions = {}

# ===== UTILS =====
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(filepath, default):
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ===== TEACHERS =====
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
    data = load_json(TEACHERS_FILE, None)
    if data is None:
        save_json(TEACHERS_FILE, DEFAULT_TEACHERS)
        return DEFAULT_TEACHERS
    return data

# ===== ATTENDANCE =====
def load_attendance():
    return load_json(ATTENDANCE_FILE, {})

def save_attendance(data):
    save_json(ATTENDANCE_FILE, data)

def get_now():
    return datetime.utcnow() + timedelta(hours=TZ_OFFSET)

def get_today():
    return get_now().strftime("%Y-%m-%d")

def record_attendance(username, status):
    db = load_attendance()
    today = get_today()
    db.setdefault(today, [])
    db[today].append({
        "user": username,
        "status": status
    })
    save_attendance(db)

# ===== KEYBOARD =====
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
        InlineKeyboardButton("🚪 Ketdim", callback_data="att_ketdi"),
    )
    kb.add(
        InlineKeyboardButton("📋 Uzrli sabab", callback_data="att_uzrli"),
        InlineKeyboardButton("📊 Bugungi holat", callback_data="att_stat"),
        InlineKeyboardButton("📜 Tarix", callback_data="att_history"),
    )
    kb.add(InlineKeyboardButton("← Chiqish", callback_data="logout"))
    return kb

def send_main(uid):
    bot.send_message(uid, "🏫 10-MAKTAB BOSHQARUV TIZIMI", reply_markup=kb_main(uid))

# ===== START =====
@bot.message_handler(commands=["start"])
def start(m):
    sessions.pop(m.chat.id, None)
    send_main(m.chat.id)

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: True)
def call_handler(call):	
    uid = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    # PUBLIC BO'LIMLAR
    if data == "school":
        bot.send_message(uid, "🏫 Maktab haqida ma'lumot...")
        return

    if data == "teachers":
        teachers = load_teachers()
        msg = "👨‍🏫 O'qituvchilar:\n\n"
        for t in teachers:
            msg += f"• {t}\n"
        bot.send_message(uid, msg)
        return

    if data == "classes":
        bot.send_message(uid, "📚 Sinflar bo'limi")
        return

    if data == "news":
        bot.send_message(uid, "📰 Yangiliklar")
        return

    if data == "contact":
        bot.send_message(uid, "📩 Admin bilan bog'laning @zkurtuve")
        return

    # LOGIN
    if data == "login":
        sessions[uid] = {"step": "user"}
        bot.send_message(uid, "Username kiriting")
        return

    if data == "logout":
        sessions.pop(uid, None)
        send_main(uid)
        return

    if uid not in sessions or sessions[uid].get("step") != "done":
        return

    username = sessions[uid]["username"]

    if data == "att_keldi":
        record_attendance(username, "Keldi")
        bot.send_message(uid, "✅ Keldi belgilandi")

    if data == "att_ketdi":
        record_attendance(username, "Ketdi")
        bot.send_message(uid, "🚪 Ketdi belgilandi")

    if data == "att_uzrli":
        record_attendance(username, "Uzrli")
        bot.send_message(uid, "📋 Uzrli sabab belgilandi")

    if data == "att_stat":
    if data == "att_history":
    db = load_attendance()

    if not db:
        bot.send_message(uid, "📭 Hali tarix yo'q")
        return

    msg = "📜 Davomat tarixi:\n\n"

    for date in sorted(db.keys(), reverse=True):
        msg += f"📅 {date}\n"

        for r in db[date]:
            msg += f" - {r['user']} | {r['status']} | {r['time']}\n"

        msg += "\n"

    bot.send_message(uid, msg)
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

# ===== LOGIN =====
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