"""
🏢 EMPLOYER BOT — For companies posting creative jobs
Run with: python employer_bot.py
"""

import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from database import init_db, get_db
from config import EMPLOYER_BOT_TOKEN, CATEGORIES, BUDGET_RANGES

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
(
    EMPLOYER_NAME, EMPLOYER_COMPANY, EMPLOYER_CONTACT,
    JOB_TITLE, JOB_CATEGORY, JOB_DESCRIPTION, JOB_SKILLS,
    JOB_BUDGET, JOB_DEADLINE, JOB_CONFIRM,
    VIEW_APPLICANTS, APPLICANT_ACTION
) = range(12)


# ─────────────────────────────────────────────
# START & REGISTRATION
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    employer = db.execute("SELECT * FROM employers WHERE telegram_id=?", (user_id,)).fetchone()
    db.close()

    if employer:
        await show_main_menu(update, context)
    else:
        await update.message.reply_text(
            "👋 *Welcome to CreativeMatch — Employer Portal!*\n\n"
            "Connect with Ethiopia's top creative talent.\n"
            "Designers • Photographers • Videographers • Copywriters & more.\n\n"
            "Let's set up your employer profile. What is your full name?",
            parse_mode="Markdown"
        )
        return EMPLOYER_NAME


async def get_employer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("🏢 What is your *company or organization name*?", parse_mode="Markdown")
    return EMPLOYER_COMPANY


async def get_employer_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["company"] = update.message.text.strip()
    await update.message.reply_text(
        "📞 What is your *contact* (phone number or email)?\n\n"
        "_This will be shared with matched applicants._",
        parse_mode="Markdown"
    )
    return EMPLOYER_CONTACT


async def get_employer_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text.strip()
    user = update.effective_user

    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO employers (telegram_id, name, company, contact) VALUES (?, ?, ?, ?)",
        (user.id, context.user_data["name"], context.user_data["company"], context.user_data["contact"])
    )
    db.commit()
    db.close()

    await update.message.reply_text(
        f"✅ *Profile created!*\n\n"
        f"👤 {context.user_data['name']}\n"
        f"🏢 {context.user_data['company']}\n\n"
        "You're ready to post jobs and find creative talent!",
        parse_mode="Markdown"
    )
    await show_main_menu(update, context)
    return ConversationHandler.END


# ─────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📢 Post a New Job"],
        ["📋 My Posted Jobs", "👥 View Applicants"],
        ["👤 My Profile", "ℹ️ Help"],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    msg = update.message or update.callback_query.message
    await msg.reply_text(
        "🏠 *Main Menu* — What would you like to do?",
        reply_markup=markup,
        parse_mode="Markdown"
    )


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📢 Post a New Job":
        return await post_job_start(update, context)
    elif text == "📋 My Posted Jobs":
        return await my_jobs(update, context)
    elif text == "👥 View Applicants":
        return await view_all_applicants(update, context)
    elif text == "👤 My Profile":
        return await my_profile(update, context)
    elif text == "ℹ️ Help":
        return await help_cmd(update, context)


# ─────────────────────────────────────────────
# POST A JOB
# ─────────────────────────────────────────────

async def post_job_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📢 *Post a New Job*\n\nStep 1/7 — What is the *job title*?\n\n"
        "_Example: Logo Designer, Wedding Photographer, Brand Video Editor_",
        parse_mode="Markdown"
    )
    return JOB_TITLE


async def get_job_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job_title"] = update.message.text.strip()

    buttons = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in CATEGORIES]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "Step 2/7 — Choose the *job category*:",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return JOB_CATEGORY


async def get_job_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["job_category"] = query.data.replace("cat_", "")

    await query.message.reply_text(
        f"✅ Category: *{context.user_data['job_category']}*\n\n"
        "Step 3/7 — Write a *job description*.\n\n"
        "_Describe what you need done, the scope, and any important details._",
        parse_mode="Markdown"
    )
    return JOB_DESCRIPTION


async def get_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job_description"] = update.message.text.strip()
    await update.message.reply_text(
        "Step 4/7 — What *skills* are required?\n\n"
        "_Separate with commas. Example: Photoshop, Illustrator, Logo Design_",
        parse_mode="Markdown"
    )
    return JOB_SKILLS


async def get_job_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job_skills"] = update.message.text.strip()

    buttons = [[InlineKeyboardButton(b, callback_data=f"budget_{b}")] for b in BUDGET_RANGES]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "Step 5/7 — What is the *budget range*?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return JOB_BUDGET


async def get_job_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["job_budget"] = query.data.replace("budget_", "")

    await query.message.reply_text(
        f"✅ Budget: *{context.user_data['job_budget']}*\n\n"
        "Step 6/7 — What is the *application deadline*?\n\n"
        "_Example: 20 May 2025 or Ongoing_",
        parse_mode="Markdown"
    )
    return JOB_DEADLINE


async def get_job_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job_deadline"] = update.message.text.strip()

    jd = context.user_data
    await update.message.reply_text(
        f"📋 *Review Your Job Post*\n\n"
        f"🏷️ Title: {jd['job_title']}\n"
        f"📂 Category: {jd['job_category']}\n"
        f"🛠️ Skills: {jd['job_skills']}\n"
        f"💰 Budget: {jd['job_budget']}\n"
        f"📅 Deadline: {jd['job_deadline']}\n\n"
        f"📝 Description:\n_{jd['job_description']}_\n\n"
        "Publish this job?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Publish", callback_data="publish_yes"),
             InlineKeyboardButton("❌ Cancel", callback_data="publish_no")]
        ])
    )
    return JOB_CONFIRM


async def confirm_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "publish_no":
        await query.message.reply_text("❌ Job post cancelled.")
        await show_main_menu(update, context)
        return ConversationHandler.END

    user_id = update.effective_user.id
    jd = context.user_data

    db = get_db()
    employer = db.execute("SELECT id FROM employers WHERE telegram_id=?", (user_id,)).fetchone()
    db.execute(
        "INSERT INTO jobs (employer_id, title, category, description, skills, budget, deadline, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'open')",
        (employer["id"], jd["job_title"], jd["job_category"],
         jd["job_description"], jd["job_skills"], jd["job_budget"], jd["job_deadline"])
    )
    db.commit()
    db.close()

    await query.message.reply_text(
        "🎉 *Job Published Successfully!*\n\n"
        f"Your job *\"{jd['job_title']}\"* is now live.\n"
        "Matching creatives will be notified automatically.\n\n"
        "You'll receive alerts when someone applies.",
        parse_mode="Markdown"
    )
    await show_main_menu(update, context)
    return ConversationHandler.END


# ─────────────────────────────────────────────
# VIEW MY JOBS
# ─────────────────────────────────────────────

async def my_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    employer = db.execute("SELECT id FROM employers WHERE telegram_id=?", (user_id,)).fetchone()
    if not employer:
        await update.message.reply_text("Please register first with /start")
        db.close()
        return

    jobs = db.execute(
        "SELECT * FROM jobs WHERE employer_id=? ORDER BY created_at DESC", (employer["id"],)
    ).fetchall()
    db.close()

    if not jobs:
        await update.message.reply_text(
            "📋 You haven't posted any jobs yet.\n\nTap *📢 Post a New Job* to get started!",
            parse_mode="Markdown"
        )
        return

    text = "📋 *Your Job Posts*\n\n"
    for j in jobs:
        count_db = get_db()
        apps = count_db.execute("SELECT COUNT(*) as c FROM applications WHERE job_id=?", (j["id"],)).fetchone()
        count_db.close()
        status_icon = "🟢" if j["status"] == "open" else "🔴"
        text += f"{status_icon} *{j['title']}*\n"
        text += f"   📂 {j['category']} | 💰 {j['budget']}\n"
        text += f"   👥 {apps['c']} applicant(s) | 📅 {j['deadline']}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


# ─────────────────────────────────────────────
# VIEW APPLICANTS
# ─────────────────────────────────────────────

async def view_all_applicants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    employer = db.execute("SELECT id FROM employers WHERE telegram_id=?", (user_id,)).fetchone()
    if not employer:
        await update.message.reply_text("Please register first with /start")
        db.close()
        return

    jobs = db.execute("SELECT * FROM jobs WHERE employer_id=?", (employer["id"],)).fetchall()
    db.close()

    if not jobs:
        await update.message.reply_text("No jobs posted yet.")
        return

    buttons = [[InlineKeyboardButton(f"📂 {j['title']}", callback_data=f"viewapps_{j['id']}")] for j in jobs]
    await update.message.reply_text(
        "👥 *View Applicants* — Select a job:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )


async def show_applicants_for_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    job_id = int(query.data.replace("viewapps_", ""))

    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    apps = db.execute(
        "SELECT a.*, s.name, s.category, s.skills, s.portfolio, s.bio, s.telegram_id "
        "FROM applications a JOIN job_seekers s ON a.seeker_id = s.id WHERE a.job_id=?",
        (job_id,)
    ).fetchall()
    db.close()

    if not apps:
        await query.message.reply_text(f"No applicants yet for *{job['title']}*.", parse_mode="Markdown")
        return

    await query.message.reply_text(
        f"👥 *Applicants for: {job['title']}*\n\n"
        f"Total: {len(apps)} applicant(s)",
        parse_mode="Markdown"
    )

    for app in apps:
        status_icon = {"pending": "⏳", "accepted": "✅", "rejected": "❌"}.get(app["status"], "⏳")
        text = (
            f"{status_icon} *{app['name']}*\n"
            f"📂 Category: {app['category']}\n"
            f"🛠️ Skills: {app['skills']}\n"
            f"📝 Bio: {app['bio']}\n"
            f"🔗 Portfolio: {app['portfolio'] or 'Not provided'}\n"
            f"💬 Message: {app['cover_message'] or 'No message'}\n"
        )
        buttons = []
        if app["status"] == "pending":
            buttons = [[
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_{app['id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{app['id']}")
            ]]
        await query.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)


async def handle_applicant_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, app_id = query.data.split("_")
    app_id = int(app_id)

    new_status = "accepted" if action == "accept" else "rejected"
    db = get_db()
    db.execute("UPDATE applications SET status=? WHERE id=?", (new_status, app_id))
    db.commit()

    app = db.execute(
        "SELECT a.*, s.name, s.telegram_id FROM applications a "
        "JOIN job_seekers s ON a.seeker_id=s.id WHERE a.id=?", (app_id,)
    ).fetchone()
    job = db.execute("SELECT title FROM jobs WHERE id=?", (app["job_id"],)).fetchone()
    db.close()

    icon = "✅" if new_status == "accepted" else "❌"
    await query.message.reply_text(
        f"{icon} You *{new_status}* {app['name']}'s application for *{job['title']}*.",
        parse_mode="Markdown"
    )

    # Notify the job seeker
    msg = (
        f"🔔 *Application Update*\n\n"
        f"Your application for *{job['title']}* has been *{new_status}*.\n\n"
        + ("🎉 Congratulations! The employer will contact you soon." if new_status == "accepted"
           else "Keep applying — the right job is coming!")
    )
    try:
        await context.bot.send_message(chat_id=app["telegram_id"], text=msg, parse_mode="Markdown")
    except Exception:
        pass  # Seeker may not have started the bot yet


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db()
    employer = db.execute("SELECT * FROM employers WHERE telegram_id=?", (user_id,)).fetchone()
    db.close()
    if employer:
        await update.message.reply_text(
            f"👤 *Your Profile*\n\n"
            f"Name: {employer['name']}\n"
            f"Company: {employer['company']}\n"
            f"Contact: {employer['contact']}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("No profile found. Type /start to register.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Help — Employer Bot*\n\n"
        "📢 *Post a New Job* — Create a job listing\n"
        "📋 *My Posted Jobs* — See all your jobs\n"
        "👥 *View Applicants* — Review and accept/reject applicants\n"
        "👤 *My Profile* — View your profile\n\n"
        "Questions? Contact @YourSupportHandle",
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    init_db()
    app = Application.builder().token(EMPLOYER_BOT_TOKEN).build()

    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EMPLOYER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_employer_name)],
            EMPLOYER_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_employer_company)],
            EMPLOYER_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_employer_contact)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    job_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 Post a New Job$"), post_job_start)],
        states={
            JOB_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job_title)],
            JOB_CATEGORY: [CallbackQueryHandler(get_job_category, pattern="^cat_")],
            JOB_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job_description)],
            JOB_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job_skills)],
            JOB_BUDGET: [CallbackQueryHandler(get_job_budget, pattern="^budget_")],
            JOB_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job_deadline)],
            JOB_CONFIRM: [CallbackQueryHandler(confirm_job, pattern="^publish_")],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(reg_conv)
    app.add_handler(job_conv)
    app.add_handler(MessageHandler(filters.Regex("^(📋 My Posted Jobs|👥 View Applicants|👤 My Profile|ℹ️ Help)$"), main_menu_handler))
    app.add_handler(CallbackQueryHandler(show_applicants_for_job, pattern="^viewapps_"))
    app.add_handler(CallbackQueryHandler(handle_applicant_action, pattern="^(accept|reject)_"))

    print("🏢 Employer Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
