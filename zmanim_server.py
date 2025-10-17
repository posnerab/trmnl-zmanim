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

app = Flask(__name__)

# Load zmanim data
ZMANIM_FILE = '/var/lib/homebridge/zmanim-js/hebcal_zmanim.json'

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

def get_next_time_only(zmanim_data):
    """Get only the next upcoming time"""
    if not zmanim_data:
        return {"error": "No zmanim data available"}
    
    now = datetime.now(pytz.timezone('America/Chicago'))
    today = now.date()
    
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
    if time_objects.get('plagHaMincha'):
        all_times.append(("Plag HaMincha", time_objects.get('plagHaMincha')))
    
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
        period = "Morning"
    elif now >= chatzot and now < sunset:
        if today.weekday() == 4:
            period = "Erev Shabbos"
        else:
            period = "Afternoon"
    elif now >= sunset or (sunrise and now < sunrise):
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
        "date": today.strftime("%B %d, %Y"),
        "times": formatted_times,
        "location": zmanim_data.get('location', {}).get('title', 'Unknown Location')
    }

def get_current_period(zmanim_data):
    """Determine current period and relevant times"""
    if not zmanim_data:
        return {"error": "No zmanim data available"}
    
    now = datetime.now(pytz.timezone('America/Chicago'))
    today = now.date()
    
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
        if today.weekday() == 4:  # Friday (0=Monday, 4=Friday)
            period = "Erev Shabbos"
        else:
            period = "Afternoon"
        
        relevant_times = {}
        
        # Add Plag HaMincha
        plag = time_objects.get('plagHaMincha')
        if plag:
            relevant_times["Plag HaMincha"] = plag.strftime("%-I:%M %p")
        
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
        "date": today.strftime("%B %d, %Y"),
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
    data = get_next_time_only(load_zmanim_data())
    return render_template('trmnl_markup_quadrant.html', **data)



if __name__ == '__main__':
    print("Starting Zmanim Tracker Server...")
    print("API available at: https://abie.live/zmanim/api/zmanim")
    app.run(host='0.0.0.0', port=5001, debug=True)
