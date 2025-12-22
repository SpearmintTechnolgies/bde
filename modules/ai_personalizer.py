"""
AI-powered email personalization using LangChain.

Generates highly personalized pitch emails using the master prompt framework.
"""

import logging
import re
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from config.settings import Config
from config.prompts import (
    RESILUTION_CORE,
    MASTER_PROMPT_TEMPLATE,
    FALLBACK_EMAIL_SUBJECT,
    FALLBACK_EMAIL_BODY
)

logger = logging.getLogger(__name__)


class AIPersonalizer:
    """
    AI-powered email personalizer using multi-source scraped data.
    
    Uses master prompt from config.prompts for consistent email generation.
    """

    def __init__(self, temperature: float = 0.7):
        """Initialize the AI personalizer with OpenAI.

        Some models (notably the `o4-*` family) only accept the default
        temperature value. If an `o4-` model is configured, force
        temperature to 1 to avoid API errors.
        """
        # Adjust temperature for models that enforce default only
        adjusted_temp = temperature
        try:
            if isinstance(Config.OPENAI_MODEL, str) and Config.OPENAI_MODEL.startswith("o4"):
                adjusted_temp = 1.0
        except Exception:
            adjusted_temp = temperature

        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=adjusted_temp,
            api_key=Config.OPENAI_API_KEY,
            request_timeout=60,
            max_retries=2
        )
        logger.info("AI Personalizer initialized with model: %s", Config.OPENAI_MODEL)

    def personalize_email(
        self, 
        contact: Dict[str, Any], 
        scraped_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a highly personalized pitch email.
        
        Uses multi-source scraped data to create an email that:
        1. Opens with their world, not ours
        2. Frames the problem in one sentence
        3. Explains the product in outcomes, not mechanics
        4. Shows traction + clear use of funds
        5. Ends with a low-pressure CTA
        
        Args:
            contact: Contact info (name, company, job_title, email, etc.)
            scraped_data: Combined data from website, LinkedIn, Google
            
        Returns:
            Dict with subject, body, confidence score
        """
        
        # Build recipient context
        recipient_context = self._build_recipient_context(contact, scraped_data)
        
        # Build the prompt using imported MASTER_PROMPT_TEMPLATE
        prompt = PromptTemplate(
            input_variables=["investor_data", "resilution_core"],
            template=MASTER_PROMPT_TEMPLATE
        )
        
        try:
            # Generate email using master prompt (from config.prompts)
            formatted_prompt = prompt.format(
                investor_data=recipient_context,
                resilution_core=RESILUTION_CORE
            )
            
            response = self.llm.invoke(formatted_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse subject and body
            subject, body = self._parse_email_response(content)
            
            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(scraped_data)
            
            logger.info("Generated email with subject: %s (confidence: %.2f)", subject[:50], confidence)
            
            return {
                "subject": subject,
                "body": body,
                "confidence": confidence,
                "model": Config.OPENAI_MODEL,
                "sources_used": scraped_data.get("sources_succeeded", []) if scraped_data else []
            }
            
        except Exception as e:
            logger.error("AI personalization failed: %s", e)
            return self._fallback_email(contact)

    def _build_recipient_context(
        self, 
        contact: Dict[str, Any], 
        scraped_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive recipient context from contact + scraped data."""
        
        context = f"""
RECIPIENT PROFILE:
- Name: {contact.get('name', 'Unknown')}
- First Name: {contact.get('first_name', contact.get('name', 'there').split()[0])}
- Company: {contact.get('company', 'Unknown')}
- Job Title: {contact.get('job_title', 'Unknown')}
- Email: {contact.get('email', 'Unknown')}
- Industry: {contact.get('industry', 'Unknown')}
"""
        
        if scraped_data:
            # Add sources info
            context += f"""
DATA SOURCES:
- Tried: {', '.join(scraped_data.get('sources_tried', []))}
- Succeeded: {', '.join(scraped_data.get('sources_succeeded', []))}
"""
            
            # Add website data
            if scraped_data.get('description'):
                context += f"\nCOMPANY DESCRIPTION:\n{scraped_data['description'][:500]}\n"
                
            if scraped_data.get('company_focus'):
                context += f"\nINVESTMENT FOCUS:\n{scraped_data['company_focus'][:300]}\n"
                
            if scraped_data.get('keywords'):
                context += f"\nKEYWORDS: {', '.join(scraped_data['keywords'][:10])}\n"
                
            # Add content summary (combined from all sources)
            if scraped_data.get('content_summary'):
                context += f"\nRESEARCH SUMMARY:\n{scraped_data['content_summary'][:2000]}\n"
                
            # Add LinkedIn insights
            if scraped_data.get('linkedin_data'):
                linkedin = scraped_data['linkedin_data']
                if linkedin.get('headline'):
                    context += f"\nLINKEDIN HEADLINE: {linkedin['headline']}\n"
                if linkedin.get('summary'):
                    context += f"\nLINKEDIN SUMMARY: {linkedin['summary'][:500]}\n"
                    
            # Add Google insights
            if scraped_data.get('google_data'):
                google = scraped_data['google_data']
                if google.get('snippets'):
                    context += f"\nPUBLIC MENTIONS:\n"
                    for snippet in google['snippets'][:3]:
                        context += f"- {snippet[:200]}\n"
        else:
            context += "\nNOTE: No scraped data available. Use contact info only.\n"
            
        return context

    def _parse_email_response(self, content: str) -> tuple:
        """Parse AI response into subject and body."""
        
        # Try to extract subject line
        subject_match = re.search(r'SUBJECT:\s*(.+?)(?:\n|$)', content, re.I)
        
        if subject_match:
            subject = subject_match.group(1).strip()
            # Remove subject line from body
            body = content[subject_match.end():].strip()
        else:
            # Fallback: first line is subject
            lines = content.strip().split('\n', 1)
            subject = lines[0].replace('Subject:', '').strip()
            body = lines[1].strip() if len(lines) > 1 else content
            
        # Clean up subject
        subject = subject.strip('"\'')
        
        # Ensure body has proper formatting
        body = body.strip()
        
        return subject, body

    def _calculate_confidence(self, scraped_data: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence score based on available data."""
        if not scraped_data:
            return 0.5
            
        score = 0.5  # Base score
        
        sources = scraped_data.get('sources_succeeded', [])
        
        # Boost for each successful source
        if 'website' in sources:
            score += 0.2
        if 'linkedin' in sources:
            score += 0.15
        if 'google' in sources:
            score += 0.1
            
        # Boost for rich data
        if scraped_data.get('description'):
            score += 0.05
        if scraped_data.get('company_focus'):
            score += 0.05
        if scraped_data.get('keywords'):
            score += 0.05
            
        return min(score, 0.99)

    def _fallback_email(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic fallback email when AI fails (uses templates from config.prompts)."""
        
        first_name = contact.get('first_name', contact.get('name', 'there').split()[0])
        company = contact.get('company', 'your company')
        
        subject = FALLBACK_EMAIL_SUBJECT
        body = FALLBACK_EMAIL_BODY.format(first_name=first_name, company=company)

        return {
            "subject": subject,
            "body": body,
            "confidence": 0.3,
            "model": "fallback",
            "sources_used": []
        }
