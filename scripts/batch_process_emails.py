"""
Batch Email Generation - Process All Contacts

Loads contacts from CSV, generates personalized emails for each, and saves
results to a JSON file with two fields: email and generated_email.

This script does NOT send emails - it only generates them for review.
"""

import json
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Config
from modules.csv_loader import load_contacts_csv
from modules.web_scraper import WebScraper
from modules.ai_personalizer import AIPersonalizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_contact(contact: Dict[str, Any], scraper: WebScraper, personalizer: AIPersonalizer) -> Dict[str, Any]:
    """
    Process a single contact: scrape data and generate email.
    
    Returns dict with: email and generated_email only
    """
    email_addr = contact.get('email', '')
    name = contact.get('name', 'Unknown')
    
    result = {
        'email': email_addr,
        'generated_email': ''
    }
    
    try:
        # Step 1: Scrape contact data
        logger.info(f"Scraping data for {name} ({email_addr})")
        scraped_data = scraper.scrape_all_sources(contact)
        
        sources = scraped_data.get('sources_succeeded', [])
        logger.info(f"  Sources: {', '.join(sources) or 'none'}")
        
        # Step 2: Generate personalized email
        logger.info(f"Generating email for {name}")
        email_data = personalizer.personalize_email(contact, scraped_data)
        
        # Build complete email with subject + body
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        
        # Combine subject and body into generated_email
        complete_email = f"Subject: {subject}\n\n{body}"
        result['generated_email'] = complete_email
        
        word_count = len(body.split())
        confidence = email_data.get('confidence', 0.0)
        
        logger.info(f"✅ Generated email for {name} ({word_count} words, confidence: {confidence:.2f})")
        
    except Exception as e:
        logger.error(f"❌ Failed to process {name}: {e}")
        result['generated_email'] = f"ERROR: {str(e)}"
    
    return result


def batch_process_contacts(
    csv_path: str,
    output_path: str,
    max_contacts: int = None,
    delay_seconds: tuple = (3, 5)
):
    """
    Process all contacts from CSV and save results to JSON.
    
    Args:
        csv_path: Path to input CSV with contacts
        output_path: Path to output JSON (will be created)
        max_contacts: Maximum contacts to process (None = all)
        delay_seconds: (min, max) delay between contacts
    """
    logger.info("="*70)
    logger.info("BATCH EMAIL GENERATION - PROCESS ALL CONTACTS")
    logger.info("="*70)
    
    # Load contacts
    logger.info(f"Loading contacts from: {csv_path}")
    contacts = load_contacts_csv(csv_path)
    
    if max_contacts:
        contacts = contacts[:max_contacts]
    
    total_contacts = len(contacts)
    logger.info(f"✅ Loaded {total_contacts} contacts")
    
    # Initialize AI personalizer
    logger.info(f"Initializing AI with model: {Config.OPENAI_MODEL}")
    personalizer = AIPersonalizer(temperature=0.7)
    
    # Initialize web scraper
    logger.info("Initializing web scraper (website + linkedin + gemini)")
    scraper = WebScraper()
    
    # Process each contact
    results: List[Dict[str, Any]] = []
    success_count = 0
    
    start_time = time.time()
    
    for idx, contact in enumerate(contacts, 1):
        logger.info("="*70)
        logger.info(f"CONTACT {idx}/{total_contacts}: {contact.get('name')} ({contact.get('company')})")
        logger.info("="*70)
        
        # Process contact
        result = process_contact(contact, scraper, personalizer)
        results.append(result)
        
        if result.get('generated_email') and 'ERROR' not in result.get('generated_email', ''):
            success_count += 1
        
        # Progress update every 10 contacts
        if idx % 10 == 0:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            remaining = (total_contacts - idx) / rate if rate > 0 else 0
            logger.info(f"Progress: {idx}/{total_contacts} ({success_count} success)")
            logger.info(f"Rate: {rate:.1f} contacts/min | Est. remaining: {remaining/60:.1f} minutes")
        
        # Delay between contacts (except for last one)
        if idx < total_contacts:
            import random
            delay = random.uniform(delay_seconds[0], delay_seconds[1])
            logger.info(f"⏳ Waiting {delay:.1f}s before next contact...")
            time.sleep(delay)
    
    # Save results to JSON
    logger.info("="*70)
    logger.info("SAVING RESULTS")
    logger.info("="*70)
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Change extension to .json
    if output_path.suffix == '.csv':
        output_path = output_path.with_suffix('.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Summary
    elapsed_total = time.time() - start_time
    logger.info("="*70)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info("="*70)
    logger.info(f"Total contacts: {total_contacts}")
    logger.info(f"✅ Success: {success_count}")
    logger.info(f"⏱️  Total time: {elapsed_total/60:.1f} minutes")
    logger.info(f"📄 Output saved to: {output_path}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review the JSON file to inspect generated emails")
    logger.info("2. Each email object contains 'email' and 'generated_email' fields")
    logger.info("3. Use the JSON for bulk email sending (separate script)")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch process contacts and generate emails')
    parser.add_argument(
        '--input',
        default='1000-leads-2025-12-16.csv',
        help='Input CSV file path (default: 1000-leads-2025-12-16.csv)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output CSV file path (default: data/processed_emails_TIMESTAMP.csv)'
    )
    parser.add_argument(
        '--max',
        type=int,
        default=None,
        help='Maximum number of contacts to process (default: all)'
    )
    parser.add_argument(
        '--delay-min',
        type=float,
        default=3.0,
        help='Minimum delay between contacts in seconds (default: 3)'
    )
    parser.add_argument(
        '--delay-max',
        type=float,
        default=5.0,
        help='Maximum delay between contacts in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Set default output path with timestamp
    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'data/processed_emails_{timestamp}.json'
    
    # Run batch processing
    batch_process_contacts(
        csv_path=args.input,
        output_path=args.output,
        max_contacts=args.max,
        delay_seconds=(args.delay_min, args.delay_max)
    )


if __name__ == '__main__':
    main()
