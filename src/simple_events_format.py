import os
import re
from datetime import datetime

def convert_simple_to_app_format():
    """
    Converts a simple events format to the format required by the Streamlit app.
    
    Simple format (simple_events.txt):
    Each event is separated by a blank line and has the following fields:
    - Title: Event name
    - Type: Event type (MTB, Gravel, Maantie, etc.)
    - Date: DD.MM.YYYY
    - Location: City or location
    - Organizer: Event organizer (optional)
    - Link: URL for more information (optional)
    - Description: Additional details (optional)
    """
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Check if simple_events.txt exists, if not create a template
    if not os.path.exists('data/simple_events.txt'):
        create_template_file()
        print("Created template file at data/simple_events.txt")
        print("Please add your events to this file and run this script again.")
        return
    
    # Read the simple events file
    with open('data/simple_events.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split the content by event (blank line separator)
    event_blocks = re.split(r'\n\s*\n', content)
    
    # Process each event
    events = []
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
        if 'title' in event and 'date' in event and 'location' in event and 'type' in event:
            events.append(event)
        else:
            missing = []
            for field in ['title', 'date', 'location', 'type']:
                if field not in event:
                    missing.append(field)
            print(f"Warning: Skipping event because it's missing required fields: {', '.join(missing)}")
    
    # Sort events by date
    events.sort(key=lambda x: x.get('datetime', '9999-99-99'))
    
    # Create the output file in the format required by the Streamlit app
    with open('output/clean_combined_events.txt', 'w', encoding='utf-8') as f:
        for event in events:
            # Create a clean description
            description = f"{event['title']} järjestetään {event['date']} paikkakunnalla {event['location']}."
            
            # Add organizer if available
            if 'organizer' in event and event['organizer']:
                description += f" Järjestäjänä toimii {event['organizer']}."
            
            # Add custom description if available
            if 'description' in event and event['description']:
                description += f" {event['description']}"
            
            # Add link if available
            if 'link' in event and event['link']:
                description += f" Lisätietoja tapahtumasta: {event['link']}"
            
            # Create the event template
            template = f"""/create 
title: {event['title']} ({event['type']})
channel: #ulkotapahtumat_listaus  
datetime: {event['datetime']}   
description: {description}

💡 **Ohjeet:** Klikkaa haluamaasi emojia ilmoittaaksesi osallistumisesi tai kiinnostuksesi. Emojin valinnan jälkeen sivupalkkiin avautuu chätti, jossa voit keskustella muiden osallistujien kanssa. 
---
"""
            f.write(template)
    
    print(f"Successfully converted {len(events)} events to the format required by the Streamlit app.")
    print("Output file: output/clean_combined_events.txt")

def create_template_file():
    """Create a template file with example events in the simple format."""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
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
    convert_simple_to_app_format() 