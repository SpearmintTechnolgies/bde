"""
Enhanced campaign runner with web scraping and AI personalization.

This script:
1. Gets pending contacts for a campaign
2. Scrapes their company websites
3. Uses AI to personalize each email based on scraped data
4. Sends emails in batches
5. Tracks everything in PostgreSQL

Usage:
    python run_campaign_ai.py --campaign-id 1 --batch-size 10 --use-ai

Features:
- Web scraping for context
- AI-powered personalization
- Batch processing
- Full status tracking
"""

import argparse
import sys
import logging
import time
import json
from pathlib import Path

from config.settings import Config

# Setup logging
Config.ensure_directories()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from modules.database import Database, CampaignStatus
from modules.email_sender import EmailSender
from modules.web_scraper import WebScraper
from modules.ai_personalizer import AIPersonalizer


def run_ai_campaign(campaign_id: int, batch_size: int = 10, 
                   use_ai: bool = True, use_scraping: bool = True,
                   max_batches: int = None):
    """
    Run campaign with AI personalization and web scraping.
    
    Args:
        campaign_id: Campaign ID to run
        batch_size: Contacts per batch (smaller for AI due to API costs)
        use_ai: Whether to use AI personalization
        use_scraping: Whether to scrape websites
        max_batches: Maximum number of batches to send (None = unlimited)
    """
    print("=" * 70)
    print("AI-POWERED EMAIL CAMPAIGN")
    print("=" * 70)
    
    # Initialize components
    db = Database()
    sender = EmailSender(db)
    scraper = WebScraper() if use_scraping else None
    ai = AIPersonalizer() if use_ai else None
    
    # Get campaign
    campaign = db.get_campaign(campaign_id)
    if not campaign:
        print(f"❌ Campaign {campaign_id} not found")
        return False
    
    print(f"\n📧 Campaign: {campaign['name']}")
    print(f"   Subject: {campaign['subject']}")
    print(f"   AI Personalization: {'✅ Enabled' if use_ai else '❌ Disabled'}")
    print(f"   Web Scraping: {'✅ Enabled' if use_scraping else '❌ Disabled'}")
    print(f"   Batch Size: {batch_size} contacts")
    
    # Update campaign status
    db.update_campaign_status(campaign_id, CampaignStatus.ACTIVE)
    
    batch_num = 0
    total_sent = 0
    total_failed = 0
    
    while True:
        batch_num += 1
        
        if max_batches and batch_num > max_batches:
            print(f"\n✅ Reached maximum batches ({max_batches})")
            break
        
        # Get next batch
        print(f"\n{'='*70}")
        print(f"BATCH {batch_num}")
        print(f"{'='*70}")
        
        contacts = db.get_batch_to_send(campaign_id, batch_size)
        
        if not contacts:
            print("\n✅ All emails sent! Campaign complete.")
            db.update_campaign_status(campaign_id, CampaignStatus.COMPLETED)
            break
        
        print(f"📊 Processing {len(contacts)} contacts...")
        
        # Process each contact in batch
        for i, contact in enumerate(contacts, 1):
            print(f"\n[{i}/{len(contacts)}] {contact['email']} - {contact.get('company', 'Unknown')}")
            
            # Step 1: Scrape website (if enabled)
            scraped_data = {}
            if use_scraping and contact.get('company_website'):
                print(f"  🔍 Scraping {contact['company_website']}...")
                try:
                    scraped_data = scraper.scrape_website(contact['company_website'])
                    if scraped_data.get('description'):
                        print(f"     ✓ Found: {scraped_data['description'][:100]}...")
                    
                    # Save scraped data to database
                    if scraped_data.get('raw_text'):
                        # Store scraped data in contact record
                        session = db.get_session()
                        from modules.database import Contact
                        db_contact = session.query(Contact).filter(Contact.id == contact['id']).first()
                        if db_contact:
                            db_contact.scraped_data = json.dumps(scraped_data)
                            session.commit()
                        session.close()
                        
                except Exception as e:
                    logger.error(f"Scraping error: {e}")
                    print(f"     ⚠ Scraping failed: {e}")
            
            # Step 2: AI Personalization (if enabled)
            email_body = campaign['body_text']
            email_subject = campaign['subject']
            
            if use_ai and scraped_data:
                print(f"  🤖 Personalizing with AI...")
                try:
                    personalized = ai.personalize_email(
                        contact=contact,
                        scraped_data=scraped_data,
                        base_template=campaign['body_text'],
                        subject=campaign['subject']
                    )
                    
                    # Use personalized content
                    if personalized.get('personalized_body'):
                        email_body = personalized['personalized_body']
                        print(f"     ✓ Personalized (confidence: {personalized.get('confidence_score', 0):.2f})")
                    
                    if personalized.get('personalized_subject'):
                        email_subject = personalized['personalized_subject']
                    
                    if personalized.get('talking_points'):
                        print(f"     Talking points: {', '.join(personalized['talking_points'][:2])}")
                        
                except Exception as e:
                    logger.error(f"AI personalization error: {e}")
                    print(f"     ⚠ AI failed, using template: {e}")
            
            # Basic variable substitution
            email_body = sender._personalize_email(email_body, contact)
            
            # Step 3: Send email
            print(f"  📤 Sending email...")
            success = sender.send_email(
                to_email=contact['email'],
                subject=email_subject,
                body_text=email_body
            )
            
            # Step 4: Log in database
            from modules.database import EmailStatus
            status = EmailStatus.SENT if success else EmailStatus.FAILED
            db.log_email_sent(
                contact_id=contact['id'],
                campaign_id=campaign_id,
                subject=email_subject,
                body_text=email_body,
                status=status
            )
            
            if success:
                total_sent += 1
                print(f"  ✅ Sent successfully")
            else:
                total_failed += 1
                print(f"  ❌ Send failed")
            
            # Delay between emails (except last)
            if i < len(contacts):
                delay = Config.MIN_DELAY_SECONDS
                print(f"  ⏳ Waiting {delay}s before next email...")
                time.sleep(delay)
        
        # Batch summary
        print(f"\n{'='*70}")
        print(f"BATCH {batch_num} COMPLETE")
        print(f"{'='*70}")
        print(f"✅ Sent: {total_sent}")
        print(f"❌ Failed: {total_failed}")
        
        # Show progress
        stats = db.get_campaign_stats(campaign_id)
        print(f"\n📊 Campaign Progress:")
        print(f"   Total Contacts: {stats['total_contacts']}")
        print(f"   Sent: {stats['sent']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Pending: {stats['pending']}")
        
        # Ask to continue
        if stats['pending'] > 0:
            response = input("\n▶ Continue to next batch? (y/n): ")
            if response.lower() != 'y':
                print("\n⏸ Campaign paused. Run again to continue.")
                db.update_campaign_status(campaign_id, CampaignStatus.PAUSED)
                break
        else:
            db.update_campaign_status(campaign_id, CampaignStatus.COMPLETED)
            break
    
    print("\n" + "="*70)
    print("CAMPAIGN SUMMARY")
    print("="*70)
    print(f"Total Batches: {batch_num}")
    print(f"Total Sent: {total_sent}")
    print(f"Total Failed: {total_failed}")
    print()
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Run AI-powered email campaign')
    parser.add_argument('--campaign-id', type=int, required=True, help='Campaign ID to run')
    parser.add_argument('--batch-size', type=int, default=10, help='Contacts per batch (default: 10)')
    parser.add_argument('--use-ai', action='store_true', help='Enable AI personalization')
    parser.add_argument('--use-scraping', action='store_true', help='Enable web scraping')
    parser.add_argument('--max-batches', type=int, help='Maximum batches to send')
    
    args = parser.parse_args()
    
    try:
        success = run_ai_campaign(
            campaign_id=args.campaign_id,
            batch_size=args.batch_size,
            use_ai=args.use_ai,
            use_scraping=args.use_scraping,
            max_batches=args.max_batches
        )
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏸ Campaign interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Campaign error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
