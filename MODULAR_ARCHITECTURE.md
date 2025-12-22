# Modular Scraper Architecture

## Overview
The scraping system has been refactored into **independent, modular components** for better maintainability.

## New Structure

```
modules/
├── web_scraper.py              (Orchestrator - 170 lines)
└── scrapers/
    ├── __init__.py             (Module exports)
    ├── website_scraper.py      (HTML scraping for websites)
    ├── linkedin_scraper.py     (HTML scraping for LinkedIn)
    └── gemini_researcher.py    (AI-powered research - NO scraping!)
```

## Benefits

### 1. **Single Responsibility**
- Each file has ONE job
- Easy to understand and test
- Clear separation of concerns

### 2. **Easy Maintenance**
- Want to change website scraping? → Edit `website_scraper.py` only
- Want to change Gemini prompts? → Edit `gemini_researcher.py` only
- Want to change LinkedIn logic? → Edit `linkedin_scraper.py` only
- **No need to touch multiple files!**

### 3. **Independent Testing**
```python
# Test website scraping only
from modules.scrapers import WebsiteScraper
scraper = WebsiteScraper()
data = scraper.scrape("https://example.com")

# Test Gemini research only
from modules.scrapers import GeminiResearcher
researcher = GeminiResearcher()
data = researcher.research("email@domain.com", "John Doe", "Company Inc")
```

## Key Differences

### Before (Monolithic):
```
web_scraper.py (600+ lines)
├── _fetch_page()          ← Used by all
├── _parse_website()       ← Website specific
├── _parse_linkedin()      ← LinkedIn specific  
├── _search_with_gemini()  ← Gemini specific
└── scrape_all_sources()   ← Orchestrator

Problem: Changing one thing requires editing a huge file
```

### After (Modular):
```
web_scraper.py (170 lines)
└── scrape_all_sources()   ← Orchestrator only

website_scraper.py
├── fetch_page()
├── parse()
└── scrape()

linkedin_scraper.py
├── fetch_page()
├── parse()
└── scrape()

gemini_researcher.py
├── research()
└── _build_research_prompt()

Benefit: Each file is focused and independent
```

## Important Clarifications

### Website Scraping (UNCHANGED)
- **Still exists** in `modules/scrapers/website_scraper.py`
- **Still works** exactly the same way
- Parses HTML, extracts meta tags, content, etc.
- **No changes to functionality**

### LinkedIn Scraping (UNCHANGED)
- **Still exists** in `modules/scrapers/linkedin_scraper.py`
- **Still works** exactly the same way (success rate ~30-50%)
- Handles HTTP 999 errors, retries, etc.
- **No changes to functionality**

### Gemini AI Research (NEW REPLACEMENT)
- **Replaces**: Google Custom Search API + HTML scraping
- **Location**: `modules/scrapers/gemini_researcher.py`
- **What it does**: AI-powered research with Google search grounding
- **No HTML parsing** - Gemini does the work!

### What Changed?
```
BEFORE:
Source 3 = Google API → Find top link → Scrape that HTML → Parse

AFTER:
Source 3 = Gemini AI → Search web → AI summarizes → Done!
```

## How to Modify Each Source

### Modify Website Scraping
```python
# Edit: modules/scrapers/website_scraper.py

# Example: Add new meta tag extraction
def parse(self, html: str, url: str):
    # ... existing code ...
    
    # Add your custom extraction here
    author_tag = soup.find('meta', attrs={'name': 'author'})
    if author_tag:
        data["author"] = author_tag.get('content', '')
```

### Modify Gemini AI Research
```python
# Edit: modules/scrapers/gemini_researcher.py

# Example: Change the research prompt
def _build_research_prompt(self, name, company, domain, title):
    prompt = f"""
    Search and provide information about {name} at {company}.
    
    Focus on:
    1. Their recent investments (last 12 months)
    2. Typical check size
    3. Geographic focus
    # ... add your custom requirements ...
    """
    return prompt
```

### Modify LinkedIn Scraping
```python
# Edit: modules/scrapers/linkedin_scraper.py

# Example: Increase retry attempts
def __init__(self):
    self.max_retries = 5  # Increase from 3 to 5
```

## No Breaking Changes

All existing code works without modification:
```python
# Still works exactly the same!
from modules.web_scraper import WebScraper

scraper = WebScraper()
data = scraper.scrape_all_sources(contact)

# Returns same structure:
# {
#   "sources_tried": ["website", "linkedin", "gemini_ai"],
#   "sources_succeeded": ["website", "gemini_ai"],
#   "website_data": {...},
#   "linkedin_data": None,
#   "gemini_data": {...},
#   ...
# }
```

## Next Steps

1. **Install Gemini package**: `pip install google-generativeai`
2. **Get Gemini API key**: https://aistudio.google.com/app/apikey
3. **Add to .env**: `GOOGLE_GEMINI_API_KEY=your_key_here`
4. **Test**: Run `python scripts/preview_emails.py`

## File Locations

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **Orchestrator** | `modules/web_scraper.py` | Coordinates all sources |
| **Website Scraper** | `modules/scrapers/website_scraper.py` | HTML parsing for websites |
| **LinkedIn Scraper** | `modules/scrapers/linkedin_scraper.py` | HTML parsing for LinkedIn |
| **Gemini Researcher** | `modules/scrapers/gemini_researcher.py` | AI-powered research |

---

**Summary**: The system is now **modular and maintainable**. Each source is independent, testable, and easy to modify without affecting others! 🎉
