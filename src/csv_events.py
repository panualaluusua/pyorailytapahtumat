import csv
import os
import re
from datetime import datetime
import json

def process_csv_events():
    """
    Process events from the CSV file and save them to a JSON file.
    Returns the number of new events found.
    """
    print("Processing events from CSV file...")
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Check if CSV file exists
    csv_path = 'data/pyorailyfi-tapahtumat.csv'
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return 0
    
    # Load existing events if available
    existing_events = []
    if os.path.exists('data/csv_events.json'):
        try:
            with open('data/csv_events.json', 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
            print(f"Loaded {len(existing_events)} existing events")
        except Exception as e:
            print(f"Error loading existing events: {e}")
    
    # Create a set of existing event identifiers (title + date) for quick comparison
    existing_event_ids = {f"{event['title']}_{event['datetime'].split()[0]}" 
                         for event in existing_events if 'title' in event and 'datetime' in event}
    
    # Read events from CSV
    new_events = []
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            # CSV is semicolon-separated with quotes
            reader = csv.reader(f, delimiter=';', quotechar='"')
            
            # Skip header row
            header = next(reader)
            print(f"CSV header: {header}")
            
            for row in reader:
                if len(row) >= 6:  # Ensure we have all required fields
                    date_str = row[0].strip()
                    name = row[1].strip()
                    location = row[2].strip()
                    event_type = row[3].strip()
                    organizer = row[4].strip()
                    info = row[5].strip()
                    
                    # Convert date to ISO format (YYYY-MM-DD 08:00)
                    try:
                        # Expected format: DD.MM.YYYY
                        date_parts = date_str.split('.')
                        if len(date_parts) == 3:
                            day = date_parts[0].zfill(2)
                            month = date_parts[1].zfill(2)
                            year = date_parts[2]
                            iso_date = f"{year}-{month}-{day} 08:00"
                        else:
                            iso_date = "Unknown Date"
                    except Exception as e:
                        print(f"Error parsing date {date_str}: {e}")
                        iso_date = "Unknown Date"
                    
                    # Extract link from info text
                    link = ""
                    url_pattern = r'https?://[^\s)"]+'
                    matches = re.findall(url_pattern, info)
                    if matches:
                        link = matches[0]
                    
                    # Create event object
                    event = {
                        'title': name,
                        'type': event_type,
                        'datetime': iso_date,
                        'location': location,
                        'organizer': organizer,
                        'description': info,
                        'link': link,
                        'source': 'csv'
                    }
                    
                    # Check if this is a new event
                    event_id = f"{name}_{iso_date.split()[0]}"
                    if event_id not in existing_event_ids:
                        new_events.append(event)
                        existing_event_ids.add(event_id)
                        print(f"Added new event: {name} ({event_type}) on {iso_date} at {location}")
                    else:
                        print(f"Event already exists: {name} on {iso_date}")
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    # Combine existing and new events
    all_events = existing_events + new_events
    
    # Save all events to JSON file
    with open('data/csv_events.json', 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    
    print(f"\nFound {len(new_events)} new events")
    print(f"Total events: {len(all_events)}")
    print("Events saved to data/csv_events.json")
    
    return len(new_events)

if __name__ == "__main__":
    new_events_count = process_csv_events()
    print(f"CSV processing complete. Found {new_events_count} new events.") 