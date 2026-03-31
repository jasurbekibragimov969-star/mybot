 import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask
from datetime import datetime, timedelta
import json
import os
import hashlib

TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
DATA_FILE = "attendance.json"
TZ_OFFSET = 5

def h(p):
    return hashlib.sha256(p.encode()).hexdigest()

TEACHERS = {
"dilara_abdullayeva": h("dilara452"),
"nigora_abdurahmonova": h("nigora879"),
"gulxon_abduraxmonova": h("gulxon098"),
"sharofiddin_ahmedov": h("sharofiddin321"),
"nafisa_akkulova": h("nafisa654"),
"rano_aliyeva": h("rano111"),
"feruza_alloberdiyeva": h("feruza222"),
"gulpari_asrayeva": h("gulpari333"),
"orzugul_bekmuradova": h("orzugul444"),
"maftuna_egamberdiyeva": h("maftuna555"),
"nargiz_hakimova": h("nargiz666"),
"mavluda_ibragimjonova": h("mavluda777"),
"olmasoy_karimova": h("olmasoy888"),
"dilshoda_mamatqulova": h("dilshoda999"),
"zulfiya_mamedova": h("zulfiya147"),
"muhayyo_maxsudova": h("muhayyo258"),
"izatulla_mirzakulov": h("izatulla369"),
"dilbarbibi_nishonova": h("dilbarbibi159"),
"gulandom_qurolova": h("gulandom753"),
"robiya_rayimova": h("robiya852"),
"nadira_rustamova": h("nadira951"),
"shoxsanam_subanova": h("shoxsanam357"),
"lobar_sulaymanova": h("lobar258"),
"muslim_turgunbayev": h("muslim654"),
"gulnoza_xalmanova": h("gulnoza741"),
"olmasoy_shabazova": h("olmasoy852"),
"jaxongir_isroilov": h("jaxongir963")
} 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot ishlayapti"

def run():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run, daemon=True).start()

sessions = {}

# ===== DATA =====
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def now():
    return datetime.utcnow() + timedelta(hours=TZ_OFFSET)

def today():
    return now().strftime("%Y-%m-%d")

def time_now():
    return now().strftime("%H:%M")

def record(user, status):
    db = load_data()
    d = today()
    if d not in db:
        db[d] = []
    db[d].append({"user": user, "status": status, "time": time_now()})
    save_data(db)

# ===== KEYBOARD =====
def main_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔐 Kabinet", callback_data="login"))
    return kb

def panel_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Keldim", callback_data="keldi"),
        InlineKeyboardButton("🚪 Ketdim", callback_data="ketdi"),
    )
    kb.add(
        InlineKeyboardButton("📋 Uzrli", callback_data="uzrli"),
        InlineKeyboardButton("📊 Statistika", callback_data="stat"),
    )
    kb.add(InlineKeyboardButton("🗓 Sanalar", callback_data="dates"))
    kb.add(InlineKeyboardButton("← Chiqish", callback_data="logout"))
    return kb

# ===== START =====
@bot.message_handler(commands=["start"])
def start(m):
    sessions.pop(m.chat.id, None)
    bot.send_message(m.chat.id, "🏫 Maktab tizimi", reply_markup=main_kb())

# ===== LOGIN =====
@bot.message_handler(func=lambda m: True)
def login(m):
    uid = m.chat.id
    s = sessions.get(uid)

    if not s:
        return

    if s.get("step") == "done":
        return

    if s["step"] == "user":
        if m.text not in TEACHERS:
            bot.send_message(uid, "❌ User topilmadi")
            return
        sessions[uid]["u"] = m.text
        sessions[uid]["step"] = "pass"
        bot.send_message(uid, "🔒 Parol")

    elif s["step"] == "pass":
        u = s["u"]
        if TEACHERS[u] == h(m.text):
            sessions[uid] = {"step": "done", "u": u}
            bot.send_message(uid, f"✅ Xush kelibsiz {u}", reply_markup=panel_kb())
        else:
            sessions.pop(uid)
            bot.send_message(uid, "❌ Xato")

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda c: True)
def call(c):
    uid = c.message.chat.id
    d = c.data
    bot.answer_callback_query(c.id)

    if d == "login":
        sessions[uid] = {"step": "user"}
        bot.send_message(uid, "👤 Username")
        return

    if d == "logout":
        sessions.pop(uid, None)
        bot.send_message(uid, "Chiqdingiz", reply_markup=main_kb())
        return

    if sessions.get(uid, {}).get("step") != "done":
        bot.send_message(uid, "Avval login qiling")
        return

    u = sessions[uid]["u"]

    if d == "keldi":
        record(u, "Keldi")
        bot.send_message(uid, "🟢 Keldi")

    elif d == "ketdi":
        record(u, "Ketdi")
        bot.send_message(uid, "🔴 Ketdi")

    elif d == "uzrli":
        record(u, "Uzrli")
        bot.send_message(uid, "🟡 Uzrli")

    elif d == "stat":
        db = load_data()
        t = today()
        if t not in db:
            bot.send_message(uid, "Bo‘sh")
            return
        msg = f"{t}\n"
        for i in db[t]:
            msg += f"{i['user']} | {i['status']} | {i['time']}\n"
        bot.send_message(uid, msg)

    elif d == "dates":
        db = load_data()
        bot.send_message(uid, "\n".join(db.keys()) if db else "Bo‘sh")

print("🚀 ISHLAYAPTI")
bot.infinity_polling()