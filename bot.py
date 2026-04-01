import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask, request, redirect
from datetime import datetime, timedelta
import json, os, hashlib

# CONFIG
TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
TZ_OFFSET = 5

# WEB ADMIN LOGIN
ADMIN_USERNAME = "zkurtuve"
ADMIN_PASSWORD = "20091608"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

sessions = {}

# ===== WEB =====
@app.route("/")
def home():
    return "Bot ishlayapti"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("u") == ADMIN_USERNAME and request.form.get("p") == ADMIN_PASSWORD:
            return redirect("/dashboard")
        return "Login xato"

    return '''
    <h2>Admin Login</h2>
    <form method="post">
    <input name="u"><br><br>
    <input name="p" type="password"><br><br>
    <button>Kirish</button>
    </form>
    '''

@app.route("/dashboard")
def dashboard():
    db = load_attendance()
    html = "<h1>Davomat</h1><a href='/add'>➕ O‘qituvchi qo‘shish</a><br><br>"

    for d in db:
        html += f"<h3>{d}</h3>"
        for r in db[d]:
            html += f"{r['user']} | {r['status']} | {r['time']}<br>"
    return html

@app.route("/add", methods=["GET","POST"])
def add():
    if request.method == "POST":
        t = load_teachers()
        t[request.form.get("u")] = hash_password(request.form.get("p"))
        json.dump(t, open("teachers.json","w"))
        return "Qo‘shildi <a href='/dashboard'>Orqaga</a>"

    return '''
    <form method="post">
    <input name="u"><br>
    <input name="p"><br>
    <button>Qo‘shish</button>
    </form>
    '''

threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()

# ===== UTILS =====
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def load_teachers():
    if not os.path.exists("teachers.json"):
        return {}
    return json.load(open("teachers.json"))

def load_attendance():
    if not os.path.exists("att.json"):
        return {}
    return json.load(open("att.json"))

def save_attendance(d):
    json.dump(d, open("att.json","w"))

def get_today():
    return (datetime.utcnow()+timedelta(hours=TZ_OFFSET)).strftime("%Y-%m-%d")

def get_time():
    return (datetime.utcnow()+timedelta(hours=TZ_OFFSET)).strftime("%H:%M")

def record(user, status):
    db = load_attendance()
    t = get_today()
    db.setdefault(t, [])
    db[t].append({"user":user,"status":status,"time":get_time()})
    save_attendance(db)

# ===== KEYBOARD =====
def kb_main():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏫 Maktab",callback_data="school"))
    kb.add(InlineKeyboardButton("📚 Sinflar",callback_data="classes"))
    kb.add(InlineKeyboardButton("👨‍🏫 O'qituvchilar",callback_data="teachers"))
    kb.add(InlineKeyboardButton("🔐 Kabinet",callback_data="login"))
    kb.add(InlineKeyboardButton("📩 Murojaat",callback_data="contact"))
    return kb

def kb_classes():
    kb = InlineKeyboardMarkup(row_width=2)
    classes = ["1-a","2-a","3-a","3-b","4-a","5-a","6-a","6-b","7-a","8-a","9-a","9-b","10-a","11-a"]
    for c in classes:
        kb.add(InlineKeyboardButton(c.upper(),callback_data="c_"+c))
    kb.add(InlineKeyboardButton("⬅️ Orqaga",callback_data="back"))
    return kb

def kb_teachers():
    kb = InlineKeyboardMarkup()
    for t in load_teachers():
        kb.add(InlineKeyboardButton(t,callback_data="t_"+t))
    kb.add(InlineKeyboardButton("⬅️ Orqaga",callback_data="back"))
    return kb

def kb_panel():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Keldim",callback_data="keldi"))
    kb.add(InlineKeyboardButton("📊 Statistika",callback_data="stat"))
    kb.add(InlineKeyboardButton("📜 Tarix",callback_data="history"))
    kb.add(InlineKeyboardButton("⬅️ Chiqish",callback_data="logout"))
    return kb

# ===== START =====
@bot.message_handler(commands=["start"])
def start(m):
    sessions.pop(m.chat.id, None)
    bot.send_message(m.chat.id,"🏫 Tizim",reply_markup=kb_main())

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda c:True)
def cb(c):
    uid=c.message.chat.id
    d=c.data

    if d=="back":
        bot.send_message(uid,"🏫 Tizim",reply_markup=kb_main())

    elif d=="school":
        bot.send_message(uid,"1-qator\n2-qator\n3-qator\n4-qator\n5-qator\n6-qator")

    elif d=="classes":
        bot.send_message(uid,"Sinflar",reply_markup=kb_classes())

    elif d.startswith("c_"):
        bot.send_message(uid,"O‘quvchi soni: ...\nSinf rahbari: ...")

    elif d=="teachers":
        bot.send_message(uid,"O‘qituvchilar",reply_markup=kb_teachers())

    elif d.startswith("t_"):
        name=d[2:]
        bot.send_message(uid,f"{name}\nFan: ...\nToifa: ...\nAloqa: ...")

    elif d=="contact":
        bot.send_message(uid,"@zkurtuve")

    elif d=="login":
        sessions[uid]={"step":"u"}
        bot.send_message(uid,"Username")

    elif d=="logout":
        sessions.pop(uid,None)
        bot.send_message(uid,"Chiqildi",reply_markup=kb_main())

    elif uid in sessions and sessions[uid].get("ok"):
        user=sessions[uid]["u"]

        if d=="keldi":
            record(user,"Keldi")
            bot.send_message(uid,"Belgilandi")

        elif d=="stat":
            db=load_attendance()
            today=get_today()
            msg="Stat\n"
            for t in load_teachers():
                status="yo'q"
                for r in db.get(today,[]):
                    if r["user"]==t:
                        status=r["status"]
                msg+=f"{t} - {status}\n"
            bot.send_message(uid,msg)

        elif d=="history":
            db=load_attendance()
            msg=""
            for d in db:
                msg+=d+"\n"
                for r in db[d]:
                    msg+=f"{r['user']} {r['status']} {r['time']}\n"
            bot.send_message(uid,msg)

# ===== LOGIN =====
@bot.message_handler(func=lambda m:True)
def login(m):
    uid=m.chat.id
    if uid not in sessions: return

    if sessions[uid]["step"]=="u":
        sessions[uid]["u"]=m.text
        sessions[uid]["step"]="p"
        bot.send_message(uid,"Parol")

    elif sessions[uid]["step"]=="p":
        t=load_teachers()
        if t.get(sessions[uid]["u"])==hash_password(m.text):
            sessions[uid]["ok"]=True
            bot.send_message(uid,"Kabinet",reply_markup=kb_panel())
        else:
            bot.send_message(uid,"Xato")

print("ISHGA TUSHDI")
bot.infinity_polling()