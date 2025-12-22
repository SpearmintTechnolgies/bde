"""
Test script to initialize PostgreSQL database and verify connection.

Run this first to:
1. Test PostgreSQL connection
2. Create all tables (contacts, campaigns, email_logs)
3. Verify the setup is working

Usage:
    python test_db_setup.py
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

# Import our modules
from config.settings import Config
from modules.database import Database, Contact, Campaign, EmailLog

def test_database_setup():
    """Test database connection and setup."""
    
    print("=" * 60)
    print("BDE EMAIL AUTOMATION - DATABASE SETUP TEST")
    print("=" * 60)
    
    # Step 1: Validate configuration
    print("\n[1/5] Validating configuration...")
    try:
        Config.validate()
        print("✓ Configuration valid")
        print(f"  - Database: {Config.POSTGRES_DB}")
        print(f"  - Host: {Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}")
        print(f"  - User: {Config.POSTGRES_USER}")
        print(f"  - Batch size: {Config.BATCH_SIZE}")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return False
    
    # Step 2: Connect to database
    print("\n[2/5] Connecting to PostgreSQL...")
    try:
        db = Database()
        print("✓ Database connection established")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nMake sure:")
        print("  - PostgreSQL is running")
        print("  - Database 'bde_email_automation' exists (or create it)")
        print("  - Credentials in .env are correct")
        return False
    
    # Step 3: Test connection
    print("\n[3/5] Testing connection...")
    if db.test_connection():
        print("✓ Connection test passed")
    else:
        print("✗ Connection test failed")
        return False
    
    # Step 4: Create schema
    print("\n[4/5] Creating database schema...")
    try:
        db.init_schema()
        print("✓ Schema created successfully")
        print("  - Table: contacts")
        print("  - Table: campaigns")
        print("  - Table: email_logs")
    except Exception as e:
        print(f"✗ Schema creation failed: {e}")
        return False
    
    # Step 5: Test basic operations
    print("\n[5/5] Testing basic operations...")
    try:
        # Test adding a contact
        test_contact = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'company': 'Test Company',
            'website': 'www.test.com'
        }
        
        contact_id = db.add_contact(test_contact)
        if contact_id:
            print(f"✓ Added test contact (ID: {contact_id})")
        else:
            print("  Contact already exists (this is okay)")
        
        # Test getting contact
        session = db.get_session()
        contact = session.query(Contact).filter(Contact.email == 'test@example.com').first()
        if contact:
            name = f"{contact.first_name} {contact.last_name}".strip()
            print(f"✓ Retrieved contact: {name}")
        session.close()
        
        # Test contact count
        session = db.get_session()
        count = session.query(Contact).count()
        print(f"✓ Total contacts in database: {count}")
        session.close()
        
        # Test creating a campaign
        session = db.get_session()
        from modules.database import Campaign, Template
        
        # Create template first
        template = Template(
            name="Test Template",
            subject="Test Subject",
            body="Test body content"
        )
        session.add(template)
        session.commit()
        
        # Create campaign
        campaign = Campaign(
            name="Test Campaign",
            template_id=template.id,
            status='draft'
        )
        session.add(campaign)
        session.commit()
        print(f"✓ Created test campaign (ID: {campaign.id})")
        session.close()
        
    except Exception as e:
        print(f"✗ Operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour database is ready to use. Next steps:")
    print("  1. Import contacts from CSV")
    print("  2. Create a campaign")
    print("  3. Start sending emails in batches")
    print()
    
    return True


if __name__ == "__main__":
    success = test_database_setup()
    sys.exit(0 if success else 1)
