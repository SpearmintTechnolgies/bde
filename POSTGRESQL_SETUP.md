# BDE Email Automation - PostgreSQL Setup Guide

## Overview

This system now uses **PostgreSQL** for robust contact management and email campaign tracking with **batch processing** to save resources.

## Key Features

✅ **PostgreSQL Database** - Scalable, reliable data storage  
✅ **Batch Processing** - Process contacts in chunks (default: 50 at a time)  
✅ **Status Tracking** - Track every email (pending, sent, failed, bounced)  
✅ **Campaign Management** - Create and manage multiple campaigns  
✅ **Safe to Resume** - Stop and restart anytime without duplicate sends  
✅ **Resource Efficient** - Processes contacts in batches to save memory  

## Database Schema

### Tables

1. **contacts** - Contact information
   - email, full_name, company, job_title, etc.
   - Automatic deduplication by email

2. **campaigns** - Email campaigns
   - name, subject, body_text, body_html
   - status (draft, active, paused, completed)

3. **email_logs** - Email send tracking
   - Links contacts + campaigns
   - status (pending, sent, failed, bounced)
   - sent_at timestamp

## Setup Instructions

### 1. Install PostgreSQL

**Windows:**
- Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Install and remember your postgres password

**Mac:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE bde_email_automation;

# Exit
\q
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
# IMPORTANT: Set your PostgreSQL password!
```

### 5. Initialize Database

```bash
python test_db_setup.py
```

This will:
- Test PostgreSQL connection
- Create all tables and indexes
- Verify everything works

## Usage

### Step 1: Import Contacts from CSV

```bash
python import_contacts.py
```

This imports contacts from `contacts.csv` in batches (default: 50 at a time).

**CSV Required Columns:**
- Email (required)
- Full name or First name + Last name
- Company
- Company Website (optional)

### Step 2: Create a Campaign

Use Python:

```python
from modules.database import Database

db = Database()
campaign_id = db.create_campaign(
    name="Seed Round Outreach",
    subject="Resilution's seed round overview",
    body_text="Hi {name},\n\nI am reaching out...",
    body_html="<p>Hi {name},</p><p>I am reaching out...</p>"
)

print(f"Campaign ID: {campaign_id}")
```

### Step 3: Run Campaign in Batches

```bash
# Send 50 emails at a time (safe, resource-efficient)
python run_campaign.py --campaign-id 1 --batch-size 50

# Send only 2 batches as a test
python run_campaign.py --campaign-id 1 --batch-size 50 --max-batches 2
```

The script will:
1. Send a batch of emails
2. Update status in PostgreSQL
3. Ask if you want to continue to the next batch
4. Track progress automatically

**Safe to stop and resume!** The system tracks what's been sent, so you can run it again later without duplicates.

## Batch Processing Benefits

### Why Batches?
- **Save Memory** - Don't load all contacts at once
- **Save Resources** - Process incrementally
- **Easy to Monitor** - See progress batch by batch
- **Easy to Stop** - Pause between batches
- **Resume Anytime** - Database tracks everything

### Configuration

In `.env`:
```
BATCH_SIZE=50  # Process 50 contacts at a time
MAX_EMAILS_PER_RUN=260  # Overall daily limit
```

## Email Templates

Use placeholders in your email templates:

- `{name}` - First name or full name
- `{first_name}` - First name
- `{full_name}` - Full name
- `{company}` - Company name
- `{job_title}` - Job title

Example:
```
Hi {name},

I am reaching out to {company}...
```

## Monitoring Progress

### Check Campaign Stats

```python
from modules.database import Database

db = Database()
stats = db.get_campaign_stats(campaign_id=1)

print(f"Total contacts: {stats['total_contacts']}")
print(f"Sent: {stats['sent']}")
print(f"Failed: {stats['failed']}")
print(f"Pending: {stats['pending']}")
```

### View in PostgreSQL

```bash
psql -U postgres -d bde_email_automation

# View contacts
SELECT * FROM contacts LIMIT 10;

# View campaign progress
SELECT status, COUNT(*) FROM email_logs WHERE campaign_id = 1 GROUP BY status;

# View recent sends
SELECT c.email, c.company, e.status, e.sent_at 
FROM email_logs e 
JOIN contacts c ON e.contact_id = c.id 
ORDER BY e.sent_at DESC 
LIMIT 20;
```

## Common Operations

### Get Total Contacts

```python
db = Database()
count = db.get_all_contacts_count()
print(f"Total contacts: {count}")
```

### Get Pending Contacts for Campaign

```python
pending = db.get_pending_contacts(campaign_id=1, limit=10)
print(f"Next {len(pending)} contacts to email")
```

### Add Individual Contact

```python
contact = {
    'email': 'investor@example.com',
    'full_name': 'John Smith',
    'company': 'Smith Ventures'
}

contact_id = db.add_contact(contact)
```

## Troubleshooting

### "Connection refused"
- Make sure PostgreSQL is running
- Check host/port in `.env` (default: localhost:5432)

### "Database does not exist"
- Create it: `CREATE DATABASE bde_email_automation;`

### "Authentication failed"
- Check POSTGRES_PASSWORD in `.env`
- Try: `psql -U postgres` to test login

### "Table does not exist"
- Run: `python test_db_setup.py`
- This creates all tables

## Next Steps: Frontend (Coming Soon)

The frontend will provide:
- CSV upload interface
- Campaign creation UI
- Real-time send status dashboard
- Progress monitoring

But all the core backend is ready to use now!

## Environment Variables

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bde_email_automation
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Email
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Batch Processing
BATCH_SIZE=50
MAX_EMAILS_PER_RUN=260
MIN_DELAY_SECONDS=120
MAX_DELAY_SECONDS=180
```

## Architecture

```
┌─────────────┐
│ contacts.csv│
└──────┬──────┘
       │
       ▼
┌─────────────────┐         ┌──────────────┐
│ import_contacts │────────▶│ PostgreSQL   │
└─────────────────┘         │  - contacts  │
                            │  - campaigns │
┌─────────────────┐         │  - email_logs│
│ run_campaign    │◀───────▶└──────────────┘
│ (batch by batch)│
└─────────────────┘
       │
       ▼
┌─────────────────┐
│ Email Sent!     │
│ Status Tracked  │
└─────────────────┘
```

## Support

For issues:
1. Check `.env` configuration
2. Run `python test_db_setup.py`
3. Check logs in `data/logs/email_sender.log`
