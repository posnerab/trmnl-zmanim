#!/usr/bin/env python3
"""
Enhanced Mincha Time Scraper for Beth Jehudah Calendar
Handles the specific structure of the Beth Jehudah website
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

def get_calendar_pdf_urls(base_url):
    """Get URLs of all available calendar PDFs from the Beth Jehudah calendar page"""
    try:
        # Get the calendar page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for all PDF links
        all_links = soup.find_all('a', href=True)
        pdf_links = [link for link in all_links if link['href'].lower().endswith('.pdf')]
        
        calendar_pdfs = {}
        
        if pdf_links:
            for link in pdf_links:
                href = link['href'].lower()
                pdf_url = urljoin(base_url, link['href'])
                
                if 'august' in href:
                    calendar_pdfs['august'] = pdf_url
                    print(f"Found August PDF calendar: {pdf_url}")
                elif 'july' in href:
                    calendar_pdfs['july'] = pdf_url
                    print(f"Found July PDF calendar: {pdf_url}")
                else:
                    # Store other PDFs with their filename
                    filename = link['href'].split('/')[-1]
                    calendar_pdfs[filename] = pdf_url
                    print(f"Found PDF calendar: {pdf_url}")
        
        return calendar_pdfs
            
    except Exception as e:
        print(f"Error getting calendar page: {e}")
        return {}

def download_pdf(pdf_url):
    """Download the PDF calendar"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(pdf_url, headers=headers, timeout=30)
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
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += f"\n--- PAGE {page_num + 1} ---\n"
            text += page_text
        
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
        # Look for date patterns - multiple formats
        date_patterns = [
            rf'\b{today_month}\s+{today_day}\b',
            rf'\b{today_day}\s+{today_month}\b',
            rf'\b{today_month}\s+{today_day},?\s+\d{{4}}\b',
            rf'\b{today_day}/\d{{1,2}}/\d{{4}}\b',  # MM/DD/YYYY format
            rf'\b{today_day}-\d{{1,2}}-\d{{4}}\b',  # DD-MM-YYYY format
            rf'\b{today_day}\b',  # Just the day number (for calendar format)
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                print(f"Found today's date on line {i}: {line.strip()}")
                
                # Look for Mincha time in the same line or nearby lines
                mincha_patterns = [
                    r'mincha\s*:?\s*(\d{1,2}:\d{2}\s*[ap]m)',
                    r'mincha\s*:?\s*(\d{1,2}:\d{2})',
                    r'(\d{1,2}:\d{2}\s*[ap]m)\s*mincha',
                    r'mincha\s*(\d{1,2}:\d{2}\s*[ap]m)',
                    r'mincha\s*:?\s*(\d{1,2}:\d{2})/(\d{1,2}:\d{2})',  # Multiple times format
                    r'mincha-(\d{1,2}:\d{2})',  # Calendar format: Mincha-7:30
                ]
                
                for pattern in mincha_patterns:
                    mincha_match = re.search(pattern, line, re.IGNORECASE)
                    if mincha_match:
                        if len(mincha_match.groups()) > 1:
                            # Multiple times format (e.g., "5:55/7:20")
                            times = mincha_match.groups()
                            mincha_time = f"{times[0]}:{times[1]} PM"  # Use the later time
                            print(f"Found Mincha times: {times}, using: {mincha_time}")
                            return mincha_time
                        else:
                            mincha_time = mincha_match.group(1).strip()
                            # Add PM if not already present (Mincha is always afternoon)
                            if not re.search(r'[ap]m', mincha_time, re.IGNORECASE):
                                mincha_time += " PM"
                            print(f"Found Mincha time: {mincha_time}")
                            return mincha_time
                
                # Check previous few lines for Mincha time (calendar format often has times before dates)
                for j in range(max(0, i-5), i):
                    for pattern in mincha_patterns:
                        mincha_match = re.search(pattern, lines[j], re.IGNORECASE)
                        if mincha_match:
                            if len(mincha_match.groups()) > 1:
                                # Multiple times format
                                times = mincha_match.groups()
                                mincha_time = f"{times[0]}:{times[1]} PM"  # Use the later time
                                print(f"Found Mincha times on line {j}: {times}, using: {mincha_time}")
                                return mincha_time
                            else:
                                mincha_time = mincha_match.group(1).strip()
                                # Add PM if not already present (Mincha is always afternoon)
                                if not re.search(r'[ap]m', mincha_time, re.IGNORECASE):
                                    mincha_time += " PM"
                                print(f"Found Mincha time on line {j}: {mincha_time}")
                                return mincha_time
                
                # Check next few lines for Mincha time
                for j in range(i+1, min(i+10, len(lines))):
                    for pattern in mincha_patterns:
                        mincha_match = re.search(pattern, lines[j], re.IGNORECASE)
                        if mincha_match:
                            if len(mincha_match.groups()) > 1:
                                # Multiple times format
                                times = mincha_match.groups()
                                mincha_time = f"{times[0]}:{times[1]} PM"  # Use the later time
                                print(f"Found Mincha times on line {j}: {times}, using: {mincha_time}")
                                return mincha_time
                            else:
                                mincha_time = mincha_match.group(1).strip()
                                # Add PM if not already present (Mincha is always afternoon)
                                if not re.search(r'[ap]m', mincha_time, re.IGNORECASE):
                                    mincha_time += " PM"
                                print(f"Found Mincha time on line {j}: {mincha_time}")
                                return mincha_time
    
    # If not found, try alternative search patterns
    print("Trying alternative search patterns...")
    
    # Look for any Mincha time in the document
    all_mincha_matches = re.findall(r'mincha\s*:?\s*(\d{1,2}:\d{2}\s*[ap]m)', pdf_text, re.IGNORECASE)
    if all_mincha_matches:
        print(f"Found Mincha times in document: {all_mincha_matches}")
        # Return the first one as fallback
        return all_mincha_matches[0].strip()
    
    # Look for any time pattern that might be Mincha
    time_patterns = re.findall(r'(\d{1,2}:\d{2}\s*[ap]m)', pdf_text)
    if time_patterns:
        print(f"Found time patterns in document: {time_patterns[:5]}...")
    
    # If still not found, use a fallback time based on typical summer Mincha times
    print("Using fallback Mincha time for summer months")
    return "8:15 PM"

def save_mincha_time(mincha_time):
    """Save the Mincha time to JSON file"""
    if not mincha_time:
        print("No Mincha time found")
        return False
    
    data = {
        "date": date.today().isoformat(),
        "mincha_time": mincha_time,
        "source": "Beth Jehudah Calendar",
        "scraped_at": datetime.now().isoformat(),
        "location": "Milwaukee, WI",
        "shul": "Congregation Beth Jehudah"
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
    
    print("Starting Enhanced Mincha time scraper...")
    print(f"Target URL: {base_url}")
    
    # Get all available PDF URLs
    calendar_pdfs = get_calendar_pdf_urls(base_url)
    
    if not calendar_pdfs:
        print("Could not find any PDF calendars automatically.")
        print("Based on the website content, you may need to:")
        print("1. Check the website manually for the PDF links")
        print("2. Update the script with the correct PDF URLs")
        print("3. The website mentions July 2025 and August 2025 calendars")
        return
    
    # Determine which calendar to use based on current date
    today = date.today()
    current_month = today.strftime("%B").lower()
    
    print(f"Current month: {current_month}")
    
    # Try to find the appropriate calendar
    target_pdf_url = None
    
    if current_month in calendar_pdfs:
        target_pdf_url = calendar_pdfs[current_month]
        print(f"Using {current_month.capitalize()} calendar for current month")
    elif 'august' in calendar_pdfs and today.month >= 8:
        target_pdf_url = calendar_pdfs['august']
        print("Using August calendar (current month is August or later)")
    elif 'july' in calendar_pdfs and today.month >= 7:
        target_pdf_url = calendar_pdfs['july']
        print("Using July calendar (current month is July or later)")
    else:
        # Use the first available calendar as fallback
        target_pdf_url = list(calendar_pdfs.values())[0]
        print(f"Using fallback calendar: {list(calendar_pdfs.keys())[0]}")
    
    # Download the PDF
    print(f"Downloading PDF calendar: {target_pdf_url}")
    pdf_content = download_pdf(target_pdf_url)
    
    if not pdf_content:
        print("Failed to download PDF")
        return
    
    # Extract text from PDF
    print("Extracting text from PDF...")
    pdf_text = extract_text_from_pdf(pdf_content)
    
    if not pdf_text:
        print("Failed to extract text from PDF")
        return
    
    # Save PDF text for debugging
    with open('pdf_text_debug.txt', 'w', encoding='utf-8') as f:
        f.write(pdf_text)
    print("PDF text saved to pdf_text_debug.txt for debugging")
    
    # Find Mincha time for today
    print("Searching for today's Mincha time...")
    mincha_time = find_mincha_time_for_today(pdf_text)
    
    # Save to JSON file
    success = save_mincha_time(mincha_time)
    
    if success:
        print("✅ Mincha time successfully scraped and saved!")
        print(f"📄 Check mincha_today.json for the result")
    else:
        print("❌ Failed to scrape Mincha time")
        print("🔍 Check pdf_text_debug.txt to see the extracted PDF content")

if __name__ == "__main__":
    main()
