#!/usr/bin/env python3
"""
Zmanim (Jewish Halachic Times) Server for TRMNL Plugin
Displays prayer times based on time of day
"""

from flask import Flask, jsonify, render_template, request, abort
from datetime import datetime, date, time, timedelta
import json
import os
import pytz
import requests

app = Flask(__name__)

# Load zmanim data
ZMANIM_FILE = '/var/lib/homebridge/zmanim-js/hebcal_zmanim.json'
PARASHA_FILE = '/var/lib/homebridge/zmanim-js/parasha.json'

# Hebcal API configuration
HEBCAL_API_BASE = 'https://www.hebcal.com/hebcal'
HEBCAL_LEYNING_API = 'https://www.hebcal.com/leyning'
HEBCAL_ZIP = '53216'

# API key authentication removed - endpoints are now public

def load_zmanim_data():
    """Load zmanim data from JSON file"""
    try:
        with open(ZMANIM_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {ZMANIM_FILE} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in {ZMANIM_FILE}")
        return None

def parse_time(time_str):
    """Parse ISO time string to datetime object"""
    try:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    except:
        return None

def load_parasha_data():
    """Load parasha data from JSON file"""
    try:
        with open(PARASHA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {PARASHA_FILE} not found.")
        return {'parasha': 'Unknown'}
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in {PARASHA_FILE}")
        return {'parasha': 'Unknown'}

def fetch_weekly_parasha():
    """Fetch weekly parasha from Hebcal Leyning API and save to file"""
    try:
        # Get the upcoming Saturday (or current if today is Saturday)
        now = datetime.now(pytz.timezone('America/Chicago'))
        days_ahead = 5 - now.weekday()  # Saturday is weekday 5
        if days_ahead < 0:
            days_ahead += 7
        
        # Get date range (today through next Saturday)
        start_date = now.date()
        end_date = (now + timedelta(days=days_ahead)).date()
        
        params = {
            'cfg': 'json',
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
        
        response = requests.get(HEBCAL_LEYNING_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Find the Shabbat reading (type=shabbat or weekday 6/Saturday)
        parasha_name = None
        for item in data.get('items', []):
            # Look for the Saturday/Shabbat reading
            item_date = datetime.strptime(item.get('date'), '%Y-%m-%d').date()
            if item_date.weekday() == 5:  # Saturday
                name_obj = item.get('name', {})
                if isinstance(name_obj, dict):
                    parasha_name = name_obj.get('en')
                break
        
        if not parasha_name:
            parasha_name = 'Unknown'
        
        # Save to file
        parasha_data = {
            'parasha': parasha_name,
            'updated': now.isoformat(),
            'shabbat_date': end_date.strftime('%Y-%m-%d')
        }
        
        with open(PARASHA_FILE, 'w') as f:
            json.dump(parasha_data, f, indent=2)
        
        print(f"Parasha updated: {parasha_name} for {end_date}")
        return parasha_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Leyning data: {e}")
        return {'parasha': 'Unknown', 'error': str(e)}
    except Exception as e:
        print(f"Error parsing Leyning data: {e}")
        return {'parasha': 'Unknown', 'error': str(e)}

def fetch_hebcal_data():
    """Fetch Hebrew calendar data from Hebcal API"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'v': '1',
            'cfg': 'json',
            'zip': HEBCAL_ZIP,
            'start': today,
            'end': today,
            'maj': 'on',
            'min': 'on',
            'mod': 'on',
            'nx': 'on',
            'mf': 'on',
            'ss': 'on',
            's': 'on',
            'd': 'on',
            'c': 'on',
            'M': 'on',
            'lg': 'a'
        }
        
        response = requests.get(HEBCAL_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract Hebrew date and parasha from items
        hdate = None
        parasha = None
        
        for item in data.get('items', []):
            if item.get('category') == 'hebdate':
                hdate = item.get('hdate')
            elif item.get('category') in ['parashat', 'candles']:
                # Parasha info is in the memo field
                memo = item.get('memo')
                if memo:
                    parasha = memo
        
        return {
            'hdate': hdate,
            'parasha': parasha,
            'location': data.get('location', {}).get('title', 'Unknown Location'),
            'date': today
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Hebcal data: {e}")
        return {
            'error': 'Failed to fetch Hebrew calendar data',
            'hdate': None,
            'parasha': None
        }
    except Exception as e:
        print(f"Error parsing Hebcal data: {e}")
        return {
            'error': 'Failed to parse Hebrew calendar data',
            'hdate': None,
            'parasha': None
        }

def get_next_time_only(zmanim_data):
    """Get only the next upcoming time"""
    if not zmanim_data:
        return {"error": "No zmanim data available"}
    
    now = datetime.now(pytz.timezone('America/Chicago'))
    today = now.date()
    
    # Fetch Hebrew calendar data
    hebcal_data = fetch_hebcal_data()
    
    # Load parasha data
    parasha_data = load_parasha_data()
    
    # Parse today's times
    times = zmanim_data.get('times', {})
    
    # Convert string times to datetime objects
    time_objects = {}
    for key, time_str in times.items():
        parsed_time = parse_time(time_str)
        if parsed_time:
            time_objects[key] = parsed_time
    
    # Get all relevant times throughout the day
    sunrise = time_objects.get('sunrise')
    chatzot = time_objects.get('chatzot')
    sunset = time_objects.get('sunset')
    tzeit72min = time_objects.get('tzeit72min')
    
    if not chatzot or not sunset:
        return {"error": "Missing critical times"}
    
    # Build list of all times with their names
    all_times = []
    
    # Morning times
    if time_objects.get('sofZmanShmaMGA'):
        all_times.append(("Shema (MGA)", time_objects.get('sofZmanShmaMGA')))
    if time_objects.get('sofZmanShma'):
        all_times.append(("Shema (Gra)", time_objects.get('sofZmanShma')))
    if time_objects.get('sofZmanTfilla'):
        all_times.append(("Tefilla (Gra)", time_objects.get('sofZmanTfilla')))
    if chatzot:
        all_times.append(("Chatzos", chatzot))
    
    # Afternoon times
    if time_objects.get('minchaKetana'):
        all_times.append(("Mincha Ketana", time_objects.get('minchaKetana')))
    
    # Friday candle lighting
    if today.weekday() == 4 and sunset:
        candle_lighting = sunset - timedelta(minutes=18)
        all_times.append(("Candle Lighting", candle_lighting))
    
    if sunset:
        all_times.append(("Sunset", sunset))
    
    # Evening times
    if tzeit72min:
        all_times.append(("Tzeis (72 min)", tzeit72min))
    if time_objects.get('chatzotNight'):
        all_times.append(("Chatzos Night", time_objects.get('chatzotNight')))
    
    # Filter to only future times and get the first one
    next_time = None
    next_time_name = None
    
    for name, time_obj in all_times:
        if time_obj and time_obj > now:
            next_time = time_obj
            next_time_name = name
            break
    
    # Determine period based on current time
    if sunrise and now >= sunrise and now < chatzot:
        if today.weekday() == 5:  # Saturday
            period = "Shabbos Morning"
        else:
            period = "Morning"
    elif now >= chatzot and now < sunset:
        if today.weekday() == 4:
            period = "Erev Shabbos"
        elif today.weekday() == 5:  # Saturday
            period = "Shabbos Afternoon"
        else:
            period = "Afternoon"
    elif now >= sunset or (sunrise and now < sunrise):
        if today.weekday() == 5:  # Saturday evening
            period = "Motzei Shabbos"
        else:
            period = "Evening"
    else:
        period = "Morning"
    
    # Format the next time
    formatted_times = []
    if next_time and next_time_name:
        formatted_times.append([next_time_name, next_time.strftime("%-I:%M %p")])
    
    return {
        "period": period,
        "current_time": now.strftime("%-I:%M %p"),
        "date": today.strftime("%a, %B ") + str(today.day) + today.strftime(", %Y"),
        "hdate": hebcal_data.get('hdate', 'Unknown'),
        "parasha": parasha_data.get('parasha', 'Unknown'),
        "times": formatted_times,
        "location": zmanim_data.get('location', {}).get('title', 'Unknown Location')
    }

def get_current_period(zmanim_data):
    """Determine current period and relevant times"""
    if not zmanim_data:
        return {"error": "No zmanim data available"}
    
    now = datetime.now(pytz.timezone('America/Chicago'))
    today = now.date()
    
    # Fetch Hebrew calendar data
    hebcal_data = fetch_hebcal_data()
    
    # Load parasha data
    parasha_data = load_parasha_data()
    
    # Parse today's times
    times = zmanim_data.get('times', {})
    
    # Convert string times to datetime objects
    time_objects = {}
    for key, time_str in times.items():
        parsed_time = parse_time(time_str)
        if parsed_time:
            time_objects[key] = parsed_time
    
    # Determine current period
    sunrise = time_objects.get('sunrise')
    chatzot = time_objects.get('chatzot')
    sunset = time_objects.get('sunset')
    tzeit72min = time_objects.get('tzeit72min')
    
    if not chatzot or not sunset:
        return {"error": "Missing critical times"}
    
    # Determine period and relevant times
    if sunrise and now >= sunrise and now < chatzot:
        # After sunrise, before chatzot - show Morning times
        # On Saturday, call it "Shabbos Morning"
        if today.weekday() == 5:  # Saturday (0=Monday, 5=Saturday)
            period = "Shabbos Morning"
        else:
            period = "Morning"
        relevant_times = {
            "Shema (MGA)": time_objects.get('sofZmanShmaMGA'),
            "Shema (Gra)": time_objects.get('sofZmanShma'),
            "Tefilla (Gra)": time_objects.get('sofZmanTfilla'),
            "Chatzos": chatzot
        }
    elif now >= chatzot and now < sunset:
        # After chatzot, before sunset - show Afternoon times
        # On Friday, call it "Erev Shabbos" instead of "Afternoon"
        # On Saturday, call it "Shabbos Afternoon"
        if today.weekday() == 4:  # Friday (0=Monday, 4=Friday)
            period = "Erev Shabbos"
        elif today.weekday() == 5:  # Saturday
            period = "Shabbos Afternoon"
        else:
            period = "Afternoon"
        
        relevant_times = {}
        
        # On Saturday (Shabbos Afternoon), show specific times in order
        if today.weekday() == 5:  # Saturday
            # Mincha Ketana
            mincha_ketana = time_objects.get('minchaKetana')
            if mincha_ketana:
                relevant_times["Mincha Ketana"] = mincha_ketana.strftime("%-I:%M %p")
            
            # Sunset
            if sunset:
                relevant_times["Sunset"] = sunset.strftime("%-I:%M %p")
            
            # Maariv (60 minutes after sunset)
            if sunset:
                maariv_time = sunset + timedelta(minutes=60)
                relevant_times["Maariv"] = maariv_time.strftime("%-I:%M %p")
            
            # Havdalah is same as tzeit72min (sunset + 72 minutes)
            if tzeit72min:
                relevant_times["Havdalah"] = tzeit72min.strftime("%-I:%M %p")
        else:
            # For other afternoons (including Friday), add Mincha Ketana
            mincha_ketana = time_objects.get('minchaKetana')
            if mincha_ketana:
                relevant_times["Mincha Ketana"] = mincha_ketana.strftime("%-I:%M %p")
            
            # On Fridays, add Candle Lighting (18 minutes before sunset)
            if today.weekday() == 4:  # Friday (0=Monday, 4=Friday)
                if sunset:
                    candle_lighting = sunset - timedelta(minutes=18)
                    relevant_times["Candle Lighting"] = candle_lighting.strftime("%-I:%M %p")
            
            # Add sunset time (formatted as 7:51 not 07:51)
            if sunset:
                relevant_times["Sunset"] = sunset.strftime("%-I:%M %p")
    elif now >= sunset or (sunrise and now < sunrise):
        # After sunset or before sunrise - show Evening times
        # On Saturday evening, call it "Motzei Shabbos"
        if today.weekday() == 5:  # Saturday evening
            period = "Motzei Shabbos"
            relevant_times = {
                "Havdalah": tzeit72min,  # Show as Havdalah instead of Tzeis
                "Latest Maleve Malka": time_objects.get('chatzotNight')  # Chatzos Night renamed
            }
        else:
            period = "Evening"
            relevant_times = {
                "Tzeis (72 min)": tzeit72min,
                "Chatzos Night": time_objects.get('chatzotNight')
            }
    else:
        # Fallback - show Shacharis times
        period = "Morning"
        relevant_times = {
            "Shema (MGA)": time_objects.get('sofZmanShmaMGA'),
            "Shema (Gra)": time_objects.get('sofZmanShma'),
            "Tefilla (Gra)": time_objects.get('sofZmanTfilla'),
            "Chatzos": chatzot
        }
    
    # Format times for display
    formatted_times = []
    for name, time_obj in relevant_times.items():
        if time_obj:
            if isinstance(time_obj, str):
                # Already formatted string
                formatted_times.append([name, time_obj])
            else:
                # Datetime object - format it
                formatted_times.append([name, time_obj.strftime("%-I:%M %p")])  # Remove leading zero
    
    return {
        "period": period,
        "current_time": now.strftime("%-I:%M %p"),  # Remove leading zero
        "date": today.strftime("%a, %B ") + str(today.day) + today.strftime(", %Y"),
        "hdate": hebcal_data.get('hdate', 'Unknown'),
        "parasha": parasha_data.get('parasha', 'Unknown'),
        "times": formatted_times,
        "location": zmanim_data.get('location', {}).get('title', 'Unknown Location')
    }

@app.route('/')
def home():
    """Home page with basic info"""
    return """
    <h1>Zmanim Tracker</h1>
    <p>Jewish Halachic Times Display</p>
    <p>API endpoint: <a href="/api/zmanim">/api/zmanim</a></p>
    """

@app.route('/api/zmanim')
def zmanim_api():
    """API endpoint that returns zmanim data as JSON"""
    data = get_current_period(load_zmanim_data())
    return jsonify(data)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/html')
def html_markup():
    """HTML markup endpoint for TRMNL"""
    data = get_current_period(load_zmanim_data())
    return render_template('zmanim_display_liquid.html', **data)

@app.route('/quadrant')
def quadrant_markup():
    """HTML markup endpoint for TRMNL quadrant view - shows only next time"""
    # Return raw Liquid template for TRMNL to process client-side
    template_path = os.path.join(app.template_folder, 'trmnl_markup_quadrant.html')
    with open(template_path, 'r') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/hebcal')
def hebcal_markup():
    """HTML markup endpoint for TRMNL - shows Hebrew date and Parasha"""
    # Return raw Liquid template for TRMNL to process client-side
    template_path = os.path.join(app.template_folder, 'trmnl_markup_hebcal.html')
    with open(template_path, 'r') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/update-parasha')
def update_parasha():
    """Manual endpoint to update the weekly parasha"""
    data = fetch_weekly_parasha()
    return jsonify(data)


if __name__ == '__main__':
    print("Starting Zmanim Tracker Server...")
    print("API available at: https://abie.live/zmanim/api/zmanim")
    app.run(host='0.0.0.0', port=5001, debug=True)
