"""
Preview Email Output - Generate and Save Emails Without Sending
"""
import sys
import os
import time
import random
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.csv_loader import load_contacts_csv
from modules.web_scraper import WebScraper
from modules.ai_personalizer import AIPersonalizer
from config.settings import Config

def save_email_preview(emails_data, output_file='email_preview.html'):
    """Save generated emails to HTML file for preview"""
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Email Preview - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .email-card {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .email-card.failed {{
            border-left: 5px solid #ff4444;
        }}
        .email-card.success {{
            border-left: 5px solid #44ff44;
        }}
        .meta-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .meta-item {{
            display: flex;
            flex-direction: column;
        }}
        .meta-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .meta-value {{
            font-size: 14px;
            font-weight: bold;
            color: #333;
        }}
        .confidence {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }}
        .confidence.high {{ background: #d4edda; color: #155724; }}
        .confidence.medium {{ background: #fff3cd; color: #856404; }}
        .confidence.low {{ background: #f8d7da; color: #721c24; }}
        .subject {{
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px 0 15px 0;
            padding: 15px;
            background: #e8f4f8;
            border-left: 4px solid #3498db;
        }}
        .body {{
            line-height: 1.8;
            color: #34495e;
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: Georgia, serif;
        }}
        .sources {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }}
        .source-badge {{
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }}
        .source-badge.success {{
            background: #d4edda;
            color: #155724;
        }}
        .source-badge.failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-box {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 10px;
        }}
        .word-count {{
            font-size: 12px;
            color: #666;
            font-style: italic;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📧 Email Preview - AI Generated</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Model: {Config.OPENAI_MODEL}</p>
        <p>Prompt: Concise v2 (120-180 words, structured)</p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{len(emails_data)}</div>
            <div class="stat-label">Total Emails</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{sum(1 for e in emails_data if e.get('success'))}</div>
            <div class="stat-label">Generated Successfully</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{sum(e.get('confidence', 0) for e in emails_data) / len(emails_data):.2f}</div>
            <div class="stat-label">Avg Confidence</div>
        </div>
    </div>
"""
    
    for idx, email_data in enumerate(emails_data, 1):
        confidence = email_data.get('confidence', 0)
        confidence_class = 'high' if confidence >= 0.8 else 'medium' if confidence >= 0.6 else 'low'
        card_class = 'success' if email_data.get('success') else 'failed'
        
        # Count words in body
        body = email_data.get('body', '')
        word_count = len(body.split())
        
        sources_html = ""
        if 'sources_succeeded' in email_data:
            for source in ['website', 'linkedin', 'google']:
                if source in email_data['sources_succeeded']:
                    sources_html += f'<span class="source-badge success">✓ {source}</span>'
                else:
                    sources_html += f'<span class="source-badge failed">✗ {source}</span>'
        
        html_content += f"""
    <div class="email-card {card_class}">
        <h2>Email {idx}/3: {email_data.get('name', 'Unknown')} ({email_data.get('company', 'Unknown')})</h2>
        
        <div class="meta-info">
            <div class="meta-item">
                <div class="meta-label">Recipient</div>
                <div class="meta-value">{email_data.get('email', 'N/A')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Confidence</div>
                <div class="meta-value">
                    <span class="confidence {confidence_class}">{confidence:.2f}</span>
                </div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Word Count</div>
                <div class="meta-value">{word_count} words</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Model</div>
                <div class="meta-value">{Config.OPENAI_MODEL}</div>
            </div>
        </div>
        
        <div class="sources">
            {sources_html}
        </div>
        
        <div class="subject">
            <strong>Subject:</strong> {email_data.get('subject', 'N/A')}
        </div>
        
        <div class="body">
{body}
        </div>
        
        <div class="word-count">
            Target: 120-180 words | Actual: {word_count} words | {'✅ Within range' if 120 <= word_count <= 180 else '⚠️ Outside range'}
        </div>
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file


def main():
    print("=" * 70)
    print("EMAIL PREVIEW - GENERATE WITHOUT SENDING")
    print("=" * 70)
    print("This will generate emails and save them to HTML for review")
    print("=" * 70)
    
    # Load 3 test contacts
    contacts = load_contacts_csv('1000-leads-2025-12-16.csv', max_contacts=3)
    print(f"✅ Loaded {len(contacts)} contacts from CSV\n")
    
    # Initialize components
    scraper = WebScraper()
    ai_personalizer = AIPersonalizer()
    
    emails_data = []
    
    for idx, contact in enumerate(contacts, 1):
        print("=" * 70)
        print(f"CONTACT {idx}/{len(contacts)}: {contact['name']} ({contact['company']})")
        print("=" * 70)
        
        email_data = {
            'name': contact['name'],
            'email': contact['email'],
            'company': contact['company'],
            'success': False
        }
        
        try:
            # Scrape
            print("\n📡 SCRAPING (Website + LinkedIn + Google)...")
            scraped_data = scraper.scrape_all_sources(contact)
            
            print(f"   Sources tried: {', '.join(scraped_data.get('sources_tried', []))}")
            print(f"   Sources succeeded: {', '.join(scraped_data.get('sources_succeeded', []))}")
            
            email_data['sources_tried'] = scraped_data.get('sources_tried', [])
            email_data['sources_succeeded'] = scraped_data.get('sources_succeeded', [])
            
            # AI Personalize
            print("\n🤖 AI PERSONALIZING...")
            result = ai_personalizer.personalize_email(contact, scraped_data)
            
            email_data.update({
                'subject': result['subject'],
                'body': result['body'],
                'confidence': result['confidence'],
                'success': True
            })
            
            print(f"   Model: {Config.OPENAI_MODEL}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Subject: {result['subject']}")
            print(f"   Body preview: {result['body'][:100]}...")
            print("\n✅ Email generated successfully")
            
        except Exception as e:
            print(f"\n❌ Error generating email: {e}")
            email_data['error'] = str(e)
        
        emails_data.append(email_data)
        
        if idx < len(contacts):
            delay = random.uniform(3, 5)
            print(f"\n⏳ Waiting {delay:.1f}s before next contact...")
            time.sleep(delay)
    
    # Save to HTML file
    print("\n" + "=" * 70)
    print("SAVING EMAIL PREVIEW")
    print("=" * 70)
    
    output_file = save_email_preview(emails_data)
    abs_path = os.path.abspath(output_file)
    
    print(f"✅ Saved email preview to: {abs_path}")
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for idx, email in enumerate(emails_data, 1):
        status = "✅" if email.get('success') else "❌"
        print(f"{status} {email['name']} ({email['company']})")
        if email.get('success'):
            word_count = len(email['body'].split())
            print(f"   Confidence: {email['confidence']:.2f} | Words: {word_count}")
            print(f"   Subject: {email['subject'][:60]}...")
    
    print(f"\n📄 Open this file to review: {abs_path}")
    print("\n💡 Once you fix Gmail credentials, run: python scripts/test_complete_flow.py")


if __name__ == "__main__":
    main()
