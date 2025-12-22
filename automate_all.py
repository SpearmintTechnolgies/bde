"""
BDE - Fully Automated Email Campaign Runner
Processes CSV and sends personalized emails automatically
"""
import csv
import time
from pathlib import Path
from datetime import datetime
from modules.database import Database
from modules.web_scraper import WebScraper
from modules.email_sender import EmailSender
try:
    from modules.ai_personalizer import AIPersonalizer
    AI_AVAILABLE = True
except:
    AI_AVAILABLE = False
    print("⚠️  AI Personalizer not available - using template mode")

def log(msg):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def update_campaign_status(current=None, total=None, step=None, scraped=None, ai_processed=None, sent=None, failed=None):
    """Update global campaign status for web interface"""
    try:
        from web_interface import campaign_status, add_log
        if current is not None:
            campaign_status['current'] = current
        if total is not None:
            campaign_status['total'] = total
        if step is not None:
            campaign_status['current_step'] = step
        if scraped is not None:
            campaign_status['scraped_count'] = scraped
        if ai_processed is not None:
            campaign_status['ai_processed_count'] = ai_processed
        if sent is not None:
            campaign_status['sent_count'] = sent
        if failed is not None:
            campaign_status['failed_count'] = failed
    except:
        pass  # Running standalone, no web interface

def automated_campaign(csv_path, delay_seconds=5):
    """
    Fully automated campaign pipeline:
    1. Load CSV contacts
    2. For each contact:
       - Scrape company website
       - Generate personalized email (with AI if available)
       - Send email
       - Save to database
       - Wait before next
    """
    db = Database()
    session = db.get_session()
    scraper = WebScraper()
    sender = EmailSender(db)
    ai = AIPersonalizer() if AI_AVAILABLE else None
    
    log("=" * 70)
    log("🚀 AUTOMATED EMAIL CAMPAIGN STARTED")
    log("=" * 70)
    log(f"CSV File: {csv_path}")
    log(f"AI Personalization: {'✅ Enabled' if ai else '❌ Template Mode'}")
    log(f"Delay between emails: {delay_seconds}s")
    
    try:
        from web_interface import add_log as web_log
    except:
        web_log = lambda msg, level='info': None
    
    # Step 1: Load CSV
    log("\n📂 Step 1: Loading contacts from CSV...")
    web_log("📂 Loading contacts from CSV...", 'info')
    update_campaign_status(step="Loading CSV")
    
    contacts = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = (row.get('Email address') or row.get('Email') or '').strip()
                if email:
                    contacts.append({
                        'email': email,
                        'first_name': (row.get('First name') or row.get('FirstName') or '').strip(),
                        'last_name': (row.get('Last name') or row.get('LastName') or '').strip(),
                        'company': (row.get('Company') or '').strip(),
                        'job_title': (row.get('Job title') or row.get('Title') or '').strip(),
                        'website': (row.get('Website') or '').strip(),
                        'linkedin': (row.get('LinkedIn URL') or row.get('LinkedIn') or '').strip(),
                    })
        log(f"✅ Loaded {len(contacts)} contacts with valid emails")
        web_log(f"✅ Loaded {len(contacts)} contacts", 'success')
        update_campaign_status(total=len(contacts))
    except Exception as e:
        log(f"❌ Error loading CSV: {e}")
        web_log(f"❌ Error loading CSV: {e}", 'error')
        return False
    
    if not contacts:
        log("❌ No valid contacts found in CSV")
        web_log("❌ No valid contacts found", 'error')
        return False
    
    # Step 2: Process each contact
    log(f"\n📧 Step 2: Processing {len(contacts)} contacts...")
    log("=" * 70)
    web_log(f"📧 Starting to process {len(contacts)} contacts", 'info')
    
    success_count = 0
    fail_count = 0
    scraped_count = 0
    ai_processed_count = 0
    
    from modules.database import Contact
    
    for i, contact in enumerate(contacts, 1):
        log(f"\n[{i}/{len(contacts)}] Processing: {contact['first_name']} {contact['last_name']} <{contact['email']}>")
        web_log(f"[{i}/{len(contacts)}] Processing: {contact['email']}", 'info')
        update_campaign_status(current=i, step=f"Processing email {i}/{len(contacts)}")
        
        try:
            # 2a. Add/Update contact in database
            db_contact = session.query(Contact).filter(Contact.email == contact['email']).first()
            if not db_contact:
                db_contact = Contact(
                    email=contact['email'],
                    first_name=contact['first_name'],
                    last_name=contact['last_name'],
                    company=contact['company'],
                    website=contact['website'],
                    contact_metadata={'linkedin': contact['linkedin'], 'job_title': contact['job_title']}
                )
                session.add(db_contact)
                session.commit()
                log(f"  ✅ Contact added to database (ID: {db_contact.id})")
            else:
                log(f"  ℹ️  Contact exists (ID: {db_contact.id})")
            
            contact['id'] = db_contact.id
            
            # 2b. Scrape company website
            scraped_data = {}
            if contact['website']:
                log(f"  🔍 Scraping website: {contact['website']}")
                web_log(f"🔍 Scraping: {contact['website']}", 'info')
                update_campaign_status(step=f"Scraping website [{i}/{len(contacts)}]")
                
                try:
                    scraped_data = scraper.scrape_website(contact['website'])
                    if scraped_data and scraped_data.get('description'):
                        log(f"     ✅ Scraped: {scraped_data['description'][:100]}...")
                        scraped_count += 1
                        update_campaign_status(scraped=scraped_count)
                        web_log(f"✅ Scraped website ({scraped_count} total)", 'success')
                    else:
                        log(f"     ⚠️  No meaningful content found")
                        web_log(f"⚠️ No content found on website", 'warning')
                except Exception as e:
                    log(f"     ⚠️  Scraping failed: {str(e)[:100]}")
                    web_log(f"⚠️ Scraping failed: {str(e)[:50]}", 'warning')
            else:
                log(f"  ⏭️  No website to scrape")
                web_log(f"⏭️ No website available", 'info')
            
            # 2c. Generate email content
            log(f"  ✍️  Generating personalized email...")
            web_log(f"✍️ Generating email with AI...", 'info')
            update_campaign_status(step=f"AI Processing [{i}/{len(contacts)}]")
            
            if ai and scraped_data:
                # AI-powered personalization
                try:
                    personalized = ai.personalize_email(
                        contact=contact,
                        scraped_data=scraped_data,
                        base_template="Hi {first_name}, I noticed {company}'s work...",
                        subject=f"Quick question about {contact['company']}"
                    )
                    subject = personalized.get('personalized_subject', f"Quick question about {contact['company']}")
                    body = personalized.get('personalized_body', '')
                    log(f"     ✅ AI personalization complete")
                    ai_processed_count += 1
                    update_campaign_status(ai_processed=ai_processed_count)
                    web_log(f"✅ AI processed email ({ai_processed_count} total)", 'success')
                except Exception as e:
                    log(f"     ⚠️  AI failed, using template: {str(e)[:50]}")
                    web_log(f"⚠️ AI failed, using template", 'warning')
                    subject = f"Quick question about {contact['company']}"
                    body = generate_template_email(contact, scraped_data)
            else:
                # Template-based personalization
                subject = f"Quick question about {contact['company']}"
                body = generate_template_email(contact, scraped_data)
                log(f"     ✅ Template email generated")
                web_log(f"✅ Template email generated", 'success')
            
            # 2d. Send email
            log(f"  📤 Sending email...")
            web_log(f"📤 Sending email to {contact['email']}...", 'info')
            update_campaign_status(step=f"Sending email [{i}/{len(contacts)}]")
            
            try:
                success = sender.send_email(
                    to_email=contact['email'],
                    subject=subject,
                    body_text=body
                )
                
                if success:
                    log(f"     ✅ Email sent successfully!")
                    success_count += 1
                    update_campaign_status(sent=success_count)
                    web_log(f"✅ Email sent successfully! ({success_count} total)", 'success')
                    
                    # Log to database
                    from modules.database import CampaignRecipient, EmailLog
                    recipient = CampaignRecipient(
                        campaign_id=1,
                        contact_id=contact['id'],
                        status='sent',
                        sent_at=datetime.now()
                    )
                    session.add(recipient)
                    session.commit()
                    
                    email_log = EmailLog(
                        campaign_recipient_id=recipient.id,
                        status='sent',
                        created_at=datetime.now()
                    )
                    session.add(email_log)
                    session.commit()
                else:
                    log(f"     ❌ Email send failed")
                    fail_count += 1
                    update_campaign_status(failed=fail_count)
                    web_log(f"❌ Email send failed ({fail_count} total)", 'error')
            except Exception as e:
                log(f"     ❌ Error sending: {str(e)[:100]}")
                fail_count += 1
                update_campaign_status(failed=fail_count)
                web_log(f"❌ Error: {str(e)[:50]}", 'error')
            
            # 2e. Wait before next email
            if i < len(contacts):
                log(f"  ⏳ Waiting {delay_seconds}s before next email...")
                time.sleep(delay_seconds)
        
        except Exception as e:
            log(f"  ❌ ERROR: {str(e)[:200]}")
            fail_count += 1
            continue
    
    # Final summary
    log("\n" + "=" * 70)
    log("📊 CAMPAIGN COMPLETE!")
    log("=" * 70)
    log(f"✅ Successfully sent: {success_count}")
    log(f"❌ Failed: {fail_count}")
    log(f"📧 Total contacts: {len(contacts)}")
    log(f"📈 Success rate: {(success_count/len(contacts)*100):.1f}%")
    log("=" * 70)
    
    session.close()
    db.close()
    return True

def generate_template_email(contact, scraped_data):
    """Generate simple template email"""
    first_name = contact['first_name'] or 'there'
    company = contact['company'] or 'your company'
    
    body = f"""Hi {first_name},

I came across {company} and was impressed by your work in the investment space.

I'm reaching out because we're building something that could be relevant to your portfolio strategy.

Would you be open to a quick 15-minute call this week or next to discuss?

Best regards,
[Your Name]

P.S. I noticed {company} focuses on venture capital - our solution has helped several VCs streamline their deal flow process."""
    
    return body

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run automated email campaign')
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--delay', type=int, default=5, help='Delay between emails (seconds)')
    args = parser.parse_args()
    
    if not Path(args.csv).exists():
        print(f"❌ CSV file not found: {args.csv}")
        exit(1)
    
    automated_campaign(args.csv, args.delay)
