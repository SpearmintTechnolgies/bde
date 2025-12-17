# Quick Reference - BDE Email Automation

## Installation

```bash
# 1. Install PostgreSQL (if not installed)
# Windows: Download from postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql

# 2. Create database
psql -U postgres
CREATE DATABASE bde_email_automation;
\q

# 3. Install Python packages
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env with your PostgreSQL password

# 5. Initialize database
python test_db_setup.py
```

## Common Commands

```bash
# Import contacts from CSV
python import_contacts.py

# Run campaign (batch mode)
python run_campaign.py --campaign-id 1 --batch-size 50

# Test database connection
python test_db_setup.py
```

## Python Quick Reference

```python
from modules.database import Database, CampaignStatus, EmailStatus
from modules.email_sender import EmailSender

# Initialize database
db = Database()

# Add contact
db.add_contact({
    'email': 'test@example.com',
    'full_name': 'John Doe',
    'company': 'Acme Corp'
})

# Import contacts in batches
contacts = [...]  # Your contact list
db.add_contacts_batch(contacts, batch_size=50)

# Create campaign
campaign_id = db.create_campaign(
    name="My Campaign",
    subject="Email Subject",
    body_text="Hi {name}, message here..."
)

# Get campaign stats
stats = db.get_campaign_stats(campaign_id)
print(f"Sent: {stats['sent']}, Pending: {stats['pending']}")

# Get next batch to send
batch = db.get_batch_to_send(campaign_id, batch_size=50)

# Send emails
sender = EmailSender(db)
results = sender.send_batch(campaign_id, batch_size=50)

# Update campaign status
db.update_campaign_status(campaign_id, CampaignStatus.COMPLETED)

# Close connection
db.close()
```

## Configuration (.env)

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bde_email_automation
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Email
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password

# Batch Settings
BATCH_SIZE=50
MAX_EMAILS_PER_RUN=260
MIN_DELAY_SECONDS=120
MAX_DELAY_SECONDS=180
```

## PostgreSQL Commands

```sql
-- View all contacts
SELECT * FROM contacts LIMIT 10;

-- Count contacts
SELECT COUNT(*) FROM contacts;

-- View campaigns
SELECT * FROM campaigns;

-- Campaign progress
SELECT status, COUNT(*) 
FROM email_logs 
WHERE campaign_id = 1 
GROUP BY status;

-- Recent sends
SELECT c.email, c.company, e.status, e.sent_at
FROM email_logs e
JOIN contacts c ON e.contact_id = c.id
ORDER BY e.sent_at DESC
LIMIT 20;

-- Pending contacts for campaign
SELECT c.* 
FROM contacts c
LEFT JOIN email_logs e ON c.id = e.contact_id AND e.campaign_id = 1
WHERE e.id IS NULL;
```

## File Structure

```
Key Files:
├── config/settings.py           # Configuration
├── modules/database.py          # PostgreSQL ORM
├── modules/email_sender.py      # Batch email sender
├── modules/csv_loader.py        # CSV import
├── test_db_setup.py            # DB initialization
├── import_contacts.py          # Import script
├── run_campaign.py             # Campaign runner
└── requirements.txt            # Dependencies

Docs:
├── IMPLEMENTATION_SUMMARY.md   # Full implementation details
├── POSTGRESQL_SETUP.md         # Setup guide
└── QUICK_REFERENCE.md          # This file
```

## Email Templates

Use these placeholders:
- `{name}` - First name or full name
- `{first_name}` - First name only
- `{full_name}` - Full name
- `{company}` - Company name
- `{job_title}` - Job title

Example:
```
Hi {name},

I'm reaching out to {company}...
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Start PostgreSQL: `brew services start postgresql` |
| Database not found | Create it: `CREATE DATABASE bde_email_automation;` |
| Auth failed | Check POSTGRES_PASSWORD in .env |
| Table not found | Run `python test_db_setup.py` |
| Import fails | Check CSV format, required: email, name, company |

## Status Values

**Email Status:**
- `pending` - Not sent yet
- `sent` - Successfully sent
- `failed` - Send failed
- `bounced` - Email bounced

**Campaign Status:**
- `draft` - Being created
- `active` - Currently sending
- `paused` - Temporarily stopped
- `completed` - All emails sent

## Best Practices

1. **Start Small**: Test with `--batch-size 10` first
2. **Monitor Progress**: Check stats between batches
3. **Use Delays**: Keep MIN_DELAY_SECONDS at least 120
4. **Test DB**: Run `test_db_setup.py` before campaigns
5. **Backup**: Keep original CSV file safe
6. **Check Logs**: Monitor `data/logs/email_sender.log`

## Support

Check these files for help:
- [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) - Detailed setup
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Full docs
- `data/logs/email_sender.log` - Runtime logs
