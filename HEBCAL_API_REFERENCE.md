# Hebcal API Reference

## 1. Hebcal Calendar API (Hebrew Date & Events)

### Endpoint
```
https://www.hebcal.com/hebcal
```

### Request Parameters
```python
params = {
    'v': '1',              # API version
    'cfg': 'json',         # Output format (json)
    'zip': '53216',        # ZIP code for location
    'start': '2025-10-19', # Start date (YYYY-MM-DD)
    'end': '2025-10-19',   # End date (YYYY-MM-DD)
    'maj': 'on',           # Major holidays
    'min': 'on',           # Minor holidays
    'mod': 'on',           # Modern holidays
    'nx': 'on',            # Rosh Chodesh
    'mf': 'on',            # Minor fasts
    'ss': 'on',            # Special Shabbatot
    's': 'on',             # Parashat hashavua
    'd': 'on',             # Hebrew date
    'c': 'on',             # Candle lighting
    'M': 'on',             # Havdalah
    'lg': 'a'              # Language (a=Ashkenazi transliterations)
}
```

### Response Format
```json
{
    "title": "Hebcal Milwaukee October 2025",
    "date": "2025-10-19T19:16:06.798Z",
    "version": "5.10.1-3.4.6",
    "location": {
        "title": "Milwaukee, WI 53216",
        "city": "Milwaukee",
        "tzid": "America/Chicago",
        "latitude": 43.088013,
        "longitude": -87.977046,
        "cc": "US",
        "country": "United States",
        "elevation": 680,
        "admin1": "WI",
        "geo": "zip",
        "zip": "53216",
        "state": "WI",
        "stateName": "Wisconsin"
    },
    "range": {
        "start": "2025-10-19",
        "end": "2025-10-19"
    },
    "items": [
        {
            "title": "27th of Tishrei",
            "date": "2025-10-19",
            "hdate": "27 Tishrei 5786",         // Hebrew date in readable format
            "category": "hebdate",               // Category type
            "title_orig": "27 Tishrei 5786",
            "hebrew": "כ״ז תשרי",               // Hebrew characters
            "heDateParts": {
                "y": "תשפ״ו",                   // Year
                "m": "תשרי",                     // Month
                "d": "כ״ז"                       // Day
            }
        }
        // Additional items for holidays, parashat, candle lighting, etc.
    ]
}
```

### Categories Found in Items
- `hebdate` - Hebrew date for each day
- `parashat` - Torah portion for Shabbat
- `candles` - Candle lighting time (Friday)
- `havdalah` - Havdalah time (Saturday evening)
- `holiday` - Jewish holidays
- `roshchodesh` - Beginning of Hebrew month
- `fast` - Fast days

### What the Code Extracts
```python
# From items array:
for item in data.get('items', []):
    if item.get('category') == 'hebdate':
        hdate = item.get('hdate')  # e.g., "27 Tishrei 5786"
    elif item.get('category') in ['parashat', 'candles']:
        parasha = item.get('memo')  # Torah portion info
```

---

## 2. Hebcal Leyning API (Torah Portion/Parasha)

### Endpoint
```
https://www.hebcal.com/leyning
```

### Request Parameters
```python
params = {
    'cfg': 'json',         # Output format (json)
    'start': '2025-10-19', # Start date (YYYY-MM-DD)
    'end': '2025-10-25'    # End date (YYYY-MM-DD)
}
```

### Response Format
```json
{
    "date": "2025-10-19T19:34:18.858Z",
    "location": "Diaspora",
    "range": {
        "start": "2025-10-19",
        "end": "2025-10-25"
    },
    "items": [
        {
            "date": "2025-10-25",
            "hdate": "3 Cheshvan 5786",
            "name": {
                "en": "Noach",           // English name
                "he": "נֹחַ"             // Hebrew name
            },
            "type": "shabbat",
            "parshaNum": 2,
            "summary": "Genesis 6:9-11:32",
            "fullkriyah": { ... },       // Full Torah reading breakdown
            "haftara": "Isaiah 54:1-55:5"
        }
    ]
}
```

### What the Code Extracts
```python
# From items array, find Saturday reading:
for item in data.get('items', []):
    item_date = datetime.strptime(item.get('date'), '%Y-%m-%d').date()
    if item_date.weekday() == 5:  # Saturday
        parasha_name = item.get('name', {}).get('en')  # e.g., "Noach"
```

### Update Schedule
- **Automatic**: Every Sunday at 12:01 AM CT via cron job
- **Manual**: Visit `/update-parasha` endpoint
- **Storage**: Saved to `/var/lib/homebridge/zmanim-js/parasha.json`

---

## 3. Hebcal Zmanim API (Prayer/Halachic Times)

### Data Source
Currently loaded from file: `/var/lib/homebridge/zmanim-js/hebcal_zmanim.json`

### Structure
```json
{
    "date": "2025-10-19",
    "version": "5.10.1-3.4.6",
    "location": {
        "title": "Milwaukee, WI 53216",
        "city": "Milwaukee",
        "tzid": "America/Chicago",
        "latitude": 43.088013,
        "longitude": -87.977046,
        "cc": "US",
        "country": "United States",
        "admin1": "WI",
        "geo": "zip",
        "zip": "53216",
        "state": "WI",
        "stateName": "Wisconsin"
    },
    "times": {
        "chatzotNight": "2025-10-19T00:37:00-05:00",        // Midnight
        "alotHaShachar": "2025-10-19T05:46:00-05:00",       // Dawn
        "misheyakir": "2025-10-19T06:12:00-05:00",          // Earliest tallit/tefillin
        "misheyakirMachmir": "2025-10-19T06:19:00-05:00",   // Stringent misheyakir
        "dawn": "2025-10-19T06:42:00-05:00",                // Civil dawn
        "sunrise": "2025-10-19T07:11:00-05:00",             // Sunrise (netz)
        
        // Shema times (latest time to recite Shema)
        "sofZmanShmaMGA19Point8": "2025-10-19T09:01:00-05:00",
        "sofZmanShmaMGA16Point1": "2025-10-19T09:11:00-05:00",
        "sofZmanShmaMGA": "2025-10-19T09:18:00-05:00",      // MGA opinion
        "sofZmanShma": "2025-10-19T09:54:00-05:00",         // Gra opinion
        
        // Tefilla/Amidah times (latest time for morning prayers)
        "sofZmanTfillaMGA19Point8": "2025-10-19T10:13:00-05:00",
        "sofZmanTfillaMGA16Point1": "2025-10-19T10:20:00-05:00",
        "sofZmanTfillaMGA": "2025-10-19T10:24:00-05:00",    // MGA opinion
        "sofZmanTfilla": "2025-10-19T10:48:00-05:00",       // Gra opinion
        
        "chatzot": "2025-10-19T12:36:00-05:00",             // Solar noon/midday
        
        // Afternoon prayer times
        "minchaGedola": "2025-10-19T13:04:00-05:00",        // Earliest Mincha
        "minchaGedolaMGA": "2025-10-19T13:10:00-05:00",     // MGA opinion
        "minchaKetana": "2025-10-19T15:46:00-05:00",        // Preferred Mincha time
        "minchaKetanaMGA": "2025-10-19T16:28:00-05:00",     // MGA opinion
        "plagHaMincha": "2025-10-19T16:54:00-05:00",        // Plag HaMincha
        
        "sunset": "2025-10-19T18:02:00-05:00",              // Shkiah
        "beinHaShmashos": "2025-10-19T18:23:00-05:00",      // Between sunset and darkness
        "dusk": "2025-10-19T18:31:00-05:00",                // Civil dusk
        
        // Evening (nightfall) times
        "tzeit7083deg": "2025-10-19T18:37:00-05:00",        // 7.083° below horizon
        "tzeit85deg": "2025-10-19T18:45:00-05:00",          // 8.5° below horizon
        "tzeit42min": "2025-10-19T18:44:00-05:00",          // 42 minutes after sunset
        "tzeit50min": "2025-10-19T18:52:00-05:00",          // 50 minutes after sunset
        "tzeit72min": "2025-10-19T19:14:00-05:00"           // 72 minutes after sunset (R' Tam)
    }
}
```

### Key Times Used in Application

**Morning (Shacharis):**
- `sofZmanShmaMGA` - Latest Shema (MGA)
- `sofZmanShma` - Latest Shema (Gra)
- `sofZmanTfilla` - Latest Tefilla (Gra)
- `chatzot` - Midday (Chatzos)

**Afternoon (Mincha):**
- `minchaKetana` - **Preferred Mincha time** (replaces plagHaMincha)
- `sunset` - Shkiah

**Shabbos Afternoon (Special):**
- `minchaKetana` - Mincha Ketana
- `sunset` - Shkiah
- Calculated: Maariv = sunset + 60 minutes
- `tzeit72min` - Havdalah (72 min after sunset)

**Friday (Erev Shabbos):**
- Calculated: Candle Lighting = sunset - 18 minutes
- `sunset` - Shkiah

**Evening (Maariv):**
- `tzeit72min` - Tzeis (72 minutes after sunset)
- `chatzotNight` - Midnight

**Saturday Evening (Motzei Shabbos):**
- `tzeit72min` - Havdalah time
- `chatzotNight` - Latest Melaveh Malkah

### Time Format
All times are in ISO 8601 format with timezone:
```
"2025-10-19T18:02:00-05:00"
```

Parsed in Python using:
```python
datetime.fromisoformat(time_str.replace('Z', '+00:00'))
```

Displayed as:
```python
time_obj.strftime("%-I:%M %p")  # e.g., "6:02 PM" (no leading zero)
```

---

## Custom Calculations

### Candle Lighting (Fridays)
```python
candle_lighting = sunset - timedelta(minutes=18)
```

### Maariv (Saturday/Shabbos)
```python
maariv_time = sunset + timedelta(minutes=60)
```

### Havdalah
Uses `tzeit72min` from zmanim data (sunset + 72 minutes)

---

## API Endpoints in Application

### `/api/zmanim` (Primary Endpoint)
**The single source of truth for all zmanim data.**

Returns current period with relevant times, Hebrew date, and weekly parasha:
```json
{
    "period": "Afternoon",
    "current_time": "2:46 PM",
    "date": "October 19, 2025",
    "hdate": "27 Tishrei 5786",
    "parasha": "Noach",
    "times": [
        ["Mincha Ketana", "3:46 PM"],
        ["Sunset", "6:02 PM"]
    ],
    "location": "Milwaukee, WI 53216"
}
```

All HTML templates retrieve their data from this endpoint.

### `/update-parasha`
Manual endpoint to trigger parasha update (fetches from Hebcal Leyning API):
```json
{
    "parasha": "Noach",
    "shabbat_date": "2025-10-25",
    "updated": "2025-10-19T14:36:32.153726-05:00"
}
```

---

## HTML Display Endpoints

All HTML endpoints use data from `/api/zmanim` and display it in different layouts:

### `/html`
Full-screen display with all times for the current period in a 2-column grid.
- **Header**: Date (left) | Period with icon (center) | Hebrew date (right)
- **Subheader**: Current time and location
- **Content**: All zmanim for current period (2-column grid)

### `/quadrant`
Compact quadrant display showing only the next upcoming time.
- **Header**: Date (left) | Period with icon (center) | Hebrew date (right)
- **Content**: Next single time with large text

### `/hebcal`
Hebrew calendar information display.
- Shows Hebrew date and Parasha in separate cards
- Full-screen layout

### Additional Template Files

The following templates are available for TRMNL polling (Liquid format):
- `trmnl_markup_half_horizontal.html` - Half-screen horizontal layout
- `trmnl_markup_all.html` - Alternative full layout
- `trmnl_markup_hebcal_date.html` - Hebrew date only
- `trmnl_markup_hebcal_parasha.html` - Parasha only

