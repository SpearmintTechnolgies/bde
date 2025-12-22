"""
Scrapers module - Modular web scraping components.

Each scraper is independent and focused on a single source:
- WebsiteScraper: HTML scraping of company websites
- LinkedInScraper: HTML scraping of LinkedIn profiles
- GeminiResearcher: AI-powered research using Google Gemini with search grounding
"""

from .website_scraper import WebsiteScraper
from .linkedin_scraper import LinkedInScraper
from .gemini_researcher import GeminiResearcher

__all__ = ['WebsiteScraper', 'LinkedInScraper', 'GeminiResearcher']
