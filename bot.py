import os
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from google import genai
from google.genai import types

TOKEN = os.environ.get("TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
FIREBASE_URL = "https://sabuj-computers-default-rtdb.asia-southeast1.firebasedatabase.app"

# Setup Gemini AI if available
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Failed to init Gemini: {e}")

# Database Helpers
def get_db(path):
    try:
        res = requests.get(f"{FIREBASE_URL}/{path}.json")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error reading DB: {e}")
    return None

def put_db(path, data):
    res = requests.put(f"{FIREBASE_URL}/{path}.json", json=data)
    return res.json()
    
def patch_db(path, data):
    res = requests.patch(f"{FIREBASE_URL}/{path}.json", json=data)
    return res.json()

def get_main_keyboard():
    return [
        [InlineKeyboardButton("🎓 কোর্সসমূহ", callback_data="courses"),
         InlineKeyboardButton("💰 ফি তথ্য", callback_data="fees")],
        [InlineKeyboardButton("📝 ভর্তি তথ্য", callback_data="admission"),
         InlineKeyboardButton("🏆 ফলাফল", callback_data="results")],
        [InlineKeyboardButton("👨‍🎓 স্টুডেন্ট পোর্টাল", url="https://sabujcomputers.pro.bd/portal.html"),
         InlineKeyboardButton("📚 রিসোর্স হাব", url="https://sabujcomputers.pro.bd/resource-hub.html")],
        [InlineKeyboardButton("📢 নোটিশ বোর্ড", callback_data="notice"),
         InlineKeyboardButton("📞 যোগাযোগ", callback_data="contact")],
        [InlineKeyboardButton("🔗 অ্যাকাউন্ট লিঙ্ক করুন", callback_data="link_account")],
        [InlineKeyboardButton("🎧 অ্যাডমিনের সাথে কথা বলুন", callback_data="talk_admin")],
        [InlineKeyboardButton("🌐 মূল ওয়েবসাইট", url="https://sabujcomputers.pro.bd")]
    ]

# 1. Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message if update.message else update.callback_query.message
    text = (
        "🌿 *সবুজ কম্পিউটার্সে আপনাকে স্বাগতম!*\n\n"
        "বাগাতিপাড়া, নাটোরের সেরা BTEB অনুমোদিত কম্পিউটার প্রশিক্ষণ কেন্দ্র।\n"
        "✨ *৫+ বছরের অভিজ্ঞতা* | *১০০০+ শিক্ষার্থী* | *১০০% সার্টিফিকেট গ্যারান্টি*\n\n"
        "আমি একটি স্মার্ট AI বট। আপনি চাইলে স্বাভাবিক ভাষায় আমার সাথে কথা বলে তথ্য জানতে পারবেন।\n\n"
        "নিচের মেনু থেকে আপনার প্রয়োজনীয় সেবা বেছে নিন 👇"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(get_main_keyboard()))
    else:
        await msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(get_main_keyboard()))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")]])

    if query.data == "menu":
        await start(update, context)

    elif query.data == "courses":
        await query.edit_message_text(
            "🎓 *আমাদের কোর্সসমূহ*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ *ফাউন্ডেশন কোর্স*\n"
            "   ✅ মেয়াদ: ৬ মাস\n"
            "   ✅ সার্টিফিকেট: নিজস্ব সার্টিফিকেট\n"
            "   ✅ বিষয়: Basic Computer, MS Office, Internet\n\n"
            "2️⃣ *BTEB কোর্স*\n"
            "   ✅ মেয়াদ: ৬ মাস\n"
            "   ✅ সার্টিফিকেট: সরকারি (BTEB অনুমোদিত)\n"
            "   ✅ চাকরির বাজারে সম্পূর্ণ গ্রহণযোগ্য\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📞 ভর্তির জন্য: 01724-084350",
            parse_mode="Markdown",
            reply_markup=back_markup
        )

    elif query.data == "fees":
        await query.edit_message_text(
            "💰 *ফি সংক্রান্ত তথ্য*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎓 *ফাউন্ডেশন কোর্স:*\n"
            "   🏷️ কোর্স ফি: *৩৫০০ টাকা*\n"
            "   (বেসিক কম্পিউটার, এমএস অফিস, ইন্টারনেট)\n\n"
            "🏆 *BTEB কোর্স:*\n"
            "   🏷️ কোর্স ফি: *৪৫০০ টাকা*\n"
            "   (সরকারি সনদপ্রাপ্ত, চাকরির বাজারে ১০০% গ্রহণযোগ্য)\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💡 বিস্তারিত জানতে যোগাযোগ করুন:\n"
            "📞 01724-084350",
            parse_mode="Markdown",
            reply_markup=back_markup
        )

    elif query.data == "results":
        await query.edit_message_text(
            "🏆 *ফলাফল ও সার্টিফিকেট যাচাই*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "আপনার রেজিস্ট্রেশন নম্বর ব্যবহার করে অনলাইনে ফলাফল এবং সার্টিফিকেট যাচাই করতে পারবেন।\n\n"
            "নিচের 'ফলাফল দেখুন' বাটনে ক্লিক করে ওয়েবসাইটে গিয়ে আপনার রেজাল্ট চেক করুন।",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 ফলাফল দেখুন", url="https://sabujcomputers.pro.bd/verify.html")],
                [InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")]
            ])
        )

    elif query.data == "notice":
        notices = get_db("sabuj/notices")
        notice_text = "📢 *নোটিশ বোর্ড*\n\n━━━━━━━━━━━━━━━━━━\n"
        if notices and isinstance(notices, dict):
            # Show latest 3 notices
            sorted_notices = sorted(notices.items(), key=lambda x: x[1].get('date', ''), reverse=True)
            for i, (k, notice) in enumerate(sorted_notices[:3]):
                notice_text += f"📌 *{notice.get('title', '')}* ({notice.get('date', '')})\n"
                notice_text += f"{notice.get('details', '')}\n\n"
        else:
            notice_text += "বর্তমানে কোনো নোটিশ নেই।\n"

        await query.edit_message_text(
            notice_text,
            parse_mode="Markdown",
            reply_markup=back_markup
        )

    elif query.data == "admission":
        await query.edit_message_text(
            "📝 *ভর্তি তথ্য*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🏫 *সবুজ কম্পিউটার ট্রেনিং সেন্টার*\n"
            "📍 তমালতলা বাজার, বাগাতিপাড়া, নাটোর\n\n"
            "📋 ভর্তির জন্য যা লাগবে:\n"
            "   • জাতীয় পরিচয়পত্র / জন্ম নিবন্ধন\n"
            "   • ১ কপি পাসপোর্ট সাইজ ছবি\n"
            "   • শিক্ষাগত সনদ (প্রযোজ্য ক্ষেত্রে)\n\n"
            "⏰ অফিস সময়:\n"
            "   সকাল ৯:০০ — দুপুর ১:৩০\n"
            "   বিকেল ৪:০০ — রাত ৮:৩০\n"
            "   (শুক্রবার লাইব্রেরি বন্ধ)\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📞 01724-084350",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 অনলাইন ভর্তি ফরম", url="https://sabujcomputers.pro.bd/admission-form.html")],
                [InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")]
            ])
        )

    elif query.data == "contact":
        await query.edit_message_text(
            "📞 *যোগাযোগ করুন*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🏫 সবুজ কম্পিউটার ট্রেনিং সেন্টার\n\n"
            "📞 ফোন: 01724-084350\n"
            "✉️ ইমেইল: sssabuj007@gmail.com\n"
            "📍 তমালতলা বাজার, বাগাতিপাড়া, নাটোর\n\n"
            "⏰ সেবার সময়:\n"
            "সকাল ৯:০০ AM — রাত ৮:৩০ PM\n"
            "(শুক্রবার লাইব্রেরি বন্ধ)",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 কল করুন", url="tel:+8801724084350"),
                 InlineKeyboardButton("💬 WhatsApp", url="https://wa.me/8801724084350")],
                [InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")]
            ])
        )

    elif query.data == "link_account":
        context.user_data["awaiting"] = "link_reg"
        await query.edit_message_text(
            "🔗 *অ্যাকাউন্ট লিঙ্ক করুন*\n\n"
            "আপনার ফোন নম্বর বা রেজিস্ট্রেশন নম্বর টাইপ করে সেন্ড করুন:",
            parse_mode="Markdown",
            reply_markup=back_markup
        )

    elif query.data == "talk_admin":
        context.user_data["awaiting"] = "talk_admin"
        await query.edit_message_text(
            "🎧 *সরাসরি অ্যাডমিনের সাথে কথা বলুন*\n\n"
            "আপনার প্রশ্ন বা মেসেজটি এখন টাইপ করে সেন্ড করুন। অ্যাডমিন কিছুক্ষণের মধ্যে রিপ্লাই দেবেন।",
            parse_mode="Markdown",
            reply_markup=back_markup
        )

# Document delivery command /receipt
async def cmd_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    linked = get_db(f"sabuj/telegram_users/{chat_id}")
    if linked and "appId" in linked:
        app_data = get_db(f"sabuj/applications/{linked['appId']}")
        if not app_data:
            await update.message.reply_text("❌ ডাটাবেস থেকে তথ্য পাওয়া যায়নি।")
            return
            
        due = app_data.get("payment", {}).get("due", 0)
        total = app_data.get("payment", {}).get("total", 0)
        paid = app_data.get("payment", {}).get("paid", 0)
        name = app_data.get("personal", {}).get("nameEn", "শিক্ষার্থী")
        reg = app_data.get("regNo", "প্রযোজ্য নয়")
        
        receipt_text = (
            "🧾 *Digital Receipt / পেমেন্ট রসিদ*\n\n"
            f"নাম: {name}\n"
            f"রেজিস্ট্রেশন: {reg}\n\n"
            f"মোট ফি: ৳{total}\n"
            f"পরিশোধিত: ৳{paid}\n"
            f"বকেয়া: ৳{due}\n\n"
            "✅ *অফিসিয়াল রিসিপ্ট* (System Generated)"
        )
        await update.message.reply_text(receipt_text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ আপনার অ্যাকাউন্টটি লিঙ্ক করা নেই। অনুগ্রহ করে 'অ্যাকাউন্ট লিঙ্ক করুন' বাটনটি চাপুন।")


# Message & Command Handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    chat_id = str(update.message.chat_id)
    state = context.user_data.get("awaiting", "")
    
    # Check if admin is replying to user
    if str(chat_id) == str(ADMIN_CHAT_ID) and update.message.reply_to_message:
        orig = update.message.reply_to_message.text
        if orig and "New Support Message from" in orig:
            try:
                # Extract chat_id from the original message (format: ... from User Name (CHAT_ID):)
                target_chat_id = orig.split("(")[1].split(")")[0]
                await context.bot.send_message(chat_id=target_chat_id, text=f"🎧 *অ্যাডমিনের রিপ্লাই:*\n\n{msg}", parse_mode="Markdown")
                await update.message.reply_text("✅ রিপ্লাই পাঠানো হয়েছে।")
                return
            except Exception as e:
                print(e)
                pass
                
    # 1. Answer specific flows
    if state == "link_reg":
        apps = get_db("sabuj/applications") or {}
        found_key = None
        for key, details in apps.items():
            reg = details.get("regNo", "")
            phone = details.get("personal", {}).get("phone", "")
            if msg == reg or msg == phone:
                found_key = key
                break
        
        if found_key:
            patch_db(f"sabuj/telegram_users/{chat_id}", {"appId": found_key, "linkedAt": "now"})
            context.user_data["awaiting"] = ""
            await update.message.reply_text(
                "✅ আপনার অ্যাকাউন্ট সফলভাবে লিঙ্ক হয়েছে! 🎉\n\n"
                "এখন আপনি নিচের কমান্ডগুলো ব্যবহার করতে পারবেন:\n"
                "🔹 `/due` - বকেয়া ফি জানতে\n"
                "🔹 `/attendance` - উপস্থিতির স্ট্যাটাস জানতে\n"
                "🔹 `/receipt` - পেমেন্ট রসিদ পেতে",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ কোনো তথ্য পাওয়া যায়নি। দয়া করে সঠিক ফোন বা রেজিস্ট্রেশন নম্বর দিয়ে পুনরায় চেষ্টা করুন:")
        return

    elif state == "talk_admin":
        context.user_data["awaiting"] = ""
        user_name = update.message.from_user.first_name
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"📨 *New Support Message from {user_name} ({chat_id}):*\n\n{msg}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(e)
        await update.message.reply_text("✅ আপনার মেসেজটি অ্যাডমিনের কাছে পাঠানো হয়েছে প্রাইভেট গ্রুপে। রিপ্লাই পেলে এখানেই আপনার কাছে নোটিফিকেশন আসবে।")
        return

    # 4. Smart AI (Gemini) Integration
    if ai_client and not msg.startswith("/"):
        system_prompt = (
            "You are a helpful AI assistant for 'Sabuj Computers Training Center', located in Bagatipara, Natore. "
            "You provide polite, human-like answers in Bengali. "
            "Office hours: 9 AM to 1:30 PM & 4 PM to 8:30 PM (Friday closed). "
            "Courses: Foundation Course (6 months, 3500 BDT), BTEB Course (6 months, 4500 BDT). "
            "Phone: 01724-084350. "
            "Answer questions accurately based on this data. Keep it short and helpful. "
            "If they ask about their fee, attendance, or receipt, advise them to link their account and use commands like /due, /attendance or /receipt."
        )
        try:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=msg,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3
                )
            )
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text("দুঃখিত, একটু সার্ভার ত্রুটি হচ্ছে। অনুগ্রহ করে মেনু থেকে অপশন বেছে নিন:", reply_markup=InlineKeyboardMarkup(get_main_keyboard()))
        return
        
    await update.message.reply_text("আমি বুঝতে পারিনি। অনুগ্রহ করে মেনু থেকে অপশন বেছে নিন:", reply_markup=InlineKeyboardMarkup(get_main_keyboard()))

async def cmd_due(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    linked = get_db(f"sabuj/telegram_users/{chat_id}")
    if linked and "appId" in linked:
        app_data = get_db(f"sabuj/applications/{linked['appId']}")
        if not app_data:
            await update.message.reply_text("❌ ডাটাবেস থেকে তথ্য পাওয়া যায় নি।")
            return
            
        due = app_data.get("payment", {}).get("due", 0)
        total = app_data.get("payment", {}).get("total", 0)
        paid = app_data.get("payment", {}).get("paid", 0)
        
        await update.message.reply_text(f"💳 *ফি স্ট্যাটাস*\n\nমোট ফি: ৳{total}\nপরিশোধিত: ৳{paid}\n⚠️ *বকেয়া ফি: ৳{due}*", parse_mode="Markdown")
        
        if int(due) > 0:
            await update.message.reply_text("🔔 *Reminder:* আপনার বকেয়া ফি পরিশোধ করার জন্য অনুরোধ করা হচ্ছে।")
    else:
        await update.message.reply_text("❌ আপনার অ্যাকাউন্টটি লিঙ্ক করা নেই। অনুগ্রহ করে 'অ্যাকাউন্ট লিঙ্ক করুন' বাটনটি চাপুন।")

async def cmd_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    linked = get_db(f"sabuj/telegram_users/{chat_id}")
    if linked and "appId" in linked:
        stu_data = get_db(f"sabuj/applications/{linked['appId']}")
        if not stu_data:
            await update.message.reply_text("❌ ডাটাবেস থেকে তথ্য পাওয়া যায় নি।")
            return
            
        name = stu_data.get("personal", {}).get("nameBn", "শিক্ষার্থী")
        reg = stu_data.get("regNo", "")
        awaits = "উপস্থিতির তথ্য নিয়মিত ডাটাবেসে হালনাগাদ করা হচ্ছে। বিস্তারিত জানতে আপনার পোর্টাল চেক করুন।"
        await update.message.reply_text(f"📋 *অ্যাটেনডেন্স - {name}*\n\n{awaits}\n\n[পোর্টালে যান](https://sabujcomputers.pro.bd/portal.html)", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ আপনার অ্যাকাউন্টটি লিঙ্ক করা নেই।")

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id != str(ADMIN_CHAT_ID):
        await update.message.reply_text("❌ এই কমান্ডটি শুধু অ্যাডমিন ব্যবহার করতে পারবেন।")
        return
    
    msg = update.message.text.split(" ", 1)
    if len(msg) < 2:
        await update.message.reply_text("সঠিক নিয়ম: `/broadcast আপনাদের মেসেজ`", parse_mode="Markdown")
        return
        
    broadcast_msg = msg[1]
    users = get_db("sabuj/telegram_users")
    if not users:
        await update.message.reply_text("কোনো লিঙ্কড ইউজার পাওয়া যায়নি।")
        return
        
    success = 0
    for u_id in users.keys():
        try:
            await context.bot.send_message(chat_id=u_id, text=f"📢 *সেন্টার নোটিশ:*\n\n{broadcast_msg}", parse_mode="Markdown")
            success += 1
        except Exception:
            pass
            
    await update.message.reply_text(f"✅ সফলভাবে {success} জন শিক্ষার্থীর কাছে মেসেজ পাঠানো হয়েছে।")

async def cmd_add_notice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id != str(ADMIN_CHAT_ID):
        await update.message.reply_text("❌ এই কমান্ডটি শুধু অ্যাডমিন ব্যবহার করতে পারবেন।")
        return
        
    msg = update.message.text.split(" ", 1)
    if len(msg) < 2:
        await update.message.reply_text("সঠিক নিয়ম: `/add_notice নোটিশের বিস্তারিত বিবরণ`\n\nঅথবা টাইটেলসহ: `/add_notice টাইটেল | বিবরণ`", parse_mode="Markdown")
        return
        
    parts = msg[1].split("|", 1)
    title = parts[0].strip() if len(parts) > 1 else "নতুন নোটিশ"
    details = parts[1].strip() if len(parts) > 1 else parts[0].strip()
    
    import datetime
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    put_db(f"sabuj/notices/t{int(datetime.datetime.now().timestamp())}", {
        "title": title,
        "details": details,
        "date": date_str
    })
    
    # Also notify linked users!
    users = get_db("sabuj/telegram_users")
    success = 0
    if users:
        for u_id in users.keys():
            try:
                await context.bot.send_message(chat_id=u_id, text=f"📌 *নতুন নোটিশ: {title}*\n\n{details}\n\n(তারিখ: {date_str})", parse_mode="Markdown")
                success += 1
            except Exception:
                pass

    await update.message.reply_text(f"✅ নোটিশটি সফলভাবে ওয়েবসাইটে যুক্ত করা হয়েছে এবং {success} জনকে ব্রডকাস্ট করা হয়েছে!")

async def cmd_verify_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id != str(ADMIN_CHAT_ID):
        return
        
    msg = update.message.text.split(" ", 1)
    if len(msg) < 2:
        await update.message.reply_text("সঠিক নিয়ম: `/verify_student <RegNo/Phone>`", parse_mode="Markdown")
        return
        
    search = msg[1].strip()
    apps = get_db("sabuj/applications") or {}
    for key, data in apps.items():
        reg = str(data.get("regNo", ""))
        phone = str(data.get("personal", {}).get("phone", ""))
        if search == reg or search == phone:
            name = data.get("personal", {}).get("nameBn", "N/A")
            course = data.get("enrollment", {}).get("courseId", "N/A")
            fee_due = data.get("payment", {}).get("due", "N/A")
            
            info = f"✅ *স্টুডেন্ট ডাটা পাওয়া গেছে:*\n\nনাম: {name}\nকোর্স: {course}\nরেজিস্ট্রেশন: {reg}\nফোন: {phone}\nবকেয়া ফি: ৳{fee_due}"
            await update.message.reply_text(info, parse_mode="Markdown")
            return
            
    await update.message.reply_text("❌ কোনো স্টুডেন্ট ডাটা পাওয়া যায়নি।")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("due", cmd_due))
    app.add_handler(CommandHandler("attendance", cmd_attendance))
    app.add_handler(CommandHandler("receipt", cmd_receipt))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("add_notice", cmd_add_notice))
    app.add_handler(CommandHandler("verify_student", cmd_verify_student))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ সবুজ কম্পিউটার্স Bot چلছে... (Live Firebase + Gemini Enabled)")
    app.run_polling()

if __name__ == "__main__":
    main()
