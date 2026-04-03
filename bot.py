import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask, request, redirect
from datetime import datetime, timedelta
import json
import os
import hashlib

# CONFIG
TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"
TZ_OFFSET = 5

# WEB ADMIN LOGIN
ADMIN_USERNAME = "maktab10"
ADMIN_PASSWORD = "maktab1010"

TEACHER_CREDENTIALS = {
    "dilara_abdullayeva": "dilara452",
    "nigora_abdurahmonova": "nigora879",
    "gulxon_abduraxmonova": "gulxon098",
    "sharofiddin_ahmedov": "sharofiddin321",
    "nafisa_akkulova": "nafisa654",
    "rano_aliyeva": "rano111",
    "orzugul_bekmuradova": "orzugul444",
    "maftuna_egamberdiyeva": "maftuna555",
    "nargiz_hakimova": "nargiz666",
    "mavluda_ibragimjonova": "mavluda777",
    "olmasoy_karimova": "olmasoy888",
    "dilshoda_mamatqulova": "dilshoda999",
    "zulfiya_mamedova": "zulfiya147",
    "muhayyo_maxsudova": "muhayyo258",
    "izatulla_mirzakulov": "izatulla369",
    "dilbarbibi_nishonova": "dilbarbibi159",
    "gulandom_qurolova": "gulandom753",
    "robiya_rayimova": "robiya852",
    "nadira_rustamova": "nadira951",
    "shoxsanam_subanova": "shoxsanam357",
    "lobar_sulaymanova": "lobar258",
    "muslim_turgunbayev": "muslim654",
    "gulnoza_xalmanova": "gulnoza741",
    "olmasoy_shabazova": "olmasoy852",
    "feruza_alloberdiyeva": "feruza222",
    "gulpari_asrayeva": "gulpari333",
    "jaxongir_isroilov": "jaxongir963",
}

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

sessions = {}


# ===== UTILS =====
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_classes():
    if not os.path.exists("classes.json"):
        return {}
    with open("classes.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_teacher_info():
    if not os.path.exists("teacher_info.json"):
        return {}
    with open("teacher_info.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_news():
    if not os.path.exists("news.json"):
        return []
    with open("news.json", "r", encoding="utf-8") as f:
        return json.load(f)


def save_news(data):
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_teachers():
    teachers = {}
    if os.path.exists("teachers.json"):
        with open("teachers.json", "r", encoding="utf-8") as file:
            teachers = json.load(file)

    updated = False
    for username, plain_password in TEACHER_CREDENTIALS.items():
        hashed_password = hash_password(plain_password)
        if teachers.get(username) != hashed_password:
            teachers[username] = hashed_password
            updated = True

    if updated or not os.path.exists("teachers.json"):
        with open("teachers.json", "w", encoding="utf-8") as file:
            json.dump(teachers, file, ensure_ascii=False, indent=2)

    return teachers

def load_school():
    if not os.path.exists("school.json"):
        return {}
    with open("school.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_attendance():
    if not os.path.exists("att.json"):
        return {}
    with open("att.json", "r", encoding="utf-8") as file:
        return json.load(file)


def save_attendance(data):
    with open("att.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_today():
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET)).strftime("%Y-%m-%d")


def get_time():
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET)).strftime("%H:%M")


def record(user, status):
    db = load_attendance()
    today = get_today()

    db.setdefault(today, {})

    db[today][user] = {
        "status": status,
        "time": get_time()
    }

    save_attendance(db)

def build_daily_status_map(records):
    status_map = {}
    for item in records:
        status_map[item["user"]] = item["status"]
    return status_map


# ===== WEB =====
@app.route("/")
def home():
    return "Bot ishlayapti"

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        teachers = load_teachers()
        teachers[request.form.get("u")] = hash_password(request.form.get("p"))
        with open("teachers.json", "w", encoding="utf-8") as file:
            json.dump(teachers, file, ensure_ascii=False, indent=2)
        return "Qoshildi <a href='/dashboard'>Orqaga</a>"

    return '''
    <form method="post">
    <input name="u"><br>
    <input name="p"><br>
    <button>Qoshish</button>
    </form>
    '''

@app.route("/dashboard")
def dashboard():
    db = load_attendance()
    teachers = load_teachers()

    html = """
    <html>
    <head>
    <title>Davomat</title>
    <style>
        body {font-family: Arial; background: #0f172a; color: white;}
        h1 {text-align: center;}
        .card {background: #1e293b; padding: 15px; margin: 10px; border-radius: 10px;}
        .green {color: #22c55e;}
        .blue {color: #3b82f6;}
        .yellow {color: #eab308;}
        .gray {color: #9ca3af;}
    </style>
    </head>
    <body>
    <h1>📊 Davomat Dashboard</h1>

    <!-- 🔥 SHU YERGA QO‘SHASAN 🔥 -->
    <div style='text-align:center; margin-bottom:20px;'>
    <a href='/add_news'>📰 Yangilik qo‘shish</a> |
    <a href='/add_school'>🏫 Maktab info</a> |
    <a href='/add_teacher_info'>👨‍🏫 Teacher info</a> |
    <a href='/add_class'>📚 Sinf info</a>
    </div>
    """

    for date_key in sorted(db.keys(), reverse=True):
        html += f"<div class='card'><h3>📅 {date_key}</h3>"

        day_data = db.get(date_key, {})

        for teacher in teachers.keys():
            info = day_data.get(teacher)

            if info:
                status = info["status"]
                time = info["time"]

                if status == "Keldi":
                    cls = "green"
                elif status == "Ketdi":
                    cls = "blue"
                elif status == "Uzrli":
                    cls = "yellow"
                else:
                    cls = "gray"

                html += f"<p class='{cls}'>{teacher} — {status} ({time})</p>"
            else:
                html += f"<p class='gray'>{teacher} — Belgilanmagan</p>"

        html += "</div>"

    html += "</body></html>"
    return html

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        teachers = load_teachers()
        teachers[request.form.get("u")] = hash_password(request.form.get("p"))
        with open("teachers.json", "w", encoding="utf-8") as file:
            json.dump(teachers, file, ensure_ascii=False, indent=2)
        return "Qoshildi <a href='/dashboard'>Orqaga</a>"

    return '''
   
@app.route("/add_news", methods=["GET", "POST"])
def add_news():
    if request.method == "POST":
        news = load_news()
        news.append(request.form.get("text"))
        save_news(news)
        return "Qoshildi <a href='/dashboard'>Orqaga</a>"

    return '''
   
@app.route("/add_school", methods=["GET", "POST"])
def add_school():
    if request.method == "POST":
        data = {"info": request.form.get("text")}
        with open("school.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return "Saqlandi <a href='/dashboard'>Orqaga</a>"

    return '''
    <form method="post">
    <textarea name="text"></textarea><br>
    <button>Saqlash</button>
    </form>
    '''

@app.route("/add_teacher_info", methods=["GET", "POST"])
def add_teacher_info():
    if request.method == "POST":
        data = load_teacher_info()
        data[request.form.get("name")] = request.form.get("text")

        with open("teacher_info.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return "Saqlandi <a href='/dashboard'>Orqaga</a>"

    return '''
    <form method="post">
    Username:<br>
    <input name="name"><br>
    Info:<br>
    <textarea name="text"></textarea><br>
    <button>Saqlash</button>
    </form>
    '''

@app.route("/add_class", methods=["GET", "POST"])
def add_class():
    if request.method == "POST":
        data = load_classes()
        data[request.form.get("name")] = request.form.get("text")

        with open("classes.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return "Saqlandi <a href='/dashboard'>Orqaga</a>"

    return '''
    <form method="post">
    Sinf nomi:<br>
    <input name="name"><br>
    Info:<br>
    <textarea name="text"></textarea><br>
    <button>Saqlash</button>
    </form>
    '''

    <form method="post">
    <input name="u"><br>
    <input name="p"><br>
    <button>Qoshish</button>
    </form>
    '''


# ===== KEYBOARD =====
def kb_main():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🏫 Maktab", callback_data="school"))
    kb.add(InlineKeyboardButton("📚 Sinflar", callback_data="classes"))
    kb.add(InlineKeyboardButton("👨‍🏫 O'qituvchilar", callback_data="teachers"))
    kb.add(InlineKeyboardButton("🔐 Kabinet", callback_data="login"))
    kb.add(InlineKeyboardButton("📰 Yangiliklar", callback_data="news"))
    kb.add(InlineKeyboardButton("📩 Murojaat", callback_data="contact"))
    return kb


def kb_classes():
    kb = InlineKeyboardMarkup(row_width=2)
    classes = ["1-a", "2-a", "3-a", "3-b", "4-a", "5-a", "6-a", "6-b", "7-a", "8-a", "9-a", "9-b", "10-a", "11-a"]
    for c_name in classes:
        kb.add(InlineKeyboardButton(c_name.upper(), callback_data="c_" + c_name))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="back"))
    return kb


def kb_teachers():
    kb = InlineKeyboardMarkup()
    for teacher in load_teachers().keys():
        kb.add(InlineKeyboardButton(teacher, callback_data="t_" + teacher))
    kb.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="back"))
    return kb


def kb_panel():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Keldim👍", callback_data="keldi"))
    kb.add(InlineKeyboardButton("Ketdim🫡", callback_data="ketdi"))
    kb.add(InlineKeyboardButton("Uzrli sabab‼️", callback_data="uzrli"))
    kb.add(InlineKeyboardButton("Statistika📊", callback_data="stat"))
    kb.add(InlineKeyboardButton("Tarix⌛", callback_data="history"))
    kb.add(InlineKeyboardButton("⬅️ Chiqish", callback_data="logout"))
    return kb


# ===== START =====
@bot.message_handler(commands=["start"])
def start(message):
    sessions.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "🏫 Tizim", reply_markup=kb_main())


# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = call.message.chat.id
    data = call.data

    if data == "back":
        bot.send_message(uid, "🏫 Tizim", reply_markup=kb_main())

    elif data.startswith("c_"):
        cname = data[2:]
        classes = load_classes()
        info = classes.get(cname, "Ma’lumot yo‘q")

        bot.send_message(uid, f"{cname}\n{info}")

    elif data == "school":
        school = load_school()
        bot.send_message(uid, school.get("info", "Ma’lumot yo‘q"))

    elif data == "classes":
        bot.send_message(uid, "Sinflar", reply_markup=kb_classes())

    elif data == "teachers":
        bot.send_message(uid, "O‘qituvchilar", reply_markup=kb_teachers())

    elif data.startswith("t_"):
        name = data[2:]
        data_info = load_teacher_info()
        info = data_info.get(name, "Ma’lumot yo‘q")

        bot.send_message(uid, f"{name}\n{info}")

    elif data == "contact":
        bot.send_message(uid, "Muammo yuz bersa 👉 @zkurtuve")

    elif data == "news":
        news = load_news()

        if not news:
            bot.send_message(uid, "Hozircha yangilik yo‘q")
            return

        text = "📰 Yangiliklar:\n\n"
        for item in news[-5:][::-1]:
            text += f"• {item}\n\n"

        bot.send_message(uid, text)

    elif data == "login":
        sessions[uid] = {"step": "u"}
        bot.send_message(uid, "Username")

    elif data == "logout":
        sessions.pop(uid, None)
        bot.send_message(uid, "Chiqildi🫡", reply_markup=kb_main())

    elif uid in sessions and sessions[uid].get("ok"):
        user = sessions[uid]["u"]

        if data == "keldi":
            record(user, "Keldi")
            bot.send_message(uid, "Belgilandi: Keldi👏")

        elif data == "ketdi":
            record(user, "Ketdi")
            bot.send_message(uid, "Belgilandi: Ketdi🤝")

        elif data == "uzrli":
            record(user, "Uzrli")
            bot.send_message(uid, "Belgilandi: Uzrli👌")

        elif data == "stat":
            db = load_attendance()
            today = get_today()

            teachers = load_teachers()
            today_data = db.get(today, {})

            lines = [f"Statistika ({today})"]

            for teacher in teachers.keys():
                info = today_data.get(teacher)

                if info:
                    status = info["status"]
                    time = info["time"]

                    if status == "Keldi":
                        icon = "🟢"
                    elif status == "Ketdi":
                        icon = "🔵"
                    elif status == "Uzrli":
                        icon = "🟡"
                    else:
                        icon = "⚫"

                    lines.append(f"{icon} {teacher} — {status} ({time})")

                else:
                    lines.append(f"⚫ {teacher} — Belgilanmagan😠")

            bot.send_message(uid, "\n".join(lines))


        elif data == "history":
            db = load_attendance()
            teachers = load_teachers()

            if not db:
                bot.send_message(uid, "Tarix bo‘sh")
                return

            lines = ["Keldi ketdi tarixi"]

            for date_key in sorted(db.keys(), reverse=True):
                lines.append(f"\n📅 {date_key}")

                day_data = db.get(date_key, {})

                for teacher in teachers.keys():
                    info = day_data.get(teacher)

                    if info:
                        lines.append(f"{teacher} — {info['status']} ({info['time']})")
                    else:
                        lines.append(f"{teacher} — Belgilanmagan")

            bot.send_message(uid, "\n".join(lines))

# ===== LOGIN =====
@bot.message_handler(func=lambda message: True)
def login(message):
    uid = message.chat.id
    if uid not in sessions:
        return

    if sessions[uid]["step"] == "u":
        sessions[uid]["u"] = message.text
        sessions[uid]["step"] = "p"
        bot.send_message(uid, "Parol🧐")

    elif sessions[uid]["step"] == "p":
        teachers = load_teachers()
        if teachers.get(sessions[uid]["u"]) == hash_password(message.text):
            sessions[uid]["ok"] = True
            bot.send_message(uid, "Kabinet", reply_markup=kb_panel())
        else:
            bot.send_message(uid, "Kiritilgan ma'lumot nato'g'ri😔")


# Ensure required teachers are present at startup.
load_teachers()

WEBHOOK_URL = "https://mybot-4k74.onrender.com"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/setwebhook")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    return "Webhook set"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
