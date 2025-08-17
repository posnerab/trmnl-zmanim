#!/usr/bin/env python3
"""
Zmanim (Jewish Halachic Times) Server for TRMNL Plugin
Displays prayer times based on time of day
"""

from flask import Flask, jsonify, render_template, request, abort
from datetime import datetime, date, time
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
    chatzot = time_objects.get('chatzot')
    sunset = time_objects.get('sunset')
    tzeit72min = time_objects.get('tzeit72min')
    
    if not chatzot or not sunset:
        return {"error": "Missing critical times"}
    
    # Determine period and relevant times
    if now < chatzot:
        # Before chatzot - show Shacharis times
        period = "Shacharis"
        relevant_times = {
            "Shema (MGA)": time_objects.get('sofZmanShmaMGA'),
            "Shema (GR'A)": time_objects.get('sofZmanShma'),
            "Tefilla (MGA)": time_objects.get('sofZmanTfillaMGA'),
            "Tefilla (GR'A)": time_objects.get('sofZmanTfilla'),
            "Chatzot": chatzot
        }
    elif now < sunset:
        # After chatzot, before sunset - show Mincha times
        period = "Mincha"
        relevant_times = {
            "Mincha Gedola": time_objects.get('minchaGedola'),
            "Mincha Ketana": time_objects.get('minchaKetana'),
            "Plag HaMincha": time_objects.get('plagHaMincha'),
            "Sunset": sunset
        }
    else:
        # After sunset - show nightfall and chatzot night
        period = "Evening"
        relevant_times = {
            "Tzeit (72 min)": tzeit72min,
            "Chatzot Night": time_objects.get('chatzotNight')
        }
    
    # Format times for display
    formatted_times = {}
    for name, time_obj in relevant_times.items():
        if time_obj:
            formatted_times[name] = time_obj.strftime("%I:%M %p")
    
    return {
        "period": period,
        "current_time": now.strftime("%I:%M %p"),
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
    return render_template('zmanim_display.html', **data)

if __name__ == '__main__':
    print("Starting Zmanim Tracker Server...")
    print("API available at: https://abie.live/zmanim/api/zmanim")
    app.run(host='0.0.0.0', port=5001, debug=True)
