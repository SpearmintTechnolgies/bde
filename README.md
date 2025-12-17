# 🚀 BDE - AI-Powered Email Automation System

Intelligent investor outreach system that researches prospects and generates personalized emails using AI.

## 📋 Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd bde

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env and add your credentials:
# - Gmail address and app password
# - OpenAI API key
```

**Important:** Get your credentials:
- **Gmail App Password**: https://myaccount.google.com/apppasswords
- **OpenAI API Key**: https://platform.openai.com/api-keys

### 3. Initialize Database

```bash
python scripts/setup_database.py
```

### 4. Prepare Your Contacts

Edit `data/contacts.csv` with your investor contacts:

```csv
name,email,company,website,linkedin_url,status
John Smith,john@vc.com,ABC Ventures,https://abcvc.com,https://linkedin.com/in/johnsmith,pending
```

### 5. Test Components

```bash
# Test web scraping
python scripts/test_components.py scraping

# Test AI generation
python scripts/test_components.py ai

# Test email sending
python scripts/test_components.py email
```

### 6. Run Campaign

```bash
# Test run with 10 emails
python scripts/main.py --limit 10

# Full production run
python scripts/main.py
```

## 📁 Project Structure

```
bde/
├── config/              # Configuration files
│   ├── settings.py      # Environment variables loader
│   └── email_templates.py
├── modules/             # Core functionality
│   ├── data_enrichment.py   # Web scraping
│   ├── ai_generator.py      # OpenAI integration
│   ├── email_sender.py      # SMTP delivery
│   ├── database.py          # SQLite operations
│   └── utils.py             # Helper functions
├── scripts/             # Executable scripts
│   ├── main.py             # Main orchestrator
│   ├── setup_database.py   # DB initialization
│   └── test_components.py  # Testing utilities
├── data/                # Data storage
│   ├── contacts.csv        # Input contacts
│   ├── sent_emails.db      # Campaign tracking
│   └── logs/               # Log files
└── docs/                # Documentation
    └── IMPLEMENTATION_PLAN.md
```

## 🎯 What This System Does

1. **Researches** each investor (website + LinkedIn)
2. **Analyzes** their investment focus and portfolio
3. **Generates** personalized emails using AI (GPT-4)
4. **Sends** emails via Gmail with smart delays
5. **Tracks** all campaign metrics in database

## 📊 Expected Results

- **Response Rate**: 5-8% (vs 1-2% with generic emails)
- **Time Saved**: 10+ hours/week on research
- **Cost**: ~$55-115/month (AI + scraping)

## 🔧 Configuration

Key settings in `.env`:

- `MAX_EMAILS_PER_RUN`: Emails per execution (default: 260)
- `MIN_DELAY_SECONDS`: Minimum delay between emails (default: 120)
- `OPENAI_MODEL`: AI model to use (gpt-3.5-turbo or gpt-4)
- `MIN_FIT_SCORE`: Minimum investor match score (0.0-1.0)

## 🐛 Troubleshooting

**Gmail Authentication Error:**
- Enable 2FA on Gmail
- Generate new App Password
- Use that 16-char password in `.env`

**OpenAI Rate Limit:**
- Add delays between API calls
- Upgrade your OpenAI tier
- Use GPT-3.5-turbo instead of GPT-4

**Database Locked:**
- Close any database browser tools
- Check no other scripts are running

## 📚 Documentation

- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Complete system architecture
- [Component Guide](docs/COMPONENT_GUIDE.md) - Detailed module docs
- [Setup Guide](docs/SETUP_GUIDE.md) - Step-by-step installation

## 🔐 Security

- Never commit `.env` to GitHub
- Rotate API keys regularly
- Use separate Gmail account for sending
- Monitor for unusual activity

## 📞 Support

For issues or questions, check the logs:
```bash
tail -f data/logs/email_sender.log
```

## 📝 License

[Add your license here]

---

**Built for Resilution's seed round outreach** 🚀
