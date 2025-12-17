# 📊 CSV Column Selection Guide

## What We Use from Your CSV

Your CSV has **many columns**, but we only need a few! Here's what we use:

---

## ✅ **REQUIRED COLUMNS (Must Have)**

### 1. **Email address**
- **Why:** To send the email
- **Variations accepted:** "Email", "email address", "email_address", "e-mail"
- **Example:** `john@vc.com`

### 2. **Full name** (or First name + Last name)
- **Why:** Personalization ("Hi John,")
- **Variations accepted:** "Full name", "name", "first name + last name"
- **Example:** `John Smith`

### 3. **Company**
- **Why:** Know which firm they represent
- **Variations accepted:** "Company", "company name", "organization", "firm"
- **Example:** `ABC Ventures`

### 4. **Company Website**
- **Why:** This is what we SCRAPE for information!
- **Variations accepted:** "website", "company website", "url", "web"
- **Example:** `https://abcvc.com` or `abcvc.com`

---

## 📋 **OPTIONAL COLUMNS (Nice to Have)**

### 5. **LinkedIn URL**
- **Why:** Backup source if website scraping fails
- **Variations accepted:** "linkedin", "LinkedIn URL", "linkedin_url"
- **Example:** `https://linkedin.com/in/johnsmith`

### 6. **Job title**
- **Why:** Useful context (Partner vs Analyst = different approach)
- **Variations accepted:** "job title", "title", "position", "role"
- **Example:** `Partner`, `Managing Director`

---

## ❌ **COLUMNS WE IGNORE (Don't Need)**

All other columns are **automatically skipped**:

- ❌ **Industry** → We discover this by scraping their website
- ❌ **Department** → Not needed
- ❌ **Phone number** → We don't call, we email
- ❌ **Twitter** → Not used
- ❌ **City, State, Postal code, Country** → Not needed for emails
- ❌ **Notes, Source, Owner** → Your internal tracking, we skip
- ❌ **Sending status** → We track this in our own database
- ❌ **Dates (creation, last update, etc.)** → Not needed
- ❌ **Verification, Confidence, Tags** → Not needed

---

## 🔄 **How It Works**

### Input (Your CSV):
```csv
First name,Last name,Full name,Job title,Company,Email address,Company Website,LinkedIn URL,Phone,Twitter,City,State,...
John,Smith,John Smith,Partner,ABC Ventures,john@abcvc.com,https://abcvc.com,linkedin.com/in/john,555-1234,@john,NYC,NY,...
```

### What We Extract:
```python
{
    'email': 'john@abcvc.com',
    'name': 'John Smith',
    'company': 'ABC Ventures',
    'website': 'https://abcvc.com',
    'linkedin_url': 'https://linkedin.com/in/john',  # optional
    'title': 'Partner'  # optional
}
```

### What We Do With It:
1. **Email** → Send the personalized email here
2. **Name** → "Hi John," in the email
3. **Company** → Context for AI
4. **Website** → **SCRAPE THIS** for investment focus, portfolio, etc.
5. **LinkedIn** → Backup info if website fails
6. **Title** → Adjust tone (Partner vs Junior Associate)

---

## 🎯 **Why This Approach?**

### We **SCRAPE** the website to get:
- Investment focus (fintech, web3, B2B SaaS, etc.)
- Portfolio companies (Stripe, Coinbase, etc.)
- Recent news (Announced new fund, etc.)
- Company description

### We **DON'T** need this in CSV because:
- ✅ Scraping gets fresh, up-to-date info
- ✅ More accurate than static CSV data
- ✅ Discovers details not in your CSV
- ✅ AI generates better emails with real data

---

## 📝 **CSV Validation**

The system automatically:
1. ✅ Detects column names (case-insensitive)
2. ✅ Validates email format
3. ✅ Cleans URLs (adds https://, removes trailing /)
4. ✅ Skips rows with missing required fields
5. ✅ Reports errors (invalid email, missing company, etc.)

---

## 🧪 **Test Your CSV**

You can preview what the system will extract:

```python
from modules.csv_loader import preview_csv_columns

info = preview_csv_columns('data/contacts.csv')

print("Total columns:", info['total_columns'])
print("Detected:")
print("  Email column:", info['detected_columns']['email'])
print("  Name column:", info['detected_columns']['name'])
print("  Company column:", info['detected_columns']['company'])
print("  Website column:", info['detected_columns']['website'])
print("\nSample row:", info['sample_row'])
```

---

## ✅ **Summary**

**You keep your CSV with all columns** (don't delete anything!)

**We automatically:**
- ✅ Extract only what we need
- ✅ Ignore everything else
- ✅ Handle different column names
- ✅ Validate data quality
- ✅ Clean and normalize values

**Simple as that!** 🎉
