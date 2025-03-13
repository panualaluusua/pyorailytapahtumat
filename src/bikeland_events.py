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
    
    # List of known events from the website
    known_events = [
        "Tour De Tuusulanjärvi",
        "Gravel Primavera I Nordic Gravel Series",
        "Koli Gravel Carnival",
        "Lohjanjärven ympäripyöräily",
        "Tour De Koivujärven ympäripyöräily",
        "Midnight Sun Gravel",
        "Pirkan pyöräily",
        "Tahko MTB",
        "Tour de Kainuu",
        "Nordic Gravel Series Jyväskylä",
        "Saimaa Cycle Tour",
        "Kitka MTB",
        "Kaldoaivi Ultra Road",
        "Kaldoaivi Ultra MTB",
        "Syöte MTB",
        "Dirty Sipoo x NGS",
        "Puss Weekend",
        "Luonterin pyöräily",
        "FNLD GRVL",
        "Sorahiisi",
        "Saariselkä MTB Stages",
        "Falling Leaves Lahti"
    ]
    
    # Finnish month names to numbers mapping
    finnish_months = {
        'tammi': '01', 'tammi.': '01',
        'helmik': '02', 'helmik.': '02',
        'maalis': '03', 'maalis.': '03',
        'huhti': '04', 'huhti.': '04',
        'touko': '05', 'touko.': '05',
        'kesä': '06', 'kesä.': '06', 'kesäk': '06', 'kesäk.': '06',
        'heinä': '07', 'heinä.': '07', 'heinäk': '07', 'heinäk.': '07',
        'elo': '08', 'elo.': '08', 'elok': '08', 'elok.': '08',
        'syys': '09', 'syys.': '09',
        'loka': '10', 'loka.': '10',
        'marras': '11', 'marras.': '11',
        'joulu': '12', 'joulu.': '12'
    }
    
    # Function to convert Finnish date format to ISO format
    def convert_date_to_iso(finnish_date):
        try:
            parts = finnish_date.split()
            if len(parts) != 3:
                return "Unknown Date"
            
            day = parts[0].replace('.', '').strip().zfill(2)
            month_name = parts[1].lower()
            year = parts[2].strip()
            
            month = None
            for key, value in finnish_months.items():
                if month_name.startswith(key):
                    month = value
                    break
            
            if not month:
                return "Unknown Date"
            
            return f"{year}-{month}-{day} 08:00"
        except Exception as e:
            print(f"Error converting date: {e}")
            return "Unknown Date"
    
    # List to store new events
    new_events = []
    
    # Process each known event
    for event_name in known_events:
        print(f"\nLooking for event: {event_name}")
        
        if event_name not in response.text:
            print(f"Event not found in HTML: {event_name}")
            continue
        
        try:
            # Get the section of HTML that contains the event
            event_start_index = response.text.find(event_name)
            event_section = response.text[event_start_index:event_start_index + 5000]
            
            # Extract event type
            event_type = "Unknown"
            type_pattern = r'class="wixui-rich-text__text"><span class="color_42 wixui-rich-text__text">(.*?)</span></span></p>'
            type_match = re.search(type_pattern, event_section)
            
            if type_match:
                event_type = type_match.group(1).strip()
            else:
                if 'MTB' in event_name:
                    event_type = "MTB"
                elif 'Gravel' in event_name or 'GRVL' in event_name:
                    event_type = "GRAVEL"
                elif 'Road' in event_name:
                    event_type = "MAANTIE"
            
            # Extract event location
            event_location = "Unknown Location"
            location_pattern = r'class="wixui-rich-text__text">([A-Za-z\-,\s]+)</span></span></p></div>'
            location_match = re.search(location_pattern, event_section)
            
            if location_match:
                event_location = location_match.group(1).strip()
            
            # Extract event date
            event_date = "Unknown Date"
            date_pattern = r'class="color_42 wixui-rich-text__text">(\d{1,2}\.\s+\w+\.\s+\d{4})</span>'
            date_match = re.search(date_pattern, event_section)
            
            if date_match:
                finnish_date = date_match.group(1).strip()
                event_date = convert_date_to_iso(finnish_date)
            else:
                date_pattern = r'(\d{1,2}\.\s+\w+\.\s+\d{4})'
                date_match = re.search(date_pattern, event_section)
                if date_match:
                    finnish_date = date_match.group(1).strip()
                    event_date = convert_date_to_iso(finnish_date)
            
            # Extract event description
            event_description = ""
            desc_pattern = r'<span class="color_25 wixui-rich-text__text">(.*?)</span></p></div>'
            desc_match = re.search(desc_pattern, event_section)
            
            if desc_match:
                event_description = desc_match.group(1).strip()
                if len(event_description) < 50 or event_name not in event_description:
                    desc_pattern2 = r'<p class="font_9 wixui-rich-text__text"[^>]*><span class="color_25 wixui-rich-text__text">(.*?)</span></p>'
                    desc_match2 = re.search(desc_pattern2, event_section)
                    if desc_match2:
                        event_description = desc_match2.group(1).strip()
            
            # Clean up the description - remove HTML tags
            if event_description:
                soup = BeautifulSoup(f"<p>{event_description}</p>", 'html.parser')
                event_description = soup.get_text()
            
            # Extract event link
            event_link = ""
            link_pattern = r'href="(https?://[^"]+)"'
            link_matches = re.findall(link_pattern, event_section)
            
            if link_matches:
                for link in link_matches:
                    if 'bikeland.fi' not in link and 'wix' not in link:
                        event_link = link
                        break
            
            # Create event object
            event = {
                'title': event_name,
                'type': event_type,
                'datetime': event_date,
                'location': event_location,
                'description': event_description,
                'link': event_link,
                'source': 'bikeland'
            }
            
            # Check if this is a new event
            event_id = f"{event_name}_{event_date.split()[0]}"
            if event_id not in existing_event_ids:
                new_events.append(event)
                existing_event_ids.add(event_id)
                print(f"Added new event: {event_name} ({event_type}) on {event_date} at {event_location}")
            else:
                print(f"Event already exists: {event_name} on {event_date}")
            
        except Exception as e:
            print(f"Error processing event {event_name}: {e}")
    
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