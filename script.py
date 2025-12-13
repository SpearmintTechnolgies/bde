import csv
import smtplib
import time
import random
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

# -----------------------------
# CONFIGURATION
# -----------------------------

GMAIL_ADDRESS = "matt@resilution.io"
GMAIL_APP_PASSWORD = "mjtqzgjvpxalrlcs"  # 16-char app password
CSV_FILE = "contacts.csv"  # your CSV file

# Safety cap: how many emails to send per run
MAX_PER_RUN = 260

SUBJECT = "Resilution's seed round overview, real business revenue & on-chain yield"

# Plain text version (fallback)
BODY_TEXT_TEMPLATE = """Hi {name},

I am reaching out to share Resilution, a platform that lets investors back real world SME revenue streams in a way that is transparent, data driven and on chain.

SMEs sit on a huge financing gap while investors struggle to access real world yield in a clean, compliant way. Resilution connects the two. Businesses raise directly from a global pool of investors, plug in their CRM or sales data, and smart contracts handle revenue sharing and payouts automatically. Investors see live performance instead of quarterly PDFs and get programmatic distributions when milestones are hit.

We are raising a 2 million dollar seed round to take Resilution from private pilots to a fully live platform, scaling SME onboarding, investor acquisition and expanding into products like supply chain financing and invoice based yields.

Below I have provided links to our pitch deck and whitepaper for more detail. If this fits your focus on fintech, real world assets or web3 infrastructure, I would love to schedule a quick call to walk you through the product and metrics or continue the discussion here over text if that is easier for you.

Calendly: https://calendly.com/resilblockchain

Best,
Matthew Ettswold

Website: https://www.resilution.io/
Linktree: https://linktr.ee/Resilution
Whitepaper: https://www.resilution.io/resilution-whitepaper.pdf
Pitch Deck: https://media.resilution.io/RESILUTION_PITCH_DECK.pdf

If this isn’t relevant, just reply “no” and I won’t follow up again.
"""

# HTML version (with embedded links)
BODY_HTML_TEMPLATE = """\
<html>
  <body>
    <p>Hi {name},</p>

    <p>
      I am reaching out to share <strong>Resilution</strong>, a platform that lets investors back
      real world SME revenue streams in a way that is transparent, data driven and on chain.
    </p>

    <p>
      SMEs sit on a huge financing gap while investors struggle to access real world yield in a clean,
      compliant way. Resilution connects the two. Businesses raise directly from a global pool of
      investors, plug in their CRM or sales data, and smart contracts handle revenue sharing and payouts
      automatically. Investors see live performance instead of quarterly PDFs and get programmatic
      distributions when milestones are hit.
    </p>

    <p>
      We are raising a 2 million dollar seed round to take Resilution from private pilots to a fully
      live platform, scaling SME onboarding, investor acquisition and expanding into products like
      supply chain financing and invoice based yields.
    </p>

    <p>
      Below I have provided links to our pitch deck and whitepaper for more detail. If this fits your
      focus on fintech, real world assets or web3 infrastructure, I would love to schedule a quick call
      to walk you through the product and metrics or continue the discussion here over text if that is
      easier for you.
    </p>

    <p>
      Calendly:
      <a href="https://calendly.com/resilblockchain">https://calendly.com/resilblockchain</a>
    </p>

    <p>
      Best,<br/>
      Matthew Ettswold
    </p>

    <p>
      <a href="https://www.resilution.io/">Website</a> | <a href="https://linktr.ee/Resilution">Linktree</a> | <a href="https://www.resilution.io/resilution-whitepaper.pdf">Whitepaper</a> | <a href="https://media.resilution.io/RESILUTION_PITCH_DECK.pdf">Pitch Deck</a>
    </p>

    <p style="font-size: 12px; color: #777;">
      If this isn’t relevant, just reply “no” and I won’t follow up again.
    </p>
  </body>
</html>
"""


# -----------------------------
# EMAIL SENDING LOGIC
# -----------------------------

def load_contacts(csv_file, max_per_run):
    """Load up to max_per_run contacts from CSV."""
    contacts = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip()
            if email:
                contacts.append({"name": name if name else "there", "email": email})
            if len(contacts) >= max_per_run:
                break
    return contacts


def create_message(to_email, to_name):
    """Create a personalized EmailMessage with plain text + HTML parts."""
    msg = EmailMessage()
    msg["From"] = f"Matthew from Resilution <{GMAIL_ADDRESS}>"
    msg["To"] = to_email

    # Dynamic subject using first name
    first_name = to_name.split()[0] if to_name and to_name.lower() != "there" else ""
    if first_name:
        subject = f"{first_name}, Resilution's seed round overview, real business revenue & on-chain yield"
    else:
        subject = "Resilution's seed round overview, real business revenue & on-chain yield"

    msg["Subject"] = subject

    # Best-practice headers
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg["Reply-To"] = GMAIL_ADDRESS

    # Personalized bodies
    text_body = BODY_TEXT_TEMPLATE.format(name=to_name)
    html_body = BODY_HTML_TEMPLATE.format(name=to_name)

    # Plain text (fallback)
    msg.set_content(text_body)

    # HTML alternative
    msg.add_alternative(html_body, subtype="html")

    return msg


def main():
    contacts = load_contacts(CSV_FILE, MAX_PER_RUN)
    total = len(contacts)

    if total == 0:
        print("No contacts found in CSV (or MAX_PER_RUN is 0).")
        return

    print(f"Loaded {total} contacts from {CSV_FILE} (limited by MAX_PER_RUN={MAX_PER_RUN})")
    print("Starting to send emails...\n")

    # Set up SMTP connection once and reuse
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    except Exception as e:
        print("Error connecting to Gmail SMTP:", e)
        return

    sent_count = 0

    try:
        for index, contact in enumerate(contacts, start=1):
            name = contact["name"]
            email = contact["email"]

            msg = create_message(email, name)

            try:
                server.send_message(msg)
                sent_count += 1
                print(f"[{index}/{total}] Sent to {name} <{email}>  |  Total sent: {sent_count}")
            except Exception as send_error:
                print(f"[{index}/{total}] Error sending to {name} <{email}>:", send_error)

            # Random delay between 2 and 3 minutes
            delay = 120 + random.uniform(0, 60)
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl+C).")

    finally:
        server.quit()
        print(f"\nDone. Successfully sent {sent_count} emails out of {total} contacts.")


if __name__ == "__main__":
    main()