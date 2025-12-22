"""
Master prompts for AI email generation.

This file contains all prompt templates used by the AI personalizer.
Edit these prompts to change email generation behavior without touching code.
"""

# ==============================================================================
# RESILUTION CORE FRAMING
# ==============================================================================
# This context is included in every email generation request.
# It defines what Resilution is and how to position it.

RESILUTION_CORE = """
UNIVERSAL CORE FRAMING (adapt wording as needed):
Resilution enables real businesses to raise capital against live revenue streams—without dilution—while giving investors transparent, performance-linked yield.

WHAT RESILUTION IS:
- Revenue-linked financing rails (infrastructure, not platform)
- Data-driven capital allocation
- Performance-based distributions
- Automated revenue sharing
- Web3 is INVISIBLE—present as financial infrastructure only

CURRENT CONTEXT:
- Raising $2M seed round
- Moving from successful private pilots to fully live platform
- Scaling SME onboarding across verticals
- Launching: invoice-based yields and supply-chain financing

SECTOR EXAMPLES (use to anchor to their focus):
- SaaS → MRR, contracts, churn
- Life sciences → commercialization, diagnostics, CROs
- Climate → project revenues, offtake agreements
- Supply chain → invoices, purchase orders
- Marketplaces → GMV, take rates

MUTUAL UPSIDE (always balance both):
For Operators:
• Non-dilutive growth capital
• Financing aligned with real performance
• No cap-table or IP pressure

For Investors:
• Real-world yield
• Live performance visibility
• Programmatic, milestone-based distributions

REQUIRED LINKS (include at end):
Calendly: https://calendly.com/resilblockchain
Website: https://www.resilution.io/
Linktree: https://linktr.ee/Resilution
Whitepaper: https://www.resilution.io/resilution-whitepaper.pdf
Pitch Deck: https://media.resilution.io/RESILUTION_PITCH_DECK.pdf

SIGN-OFF:
Best,
Matthew Ettswold

OPT-OUT (always final line):
If this isn't relevant, feel free to reply "no" and I won't follow up again.
"""

# ==============================================================================
# MASTER PROMPT TEMPLATE - 5 PARAGRAPH STRUCTURE
# ==============================================================================

MASTER_PROMPT_TEMPLATE = """Generate a personalized investor outreach email.

===== INPUTS =====
INVESTOR_DATA: {investor_data}
RESILUTION_CORE: {resilution_core}

===== GOAL =====
Create a short, professional email that aligns Resilution with the investor’s existing strategy
and maximizes the chance of a thoughtful reply or meeting.

Resilution must read as financing infrastructure, not a product or crypto venture.

===== STRUCTURE (STRICT – 5 PARAGRAPHS) =====

Paragraph 1: Show Understanding
- Reference verifiable facts from INVESTOR_DATA (sector, stage, portfolio focus)
- If specific facts are unavailable, use conservative sector-level understanding
- Commend their approach without flattery or hype
- MUST NOT mention Resilution, funding, or products

Paragraph 2: Define the Structural Problem
- Describe a capital or financing mismatch the investor already recognizes
- Frame as a systemic issue, not execution or technology risk
- MUST NOT mention Resilution by name

Paragraph 3: Introduce Resilution
- FIRST and ONLY place Resilution may be introduced
- Describe as revenue-linked financing infrastructure
- Focus on outcomes, not features
- Avoid all platform, product, or crypto language

Paragraph 4: Why Now
- Mention the $2M seed round
- Include one concrete timing trigger (e.g., pilots to live, demand inflection)
- Explain why this investor is relevant at this stage (sector or stage fit)

Paragraph 5: Next Step
- Clear, low-pressure invitation to connect or review materials
- Professional and concise

===== HARD CONSTRAINTS =====
- 120–170 words total
- Exactly 5 paragraphs (excluding greeting and signature)
- No bullets, symbols, emojis, or hype language
- No Web3, crypto, blockchain, token, platform, or ecosystem terms
- No speculative claims about the investor
- No repeated value propositions across paragraphs

===== LANGUAGE GUARDRAILS =====
Preferred terms:
- financing infrastructure
- revenue-linked capital
- performance-aligned financing
- non-dilutive growth capital

Avoid:
- solution (as a noun)
- disruptive
- revolutionary
- cutting-edge
- building

===== OUTPUT FORMAT (STRICT) =====

SUBJECT: Short, relevant subject line under 60 characters

Hi [First Name],

[Paragraph 1]

[Paragraph 2]

[Paragraph 3]

[Paragraph 4]

[Paragraph 5]

Best,
Matthew Ettswold

Calendly: https://calendly.com/resilblockchain
Website: https://www.resilution.io/
Linktree: https://linktr.ee/Resilution
Whitepaper: https://www.resilution.io/resilution-whitepaper.pdf
Pitch Deck: https://media.resilution.io/RESILUTION_PITCH_DECK.pdf

If this isn't relevant, feel free to reply "no" and I won't follow up again.
"""

# ==============================================================================
# FALLBACK EMAIL TEMPLATE
# ==============================================================================
# Used when AI generation fails or no data is available.

FALLBACK_EMAIL_SUBJECT = "Resilution's seed round overview"

FALLBACK_EMAIL_BODY = """Hi {first_name},

I wanted to reach out regarding Resilution—we're building infrastructure that lets investors back real-world SME revenue streams in a transparent, data-driven way.

We're raising a $2M seed round to move from successful private pilots to a fully live platform. If this aligns with {company}'s interests, I'd be happy to walk you through the product and early metrics.

Calendly: https://calendly.com/resilblockchain

Best,
Matthew Ettswold

Website: https://www.resilution.io/
Linktree: https://linktr.ee/Resilution
Whitepaper: https://www.resilution.io/resilution-whitepaper.pdf
Pitch Deck: https://media.resilution.io/RESILUTION_PITCH_DECK.pdf

If this isn't relevant, feel free to reply "no" and I won't follow up again."""
