import os
import re
from datetime import datetime
import json

def process_manual_events():
    """
    Process events from the simple_events.txt file and save them to a JSON file.
    Returns the number of new events found.
    """
    print("Processing manual events from simple_events.txt...")
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Check if simple_events.txt exists, if not create a template
    if not os.path.exists('data/simple_events.txt'):
        create_template_file()
        print("Created template file at data/simple_events.txt")
        print("Please add your events to this file and run this script again.")
        return 0
    
    # Load existing events if available
    existing_events = []
    existing_event_dict = {}
    if os.path.exists('data/manual_events.json'):
        try:
            with open('data/manual_events.json', 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
            print(f"Loaded {len(existing_events)} existing events")
            
            # Create a dictionary for quick lookup
            for event in existing_events:
                event_id = f"{event['title']}_{event['datetime'].split()[0]}" 
                existing_event_dict[event_id] = event
        except Exception as e:
            print(f"Error loading existing events: {e}")
    
    # Create a set of existing event identifiers (title + date) for quick comparison
    existing_event_ids = {f"{event['title']}_{event['datetime'].split()[0]}" 
                         for event in existing_events if 'title' in event and 'datetime' in event}
    
    # Read the simple events file
    with open('data/simple_events.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the content by event (blank line separator)
    event_blocks = re.split(r'\n\s*\n', content)
    
    # Process each event
    new_events = []
    for block in event_blocks:
        if not block.strip():
            continue
        
        # Parse the event
        event = {}
        lines = block.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            # Extract key-value pairs
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'title':
                    event['title'] = value
                elif key == 'type':
                    event['type'] = value
                elif key == 'date':
                    event['date'] = value
                    # Convert date to ISO format (YYYY-MM-DD 08:00)
                    try:
                        # Expected format: DD.MM.YYYY
                        date_parts = value.split('.')
                        if len(date_parts) == 3:
                            day = date_parts[0].zfill(2)
                            month = date_parts[1].zfill(2)
                            year = date_parts[2]
                            event['datetime'] = f"{year}-{month}-{day} 08:00"
                        else:
                            event['datetime'] = "Unknown Date"
                    except Exception as e:
                        print(f"Error parsing date {value}: {e}")
                        event['datetime'] = "Unknown Date"
                elif key == 'location':
                    event['location'] = value
                elif key == 'organizer':
                    event['organizer'] = value
                elif key == 'link':
                    event['link'] = value
                elif key == 'description':
                    event['description'] = value
        
        # Check if we have the minimum required fields
        if 'title' in event and 'datetime' in event and 'location' in event and 'type' in event:
            # Add source field
            event['source'] = 'manual'
            
            # Check if this is a new event
            event_id = f"{event['title']}_{event['datetime'].split()[0]}"
            if event_id not in existing_event_ids:
                # Add timestamp for new events
                event['added_timestamp'] = datetime.now().isoformat()
                
                new_events.append(event)
                existing_event_ids.add(event_id)
                print(f"Added new event: {event['title']} ({event['type']}) on {event['datetime']} at {event['location']}")
            else:
                # Preserve the timestamp for existing events
                if event_id in existing_event_dict and 'added_timestamp' in existing_event_dict[event_id]:
                    event['added_timestamp'] = existing_event_dict[event_id]['added_timestamp']
                else:
                    event['added_timestamp'] = datetime.now().isoformat()
                
                print(f"Event already exists: {event['title']} on {event['datetime']}")
        else:
            missing = []
            for field in ['title', 'date', 'location', 'type']:
                if field not in event:
                    missing.append(field)
            print(f"Warning: Skipping event because it's missing required fields: {', '.join(missing)}")
    
    # Combine existing and new events
    all_events = existing_events + new_events
    
    # Save all events to JSON file
    with open('data/manual_events.json', 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    
    print(f"\nFound {len(new_events)} new events")
    print(f"Total events: {len(all_events)}")
    print("Events saved to data/manual_events.json")
    
    return len(new_events)

def create_template_file():
    """Create a template file with example events in the simple format."""
    template = """Title: Helsinki MTB Marathon
Type: MTB XCM
Date: 15.06.2025
Location: Helsinki
Organizer: Cycle Club Helsinki
Link: https://example.com/helsinki-mtb
Description: Challenging mountain bike marathon through the forests of Helsinki.

Title: Turku Gravel Race
Type: Gravel
Date: 05.07.2025
Location: Turku
Organizer: Turun Urheiluliitto
Link: https://example.com/turku-gravel
Description: Beautiful gravel roads around Turku archipelago.

Title: Tampere Road Race
Type: Maantie
Date: 20.08.2025
Location: Tampere
Organizer: Tampereen Pyöräilijät
Link: https://example.com/tampere-road
Description: Classic road cycling event with multiple distance options.
"""
    
    with open('data/simple_events.txt', 'w', encoding='utf-8') as f:
        f.write(template)

if __name__ == "__main__":
    new_events_count = process_manual_events()
    print(f"Manual events processing complete. Found {new_events_count} new events.") 