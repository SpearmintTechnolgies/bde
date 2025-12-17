"""
Quick setup script to prepare the BDE system.

This script will:
1. Check if .env exists (copy from .env.example if not)
2. Install Python dependencies
3. Create necessary directories
4. Test database connection
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    print("=" * 60)
    print("BDE EMAIL AUTOMATION - QUICK SETUP")
    print("=" * 60)
    
    # Check .env file
    print("\n[1/4] Checking configuration...")
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("  Creating .env from .env.example...")
            env_example.read_text().replace(
                "your_postgres_password", "postgres"
            )
            with open(".env", "w") as f:
                f.write(env_example.read_text())
            print("  ✓ Created .env file")
            print("  ⚠ IMPORTANT: Edit .env and set your PostgreSQL password!")
        else:
            print("  ✗ .env.example not found!")
            return False
    else:
        print("  ✓ .env file exists")
    
    # Install dependencies
    print("\n[2/4] Installing Python dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("  ✓ Dependencies installed")
    except subprocess.CalledProcessError:
        print("  ✗ Failed to install dependencies")
        return False
    
    # Create directories
    print("\n[3/4] Creating directories...")
    dirs = ["data", "data/logs"]
    for dir_path in dirs:
        Path(dir_path).mkdir(exist_ok=True, parents=True)
    print("  ✓ Directories created")
    
    # Test database
    print("\n[4/4] Testing database connection...")
    print("  Run 'python test_db_setup.py' to test PostgreSQL connection")
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Edit .env file with your PostgreSQL password")
    print("  2. Create PostgreSQL database: CREATE DATABASE bde_email_automation;")
    print("  3. Run: python test_db_setup.py")
    print("  4. Import contacts: python import_contacts.py")
    print("  5. Run campaign: python run_campaign.py --campaign-id 1")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
