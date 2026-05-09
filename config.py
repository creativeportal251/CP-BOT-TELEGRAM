"""
⚙️ CONFIG — Bot tokens are read from environment variables.
             Set TELEGRAM_BOT_TOKEN and SEEKER_BOT_TOKEN in your Railway service.
"""

import os

# ─────────────────────────────────────────────────────────
# 🔑 BOT TOKENS — Loaded from Railway environment variables
# ─────────────────────────────────────────────────────────
EMPLOYER_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
SEEKER_BOT_TOKEN   = os.getenv("SEEKER_BOT_TOKEN", "")


# ─────────────────────────────────────────────────────────
# 🎨 JOB CATEGORIES — Add or remove as you like
# ─────────────────────────────────────────────────────────
CATEGORIES = [
    "Graphic Design",
    "Photography",
    "Videography & Editing",
    "Motion Graphics & Animation",
    "Copywriting & Content",
    "Social Media Management",
    "UI/UX Design",
    "Illustration",
    "Music & Audio",
    "Other Creative",
]


# ─────────────────────────────────────────────────────────
# 💰 BUDGET RANGES (in ETB)
# ─────────────────────────────────────────────────────────
BUDGET_RANGES = [
    "Under 1,000 ETB",
    "1,000 – 5,000 ETB",
    "5,000 – 15,000 ETB",
    "15,000 – 30,000 ETB",
    "30,000+ ETB",
    "Negotiable",
]
