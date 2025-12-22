"""
Website Scraper - HTML scraping for company websites.

Extracts:
- Meta descriptions and keywords
- Company focus and portfolio information
- Social media links
- Main content for AI analysis
"""

import logging
import re
import random
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config.settings import Config

logger = logging.getLogger(__name__)


class WebsiteScraper:
    """
    Scrapes company websites for relevant information.
    Focused on HTML parsing and content extraction.
    """

    # Rotate user agents to avoid blocks
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        """Initialize website scraper with session and settings."""
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
        Fetch a page with retries and error handling.
        
        Args:
            url: URL to fetch
            retries: Number of retries (default: Config.MAX_RETRIES)
            
        Returns:
            HTML content or None if failed
        """
        if retries is None:
            retries = self.max_retries
            
        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
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
                elif response.status_code == 403:
                    logger.warning("Access forbidden (403) for %s", url)
                    return None
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = (attempt + 1) * 5
                    logger.warning("Rate limited, waiting %ds...", wait_time)
                    time.sleep(wait_time)
                else:
                    logger.warning("HTTP %d for %s", response.status_code, url)
                    
            except requests.exceptions.Timeout:
                logger.warning("Timeout fetching %s (attempt %d/%d)", url, attempt + 1, retries)
            except requests.exceptions.RequestException as e:
                logger.warning("Request error for %s: %s", url, str(e)[:100])
                
            # Small delay between retries
            if attempt < retries - 1:
                time.sleep(random.uniform(1, 3))
                
        return None

    def parse(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse company website for relevant information.
        
        Extracts:
        - Description (meta, og:description, or first paragraphs)
        - Keywords (meta keywords + inferred from content)
        - Products/services mentioned
        - Team/about information
        - Recent news/blog posts
        - Social links
        
        Args:
            html: HTML content to parse
            url: URL of the page
            
        Returns:
            Dict with extracted website data
        """
        soup = BeautifulSoup(html, 'html.parser')
        data = {
            "source": "website",
            "url": url,
            "description": "",
            "keywords": [],
            "products": [],
            "team_info": "",
            "recent_news": [],
            "social_links": {},
            "company_focus": "",
        }
        
        # Extract title
        title = soup.find('title')
        if title:
            data["title"] = title.get_text(strip=True)
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            data["description"] = meta_desc.get('content', '')[:500]
        
        # Try og:description if no meta description
        if not data["description"]:
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc:
                data["description"] = og_desc.get('content', '')[:500]
        
        # Extract meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            keywords = meta_keywords.get('content', '')
            data["keywords"] = [k.strip() for k in keywords.split(',') if k.strip()][:15]
        
        # Extract main content for analysis
        # Remove script, style, nav, footer
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        # Get visible text
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)[:5000]  # Limit text length
        
        # Infer keywords from headings
        headings = soup.find_all(['h1', 'h2', 'h3'])
        heading_text = ' '.join([h.get_text(strip=True) for h in headings[:10]])
        if heading_text:
            data["headings"] = heading_text[:500]
        
        # Look for about/team pages
        about_links = soup.find_all('a', href=re.compile(r'(about|team|people|who-we-are)', re.I))
        if about_links:
            data["has_team_page"] = True
        
        # Look for portfolio/investments (for VCs)
        portfolio_links = soup.find_all('a', href=re.compile(r'(portfolio|investments|companies)', re.I))
        if portfolio_links:
            data["has_portfolio"] = True
            
        # Extract social links
        social_patterns = {
            'linkedin': r'linkedin\.com',
            'twitter': r'twitter\.com|x\.com',
            'facebook': r'facebook\.com',
            'youtube': r'youtube\.com',
        }
        
        for social, pattern in social_patterns.items():
            link = soup.find('a', href=re.compile(pattern, re.I))
            if link:
                data["social_links"][social] = link.get('href', '')
        
        # Look for investment focus patterns in text
        focus_patterns = [
            r'we invest in (.+?)(?:\.|$)',
            r'focus(?:ed)? on (.+?)(?:\.|$)',
            r'back(?:ing)? (.+?)(?:\.|$)',
            r'portfolio (?:of |includes? )(.+?)(?:\.|$)',
        ]
        
        for pattern in focus_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                data["company_focus"] = match.group(1)[:200]
                break
        
        # Store trimmed content for AI
        data["content_summary"] = text[:2000]
        
        return data

    def scrape(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a website URL and return parsed data.
        
        Args:
            url: Website URL to scrape
            
        Returns:
            Parsed website data or None if failed
        """
        logger.info("Scraping website: %s", url)
        html = self.fetch_page(url)
        
        if not html:
            logger.warning("❌ Website scrape failed: %s", url)
            return None
        
        data = self.parse(html, url)
        logger.info("✅ Website scraped successfully")
        return data
