# 🚀 Quick Start - What to Do Next

## ✅ Changes Made

1. ✅ **LangChain is now the ONLY AI method** - removed direct OpenAI approach
2. ✅ **requirements.txt updated** - added `langchain` and `langchain-openai`
3. ✅ **LangChain dependencies installed** - all packages ready
4. ✅ **AIPersonalizer now uses LangChain** - better structure, retries, parsing

## 📋 Your Next Steps

### 1. Install PostgreSQL (YOU NEED TO DO THIS FIRST!)

Follow this guide: **[POSTGRESQL_WINDOWS_SETUP.md](POSTGRESQL_WINDOWS_SETUP.md)**

**Quick version:**
```powershell
# 1. Download PostgreSQL 16
# Go to: https://www.postgresql.org/download/windows/

# 2. Install it
# - Remember the password you set!
# - Default port: 5432
# - Install pgAdmin 4 (GUI tool)

# 3. Create database
psql -U postgres
# Enter password
CREATE DATABASE bde_email_automation;
\q
```

### 2. Configure Your .env File

```powershell
cd "d:\web peojects\email-automation-spearmmint\bde"
Copy-Item .env.example .env
notepad .env
```

**Fill in these values:**
```env
# PostgreSQL - USE YOUR PASSWORD FROM STEP 1!
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bde_email_automation
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_POSTGRES_PASSWORD_HERE  # ⚠️ Change this!

# Gmail SMTP
GMAIL_USER=your.email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password

# OpenAI API (for LangChain AI)
OPENAI_API_KEY=sk-...your_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Batch Processing
BATCH_SIZE=50
EMAIL_DELAY=2
```

### 3. Test Database Connection

```powershell
cd "d:\web peojects\email-automation-spearmmint\bde"

# Test PostgreSQL connection and create tables
python test_db_setup.py
```

**Expected output:**
```
✓ Config validation passed
✓ Database connection successful
✓ Schema created successfully
✓ CRUD operations working
✓ All tests passed!
```

### 4. Import Your Contacts

```powershell
# Import from CSV
python import_contacts.py

# You should see:
# Loaded 100 contacts from CSV
# Importing in batches of 50...
# Batch 1: 50 contacts imported
# Batch 2: 50 contacts imported
# Total: 100 contacts imported successfully
```

### 5. Send Your First Campaign with AI!

```powershell
# Send emails with LangChain AI personalization
python run_campaign_ai.py --campaign-id 1 --batch-size 10 --use-ai

# What happens:
# 1. Loads 10 contacts
# 2. Scrapes their websites
# 3. LangChain AI personalizes each email
# 4. Sends personalized emails
# 5. Logs everything to PostgreSQL
```

## 🎯 PostgreSQL Connection String

After you set up PostgreSQL, your connection string will be:

```
postgresql://postgres:your_password@localhost:5432/bde_email_automation
```

This is automatically built by `Config.get_database_url()` in your code!

## 🔧 LangChain is Now Active

Your project now uses **LangChain for everything**:

```python
from modules.ai_personalizer import AIPersonalizer  # This is LangChain!

ai = AIPersonalizer()  # LangChain-powered
result = ai.personalize_email(contact, scraped_data, template)
```

**Benefits you get:**
- ✅ Structured output (no JSON parsing errors)
- ✅ Automatic retries (2 attempts)
- ✅ Better prompts (reusable templates)
- ✅ Validation (Pydantic models)
- ✅ Easier to maintain

## 📁 Files You Need to Know

| File | Purpose | Status |
|------|---------|--------|
| `requirements.txt` | Dependencies | ✅ Updated with LangChain |
| `modules/ai_personalizer.py` | AI personalization | ✅ Now uses LangChain |
| `.env` | Configuration | ⚠️ YOU NEED TO CREATE THIS |
| `test_db_setup.py` | Test PostgreSQL | ⚠️ Run after PostgreSQL install |
| `import_contacts.py` | Import CSV | ⏳ Run after database setup |
| `run_campaign_ai.py` | Send campaigns | ⏳ Run after contacts imported |

## ❓ Troubleshooting

### "Module 'langchain' not found"
```powershell
pip install langchain langchain-openai
```

### "psycopg2 error: connection refused"
- PostgreSQL not installed or not running
- Check Windows Services → postgresql-x64-16 → Start

### "password authentication failed"
- Password in `.env` doesn't match PostgreSQL password
- Edit `.env` and fix `POSTGRES_PASSWORD`

### "database does not exist"
```sql
psql -U postgres
CREATE DATABASE bde_email_automation;
```

## 🎉 That's It!

Once you:
1. ✅ Install PostgreSQL ([guide](POSTGRESQL_WINDOWS_SETUP.md))
2. ✅ Create `.env` with your passwords
3. ✅ Run `python test_db_setup.py`

Your project will be ready to send AI-personalized emails! 🚀

---

**Need help?** Check these guides:
- [POSTGRESQL_WINDOWS_SETUP.md](POSTGRESQL_WINDOWS_SETUP.md) - Detailed PostgreSQL installation
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command reference
- [AI_PERSONALIZATION_GUIDE.md](AI_PERSONALIZATION_GUIDE.md) - How AI works
- [LANGCHAIN_GUIDE.md](LANGCHAIN_GUIDE.md) - Why LangChain is awesome
