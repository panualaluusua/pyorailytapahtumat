import os
import re
from datetime import datetime

def convert_combined_to_simple():
    """
    Converts the existing combined events to the simple format.
    """
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Read the combined events file
    try:
        with open('output/combined_events.txt', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: combined_events.txt not found. Please run combine_events.py first.")
        return
    
    # Split the content by event (using the /create marker)
    event_blocks = content.split('/create')
    
    # Process each event
    simple_events = []
    
    for block in event_blocks:
        if not block.strip():
            continue
        
        # Extract event details using regex
        title_match = re.search(r'title: (.*?)(?:\((.+?)\))?$', block, re.MULTILINE)
        datetime_match = re.search(r'datetime: (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})', block, re.MULTILINE)
        description_match = re.search(r'description: (.*?)(?=\n\n💡)', block, re.MULTILINE | re.DOTALL)
        
        if title_match and datetime_match and description_match:
            # Extract title and event type
            full_title = title_match.group(1).strip()
            event_type = title_match.group(2).strip() if title_match.group(2) else "Pyöräily"
            
            # Clean up title if it contains the event type
            title = full_title.replace(f"({event_type})", "").strip()
            
            # Extract date and convert to DD.MM.YYYY format
            date_str = datetime_match.group(1)
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                date_formatted = date_obj.strftime("%d.%m.%Y")
            except ValueError:
                date_formatted = date_str
            
            # Extract description
            description = description_match.group(1).strip()
            
            # Extract location and organizer from description
            location_match = re.search(r'at (.*?)(?= Järjestäjä:|$)', description)
            organizer_match = re.search(r'Järjestäjä: (.*?)(?= Lisätietoja:|$)', description)
            link_match = re.search(r'Lisätietoja: (https?://\S+)', description)
            
            location = location_match.group(1).strip() if location_match else "Unknown"
            organizer = organizer_match.group(1).strip() if organizer_match else ""
            link = link_match.group(1).strip() if link_match else ""
            
            # Clean up location - sometimes it contains the full event description
            if len(location) > 50 or " on " in location:
                location = location.split(" ")[0]  # Take just the first word
            
            # Clean up organizer - sometimes it contains extra text
            if organizer and len(organizer) > 50:
                organizer = organizer.split(" ")[0]  # Take just the first word
            
            # Create event in simple format
            simple_event = f"Title: {title}\n"
            simple_event += f"Type: {event_type}\n"
            simple_event += f"Date: {date_formatted}\n"
            simple_event += f"Location: {location}\n"
            
            if organizer:
                simple_event += f"Organizer: {organizer}\n"
            
            if link:
                # Clean up link - sometimes there are multiple links or text after the link
                clean_link = link.split(" ")[0]
                simple_event += f"Link: {clean_link}\n"
            
            # Add any additional description
            # Extract any additional description that's not already captured
            # For now, let's skip adding descriptions as they often contain duplicated information
            # that's already in the title, location, etc.
            
            simple_events.append(simple_event)
    
    # Write to simple_events.txt
    with open('data/simple_events.txt', 'w', encoding='utf-8') as f:
        f.write("\n\n".join(simple_events))
    
    print(f"Successfully converted {len(simple_events)} events to the simple format.")
    print("Output file: data/simple_events.txt")
    print("You can now edit this file and run 'python src/simple_events_format.py' to update the app.")

if __name__ == "__main__":
    convert_combined_to_simple() 