# Web Scraping & AI Personalization Guide

## 🎯 Overview

The system now includes **intelligent web scraping** and **AI-powered personalization** to create highly targeted, relevant emails based on real company data.

## 📊 Complete Data Flow with AI

```
CSV Import
    ↓
PostgreSQL (Contacts)
    ↓
[Web Scraper] ─────→ Company Website
    ↓                      ↓
Scraped Data          Extract:
(stored in DB)        - Description
    ↓                 - Recent news
    ↓                 - Products
    ↓                 - Team size
    ↓                 - Raw text
    ↓
[AI Personalizer] ←── Scraped Data + Contact Info
    ↓
OpenAI GPT Model
    ↓
Personalized Email:
- Custom opening line
- Relevant talking points
- Specific company references
- Personalized subject
    ↓
[Email Sender] ─────→ Gmail SMTP
    ↓
Email Sent!
    ↓
Status logged in PostgreSQL
```

## 🔧 How It Works

### **1. Web Scraping Module** ([modules/web_scraper.py](modules/web_scraper.py))

**What it does:**
- Visits company website
- Extracts meaningful information
- Cleans and structures data for AI processing

**What it scrapes:**
```python
{
    'description': 'Company overview from meta tags',
    'keywords': ['AI', 'SaaS', 'Enterprise'],
    'recent_news': ['Company raises $10M', 'Launches new product'],
    'products': ['Product A', 'Service B'],
    'team_size': 'Medium (10-50)',
    'social_links': {'linkedin': '...', 'twitter': '...'},
    'raw_text': 'Full page content for AI analysis...',
    'meta_info': {'title': '...', 'author': '...'}
}
```

**Example:**
```python
from modules.web_scraper import WebScraper

scraper = WebScraper()
data = scraper.scrape_website("https://resilution.io")

print(data['description'])
# Output: "Resilution connects SMEs with investors through blockchain..."

print(data['recent_news'])
# Output: ['Raises $2M seed round', 'Launches supply chain financing']
```

**How it works:**
1. **Fetch HTML** - Uses `requests` with retry logic
2. **Parse with BeautifulSoup** - Extract structured data
3. **Find key elements:**
   - Meta tags (description, keywords)
   - Headers (H1, H2, H3)
   - Article/news sections
   - Product listings
   - Team member sections
4. **Clean text** - Remove scripts, styles, navigation
5. **Return structured data** - JSON format for AI

**Smart features:**
- Tries to find About page automatically
- Handles missing data gracefully
- Limits text length for AI token limits
- Extracts social media links
- Estimates team size from page structure

---

### **2. AI Personalization Module** ([modules/ai_personalizer.py](modules/ai_personalizer.py))

**What it does:**
- Takes scraped data + contact info
- Sends to OpenAI GPT model
- Generates highly personalized email content

**Personalization levels:**

```
Level 1: Basic Template
"Hi {name}, I am reaching out..."

Level 2: Company Context
"Hi John, I noticed Acme Corp is in fintech..."

Level 3: AI Personalized (with scraping)
"Hi John, I saw that Acme Corp recently launched your supply 
chain financing product. Given your focus on SME lending and 
recent $10M Series A, I thought Resilution's on-chain revenue 
sharing might align with your roadmap..."
```

**What AI generates:**

```python
{
    'personalized_opening': 'Hi John, I was impressed by Acme Corp\'s...',
    'personalized_body': 'Full email body with specific references...',
    'personalized_subject': 'Acme Corp + Resilution: SME Financing Synergy',
    'talking_points': [
        'Recent $10M funding round',
        'Supply chain financing product',
        'Focus on SME market'
    ],
    'confidence_score': 0.85  # How confident AI is about personalization
}
```

**How AI works:**

1. **Build Context:**
```python
context = f"""
Recipient: John Smith
Title: VP of Partnerships
Company: Acme Corp

Company Description: {scraped_data['description']}
Recent News: {scraped_data['recent_news']}
Products: {scraped_data['products']}
Website Content: {scraped_data['raw_text'][:800]}
"""
```

2. **Send to OpenAI:**
```python
response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a business development expert..."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7  # Balance creativity and consistency
)
```

3. **Extract personalized content** from AI response

4. **Validate and return** structured result

**Example AI Prompt:**
```
You are writing a personalized business development email.

Context about recipient:
Recipient: John Smith
Title: VP of Partnerships
Company: Acme Corp
Company Description: Acme Corp provides SME lending solutions...
Recent News: Raised $10M Series A, Launched supply chain financing
Products: SME Loans, Invoice Financing, Supply Chain Finance

Base template (for reference):
"Hi {name}, I am reaching out to share Resilution, a platform 
that lets investors back real world SME revenue streams..."

Task:
1. Generate a personalized email body that references specific 
   information about their company
2. Include 2-3 relevant talking points based on their business
3. Keep the email concise (150-200 words)
4. Include a clear call-to-action

Return as JSON: {"body": "...", "talking_points": [...]}
```

**AI Output:**
```json
{
  "body": "Hi John,\n\nI was excited to see Acme Corp's recent $10M Series A and the launch of your supply chain financing product. As someone focused on SME lending, you're clearly aligned with addressing the massive financing gap facing small businesses.\n\nAt Resilution, we're tackling a similar problem from a different angle—connecting SMEs directly with investors through blockchain-backed revenue sharing. Our smart contracts automate distributions based on real CRM data, providing the transparency and programmatic execution that traditional lending lacks.\n\nGiven your focus on supply chain finance and SME markets, I think there could be interesting synergies between our approaches. Would you be open to a quick call to explore potential collaboration?\n\nBest,\nMatthew",
  "talking_points": [
    "Recent $10M Series A funding",
    "New supply chain financing product launch",
    "Shared focus on SME market",
    "Potential synergies in alternative financing"
  ],
  "confidence": 0.92
}
```

---

### **3. Enhanced Campaign Runner** ([run_campaign_ai.py](run_campaign_ai.py))

**Usage:**
```bash
# Run with AI personalization and web scraping
python run_campaign_ai.py --campaign-id 1 --batch-size 10 --use-ai --use-scraping

# Run with only scraping (no AI)
python run_campaign_ai.py --campaign-id 1 --batch-size 10 --use-scraping

# Run without AI or scraping (basic template)
python run_campaign_ai.py --campaign-id 1 --batch-size 50
```

**What it does per contact:**

```
For each contact in batch:
    ↓
1. Get contact from database
    ↓
2. Scrape company website (if --use-scraping)
   - Visit website
   - Extract data
   - Save to database (scraped_data field)
    ↓
3. AI Personalization (if --use-ai)
   - Send scraped data + contact to OpenAI
   - Get personalized content
   - Replace template with AI content
    ↓
4. Send personalized email via SMTP
    ↓
5. Log result in database (sent/failed)
    ↓
6. Wait (delay to avoid spam detection)
```

**Console output:**
```
===================================================================
AI-POWERED EMAIL CAMPAIGN
===================================================================

📧 Campaign: Seed Round Outreach
   Subject: Resilution's seed round overview
   AI Personalization: ✅ Enabled
   Web Scraping: ✅ Enabled
   Batch Size: 10 contacts

===================================================================
BATCH 1
===================================================================
📊 Processing 10 contacts...

[1/10] john@acmecorp.com - Acme Corp
  🔍 Scraping https://acmecorp.com...
     ✓ Found: Acme Corp provides SME lending solutions...
  🤖 Personalizing with AI...
     ✓ Personalized (confidence: 0.92)
     Talking points: Recent $10M funding, Supply chain financing
  📤 Sending email...
  ✅ Sent successfully
  ⏳ Waiting 120s before next email...

[2/10] jane@techventures.com - Tech Ventures
  🔍 Scraping https://techventures.com...
     ✓ Found: Tech Ventures invests in early-stage fintech...
  🤖 Personalizing with AI...
     ✓ Personalized (confidence: 0.88)
     Talking points: Focus on fintech, Recent portfolio exit
  📤 Sending email...
  ✅ Sent successfully
  ⏳ Waiting 120s before next email...

...

===================================================================
BATCH 1 COMPLETE
===================================================================
✅ Sent: 9
❌ Failed: 1

📊 Campaign Progress:
   Total Contacts: 1000
   Sent: 9
   Failed: 1
   Pending: 990

▶ Continue to next batch? (y/n):
```

---

## 💾 Data Storage

### **Database Schema (Updated)**

```sql
-- Contacts table with scraped_data field
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    company VARCHAR(255),
    company_website VARCHAR(500),
    job_title VARCHAR(255),
    
    -- AI/Scraping fields
    scraped_data TEXT,  -- JSON string of scraped website data
    fit_score FLOAT,    -- AI-calculated fit score (optional)
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Example scraped_data JSON:**
```json
{
  "url": "https://acmecorp.com",
  "description": "Acme Corp provides...",
  "keywords": ["SME", "lending", "fintech"],
  "recent_news": ["Raises $10M", "Launches product"],
  "products": ["SME Loans", "Invoice Financing"],
  "team_size": "Medium (10-50)",
  "social_links": {
    "linkedin": "https://linkedin.com/company/acme",
    "twitter": "https://twitter.com/acmecorp"
  },
  "raw_text": "Full website text for AI...",
  "meta_info": {"title": "Acme Corp - SME Lending"}
}
```

---

## 🚀 Complete Example Workflow

### **Step 1: Import contacts with websites**

CSV file:
```csv
Email,Full Name,Company,Company Website,Job Title
john@acme.com,John Smith,Acme Corp,https://acmecorp.com,VP Partnerships
jane@techvc.com,Jane Doe,Tech Ventures,https://techventures.com,Partner
```

```bash
python import_contacts.py
```

### **Step 2: Create campaign**

```python
from modules.database import Database

db = Database()
campaign_id = db.create_campaign(
    name="Seed Round Outreach",
    subject="Resilution's seed round overview",
    body_text="""Hi {name},

I am reaching out to share Resilution, a platform that connects 
SMEs with investors through blockchain-backed revenue sharing.

We're raising a $2M seed round to scale our platform.

Would you be open to a quick call?

Best,
Matthew"""
)

print(f"Campaign ID: {campaign_id}")
```

### **Step 3: Run AI-powered campaign**

```bash
# Start with small batch to test
python run_campaign_ai.py \
    --campaign-id 1 \
    --batch-size 5 \
    --use-ai \
    --use-scraping \
    --max-batches 1
```

**What happens:**
1. ✅ Gets 5 pending contacts
2. ✅ Scrapes each company website
3. ✅ AI generates personalized emails
4. ✅ Sends via Gmail SMTP
5. ✅ Logs everything in database

**Result:**
- Each email is **highly personalized** with specific company references
- Mentions recent news, products, or achievements
- Sounds like it was written by a human who researched the company

---

## ⚙️ Configuration

Add to `.env`:
```env
# OpenAI (required for AI personalization)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4 for better quality

# Scraping settings
SCRAPING_TIMEOUT=10
MAX_RETRIES=3
USER_AGENT=Mozilla/5.0...
```

---

## 💰 Cost Considerations

### **API Costs:**
- **OpenAI GPT-3.5-turbo**: ~$0.002 per email
- **OpenAI GPT-4**: ~$0.03 per email
- **Web scraping**: Free (just HTTP requests)

### **Batch size recommendations:**
- **With AI**: 5-10 contacts per batch (allows monitoring costs)
- **Without AI**: 50+ contacts per batch (faster, cheaper)

---

## 🎯 Best Practices

### **When to use AI personalization:**
✅ High-value prospects (VCs, strategic partners)  
✅ Smaller, targeted lists (<500 contacts)  
✅ Cold outreach where personalization matters  
❌ Large bulk campaigns (too expensive)  
❌ Already-warm leads (basic template is fine)  

### **Web scraping tips:**
- Always scrape before campaign (not during)
- Cache scraped data in database
- Handle failures gracefully (not all sites allow scraping)
- Respect robots.txt and rate limits

### **Quality control:**
1. **Test with 1-2 contacts first**
2. **Review AI output** for accuracy
3. **Check confidence scores** (low = review manually)
4. **Monitor bounce rates**

---

## 🔍 Monitoring & Debugging

### **Check AI personalization quality:**
```python
from modules.database import Database
import json

db = Database()
contact = db.get_contact_by_email('john@acme.com')

# View scraped data
session = db.get_session()
from modules.database import Contact
c = session.query(Contact).filter(Contact.email == contact['email']).first()
scraped = json.loads(c.scraped_data) if c.scraped_data else {}

print("Scraped data:")
print(f"Description: {scraped.get('description')}")
print(f"Recent news: {scraped.get('recent_news')}")
```

### **Test scraping manually:**
```python
from modules.web_scraper import WebScraper

scraper = WebScraper()
data = scraper.scrape_website("https://example.com")

print(json.dumps(data, indent=2))
```

### **Test AI personalization:**
```python
from modules.ai_personalizer import AIPersonalizer

ai = AIPersonalizer()
contact = {'email': 'test@example.com', 'full_name': 'John Doe', 'company': 'Acme Corp'}
scraped_data = {...}  # Your scraped data

result = ai.personalize_email(contact, scraped_data, base_template="Hi {name}...")
print(result['personalized_body'])
```

---

## 📚 Summary

**Without AI/Scraping:**
```
"Hi John, I am reaching out to share Resilution..."
```

**With AI/Scraping:**
```
"Hi John, I was excited to see Acme Corp's recent $10M 
Series A and your new supply chain financing product. 
Given your focus on SME lending, Resilution's blockchain-
backed revenue sharing could provide interesting synergies 
with your approach..."
```

**The difference:** Highly personalized, relevant, researched emails that get responses! 🎯
