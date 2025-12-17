"""
Email template structures for BDE email automation system.

This module contains:
- Email body templates with placeholders
- Email signature
- Company context for AI generation
- Subject line formats

Templates use {variable} syntax for string formatting.
"""

# ============================================
# BASE EMAIL TEMPLATE
# ============================================

BASE_TEMPLATE = """Hi {name},

{personalized_intro}

{company_pitch}

{call_to_action}

Best,
Matthew Ettswold

{signature}
"""

# ============================================
# EMAIL SIGNATURE
# ============================================

SIGNATURE = """Website: https://www.resilution.io/
Calendly: https://calendly.com/resilblockchain
Whitepaper: https://www.resilution.io/resilution-whitepaper.pdf
Pitch Deck: https://media.resilution.io/RESILUTION_PITCH_DECK.pdf

If this isn't relevant, just reply "no" and I won't follow up again."""

# HTML version of signature
SIGNATURE_HTML = """
<p>
<a href="https://www.resilution.io/">Website</a> | 
<a href="https://calendly.com/resilblockchain">Calendly</a> | 
<a href="https://www.resilution.io/resilution-whitepaper.pdf">Whitepaper</a> | 
<a href="https://media.resilution.io/RESILUTION_PITCH_DECK.pdf">Pitch Deck</a>
</p>
<p style="font-size: 12px; color: #777;">
If this isn't relevant, just reply "no" and I won't follow up again.
</p>
"""

# ============================================
# COMPANY CONTEXT FOR AI GENERATION
# ============================================

COMPANY_CONTEXT = {
    'name': 'Resilution',
    'tagline': 'Platform that lets investors back real world SME revenue streams on blockchain',
    'description': 'Resilution connects SMEs directly to a global pool of investors through transparent, data-driven, on-chain financing.',
    'stage': 'Raising $2M seed round',
    'traction': 'Private pilots completed with live smart contracts handling automated revenue distribution',
    'problem_solving': 'SMEs face huge financing gaps while investors struggle to access real-world yield in a clean, compliant way',
    'differentiators': [
        'Transparent, data-driven, on-chain',
        'Direct SME-to-investor connection',
        'Automated revenue distribution via smart contracts',
        'Live performance tracking instead of quarterly PDFs',
        'Programmatic distributions when milestones hit'
    ],
    'product_features': [
        'Businesses plug in CRM or sales data',
        'Smart contracts handle revenue sharing automatically',
        'Investors see live performance data',
        'On-chain transparency and compliance'
    ],
    'use_cases': [
        'SME revenue stream financing',
        'Supply chain financing',
        'Invoice-based yields'
    ],
    'target_investors': [
        'Fintech investors',
        'Web3/blockchain funds',
        'Real World Assets (RWA) focused VCs',
        'B2B SaaS investors',
        'Infrastructure investors'
    ],
    'website': 'https://www.resilution.io/',
    'calendly': 'https://calendly.com/resilblockchain',
    'whitepaper': 'https://www.resilution.io/resilution-whitepaper.pdf',
    'pitch_deck': 'https://media.resilution.io/RESILUTION_PITCH_DECK.pdf'
}

# ============================================
# SUBJECT LINE TEMPLATES
# ============================================

SUBJECT_TEMPLATES = [
    "{first_name}, Resilution's seed round overview, real business revenue & on-chain yield",
    "Resilution's seed round - SME financing meets blockchain",
    "{first_name}, connecting real-world SME revenue to on-chain investors",
    "Real business yield on-chain - Resilution's $2M seed round",
    "{first_name}, transparent SME financing for {focus_area} investors",
]

# ============================================
# AI PROMPT TEMPLATE
# ============================================

AI_PROMPT_TEMPLATE = """You are an expert fundraising consultant writing an email to {name}, a {title} at {company}.

INVESTOR CONTEXT:
- Investment Focus: {investment_focus}
- Portfolio Companies: {portfolio_companies}
- Recent Activity: {recent_news}

YOUR COMPANY (Resilution):
- Product: {product_description}
- Stage: {stage}
- Traction: {traction}
- Unique Value: {differentiators}

TASK:
Write a professional, personalized 3-paragraph email (150-200 words) that:

1. Shows you researched their firm's investment thesis and portfolio
2. Explains specifically why Resilution aligns with their focus (reference their portfolio companies if relevant)
3. Proposes a brief 15-minute introductory call

GUIDELINES:
- Tone: Professional but warm, conversational
- Style: Concise and direct, no buzzwords or hype
- Length: Under 200 words
- Format: Plain text, paragraphs separated by blank lines
- DO NOT include: Subject line, signature, or links (those are added separately)
- DO include: Clear call-to-action mentioning the Calendly link

IMPORTANT:
- Be specific about how Resilution matches their investment thesis
- If their portfolio includes fintech or blockchain companies, mention the connection
- Keep it concise - investors are busy
- End with clear next step (schedule call via Calendly)

Write the email body now (DO NOT include subject, signature, or greetings - just the 3 paragraphs):
"""

# ============================================
# SUBJECT LINE GENERATION PROMPT
# ============================================

SUBJECT_PROMPT_TEMPLATE = """Create a compelling email subject line for {name}, who invests in {focus_area}.

Context:
- Our company (Resilution) does SME revenue stream financing on blockchain
- Stage: Raising $2M seed round
- Target: Fintech, web3, RWA investors

Requirements:
- 60-80 characters max
- Professional and direct
- Mention key value proposition (real business revenue, on-chain, seed round)
- Optional: Include {first_name} for personalization

DO NOT include:
- Clickbait or salesy language
- Emojis
- ALL CAPS
- Excessive punctuation

Generate 1 subject line:
"""

# ============================================
# FALLBACK TEMPLATES (if AI fails)
# ============================================

FALLBACK_EMAIL_BODY = """Hi {name},

I'm reaching out to share Resilution, a platform that lets investors back real-world SME revenue streams in a way that is transparent, data-driven, and on-chain.

SMEs sit on a huge financing gap while investors struggle to access real-world yield in a clean, compliant way. Resilution connects the two. Businesses raise directly from a global pool of investors, plug in their CRM or sales data, and smart contracts handle revenue sharing and payouts automatically.

We're raising a $2M seed round to take Resilution from private pilots to a fully live platform. If this fits your focus on fintech, real world assets, or web3 infrastructure, I'd love to schedule a quick 15-minute call to walk you through the product and metrics.

Calendly: https://calendly.com/resilblockchain

Best,
Matthew Ettswold

{signature}
"""

FALLBACK_SUBJECT = "Resilution's seed round overview - real business revenue & on-chain yield"

# ============================================
# HELPER FUNCTIONS
# ============================================

def format_email_body(personalized_intro, company_pitch, call_to_action, name="there"):
    """
    Format complete email body from components.
    
    Args:
        personalized_intro: Opening paragraph
        company_pitch: Main pitch paragraph
        call_to_action: Closing with CTA
        name: Recipient name
        
    Returns:
        str: Formatted email body
    """
    return BASE_TEMPLATE.format(
        name=name,
        personalized_intro=personalized_intro,
        company_pitch=company_pitch,
        call_to_action=call_to_action,
        signature=SIGNATURE
    )


def get_company_context_string():
    """
    Get company context as formatted string for AI prompts.
    
    Returns:
        str: Formatted company description
    """
    context = COMPANY_CONTEXT
    
    return f"""
Product: {context['description']}
Stage: {context['stage']}
Traction: {context['traction']}
Key Differentiators: {', '.join(context['differentiators'][:3])}
Use Cases: {', '.join(context['use_cases'])}
    """.strip()


def get_fallback_email(name="there"):
    """
    Get fallback email if AI generation fails.
    
    Args:
        name: Recipient name
        
    Returns:
        dict: {'subject': str, 'body': str}
    """
    return {
        'subject': FALLBACK_SUBJECT,
        'body': FALLBACK_EMAIL_BODY.format(name=name, signature=SIGNATURE)
    }
