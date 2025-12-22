"""
Gemini AI Researcher - AI-powered research using Google Gemini with search grounding.

Unlike traditional web scraping (HTML parsing), this uses Google's Gemini AI
to search the web and provide summarized, relevant information.

Benefits over HTML scraping:
- No HTML parsing needed - AI does the work
- More precise, relevant information
- Handles dynamic/JavaScript sites that block scrapers
- Provides context-aware summaries instead of raw text
"""

import logging
from typing import Any, Dict

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from config.settings import Config

logger = logging.getLogger(__name__)


class GeminiResearcher:
    """
    Uses Google Gemini AI with search grounding for investor research.
    
    This is NOT web scraping - it's AI-powered research that:
    1. Searches the web using Google's search engine
    2. Reads and understands the content
    3. Provides a summarized, relevant answer
    
    Much more powerful than traditional scraping!
    """

    def __init__(self):
        """Initialize Gemini researcher with API configuration."""
        if not GEMINI_AVAILABLE:
            logger.warning("google-generativeai not installed. Run: pip install google-generativeai")
            return
        
        if not Config.GOOGLE_GEMINI_API_KEY:
            logger.warning("Gemini API key not configured in .env")
            return
        
        # Configure Gemini API
        genai.configure(api_key=Config.GOOGLE_GEMINI_API_KEY)
        
        # Use Gemini 2.0 Flash with search grounding
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def research(self, email: str, name: str = "", company: str = "", title: str = "") -> Dict[str, Any]:
        """
        Use Gemini AI to research an investor and their focus areas.
        
        Args:
            email: Contact's email address
            name: Contact's full name
            company: Company name
            title: Job title
            
        Returns:
            Dict with AI-generated research summary and metadata
        """
        if not GEMINI_AVAILABLE:
            return {
                "error": "Gemini not available - install google-generativeai",
                "source": "gemini_ai",
                "success": False
            }
        
        if not Config.GOOGLE_GEMINI_API_KEY:
            return {
                "error": "Gemini API key not configured",
                "source": "gemini_ai",
                "success": False
            }
        
        # Validate email
        if '@' not in email:
            logger.warning("Invalid email format: %s", email)
            return {
                "error": "Invalid email format",
                "source": "gemini_ai",
                "success": False
            }
        
        username, domain = email.split('@', 1)
        
        # Build comprehensive research prompt
        search_prompt = self._build_research_prompt(name or username, company, domain, title)
        
        logger.info("🔍 Gemini AI researching: %s at %s", name or username, company)
        
        try:
            # Generate with search grounding enabled (Gemini 2.0 Flash)
            # Search grounding is built-in for this model
            response = self.model.generate_content(search_prompt)
            
            if not response or not response.text:
                logger.warning("Gemini returned empty response")
                return {
                    "source": "gemini_ai",
                    "query": f"{name} {company}",
                    "success": False,
                    "error": "Empty response from Gemini"
                }
            
            # Extract the AI-generated summary
            summary = response.text
            
            # Get grounding metadata (sources/citations) if available
            sources = []
            grounding_metadata = getattr(response, 'grounding_metadata', None)
            if grounding_metadata:
                for chunk in getattr(grounding_metadata, 'search_entry_point', []):
                    if hasattr(chunk, 'rendered_content'):
                        sources.append(chunk.rendered_content)
            
            logger.info("✅ Gemini research completed (%d chars)", len(summary))
            
            return {
                "source": "gemini_ai",
                "query": f"{name} {company}",
                "success": True,
                "summary": summary[:2500],  # Trim to reasonable length
                "sources": sources,
                "raw_length": len(summary),
                "content_summary": summary[:2000],  # For AI personalization
                "description": summary[:500] if len(summary) > 500 else summary,
            }
            
        except Exception as e:
            logger.error("Gemini research error: %s", str(e))
            return {
                "error": f"Gemini error: {str(e)[:150]}",
                "source": "gemini_ai",
                "query": f"{name} {company}",
                "success": False
            }

    def _build_research_prompt(self, name: str, company: str, domain: str, title: str = "") -> str:
        """
        Build a comprehensive research prompt for Gemini.
        
        The prompt instructs Gemini to search and summarize information
        about the investor and their investment focus.
        
        Args:
            name: Investor's name
            company: Company name
            domain: Email domain
            title: Job title (optional)
            
        Returns:
            Formatted research prompt string
        """
        prompt = f"""Search the web and provide detailed information about this investor:

Name: {name}
Company: {company}
Email Domain: {domain}
{f"Title: {title}" if title else ""}

Please find and summarize:
1. Their investment focus (what sectors/stages they invest in)
2. Recent portfolio companies or investments
3. Their background and expertise
4. Company's investment thesis and focus areas
5. Any notable achievements or specializations

Be specific and factual. Include relevant links/sources."""
        
        return prompt

    def is_available(self) -> bool:
        """
        Check if Gemini researcher is properly configured and available.
        
        Returns:
            True if Gemini is available and configured, False otherwise
        """
        return GEMINI_AVAILABLE and bool(Config.GOOGLE_GEMINI_API_KEY)
