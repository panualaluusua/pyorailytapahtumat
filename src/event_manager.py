import os
import json
from datetime import datetime
import sys
import importlib.util

def import_module_from_file(module_name, file_path):
    """Import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import the event processing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
bikeland_events = import_module_from_file("bikeland_events", os.path.join(current_dir, "bikeland_events.py"))
csv_events = import_module_from_file("csv_events", os.path.join(current_dir, "csv_events.py"))
manual_events = import_module_from_file("manual_events", os.path.join(current_dir, "manual_events.py"))

def create_event_id(event):
    """Create a unique ID for an event based on title and date"""
    if 'title' in event and 'datetime' in event:
        date_part = event['datetime'].split()[0] if ' ' in event['datetime'] else event['datetime']
        return f"{event['title']}_{date_part}"
    return None

def combine_all_events():
    """
    Combine events from all sources and generate the output for the Streamlit app.
    """
    print("Starting event manager...")
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Process events from all sources
    bikeland_count = bikeland_events.scrape_bikeland_events()
    csv_count = csv_events.process_csv_events()
    manual_count = manual_events.process_manual_events()
    
    print(f"\nProcessed events from all sources:")
    print(f"- Bikeland: {bikeland_count} new events")
    print(f"- CSV: {csv_count} new events")
    print(f"- Manual: {manual_count} new events")
    
    # Load events from all sources
    all_events = []
    
    # Load manually edited events first (highest priority)
    manual_edits_file = 'data/manual_edits.json'
    manual_edits = []
    if os.path.exists(manual_edits_file):
        try:
            with open(manual_edits_file, 'r', encoding='utf-8') as f:
                manual_edits = json.load(f)
                all_events.extend(manual_edits)
                print(f"Loaded {len(manual_edits)} manually edited events")
        except Exception as e:
            print(f"Error loading manually edited events: {e}")
    
    # Load Bikeland events
    if os.path.exists('data/bikeland_events.json'):
        try:
            with open('data/bikeland_events.json', 'r', encoding='utf-8') as f:
                bikeland_events_data = json.load(f)
                all_events.extend(bikeland_events_data)
                print(f"Loaded {len(bikeland_events_data)} Bikeland events")
        except Exception as e:
            print(f"Error loading Bikeland events: {e}")
    
    # Load CSV events
    if os.path.exists('data/csv_events.json'):
        try:
            with open('data/csv_events.json', 'r', encoding='utf-8') as f:
                csv_events_data = json.load(f)
                all_events.extend(csv_events_data)
                print(f"Loaded {len(csv_events_data)} CSV events")
        except Exception as e:
            print(f"Error loading CSV events: {e}")
    
    # Load manual events
    if os.path.exists('data/manual_events.json'):
        try:
            with open('data/manual_events.json', 'r', encoding='utf-8') as f:
                manual_events_data = json.load(f)
                all_events.extend(manual_events_data)
                print(f"Loaded {len(manual_events_data)} manual events")
        except Exception as e:
            print(f"Error loading manual events: {e}")
    
    # Load blacklist
    blacklist = []
    if os.path.exists('data/event_blacklist.json'):
        try:
            with open('data/event_blacklist.json', 'r', encoding='utf-8') as f:
                blacklist = json.load(f)
            print(f"Loaded {len(blacklist)} blacklisted events")
        except Exception as e:
            print(f"Error loading blacklist: {e}")
    
    # Remove duplicate events (same title and date)
    unique_events = {}
    blacklisted_count = 0
    
    for event in all_events:
        # Create event ID using the same method as in event_admin.py
        event_id = create_event_id(event)
        
        # Skip blacklisted events
        if event_id and event_id in blacklist:
            print(f"Skipping blacklisted event: {event_id}")
            blacklisted_count += 1
            continue
            
        # If there are duplicates, prioritize:
        # 1. manual_edit (from admin panel)
        # 2. manual (from simple_events.txt)
        # 3. csv (from CSV file)
        # 4. bikeland (from Bikeland.fi)
        if event_id:
            if event_id not in unique_events:
                unique_events[event_id] = event
            elif event.get('source') == 'manual_edit':
                # Always prefer manual_edit
                unique_events[event_id] = event
            elif event.get('source') == 'manual' and unique_events[event_id].get('source') != 'manual_edit':
                # Prefer manual over csv and bikeland
                unique_events[event_id] = event
            elif event.get('source') == 'csv' and unique_events[event_id].get('source') not in ['manual_edit', 'manual']:
                # Prefer csv over bikeland
                unique_events[event_id] = event
    
    # Convert back to list
    combined_events = list(unique_events.values())
    
    # Sort events by date
    combined_events.sort(key=lambda x: x.get('datetime', '9999-99-99'))
    
    print(f"\nTotal unique events: {len(combined_events)}")
    print(f"Blacklisted events skipped: {blacklisted_count}")
    
    # Save combined events to JSON file
    with open('data/all_events.json', 'w', encoding='utf-8') as f:
        json.dump(combined_events, f, indent=2, ensure_ascii=False)
    
    print("Combined events saved to data/all_events.json")
    
    # Generate the output file for the Streamlit app
    generate_streamlit_output(combined_events)
    
    return len(combined_events)

def generate_streamlit_output(events):
    """
    Generate the output file for the Streamlit app.
    """
    print("\nGenerating output for Streamlit app...")
    
    with open('output/clean_combined_events.txt', 'w', encoding='utf-8') as f:
        for event in events:
            # Create a clean description
            description = f"{event['title']} järjestetään "
            
            # Add date in Finnish format
            try:
                date_str = event['datetime'].split()[0]
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d.%m.%Y')
                description += f"{formatted_date} "
            except:
                description += f"{event['datetime']} "
            
            # Add location
            description += f"paikkakunnalla {event['location']}."
            
            # Add organizer if available
            if 'organizer' in event and event['organizer']:
                description += f" Järjestäjänä toimii {event['organizer']}."
            
            # Add custom description if available
            if 'description' in event and event['description'] and event['source'] == 'manual':
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
    
    print("Output file created: output/clean_combined_events.txt")

def main():
    """Main function to run the event manager."""
    print("=== Bike Event Manager ===")
    print("This script will:")
    print("1. Scrape events from Bikeland.fi")
    print("2. Process events from the CSV file")
    print("3. Process manual events from simple_events.txt")
    print("4. Combine all events and remove duplicates")
    print("5. Generate the output file for the Streamlit app")
    print("===============================")
    
    event_count = combine_all_events()
    
    print("\nAll done!")
    print(f"Total events: {event_count}")
    print("You can now run the Streamlit app with: python -m streamlit run src/event_map_app.py")

if __name__ == "__main__":
    main() 