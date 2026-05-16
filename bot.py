import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎓 কোর্সসমূহ", callback_data="courses"),
         InlineKeyboardButton("💰 ফি তথ্য", callback_data="fees")],
        [InlineKeyboardButton("📢 নোটিশ বোর্ড", callback_data="notice"),
         InlineKeyboardButton("📝 ভর্তি তথ্য", callback_data="admission")],
        [InlineKeyboardButton("📞 যোগাযোগ", callback_data="contact"),
         InlineKeyboardButton("🌐 ওয়েবসাইট", url="https://sabujcomputers.pro.bd")],
    ]
    await update.message.reply_text(
        "🌿 *সবুজ কম্পিউটার্সে আপনাকে স্বাগতম!*\n\n"
        "বাগাতিপাড়া, নাটোরের BTEB অনুমোদিত কম্পিউটার প্রশিক্ষণ কেন্দ্র।\n\n"
        "নিচের মেনু থেকে আপনার পছন্দের তথ্য দেখুন 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    back_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")]])

    if query.data == "menu":
        keyboard = [
            [InlineKeyboardButton("🎓 কোর্সসমূহ", callback_data="courses"),
             InlineKeyboardButton("💰 ফি তথ্য", callback_data="fees")],
            [InlineKeyboardButton("📢 নোটিশ বোর্ড", callback_data="notice"),
             InlineKeyboardButton("📝 ভর্তি তথ্য", callback_data="admission")],
            [InlineKeyboardButton("📞 যোগাযোগ", callback_data="contact"),
             InlineKeyboardButton("🌐 ওয়েবসাইট", url="https://sabujcomputers.pro.bd")],
        ]
        await query.edit_message_text(
            "🌿 *সবুজ কম্পিউটার্সে আপনাকে স্বাগতম!*\n\nনিচের মেনু থেকে তথ্য দেখুন 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

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
            "🎓 ফাউন্ডেশন কোর্স:\n"
            "   সাশ্রয়ী মূল্যে সর্বোচ্চ মানের প্রশিক্ষণ\n\n"
            "🏆 BTEB কোর্স:\n"
            "   সরকার নির্ধারিত ফি অনুযায়ী\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💡 বিস্তারিত ফি জানতে যোগাযোগ করুন:\n"
            "📞 01724-084350\n"
            "🌐 sabujcomputers.pro.bd",
            parse_mode="Markdown",
            reply_markup=back_markup
        )

    elif query.data == "notice":
        await query.edit_message_text(
            "📢 *নোটিশ বোর্ড*\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "সর্বশেষ নোটিশ ও বিজ্ঞপ্তির জন্য ওয়েবসাইট ভিজিট করুন:\n\n"
            "🌐 https://sabujcomputers.pro.bd\n\n"
            "অথবা যোগাযোগ করুন:\n"
            "📞 01724-084350",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 নোটিশ দেখুন", url="https://sabujcomputers.pro.bd/#notice")],
                [InlineKeyboardButton("🔙 মেনুতে ফিরে যাও", callback_data="menu")]
            ])
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    keyboard = [[InlineKeyboardButton("📋 মেনু দেখুন", callback_data="menu")]]

    if any(w in text for w in ["কোর্স", "course", "ভর্তি", "admission", "training", "প্রশিক্ষণ"]):
        await update.message.reply_text("🎓 কোর্স সম্পর্কে জানতে:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎓 কোর্স দেখুন", callback_data="courses")]]))
    elif any(w in text for w in ["ফি", "fee", "খরচ", "টাকা", "price"]):
        await update.message.reply_text("💰 ফি সম্পর্কে জানতে:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 ফি তথ্য", callback_data="fees")]]))
    elif any(w in text for w in ["যোগাযোগ", "contact", "phone", "ফোন", "নম্বর"]):
        await update.message.reply_text("📞 যোগাযোগের তথ্য:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 যোগাযোগ", callback_data="contact")]]))
    elif any(w in text for w in ["নোটিশ", "notice", "বিজ্ঞপ্তি", "circular"]):
        await update.message.reply_text("📢 নোটিশ দেখুন:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 নোটিশ বোর্ড", callback_data="notice")]]))
    else:
        await update.message.reply_text(
            "🌿 ধন্যবাদ! নিচের মেনু থেকে আপনার প্রয়োজনীয় তথ্য দেখুন 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ সবুজ কম্পিউটার্স Bot চলছে...")
    app.run_polling()

if __name__ == "__main__":
    main()
