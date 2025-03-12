import re
import os
from datetime import datetime

def read_combined_events():
    """Read events from the combined events file."""
    print("Reading combined events...")
    events = []
    current_event = {}
    in_event = False
    
    try:
        with open('output/combined_events.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('/create'):
                    # Start of a new event
                    if current_event and 'title' in current_event:
                        events.append(current_event)
                    current_event = {}
                    in_event = True
                
                elif line.startswith('title:') and in_event:
                    # Extract title and type: "title: Event Name (Type)"
                    title_match = re.match(r'title:\s*(.*?)\s*\((.*?)\)', line)
                    if title_match:
                        current_event['title'] = title_match.group(1).strip()
                        current_event['type'] = title_match.group(2).strip()
                    else:
                        current_event['title'] = line.replace('title:', '').strip()
                        current_event['type'] = "Unknown"
                
                elif line.startswith('channel:') and in_event:
                    current_event['channel'] = line.replace('channel:', '').strip()
                
                elif line.startswith('datetime:') and in_event:
                    current_event['datetime'] = line.replace('datetime:', '').strip()
                
                elif line.startswith('description:') and in_event:
                    desc = line.replace('description:', '').strip()
                    current_event['description'] = desc
                    
                    # Extract location from description
                    loc_match = re.search(r'at\s+(.*?)(?:\s+Järjestäjä:|\s+Lisätietoja:|$)', desc)
                    if loc_match:
                        current_event['location'] = loc_match.group(1).strip()
                    else:
                        current_event['location'] = "Unknown Location"
                    
                    # Extract organizer from description
                    org_match = re.search(r'Järjestäjä:\s*(.*?)(?:\s+Lisätietoja:|$)', desc)
                    if org_match:
                        current_event['organizer'] = org_match.group(1).strip()
                    else:
                        current_event['organizer'] = ""
                    
                    # Extract link from description
                    link_match = re.search(r'Lisätietoja:\s*(https?://[^\s]+)', desc)
                    if link_match:
                        current_event['link'] = link_match.group(1).strip()
                    else:
                        current_event['link'] = ""
                
                elif line == "---":
                    # End of an event
                    if current_event and 'title' in current_event:
                        events.append(current_event)
                        current_event = {}
                        in_event = False
            
            # Add the last event if exists
            if current_event and 'title' in current_event:
                events.append(current_event)
    
    except Exception as e:
        print(f"Error reading combined events: {e}")
    
    print(f"Found {len(events)} events")
    return events

def create_clean_description(event):
    """Create a clean, fluid description without redundancy."""
    # Start with the basic information
    title = event['title']
    date_str = event['datetime']
    location = event['location']
    
    # Format the date in a more readable way
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        formatted_date = date_obj.strftime('%d.%m.%Y')
    except:
        formatted_date = date_str
    
    # Create a clean description
    description = f"{title} järjestetään {formatted_date} paikkakunnalla {location}."
    
    # Add organizer information if available
    if event.get('organizer'):
        description += f" Järjestäjänä toimii {event['organizer']}."
    
    # Add link if available
    if event.get('link'):
        description += f" Lisätietoja tapahtumasta: {event['link']}"
    
    return description

def create_clean_combined_file(events):
    """Create a clean combined events file with fluid descriptions."""
    print("\nCreating clean combined events file...")
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Sort events by date
    sorted_events = sorted(events, key=lambda x: x['datetime'] if x['datetime'] != "Unknown Date" else "9999-99-99")
    
    with open('output/clean_combined_events.txt', 'w', encoding='utf-8') as f:
        for event in sorted_events:
            # Create a clean description
            clean_description = create_clean_description(event)
            
            template = f"""/create 
title: {event['title']} ({event['type']})
channel: {event.get('channel', '#ulkotapahtumat_listaus')}  
datetime: {event['datetime']}   
description: {clean_description}

💡 **Ohjeet:** Klikkaa haluamaasi emojia ilmoittaaksesi osallistumisesi tai kiinnostuksesi. Emojin valinnan jälkeen sivupalkkiin avautuu chätti, jossa voit keskustella muiden osallistujien kanssa. 

"""
            f.write(template)
            f.write("\n---\n\n")  # Separator between events
    
    print(f"Clean combined events file created: output/clean_combined_events.txt")

def main():
    print("Starting clean combined events process...")
    
    # Read combined events
    events = read_combined_events()
    
    # Create clean combined file
    create_clean_combined_file(events)
    
    print("Done! Check output/clean_combined_events.txt for the clean combined events.")

if __name__ == "__main__":
    main() 