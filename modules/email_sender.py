"""
Email sender module with PostgreSQL status tracking and batch processing.

Sends emails in batches to save resources and tracks status in database.

Features:
- Batch processing (configurable batch size)
- Status tracking (pending, sent, failed, bounced)
- Automatic delays between emails
- Error handling and logging
"""

import smtplib
import time
import random
import logging
from typing import Dict, List, Optional
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from config.settings import Config
from modules.database import Database, EmailStatus

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Email sender with batch processing and status tracking.
    """
    
    def __init__(self, db: Database = None):
        """
        Initialize email sender.
        
        Args:
            db: Database instance (creates new one if not provided)
        """
        self.db = db if db else Database()
        self.gmail_address = Config.GMAIL_ADDRESS
        self.gmail_password = Config.GMAIL_APP_PASSWORD
        
    def send_email(self, to_email: str, subject: str, body_text: str, 
                   body_html: str = None) -> bool:
        """
        Send a single email via Gmail SMTP.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
        
        Returns:
            bool: True if sent successfully
        """
        try:
            msg = EmailMessage()
            msg['From'] = self.gmail_address
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid()
            
            # Set content
            msg.set_content(body_text)
            if body_html:
                msg.add_alternative(body_html, subtype='html')
            
            # Send via Gmail SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.gmail_address, self.gmail_password)
                smtp.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_batch(self, campaign_id: int, batch_size: int = None,
                   delay_min: int = None, delay_max: int = None) -> Dict:
        """
        Send emails to a batch of pending contacts for a campaign.
        
        Args:
            campaign_id: Campaign ID
            batch_size: Number of emails to send (uses Config.BATCH_SIZE if None)
            delay_min: Min delay between emails in seconds
            delay_max: Max delay between emails in seconds
        
        Returns:
            dict: Statistics (sent, failed, total)
        """
        if batch_size is None:
            batch_size = Config.BATCH_SIZE
        if delay_min is None:
            delay_min = Config.MIN_DELAY_SECONDS
        if delay_max is None:
            delay_max = Config.MAX_DELAY_SECONDS
        
        # Get campaign details
        campaign = self.db.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Get pending contacts for this campaign
        contacts = self.db.get_batch_to_send(campaign_id, batch_size=batch_size)
        
        if not contacts:
            logger.info("No pending contacts to email")
            return {'sent': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"Starting batch send: {len(contacts)} contacts")
        
        stats = {'sent': 0, 'failed': 0, 'total': len(contacts)}
        
        for i, contact in enumerate(contacts, 1):
            # Personalize email
            body_text = self._personalize_email(campaign['body_text'], contact)
            body_html = None
            if campaign.get('body_html'):
                body_html = self._personalize_email(campaign['body_html'], contact)
            
            # Send email
            success = self.send_email(
                to_email=contact['email'],
                subject=campaign['subject'],
                body_text=body_text,
                body_html=body_html
            )
            
            # Log result in database
            status = EmailStatus.SENT if success else EmailStatus.FAILED
            error_msg = None if success else "SMTP send failed"
            
            self.db.log_email_sent(
                contact_id=contact['id'],
                campaign_id=campaign_id,
                subject=campaign['subject'],
                body_text=body_text,
                body_html=body_html,
                status=status,
                error_message=error_msg
            )
            
            if success:
                stats['sent'] += 1
            else:
                stats['failed'] += 1
            
            # Progress update
            logger.info(f"Progress: {i}/{len(contacts)} - {contact['email']} - {status.value}")
            
            # Delay before next email (except for last one)
            if i < len(contacts):
                delay = random.uniform(delay_min, delay_max)
                logger.debug(f"Waiting {delay:.1f} seconds before next email...")
                time.sleep(delay)
        
        logger.info(f"Batch complete: {stats['sent']} sent, {stats['failed']} failed")
        return stats
    
    def _personalize_email(self, template: str, contact: Dict) -> str:
        """
        Personalize email template with contact data.
        
        Args:
            template: Email template with placeholders
            contact: Contact dictionary
        
        Returns:
            str: Personalized email
        """
        # Extract name for personalization
        name = contact.get('first_name') or contact.get('full_name') or contact.get('email').split('@')[0]
        
        # Replace placeholders
        personalized = template.replace('{name}', name)
        personalized = personalized.replace('{first_name}', contact.get('first_name', name))
        personalized = personalized.replace('{full_name}', contact.get('full_name', name))
        personalized = personalized.replace('{company}', contact.get('company', ''))
        personalized = personalized.replace('{job_title}', contact.get('job_title', ''))
        
        return personalized
    
    def get_campaign_progress(self, campaign_id: int) -> Dict:
        """
        Get sending progress for a campaign.
        
        Returns:
            dict: Progress statistics
        """
        return self.db.get_campaign_stats(campaign_id)
    
    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()
