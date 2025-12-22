"""
LinkedIn Scraper - HTML scraping for LinkedIn profiles.

Note: LinkedIn heavily blocks scrapers. This works for public profiles
that don't require login, but success rate is low (~30-50%).
"""

import logging
import re
import random
import time
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

from config.settings import Config

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """
    Scrapes LinkedIn profiles and company pages.
    
    Warning: LinkedIn uses heavy anti-scraping measures:
    - HTTP 999 errors are common (rate limiting)
    - Most profiles require login
    - Success rate is typically 30-50%
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    def __init__(self):
        """Initialize LinkedIn scraper with session and settings."""
        self.session = requests.Session()
        self.timeout = Config.SCRAPING_TIMEOUT
        self.max_retries = Config.MAX_RETRIES
        self.proxy_config = Config.get_proxy_config()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent."""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def fetch_page(self, url: str, retries: int = None) -> Optional[str]:
        """
        Fetch LinkedIn page with retries.
        
        Args:
            url: LinkedIn URL to fetch
            retries: Number of retries (default: Config.MAX_RETRIES)
            
        Returns:
            HTML content or None if failed
        """
        if retries is None:
            retries = self.max_retries
            
        for attempt in range(retries):
            try:
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                    proxies=self.proxy_config,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 999:
                    # LinkedIn's anti-scraping response
                    logger.warning("HTTP 999 for %s", url)
                    # Longer wait for 999 errors
                    time.sleep(random.uniform(3, 6))
                elif response.status_code == 403:
                    logger.warning("Access forbidden (403) for %s", url)
                    return None
                else:
                    logger.warning("HTTP %d for %s", response.status_code, url)
                    
            except requests.exceptions.Timeout:
                logger.warning("Timeout fetching %s (attempt %d/%d)", url, attempt + 1, retries)
            except requests.exceptions.RequestException as e:
                logger.warning("Request error for %s: %s", url, str(e)[:100])
                
            # Longer delay between retries for LinkedIn
            if attempt < retries - 1:
                time.sleep(random.uniform(2, 5))
                
        return None

    def parse(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse LinkedIn profile/company page.
        
        Args:
            html: HTML content to parse
            url: URL of the LinkedIn page
            
        Returns:
            Dict with extracted LinkedIn data
        """
        soup = BeautifulSoup(html, 'html.parser')
        data = {
            "source": "linkedin",
            "url": url,
            "headline": "",
            "summary": "",
            "experience": [],
            "company_about": "",
        }
        
        # Try to get basic info (works on some public pages)
        # LinkedIn structure changes often, so we try multiple selectors
        
        # Get page text as fallback
        for tag in soup(['script', 'style', 'nav']):
            tag.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)[:3000]
        
        # Look for common LinkedIn content patterns
        if 'Experience' in text:
            data["has_experience"] = True
        if 'About' in text:
            data["has_about"] = True
            
        data["content_summary"] = text[:1500]
        
        return data

    def scrape(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a LinkedIn URL and return parsed data.
        
        Args:
            url: LinkedIn URL to scrape
            
        Returns:
            Parsed LinkedIn data or None if failed
        """
        if not url or "linkedin.com" not in url:
            logger.warning("Invalid LinkedIn URL: %s", url)
            return None
        
        logger.info("Scraping LinkedIn: %s", url)
        html = self.fetch_page(url)
        
        if not html:
            logger.warning("❌ LinkedIn scrape failed (likely blocked)")
            return None
        
        data = self.parse(html, url)
        logger.info("✅ LinkedIn scraped successfully")
        return data
