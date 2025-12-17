"""
Website scraping module for enriching contact data.

This module scrapes company websites to gather information for email personalization:
- Company description
- Recent news/press releases
- Product/service information
- Investment focus (for VCs)
- Team information

The scraped data is stored in the database and used by AI to personalize emails.

Usage:
    from modules.web_scraper import WebScraper
    
    scraper = WebScraper()
    data = scraper.scrape_website("https://example.com")
    
    # Store in database
    db.update_contact_scraped_data(contact_id, data)
"""

import logging
import json
from typing import Dict, Optional, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config.settings import Config
from modules.utils import safe_request, clean_url, is_valid_url

logger = logging.getLogger(__name__)


class WebScraper:
    """
    Scrape and extract relevant information from company websites.
    """
    
    def __init__(self):
        """Initialize web scraper."""
        self.timeout = Config.SCRAPING_TIMEOUT
        self.max_retries = Config.MAX_RETRIES
    
    def scrape_website(self, url: str) -> Dict:
        """
        Scrape a company website and extract relevant information.
        
        Args:
            url: Company website URL
        
        Returns:
            dict: Scraped data including:
                - description: Company description
                - keywords: Relevant keywords
                - recent_news: Recent announcements
                - products: Products/services
                - team_size: Estimated team size
                - raw_text: Full cleaned text for AI processing
        """
        if not is_valid_url(url):
            logger.warning(f"Invalid URL: {url}")
            return self._empty_result()
        
        url = clean_url(url)
        logger.info(f"Scraping website: {url}")
        
        try:
            # Get homepage
            response = safe_request(url, retries=self.max_retries, timeout=self.timeout)
            if not response:
                return self._empty_result()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract various data points
            result = {
                'url': url,
                'description': self._extract_description(soup, url),
                'keywords': self._extract_keywords(soup),
                'recent_news': self._extract_news(soup, url),
                'products': self._extract_products(soup),
                'team_size': self._estimate_team_size(soup),
                'social_links': self._extract_social_links(soup),
                'raw_text': self._extract_clean_text(soup),
                'meta_info': self._extract_meta_tags(soup)
            }
            
            logger.info(f"Successfully scraped {url}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return self._empty_result()
    
    def scrape_about_page(self, base_url: str) -> Optional[str]:
        """
        Find and scrape the About page for more detailed information.
        
        Args:
            base_url: Company website homepage URL
        
        Returns:
            str or None: About page content
        """
        about_urls = [
            urljoin(base_url, '/about'),
            urljoin(base_url, '/about-us'),
            urljoin(base_url, '/about/'),
            urljoin(base_url, '/company'),
        ]
        
        for url in about_urls:
            try:
                response = safe_request(url, retries=1, timeout=5)
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    return self._extract_clean_text(soup)
            except:
                continue
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup, url: str) -> str:
        """Extract company description from meta tags or first paragraphs."""
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Fall back to first substantial paragraph
        paragraphs = soup.find_all('p')
        for p in paragraphs[:5]:
            text = p.get_text().strip()
            if len(text) > 100:  # Substantial content
                return text[:500]  # Limit length
        
        return "No description found"
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract relevant keywords from meta tags and headers."""
        keywords = []
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords.extend([k.strip() for k in meta_keywords['content'].split(',')])
        
        # Extract from headers
        headers = soup.find_all(['h1', 'h2', 'h3'])
        for header in headers[:10]:
            text = header.get_text().strip()
            if text and len(text) < 100:
                keywords.append(text)
        
        return keywords[:20]  # Limit to top 20
    
    def _extract_news(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract recent news or blog posts."""
        news_items = []
        
        # Look for common news/blog selectors
        selectors = [
            'article',
            '.news-item',
            '.blog-post',
            '.press-release',
            '[class*="news"]',
            '[class*="blog"]'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            for item in items[:5]:
                title = item.find(['h1', 'h2', 'h3', 'h4'])
                if title:
                    news_items.append(title.get_text().strip())
        
        return news_items[:5]  # Top 5 news items
    
    def _extract_products(self, soup: BeautifulSoup) -> List[str]:
        """Extract product or service names."""
        products = []
        
        # Look for product-related sections
        product_sections = soup.find_all(['div', 'section'], class_=lambda c: c and any(
            term in c.lower() for term in ['product', 'service', 'solution', 'offering']
        ))
        
        for section in product_sections[:5]:
            headers = section.find_all(['h2', 'h3', 'h4'])
            for header in headers:
                text = header.get_text().strip()
                if text and len(text) < 100:
                    products.append(text)
        
        return products[:10]
    
    def _estimate_team_size(self, soup: BeautifulSoup) -> Optional[str]:
        """Estimate team size from Team/About pages."""
        # Look for team member listings
        team_indicators = soup.find_all(class_=lambda c: c and any(
            term in c.lower() for term in ['team', 'member', 'employee', 'staff']
        ))
        
        if len(team_indicators) > 20:
            return "Large (50+)"
        elif len(team_indicators) > 10:
            return "Medium (10-50)"
        elif len(team_indicators) > 5:
            return "Small (5-10)"
        else:
            return "Startup (<5)"
    
    def _extract_social_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media links."""
        social_links = {}
        
        social_domains = {
            'linkedin.com': 'linkedin',
            'twitter.com': 'twitter',
            'facebook.com': 'facebook',
            'github.com': 'github',
            'youtube.com': 'youtube'
        }
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            for domain, name in social_domains.items():
                if domain in href:
                    social_links[name] = href
                    break
        
        return social_links
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """
        Extract clean, readable text from page (for AI processing).
        
        This removes scripts, styles, navigation, footers, etc.
        """
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'noscript']):
            element.decompose()
        
        # Get text from main content areas
        main_content = soup.find('main') or soup.find('article') or soup.body
        if not main_content:
            return ""
        
        # Get text
        text = main_content.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Limit length (for AI token limits)
        return text[:5000]
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract useful meta tags."""
        meta_info = {}
        
        # Common meta tags
        meta_tags = {
            'og:title': 'title',
            'og:type': 'type',
            'og:image': 'image',
            'twitter:card': 'twitter_card',
            'author': 'author'
        }
        
        for meta_name, key in meta_tags.items():
            meta = soup.find('meta', attrs={'property': meta_name}) or \
                   soup.find('meta', attrs={'name': meta_name})
            if meta and meta.get('content'):
                meta_info[key] = meta['content']
        
        return meta_info
    
    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'url': '',
            'description': '',
            'keywords': [],
            'recent_news': [],
            'products': [],
            'team_size': None,
            'social_links': {},
            'raw_text': '',
            'meta_info': {}
        }
    
    def scrape_contact_data(self, contact: Dict) -> Dict:
        """
        Scrape website data for a contact.
        
        Args:
            contact: Contact dict with 'company_website' field
        
        Returns:
            dict: Scraped data with 'scraped_data' key (JSON string)
        """
        website = contact.get('company_website')
        if not website:
            logger.debug(f"No website for contact: {contact.get('email')}")
            return {}
        
        scraped = self.scrape_website(website)
        
        # Also try to get About page
        about_text = self.scrape_about_page(website)
        if about_text:
            scraped['about_page'] = about_text
        
        return {
            'scraped_data': json.dumps(scraped),
            'scraped_at': None  # Will be set by database
        }
