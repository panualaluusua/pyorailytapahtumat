import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os
import json

def scrape_bikeland_events():
    """
    Scrape events from Bikeland.fi and save them to a JSON file.
    Returns the number of new events found.
    """
    print("Scraping events from Bikeland.fi...")
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Load existing events if available
    existing_events = []
    if os.path.exists('data/bikeland_events.json'):
        try:
            with open('data/bikeland_events.json', 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
            print(f"Loaded {len(existing_events)} existing events")
        except Exception as e:
            print(f"Error loading existing events: {e}")
    
    # Create a set of existing event identifiers (title + date) for quick comparison
    existing_event_ids = {f"{event['title']}_{event['datetime'].split()[0]}" 
                         for event in existing_events if 'title' in event and 'datetime' in event}
    
    # Fetch the Bikeland.fi website
    url = "https://www.bikeland.fi/tapahtumat"
    print(f"Fetching URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save the HTML content for debugging
        with open('data/bikeland_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"Saved response HTML to data/bikeland_response.html")
        
    except Exception as e:
        print(f"Error fetching the website: {e}")
        return 0
    
    new_events = []
    
    # Try to extract the JSON objects from the <script> tags
    # We look for "var upcoming_eventdata = {...};" and "var past_eventdata = {...};"
    import re
    import json
    
    combined_data = {}
    
    for var_name in ['upcoming_eventdata', 'past_eventdata']:
        pattern = f'var {var_name} = ({{.*?}});'
        match = re.search(pattern, response.text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                combined_data.update(data)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON for {var_name}: {e}")
                
    if not combined_data:
        print("Could not find any event data in the expected format.")
        return 0

    # Function to clean HTML from text
    def clean_html(raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', str(raw_html))
        return cleantext.strip()

    # Function to convert Finnish date format to ISO format
    def convert_date_to_iso(date_str):
        # Extracts the first date like '03.07.2026' and converts to '2026-07-03'
        match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', date_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)} 08:00"
        return None

    for event_id, event_info in combined_data.items():
        title = event_info.get('title', 'Unknown Title')
        ingress = clean_html(event_info.get('ingress', ''))
        url = event_info.get('url', '')
        
        categories = event_info.get('categories', [])
        # Provide better formatting for categories
        type_str = ", ".join(categories).upper() if categories else "Unknown"
        
        dates_obj = event_info.get('dates', {})
        # dates_obj looks like: {"2026-07": ["03.07.2026<span class=\"date-separator\">-</span>04.07.2026 | Saariselkä"]}
        date_text = ""
        location = "Unknown Location"
        for month_key, items in dates_obj.items():
            if items:
                date_text = clean_html(items[0]).replace('-', ' - ') # e.g. "03.07.2026 - 04.07.2026 | Saariselkä"
                break
                
        datetime_str = convert_date_to_iso(date_text)
        if not datetime_str:
            continue
            
        if '|' in date_text:
            location = date_text.split('|', 1)[1].strip()
        
        event = {
            'title': title,
            'type': type_str,
            'datetime': datetime_str,
            'location': location,
            'description': ingress,
            'link': url,
            'source': 'bikeland'
        }
        
        # Check against existing to avoid duplicates
        existing_id = f"{title}_{datetime_str.split()[0]}"
        if existing_id not in existing_event_ids:
            new_events.append(event)
            existing_event_ids.add(existing_id)
            print(f"Added new event: {title} ({type_str}) on {datetime_str} at {location}")
        else:
            print(f"Event already exists: {title} on {datetime_str}")
            
    # Combine existing and new events
    all_events = existing_events + new_events
    
    # Save all events to JSON file
    with open('data/bikeland_events.json', 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    
    print(f"\nFound {len(new_events)} new events")
    print(f"Total events: {len(all_events)}")
    print("Events saved to data/bikeland_events.json")
    
    return len(new_events)

if __name__ == "__main__":
    new_events_count = scrape_bikeland_events()
    print(f"Scraping complete. Found {new_events_count} new events.") 