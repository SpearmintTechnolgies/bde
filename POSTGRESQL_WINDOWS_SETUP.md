# PostgreSQL Installation & Setup Guide (Windows)

## 📥 Step 1: Download PostgreSQL

### Option A: PostgreSQL Installer (Recommended)
1. Go to: https://www.postgresql.org/download/windows/
2. Click "Download the installer"
3. Download **PostgreSQL 16** (or latest version) for Windows x86-64

### Option B: Direct Link
- Download from: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- Choose: **PostgreSQL 16.x - Windows x86-64**

## 🔧 Step 2: Install PostgreSQL

1. **Run the installer** (postgresql-16.x-windows-x64.exe)

2. **Installation Directory**: 
   - Default: `C:\Program Files\PostgreSQL\16`
   - Click **Next**

3. **Select Components**:
   - ✅ PostgreSQL Server (required)
   - ✅ pgAdmin 4 (GUI tool - recommended)
   - ✅ Command Line Tools (required)
   - ✅ Stack Builder (optional)
   - Click **Next**

4. **Data Directory**:
   - Default: `C:\Program Files\PostgreSQL\16\data`
   - Click **Next**

5. **Password**:
   - Set password for `postgres` superuser
   - **REMEMBER THIS PASSWORD!** You'll need it for your `.env` file
   - Example: `postgres123` (use something secure in production)
   - Click **Next**

6. **Port**:
   - Default: `5432`
   - Click **Next**

7. **Locale**:
   - Default: `[Default locale]`
   - Click **Next**

8. **Summary**:
   - Review settings
   - Click **Next** to install

9. **Installation Progress**:
   - Wait for installation to complete (2-5 minutes)

10. **Stack Builder**:
    - Uncheck "Launch Stack Builder at exit" (not needed now)
    - Click **Finish**

## ✅ Step 3: Verify Installation

Open **Command Prompt** or **PowerShell** and test:

```powershell
# Check PostgreSQL version
psql --version

# Should show: psql (PostgreSQL) 16.x
```

If command not found, add to PATH:
1. Search Windows for "Environment Variables"
2. Edit System Environment Variables
3. Add: `C:\Program Files\PostgreSQL\16\bin`
4. Restart terminal

## 🗄️ Step 4: Create Database

### Method 1: Using Command Line (psql)

```powershell
# Connect to PostgreSQL as superuser
psql -U postgres

# Enter password when prompted (the one you set during installation)

# Create database
CREATE DATABASE bde_email_automation;

# Verify database was created
\l

# Exit psql
\q
```

### Method 2: Using pgAdmin 4 (GUI)

1. **Open pgAdmin 4**
   - Start Menu → PostgreSQL 16 → pgAdmin 4

2. **Connect to Server**
   - Left panel → Servers → PostgreSQL 16
   - Enter your password

3. **Create Database**
   - Right-click "Databases"
   - Create → Database
   - Database name: `bde_email_automation`
   - Owner: `postgres`
   - Click **Save**

## 🔐 Step 5: Configure Your Project

Create `.env` file in your project folder:

```bash
cd "d:\web peojects\email-automation-spearmmint\bde"
Copy-Item .env.example .env
```

Edit `.env` with your PostgreSQL credentials:

```env
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bde_email_automation
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here  # ⚠️ Replace with your actual password!

# Gmail SMTP
GMAIL_USER=your.email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password

# OpenAI API (for AI personalization)
OPENAI_API_KEY=sk-...your_openai_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Batch Processing
BATCH_SIZE=50
EMAIL_DELAY=2
```

## 🧪 Step 6: Test Database Connection

```powershell
cd "d:\web peojects\email-automation-spearmmint\bde"

# Install dependencies if not already installed
pip install -r requirements.txt

# Test database setup
python test_db_setup.py
```

Expected output:
```
✓ Config validation passed
✓ Database connection successful
✓ Schema created successfully
✓ CRUD operations working
✓ All tests passed!
```

## 🚀 Step 7: Initialize Database Schema

```powershell
# Create tables
python test_db_setup.py

# Import contacts from CSV
python import_contacts.py
```

## 🛠️ Useful PostgreSQL Commands

### Connect to database:
```bash
psql -U postgres -d bde_email_automation
```

### List databases:
```sql
\l
```

### List tables:
```sql
\dt
```

### View table structure:
```sql
\d contacts
\d campaigns
\d email_logs
```

### Check contact count:
```sql
SELECT COUNT(*) FROM contacts;
```

### View campaigns:
```sql
SELECT id, name, status, created_at FROM campaigns;
```

### View recent email logs:
```sql
SELECT c.email, c.company, el.status, el.sent_at 
FROM email_logs el
JOIN contacts c ON el.contact_id = c.id
ORDER BY el.sent_at DESC
LIMIT 10;
```

### Exit psql:
```sql
\q
```

## 📍 PostgreSQL File Locations

- **Installation**: `C:\Program Files\PostgreSQL\16`
- **Data Directory**: `C:\Program Files\PostgreSQL\16\data`
- **Config File**: `C:\Program Files\PostgreSQL\16\data\postgresql.conf`
- **Logs**: `C:\Program Files\PostgreSQL\16\data\log`

## 🔧 Troubleshooting

### Problem: "psql: command not found"
**Solution**: Add PostgreSQL to PATH
```powershell
$env:Path += ";C:\Program Files\PostgreSQL\16\bin"
```

### Problem: "password authentication failed"
**Solution**: 
1. Check your password in `.env` matches installation password
2. Or reset password:
```sql
ALTER USER postgres WITH PASSWORD 'new_password';
```

### Problem: "connection refused"
**Solution**: Start PostgreSQL service
1. Open Services (Win + R → `services.msc`)
2. Find "postgresql-x64-16"
3. Right-click → Start

### Problem: Port 5432 already in use
**Solution**: 
1. Check what's using the port:
```powershell
netstat -ano | findstr :5432
```
2. Change PostgreSQL port in `postgresql.conf` and `.env`

## 🎯 Your Connection String

Based on your setup, your database connection string is:

```
postgresql://postgres:your_password@localhost:5432/bde_email_automation
```

This is automatically built by `Config.get_database_url()` in your project!

## ✅ Quick Checklist

- [ ] PostgreSQL 16 installed
- [ ] Password saved (you'll need it!)
- [ ] Database `bde_email_automation` created
- [ ] `.env` file created with correct password
- [ ] `pip install -r requirements.txt` completed
- [ ] `python test_db_setup.py` successful
- [ ] Ready to import contacts and send emails! 🚀

## 📚 Resources

- **Official Docs**: https://www.postgresql.org/docs/
- **pgAdmin Docs**: https://www.pgadmin.org/docs/
- **psql Commands**: https://www.postgresql.org/docs/current/app-psql.html

---

**Need Help?** If you get stuck, check:
1. PostgreSQL service is running in Services
2. Password in `.env` matches your installation password
3. Database name is `bde_email_automation`
4. Port 5432 is not blocked by firewall
