import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask
from datetime import datetime, timedelta
import json, os, hashlib

TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
ADMIN_ID = 6344661867
DATA_FILE = "attendance.json"
TZ_OFFSET = 5

def h(p): return hashlib.sha256(p.encode()).hexdigest()

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

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()

sessions = {}
user_states = {}

# ===== DATA =====
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    return json.load(open(DATA_FILE, encoding="utf-8"))

def save_data(d):
    json.dump(d, open(DATA_FILE,"w",encoding="utf-8"), indent=2, ensure_ascii=False)

def now(): return datetime.utcnow()+timedelta(hours=TZ_OFFSET)
def today(): return now().strftime("%Y-%m-%d")
def time_now(): return now().strftime("%H:%M")

def record(user,status):
    db=load_data()
    db.setdefault(today(),[]).append({"user":user,"status":status,"time":time_now()})
    save_data(db)

# ===== MENYU =====
def main_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🏫 Maktab",callback_data="school"),
        InlineKeyboardButton("👨‍🏫 O‘qituvchilar",callback_data="teachers"),
    )
    kb.add(
        InlineKeyboardButton("📚 Sinflar",callback_data="classes"),
        InlineKeyboardButton("📰 Yangiliklar",callback_data="news"),
    )
    kb.add(
        InlineKeyboardButton("📩 Murojaat",callback_data="contact"),
        InlineKeyboardButton("🔐 Kabinet",callback_data="login"),
    )
    return kb

def panel_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Keldim",callback_data="keldi"),
        InlineKeyboardButton("🚪 Ketdim",callback_data="ketdi"),
    )
    kb.add(
        InlineKeyboardButton("📋 Uzrli",callback_data="uzrli"),
        InlineKeyboardButton("📊 Statistika",callback_data="stat"),
    )
    kb.add(InlineKeyboardButton("🔙 Chiqish",callback_data="logout"))
    return kb

# ===== START =====
@bot.message_handler(commands=["start"])
def start(m):
    sessions.pop(m.chat.id, None)
    user_states.pop(m.chat.id, None)
    bot.send_message(m.chat.id,"🏫 10-maktab tizimi",reply_markup=main_kb())

# ===== TEXT HANDLER =====
@bot.message_handler(func=lambda m: True)
def handler(m):
    uid=m.chat.id

    # Murojaat
    if user_states.get(uid)=="contact":
        bot.send_message(ADMIN_ID,f"📩 Yangi murojaat:\n\n{m.text}")
        bot.send_message(uid,"✅ Yuborildi")
        user_states.pop(uid)
        return

    s=sessions.get(uid)

    if not s: return
    if s.get("step")=="done": return

    if s["step"]=="user":
        if m.text not in TEACHERS:
            bot.send_message(uid,"❌ User topilmadi"); return
        sessions[uid]["u"]=m.text
        sessions[uid]["step"]="pass"
        bot.send_message(uid,"🔒 Parol")

    elif s["step"]=="pass":
        u=s["u"]
        if TEACHERS[u]==h(m.text):
            sessions[uid]={"step":"done","u":u}
            bot.send_message(uid,f"✅ {u}",reply_markup=panel_kb())
        else:
            sessions.pop(uid)
            bot.send_message(uid,"❌ Xato")

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda c: True)
def call(c):
    uid=c.message.chat.id
    d=c.data
    bot.answer_callback_query(c.id)

    if d=="school":
        bot.send_message(uid,"🏫 Maktab haqida ma'lumot")
    elif d=="teachers":
        bot.send_message(uid,"👨‍🏫 O‘qituvchilar ro‘yxati")
    elif d=="classes":
        bot.send_message(uid,"📚 Sinflar haqida ma'lumot")
    elif d=="news":
        bot.send_message(uid,"📰 Yangiliklar")
    elif d=="contact":
        user_states[uid]="contact"
        bot.send_message(uid,"✍️ Murojaatingizni yozing")

    elif d=="login":
        sessions[uid]={"step":"user"}
        bot.send_message(uid,"👤 Username")

    elif d=="logout":
        sessions.pop(uid,None)
        bot.send_message(uid,"Chiqdingiz",reply_markup=main_kb())

    elif sessions.get(uid,{}).get("step")!="done":
        bot.send_message(uid,"Avval login qiling")

    else:
        u=sessions[uid]["u"]

        if d=="keldi": record(u,"Keldi")
        elif d=="ketdi": record(u,"Ketdi")
        elif d=="uzrli": record(u,"Uzrli")

        elif d=="stat":
            db=load_data()
            t=today()
            msg=f"📊 {t}\n\n"
            done={i["user"]:i["status"] for i in db.get(t,[])}
            for teacher in TEACHERS:
                if teacher in done:
                    msg+=f"🟢 {teacher} — {done[teacher]}\n"
                else:
                    msg+=f"🔴 {teacher} — Belgilanmadi\n"
            bot.send_message(uid,msg)

print("🚀 ISHLAYAPTI")
bot.infinity_polling()