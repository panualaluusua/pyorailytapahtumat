import csv
import os
import re
from datetime import datetime
import json

def read_csv_events():
    """Read events from the CSV file."""
    print("Reading events from CSV file...")
    events = []
    
    try:
        with open('data/pyorailyfi-tapahtumat.csv', 'r', encoding='utf-8-sig') as f:
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
                    
                    # Create event object
                    event = {
                        'name': name,
                        'type': event_type,
                        'datetime': iso_date,
                        'location': location,
                        'description': f"Järjestäjä: {organizer}",
                        'link': extract_link(info),
                        'source': 'csv'
                    }
                    
                    events.append(event)
                    print(f"Added CSV event: {name} ({event_type}) on {iso_date} at {location}")
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    print(f"Found {len(events)} events in CSV file")
    return events

def extract_link(info_text):
    """Extract URL from info text."""
    if not info_text:
        return ""
    
    # Look for URLs in the text
    url_pattern = r'https?://[^\s)"]+'
    matches = re.findall(url_pattern, info_text)
    
    if matches:
        return matches[0]
    return ""

def read_bikeland_events():
    """Read events from the Bikeland output file."""
    print("\nReading Bikeland events...")
    events = []
    current_event = {}
    in_event = False
    
    try:
        with open('output/datetime_bikeland_events.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('/create'):
                    # Start of a new event
                    if current_event and 'name' in current_event:
                        events.append(current_event)
                    current_event = {'source': 'bikeland'}
                    in_event = True
                
                elif line.startswith('title:') and in_event:
                    # Extract name and type: "title: Event Name (Type)"
                    title_match = re.match(r'title:\s*(.*?)\s*\((.*?)\)', line)
                    if title_match:
                        current_event['name'] = title_match.group(1).strip()
                        current_event['type'] = title_match.group(2).strip()
                    else:
                        current_event['name'] = line.replace('title:', '').strip()
                        current_event['type'] = "Unknown"
                
                elif line.startswith('datetime:') and in_event:
                    current_event['datetime'] = line.replace('datetime:', '').strip()
                
                elif line.startswith('description:') and in_event:
                    desc = line.replace('description:', '').strip()
                    current_event['description'] = desc
                    
                    # Extract location from description
                    loc_match = re.search(r'at\s+(.*?)\s+', desc)
                    if loc_match:
                        current_event['location'] = loc_match.group(1).strip()
                    else:
                        current_event['location'] = "Unknown Location"
                    
                    # Extract link from description
                    link_match = re.search(r'Lisätietoja:\s*(https?://[^\s]+)', desc)
                    if link_match:
                        current_event['link'] = link_match.group(1).strip()
                    else:
                        current_event['link'] = ""
                
                elif line == "---":
                    # End of an event
                    if current_event and 'name' in current_event:
                        events.append(current_event)
                        current_event = {'source': 'bikeland'}
                        in_event = False
            
            # Add the last event if exists
            if current_event and 'name' in current_event:
                events.append(current_event)
    
    except Exception as e:
        print(f"Error reading Bikeland events: {e}")
    
    print(f"Found {len(events)} Bikeland events")
    return events

def is_duplicate(event1, event2):
    """Check if two events are duplicates."""
    # If names are similar and dates are the same, consider them duplicates
    name_similarity = event1['name'].lower() in event2['name'].lower() or event2['name'].lower() in event1['name'].lower()
    
    # Compare only the date part (YYYY-MM-DD)
    date1 = event1['datetime'].split()[0] if event1['datetime'] != "Unknown Date" else ""
    date2 = event2['datetime'].split()[0] if event2['datetime'] != "Unknown Date" else ""
    date_similarity = date1 == date2 and date1 != ""
    
    return name_similarity and date_similarity

def combine_events(csv_events, bikeland_events):
    """Combine events from both sources, marking duplicates."""
    print("\nCombining events and checking for duplicates...")
    all_events = []
    duplicates = []
    
    # Add all Bikeland events
    for event in bikeland_events:
        all_events.append(event)
    
    # Add CSV events, checking for duplicates
    for csv_event in csv_events:
        is_duplicate_event = False
        
        for bikeland_event in bikeland_events:
            if is_duplicate(csv_event, bikeland_event):
                duplicates.append((csv_event, bikeland_event))
                is_duplicate_event = True
                print(f"Found duplicate: {csv_event['name']} on {csv_event['datetime']} matches {bikeland_event['name']} on {bikeland_event['datetime']}")
                break
        
        # Add the CSV event even if it's a duplicate
        all_events.append(csv_event)
    
    print(f"Found {len(duplicates)} duplicate events")
    print(f"Total combined events: {len(all_events)}")
    
    return all_events, duplicates

def create_combined_template(all_events, duplicates):
    """Create a combined template file with all events."""
    print("\nCreating combined template file...")
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Sort events by date
    sorted_events = sorted(all_events, key=lambda x: x['datetime'] if x['datetime'] != "Unknown Date" else "9999-99-99")
    
    with open('output/combined_events.txt', 'w', encoding='utf-8') as f:
        for event in sorted_events:
            # Clean up location
            location = event['location']
            if location == "Unknown Location" and event['name'].split()[-1]:
                # Try to extract location from the event name (often the last word)
                possible_location = event['name'].split()[-1]
                if len(possible_location) > 3 and possible_location not in ["Tour", "Race", "MTB", "Gravel"]:
                    location = possible_location
            
            # Create a clean description
            clean_description = ""
            if event['description']:
                # Remove redundant information like repeated event name and date
                clean_description = event['description']
                # Remove patterns like "Event Name on YYYY-MM-DD at Location"
                pattern = f"{re.escape(event['name'])} on {re.escape(event['datetime'])} at .*?\\s+"
                clean_description = re.sub(pattern, "", clean_description)
                # Remove "Unknown Location" if we have a better location
                clean_description = clean_description.replace("Unknown Location", "").strip()
                # Remove duplicate location mentions
                if location != "Unknown Location":
                    clean_description = clean_description.replace(location, "").strip()
                # Remove source information
                clean_description = re.sub(r'\s*\[Source: (csv|bikeland)\]', '', clean_description)
            
            # Add organizer info if available and not already in description
            if event['source'] == 'csv' and "Järjestäjä:" in clean_description:
                clean_description = clean_description.strip()
            
            # Format the link
            event_link_text = f"Lisätietoja: {event['link']}" if event['link'] else ""
            
            # Create the final description
            final_description = f"{event['name']} on {event['datetime']} at {location}"
            if clean_description:
                final_description += f" {clean_description}"
            if event_link_text and event_link_text not in final_description:
                final_description += f" {event_link_text}"
            
            # Remove source information from the description (double-check)
            final_description = re.sub(r'\s*\[Source: (csv|bikeland)\]', '', final_description)
            
            template = f"""/create 
title: {event['name']} ({event['type']})
channel: #ulkotapahtumat_listaus  
datetime: {event['datetime']}   
description: {final_description}

💡 **Ohjeet:** Klikkaa haluamaasi emojia ilmoittaaksesi osallistumisesi tai kiinnostuksesi. Emojin valinnan jälkeen sivupalkkiin avautuu chätti, jossa voit keskustella muiden osallistujien kanssa. 

"""
            f.write(template)
            f.write("\n---\n\n")  # Separator between events
    
    # Also create a duplicates report
    with open('output/duplicate_events.txt', 'w', encoding='utf-8') as f:
        f.write("# Duplicate Events Report\n\n")
        
        for i, (csv_event, bikeland_event) in enumerate(duplicates):
            f.write(f"## Duplicate {i+1}\n\n")
            f.write(f"### CSV Event\n")
            f.write(f"- Name: {csv_event['name']}\n")
            f.write(f"- Type: {csv_event['type']}\n")
            f.write(f"- Date: {csv_event['datetime']}\n")
            f.write(f"- Location: {csv_event['location']}\n")
            f.write(f"- Link: {csv_event['link']}\n\n")
            
            f.write(f"### Bikeland Event\n")
            f.write(f"- Name: {bikeland_event['name']}\n")
            f.write(f"- Type: {bikeland_event['type']}\n")
            f.write(f"- Date: {bikeland_event['datetime']}\n")
            f.write(f"- Location: {bikeland_event['location']}\n")
            f.write(f"- Link: {bikeland_event['link']}\n\n")
            
            f.write("---\n\n")
    
    print(f"Template file created: output/combined_events.txt")
    print(f"Duplicates report created: output/duplicate_events.txt")

def main():
    print("Starting event combination process...")
    
    # Read events from CSV
    csv_events = read_csv_events()
    
    # Read events from Bikeland
    bikeland_events = read_bikeland_events()
    
    # Combine events and check for duplicates
    all_events, duplicates = combine_events(csv_events, bikeland_events)
    
    # Create combined template
    create_combined_template(all_events, duplicates)
    
    print("Done! Check output/combined_events.txt for the combined events.")

if __name__ == "__main__":
    main() 