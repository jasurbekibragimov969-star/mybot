import hashlib
import json
import math
import os
import threading
import time
import zipfile
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO
from xml.sax.saxutils import escape

import telebot
from flask import Flask, redirect, request, session as web_session, url_for
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


TOKEN = "8665940219:AAGZ8w4g83Zb10c-o6O5B6xNE4mZ7Zv8mxE"

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
ADMIN_TG_ID = int(os.getenv("ADMIN_TG_ID", "6344661867"))
CONTACT_RECEIVER_ID = int(os.getenv("CONTACT_RECEIVER_ID", str(ADMIN_TG_ID)))
TZ_OFFSET = int(os.getenv("TZ_OFFSET", "5"))
START_HOUR = 8
START_MINUTE = 0
GRACE_HOUR = 8
GRACE_MINUTE = 5
REMINDER_HOUR = 8
REMINDER_MINUTE = 0
MAX_LOCATION_AGE_SECONDS = 120
NEWS_PREVIEW_LIMIT = 500

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

DATA_DEFAULTS = {
    "teachers.json": {},
    "school.json": {},
    "teacher_info.json": None,
    "tacher_info.json": {},
    "att.json": {},
    "user_bindings.json": {},
    "warnings.json": {},
    "news.json": [],
}

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "school-secret-key")

sessions = {}
admin_reply_map = {}
reminder_state = {"date": None}
late_alert_targets = {}

json_cache = {}
json_cache_serialized = {}
json_lock = threading.RLock()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _clone_default(default):
    return json.loads(json.dumps(default))


def load_json(path, default):
    with json_lock:
        if path in json_cache:
            return _clone_default(json_cache[path])

        if not os.path.exists(path):
            data = _clone_default(default)
            json_cache[path] = _clone_default(data)
            json_cache_serialized[path] = json.dumps(data, ensure_ascii=False, sort_keys=True)
            return data

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                valid = (isinstance(default, dict) and isinstance(data, dict)) or (
                    isinstance(default, list) and isinstance(data, list)
                )
                if not valid:
                    data = _clone_default(default)
        except (json.JSONDecodeError, OSError):
            data = _clone_default(default)

        json_cache[path] = _clone_default(data)
        json_cache_serialized[path] = json.dumps(data, ensure_ascii=False, sort_keys=True)
        return _clone_default(data)


def save_json(path, data):
    with json_lock:
        serialized = json.dumps(data, ensure_ascii=False, sort_keys=True)
        if json_cache_serialized.get(path) == serialized:
            return False
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        json_cache[path] = _clone_default(data)
        json_cache_serialized[path] = serialized
        return True


def prime_cache():
    for path, default in DATA_DEFAULTS.items():
        load_json(path, default)


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
    info = load_json("teacher_info.json", None)
    if isinstance(info, dict):
        return info
    legacy = load_json("tacher_info.json", {})
    return legacy if isinstance(legacy, dict) else {}


def save_teacher_info(data):
    save_json("teacher_info.json", data)


def load_attendance():
    return load_json("att.json", {})


def save_attendance(data):
    save_json("att.json", data)


def load_bindings():
    return load_json("user_bindings.json", {})


def save_bindings(data):
    save_json("user_bindings.json", data)


def load_warnings():
    return load_json("warnings.json", {})


def save_warnings(data):
    save_json("warnings.json", data)


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


def now_local() -> datetime:
    return datetime.utcnow() + timedelta(hours=TZ_OFFSET)


def get_today():
    return now_local().strftime("%Y-%m-%d")


def get_time():
    return now_local().strftime("%H:%M")


def current_timestamp():
    return now_local().strftime("%Y-%m-%d %H:%M:%S")


def parse_date_safe(date_text):
    try:
        return datetime.strptime(date_text, "%Y-%m-%d")
    except Exception:
        return None


def record_attendance(username, status):
    db = load_attendance()
    day = get_today()
    db.setdefault(day, {})
    new_payload = {"status": status, "time": get_time()}
    if db[day].get(username) == new_payload:
        return
    db[day][username] = new_payload
    save_attendance(db)


def record_attendance_for_day(day, username, status):
    db = load_attendance()
    db.setdefault(day, {})
    new_payload = {"status": status, "time": get_time()}
    if db[day].get(username) == new_payload:
        return
    db[day][username] = new_payload
    save_attendance(db)


def has_attendance_for_today(username):
    db = load_attendance()
    return username in db.get(get_today(), {})


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


def polygon_centroid(polygon):
    lat_sum = sum(point[0] for point in polygon)
    lon_sum = sum(point[1] for point in polygon)
    return lat_sum / len(polygon), lon_sum / len(polygon)


def distance_meters(lat1, lon1, lat2, lon2):
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def format_teacher_label(username):
    return username.replace("_", " ").title()


def kb_main():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🏫 Maktab"), KeyboardButton("👨‍🏫 O‘qituvchilar"))
    kb.row(KeyboardButton("📰 Yangiliklar"), KeyboardButton("📩 Murojaat"))
    kb.row(KeyboardButton("🔐 Kabinet"), KeyboardButton("ℹ️ Yordam"))
    return kb


def kb_teachers():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    teachers = list(load_teachers().keys())
    for i in range(0, len(teachers), 2):
        row = [KeyboardButton(format_teacher_label(teachers[i]))]
        if i + 1 < len(teachers):
            row.append(KeyboardButton(format_teacher_label(teachers[i + 1])))
        kb.row(*row)
    kb.row(KeyboardButton("⬅️ Orqaga"), KeyboardButton("🏠 Asosiy menyu"))
    return kb


def kb_cabinet():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("✅ Keldim"), KeyboardButton("🚶 Ketdim"))
    kb.row(KeyboardButton("⚠️ Uzrli"), KeyboardButton("📊 Statistika"))
    kb.row(KeyboardButton("📜 Tarix"), KeyboardButton("📤 Export"))
    kb.row(KeyboardButton("⬅️ Orqaga"), KeyboardButton("🚪 Chiqish"))
    return kb


def kb_location_request():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(KeyboardButton("📍 Lokatsiya yuborish", request_location=True))
    kb.row(KeyboardButton("⬅️ Orqaga"), KeyboardButton("🏠 Asosiy menyu"))
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


def teacher_from_user_id(uid):
    bindings = load_bindings()
    for username, tg_id in bindings.items():
        try:
            if int(tg_id) == int(uid):
                return username
        except (TypeError, ValueError):
            continue
    return None


def detect_arrive_status():
    now = now_local()
    grace = now.replace(hour=GRACE_HOUR, minute=GRACE_MINUTE, second=0, microsecond=0)
    return "Kechikdi" if now > grace else "Keldi"


def late_message_keyboard(target_user_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✉️ Xabar yuborish", callback_data=f"late_msg:{target_user_id}"))
    return kb


def uzrli_keyboard(username, teacher_uid, date_key):
    compact_date = date_key.replace("-", "")
    approve_data = f"uzrli_ok:{username}:{teacher_uid}:{compact_date}"
    reject_data = f"uzrli_no:{username}:{teacher_uid}:{compact_date}"
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=approve_data),
        InlineKeyboardButton("❌ Bekor qilish", callback_data=reject_data),
    )
    return kb


def register_late_warning(username, uid):
    warnings = load_warnings()
    count = int(warnings.get(username, 0)) + 1
    warnings[username] = count
    save_warnings(warnings)

    if count >= 3 and count % 3 == 0:
        bot.send_message(
            uid,
            "⏰ Bugun yana kechikdingiz. Bu qayta-qayta takrorlanyapti, iltimos jadvalni qat’iy rejalashtiring.",
        )
    elif count >= 2:
        bot.send_message(uid, "⚠️ Kechikish qayd etildi. Ertadan vaqtga yanada e’tibor bering.")
    else:
        bot.send_message(uid, "⏰ Bugungi belgilash *kechikdi* holatida saqlandi.", parse_mode="Markdown")

    if count % 3 == 0:
        alert_text = (
            "⚠️ O'qituvchi kech qoldi!\n\n"
            f"👤 Username: {username}\n"
            f"🆔 ID: {uid}\n"
            f"📅 Sana: {get_today()}\n"
            f"⏰ Vaqt: {get_time()}\n"
            "❗ 3-marta kechikdi"
        )
        try:
            sent = bot.send_message(
                ADMIN_TG_ID,
                alert_text,
                reply_markup=late_message_keyboard(uid),
            )
            late_alert_targets[sent.message_id] = uid
        except Exception:
            pass


def valid_fresh_location(message):
    if not getattr(message, "date", None):
        return False
    msg_time_utc = datetime.utcfromtimestamp(message.date)
    age = datetime.utcnow() - msg_time_utc
    return age.total_seconds() <= MAX_LOCATION_AGE_SECONDS


def monthly_statistics_for(username, year, month):
    db = load_attendance()
    month_days = []
    for day in db.keys():
        dt = parse_date_safe(day)
        if dt and dt.year == year and dt.month == month:
            month_days.append(day)

    counts = {"Keldi": 0, "Kechikdi": 0, "Uzrli": 0, "Kelmagan": 0}
    for day in month_days:
        status = (db.get(day, {}).get(username) or {}).get("status")
        if status in counts:
            counts[status] += 1
        else:
            counts["Kelmagan"] += 1

    counts["Kelmagan"] += max(len(month_days) - (counts["Keldi"] + counts["Kechikdi"] + counts["Uzrli"]), 0)
    return counts, sorted(month_days)


def all_monthly_statistics(year, month):
    result = {}
    for username in load_teachers().keys():
        result[username] = monthly_statistics_for(username, year, month)[0]
    return result


def format_news_message(item):
    timestamp = item.get("time", "")
    dt = None
    try:
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    if dt:
        time_part = dt.strftime("%H:%M | %d-%b")
    else:
        time_part = timestamp

    text = item.get("text", "")
    if len(text) > NEWS_PREVIEW_LIMIT:
        text = f"{text[:NEWS_PREVIEW_LIMIT].rstrip()}..."

    return f"📰 *Yangilik:*\n\n{text}\n\n🕒 {time_part}"


def build_sheet_xml(rows):
    xml_rows = []
    for r_index, row in enumerate(rows, start=1):
        cells = []
        for c_index, value in enumerate(row, start=1):
            col_name = ""
            n = c_index
            while n:
                n, rem = divmod(n - 1, 26)
                col_name = chr(65 + rem) + col_name
            ref = f"{col_name}{r_index}"
            val = escape(str(value if value is not None else ""))
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{val}</t></is></c>')
        xml_rows.append(f"<row r=\"{r_index}\">{''.join(cells)}</row>")

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(xml_rows)}</sheetData>"
        "</worksheet>"
    )


def create_attendance_xlsx():
    db = load_attendance()
    rows = [["Sana", "O'qituvchi", "Status", "Vaqt"]]
    teachers = load_teachers()
    for day in sorted(db.keys()):
        day_data = db.get(day, {})
        for username in teachers.keys():
            info = day_data.get(username)
            if info:
                rows.append([day, format_teacher_label(username), info.get("status", ""), info.get("time", "")])
            else:
                rows.append([day, format_teacher_label(username), "Kelmagan", "-"])

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Attendance" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )

    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", build_sheet_xml(rows))
    stream.seek(0)
    return stream


def send_export_to_admin(requester_id):
    xlsx_data = create_attendance_xlsx()
    filename = f"attendance_{get_today()}.xlsx"
    caption = f"📤 Export so‘rovi: {requester_id}"
    bot.send_document(CONTACT_RECEIVER_ID, (filename, xlsx_data), caption=caption)


def send_reminders():
    today = get_today()
    db = load_attendance()
    day_data = db.get(today, {})
    bindings = load_bindings()

    for username in load_teachers().keys():
        if username in day_data:
            continue
        uid = bindings.get(username)
        if uid is None:
            continue
        try:
            bot.send_message(
                int(uid),
                "🔔 Eslatma: bugungi davomatni belgilang (✅ Keldim / ⚠️ Uzrli).",
                reply_markup=kb_cabinet(),
            )
        except Exception:
            continue


def reminder_loop():
    while True:
        try:
            now = now_local()
            date_key = now.strftime("%Y-%m-%d")
            target = now.replace(hour=REMINDER_HOUR, minute=REMINDER_MINUTE, second=0, microsecond=0)
            if now >= target and reminder_state.get("date") != date_key:
                send_reminders()
                reminder_state["date"] = date_key
        except Exception:
            pass
        time.sleep(30)


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
    :root {{
        --bg:#f1f5f9;
        --card:#ffffff;
        --text:#0f172a;
        --muted:#64748b;
        --primary:#2563eb;
        --danger:#dc2626;
        --success:#16a34a;
        --border:#dbe2ee;
    }}
    * {{ box-sizing:border-box; }}
    body {{ font-family:Inter,Arial,sans-serif;background:var(--bg);margin:0;color:var(--text); }}
    .page {{ min-height:100vh; display:flex; justify-content:center; padding:26px 14px; }}
    .wrap {{ width:100%; max-width:1160px; }}
    .card {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:16px; margin-bottom:14px; box-shadow:0 6px 20px rgba(15,23,42,.06); }}
    .center {{ max-width:760px; margin:0 auto; }}
    h1,h2,h3 {{ margin:0 0 12px 0; }}
    p {{ margin:6px 0; line-height:1.5; }}
    .muted {{ color:var(--muted); }}
    .btn,button {{ display:inline-block; border:0; border-radius:10px; background:var(--primary); color:#fff; text-decoration:none; padding:10px 14px; cursor:pointer; font-weight:600; }}
    .btn:hover,button:hover {{ opacity:.95; }}
    .danger {{ background:var(--danger); }}
    .success {{ background:var(--success); }}
    .btn-row {{ display:flex; gap:10px; flex-wrap:wrap; }}
    input,textarea {{ width:100%; border:1px solid var(--border); border-radius:10px; padding:11px 12px; margin-top:6px; margin-bottom:12px; font-size:14px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(290px,1fr)); gap:14px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ border-bottom:1px solid var(--border); text-align:left; padding:8px; vertical-align:top; }}
    .topnav {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px; }}
    .flash {{ border:1px solid #86efac; background:#f0fdf4; color:#14532d; font-weight:700; }}
</style>
<script>
function confirmDelete(url) {{
    if (confirm("Ushbu yangilikni o‘chirmoqchimisiz?")) {{
        window.location.href = url;
    }}
}}
</script>
</head>
<body>
<div class='page'>
<div class='wrap'>
{content}
</div>
</div>
</body>
</html>
"""


def render_reset_form(error_text=""):
    error_block = f"<p style='color:#dc2626;font-weight:bold;'>{error_text}</p>" if error_text else ""
    warning_text = "⚠️ DIQQAT!<br>Bu amal barcha davomat (att.json) ma’lumotlarini O‘CHIRADI!<br><br>Bu amalni qaytarib bo‘lmaydi.<br><br>Davom etasizmi?"
    content = f"""
    <div class='card center'>
        <h2>🔄 Tizimni tozalash</h2>
        <form method='post' action='/admin/reset'>
            <label>ADMIN_USERNAME</label>
            <input name='username' required>
            <label>ADMIN_PASSWORD</label>
            <input name='password' type='password' required>
            <div style='margin:14px 0;padding:14px;border:2px solid #dc2626;border-radius:10px;background:#fef2f2;font-size:18px;line-height:1.5;'>
                {warning_text}
            </div>
            <div class='btn-row'>
                <button class='danger' type='submit' name='confirm' value='YES'>YES</button>
                <button type='submit' name='confirm' value='NO'>NO</button>
            </div>
        </form>
        {error_block}
        <p style='margin-top:12px;'><a class='btn' href='/dashboard'>⬅️ Orqaga</a></p>
    </div>
    """
    return render_html_page("System Reset", content)


def safe_user_message(uid, text, reply_markup=None, parse_mode=None):
    try:
        bot.send_message(uid, text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        pass


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
    <div class='card center' style='max-width:460px;'>
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
    dashboard_message = web_session.pop("dashboard_message", "")

    news_rows = ""
    for idx, item in enumerate(news):
        image_text = item.get("image") or "-"
        news_rows += (
            "<div class='card'>"
            f"<p><b>#{idx}</b> {item.get('text', '')}</p>"
            f"<p class='muted'>Rasm: {image_text}</p>"
            f"<p class='muted'>Vaqt: {item.get('time', '')}</p>"
            f"<button class='danger' onclick=\"confirmDelete('/delete_news/{idx}')\">O‘chirish</button>"
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

    now = now_local()
    month_stats = all_monthly_statistics(now.year, now.month)
    stat_rows = ""
    for username in teachers.keys():
        stat = month_stats.get(username, {})
        stat_rows += (
            "<tr>"
            f"<td>{format_teacher_label(username)}</td>"
            f"<td>{stat.get('Keldi', 0)}</td>"
            f"<td>{stat.get('Kechikdi', 0)}</td>"
            f"<td>{stat.get('Uzrli', 0)}</td>"
            f"<td>{stat.get('Kelmagan', 0)}</td>"
            "</tr>"
        )
    monthly_table = (
        "<div class='card'>"
        f"<h2>📊 Oylik analitika ({now.strftime('%Y-%m')})</h2>"
        "<div style='overflow-x:auto;'>"
        "<table>"
        "<thead><tr><th>O‘qituvchi</th><th>Keldi</th><th>Kechikdi</th><th>Uzrli</th><th>Kelmagan</th></tr></thead>"
        f"<tbody>{stat_rows}</tbody>"
        "</table></div></div>"
    )

    message_block = f"<div class='card flash'><b>{dashboard_message}</b></div>" if dashboard_message else ""

    content = f"""
    <h1>🏫 Maktab boshqaruv paneli</h1>
    <div class='topnav'>
        <a class='btn' href='/add_news'>📰 Yangilik qo‘shish</a>
        <a class='btn' href='/add_school'>🏫 Maktab ma’lumoti</a>
        <a class='btn' href='/add_teacher_info'>👨‍🏫 O‘qituvchi info</a>
        <form method='post' action='/admin/reset' style='display:inline;'>
            <button class='danger' type='submit'>🔄 Restart / Yangi yil</button>
        </form>
        <a class='btn danger' href='/admin/logout'>🚪 Chiqish</a>
    </div>
    {message_block}

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
    {monthly_table}
    """
    return render_html_page("Dashboard", content)


@app.route("/admin/reset", methods=["POST"])
@login_required
def admin_reset():
    username = request.form.get("username")
    password = request.form.get("password")
    confirm = (request.form.get("confirm") or "").upper()

    if username is None and password is None and not confirm:
        return render_reset_form()

    if confirm == "NO":
        web_session["dashboard_message"] = "Reset bekor qilindi."
        return redirect("/dashboard")

    if confirm == "YES":
        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            return render_reset_form("Noto‘g‘ri login ❌")
        save_attendance({})
        web_session["dashboard_message"] = "✅ Tizim tozalandi! Yangi o‘quv yili uchun tayyor 📚"
        return redirect("/dashboard")

    return render_reset_form()


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
            web_session["dashboard_message"] = "✅ Yangilik qo‘shildi"
        return redirect("/dashboard")

    content = """
    <div class='card center'>
        <h2>📰 Yangilik qo‘shish</h2>
        <form method='post'>
            <label>Matn</label>
            <textarea name='text' rows='5' required></textarea>
            <label>Rasm URL yoki Telegram file_id (ixtiyoriy)</label>
            <input name='image'>
            <button type='submit' class='success'>Saqlash</button>
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
        web_session["dashboard_message"] = "✅ Yangilik o‘chirildi"
    return redirect("/dashboard")


@app.route("/add_school", methods=["GET", "POST"])
@login_required
def add_school():
    if request.method == "POST":
        save_json("school.json", {"info": request.form.get("text", "")})
        web_session["dashboard_message"] = "✅ Maktab ma’lumoti yangilandi"
        return redirect("/dashboard")

    school = load_school().get("info", "")
    content = f"""
    <div class='card center'>
        <h2>🏫 Maktab ma’lumoti</h2>
        <form method='post'>
            <textarea name='text' rows='8'>{school}</textarea>
            <button type='submit' class='success'>Saqlash</button>
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
            save_teacher_info(data)
            web_session["dashboard_message"] = "✅ O‘qituvchi ma’lumoti saqlandi"
        return redirect("/dashboard")

    options = "".join([f"<option value='{name}'>{name}</option>" for name in load_teachers().keys()])
    content = f"""
    <div class='card center'>
        <h2>👨‍🏫 O‘qituvchi ma’lumoti</h2>
        <form method='post'>
            <label>Username</label>
            <input name='name' list='teacher-list' required>
            <datalist id='teacher-list'>{options}</datalist>
            <label>Ma’lumot</label>
            <textarea name='text' rows='6' required></textarea>
            <button type='submit' class='success'>Saqlash</button>
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


def send_main_menu(uid, headline="🏫 Maktab tizimiga xush kelibsiz"):
    safe_user_message(uid, f"*{headline}*\n\nQuyidagilardan birini tanlang.", reply_markup=kb_main(), parse_mode="Markdown")


def send_cabinet_menu(uid, headline="🔐 Kabinetingizga xush kelibsiz"):
    safe_user_message(uid, f"*{headline}*\n\n✅ Davomatni belgilang yoki statistikani ko‘ring.", reply_markup=kb_cabinet(), parse_mode="Markdown")


@bot.message_handler(commands=["start"])
def handle_start(message):
    uid = message.chat.id
    bound_teacher = teacher_from_user_id(uid)
    if bound_teacher:
        sessions[uid] = {"ok": True, "u": bound_teacher}
        send_cabinet_menu(uid)
        return

    user_session = sessions.get(uid)
    if user_session and user_session.get("ok"):
        send_cabinet_menu(uid)
    else:
        send_main_menu(uid)


@bot.message_handler(content_types=["location"])
def handle_location(message):
    uid = message.chat.id
    user_session = sessions.get(uid)
    if not user_session or not user_session.get("ok") or user_session.get("step") != "wait_location":
        return

    if not valid_fresh_location(message):
        safe_user_message(uid, "❌ Lokatsiya eskirgan. Iltimos yangisini yuboring.", reply_markup=kb_location_request())
        return

    lat = message.location.latitude
    lon = message.location.longitude

    if is_inside_polygon(lat, lon, SCHOOL_POLYGON):
        arrive_status = detect_arrive_status()
        record_attendance(user_session["u"], arrive_status)
        if arrive_status == "Kechikdi":
            register_late_warning(user_session["u"], uid)
            safe_user_message(uid, "✅ Siz muvaffaqiyatli belgilandingiz!\n\n⏰ Holat: *Kechikdi*", reply_markup=kb_cabinet(), parse_mode="Markdown")
        else:
            safe_user_message(uid, "✅ Siz muvaffaqiyatli belgilandingiz!\n\n👏 Ajoyib! Siz bugun o‘z vaqtida keldingiz.", reply_markup=kb_cabinet())
    else:
        center_lat, center_lon = polygon_centroid(SCHOOL_POLYGON)
        distance = distance_meters(lat, lon, center_lat, center_lon)
        safe_user_message(
            uid,
            f"⚠️ Siz maktab hududidan tashqaridasiz.\n\nTaxminiy masofa: *{distance} m*\nIltimos, hudud ichidan qayta yuboring.",
            reply_markup=kb_cabinet(),
            parse_mode="Markdown",
        )

    user_session.pop("step", None)


def send_last_news(uid):
    news = load_news()
    if not news:
        safe_user_message(uid, "📰 Hozircha yangilik yo‘q.", reply_markup=kb_main())
        return

    safe_user_message(uid, "📰 *So‘nggi 5 ta yangilik*", reply_markup=kb_main(), parse_mode="Markdown")
    for item in news[-5:][::-1]:
        caption = format_news_message(item)
        image = item.get("image")
        if image:
            try:
                bot.send_photo(uid, image, caption=caption[:1024], parse_mode="Markdown")
            except Exception:
                safe_user_message(uid, caption, parse_mode="Markdown")
        else:
            safe_user_message(uid, caption, parse_mode="Markdown")


def send_statistics(uid, username):
    now = now_local()
    year, month = now.year, now.month
    counts, _ = monthly_statistics_for(username, year, month)

    text = (
        "📊 *Oylik hisobot:*\n\n"
        f"✅ Keldi: {counts['Keldi']}\n"
        f"⏰ Kechikdi: {counts['Kechikdi']}\n"
        f"⚠️ Uzrli: {counts['Uzrli']}\n"
        f"❌ Kelmagan: {counts['Kelmagan']}"
    )
    safe_user_message(uid, text, reply_markup=kb_cabinet(), parse_mode="Markdown")


def status_emoji(status):
    return {
        "Keldi": "✅ Keldi",
        "Kechikdi": "⏰ Kechikdi",
        "Uzrli": "⚠️ Uzrli",
        "Ketdi": "🚶 Ketdi",
        "pending_uzrli": "⏳ Uzrli (kutilyapti)",
        "Uzrli rad etildi": "❌ Uzrli rad etildi",
    }.get(status, f"❔ {status}")


def send_history(uid, username):
    db = load_attendance()
    rows = []
    for date_key in sorted(db.keys(), reverse=True):
        info = db.get(date_key, {}).get(username)
        if not info:
            continue
        dt = parse_date_safe(date_key)
        date_label = dt.strftime("%d-%b") if dt else date_key
        rows.append((date_label, status_emoji(info.get("status", ""))))
        if len(rows) >= 7:
            break

    if not rows:
        safe_user_message(uid, "📜 Sizda tarix yozuvi topilmadi.", reply_markup=kb_cabinet())
        return

    blocks = ["📜 *So‘nggi 7 ta davomat:*\n"]
    for date_label, status in rows:
        blocks.append(f"📅 {date_label}\n{status}\n")

    safe_user_message(uid, "\n".join(blocks), reply_markup=kb_cabinet(), parse_mode="Markdown")


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
        sent = bot.send_message(CONTACT_RECEIVER_ID, payload)
        admin_reply_map[sent.message_id] = user.id
        bot.reply_to(message, "✅ Xabaringiz yuborildi", reply_markup=kb_main())
    except Exception:
        bot.reply_to(message, "❌ Xabar yuborilmadi. Iltimos keyinroq urinib ko‘ring.", reply_markup=kb_main())


def reply_admin_to_user(message):
    if message.from_user.id != CONTACT_RECEIVER_ID:
        return False
    if not message.reply_to_message:
        return False

    target_user_id = admin_reply_map.get(message.reply_to_message.message_id)
    if not target_user_id:
        return False

    reply_text = message.text or ""
    if not reply_text:
        return False

    try:
        bot.send_message(target_user_id, f"📬 *Admin javobi*\n\n{reply_text}", parse_mode="Markdown")
        bot.reply_to(message, "✅ Foydalanuvchiga yuborildi")
    except Exception:
        bot.reply_to(message, "❌ Yuborilmadi")
    return True


def begin_login(uid):
    sessions[uid] = {"step": "login_username"}
    safe_user_message(uid, "🔐 *Kabinetga kirish*\n\nLogin kiriting:", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    data = call.data or ""
    caller_id = call.from_user.id

    if data.startswith("late_msg:"):
        if caller_id != ADMIN_TG_ID:
            bot.answer_callback_query(call.id, "Ruxsat yo‘q")
            return
        _, target_id = data.split(":", 1)
        try:
            target_id_int = int(target_id)
        except ValueError:
            bot.answer_callback_query(call.id, "Xatolik")
            return
        sessions.setdefault(caller_id, {})["step"] = "waiting_late_admin_message"
        sessions[caller_id]["late_target_id"] = target_id_int
        bot.answer_callback_query(call.id, "Xabar yozing")
        safe_user_message(caller_id, "O‘qituvchiga yuboriladigan xabarni yozing:")
        return

    if data.startswith("uzrli_ok:") or data.startswith("uzrli_no:"):
        if caller_id != ADMIN_TG_ID:
            bot.answer_callback_query(call.id, "Ruxsat yo‘q")
            return
        try:
            action, username, teacher_uid, compact_date = data.split(":", 3)
            teacher_uid_int = int(teacher_uid)
            date_key = datetime.strptime(compact_date, "%Y%m%d").strftime("%Y-%m-%d")
        except Exception:
            bot.answer_callback_query(call.id, "Xatolik")
            return

        db = load_attendance()
        day_data = db.get(date_key, {})
        teacher_record = day_data.get(username, {})
        if teacher_record.get("status") != "pending_uzrli":
            bot.answer_callback_query(call.id, "So‘rov topilmadi yoki allaqachon ko‘rilgan")
            return

        if action == "uzrli_ok":
            record_attendance_for_day(date_key, username, "Uzrli")
            safe_user_message(teacher_uid_int, "✅ Sizning uzrli so'rovingiz tasdiqlandi")
            bot.answer_callback_query(call.id, "Tasdiqlandi")
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            return

        db.setdefault(date_key, {})
        if username in db[date_key]:
            db[date_key][username]["status"] = "Uzrli rad etildi"
        else:
            db[date_key][username] = {"status": "Uzrli rad etildi", "time": get_time()}
        save_attendance(db)
        safe_user_message(teacher_uid_int, "❌ Sizning uzrli so'rovingiz rad etildi")
        bot.answer_callback_query(call.id, "Bekor qilindi")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception:
            pass
        return


@bot.message_handler(content_types=["text", "photo", "document"])
def message_router(message):
    uid = message.chat.id
    text = (message.text or "").strip() if message.content_type == "text" else ""
    user_session = sessions.get(uid, {})

    if message.content_type == "text" and reply_admin_to_user(message):
        return

    if user_session.get("step") == "waiting_for_message":
        if message.content_type != "text" or not text:
            safe_user_message(uid, "Faqat matnli xabar yuboring.")
            return
        forward_contact_to_admin(message)
        user_session.pop("step", None)
        return

    if user_session.get("step") == "waiting_late_admin_message":
        if uid != ADMIN_TG_ID:
            user_session.pop("step", None)
            user_session.pop("late_target_id", None)
            return
        if message.content_type != "text" or not text:
            safe_user_message(uid, "Faqat matnli xabar yuboring.")
            return
        target_id = user_session.get("late_target_id")
        if not target_id:
            user_session.pop("step", None)
            safe_user_message(uid, "Maqsadli o‘qituvchi topilmadi.")
            return
        try:
            bot.send_message(int(target_id), f"📬 *Admin xabari*\n\n{text}", parse_mode="Markdown")
            safe_user_message(uid, "✅ O‘qituvchiga yuborildi")
        except Exception:
            safe_user_message(uid, "❌ Xabar yuborilmadi")
        user_session.pop("step", None)
        user_session.pop("late_target_id", None)
        return

    if message.content_type != "text":
        return

    if user_session.get("step") == "login_username":
        sessions[uid]["pending_username"] = text
        sessions[uid]["step"] = "login_password"
        safe_user_message(uid, "Parol kiriting:")
        return

    if user_session.get("step") == "login_password":
        username = sessions[uid].get("pending_username", "")
        teachers = load_teachers()
        if teachers.get(username) == hash_password(text):
            if not ensure_teacher_binding(username, uid):
                sessions.pop(uid, None)
                safe_user_message(uid, "❌ Sizga ruxsat berilmagan")
                return
            sessions[uid] = {"ok": True, "u": username}
            send_cabinet_menu(uid, "✅ Muvaffaqiyatli kirildi")
        else:
            sessions[uid] = {"step": "login_username"}
            safe_user_message(uid, "❌ Login yoki parol noto‘g‘ri. Loginni qayta kiriting:")
        return

    if text in ("⬅️ Orqaga", "🏠 Asosiy menyu"):
        if user_session.get("ok") and user_session.get("step") == "wait_location":
            user_session.pop("step", None)
            send_cabinet_menu(uid, "🔐 Kabinet")
        else:
            user_session.pop("step", None)
            send_main_menu(uid, "🏠 Asosiy menyu")
        return

    if text == "🏫 Maktab":
        safe_user_message(uid, f"🏫 *Maktab ma’lumoti*\n\n{load_school().get('info', 'Ma’lumot yo‘q')}", reply_markup=kb_main(), parse_mode="Markdown")
        return

    if text in ("👨‍🏫 O‘qituvchilar", "👨‍🏫 O'qituvchilar"):
        safe_user_message(uid, "👨‍🏫 *O‘qituvchilar ro‘yxati*", reply_markup=kb_teachers(), parse_mode="Markdown")
        return

    selected_teacher = get_teacher_by_label(text)
    if selected_teacher:
        info = load_teacher_info().get(selected_teacher, "Ma’lumot yo‘q")
        safe_user_message(uid, f"*{format_teacher_label(selected_teacher)}*\n\n{info}", reply_markup=kb_teachers(), parse_mode="Markdown")
        return

    if text == "📰 Yangiliklar":
        send_last_news(uid)
        return

    if text == "📩 Murojaat":
        sessions.setdefault(uid, {})["step"] = "waiting_for_message"
        safe_user_message(uid, "📩 Xabaringizni yozing.", reply_markup=ReplyKeyboardRemove())
        return

    if text == "ℹ️ Yordam":
        help_text = (
            "ℹ️ *Yordam*\n\n"
            "• 🔐 Kabinet: login va davomat\n"
            "• ✅ Keldim: lokatsiya orqali belgilash\n"
            "• 📊 Statistika: oylik natijalar\n"
            "• 📩 Murojaat: admin bilan aloqa"
        )
        safe_user_message(uid, help_text, reply_markup=kb_main(), parse_mode="Markdown")
        return

    if text == "🔐 Kabinet":
        if user_session.get("ok"):
            send_cabinet_menu(uid, "🔐 Kabinet")
            return
        auto_teacher = teacher_from_user_id(uid)
        if auto_teacher:
            sessions[uid] = {"ok": True, "u": auto_teacher}
            send_cabinet_menu(uid, "✅ Avtomatik kirish bajarildi")
            return
        begin_login(uid)
        return

    if user_session.get("ok"):
        username = user_session["u"]

        if text == "✅ Keldim":
            sessions[uid]["step"] = "wait_location"
            safe_user_message(
                uid,
                "✅ *Davomat belgilash*\n\n📍 Iltimos joylashuvingizni yuboring.",
                reply_markup=kb_location_request(),
                parse_mode="Markdown",
            )
            return

        if text == "🚶 Ketdim":
            record_attendance(username, "Ketdi")
            safe_user_message(uid, "🚶 Ketdi holati saqlandi", reply_markup=kb_cabinet())
            return

        if text == "⚠️ Uzrli":
            day = get_today()
            record_attendance(username, "pending_uzrli")
            safe_user_message(uid, "⏳ Uzrli so‘rovingiz adminga yuborildi.", reply_markup=kb_cabinet())
            admin_text = (
                "⚠️ Uzrli so'rovi!\n\n"
                f"👤 {username}\n"
                f"📅 {day}\n\n"
                "Tasdiqlaysizmi?"
            )
            try:
                bot.send_message(ADMIN_TG_ID, admin_text, reply_markup=uzrli_keyboard(username, uid, day))
            except Exception:
                pass
            return

        if text == "📊 Statistika":
            send_statistics(uid, username)
            return

        if text == "📜 Tarix":
            send_history(uid, username)
            return

        if text == "📤 Export":
            try:
                send_export_to_admin(uid)
                safe_user_message(uid, "📤 Export admin ga yuborildi", reply_markup=kb_cabinet())
            except Exception:
                safe_user_message(uid, "❌ Export yuborishda xatolik", reply_markup=kb_cabinet())
            return

        if text == "🚪 Chiqish":
            sessions.pop(uid, None)
            send_main_menu(uid, "🚪 Kabinetdan chiqdingiz")
            return

    send_main_menu(uid, "Buyruq tanlang")


prime_cache()
load_teachers()
load_news()

threading.Thread(target=reminder_loop, daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
