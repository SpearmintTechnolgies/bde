"""
Simple test to verify PostgreSQL connection and query existing data.
"""
from modules.database import Database, Contact, Campaign, Template, CampaignRecipient
from config.settings import Config

def test_connection():
    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)
    
    # Test config
    print("\n1. Testing configuration...")
    try:
        db_url = Config.get_database_url()
        print(f"✓ Database URL: {db_url.replace(Config.POSTGRES_PASSWORD, '***')}")
    except Exception as e:
        print(f"✗ Config error: {e}")
        return
    
    # Connect to database
    print("\n2. Connecting to database...")
    try:
        db = Database()
        print("✓ Connected successfully")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return
    
    # Query existing data
    print("\n3. Querying existing data...")
    session = db.get_session()
    
    try:
        # Count contacts
        contact_count = session.query(Contact).count()
        print(f"✓ Contacts in database: {contact_count}")
        
        # Count campaigns
        campaign_count = session.query(Campaign).count()
        print(f"✓ Campaigns in database: {campaign_count}")
        
        # Count templates
        template_count = session.query(Template).count()
        print(f"✓ Templates in database: {template_count}")
        
        # Count campaign recipients
        recipient_count = session.query(CampaignRecipient).count()
        print(f"✓ Campaign recipients: {recipient_count}")
        
        # Show first 3 contacts
        if contact_count > 0:
            print("\n4. Sample contacts:")
            contacts = session.query(Contact).limit(3).all()
            for c in contacts:
                print(f"  - {c.email} | {c.first_name} {c.last_name} | {c.company}")
        
        # Show campaigns
        if campaign_count > 0:
            print("\n5. Sample campaigns:")
            campaigns = session.query(Campaign).limit(3).all()
            for camp in campaigns:
                print(f"  - ID: {camp.id} | Name: {camp.name} | Status: {camp.status}")
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED! Database is ready to use.")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Query error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_connection()
