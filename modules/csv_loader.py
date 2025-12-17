"""
CSV loader for BDE email automation system.

Loads contacts from CSV and extracts only the columns we need.

Required columns:
- Email address (or similar: email, Email, email_address)
- Full name (or: name, Full name, first name + last name)
- Company
- Company Website (or: website, Website)

Optional columns:
- LinkedIn URL (or: linkedin, LinkedIn)
- Job title (or: title, position)

All other columns are ignored.
"""

import csv
import logging
from typing import List, Dict
from pathlib import Path

from modules.utils import validate_email, clean_url, is_empty, ensure_string

logger = logging.getLogger(__name__)


# Column name mappings (case-insensitive)
EMAIL_COLUMNS = ['email', 'email address', 'email_address', 'e-mail']
NAME_COLUMNS = ['name', 'full name', 'fullname', 'full_name']
FIRST_NAME_COLUMNS = ['first name', 'firstname', 'first_name']
LAST_NAME_COLUMNS = ['last name', 'lastname', 'last_name']
COMPANY_COLUMNS = ['company', 'company name', 'organization', 'firm']
WEBSITE_COLUMNS = ['website', 'company website', 'url', 'web', 'company_website']
LINKEDIN_COLUMNS = ['linkedin', 'linkedin url', 'linkedin_url', 'linkedin profile']
TITLE_COLUMNS = ['job title', 'title', 'position', 'role', 'job_title']


def find_column(headers: List[str], possible_names: List[str]) -> str:
    """
    Find column name from list of possibilities (case-insensitive).
    
    Args:
        headers: List of CSV column headers
        possible_names: List of possible column names
        
    Returns:
        str: Matching column name or empty string if not found
    """
    headers_lower = [h.lower().strip() for h in headers]
    
    for possible in possible_names:
        if possible.lower() in headers_lower:
            idx = headers_lower.index(possible.lower())
            return headers[idx]
    
    return ""


def load_contacts_csv(csv_file: str, max_contacts: int = None) -> List[Dict]:
    """
    Load contacts from CSV file.
    
    Only extracts the columns we need:
    - Email address (required)
    - Name (required)
    - Company (required)
    - Website (required)
    - LinkedIn (optional)
    - Job title (optional)
    
    All other columns are ignored.
    
    Args:
        csv_file: Path to CSV file
        max_contacts: Maximum contacts to load (None = all)
        
    Returns:
        list: List of contact dictionaries with normalized keys
        
    Example:
        >>> contacts = load_contacts_csv('data/contacts.csv')
        >>> print(contacts[0])
        {
            'email': 'john@example.com',
            'name': 'John Smith',
            'company': 'ABC Ventures',
            'website': 'https://abcvc.com',
            'linkedin_url': 'https://linkedin.com/in/johnsmith',
            'title': 'Partner'
        }
    """
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_file}")
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    contacts = []
    skipped = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        logger.info(f"CSV has {len(headers)} columns")
        
        # Find which columns to use
        email_col = find_column(headers, EMAIL_COLUMNS)
        name_col = find_column(headers, NAME_COLUMNS)
        first_name_col = find_column(headers, FIRST_NAME_COLUMNS)
        last_name_col = find_column(headers, LAST_NAME_COLUMNS)
        company_col = find_column(headers, COMPANY_COLUMNS)
        website_col = find_column(headers, WEBSITE_COLUMNS)
        linkedin_col = find_column(headers, LINKEDIN_COLUMNS)
        title_col = find_column(headers, TITLE_COLUMNS)
        
        # Log what we found
        logger.info(f"Detected columns:")
        logger.info(f"  Email: {email_col or 'NOT FOUND'}")
        logger.info(f"  Name: {name_col or (first_name_col + ' + ' + last_name_col if first_name_col else 'NOT FOUND')}")
        logger.info(f"  Company: {company_col or 'NOT FOUND'}")
        logger.info(f"  Website: {website_col or 'NOT FOUND'}")
        logger.info(f"  LinkedIn: {linkedin_col or 'not found (optional)'}")
        logger.info(f"  Title: {title_col or 'not found (optional)'}")
        
        # Check required columns
        if not email_col:
            raise ValueError("Required column 'Email' not found in CSV!")
        if not (name_col or (first_name_col and last_name_col)):
            raise ValueError("Required column 'Name' not found in CSV!")
        if not company_col:
            raise ValueError("Required column 'Company' not found in CSV!")
        if not website_col:
            raise ValueError("Required column 'Website' not found in CSV!")
        
        # Read rows
        for row_num, row in enumerate(reader, start=2):
            # Stop if reached max
            if max_contacts and len(contacts) >= max_contacts:
                break
            
            # Extract email
            email = ensure_string(row.get(email_col)).strip()
            
            # Validate email
            if not validate_email(email):
                logger.warning(f"Row {row_num}: Invalid email '{email}' - skipping")
                skipped += 1
                continue
            
            # Extract name (try full name first, then first+last)
            if name_col:
                name = ensure_string(row.get(name_col)).strip()
            else:
                first = ensure_string(row.get(first_name_col)).strip()
                last = ensure_string(row.get(last_name_col)).strip()
                name = f"{first} {last}".strip()
            
            if is_empty(name):
                name = "there"  # Default fallback
            
            # Extract company
            company = ensure_string(row.get(company_col)).strip()
            if is_empty(company):
                logger.warning(f"Row {row_num}: Missing company for {email} - skipping")
                skipped += 1
                continue
            
            # Extract website
            website = ensure_string(row.get(website_col)).strip()
            if is_empty(website):
                logger.warning(f"Row {row_num}: Missing website for {email} - skipping")
                skipped += 1
                continue
            
            # Clean website URL
            website = clean_url(website)
            
            # Extract optional fields
            linkedin_url = ""
            if linkedin_col:
                linkedin_url = ensure_string(row.get(linkedin_col)).strip()
                if linkedin_url:
                    linkedin_url = clean_url(linkedin_url)
            
            title = ""
            if title_col:
                title = ensure_string(row.get(title_col)).strip()
            
            # Create normalized contact dict
            contact = {
                'email': email,
                'name': name,
                'company': company,
                'website': website,
                'linkedin_url': linkedin_url,
                'title': title
            }
            
            contacts.append(contact)
    
    logger.info(f"Loaded {len(contacts)} valid contacts from CSV")
    if skipped > 0:
        logger.warning(f"Skipped {skipped} invalid rows")
    
    return contacts


def preview_csv_columns(csv_file: str) -> Dict:
    """
    Preview CSV file structure without loading all data.
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        dict: Information about CSV structure
    """
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Read first row as sample
        first_row = next(reader, None)
    
    # Detect columns
    email_col = find_column(headers, EMAIL_COLUMNS)
    name_col = find_column(headers, NAME_COLUMNS)
    company_col = find_column(headers, COMPANY_COLUMNS)
    website_col = find_column(headers, WEBSITE_COLUMNS)
    linkedin_col = find_column(headers, LINKEDIN_COLUMNS)
    title_col = find_column(headers, TITLE_COLUMNS)
    
    return {
        'total_columns': len(headers),
        'all_columns': headers,
        'detected_columns': {
            'email': email_col,
            'name': name_col,
            'company': company_col,
            'website': website_col,
            'linkedin': linkedin_col,
            'title': title_col
        },
        'sample_row': dict(first_row) if first_row else None,
        'required_columns_found': bool(email_col and name_col and company_col and website_col)
    }


def validate_csv_structure(csv_file: str) -> bool:
    """
    Validate that CSV has all required columns.
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        bool: True if CSV is valid
        
    Raises:
        ValueError: If required columns are missing
    """
    info = preview_csv_columns(csv_file)
    
    detected = info['detected_columns']
    
    missing = []
    if not detected['email']:
        missing.append('Email')
    if not detected['name']:
        missing.append('Name')
    if not detected['company']:
        missing.append('Company')
    if not detected['website']:
        missing.append('Website')
    
    if missing:
        raise ValueError(
            f"CSV is missing required columns: {', '.join(missing)}\n"
            f"Available columns: {', '.join(info['all_columns'])}"
        )
    
    return True
