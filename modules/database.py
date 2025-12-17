"""
Database module for BDE email automation system (PostgreSQL).

Matches existing database schema with:
- contacts, campaigns, templates, campaign_recipients, email_logs tables

Usage:
    from modules.database import Database
    
    db = Database()
    contacts = db.get_all_contacts()
    db.add_recipient_to_campaign(campaign_id, contact_id)
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
import json

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, 
    Boolean, Text, Float, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError

from config.settings import Config

logger = logging.getLogger(__name__)

Base = declarative_base()


# ============================================
# DATABASE MODELS (Matching existing schema)
# ============================================

class Contact(Base):
    """Contact/prospect information."""
    __tablename__ = "contacts"
    
    # Exact columns from your database
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(Text, unique=True, nullable=False)
    first_name = Column(Text)
    last_name = Column(Text)
    company = Column(Text)
    website = Column(Text)
    contact_metadata = Column("metadata", JSONB)  # 'metadata' is reserved, use different Python name
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign_recipients = relationship("CampaignRecipient", back_populates="contact", cascade="all, delete-orphan")


class Template(Base):
    """Email template."""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    subject = Column(Text)
    body = Column(Text)
    is_html = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="template")


class Campaign(Base):
    """Email campaign."""
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    template_id = Column(Integer, ForeignKey('templates.id', ondelete='SET NULL'))
    status = Column(Text, default='draft')  # draft, active, paused, completed
    scheduled_at = Column(DateTime)
    options = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    template = relationship("Template", back_populates="campaigns")
    recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")


class CampaignRecipient(Base):
    """Junction table linking campaigns to contacts with personalization."""
    __tablename__ = "campaign_recipients"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    personalization = Column(JSONB)  # AI-generated personalized content
    status = Column(Text, default='pending')  # pending, sent, failed, bounced
    sent_at = Column(DateTime)
    message_id = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="recipients")
    contact = relationship("Contact", back_populates="campaign_recipients")
    email_logs = relationship("EmailLog", back_populates="campaign_recipient", cascade="all, delete-orphan")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('campaign_id', 'contact_id', name='campaign_recipients_campaign_id_contact_id_key'),
        Index('idx_campaign_recipients_status', 'status'),
    )


class EmailLog(Base):
    """Track email sending events and responses."""
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_recipient_id = Column(Integer, ForeignKey('campaign_recipients.id', ondelete='CASCADE'))
    provider_response = Column(JSONB)  # Raw response from email provider
    status = Column(Text)  # sent, failed, bounced, opened, clicked
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign_recipient = relationship("CampaignRecipient", back_populates="email_logs")


# ============================================
# DATABASE CLASS
# ============================================

class Database:
    """
    PostgreSQL database handler for BDE system.
    
    Manages:
    - Contact storage and deduplication
    - Email campaigns
    - Email sending logs and status
    - Batch processing
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL URL (uses Config if not provided)
        """
        if database_url is None:
            database_url = Config.get_database_url()
        
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Connected to PostgreSQL database")
    
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
    
    def init_schema(self):
        """
        Create all database tables and indexes.
        """
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database schema: {e}")
            raise
    
    # ============================================
    # CONTACT METHODS
    # ============================================
    
    def add_contact(self, contact_data: Dict) -> Optional[int]:
        """
        Add a single contact to database.
        
        Args:
            contact_data: Dict with email (required), first_name, last_name, company, etc.
        
        Returns:
            int: Contact ID or None if failed
        """
        session = self.get_session()
        try:
            # Check if contact already exists
            existing = session.query(Contact).filter(
                Contact.email == contact_data['email']
            ).first()
            
            if existing:
                logger.debug(f"Contact already exists: {contact_data['email']}")
                return existing.id
            
            # Create new contact (match actual schema)
            contact = Contact(
                email=contact_data['email'],
                first_name=contact_data.get('first_name'),
                last_name=contact_data.get('last_name'),
                company=contact_data.get('company'),
                website=contact_data.get('website'),
                contact_metadata=contact_data.get('metadata')
            )
            
            session.add(contact)
            session.commit()
            contact_id = contact.id
            logger.info(f"Added contact: {contact_data['email']} (ID: {contact_id})")
            return contact_id
            
        except IntegrityError:
            session.rollback()
            logger.warning(f"Duplicate contact: {contact_data['email']}")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding contact: {e}")
            return None
        finally:
            session.close()
    
    def add_contacts_batch(self, contacts: List[Dict], batch_size: int = None) -> int:
        """
        Add multiple contacts in batches (efficient bulk insert).
        
        Args:
            contacts: List of contact dictionaries
            batch_size: Number of contacts per batch (uses Config.BATCH_SIZE if None)
        
        Returns:
            int: Number of contacts added
        """
        if batch_size is None:
            batch_size = Config.BATCH_SIZE
        
        session = self.get_session()
        added_count = 0
        
        try:
            for i in range(0, len(contacts), batch_size):
                batch = contacts[i:i + batch_size]
                
                for contact_data in batch:
                    try:
                        # Check if exists
                        existing = session.query(Contact).filter(
                            Contact.email == contact_data['email']
                        ).first()
                        
                        if not existing:
                            contact = Contact(
                                email=contact_data['email'],
                                first_name=contact_data.get('first_name'),
                                last_name=contact_data.get('last_name'),
                                company=contact_data.get('company'),
                                website=contact_data.get('website'),
                                contact_metadata=contact_data.get('metadata')
                            )
                            session.add(contact)
                            added_count += 1
                    except Exception as e:
                        logger.warning(f"Skipping contact {contact_data.get('email')}: {e}")
                        continue
                
                session.commit()
                logger.info(f"Batch {i//batch_size + 1}: Added {added_count} contacts")
            
            logger.info(f"Total contacts added: {added_count}")
            return added_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error in batch insert: {e}")
            return added_count
        finally:
            session.close()
    
    def get_contact_by_email(self, email: str) -> Optional[Dict]:
        """
        Get contact by email address.
        
        Returns:
            dict or None: Contact data
        """
        session = self.get_session()
        try:
            contact = session.query(Contact).filter(Contact.email == email).first()
            if contact:
                return {
                    'id': contact.id,
                    'email': contact.email,
                    'full_name': contact.full_name,
                    'company': contact.company,
                    'company_website': contact.company_website,
                    'job_title': contact.job_title
                }
            return None
        finally:
            session.close()
    
    def get_pending_contacts(self, campaign_id: int, limit: int = None) -> List[Dict]:
        """
        Get contacts that haven't been emailed for this campaign.
        
        Args:
            campaign_id: Campaign ID
            limit: Maximum number to return
        
        Returns:
            list: Contacts ready to be emailed
        """
        session = self.get_session()
        try:
            # Get contacts without email logs for this campaign
            query = session.query(Contact).outerjoin(
                EmailLog, 
                (Contact.id == EmailLog.contact_id) & (EmailLog.campaign_id == campaign_id)
            ).filter(EmailLog.id == None)
            
            if limit:
                query = query.limit(limit)
            
            contacts = query.all()
            
            result = []
            for contact in contacts:
                result.append({
                    'id': contact.id,
                    'email': contact.email,
                    'full_name': contact.full_name,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'company': contact.company,
                    'company_website': contact.company_website,
                    'job_title': contact.job_title
                })
            
            logger.info(f"Found {len(result)} pending contacts for campaign {campaign_id}")
            return result
            
        finally:
            session.close()
    
    # ============================================
    # CAMPAIGN METHODS
    # ============================================
    
    def create_campaign(self, name: str, subject: str, body_text: str, 
                       body_html: str = None) -> int:
        """
        Create a new email campaign.
        
        Returns:
            int: Campaign ID
        """
        session = self.get_session()
        try:
            campaign = Campaign(
                name=name,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                max_emails_per_run=Config.MAX_EMAILS_PER_RUN,
                batch_size=Config.BATCH_SIZE,
                status='draft'
            )
            
            session.add(campaign)
            session.commit()
            campaign_id = campaign.id
            logger.info(f"Created campaign: {name} (ID: {campaign_id})")
            return campaign_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating campaign: {e}")
            raise
        finally:
            session.close()
    
    def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        """Get campaign by ID."""
        session = self.get_session()
        try:
            campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
            if campaign:
                return {
                    'id': campaign.id,
                    'name': campaign.name,
                    'subject': campaign.subject,
                    'body_text': campaign.body_text,
                    'body_html': campaign.body_html,
                    'status': campaign.status.value,
                    'created_at': campaign.created_at
                }
            return None
        finally:
            session.close()
    
    def update_campaign_status(self, campaign_id: int, status: str):
        """Update campaign status (draft, active, paused, completed)."""
        session = self.get_session()
        try:
            campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
            if campaign:
                campaign.status = status
                if status == 'active' and not hasattr(campaign, 'started_at'):
                    # started_at doesn't exist in schema, skip
                    pass
                elif status == 'completed':
                    # completed_at doesn't exist in schema, skip
                    pass
                session.commit()
                logger.info(f"Campaign {campaign_id} status updated to {status}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating campaign status: {e}")
            raise
        finally:
            session.close()
    
    # ============================================
    # EMAIL LOG METHODS
    # ============================================
    
    def log_email_sent(self, contact_id: int, campaign_id: int, 
                      subject: str, body_text: str, body_html: str = None,
                      status: str = 'sent', 
                      error_message: str = None) -> int:
        """
        Log an email send attempt.
        Note: This references old schema. Use add_recipient_to_campaign instead.
        
        Returns:
            int: Email log ID
        """
        # Old schema - replaced by campaign_recipients
        logger.warning("log_email_sent is deprecated - use add_recipient_to_campaign")
        return 0
    
    def get_campaign_stats(self, campaign_id: int) -> Dict:
        """
        Get statistics for a campaign.
        
        Returns:
            dict: Campaign statistics
        """
        session = self.get_session()
        try:
            # Total contacts
            total_contacts = session.query(Contact).count()
            
            # Email logs for this campaign
            logs = session.query(EmailLog).filter(
                EmailLog.campaign_id == campaign_id
            ).all()
            
            stats = {
                'total_contacts': total_contacts,
                'total_emails': len(logs),
                'sent': sum(1 for log in logs if log.status == 'sent'),
                'failed': sum(1 for log in logs if log.status == 'failed'),
                'pending': total_contacts - len(logs)
            }
            
            return stats
            
        finally:
            session.close()
    
    def get_batch_to_send(self, campaign_id: int, batch_size: int = None) -> List[Dict]:
        """
        Get next batch of contacts to email for campaign.
        
        This is the core method for batch processing.
        
        Args:
            campaign_id: Campaign ID
            batch_size: Batch size (uses Config.BATCH_SIZE if None)
        
        Returns:
            list: Contacts ready to send (up to batch_size)
        """
        if batch_size is None:
            batch_size = Config.BATCH_SIZE
        
        return self.get_pending_contacts(campaign_id, limit=batch_size)
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def get_all_contacts_count(self) -> int:
        """Get total number of contacts in database."""
        session = self.get_session()
        try:
            return session.query(Contact).count()
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            from sqlalchemy import text
            session = self.get_session()
            session.execute(text("SELECT 1"))
            session.close()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close(self):
        """Close database engine (cleanup)."""
        self.engine.dispose()
        logger.info("Database connection closed")
