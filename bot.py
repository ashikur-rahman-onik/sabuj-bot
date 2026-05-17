"""
╔══════════════════════════════════════════════════════╗
║     সবুজ কম্পিউটার্স — Telegram Bot (Pro Edition)   ║
║     Bug Fixed + Enhanced + Professional              ║
╚══════════════════════════════════════════════════════╝
"""

import os
import re
import time
import logging
import datetime
import functools
from collections import defaultdict

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from google import genai
from google.genai import types

# ──────────────────────────────────────────────
# 🔧 Logging Setup
# ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("SabujBot")

# ──────────────────────────────────────────────
# ⚙️ Environment & Constants
# ──────────────────────────────────────────────
TOKEN           = os.environ.get("TOKEN", "")
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
ADMIN_CHAT_ID   = os.environ.get("ADMIN_CHAT_ID", "")
FIREBASE_URL    = os.environ.get("FIREBASE_URL", "https://sabuj-computers-default-rtdb.asia-southeast1.firebasedatabase.app")
FIREBASE_SECRET = os.environ.get("FIREBASE_SECRET", "")

# Validate critical env vars on startup
if not TOKEN:
    raise EnvironmentError("❌ TOKEN environment variable is not set!")
if not ADMIN_CHAT_ID:
    logger.warning("⚠️  ADMIN_CHAT_ID not set — admin commands will be disabled.")

# Rate limiting config
RATE_LIMIT_CALLS    = 5    # max messages
RATE_LIMIT_PERIOD   = 30   # per N seconds

# Gemini conversation history length
MAX_HISTORY_TURNS = 6

# ──────────────────────────────────────────────
# 🤖 Gemini AI Setup
# ──────────────────────────────────────────────
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("✅ Gemini AI client initialized.")
    except Exception as e:
        logger.error(f"Failed to init Gemini: {e}")

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI assistant for 'Sabuj Computers Training Center' (সবুজ কম্পিউটার ট্রেনিং সেন্টার), "
    "located at Tamaltala Bazar, Bagatipara, Natore, Bangladesh. "
    "Always respond in polite, friendly Bengali. "
    "Always greet with 'আসসালামু আলাইকুম' — never use 'নমস্কার'. "
    "Office hours: Sat–Thu 9:00 AM–1:30 PM & 4:00 PM–8:30 PM (Friday closed). "
    "Courses: (1) Foundation Course — 6 months, ৳3500. (2) BTEB Course — 6 months, ৳4500 (Govt approved). "
    "Phone: 01724-084350. Email: sssabuj007@gmail.com. Website: https://sabujcomputers.pro.bd. "
    "Keep answers concise and helpful. "
    "If the user asks about their fee, attendance, or receipt, tell them to use /due, /attendance, or /receipt "
    "after linking their account via the '🔗 অ্যাকাউন্ট লিঙ্ক করুন' button. "
    "Do not make up information. If you don't know something, say so politely."
)

# ──────────────────────────────────────────────
# 🗄️ Firebase Helpers
# ──────────────────────────────────────────────
def _auth() -> str:
    return f"?auth={FIREBASE_SECRET}" if FIREBASE_SECRET else ""

def get_db(path: str):
    """GET a Firebase path. Returns parsed JSON or None."""
    try:
        url = f"{FIREBASE_URL}/{path}.json{_auth()}"
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            return res.json()
        logger.warning(f"GET failed [{path}]: {res.status_code} — {res.text[:100]}")
    except requests.exceptions.Timeout:
        logger.error(f"GET timeout [{path}]")
    except Exception as e:
        logger.error(f"GET error [{path}]: {e}")
    return None

def put_db(path: str, data: dict):
    """PUT (overwrite) a Firebase path."""
    try:
        url = f"{FIREBASE_URL}/{path}.json{_auth()}"
        res = requests.put(url, json=data, timeout=8)
        logger.info(f"PUT [{path}] → {res.status_code}")
        return res.json()
    except Exception as e:
        logger.error(f"PUT error [{path}]: {e}")
    return None

def patch_db(path: str, data: dict):
    """PATCH (merge) a Firebase path."""
    try:
        url = f"{FIREBASE_URL}/{path}.json{_auth()}"
        res = requests.patch(url, json=data, timeout=8)
        logger.info(f"PATCH [{path}] → {res.status_code}")
        return res.json()
    except Exception as e:
        logger.error(f"PATCH error [{path}]: {e}")
    return None

def delete_db(path: str):
    """DELETE a Firebase path."""
    try:
        url = f"{FIREBASE_URL}/{path}.json{_auth()}"
        res = requests.delete(url, timeout=8)
        logger.info(f"DELETE [{path}] → {res.status_code}")
        return res.status_code == 200
    except Exception as e:
        logger.error(f"DELETE error [{path}]: {e}")
    return False

def now_str() -> str:
    """Current datetime as formatted string."""
    return datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")

def now_ts() -> int:
    """Current Unix timestamp as int."""
    return int(datetime.datetime.now().timestamp())

# ──────────────────────────────────────────────
# 🛡️ Security Helpers
# ──────────────────────────────────────────────
_rate_limit_store: dict = defaultdict(list)

def is_admin(chat_id: str) -> bool:
    """Check if a chat_id belongs to the configured admin."""
    if not ADMIN_CHAT_ID:
        return False
    return str(chat_id) == str(ADMIN_CHAT_ID)

def is_rate_limited(chat_id: str) -> bool:
    """Simple in-memory rate limiter. Returns True if user is over the limit."""
    now = time.time()
    calls = _rate_limit_store[chat_id]
    # Remove timestamps outside the window
    calls = [t for t in calls if now - t < RATE_LIMIT_PERIOD]
    _rate_limit_store[chat_id] = calls
    if len(calls) >= RATE_LIMIT_CALLS:
        return True
    _rate_limit_store[chat_id].append(now)
    return False

# ──────────────────────────────────────────────
# 🎹 Keyboards
# ──────────────────────────────────────────────
def get_main_keyboard() -> list:
    return [
        [
            InlineKeyboardButton("🎓 কোর্সসমূহ",   callback_data="courses"),
            InlineKeyboardButton("💰 ফি তথ্য",      callback_data="fees"),
        ],
        [
            InlineKeyboardButton("📝 ভর্তি তথ্য",   callback_data="admission"),
            InlineKeyboardButton("🏆 ফলাফল",        callback_data="results"),
        ],
        [
            InlineKeyboardButton("👨‍🎓 স্টুডেন্ট পোর্টাল", url="https://sabujcomputers.pro.bd/portal.html"),
            InlineKeyboardButton("📚 রিসোর্স হাব",       url="https://sabujcomputers.pro.bd/resource-hub.html"),
        ],
        [
            InlineKeyboardButton("📢 নোটিশ বোর্ড", callback_data="notice"),
            InlineKeyboardButton("📞 যোগাযোগ",     callback_data="contact"),
        ],
        [InlineKeyboardButton("🔗 অ্যাকাউন্ট লিঙ্ক করুন", callback_data="link_account")],
        [InlineKeyboardButton("🎧 অ্যাডমিনের সাথে কথা বলুন", callback_data="talk_admin")],
        [InlineKeyboardButton("🌐 মূল ওয়েবসাইট", url="https://sabujcomputers.pro.bd")],
    ]

def back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")]])

# ──────────────────────────────────────────────
# 📤 Utility: send typing indicator
# ──────────────────────────────────────────────
async def typing(update: Update):
    try:
        await update.effective_chat.send_action(ChatAction.TYPING)
    except Exception:
        pass

# ──────────────────────────────────────────────
# 📌 /start & /menu
# ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)

    apps        = get_db("sabuj/applications")
    total_students = len(apps) if apps and isinstance(apps, dict) else 1000
    bot_settings   = get_db("sabuj/bot_settings") or {}
    custom_desc    = bot_settings.get("welcome_text", "")

    desc_text = custom_desc or (
        f"✨ *৫+ বছরের অভিজ্ঞতা* | *{total_students}+ শিক্ষার্থী* | *১০০% সার্টিফিকেট গ্যারান্টি*"
    )

    text = (
        "🌿 *সবুজ কম্পিউটার্সে আপনাকে স্বাগতম!*\n\n"
        "বাগাতিপাড়া, নাটোরের সেরা BTEB অনুমোদিত কম্পিউটার প্রশিক্ষণ কেন্দ্র।\n"
        f"{desc_text}\n\n"
        "আমি একটি স্মার্ট AI বট। স্বাভাবিক ভাষায় কথা বললেও আমি বুঝতে পারব।\n\n"
        "নিচের মেনু থেকে আপনার প্রয়োজনীয় সেবা বেছে নিন 👇"
    )
    markup = InlineKeyboardMarkup(get_main_keyboard())

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
    else:
        await update.callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

# ──────────────────────────────────────────────
# ❓ /help
# ──────────────────────────────────────────────
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *ব্যবহারযোগ্য কমান্ডসমূহ*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👤 *শিক্ষার্থী কমান্ড:*\n"
        "🔹 /start — মূল মেনু খুলুন\n"
        "🔹 /menu — মেনু আবার দেখুন\n"
        "🔹 /due — বকেয়া ফি দেখুন\n"
        "🔹 /receipt — পেমেন্ট রসিদ দেখুন\n"
        "🔹 /attendance — উপস্থিতি স্ট্যাটাস\n"
        "🔹 /unlink — অ্যাকাউন্ট আনলিঙ্ক করুন\n"
        "🔹 /help — এই সাহায্য বার্তা\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 *টিপস:* অ্যাকাউন্ট লিঙ্ক না করলে /due, /receipt, /attendance কাজ করবে না।\n\n"
        "📞 সাহায্যের জন্য: 01724-084350"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(get_main_keyboard()))

# ──────────────────────────────────────────────
# 🎛️ Button Handler
# ──────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu":
        await start(update, context)

    elif data == "courses":
        courses = get_db("sabuj/courses")
        if courses and isinstance(courses, dict):
            text = "🎓 *আমাদের কোর্সসমূহ*\n\n━━━━━━━━━━━━━━━━━━\n"
            for i, (k, c) in enumerate(courses.items(), 1):
                text += (
                    f"{i}️⃣ *{c.get('name', 'কোর্স')}*\n"
                    f"   ✅ মেয়াদ: {c.get('duration', 'N/A')}\n"
                    f"   ✅ ফি: ৳{c.get('fee', 'N/A')}\n"
                    f"   ✅ সার্টিফিকেট: {c.get('cert', 'N/A')}\n\n"
                )
        else:
            text = (
                "🎓 *আমাদের কোর্সসমূহ*\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "1️⃣ *ফাউন্ডেশন কোর্স*\n"
                "   ✅ মেয়াদ: ৬ মাস\n"
                "   ✅ ফি: ৳৩,৫০০\n"
                "   ✅ বিষয়: Basic Computer, MS Office, Internet\n"
                "   ✅ সার্টিফিকেট: নিজস্ব\n\n"
                "2️⃣ *BTEB কোর্স*\n"
                "   ✅ মেয়াদ: ৬ মাস\n"
                "   ✅ ফি: ৳৪,৫০০\n"
                "   ✅ সার্টিফিকেট: সরকারি (BTEB অনুমোদিত)\n"
                "   ✅ চাকরির বাজারে ১০০% গ্রহণযোগ্য\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "📞 ভর্তির জন্য: 01724-084350"
            )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif data == "fees":
        await query.edit_message_text(
            "💰 *ফি সংক্রান্ত তথ্য*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎓 *ফাউন্ডেশন কোর্স:*\n"
            "   🏷️ কোর্স ফি: *৳৩,৫০০*\n"
            "   _(বেসিক কম্পিউটার, এমএস অফিস, ইন্টারনেট)_\n\n"
            "🏆 *BTEB কোর্স:*\n"
            "   🏷️ কোর্স ফি: *৳৪,৫০০*\n"
            "   _(সরকারি সনদপ্রাপ্ত, চাকরির বাজারে ১০০% গ্রহণযোগ্য)_\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💡 বিস্তারিত জানতে: 📞 01724-084350",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button(),
        )

    elif data == "results":
        await query.edit_message_text(
            "🏆 *ফলাফল ও সার্টিফিকেট যাচাই*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "আপনার রেজিস্ট্রেশন নম্বর দিয়ে অনলাইনে ফলাফল ও সার্টিফিকেট যাচাই করুন।\n\n"
            "নিচের বাটনে ক্লিক করুন 👇",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 ফলাফল দেখুন", url="https://sabujcomputers.pro.bd/verify.html")],
                [InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")],
            ]),
        )

    elif data == "notice":
        await typing(update)
        notices = get_db("sabuj/notices")
        notice_text = "📢 *নোটিশ বোর্ড*\n\n━━━━━━━━━━━━━━━━━━\n"
        if notices and isinstance(notices, dict):
            sorted_notices = sorted(
                notices.items(),
                key=lambda x: x[1].get("date", ""),
                reverse=True,
            )
            for _, notice in sorted_notices[:5]:
                notice_text += (
                    f"📌 *{notice.get('title', 'নোটিশ')}*\n"
                    f"🗓️ _{notice.get('date', '')}_\n"
                    f"{notice.get('details', '')}\n\n"
                )
        else:
            notice_text += "বর্তমানে কোনো নোটিশ নেই।\n"
        await query.edit_message_text(notice_text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button())

    elif data == "admission":
        await query.edit_message_text(
            "📝 *ভর্তি তথ্য*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🏫 *সবুজ কম্পিউটার ট্রেনিং সেন্টার*\n"
            "📍 তমালতলা বাজার, বাগাতিপাড়া, নাটোর\n\n"
            "📋 *ভর্তির জন্য যা লাগবে:*\n"
            "   • জাতীয় পরিচয়পত্র / জন্ম নিবন্ধন\n"
            "   • ১ কপি পাসপোর্ট সাইজ ছবি\n"
            "   • শিক্ষাগত সনদ (প্রযোজ্য ক্ষেত্রে)\n\n"
            "⏰ *অফিস সময়:*\n"
            "   সকাল ৯:০০ — দুপুর ১:৩০\n"
            "   বিকেল ৪:০০ — রাত ৮:৩০\n"
            "   _(শুক্রবার বন্ধ)_\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📞 01724-084350",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 অনলাইন ভর্তি ফরম", url="https://sabujcomputers.pro.bd/admission-form.html")],
                [InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")],
            ]),
        )

    elif data == "contact":
        await query.edit_message_text(
            "📞 *যোগাযোগ করুন*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🏫 *সবুজ কম্পিউটার ট্রেনিং সেন্টার*\n\n"
            "📞 ফোন: 01724-084350\n"
            "✉️ ইমেইল: sssabuj007@gmail.com\n"
            "📍 তমালতলা বাজার, বাগাতিপাড়া, নাটোর\n\n"
            "⏰ সেবার সময়:\n"
            "   শনি–বৃহস্পতি: সকাল ৯:০০ — রাত ৮:৩০\n"
            "   _(শুক্রবার বন্ধ)_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 WhatsApp-এ মেসেজ দিন", url="https://wa.me/8801724084350")],
                [InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")],
            ]),
        )

    elif data == "link_account":
        context.user_data["awaiting"] = "link_reg"
        await query.edit_message_text(
            "🔗 *অ্যাকাউন্ট লিঙ্ক করুন*\n\n"
            "আপনার *ফোন নম্বর* অথবা *রেজিস্ট্রেশন নম্বর* টাইপ করে সেন্ড করুন:\n\n"
            "_(উদাহরণ: 01724084350 বা SC-2024-001)_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button(),
        )

    elif data == "talk_admin":
        context.user_data["awaiting"] = "talk_admin"
        await query.edit_message_text(
            "🎧 *সরাসরি অ্যাডমিনের সাথে কথা বলুন*\n\n"
            "আপনার প্রশ্ন বা মেসেজটি এখন টাইপ করে সেন্ড করুন।\n"
            "অ্যাডমিন কিছুক্ষণের মধ্যে রিপ্লাই দেবেন। ⏳",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button(),
        )

# ──────────────────────────────────────────────
# 💬 Message Handler (AI + State Machine)
# ──────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg      = update.message.text.strip()
    chat_id  = str(update.message.chat_id)
    state    = context.user_data.get("awaiting", "")
    user     = update.message.from_user

    # ── Rate limit (skip for admin) ──
    if not is_admin(chat_id) and is_rate_limited(chat_id):
        await update.message.reply_text(
            "⏳ একটু থামুন! অনেক দ্রুত মেসেজ পাঠাচ্ছেন। কিছুক্ষণ পর আবার চেষ্টা করুন।"
        )
        return

    # ── Admin replying to a support message ──
    if is_admin(chat_id) and update.message.reply_to_message:
        orig_text = update.message.reply_to_message.text or ""
        # Structured tag: [CHATID:123456789]
        match = re.search(r"\[CHATID:(\d+)\]", orig_text)
        if match:
            target_id = match.group(1)
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"🎧 *অ্যাডমিনের রিপ্লাই:*\n\n{msg}",
                    parse_mode=ParseMode.MARKDOWN,
                )
                await update.message.reply_text("✅ রিপ্লাই সফলভাবে পাঠানো হয়েছে।")
            except Exception as e:
                logger.error(f"Admin reply failed: {e}")
                await update.message.reply_text(f"❌ রিপ্লাই পাঠানো যায়নি: {e}")
            return

    # ── State: Account Linking ──
    if state == "link_reg":
        await typing(update)
        apps = get_db("sabuj/applications") or {}
        found_key = None
        for key, details in apps.items():
            reg   = str(details.get("regNo", ""))
            phone = str(details.get("personal", {}).get("phone", ""))
            if msg == reg or msg == phone:
                found_key = key
                break

        if found_key:
            patch_db(
                f"sabuj/telegram_users/{chat_id}",
                {
                    "appId":        found_key,
                    "linkedAt":     datetime.datetime.now().isoformat(),
                    "telegramName": user.full_name,
                    "username":     user.username or "",
                },
            )
            context.user_data["awaiting"] = ""
            await update.message.reply_text(
                "✅ *অ্যাকাউন্ট সফলভাবে লিঙ্ক হয়েছে!* 🎉\n\n"
                "এখন আপনি নিচের কমান্ডগুলো ব্যবহার করতে পারবেন:\n\n"
                "🔹 /due — বকেয়া ফি জানতে\n"
                "🔹 /attendance — উপস্থিতির স্ট্যাটাস\n"
                "🔹 /receipt — পেমেন্ট রসিদ\n"
                "🔹 /unlink — অ্যাকাউন্ট আনলিঙ্ক",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(get_main_keyboard()),
            )
        else:
            await update.message.reply_text(
                "❌ তথ্য পাওয়া যায়নি।\n\n"
                "সঠিক *ফোন নম্বর* বা *রেজিস্ট্রেশন নম্বর* দিয়ে আবার চেষ্টা করুন।\n"
                "সমস্যা হলে সরাসরি যোগাযোগ করুন: 📞 01724-084350",
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    # ── State: Talk to Admin ──
    if state == "talk_admin":
        context.user_data["awaiting"] = ""
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=(
                        f"📨 *নতুন সাপোর্ট মেসেজ*\n\n"
                        f"👤 নাম: {user.full_name}\n"
                        f"🆔 Username: @{user.username or 'নেই'}\n"
                        f"[CHATID:{chat_id}]\n\n"
                        f"💬 মেসেজ:\n{msg}"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                await update.message.reply_text(
                    "✅ আপনার মেসেজ অ্যাডমিনের কাছে পাঠানো হয়েছে।\n"
                    "রিপ্লাই পেলে এখানেই নোটিফিকেশন আসবে। ⏳"
                )
            except Exception as e:
                logger.error(f"Failed to forward to admin: {e}")
                await update.message.reply_text(
                    "❌ মেসেজ পাঠাতে সমস্যা হয়েছে। সরাসরি যোগাযোগ করুন: 📞 01724-084350"
                )
        else:
            await update.message.reply_text(
                "⚠️ অ্যাডমিন কনফিগার করা নেই। সরাসরি যোগাযোগ করুন: 📞 01724-084350"
            )
        return

    # ── Gemini AI ──
    if ai_client and not msg.startswith("/"):
        await typing(update)
        bot_settings  = get_db("sabuj/bot_settings") or {}
        system_prompt = bot_settings.get("system_prompt", "") or DEFAULT_SYSTEM_PROMPT

        # Build conversation history (multi-turn)
        history: list = context.user_data.get("chat_history", [])
        history.append({"role": "user", "parts": [{"text": msg}]})

        try:
            response = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.35,
                    max_output_tokens=512,
                ),
            )
            reply = response.text.strip()
            # Save assistant turn to history
            history.append({"role": "model", "parts": [{"text": reply}]})
            # Keep only last MAX_HISTORY_TURNS turns (user+model pairs)
            if len(history) > MAX_HISTORY_TURNS * 2:
                history = history[-(MAX_HISTORY_TURNS * 2):]
            context.user_data["chat_history"] = history

            await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            await update.message.reply_text(
                "⚠️ দুঃখিত, AI সার্ভারে সমস্যা হচ্ছে। মেনু থেকে সেবা বেছে নিন:",
                reply_markup=InlineKeyboardMarkup(get_main_keyboard()),
            )
        return

    await update.message.reply_text(
        "আমি বুঝতে পারিনি। নিচের মেনু থেকে সেবা বেছে নিন:",
        reply_markup=InlineKeyboardMarkup(get_main_keyboard()),
    )

# ──────────────────────────────────────────────
# 💳 /due — Fee Status
# ──────────────────────────────────────────────
async def cmd_due(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    chat_id = str(update.message.chat_id)
    linked  = get_db(f"sabuj/telegram_users/{chat_id}")

    if not (linked and "appId" in linked):
        await update.message.reply_text(
            "❌ অ্যাকাউন্ট লিঙ্ক করা নেই।\n'🔗 অ্যাকাউন্ট লিঙ্ক করুন' বাটনটি চাপুন।",
            reply_markup=InlineKeyboardMarkup(get_main_keyboard()),
        )
        return

    app_data = get_db(f"sabuj/applications/{linked['appId']}")
    if not app_data:
        await update.message.reply_text("❌ ডাটাবেস থেকে তথ্য পাওয়া যায়নি।")
        return

    payment = app_data.get("payment", {})
    total   = payment.get("total", 0)
    paid    = payment.get("paid", 0)
    due     = payment.get("due", 0)
    name    = app_data.get("personal", {}).get("nameBn", "শিক্ষার্থী")

    status_icon = "✅" if int(due) == 0 else "⚠️"
    text = (
        f"💳 *ফি স্ট্যাটাস — {name}*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📊 মোট ফি:        ৳{total}\n"
        f"✅ পরিশোধিত:    ৳{paid}\n"
        f"{status_icon} বকেয়া ফি:     ৳{due}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    if int(due) > 0:
        await update.message.reply_text(
            "🔔 *রিমাইন্ডার:* দয়া করে বকেয়া ফি দ্রুত পরিশোধ করুন।\n"
            "📞 যোগাযোগ: 01724-084350",
            parse_mode=ParseMode.MARKDOWN,
        )

# ──────────────────────────────────────────────
# 📋 /attendance
# ──────────────────────────────────────────────
async def cmd_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    chat_id = str(update.message.chat_id)
    linked  = get_db(f"sabuj/telegram_users/{chat_id}")

    if not (linked and "appId" in linked):
        await update.message.reply_text(
            "❌ অ্যাকাউন্ট লিঙ্ক করা নেই।",
            reply_markup=InlineKeyboardMarkup(get_main_keyboard()),
        )
        return

    stu_data = get_db(f"sabuj/applications/{linked['appId']}")
    if not stu_data:
        await update.message.reply_text("❌ ডাটাবেস থেকে তথ্য পাওয়া যায়নি।")
        return

    name       = stu_data.get("personal", {}).get("nameBn", "শিক্ষার্থী")
    attendance = stu_data.get("attendance", {})

    if attendance and isinstance(attendance, dict):
        present = attendance.get("present", 0)
        absent  = attendance.get("absent", 0)
        total   = present + absent
        pct     = round((present / total) * 100) if total > 0 else 0
        text = (
            f"📋 *অ্যাটেনডেন্স — {name}*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"✅ উপস্থিত: {present} দিন\n"
            f"❌ অনুপস্থিত: {absent} দিন\n"
            f"📊 হাজিরা: {pct}%\n"
            "━━━━━━━━━━━━━━━━━━"
        )
    else:
        text = (
            f"📋 *অ্যাটেনডেন্স — {name}*\n\n"
            "উপস্থিতির তথ্য নিয়মিত আপডেট হচ্ছে।\n"
            "বিস্তারিত পোর্টালে দেখুন।"
        )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 পোর্টালে যান", url="https://sabujcomputers.pro.bd/portal.html")]
        ]),
    )

# ──────────────────────────────────────────────
# 🧾 /receipt
# ──────────────────────────────────────────────
async def cmd_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await typing(update)
    chat_id = str(update.message.chat_id)
    linked  = get_db(f"sabuj/telegram_users/{chat_id}")

    if not (linked and "appId" in linked):
        await update.message.reply_text(
            "❌ অ্যাকাউন্ট লিঙ্ক করা নেই।",
            reply_markup=InlineKeyboardMarkup(get_main_keyboard()),
        )
        return

    app_data = get_db(f"sabuj/applications/{linked['appId']}")
    if not app_data:
        await update.message.reply_text("❌ ডাটাবেস থেকে তথ্য পাওয়া যায়নি।")
        return

    payment = app_data.get("payment", {})
    name    = app_data.get("personal", {}).get("nameEn", "Student")
    reg     = app_data.get("regNo", "N/A")
    total   = payment.get("total", 0)
    paid    = payment.get("paid", 0)
    due     = payment.get("due", 0)

    receipt = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🧾 *DIGITAL RECEIPT*\n"
        "   সবুজ কম্পিউটার ট্রেনিং সেন্টার\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 তারিখ:          {now_str()}\n"
        f"👤 নাম:            {name}\n"
        f"🆔 রেজিস্ট্রেশন: {reg}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 মোট ফি:       ৳{total}\n"
        f"✅ পরিশোধিত:   ৳{paid}\n"
        f"⚠️ বকেয়া:        ৳{due}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ System Generated | Official Receipt"
    )
    await update.message.reply_text(receipt, parse_mode=ParseMode.MARKDOWN)

# ──────────────────────────────────────────────
# 🔓 /unlink
# ──────────────────────────────────────────────
async def cmd_unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    linked  = get_db(f"sabuj/telegram_users/{chat_id}")
    if linked:
        delete_db(f"sabuj/telegram_users/{chat_id}")
        await update.message.reply_text(
            "✅ আপনার অ্যাকাউন্ট সফলভাবে আনলিঙ্ক করা হয়েছে।\n"
            "পুনরায় লিঙ্ক করতে মেনু থেকে '🔗 অ্যাকাউন্ট লিঙ্ক করুন' চাপুন।",
            reply_markup=InlineKeyboardMarkup(get_main_keyboard()),
        )
    else:
        await update.message.reply_text("⚠️ আপনার অ্যাকাউন্ট আগে থেকেই লিঙ্ক করা নেই।")

# ──────────────────────────────────────────────
# 📢 /broadcast (Admin only)
# ──────────────────────────────────────────────
async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if not is_admin(chat_id):
        await update.message.reply_text("❌ এই কমান্ডটি শুধু অ্যাডমিন ব্যবহার করতে পারবেন।")
        return

    parts = update.message.text.split(" ", 1)
    if len(parts) < 2:
        await update.message.reply_text(
            "সঠিক নিয়ম: `/broadcast আপনার মেসেজ`", parse_mode=ParseMode.MARKDOWN
        )
        return

    broadcast_msg = parts[1]
    users = get_db("sabuj/telegram_users")
    if not users:
        await update.message.reply_text("কোনো লিঙ্কড ইউজার পাওয়া যায়নি।")
        return

    success, failed = 0, 0
    for u_id in users.keys():
        try:
            await context.bot.send_message(
                chat_id=u_id,
                text=f"📢 *সেন্টার থেকে বিজ্ঞপ্তি:*\n\n{broadcast_msg}",
                parse_mode=ParseMode.MARKDOWN,
            )
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📊 *ব্রডকাস্ট রিপোর্ট:*\n\n"
        f"✅ সফল: {success} জন\n"
        f"❌ ব্যর্থ: {failed} জন",
        parse_mode=ParseMode.MARKDOWN,
    )

# ──────────────────────────────────────────────
# 📌 /add_notice (Admin only)
# ──────────────────────────────────────────────
async def cmd_add_notice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if not is_admin(chat_id):
        await update.message.reply_text("❌ এই কমান্ডটি শুধু অ্যাডমিন ব্যবহার করতে পারবেন।")
        return

    parts = update.message.text.split(" ", 1)
    if len(parts) < 2:
        await update.message.reply_text(
            "সঠিক নিয়ম:\n`/add_notice টাইটেল | বিবরণ`\n\nঅথবা:\n`/add_notice বিবরণ`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    segments = parts[1].split("|", 1)
    title   = segments[0].strip() if len(segments) > 1 else "নতুন নোটিশ"
    details = segments[1].strip() if len(segments) > 1 else segments[0].strip()
    date_str = now_str()

    put_db(
        f"sabuj/notices/t{now_ts()}",
        {"title": title, "details": details, "date": date_str},
    )

    # Notify all linked users
    users = get_db("sabuj/telegram_users")
    success, failed = 0, 0
    if users:
        for u_id in users.keys():
            try:
                await context.bot.send_message(
                    chat_id=u_id,
                    text=f"📌 *নতুন নোটিশ: {title}*\n\n{details}\n\n🗓️ _{date_str}_",
                    parse_mode=ParseMode.MARKDOWN,
                )
                success += 1
            except Exception:
                failed += 1

    await update.message.reply_text(
        f"✅ নোটিশ সংরক্ষিত এবং {success} জনকে পাঠানো হয়েছে।"
        + (f" ({failed} জনের কাছে পৌঁছানো যায়নি।)" if failed else "")
    )

# ──────────────────────────────────────────────
# 🗑️ /delete_notice (Admin only)
# ──────────────────────────────────────────────
async def cmd_delete_notice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if not is_admin(chat_id):
        return

    parts = update.message.text.split(" ", 1)
    if len(parts) < 2:
        # List notices with their keys
        notices = get_db("sabuj/notices")
        if not notices or not isinstance(notices, dict):
            await update.message.reply_text("কোনো নোটিশ নেই।")
            return
        text = "📋 *নোটিশ তালিকা (key সহ):*\n\n"
        for key, n in list(notices.items())[:10]:
            text += f"🔑 `{key}` — {n.get('title','')}\n"
        text += "\n`/delete_notice <key>` দিয়ে মুছুন"
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    key = parts[1].strip()
    if delete_db(f"sabuj/notices/{key}"):
        await update.message.reply_text(f"✅ নোটিশ `{key}` মুছে ফেলা হয়েছে।", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ মুছতে সমস্যা হয়েছে। key টি সঠিক কিনা দেখুন।")

# ──────────────────────────────────────────────
# 🔍 /verify_student (Admin only)
# ──────────────────────────────────────────────
async def cmd_verify_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if not is_admin(chat_id):
        return

    parts = update.message.text.split(" ", 1)
    if len(parts) < 2:
        await update.message.reply_text(
            "সঠিক নিয়ম: `/verify_student <RegNo বা Phone>`", parse_mode=ParseMode.MARKDOWN
        )
        return

    search = parts[1].strip()
    apps   = get_db("sabuj/applications") or {}

    for key, data in apps.items():
        reg   = str(data.get("regNo", ""))
        phone = str(data.get("personal", {}).get("phone", ""))
        if search == reg or search == phone:
            name    = data.get("personal", {}).get("nameBn", "N/A")
            name_en = data.get("personal", {}).get("nameEn", "N/A")
            course  = data.get("enrollment", {}).get("courseId", "N/A")
            fee_due = data.get("payment", {}).get("due", "N/A")
            fee_paid= data.get("payment", {}).get("paid", "N/A")

            info = (
                "✅ *স্টুডেন্ট তথ্য পাওয়া গেছে*\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"👤 নাম (বাংলা): {name}\n"
                f"👤 নাম (English): {name_en}\n"
                f"🆔 রেজিস্ট্রেশন: {reg}\n"
                f"📞 ফোন: {phone}\n"
                f"🎓 কোর্স: {course}\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"✅ পরিশোধিত: ৳{fee_paid}\n"
                f"⚠️ বকেয়া: ৳{fee_due}"
            )
            await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)
            return

    await update.message.reply_text("❌ কোনো স্টুডেন্ট ডাটা পাওয়া যায়নি।")

# ──────────────────────────────────────────────
# 📊 /stats (Admin only)
# ──────────────────────────────────────────────
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if not is_admin(chat_id):
        return

    await typing(update)
    apps    = get_db("sabuj/applications") or {}
    users   = get_db("sabuj/telegram_users") or {}
    notices = get_db("sabuj/notices") or {}

    total_apps    = len(apps)
    linked_users  = len(users)
    total_notices = len(notices)

    # Fee stats
    total_due  = sum(a.get("payment", {}).get("due", 0) for a in apps.values() if isinstance(a, dict))
    total_paid = sum(a.get("payment", {}).get("paid", 0) for a in apps.values() if isinstance(a, dict))

    text = (
        "📊 *বট পরিসংখ্যান*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👨‍🎓 মোট শিক্ষার্থী:  {total_apps}\n"
        f"🔗 লিঙ্কড ইউজার:  {linked_users}\n"
        f"📢 মোট নোটিশ:    {total_notices}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"✅ মোট পরিশোধিত: ৳{total_paid}\n"
        f"⚠️ মোট বকেয়া:    ৳{total_due}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🕐 আপডেট: {now_str()}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ──────────────────────────────────────────────
# ⚙️ Bot Commands Registration
# ──────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler — suppresses known harmless errors, logs the rest."""
    from telegram.error import Conflict, NetworkError, TimedOut
    err = context.error
    if isinstance(err, Conflict):
        logger.warning("⚠️  Conflict: পুরনো instance বন্ধ হচ্ছে, কিছুক্ষণের মধ্যে ঠিক হবে।")
    elif isinstance(err, (NetworkError, TimedOut)):
        logger.warning(f"🌐 Network সমস্যা (retry হবে): {err}")
    else:
        logger.error(f"❌ Unexpected error: {err}", exc_info=context.error)

async def post_init(application):
    """Set bot command list shown in Telegram menu."""
    commands = [
        BotCommand("start",    "মূল মেনু খুলুন"),
        BotCommand("menu",     "মেনু দেখুন"),
        BotCommand("due",      "বকেয়া ফি দেখুন"),
        BotCommand("receipt",  "পেমেন্ট রসিদ"),
        BotCommand("attendance","উপস্থিতি দেখুন"),
        BotCommand("unlink",   "অ্যাকাউন্ট আনলিঙ্ক"),
        BotCommand("help",     "সাহায্য"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot commands registered.")

# ──────────────────────────────────────────────
# 🚀 Main
# ──────────────────────────────────────────────
def main():
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    # User commands
    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("menu",       start))
    app.add_handler(CommandHandler("help",       cmd_help))
    app.add_handler(CommandHandler("due",        cmd_due))
    app.add_handler(CommandHandler("attendance", cmd_attendance))
    app.add_handler(CommandHandler("receipt",    cmd_receipt))
    app.add_handler(CommandHandler("unlink",     cmd_unlink))

    # Admin commands
    app.add_handler(CommandHandler("broadcast",      cmd_broadcast))
    app.add_handler(CommandHandler("add_notice",     cmd_add_notice))
    app.add_handler(CommandHandler("delete_notice",  cmd_delete_notice))
    app.add_handler(CommandHandler("verify_student", cmd_verify_student))
    app.add_handler(CommandHandler("stats",          cmd_stats))

    # Callback & messages
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Global error handler
    app.add_error_handler(error_handler)

    logger.info("🚀 সবুজ কম্পিউটার্স Bot চালু হচ্ছে... (Firebase + Gemini AI)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
