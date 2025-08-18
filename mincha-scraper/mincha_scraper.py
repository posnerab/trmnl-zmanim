#!/usr/bin/env python3
"""
Mincha Time Scraper for Beth Jehudah Calendar
Scrapes the latest calendar PDF and extracts today's Mincha time
"""

import requests
import json
import re
import PyPDF2
import io
from datetime import datetime, date
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import os

def get_calendar_pdf_url(base_url):
    """Get the URL of the latest calendar PDF from the Beth Jehudah calendar page"""
    try:
        # Get the calendar page
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for PDF links - they mention July 2025 and August 2025 calendars
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        if pdf_links:
            # Get the first PDF link (latest calendar)
            pdf_url = urljoin(base_url, pdf_links[0]['href'])
            print(f"Found PDF calendar: {pdf_url}")
            return pdf_url
        else:
            # If no direct PDF links, look for text that mentions calendar files
            calendar_text = soup.find_all(text=re.compile(r'calendar', re.IGNORECASE))
            print(f"Calendar references found: {len(calendar_text)}")
            # For now, we'll need to manually specify the PDF URL
            return None
            
    except Exception as e:
        print(f"Error getting calendar page: {e}")
        return None

def download_pdf(pdf_url):
    """Download the PDF calendar"""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return None

def extract_text_from_pdf(pdf_content):
    """Extract text from PDF content"""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def find_mincha_time_for_today(pdf_text):
    """Find today's Mincha time from the PDF text"""
    if not pdf_text:
        return None
    
    today = date.today()
    today_str = today.strftime("%B %d")  # e.g., "February 14"
    today_day = today.day
    today_month = today.strftime("%B")
    
    print(f"Looking for Mincha time for: {today_str}")
    
    # Split text into lines for easier parsing
    lines = pdf_text.split('\n')
    
    # Look for today's date and Mincha time
    for i, line in enumerate(lines):
        # Look for date patterns
        if re.search(rf'\b{today_month}\s+{today_day}\b', line, re.IGNORECASE):
            print(f"Found today's date on line: {line}")
            
            # Look for Mincha time in the same line or nearby lines
            mincha_pattern = r'mincha\s*:?\s*(\d{1,2}:\d{2}\s*[ap]m)'
            mincha_match = re.search(mincha_pattern, line, re.IGNORECASE)
            
            if mincha_match:
                mincha_time = mincha_match.group(1).strip()
                print(f"Found Mincha time: {mincha_time}")
                return mincha_time
            
            # Check next few lines for Mincha time
            for j in range(i+1, min(i+5, len(lines))):
                mincha_match = re.search(mincha_pattern, lines[j], re.IGNORECASE)
                if mincha_match:
                    mincha_time = mincha_match.group(1).strip()
                    print(f"Found Mincha time on line {j}: {mincha_time}")
                    return mincha_time
    
    # If not found, try alternative patterns
    print("Trying alternative search patterns...")
    
    # Look for any Mincha time in the document
    all_mincha_matches = re.findall(r'mincha\s*:?\s*(\d{1,2}:\d{2}\s*[ap]m)', pdf_text, re.IGNORECASE)
    if all_mincha_matches:
        print(f"Found Mincha times in document: {all_mincha_matches}")
        # Return the first one as fallback
        return all_mincha_matches[0].strip()
    
    return None

def save_mincha_time(mincha_time):
    """Save the Mincha time to JSON file"""
    if not mincha_time:
        print("No Mincha time found")
        return False
    
    data = {
        "date": date.today().isoformat(),
        "mincha_time": mincha_time,
        "source": "Beth Jehudah Calendar",
        "scraped_at": datetime.now().isoformat()
    }
    
    try:
        with open('mincha_today.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Mincha time saved to mincha_today.json: {mincha_time}")
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False

def main():
    """Main function to scrape Mincha time"""
    base_url = "https://bethjehudah.org/calendar/"
    
    print("Starting Mincha time scraper...")
    print(f"Target URL: {base_url}")
    
    # Get the PDF URL
    pdf_url = get_calendar_pdf_url(base_url)
    
    if not pdf_url:
        print("Could not find PDF URL automatically.")
        print("You may need to manually specify the PDF URL.")
        print("Please check the website and update the script with the correct PDF URL.")
        return
    
    # Download the PDF
    print("Downloading PDF calendar...")
    pdf_content = download_pdf(pdf_url)
    
    if not pdf_content:
        print("Failed to download PDF")
        return
    
    # Extract text from PDF
    print("Extracting text from PDF...")
    pdf_text = extract_text_from_pdf(pdf_content)
    
    if not pdf_text:
        print("Failed to extract text from PDF")
        return
    
    # Find Mincha time for today
    print("Searching for today's Mincha time...")
    mincha_time = find_mincha_time_for_today(pdf_text)
    
    # Save to JSON file
    success = save_mincha_time(mincha_time)
    
    if success:
        print("✅ Mincha time successfully scraped and saved!")
    else:
        print("❌ Failed to scrape Mincha time")

if __name__ == "__main__":
    main()
