import json
import os
import hashlib
from datetime import datetime, timedelta
from functools import wraps

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from flask import Flask, request, redirect, session as web_session, url_for


TOKEN = os.getenv("BOT_TOKEN", "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://mybot-4k74.onrender.com")
ADMIN_TG_ID = int(os.getenv("ADMIN_TG_ID", "0"))
CONTACT_RECEIVER_ID = 6344661867
TZ_OFFSET = int(os.getenv("TZ_OFFSET", "5"))

SCHOOL_POLYGON = [
    (40.855905, 69.629203),
    (40.855461, 69.629444),
    (40.855826, 69.631161),
    (40.856281, 69.630919),
]

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "maktab10")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "maktab1010")

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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "school-secret-key")

sessions = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(default, dict) and isinstance(data, dict):
                return data
            if isinstance(default, list) and isinstance(data, list):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_teachers():
    teachers = load_json("teachers.json", {})
    changed = False
    for username, plain_password in TEACHER_CREDENTIALS.items():
        hashed = hash_password(plain_password)
        if teachers.get(username) != hashed:
            teachers[username] = hashed
            changed = True
    if changed or not os.path.exists("teachers.json"):
        save_json("teachers.json", teachers)
    return teachers


def load_school():
    return load_json("school.json", {})


def load_teacher_info():
    return load_json("teacher_info.json", {})


def load_attendance():
    return load_json("att.json", {})


def save_attendance(data):
    save_json("att.json", data)


def load_bindings():
    return load_json("user_bindings.json", {})


def save_bindings(data):
    save_json("user_bindings.json", data)


def normalize_news_item(item):
    if isinstance(item, dict):
        return {
            "text": str(item.get("text", "")).strip(),
            "image": str(item.get("image", "")).strip() if item.get("image") else None,
            "time": str(item.get("time", "")).strip() or current_timestamp(),
        }
    return {"text": str(item), "image": None, "time": current_timestamp()}


def load_news():
    raw = load_json("news.json", [])
    normalized = [normalize_news_item(item) for item in raw]
    if normalized != raw:
        save_json("news.json", normalized)
    return normalized


def save_news(data):
    prepared = [normalize_news_item(item) for item in data]
    save_json("news.json", prepared)


def get_today():
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET)).strftime("%Y-%m-%d")


def get_time():
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET)).strftime("%H:%M")


def current_timestamp():
    return (datetime.utcnow() + timedelta(hours=TZ_OFFSET)).strftime("%Y-%m-%d %H:%M:%S")


def record_attendance(username, status):
    db = load_attendance()
    day = get_today()
    db.setdefault(day, {})
    db[day][username] = {"status": status, "time": get_time()}
    save_attendance(db)


def is_inside_polygon(lat, lon, polygon):
    inside = False
    x = lon
    y = lat
    n = len(polygon)
    p1y, p1x = polygon[0]

    for i in range(1, n + 1):
        p2y, p2x = polygon[i % n]
        if min(p1y, p2y) <= y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            else:
                xinters = p1x
            if p1x == p2x or x <= xinters:
                inside = not inside
        p1y, p1x = p2y, p2x
    return inside


def format_teacher_label(username):
    return username.replace("_", " ").title()


def kb_main():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🏫 Maktab"), KeyboardButton("👨‍🏫 O‘qituvchilar"))
    kb.row(KeyboardButton("📰 Yangiliklar"), KeyboardButton("📩 Murojaat"))
    kb.row(KeyboardButton("🔐 Kabinet"))
    return kb


def kb_teachers():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    teachers = list(load_teachers().keys())
    for i in range(0, len(teachers), 2):
        row = [KeyboardButton(format_teacher_label(teachers[i]))]
        if i + 1 < len(teachers):
            row.append(KeyboardButton(format_teacher_label(teachers[i + 1])))
        kb.row(*row)
    kb.row(KeyboardButton("⬅️ Orqaga"))
    return kb


def kb_cabinet():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("✅ Keldim"), KeyboardButton("🚶 Ketdim"))
    kb.row(KeyboardButton("⚠️ Uzrli"), KeyboardButton("📊 Statistika"))
    kb.row(KeyboardButton("📜 Tarix"), KeyboardButton("🚪 Chiqish"))
    return kb


def kb_location_request():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(KeyboardButton("📍 Lokatsiya yuborish", request_location=True))
    kb.row(KeyboardButton("⬅️ Orqaga"))
    return kb


def ensure_teacher_binding(username, uid):
    bindings = load_bindings()
    current = bindings.get(username)
    if current is None:
        bindings[username] = uid
        save_bindings(bindings)
        return True
    try:
        return int(current) == int(uid)
    except (TypeError, ValueError):
        return False


def get_teacher_by_label(label):
    lookup = {}
    for username in load_teachers().keys():
        lookup[format_teacher_label(username)] = username
    return lookup.get(label)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not web_session.get("admin_ok"):
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapper


def render_html_page(title, content):
    return f"""
<!DOCTYPE html>
<html lang='uz'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>{title}</title>
<style>
    body {{ font-family: Arial, sans-serif; background: #f5f7fb; margin: 0; color: #0f172a; }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
    .card {{ background: #ffffff; border-radius: 12px; padding: 16px; margin-bottom: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.07); }}
    h1, h2, h3 {{ margin-top: 0; }}
    a.btn, button {{ background: #2563eb; color: white; border: none; border-radius: 8px; padding: 10px 14px; text-decoration: none; cursor: pointer; }}
    a.btn.danger, button.danger {{ background: #dc2626; }}
    input, textarea {{ width: 100%; padding: 10px; margin-top: 6px; margin-bottom: 10px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
    .muted {{ color: #64748b; }}
    .topnav {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }}
</style>
</head>
<body>
<div class='wrap'>
{content}
</div>
</body>
</html>
"""


@app.route("/")
def home():
    return "Bot ishlayapti"


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        u = (request.form.get("username") or "").strip()
        p = request.form.get("password") or ""
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            web_session["admin_ok"] = True
            return redirect("/dashboard")
        error = "Login yoki parol noto‘g‘ri"

    content = f"""
    <div class='card' style='max-width:420px; margin:40px auto;'>
        <h2>🔐 Admin kirish</h2>
        <form method='post'>
            <label>Login</label>
            <input name='username' required>
            <label>Parol</label>
            <input name='password' type='password' required>
            <button type='submit'>Kirish</button>
        </form>
        <p style='color:#dc2626;'>{error}</p>
    </div>
    """
    return render_html_page("Admin Login", content)


@app.route("/admin/logout")
def admin_logout():
    web_session.clear()
    return redirect(url_for("admin_login"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = load_attendance()
    teachers = load_teachers()
    news = load_news()

    news_rows = ""
    for idx, item in enumerate(news):
        image_text = item.get("image") or "-"
        news_rows += (
            "<div class='card'>"
            f"<p><b>#{idx}</b> {item.get('text', '')}</p>"
            f"<p class='muted'>Rasm: {image_text}</p>"
            f"<p class='muted'>Vaqt: {item.get('time', '')}</p>"
            f"<a class='btn danger' href='/delete_news/{idx}'>O‘chirish</a>"
            "</div>"
        )
    if not news_rows:
        news_rows = "<p class='muted'>Yangilik yo‘q.</p>"

    attendance_blocks = ""
    for date_key in sorted(db.keys(), reverse=True):
        day_data = db.get(date_key, {})
        rows = ""
        for teacher in teachers.keys():
            info = day_data.get(teacher)
            if info:
                rows += f"<p><b>{teacher}</b> — {info.get('status', '-') } ({info.get('time', '-')})</p>"
            else:
                rows += f"<p class='muted'><b>{teacher}</b> — Belgilanmagan</p>"
        attendance_blocks += f"<div class='card'><h3>📅 {date_key}</h3>{rows}</div>"

    content = f"""
    <h1>🏫 Maktab boshqaruv paneli</h1>
    <div class='topnav'>
        <a class='btn' href='/add_news'>📰 Yangilik qo‘shish</a>
        <a class='btn' href='/add_school'>🏫 Maktab ma’lumoti</a>
        <a class='btn' href='/add_teacher_info'>👨‍🏫 O‘qituvchi info</a>
        <a class='btn danger' href='/admin/logout'>🚪 Chiqish</a>
    </div>

    <div class='grid'>
        <div class='card'>
            <h2>📰 Yangiliklar</h2>
            {news_rows}
        </div>
        <div class='card'>
            <h2>📊 Davomat</h2>
            {attendance_blocks if attendance_blocks else "<p class='muted'>Davomat yo‘q.</p>"}
        </div>
    </div>
    """
    return render_html_page("Dashboard", content)


@app.route("/add_news", methods=["GET", "POST"])
@login_required
def add_news():
    if request.method == "POST":
        text = (request.form.get("text") or "").strip()
        image = (request.form.get("image") or "").strip() or None
        if text:
            news = load_news()
            news.append({"text": text, "image": image, "time": current_timestamp()})
            save_news(news)
        return redirect("/dashboard")

    content = """
    <div class='card'>
        <h2>📰 Yangilik qo‘shish</h2>
        <form method='post'>
            <label>Matn</label>
            <textarea name='text' rows='5' required></textarea>
            <label>Rasm URL yoki Telegram file_id (ixtiyoriy)</label>
            <input name='image'>
            <button type='submit'>Saqlash</button>
        </form>
        <p><a class='btn' href='/dashboard'>⬅️ Orqaga</a></p>
    </div>
    """
    return render_html_page("Add News", content)


@app.route("/delete_news/<int:index>")
@login_required
def delete_news(index):
    news = load_news()
    if 0 <= index < len(news):
        news.pop(index)
        save_news(news)
    return redirect("/dashboard")


@app.route("/add_school", methods=["GET", "POST"])
@login_required
def add_school():
    if request.method == "POST":
        save_json("school.json", {"info": request.form.get("text", "")})
        return redirect("/dashboard")

    school = load_school().get("info", "")
    content = f"""
    <div class='card'>
        <h2>🏫 Maktab ma’lumoti</h2>
        <form method='post'>
            <textarea name='text' rows='8'>{school}</textarea>
            <button type='submit'>Saqlash</button>
        </form>
        <p><a class='btn' href='/dashboard'>⬅️ Orqaga</a></p>
    </div>
    """
    return render_html_page("School Info", content)


@app.route("/add_teacher_info", methods=["GET", "POST"])
@login_required
def add_teacher_info():
    if request.method == "POST":
        username = (request.form.get("name") or "").strip()
        text = (request.form.get("text") or "").strip()
        if username:
            data = load_teacher_info()
            data[username] = text
            save_json("teacher_info.json", data)
        return redirect("/dashboard")

    options = "".join([f"<option value='{name}'>{name}</option>" for name in load_teachers().keys()])
    content = f"""
    <div class='card'>
        <h2>👨‍🏫 O‘qituvchi ma’lumoti</h2>
        <form method='post'>
            <label>Username</label>
            <input name='name' list='teacher-list' required>
            <datalist id='teacher-list'>{options}</datalist>
            <label>Ma’lumot</label>
            <textarea name='text' rows='6' required></textarea>
            <button type='submit'>Saqlash</button>
        </form>
        <p><a class='btn' href='/dashboard'>⬅️ Orqaga</a></p>
    </div>
    """
    return render_html_page("Teacher Info", content)


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/setwebhook")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    return "Webhook set"


@bot.message_handler(commands=["start"])
def handle_start(message):
    uid = message.chat.id
    user_session = sessions.get(uid)
    if user_session and user_session.get("ok"):
        bot.send_message(uid, "🔐 Kabinetingizga xush kelibsiz", reply_markup=kb_cabinet())
    else:
        bot.send_message(uid, "🏫 Maktab tizimiga xush kelibsiz", reply_markup=kb_main())


@bot.message_handler(content_types=["location"])
def handle_location(message):
    uid = message.chat.id
    user_session = sessions.get(uid)
    if not user_session or not user_session.get("ok") or user_session.get("step") != "wait_location":
        return

    lat = message.location.latitude
    lon = message.location.longitude

    if is_inside_polygon(lat, lon, SCHOOL_POLYGON):
        record_attendance(user_session["u"], "Keldi")
        bot.send_message(uid, "✅ Keldi holati qabul qilindi", reply_markup=kb_cabinet())
    else:
        bot.send_message(uid, "Siz maktab hududida emassiz ❌", reply_markup=kb_cabinet())

    user_session.pop("step", None)


def send_last_news(uid):
    news = load_news()
    if not news:
        bot.send_message(uid, "Hozircha yangilik yo‘q", reply_markup=kb_main())
        return

    bot.send_message(uid, "📰 So‘nggi 5 ta yangilik:", reply_markup=kb_main())
    for item in news[-5:][::-1]:
        caption = f"{item.get('text', '')}\n🕒 {item.get('time', '')}".strip()
        image = item.get("image")
        if image:
            bot.send_photo(uid, image, caption=caption[:1024])
        else:
            bot.send_message(uid, caption)


def send_statistics(uid):
    db = load_attendance()
    today = get_today()
    day_data = db.get(today, {})
    teachers = load_teachers()

    lines = [f"📊 Bugungi statistika ({today})"]
    for username in teachers.keys():
        info = day_data.get(username)
        if info:
            status = info.get("status", "-")
            icon = "✅" if status == "Keldi" else "🚶" if status == "Ketdi" else "⚠️" if status == "Uzrli" else "•"
            lines.append(f"{icon} {format_teacher_label(username)} — {status} ({info.get('time', '-')})")
        else:
            lines.append(f"• {format_teacher_label(username)} — Belgilanmagan")

    bot.send_message(uid, "\n".join(lines), reply_markup=kb_cabinet())


def send_history(uid):
    db = load_attendance()
    if not db:
        bot.send_message(uid, "📜 Tarix bo‘sh", reply_markup=kb_cabinet())
        return

    teachers = load_teachers()
    lines = ["📜 Davomat tarixi"]
    for date_key in sorted(db.keys(), reverse=True):
        lines.append(f"\n📅 {date_key}")
        day_data = db.get(date_key, {})
        for username in teachers.keys():
            info = day_data.get(username)
            if info:
                lines.append(f"{format_teacher_label(username)} — {info.get('status', '-')} ({info.get('time', '-')})")
            else:
                lines.append(f"{format_teacher_label(username)} — Belgilanmagan")

    text = "\n".join(lines)
    for i in range(0, len(text), 3800):
        bot.send_message(uid, text[i : i + 3800], reply_markup=kb_cabinet())


def forward_contact_to_admin(message):
    user = message.from_user
    full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip() or "-"
    username = f"@{user.username}" if user.username else "yo‘q"
    payload = (
        "📩 Yangi murojaat\n"
        f"👤 Ism: {full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: {user.id}\n"
        f"💬 Xabar: {message.text}"
    )

    try:
        bot.send_message(CONTACT_RECEIVER_ID, payload)
        bot.reply_to(message, "Murojaatingiz yuborildi ✅", reply_markup=kb_main())
    except Exception:
        bot.reply_to(message, "Xabar yuborishda xatolik bo‘ldi", reply_markup=kb_main())


def begin_login(uid):
    sessions[uid] = {"step": "login_username"}
    bot.send_message(uid, "Login kiriting:")


@bot.message_handler(content_types=["text", "photo", "document"])
def message_router(message):
    uid = message.chat.id
    text = (message.text or "").strip() if message.content_type == "text" else ""
    user_session = sessions.get(uid, {})

    if user_session.get("step") == "waiting_for_message":
        if message.content_type != "text" or not text:
            bot.send_message(uid, "Faqat matnli xabar yuboring.")
            return
        forward_contact_to_admin(message)
        user_session.pop("step", None)
        return

    if message.content_type != "text":
        return

    if user_session.get("step") == "login_username":
        sessions[uid]["pending_username"] = text
        sessions[uid]["step"] = "login_password"
        bot.send_message(uid, "Parol kiriting:")
        return

    if user_session.get("step") == "login_password":
        username = sessions[uid].get("pending_username", "")
        teachers = load_teachers()
        if teachers.get(username) == hash_password(text):
            if not ensure_teacher_binding(username, uid):
                sessions.pop(uid, None)
                bot.send_message(uid, "❌ Bu akkaunt boshqa Telegram ID ga bog‘langan")
                return
            sessions[uid] = {"ok": True, "u": username}
            bot.send_message(uid, "✅ Muvaffaqiyatli kirildi", reply_markup=kb_cabinet())
        else:
            sessions[uid] = {"step": "login_username"}
            bot.send_message(uid, "Login yoki parol noto‘g‘ri. Loginni qayta kiriting:")
        return

    if text == "⬅️ Orqaga":
        if user_session.get("ok") and user_session.get("step") == "wait_location":
            user_session.pop("step", None)
            bot.send_message(uid, "🔐 Kabinet", reply_markup=kb_cabinet())
        else:
            user_session.pop("step", None)
            bot.send_message(uid, "🏫 Asosiy menyu", reply_markup=kb_main())
        return

    if text == "🏫 Maktab":
        bot.send_message(uid, load_school().get("info", "Ma’lumot yo‘q"), reply_markup=kb_main())
        return

    if text in ("👨‍🏫 O‘qituvchilar", "👨‍🏫 O'qituvchilar"):
        bot.send_message(uid, "👨‍🏫 O‘qituvchilar ro‘yxati", reply_markup=kb_teachers())
        return

    selected_teacher = get_teacher_by_label(text)
    if selected_teacher:
        info = load_teacher_info().get(selected_teacher, "Ma’lumot yo‘q")
        bot.send_message(uid, f"{format_teacher_label(selected_teacher)}\n\n{info}", reply_markup=kb_teachers())
        return

    if text == "📰 Yangiliklar":
        send_last_news(uid)
        return

    if text == "📩 Murojaat":
        sessions.setdefault(uid, {})["step"] = "waiting_for_message"
        bot.send_message(uid, "Xabaringizni yozing", reply_markup=ReplyKeyboardRemove())
        return

    if text == "🔐 Kabinet":
        if user_session.get("ok"):
            bot.send_message(uid, "🔐 Kabinet", reply_markup=kb_cabinet())
            return
        begin_login(uid)
        return

    if user_session.get("ok"):
        username = user_session["u"]

        if text == "✅ Keldim":
            sessions[uid]["step"] = "wait_location"
            bot.send_message(uid, "Davomat uchun lokatsiya yuboring:", reply_markup=kb_location_request())
            return

        if text == "🚶 Ketdim":
            record_attendance(username, "Ketdi")
            bot.send_message(uid, "🚶 Ketdi holati saqlandi", reply_markup=kb_cabinet())
            return

        if text == "⚠️ Uzrli":
            record_attendance(username, "Uzrli")
            bot.send_message(uid, "⚠️ Uzrli holati saqlandi", reply_markup=kb_cabinet())
            return

        if text == "📊 Statistika":
            send_statistics(uid)
            return

        if text == "📜 Tarix":
            send_history(uid)
            return

        if text == "🚪 Chiqish":
            sessions.pop(uid, None)
            bot.send_message(uid, "🚪 Kabinetdan chiqdingiz", reply_markup=kb_main())
            return

    bot.send_message(uid, "Buyruq tanlang", reply_markup=kb_main())


load_teachers()
load_news()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
