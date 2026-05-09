# 🚀 CreativeMatch Bot — Setup Guide
## No coding knowledge needed — follow these steps exactly

---

## 📁 Files You Have
| File | What it does |
|------|-------------|
| `employer_bot.py` | Bot for companies posting jobs |
| `seeker_bot.py` | Bot for creatives finding work |
| `database.py` | Stores all data (shared by both bots) |
| `config.py` | Your settings, tokens, categories |
| `requirements.txt` | List of software needed |

---

## STEP 1 — Create Your Two Bots on Telegram

1. Open Telegram and search for **@BotFather**
2. Type `/newbot`
3. Give it a name → e.g. **CreativeMatch Employer**
4. Give it a username → e.g. **creativematch_employer_bot**
5. BotFather will send you a **token** like: `7123456789:AAF...`
6. **Copy and save this token somewhere safe**

7. Repeat `/newbot` for the second bot:
   - Name: **CreativeMatch Jobs**
   - Username: **creativematch_jobs_bot**
   - Copy this token too

---

## STEP 2 — Add Tokens to config.py

Open `config.py` and replace the placeholder text:

```python
EMPLOYER_BOT_TOKEN = "PASTE_YOUR_EMPLOYER_BOT_TOKEN_HERE"
SEEKER_BOT_TOKEN   = "PASTE_YOUR_SEEKER_BOT_TOKEN_HERE"
```

Paste your actual tokens between the quotes.

---

## STEP 3 — Install Python

1. Go to https://python.org/downloads
2. Download Python 3.11 or newer
3. During install → ✅ check **"Add Python to PATH"**
4. Click Install

---

## STEP 4 — Install the Bot Library

1. Open **Command Prompt** (Windows) or **Terminal** (Mac/Linux)
2. Navigate to your bot folder:
   ```
   cd path/to/creative_jobs_bot
   ```
3. Run:
   ```
   pip install -r requirements.txt
   ```

---

## STEP 5 — Run the Bots

Open **two separate terminal windows**:

**Terminal 1 — Employer Bot:**
```
python employer_bot.py
```

**Terminal 2 — Job Seeker Bot:**
```
python seeker_bot.py
```

You should see:
```
✅ Database initialized.
🏢 Employer Bot is running...
```

---

## STEP 6 — Test Your Bots

1. Search your bot username on Telegram (e.g. @creativematch_employer_bot)
2. Click **Start**
3. Follow the registration prompts

---

## 🌐 Run 24/7 on a Server (Free Options)

When you're ready to keep the bots online always (not just on your laptop):

### Option A — Railway.app (Easiest, Free tier)
1. Go to https://railway.app
2. Connect your GitHub account
3. Upload your bot folder
4. Add environment variables: `EMPLOYER_BOT_TOKEN` and `SEEKER_BOT_TOKEN`
5. Deploy — it stays online 24/7

### Option B — Render.com (Also free)
1. Go to https://render.com
2. Create a new "Background Worker"
3. Upload your files, set start command: `python employer_bot.py`
4. Repeat for seeker bot

---

## ✏️ Customize Your Bot

### Change categories (in config.py):
```python
CATEGORIES = [
    "Graphic Design",
    "Photography",
    "Add your own here",
]
```

### Change budget ranges (in config.py):
```python
BUDGET_RANGES = [
    "Under 1,000 ETB",
    "Your custom range",
]
```

### Change support handle (in both bot files):
Search for `@YourSupportHandle` and replace with your actual Telegram username.

---

## 🔁 How Matching Works

1. A creative registers with their **category** (e.g. Graphic Design) and **skills** (e.g. Photoshop, Illustrator)
2. An employer posts a job with a **category** and required **skills**
3. The seeker bot's **🎯 Matched Jobs** shows jobs that:
   - Match their category exactly
   - OR share matching skill keywords
4. When an employer posts a new job, the bot can be extended to notify all matching seekers automatically

---

## 🗄️ Your Database

All data is saved in a file called `creativematch.db` in the same folder.
- **Back it up regularly** (just copy the file)
- It stores: employers, job seekers, jobs, applications
- When you move to a server, upload this file too (or start fresh)

---

## ❓ Common Issues

| Problem | Fix |
|---------|-----|
| "Token not found" error | Check config.py — no extra spaces around the token |
| Bot doesn't respond | Make sure the python script is still running |
| "Module not found" error | Run `pip install -r requirements.txt` again |
| Both bots use same database? | Yes! That's intentional — they share data |

---

## 📞 Future Upgrades (when ready)
- ☁️ Move database to PostgreSQL (for more users)
- 🔔 Auto-notify seekers when a matching job is posted
- 📊 Admin dashboard to see stats
- 💳 Payment integration for premium job posts
- 🌍 Multi-language support (Amharic + English)

---

*Built with Python + python-telegram-bot + SQLite*
