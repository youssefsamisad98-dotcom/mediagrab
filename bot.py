import os
import logging
import threading
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict

import telebot
from telebot import types

from config import (BOT_TOKEN, MAX_FILE_SIZE_MB, MAX_DURATION_MIN,
                    MAX_CONCURRENT_DOWNLOADS, RATE_LIMIT_PER_HOUR)
import downloader as dl
import adsgram

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

MIN_AD_TIME = 5
ADMIN_ID = 0  # حط الآيدي بتاعك هنا (اختياري)
AD_EVERY = 3

COUNTER_FILE = "counter.json"
STATS_FILE = "stats.json"
LANG_FILE = "langs.json"

LANGS = {
    "ar": {"name": "🇸🇦 العربية"},
    "en": {"name": "🇬🇧 English"},
    "fr": {"name": "🇫🇷 Français"},
    "es": {"name": "🇪🇸 Español"},
    "tr": {"name": "🇹🇷 Türkçe"},
}

T = {
    "ar": {
        "choose_lang": "🌍 اختر لغتك:",
        "welcome": "أهلاً بيك! 👋\n\nابعت لينك الفيديو وهنحملهولك.",
        "send_link": "ابعت لينك الفيديو.",
        "invalid": "❌ ده مش لينك صحيح.",
        "busy": "⏳ عندك تحميل شغال.",
        "limit": "⚠️ وصلت الحد الاقصى.",
        "checking": "🔍 جاري فحص اللينك...",
        "cant_fetch": "❌ مش قادر اوصل للفيديو.",
        "too_long": "⚠️ الفيديو طويل جدًا.",
        "choose": "اختار:",
        "audio": "🎧 صوت",
        "video": "🎬 فيديو",
        "cancel": "❌ إلغاء",
        "choose_q": "🎬 اختار الجودة:",
        "downloading": "⏳ جاري التحميل...",
        "uploading": "📤 جاري الرفع...",
        "failed": "❌ فشل التحميل.",
        "too_big": "⚠️ الملف كبير.",
        "error": "❌ خطأ: ",
        "cancelled": "❌ تم الالغاء.",
        "ad_gate": "🎁 وصلت لـ {n} تحميلات!\n\nشوف الاعلان ده عشان نكمل.",
        "ad_wait": "لسه ما خلصتش",
        "lang_set": "✅ تم اختيار اللغة.",
        "change_lang": "🌍 تغيير اللغة",
    },
    "en": {
        "choose_lang": "🌍 Choose your language:",
        "welcome": "Welcome! 👋\n\nSend me a video link.",
        "send_link": "Send me a video link.",
        "invalid": "❌ Invalid link.",
        "busy": "⏳ Active download.",
        "limit": "⚠️ Hourly limit reached.",
        "checking": "🔍 Checking...",
        "cant_fetch": "❌ Can't fetch video.",
        "too_long": "⚠️ Video too long.",
        "choose": "Choose:",
        "audio": "🎧 Audio",
        "video": "🎬 Video",
        "cancel": "❌ Cancel",
        "choose_q": "🎬 Choose quality:",
        "downloading": "⏳ Downloading...",
        "uploading": "📤 Uploading...",
        "failed": "❌ Failed.",
        "too_big": "⚠️ File too large.",
        "error": "❌ Error: ",
        "cancelled": "❌ Cancelled.",
        "ad_gate": "🎁 You reached {n} downloads!\n\nWatch this ad.",
        "ad_wait": "Not yet",
        "lang_set": "✅ Language set.",
        "change_lang": "🌍 Change language",
    },
    "fr": {
        "choose_lang": "🌍 Choisissez votre langue :",
        "welcome": "Bienvenue ! 👋\n\nEnvoyez un lien vidéo.",
        "send_link": "Envoyez un lien vidéo.",
        "invalid": "❌ Lien invalide.",
        "busy": "⏳ Téléchargement en cours.",
        "limit": "⚠️ Limite atteinte.",
        "checking": "🔍 Vérification...",
        "cant_fetch": "❌ Impossible.",
        "too_long": "⚠️ Vidéo trop longue.",
        "choose": "Choisissez :",
        "audio": "🎧 Audio",
        "video": "🎬 Vidéo",
        "cancel": "❌ Annuler",
        "choose_q": "🎬 Qualité :",
        "downloading": "⏳ Téléchargement...",
        "uploading": "📤 Envoi...",
        "failed": "❌ Échec.",
        "too_big": "⚠️ Fichier trop grand.",
        "error": "❌ Erreur : ",
        "cancelled": "❌ Annulé.",
        "ad_gate": "🎁 {n} téléchargements !\n\nRegardez cette pub.",
        "ad_wait": "Pas encore",
        "lang_set": "✅ Langue définie.",
        "change_lang": "🌍 Changer de langue",
    },
    "es": {
        "choose_lang": "🌍 Elige tu idioma:",
        "welcome": "¡Bienvenido! 👋\n\nEnvía un enlace de video.",
        "send_link": "Envía un enlace.",
        "invalid": "❌ Enlace no válido.",
        "busy": "⏳ Descarga en curso.",
        "limit": "⚠️ Límite alcanzado.",
        "checking": "🔍 Verificando...",
        "cant_fetch": "❌ No puedo acceder.",
        "too_long": "⚠️ Video muy largo.",
        "choose": "Elige:",
        "audio": "🎧 Audio",
        "video": "🎬 Video",
        "cancel": "❌ Cancelar",
        "choose_q": "🎬 Calidad:",
        "downloading": "⏳ Descargando...",
        "uploading": "📤 Subiendo...",
        "failed": "❌ Falló.",
        "too_big": "⚠️ Archivo muy grande.",
        "error": "❌ Error: ",
        "cancelled": "❌ Cancelado.",
        "ad_gate": "🎁 ¡{n} descargas!\n\nMira este anuncio.",
        "ad_wait": "Aún no",
        "lang_set": "✅ Idioma configurado.",
        "change_lang": "🌍 Cambiar idioma",
    },
    "tr": {
        "choose_lang": "🌍 Dilini seç:",
        "welcome": "Hoş geldin! 👋\n\nBir link gönder.",
        "send_link": "Bir link gönder.",
        "invalid": "❌ Geçersiz link.",
        "busy": "⏳ Aktif indirme.",
        "limit": "⚠️ Saatlik limit doldu.",
        "checking": "🔍 Kontrol...",
        "cant_fetch": "❌ Ulaşamıyorum.",
        "too_long": "⚠️ Video çok uzun.",
        "choose": "Seç:",
        "audio": "🎧 Ses",
        "video": "🎬 Video",
        "cancel": "❌ İptal",
        "choose_q": "🎬 Kalite:",
        "downloading": "⏳ İndiriliyor...",
        "uploading": "📤 Yükleniyor...",
        "failed": "❌ Başarısız.",
        "too_big": "⚠️ Dosya çok büyük.",
        "error": "❌ Hata: ",
        "cancelled": "❌ İptal edildi.",
        "ad_gate": "🎁 {n} indirme!\n\nBu reklamı izle.",
        "ad_wait": "Henüz değil",
        "lang_set": "✅ Dil ayarlandı.",
        "change_lang": "🌍 Dili değiştir",
    },
}

LANG_KEYWORDS = {
    "ar": ["عربي", "عربية", "العربية", "arabic", "arab", "ar"],
    "en": ["انجليزي", "إنجليزي", "english", "eng", "en"],
    "fr": ["فرنسي", "فرنسية", "french", "francais", "fr"],
    "es": ["اسباني", "إسباني", "spanish", "espanol", "es"],
    "tr": ["تركي", "تركية", "turkish", "turkce", "tr"],
}


def detect_lang_keyword(text):
    t = text.strip().lower()
    for code, words in LANG_KEYWORDS.items():
        for w in words:
            if t == w.lower():
                return code
    return None


def T_(uid, key, **kw):
    lang = get_lang(uid)
    text = T.get(lang, T["en"]).get(key, T["en"].get(key, key))
    if kw:
        try:
            text = text.format(**kw)
        except Exception:
            pass
    return text


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error("save: " + str(e))


def get_lang(uid):
    return load_json(LANG_FILE).get(str(uid), "en")


def set_lang(uid, lang):
    d = load_json(LANG_FILE)
    d[str(uid)] = lang
    save_json(LANG_FILE, d)


def bump_counter(uid):
    d = load_json(COUNTER_FILE)
    d[str(uid)] = d.get(str(uid), 0) + 1
    save_json(COUNTER_FILE, d)
    return d[str(uid)]


def reset_counter(uid):
    d = load_json(COUNTER_FILE)
    d[str(uid)] = 0
    save_json(COUNTER_FILE, d)


def track_user(uid):
    d = load_json(STATS_FILE)
    users = d.get("users", [])
    if str(uid) not in users:
        users.append(str(uid))
        d["users"] = users
        save_json(STATS_FILE, d)


def track_download(uid, mode):
    d = load_json(STATS_FILE)
    d["total_downloads"] = d.get("total_downloads", 0) + 1
    if mode == "audio":
        d["audio_downloads"] = d.get("audio_downloads", 0) + 1
    else:
        d["video_downloads"] = d.get("video_downloads", 0) + 1
    # نحسبلك انت
    d["your_downloads"] = d.get("your_downloads", 0) + 1
    save_json(STATS_FILE, d)


def get_stats():
    d = load_json(STATS_FILE)
    return {
        "users": len(d.get("users", [])),
        "total": d.get("total_downloads", 0),
        "audio": d.get("audio_downloads", 0),
        "video": d.get("video_downloads", 0),
    }


user_downloads = defaultdict(list)
active = set()
pending = {}
ad_action = {}
ad_click = {}
sem = threading.Semaphore(MAX_CONCURRENT_DOWNLOADS)


def rate_ok(uid):
    now = datetime.now()
    hour = now - timedelta(hours=1)
    user_downloads[uid] = [t for t in user_downloads[uid] if t > hour]
    if len(user_downloads[uid]) >= RATE_LIMIT_PER_HOUR:
        return False
    user_downloads[uid].append(now)
    return True


def fmt_dur(s):
    if not s:
        return "-"
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    if h:
        return str(h) + ":" + str(m).zfill(2) + ":" + str(sec).zfill(2)
    return str(m) + ":" + str(sec).zfill(2)


def lang_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(i["name"], callback_data="lang_" + c) for c, i in LANGS.items()]
    kb.add(*btns)
    return kb


@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    track_user(uid)
    if os.path.exists(LANG_FILE) and str(uid) in load_json(LANG_FILE):
        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton(T_(uid, "change_lang"), callback_data="show_langs")],
        ])
        bot.reply_to(m, T_(uid, "welcome"), reply_markup=kb)
    else:
        bot.reply_to(m, T["en"]["choose_lang"], reply_markup=lang_keyboard())


@bot.message_handler(commands=['lang'])
def cmd_lang(m):
    bot.reply_to(m, T["en"]["choose_lang"], reply_markup=lang_keyboard())


@bot.message_handler(commands=['by'])
def cmd_by(m):
    bot.reply_to(m, "👤 Youssef Sami\n📊 Data Analyst\n\n🌐 MediaGrab Bot")


@bot.message_handler(commands=['stats'])
def cmd_stats(m):
    uid = m.from_user.id
    # حط الآيدي بتاعك هنا للأمان (سيبها فاضية = الكل يقدر يشوف)
    if ADMIN_ID and uid != ADMIN_ID:
        return
    s = get_stats()
    text = (
        "📊 *إحصائيات البوت*\n\n"
        "👥 المستخدمين: " + str(s["users"]) + "\n"
        "📥 إجمالي التحميلات: " + str(s["total"]) + "\n"
        "🎧 صوت: " + str(s["audio"]) + "\n"
        "🎬 فيديو: " + str(s["video"])
    )
    try:
        bot.reply_to(m, text, parse_mode="Markdown")
    except Exception:
        bot.reply_to(m, text)


@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.reply_to(m, T_(m.from_user.id, "welcome"))


@bot.message_handler(func=lambda m: True, content_types=['text'])
def on_msg(m):
    uid = m.from_user.id
    text = m.text.strip()

    lc = detect_lang_keyword(text)
    if lc:
        set_lang(uid, lc)
        bot.reply_to(m, T_(uid, "lang_set"))
        bot.send_message(m.chat.id, T_(uid, "change_lang"), reply_markup=lang_keyboard())
        return

    url = text
    if not dl.is_valid_url(url):
        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton(T_(uid, "change_lang"), callback_data="show_langs")],
        ])
        bot.reply_to(m, T_(uid, "invalid"), reply_markup=kb)
        return

    if uid in active:
        bot.reply_to(m, T_(uid, "busy"))
        return

    if not rate_ok(uid):
        bot.reply_to(m, T_(uid, "limit"))
        return

    msg = bot.reply_to(m, T_(uid, "checking"))

    try:
        info = dl.get_info(url)
        if not info or not isinstance(info, dict):
            bot.edit_message_text(T_(uid, "cant_fetch"), m.chat.id, msg.message_id)
            return

        title = (info.get("title") or "?")[:80]
        dur = info.get("duration", 0)

        if dur and dur > MAX_DURATION_MIN * 60:
            bot.edit_message_text(T_(uid, "too_long"), m.chat.id, msg.message_id)
            return

        pending[uid] = url

        text_out = "📹 " + title + "\n⏱ " + fmt_dur(dur) + "\n\n" + T_(uid, "choose")
        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton(T_(uid, "audio"), callback_data="a"),
             types.InlineKeyboardButton(T_(uid, "video"), callback_data="v")],
            [types.InlineKeyboardButton(T_(uid, "cancel"), callback_data="x")],
        ])
        bot.edit_message_text(text_out, m.chat.id, msg.message_id, reply_markup=kb)

    except Exception as e:
        logger.exception(e)
        bot.edit_message_text(T_(uid, "error") + str(e)[:150], m.chat.id, msg.message_id)


@bot.callback_query_handler(func=lambda c: True)
def on_cb(c):
    uid = c.from_user.id
    d = c.data
    cid = c.message.chat.id
    mid = c.message.message_id

    if d == "show_langs":
        bot.edit_message_text(T_(uid, "choose_lang"), cid, mid, reply_markup=lang_keyboard())
        return

    if d.startswith("lang_"):
        code = d[5:]
        if code in LANGS:
            set_lang(uid, code)
            bot.edit_message_text(T_(uid, "lang_set"), cid, mid)
        return

    if d == "x":
        pending.pop(uid, None)
        ad_action.pop(uid, None)
        ad_click.pop(uid, None)
        bot.edit_message_text(T_(uid, "cancelled"), cid, mid)
        return

    if d == "a":
        url = pending.get(uid)
        if not url:
            bot.edit_message_text(T_(uid, "send_link"), cid, mid)
            return
        check_ad_then_run(uid, cid, mid, url, "audio", None)
        return

    if d == "v":
        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("360p", callback_data="q360"),
             types.InlineKeyboardButton("480p", callback_data="q480"),
             types.InlineKeyboardButton("720p", callback_data="q720")],
            [types.InlineKeyboardButton("1080p", callback_data="q1080"),
             types.InlineKeyboardButton("Best", callback_data="qbest")],
            [types.InlineKeyboardButton(T_(uid, "cancel"), callback_data="x")],
        ])
        bot.edit_message_text(T_(uid, "choose_q"), cid, mid, reply_markup=kb)
        return

    if d.startswith("q"):
        q = d[1:]
        url = pending.get(uid)
        if not url:
            bot.edit_message_text(T_(uid, "send_link"), cid, mid)
            return
        check_ad_then_run(uid, cid, mid, url, "video", q)
        return

    if d == "ad_done":
        act = ad_action.pop(uid, None)
        ad_click.pop(uid, None)
        pending.pop(uid, None)
        if not act:
            bot.edit_message_text(T_(uid, "send_link"), cid, mid)
            return
        reset_counter(uid)
        bot.edit_message_text(T_(uid, "downloading"), cid, mid)
        work(cid, act["url"], act["mode"], act["q"], uid)
        return


def show_ad(uid, cid, mid, url, mode, q):
    ad_action[uid] = {"url": url, "mode": mode, "q": q}

    try:
        ad = adsgram.get_ad(uid, get_lang(uid))
    except Exception as e:
        logger.error("adsgram err: " + str(e))
        ad = None

    if not ad:
        bot.edit_message_text(T_(uid, "downloading"), cid, mid)
        work(cid, url, mode, q, uid)
        return

    text = ad.get("text", T_(uid, "ad_gate", n=AD_EVERY))
    button_text = ad.get("buttonText", "View Ad")
    button_url = ad.get("clickUrl", "")
    image_url = ad.get("imageUrl", "")

    if not button_url:
        bot.edit_message_text(T_(uid, "downloading"), cid, mid)
        work(cid, url, mode, q, uid)
        return

    kb = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton(button_text, url=button_url)],
        [types.InlineKeyboardButton("✅ Done", callback_data="ad_done")],
    ])

    try:
        if image_url:
            bot.send_photo(cid, image_url, caption=text, reply_markup=kb)
        else:
            bot.send_message(cid, text, reply_markup=kb)
    except Exception as e:
        logger.error("send ad: " + str(e))
        bot.send_message(cid, text, reply_markup=kb)


def check_ad_then_run(uid, cid, mid, url, mode, q):
    count = bump_counter(uid)

    if count >= AD_EVERY:
        show_ad(uid, cid, mid, url, mode, q)
    else:
        bot.edit_message_text(T_(uid, "downloading"), cid, mid)
        work(cid, url, mode, q, uid)


def work(cid, url, mode, q, uid):
    active.add(cid)
    path = None
    try:
        with sem:
            if mode == "audio":
                path = dl.download_audio(url, cid)
            else:
                path = dl.download_video(url, cid, q)

        if not path or not os.path.exists(path):
            bot.send_message(cid, T_(uid, "failed"))
            return

        size = os.path.getsize(path) / (1024 * 1024)
        if size > MAX_FILE_SIZE_MB:
            bot.send_message(cid, T_(uid, "too_big"))
            return

        track_download(uid, mode)
        bot.send_message(cid, T_(uid, "uploading"))
        with open(path, "rb") as f:
            if mode == "audio":
                bot.send_audio(cid, f, caption="🎧")
            else:
                bot.send_video(cid, f, caption="🎬 " + str(q) + "p", supports_streaming=True)
    except Exception as e:
        logger.exception(e)
        bot.send_message(cid, T_(uid, "error") + str(e)[:150])
    finally:
        active.discard(cid)
        if path:
            dl.cleanup(path)


if __name__ == "__main__":
    bot.infinity_polling()
