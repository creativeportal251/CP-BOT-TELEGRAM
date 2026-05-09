"""
🚀 run_both_bots.py — Starts both the Employer Bot and the Job Seeker Bot
concurrently in a single process using asyncio.

Usage:
    python run_both_bots.py
"""

import asyncio
import logging
import signal

from telegram.ext import Application

from config import EMPLOYER_BOT_TOKEN, SEEKER_BOT_TOKEN
from database import init_db

# Import the handler-registration functions from each bot module.
# We re-use all the handlers defined there without calling their blocking
# main() / run_polling() entry points.
import employer_bot
import seeker_bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_employer_app() -> Application:
    """Build and configure the Employer Bot application."""
    from telegram.ext import (
        CommandHandler, MessageHandler, CallbackQueryHandler,
        ConversationHandler, filters,
    )
    from employer_bot import (
        start, get_employer_name, get_employer_company, get_employer_contact,
        post_job_start, get_job_title, get_job_category, get_job_description,
        get_job_skills, get_job_budget, get_job_deadline, confirm_job,
        main_menu_handler, my_jobs, view_all_applicants,
        show_applicants_for_job, handle_applicant_action,
        EMPLOYER_NAME, EMPLOYER_COMPANY, EMPLOYER_CONTACT,
        JOB_TITLE, JOB_CATEGORY, JOB_DESCRIPTION, JOB_SKILLS,
        JOB_BUDGET, JOB_DEADLINE, JOB_CONFIRM,
    )

    app = Application.builder().token(EMPLOYER_BOT_TOKEN).build()

    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EMPLOYER_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_employer_name)],
            EMPLOYER_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_employer_company)],
            EMPLOYER_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_employer_contact)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    job_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 Post a New Job$"), post_job_start)],
        states={
            JOB_TITLE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job_title)],
            JOB_CATEGORY:     [CallbackQueryHandler(get_job_category, pattern="^cat_")],
            JOB_DESCRIPTION:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job_description)],
            JOB_SKILLS:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job_skills)],
            JOB_BUDGET:       [CallbackQueryHandler(get_job_budget, pattern="^budget_")],
            JOB_DEADLINE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job_deadline)],
            JOB_CONFIRM:      [CallbackQueryHandler(confirm_job, pattern="^publish_")],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(reg_conv)
    app.add_handler(job_conv)
    app.add_handler(MessageHandler(
        filters.Regex("^(📋 My Posted Jobs|👥 View Applicants|👤 My Profile|ℹ️ Help)$"),
        main_menu_handler,
    ))
    app.add_handler(CallbackQueryHandler(show_applicants_for_job, pattern="^viewapps_"))
    app.add_handler(CallbackQueryHandler(handle_applicant_action, pattern="^(accept|reject)_"))

    return app


def build_seeker_app() -> Application:
    """Build and configure the Job Seeker Bot application."""
    from telegram.ext import (
        CommandHandler, MessageHandler, CallbackQueryHandler,
        ConversationHandler, filters,
    )
    from seeker_bot import (
        start, get_seeker_name, get_seeker_category, get_seeker_skills,
        get_seeker_bio, get_seeker_portfolio, get_seeker_contact,
        main_menu_handler, browse_jobs, show_jobs_by_category,
        apply_job_start, get_apply_message, confirm_application,
        SEEKER_NAME, SEEKER_CATEGORY, SEEKER_SKILLS, SEEKER_BIO,
        SEEKER_PORTFOLIO, SEEKER_CONTACT,
        APPLY_MESSAGE, APPLY_CONFIRM,
    )

    app = Application.builder().token(SEEKER_BOT_TOKEN).build()

    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SEEKER_NAME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_name)],
            SEEKER_CATEGORY:  [CallbackQueryHandler(get_seeker_category, pattern="^scat_")],
            SEEKER_SKILLS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_skills)],
            SEEKER_BIO:       [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_bio)],
            SEEKER_PORTFOLIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_portfolio)],
            SEEKER_CONTACT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_seeker_contact)],
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
        main_menu_handler,
    ))
    app.add_handler(CallbackQueryHandler(show_jobs_by_category, pattern="^browse_"))

    return app


async def run_bot(app: Application, name: str) -> None:
    """Initialise, start polling, and keep running until cancelled."""
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info("%s is running.", name)

    # Keep this coroutine alive until the task is cancelled (shutdown signal).
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Stopping %s…", name)
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


async def main() -> None:
    init_db()

    employer_app = build_employer_app()
    seeker_app   = build_seeker_app()

    loop = asyncio.get_running_loop()

    employer_task = asyncio.create_task(run_bot(employer_app, "🏢 Employer Bot"))
    seeker_task   = asyncio.create_task(run_bot(seeker_app,   "🎨 Seeker Bot"))

    # Graceful shutdown on SIGINT / SIGTERM
    def _request_shutdown():
        logger.info("Shutdown signal received — stopping both bots…")
        employer_task.cancel()
        seeker_task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _request_shutdown)

    logger.info("Both bots are starting up…")
    await asyncio.gather(employer_task, seeker_task, return_exceptions=True)
    logger.info("Both bots have shut down cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
