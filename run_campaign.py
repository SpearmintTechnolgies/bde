"""
Main campaign runner with batch processing.

This script runs email campaigns in batches to save resources.

Usage:
    python run_campaign.py --campaign-id 1 --batch-size 50

Features:
- Batch processing (send X emails at a time)
- Automatic status tracking in PostgreSQL
- Progress monitoring
- Safe to stop and resume (tracks what's been sent)
"""

import argparse
import sys
import logging
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
from modules.database import Database
from modules.email_sender import EmailSender


def run_campaign(campaign_id: int, batch_size: int = None, max_batches: int = None):
    """
    Run email campaign in batches.
    
    Args:
        campaign_id: Campaign ID to run
        batch_size: Contacts per batch (uses Config.BATCH_SIZE if None)
        max_batches: Maximum number of batches to run (None = run all)
    """
    
    print("=" * 70)
    print("BDE EMAIL AUTOMATION - CAMPAIGN RUNNER")
    print("=" * 70)
    
    if batch_size is None:
        batch_size = Config.BATCH_SIZE
    
    # Initialize
    print("\n[1/4] Initializing...")
    db = Database()
    sender = EmailSender(db)
    
    # Get campaign
    print(f"\n[2/4] Loading campaign {campaign_id}...")
    campaign = db.get_campaign(campaign_id)
    if not campaign:
        print(f"✗ Campaign {campaign_id} not found")
        return False
    
    print(f"✓ Campaign loaded: {campaign['name']}")
    print(f"  Subject: {campaign['subject']}")
    print(f"  Status: {campaign['status']}")
    
    # Get initial stats
    print("\n[3/4] Getting campaign stats...")
    stats = db.get_campaign_stats(campaign_id)
    print(f"✓ Campaign statistics:")
    print(f"  Total contacts: {stats['total_contacts']}")
    print(f"  Already sent: {stats['sent']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Pending: {stats['pending']}")
    
    if stats['pending'] == 0:
        print("\n✓ Campaign complete - all contacts have been emailed!")
        return True
    
    # Update campaign status to active
    if campaign['status'] != 'active':
        db.update_campaign_status(campaign_id, 'active')
        print(f"  Campaign status updated to ACTIVE")
    
    # Run batches
    print(f"\n[4/4] Sending emails in batches of {batch_size}...")
    print("-" * 70)
    
    batch_count = 0
    total_sent = 0
    total_failed = 0
    
    while True:
        batch_count += 1
        
        print(f"\n>>> BATCH {batch_count}")
        
        # Send batch
        batch_stats = sender.send_batch(
            campaign_id=campaign_id,
            batch_size=batch_size
        )
        
        total_sent += batch_stats['sent']
        total_failed += batch_stats['failed']
        
        print(f"  Sent: {batch_stats['sent']}")
        print(f"  Failed: {batch_stats['failed']}")
        
        # Check if we should continue
        if batch_stats['total'] < batch_size:
            # No more contacts to send
            print("\n✓ All pending contacts processed!")
            break
        
        if max_batches and batch_count >= max_batches:
            print(f"\n⚠ Reached maximum batch limit ({max_batches})")
            break
        
        # Check if we want to continue
        try:
            response = input("\nContinue to next batch? (y/n): ").strip().lower()
            if response != 'y':
                print("Campaign paused by user")
                break
        except KeyboardInterrupt:
            print("\n\nCampaign interrupted by user")
            break
    
    # Final stats
    print("\n" + "=" * 70)
    print("CAMPAIGN RUN COMPLETE")
    print("=" * 70)
    
    final_stats = db.get_campaign_stats(campaign_id)
    print(f"  Total sent in this run: {total_sent}")
    print(f"  Total failed in this run: {total_failed}")
    print(f"  Overall campaign progress:")
    print(f"    - Sent: {final_stats['sent']}")
    print(f"    - Failed: {final_stats['failed']}")
    print(f"    - Pending: {final_stats['pending']}")
    
    if final_stats['pending'] == 0:
        db.update_campaign_status(campaign_id, 'completed')
        print(f"\n✓ Campaign marked as COMPLETED")
    
    print()
    
    # Cleanup
    sender.close()
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Run email campaign in batches')
    parser.add_argument('--campaign-id', type=int, required=True, 
                      help='Campaign ID to run')
    parser.add_argument('--batch-size', type=int, default=None,
                      help=f'Batch size (default: {Config.BATCH_SIZE})')
    parser.add_argument('--max-batches', type=int, default=None,
                      help='Maximum number of batches to run (default: unlimited)')
    
    args = parser.parse_args()
    
    try:
        success = run_campaign(
            campaign_id=args.campaign_id,
            batch_size=args.batch_size,
            max_batches=args.max_batches
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
