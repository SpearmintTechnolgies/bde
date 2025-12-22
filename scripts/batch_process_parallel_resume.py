"""
Resume parallel batch processing from a specific row.

Skips already processed contacts and continues from row N.
"""

import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from multiprocessing import Pool, cpu_count

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import Config
from modules.csv_loader import load_contacts_csv
from modules.web_scraper import WebScraper
from modules.ai_personalizer import AIPersonalizer

logger = logging.getLogger(__name__)


def process_single_contact(contact: Dict[str, Any]) -> Dict[str, str]:
    """
    Process a single contact in a separate process.
    
    Returns:
        Dict with 'email' and 'generated_email' keys
    """
    email = contact.get("email", "")
    name = contact.get("name", "Unknown")
    company = contact.get("company", "Unknown")
    
    try:
        # Create new instances for this process
        scraper = WebScraper()
        ai = AIPersonalizer()
        
        # Step 1: Scrape sources
        scraped_data = scraper.scrape_all_sources(contact)
        
        # Step 2: Generate email with AI
        email_result = ai.personalize_email(contact, scraped_data)
        
        # Build complete email
        subject = email_result.get("subject", "")
        body = email_result.get("body", "")
        
        generated_email = f"Subject: {subject}\n\n{body}"
        
        print(f"✅ Processed: {name} ({company})")
        
        return {
            "email": email,
            "generated_email": generated_email
        }
        
    except Exception as e:
        print(f"❌ Failed: {name} ({company}) - {str(e)}")
        return {
            "email": email,
            "generated_email": f"Error: {str(e)}"
        }


def batch_process_resume(
    csv_file: str,
    start_row: int = 102,
    num_contacts: int = 10,
    num_workers: int = 4
):
    """
    Resume parallel processing from a specific row.
    
    Args:
        csv_file: Path to input CSV
        start_row: Row number to start from (1-indexed, skips header)
        num_contacts: Number of contacts to process
        num_workers: Number of parallel workers
    """
    print("=" * 70)
    print("RESUME PARALLEL BATCH PROCESSING")
    print("=" * 70)
    
    # Setup
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n🚀 Configuration:")
    print(f"   Workers: {num_workers}")
    print(f"   Starting from row: {start_row}")
    print(f"   Processing: {num_contacts} contacts")
    print()
    
    # Load ALL contacts first
    all_contacts = load_contacts_csv(csv_file)
    
    if not all_contacts:
        print(f"❌ No contacts found in {csv_file}")
        return
    
    total_available = len(all_contacts)
    print(f"📋 Total contacts in CSV: {total_available}")
    
    # Calculate skip and take
    skip = start_row - 1  # Convert to 0-indexed
    
    if skip >= total_available:
        print(f"❌ Start row {start_row} exceeds total contacts ({total_available})")
        return
    
    # Slice the contacts list
    contacts = all_contacts[skip:skip + num_contacts]
    actual_count = len(contacts)
    
    print(f"📊 Skipping first {skip} contacts (rows 1-{skip})")
    print(f"🎯 Processing rows {start_row} to {start_row + actual_count - 1}")
    print()
    
    if actual_count == 0:
        print("❌ No contacts to process in the specified range")
        return
    
    # Process in parallel
    print(f"⚙️  Processing {actual_count} contacts with {num_workers} workers...")
    print("-" * 70)
    
    start_time = time.time()
    
    # Create process pool and map contacts to workers
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_single_contact, contacts)
    
    elapsed = time.time() - start_time
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"processed_emails_rows_{start_row}_{start_row + actual_count - 1}_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Calculate stats
    success_count = sum(1 for r in results if not r["generated_email"].startswith("Error:"))
    
    # Print summary
    print()
    print("=" * 70)
    print("PARALLEL PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Rows processed: {start_row} to {start_row + actual_count - 1}")
    print(f"Total contacts: {actual_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {actual_count - success_count}")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Average time per contact: {elapsed/actual_count:.1f} seconds")
    print(f"Speedup: ~{num_workers}x faster than sequential")
    print()
    print(f"📁 Output file: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Resume parallel batch processing from specific row")
    parser.add_argument("--csv", default="1000-leads-2025-12-16.csv", help="Input CSV file")
    parser.add_argument("--start", type=int, default=102, help="Start row number (default: 102)")
    parser.add_argument("--count", type=int, default=10, help="Number of contacts to process (default: 10)")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers (default: 4)")
    
    args = parser.parse_args()
    
    batch_process_resume(
        args.csv,
        start_row=args.start,
        num_contacts=args.count,
        num_workers=args.workers
    )
