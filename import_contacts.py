"""
CSV Import Script with Batch Processing

Import contacts from CSV file into PostgreSQL database in batches.
This saves resources by processing contacts in chunks.

Usage:
    python import_contacts.py

The script will:
1. Load contacts from contacts.csv
2. Import them into PostgreSQL in batches (default 50 at a time)
3. Skip duplicates automatically
4. Show progress and statistics
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config.settings import Config
from modules.database import Database
from modules.csv_loader import load_contacts_csv


def import_contacts_from_csv(csv_file: str = "contacts.csv"):
    """
    Import contacts from CSV into PostgreSQL database.
    
    Args:
        csv_file: Path to CSV file
    """
    
    print("=" * 60)
    print("CSV CONTACTS IMPORT - BATCH PROCESSING")
    print("=" * 60)
    
    # Step 1: Load CSV
    print(f"\n[1/3] Loading contacts from {csv_file}...")
    try:
        contacts = load_contacts_csv(csv_file)
        print(f"✓ Loaded {len(contacts)} contacts from CSV")
    except FileNotFoundError:
        print(f"✗ File not found: {csv_file}")
        return False
    except Exception as e:
        print(f"✗ Error loading CSV: {e}")
        return False
    
    if not contacts:
        print("✗ No contacts found in CSV")
        return False
    
    # Step 2: Connect to database
    print("\n[2/3] Connecting to database...")
    try:
        db = Database()
        print("✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    
    # Step 3: Import in batches
    print(f"\n[3/3] Importing contacts in batches of {Config.BATCH_SIZE}...")
    try:
        added_count = db.add_contacts_batch(contacts, batch_size=Config.BATCH_SIZE)
        
        total_count = db.get_all_contacts_count()
        
        print("\n" + "=" * 60)
        print("✓ IMPORT COMPLETE!")
        print("=" * 60)
        print(f"  New contacts added: {added_count}")
        print(f"  Total contacts in DB: {total_count}")
        print(f"  Duplicates skipped: {len(contacts) - added_count}")
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='contacts.csv', help='CSV file to import')
    args = parser.parse_args()
    
    success = import_contacts_from_csv(args.csv)
    sys.exit(0 if success else 1)
