"""
🎨 JOB SEEKER BOT — For creative professionals finding work
Run with: python seeker_bot.py
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from database import init_db, get_db
from config import SEEKER_BOT_TOKEN, CATEGORIES

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
(
    SEEKER_NAME, SEEKER_CATEGORY, SEEKER_SKILLS, SEEKER_BIO,
    SEEKER_PORTFOLIO, SEEKER_CONTACT,
    BROWSE_CATEGORY, APPLY_MESSAGE, APPLY_CONFIRM
) = range(9)


# ─────────────────────────────────────────────
# START & REGISTRATION
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    seeker = db.execute("SELECT * FROM job_seekers WHERE telegram_id=?", (user_id,)).fetchone()
    db.close()

    if seeker:
        await show_main_menu(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "👋 *Welcome to CreativeMatch — Creative Portal!*\n\n"
            "Find freelance & full-time creative work with top Ethiopian companies.\n"
            "Designers • Photographers • Videographers • Copywriters & more.\n\n"
            "Let's build your profile. What is your *full name*?",
            parse_mode="Markdown"
        )
        return SEEKER_NAME


async def get_seeker_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()

    buttons = [[InlineKeyboardButton(cat, callback_data=f"scat_{cat}")] for cat in CATEGORIES]
    await update.message.reply_text(
        "🎨 What is your *main creative category*?",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    return SEEKER_CATEGORY


async def get_seeker_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["category"] = query.data.replace("scat_", "")

    await query.message.reply_text(
        f"✅ Category: *{context.user_data['category']}*\n\n"
        "🛠️ List your *skills* (separate with commas):\n\n"
        "_Example: Photoshop, Lightroom, Logo Design, Brand Identity_",
        parse_mode="Markdown"
    )
    return SEEKER_SKILLS


async def get_seeker_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["skills"] = update.message.text.strip()
    await update.message.reply_text(
        "📝 Write a short *bio* about yourself:\n\n"
        "_Example: 3 years experience in brand design, worked with 20+ clients across Ethiopia._",
        parse_mode="Markdown"
    )
    return SEEKER_BIO


async def get_seeker_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bio"] = update.message.text.strip()
    await update.message.reply_text(
        "🔗 Share your *portfolio link* (website, Behance, Instagram, Google Drive, etc.)\n\n"
        "Type *skip* if you don't have one right now.",
        parse_mode="Markdown"
    )
    return SEEKER_PORTFOLIO


async def get_seeker_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["portfolio"] = None if text.lower() == "skip" else text
    await update.message.reply_text(
        "📞 What is your *contact* (phone or email)?\n\n"
        "_Shared with employers who accept your application._",
        parse_mode="Markdown"
    )
    return SEEKER_CONTACT


async def get_seeker_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text.strip()
    user = update.effective_user
    sd = context.user_data

    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO job_seekers "
        "(telegram_id, name, category, skills, bio, portfolio, contact) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user.id, sd["name"], sd["category"], sd["skills"],
         sd["bio"], sd["portfolio"], sd["contact"])
    )
    db.commit()
    db.close()

    await update.message.reply_text(
        f"🎉 *Profile Created!*\n\n"
        f"👤 {sd['name']}\n"
        f"🎨 {sd['category']}\n"
        f"🛠️ {sd['skills']}\n\n"
        "You're ready to browse jobs and apply!\n"
        "You'll also be *automatically notified* when a matching job is posted.",
        parse_mode="Markdown"
    )
    await show_main_menu(update, context)
    return ConversationHandler.END


# ─────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🔍 Browse Jobs", "🎯 Matched Jobs"],
        ["📄 My Applications", "👤 My Profile"],
        ["ℹ️ Help"],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    msg = update.message or update.callback_query.message
    await msg.reply_text(
        "🏠 *Main Menu* — Find your next gig!",
        reply_markup=markup,
        parse_mode="Markdown"
    )


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔍 Browse Jobs":
        return await browse_jobs(update, context)
    elif text == "🎯 Matched Jobs":
        return await matched_jobs(update, context)
    elif text == "📄 My Applications":
        return await my_applications(update, context)
    elif text == "👤 My Profile":
        return await my_profile(update, context)
    elif text == "ℹ️ Help":
        return await help_cmd(update, context)


# ─────────────────────────────────────────────
# BROWSE JOBS
# ─────────────────────────────────────────────

async def browse_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[InlineKeyboardButton(cat, callback_data=f"browse_{cat}")] for cat in CATEGORIES]
    buttons.append([InlineKeyboardButton("🌐 All Categories", callback_data="browse_ALL")])
    await update.message.reply_text(
        "🔍 *Browse Jobs* — Filter by category:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )


async def show_jobs_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.replace("browse_", "")

    db = get_db()
    if cat == "ALL":
        jobs = db.execute(
            "SELECT j.*, e.company FROM jobs j JOIN employers e ON j.employer_id=e.id "
            "WHERE j.status='open' ORDER BY j.created_at DESC LIMIT 15"
        ).fetchall()
    else:
        jobs = db.execute(
            "SELECT j.*, e.company FROM jobs j JOIN employers e ON j.employer_id=e.id "
            "WHERE j.status='open' AND j.category=? ORDER BY j.created_at DESC LIMIT 15",
            (cat,)
        ).fetchall()
    db.close()

    if not jobs:
        await query.message.reply_text(
            f"😔 No open jobs in *{cat}* right now.\n\nCheck back soon or try another category!",
            parse_mode="Markdown"
        )
        return

    for job in jobs:
        text = (
            f"📌 *{job['title']}*\n"
            f"🏢 {job['company']}\n"
            f"📂 {job['category']} | 💰 {job['budget']}\n"
            f"🛠️ {job['skills']}\n"
            f"📅 Deadline: {job['deadline']}\n\n"
            f"📝 _{job['description'][:200]}{'...' if len(job['description']) > 200 else ''}_"
        )
        buttons = [[InlineKeyboardButton("📩 Apply Now", callback_data=f"apply_{job['id']}")]]
        await query.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


# ─────────────────────────────────────────────
# MATCHED JOBS (Smart Match)
# ─────────────────────────────────────────────

async def matched_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    seeker = db.execute("SELECT * FROM job_seekers WHERE telegram_id=?", (user_id,)).fetchone()
    if not seeker:
        await update.message.reply_text("Please register first with /start")
        db.close()
        return

    # Match by category first, then by skills overlap
    jobs = db.execute(
        "SELECT j.*, e.company FROM jobs j JOIN employers e ON j.employer_id=e.id "
        "WHERE j.status='open' AND j.category=? ORDER BY j.created_at DESC",
        (seeker["category"],)
    ).fetchall()

    # Also find jobs with matching skills keywords
    seeker_skills = [s.strip().lower() for s in seeker["skills"].split(",")]
    skill_matched = db.execute(
        "SELECT j.*, e.company FROM jobs j JOIN employers e ON j.employer_id=e.id "
        "WHERE j.status='open' AND j.category!=?", (seeker["category"],)
    ).fetchall()
    db.close()

    # Score skill matches
    scored = []
    seen_ids = {j["id"] for j in jobs}
    for job in skill_matched:
        job_skills = [s.strip().lower() for s in job["skills"].split(",")]
        score = len(set(seeker_skills) & set(job_skills))
        if score > 0 and job["id"] not in seen_ids:
            scored.append((score, job))

    scored.sort(reverse=True)
    extra_matches = [j for _, j in scored[:5]]
    all_matches = list(jobs) + extra_matches

    if not all_matches:
        await update.message.reply_text(
            "😔 No matching jobs right now.\n\n"
            "You'll be *automatically notified* when a match is posted! 🔔",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        f"🎯 *{len(all_matches)} Matched Jobs for You*\n\n"
        f"Based on your category: *{seeker['category']}* and skills.",
        parse_mode="Markdown"
    )

    for job in all_matches[:10]:
        text = (
            f"⭐ *{job['title']}*\n"
            f"🏢 {job['company']}\n"
            f"📂 {job['category']} | 💰 {job['budget']}\n"
            f"🛠️ {job['skills']}\n"
            f"📅 Deadline: {job['deadline']}"
        )
        buttons = [[InlineKeyboardButton("📩 Apply Now", callback_data=f"apply_{job['id']}")]]
        await update.message.reply_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


# ─────────────────────────────────────────────
# APPLY FOR JOB
# ─────────────────────────────────────────────

async def apply_job_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    job_id = int(query.data.replace("apply_", ""))
    context.user_data["applying_job_id"] = job_id

    user_id = update.effective_user.id
    db = get_db()

    # Check if already applied
    seeker = db.execute("SELECT * FROM job_seekers WHERE telegram_id=?", (user_id,)).fetchone()
    if not seeker:
        await query.message.reply_text("Please register first with /start")
        db.close()
        return ConversationHandler.END

    existing = db.execute(
        "SELECT * FROM applications WHERE job_id=? AND seeker_id=?",
        (job_id, seeker["id"])
    ).fetchone()
    db.close()

    if existing:
        await query.message.reply_text(
            "⚠️ You've already applied for this job!\n\nCheck *📄 My Applications* for status.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await query.message.reply_text(
        "📩 *Apply for this Job*\n\n"
        "Write a short *cover message* to the employer:\n\n"
        "_Why are you a great fit? Any relevant experience?_\n\n"
        "Type *skip* to apply without a message.",
        parse_mode="Markdown"
    )
    return APPLY_MESSAGE


async def get_apply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["cover_message"] = None if text.lower() == "skip" else text

    job_id = context.user_data["applying_job_id"]
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    db.close()

    await update.message.reply_text(
        f"📋 *Confirm Application*\n\n"
        f"Job: *{job['title']}*\n"
        f"Company: Looking for {job['category']} talent\n"
        f"Budget: {job['budget']}\n\n"
        "Submit your application?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Submit", callback_data="submitapp_yes"),
             InlineKeyboardButton("❌ Cancel", callback_data="submitapp_no")]
        ])
    )
    return APPLY_CONFIRM


async def confirm_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "submitapp_no":
        await query.message.reply_text("❌ Application cancelled.")
        return ConversationHandler.END

    user_id = update.effective_user.id
    job_id = context.user_data["applying_job_id"]
    cover = context.user_data.get("cover_message")

    db = get_db()
    seeker = db.execute("SELECT * FROM job_seekers WHERE telegram_id=?", (user_id,)).fetchone()
    db.execute(
        "INSERT INTO applications (job_id, seeker_id, cover_message, status) VALUES (?, ?, ?, 'pending')",
        (job_id, seeker["id"], cover)
    )
    db.commit()

    # Notify the employer
    job = db.execute("SELECT j.*, e.telegram_id FROM jobs j JOIN employers e ON j.employer_id=e.id WHERE j.id=?", (job_id,)).fetchone()
    db.close()

    await query.message.reply_text(
        "🎉 *Application Submitted!*\n\n"
        "You'll be notified when the employer responds.\n"
        "Good luck! 🍀",
        parse_mode="Markdown"
    )

    # Notify employer
    try:
        await context.bot.send_message(
            chat_id=job["telegram_id"],
            text=(
                f"🔔 *New Applicant!*\n\n"
                f"*{seeker['name']}* applied for your job: *{job['title']}*\n"
                f"Category: {seeker['category']}\n"
                f"Skills: {seeker['skills']}\n\n"
                "Open your Employer Bot to review and respond."
            ),
            parse_mode="Markdown"
        )
    except Exception:
        pass

    return ConversationHandler.END


# ─────────────────────────────────────────────
# MY APPLICATIONS
# ─────────────────────────────────────────────

async def my_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    seeker = db.execute("SELECT * FROM job_seekers WHERE telegram_id=?", (user_id,)).fetchone()
    if not seeker:
        await update.message.reply_text("Please register with /start first.")
        db.close()
        return

    apps = db.execute(
        "SELECT a.*, j.title, j.category, j.budget, e.company "
        "FROM applications a JOIN jobs j ON a.job_id=j.id "
        "JOIN employers e ON j.employer_id=e.id "
        "WHERE a.seeker_id=? ORDER BY a.applied_at DESC",
        (seeker["id"],)
    ).fetchall()
    db.close()

    if not apps:
        await update.message.reply_text(
            "📄 You haven't applied to any jobs yet.\n\nTap *🔍 Browse Jobs* to find opportunities!",
            parse_mode="Markdown"
        )
        return

    text = "📄 *My Applications*\n\n"
    for a in apps:
        icon = {"pending": "⏳", "accepted": "✅", "rejected": "❌"}.get(a["status"], "⏳")
        text += f"{icon} *{a['title']}*\n"
        text += f"   🏢 {a['company']} | 💰 {a['budget']}\n"
        text += f"   Status: *{a['status'].capitalize()}*\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    seeker = db.execute("SELECT * FROM job_seekers WHERE telegram_id=?", (user_id,)).fetchone()
    db.close()
    if seeker:
        await update.message.reply_text(
            f"👤 *Your Profile*\n\n"
            f"Name: {seeker['name']}\n"
            f"Category: {seeker['category']}\n"
            f"Skills: {seeker['skills']}\n"
            f"Bio: {seeker['bio']}\n"
            f"Portfolio: {seeker['portfolio'] or 'Not set'}\n"
            f"Contact: {seeker['contact']}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("No profile found. Type /start to register.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Help — Creative Job Seeker Bot*\n\n"
        "🔍 *Browse Jobs* — See all open jobs by category\n"
        "🎯 *Matched Jobs* — Jobs matched to your skills\n"
        "📄 *My Applications* — Track your applications\n"
        "👤 *My Profile* — View your profile\n\n"
        "You'll get automatic notifications for matching jobs!\n\n"
        "Questions? Contact @YourSupportHandle",
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    init_db()
    app = Application.builder().token(SEEKER_BOT_TOKEN).build()

    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SEEKER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_name)],
            SEEKER_CATEGORY: [CallbackQueryHandler(get_seeker_category, pattern="^scat_")],
            SEEKER_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_skills)],
            SEEKER_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_bio)],
            SEEKER_PORTFOLIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_portfolio)],
            SEEKER_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_contact)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    apply_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(apply_job_start, pattern="^apply_")],
        states={
            APPLY_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_apply_message)],
            APPLY_CONFIRM: [CallbackQueryHandler(confirm_application, pattern="^submitapp_")],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(reg_conv)
    app.add_handler(apply_conv)
    app.add_handler(MessageHandler(
        filters.Regex("^(🔍 Browse Jobs|🎯 Matched Jobs|📄 My Applications|👤 My Profile|ℹ️ Help)$"),
        main_menu_handler
    ))
    app.add_handler(CallbackQueryHandler(show_jobs_by_category, pattern="^browse_"))

    print("🎨 Job Seeker Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
