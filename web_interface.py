"""
BDE Email Automation - Web Interface
Modern, minimal, aesthetic design
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
from pathlib import Path
import threading
import time
from datetime import datetime
from modules.database import Database

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Global campaign status with detailed progress
campaign_status = {
    'running': False,
    'current': 0,
    'total': 0,
    'current_email': '',
    'current_step': '',
    'scraped_count': 0,
    'ai_processed_count': 0,
    'sent_count': 0,
    'failed_count': 0,
    'logs': []
}

def add_log(message, level='info'):
    """Add log message with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    campaign_status['logs'].append({
        'time': timestamp,
        'message': message,
        'level': level
    })
    # Keep only last 100 logs
    if len(campaign_status['logs']) > 100:
        campaign_status['logs'] = campaign_status['logs'][-100:]
    print(f"[{timestamp}] {message}")

@app.route('/')
def index():
    """Page 1: Upload CSV"""
    return render_template('upload.html')

@app.route('/emails')
def emails():
    """Page 2: View sent emails"""
    return render_template('emails.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    """Handle CSV upload and start campaign"""
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['csv_file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Please upload a valid CSV file'}), 400
    
    # Save file
    filepath = UPLOAD_FOLDER / file.filename
    file.save(filepath)
    
    # Start campaign in background
    def run_campaign():
        global campaign_status
        campaign_status['running'] = True
        campaign_status['current'] = 0
        campaign_status['scraped_count'] = 0
        campaign_status['ai_processed_count'] = 0
        campaign_status['sent_count'] = 0
        campaign_status['failed_count'] = 0
        campaign_status['logs'] = []
        
        add_log("🚀 Campaign started!", 'success')
        add_log(f"📂 Processing CSV: {file.filename}", 'info')
        
        try:
            # Import and run automation
            from automate_all import automated_campaign
            automated_campaign(str(filepath), delay_seconds=5)
            add_log("✅ Campaign completed successfully!", 'success')
        except Exception as e:
            add_log(f"❌ Campaign error: {str(e)}", 'error')
        finally:
            campaign_status['running'] = False
            add_log("⏹️ Campaign stopped", 'info')
    
    thread = threading.Thread(target=run_campaign, daemon=True)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Campaign started successfully!', 'redirect': '/emails'})

@app.route('/api/status')
def get_status():
    """Get current campaign status"""
    return jsonify(campaign_status)

@app.route('/api/emails')
def get_emails():
    """Get list of sent/failed emails only (not pending)"""
    try:
        db = Database()
        session = db.get_session()
        
        from modules.database import Contact, EmailLog, CampaignRecipient
        
        # Query ONLY sent or failed emails (exclude pending)
        results = session.query(
            Contact.email,
            Contact.first_name,
            Contact.last_name,
            Contact.company,
            Contact.website,
            CampaignRecipient.status,
            CampaignRecipient.sent_at,
            EmailLog.status.label('email_status'),
            EmailLog.created_at
        ).join(
            CampaignRecipient, Contact.id == CampaignRecipient.contact_id
        ).join(
            EmailLog, CampaignRecipient.id == EmailLog.campaign_recipient_id
        ).filter(
            EmailLog.status.in_(['sent', 'failed'])
        ).order_by(
            EmailLog.created_at.desc()
        ).all()
        
        emails = []
        for idx, row in enumerate(results, 1):
            status = row.email_status or row.status
            emails.append({
                'sr_no': len(results) - idx + 1,  # Reverse numbering (newest first)
                'email': row.email,
                'name': f"{row.first_name or ''} {row.last_name or ''}".strip() or 'N/A',
                'company': row.company or 'N/A',
                'website': row.website or '',
                'status': status,
                'sent_at': row.created_at.strftime('%Y-%m-%d %H:%M:%S') if row.created_at else row.sent_at.strftime('%Y-%m-%d %H:%M:%S') if row.sent_at else 'N/A'
            })
        
        session.close()
        db.close()
        
        return jsonify(emails)
    except Exception as e:
        print(f"Error getting emails: {e}")
        return jsonify([])

@app.route('/api/stats')
def get_stats():
    """Get campaign statistics"""
    try:
        db = Database()
        session = db.get_session()
        
        from modules.database import Contact, EmailLog, CampaignRecipient
        from sqlalchemy import func
        
        # Count by status
        total_contacts = session.query(func.count(Contact.id)).scalar()
        
        sent_count = session.query(func.count(EmailLog.id)).filter(
            EmailLog.status == 'sent'
        ).scalar() or 0
        
        failed_count = session.query(func.count(EmailLog.id)).filter(
            EmailLog.status == 'failed'
        ).scalar() or 0
        
        pending_count = total_contacts - sent_count - failed_count
        
        session.close()
        db.close()
        
        return jsonify({
            'total': total_contacts,
            'sent': sent_count,
            'failed': failed_count,
            'pending': pending_count
        })
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'total': 0, 'sent': 0, 'failed': 0, 'pending': 0})

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 BDE Email Automation - Web Interface")
    print("=" * 60)
    print("\n📍 Open in browser: http://localhost:5000")
    print("📂 Upload CSV on homepage")
    print("📧 View sent emails on /emails page\n")
    app.run(debug=True, port=5000, threaded=True)
