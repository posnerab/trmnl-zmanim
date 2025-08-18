#!/bin/bash

# Mincha Time Scraper Runner
# Runs the Python script to scrape today's Mincha time from Beth Jehudah calendar

cd /var/www/trmnl-zmanim/mincha_scraper

echo "Starting Mincha time scraper at $(date)"

# Run the Python scraper
python3 mincha_scraper_enhanced.py

# Check if the script was successful
if [ -f "mincha_today.json" ]; then
    echo "✅ Mincha time successfully scraped!"
    echo "📄 Current Mincha time:"
    cat mincha_today.json
else
    echo "❌ Failed to scrape Mincha time"
    exit 1
fi

echo "Mincha scraper completed at $(date)"
