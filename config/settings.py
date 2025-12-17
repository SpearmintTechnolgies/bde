"""
Configuration settings for BDE email automation system.

This module loads environment variables from .env file and provides
configuration constants to all other modules.

Usage:
    from config.settings import Config
    
    print(Config.GMAIL_ADDRESS)
    Config.validate()  # Check all required vars are set
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Central configuration class for BDE system.
    
    All settings are loaded from environment variables.
    Use Config.validate() to ensure required variables are set.
    """
    
    # ============================================
    # EMAIL CONFIGURATION
    # ============================================
    GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
    
    # ============================================
    # OPENAI API CONFIGURATION
    # ============================================
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # ============================================
    # CAMPAIGN SETTINGS
    # ============================================
    MAX_EMAILS_PER_RUN = int(os.getenv("MAX_EMAILS_PER_RUN", "260"))
    MIN_DELAY_SECONDS = int(os.getenv("MIN_DELAY_SECONDS", "120"))
    MAX_DELAY_SECONDS = int(os.getenv("MAX_DELAY_SECONDS", "180"))
    
    # Note: Fit score is calculated for analytics only, not for filtering
    # All contacts in CSV will receive emails regardless of fit score
    CALCULATE_FIT_SCORE = os.getenv("CALCULATE_FIT_SCORE", "true").lower() == "true"
    
    # ============================================
    # DATABASE & STORAGE (PostgreSQL)
    # ============================================
    # PostgreSQL Configuration
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "bde_email_automation")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    
    # Batch processing settings
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))  # Process contacts in batches
    
    # Legacy SQLite path (kept for backward compatibility)
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/sent_emails.db")
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "data/logs/email_sender.log")
    
    # ============================================
    # OPTIONAL SETTINGS
    # ============================================
    USER_AGENT = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    SCRAPING_TIMEOUT = int(os.getenv("SCRAPING_TIMEOUT", "10"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    # Proxy settings (optional)
    PROXY_URL = os.getenv("PROXY_URL")
    PROXY_USERNAME = os.getenv("PROXY_USERNAME")
    PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
    
    # ============================================
    # PROJECT PATHS
    # ============================================
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = DATA_DIR / "logs"
    CONFIG_DIR = BASE_DIR / "config"
    MODULES_DIR = BASE_DIR / "modules"
    
    @classmethod
    def get_database_url(cls):
        """
        Generate PostgreSQL database URL for SQLAlchemy.
        
        Returns:
            str: PostgreSQL connection URL
        """
        return (
            f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )
    
    @classmethod
    def validate(cls):
        """
        Validate that all required environment variables are set.
        
        Raises:
            ValueError: If any required variable is missing
            
        Returns:
            bool: True if all required variables are present
        """
        required_vars = {
            "GMAIL_ADDRESS": cls.GMAIL_ADDRESS,
            "GMAIL_APP_PASSWORD": cls.GMAIL_APP_PASSWORD,
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
            "POSTGRES_PASSWORD": cls.POSTGRES_PASSWORD,
        }
        
        missing = [name for name, value in required_vars.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please ensure .env file exists and contains these variables.\n"
                f"Copy .env.example to .env and fill in your credentials."
            )
        
        return True
    
    @classmethod
    def ensure_directories(cls):
        """
        Create necessary directories if they don't exist.
        
        Creates:
            - data/
            - data/logs/
        """
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_proxy_config(cls):
        """
        Get proxy configuration if set.
        
        Returns:
            dict or None: Proxy configuration for requests library
        """
        if not cls.PROXY_URL:
            return None
        
        proxy_config = {
            "http": cls.PROXY_URL,
            "https": cls.PROXY_URL,
        }
        
        return proxy_config
    
    @classmethod
    def display_config(cls):
        """
        Display current configuration (for debugging).
        
        Note: Sensitive values are masked.
        """
        print("=" * 50)
        print("BDE CONFIGURATION")
        print("=" * 50)
        print(f"Gmail Address: {cls.GMAIL_ADDRESS}")
        print(f"Gmail Password: {'*' * 8 if cls.GMAIL_APP_PASSWORD else 'NOT SET'}")
        print(f"OpenAI API Key: {'*' * 8 if cls.OPENAI_API_KEY else 'NOT SET'}")
        print(f"OpenAI Model: {cls.OPENAI_MODEL}")
        print(f"Max Emails Per Run: {cls.MAX_EMAILS_PER_RUN}")
        print(f"Delay Range: {cls.MIN_DELAY_SECONDS}-{cls.MAX_DELAY_SECONDS}s")
        print(f"Min Fit Score: {cls.MIN_FIT_SCORE}")
        print(f"Database Path: {cls.DATABASE_PATH}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"Log File: {cls.LOG_FILE}")
        print("=" * 50)


# Validate configuration on import (optional - comment out if not desired)
# This ensures .env is set up correctly when any module imports Config
try:
    Config.validate()
except ValueError as e:
    print(f"⚠️  Configuration Warning: {e}")
