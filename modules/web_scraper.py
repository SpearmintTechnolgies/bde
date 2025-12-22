"""
Multi-source web scraper orchestrator.

Coordinates 3 independent research sources:
1. WebsiteScraper: Company website HTML scraping
2. LinkedInScraper: LinkedIn profile HTML scraping  
3. GeminiResearcher: AI-powered research (no scraping!)

Each source is a separate module for easy maintenance and modification.
"""

import logging
import time
import random
from typing import Any, Dict

from modules.scrapers import WebsiteScraper, LinkedInScraper, GeminiResearcher

logger = logging.getLogger(__name__)


class WebScraper:
    """
    Orchestrates multi-source research by coordinating separate scrapers.
    
    This class doesn't scrape anything itself - it delegates to:
    - WebsiteScraper: For company website scraping
    - LinkedInScraper: For LinkedIn profile scraping
    - GeminiResearcher: For AI-powered research
    
    Benefits of this architecture:
    - Each source is independent and testable
    - Easy to modify one source without affecting others
    - Clear separation of concerns
    
    To modify a specific source:
    - Website scraping → Edit modules/scrapers/website_scraper.py
    - LinkedIn scraping → Edit modules/scrapers/linkedin_scraper.py
    - Gemini AI research → Edit modules/scrapers/gemini_researcher.py
    """

    def __init__(self):
        """Initialize orchestrator with individual scrapers."""
        self.website_scraper = WebsiteScraper()
        self.linkedin_scraper = LinkedInScraper()
        self.gemini_researcher = GeminiResearcher()

    def scrape_all_sources(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate multi-source research for a contact.
        
        Delegates to individual scrapers:
        1. WebsiteScraper → Company website (HTML)
        2. LinkedInScraper → LinkedIn profile (HTML)
        3. GeminiResearcher → AI-powered research (no scraping!)
        
        Args:
            contact: Contact dict with website, linkedin_url, email, name, company
            
        Returns:
            Combined data from all successful sources
        """
        combined_data = {
            "sources_tried": [],
            "sources_succeeded": [],
            "website_data": None,
            "linkedin_data": None,
            "gemini_data": None,
            "description": "",
            "keywords": [],
            "company_focus": "",
            "content_summary": "",
            "social_links": {},
        }
        
        # 1. Website scraping (using WebsiteScraper module)
        website = contact.get("website", "")
        if website:
            combined_data["sources_tried"].append("website")
            website_data = self.website_scraper.scrape(website)
            
            if website_data:
                combined_data["website_data"] = website_data
                combined_data["sources_succeeded"].append("website")
                
                # Merge website data
                combined_data["description"] = website_data.get("description", "")
                combined_data["keywords"] = website_data.get("keywords", [])
                combined_data["company_focus"] = website_data.get("company_focus", "")
                combined_data["social_links"] = website_data.get("social_links", {})
                combined_data["content_summary"] = website_data.get("content_summary", "")
        
        # Small delay between requests
        time.sleep(random.uniform(1, 2))
        
        # 2. LinkedIn scraping (using LinkedInScraper module)
        linkedin_url = contact.get("linkedin_url", "")
        if linkedin_url:
            combined_data["sources_tried"].append("linkedin")
            linkedin_data = self.linkedin_scraper.scrape(linkedin_url)
            
            if linkedin_data:
                combined_data["linkedin_data"] = linkedin_data
                combined_data["sources_succeeded"].append("linkedin")
                
                # Append LinkedIn content to summary
                if linkedin_data.get("content_summary"):
                    combined_data["content_summary"] += "\n\nLinkedIn: " + linkedin_data["content_summary"]
        
        # Small delay
        time.sleep(random.uniform(1, 2))
        
        # 3. Gemini AI research (using GeminiResearcher module - NO SCRAPING!)
        email = contact.get("email", "")
        name = contact.get("name", "")
        company = contact.get("company", "")
        title = contact.get("title", "")
        
        if email and name and self.gemini_researcher.is_available():
            combined_data["sources_tried"].append("gemini_ai")
            gemini_data = self.gemini_researcher.research(email, name, company, title)
            
            if gemini_data.get("success"):
                combined_data["gemini_data"] = gemini_data
                combined_data["sources_succeeded"].append("gemini_ai")
                
                # Gemini provides AI-summarized content (no HTML parsing needed!)
                # If we don't have description from website, use Gemini summary
                if not combined_data["description"] and gemini_data.get("description"):
                    combined_data["description"] = gemini_data["description"]
                
                # Append Gemini AI research to summary
                if gemini_data.get("content_summary"):
                    combined_data["content_summary"] += "\n\nGemini AI Research: " + gemini_data["content_summary"]
                
                logger.info("✅ Gemini AI research succeeded (%d chars)", len(gemini_data.get("summary", "")))
        
        # Trim content summary to max length
        if combined_data["content_summary"]:
            combined_data["content_summary"] = combined_data["content_summary"][:3000]
        
        # Log summary
        logger.info(
            "Scraping complete: %d/%d sources succeeded (%s)",
            len(combined_data["sources_succeeded"]),
            len(combined_data["sources_tried"]),
            ", ".join(combined_data["sources_succeeded"]) or "none"
        )
        
        return combined_data

    def scrape_website(self, url: str) -> Dict[str, Any]:
        """
        Legacy method: Scrape just the website.
        
        For backward compatibility with existing code.
        Use scrape_all_sources() for full multi-source scraping.
        
        Args:
            url: Website URL to scrape
            
        Returns:
            Parsed website data or error dict
        """
        if not url:
            return {"error": "No URL provided"}
        
        return self.website_scraper.scrape(url) or {"error": f"Failed to scrape {url}"}
