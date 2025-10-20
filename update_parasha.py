#!/usr/bin/env python3
"""
Script to update the weekly parasha
Run this every Sunday at 12:01 AM CT
"""

import sys
import os

# Add the parent directory to the path so we can import from zmanim_server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zmanim_server import fetch_weekly_parasha

if __name__ == '__main__':
    print("Updating weekly parasha...")
    result = fetch_weekly_parasha()
    if 'error' in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"Successfully updated parasha: {result.get('parasha')}")
        print(f"For Shabbat: {result.get('shabbat_date')}")
        sys.exit(0)

