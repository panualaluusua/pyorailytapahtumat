import json
import os
import pandas as pd
from datetime import datetime
import difflib
import argparse

def load_events():
    """Load events from all_events.json file."""
    try:
        with open('data/all_events.json', 'r', encoding='utf-8') as f:
            events = json.load(f)
        return events
    except Exception as e:
        print(f"Error loading events: {e}")
        return []

def find_exact_duplicates(events):
    """Find events with exactly the same title and date."""
    # Create a dictionary to track events by title and date
    event_dict = {}
    exact_duplicates = []
    
    for event in events:
        if 'title' in event and 'datetime' in event:
            # Create a key using title and date
            event_id = f"{event['title']}_{event['datetime'].split()[0]}"
            
            if event_id in event_dict:
                # Found a duplicate
                exact_duplicates.append({
                    'event_id': event_id,
                    'original': event_dict[event_id],
                    'duplicate': event
                })
            else:
                event_dict[event_id] = event
    
    return exact_duplicates

def find_similar_titles(events, threshold=0.8):
    """Find events with similar titles but different dates."""
    similar_events = []
    
    # Create a list of all event titles with their dates and indices
    event_titles = [(i, event.get('title', ''), event.get('datetime', '').split()[0]) 
                   for i, event in enumerate(events) if 'title' in event]
    
    # Compare each title with all others
    for i, (idx1, title1, date1) in enumerate(event_titles):
        for idx2, title2, date2 in event_titles[i+1:]:
            # Skip if dates are the same (these would be caught by exact duplicates)
            if date1 == date2:
                continue
                
            # Calculate similarity ratio
            similarity = difflib.SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
            
            if similarity >= threshold:
                similar_events.append({
                    'similarity': similarity,
                    'event1': events[idx1],
                    'event2': events[idx2]
                })
    
    # Sort by similarity (highest first)
    similar_events.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_events

def find_same_date_location(events):
    """Find events on the same date at the same location."""
    same_date_location = []
    
    # Create a dictionary to track events by date and location
    date_location_dict = {}
    
    for event in events:
        if 'datetime' in event and 'location' in event:
            date = event.get('datetime', '').split()[0]
            location = event.get('location', '')
            
            if date and location:
                key = f"{date}_{location}"
                
                if key in date_location_dict:
                    date_location_dict[key].append(event)
                else:
                    date_location_dict[key] = [event]
    
    # Find locations with multiple events on the same day
    for key, event_list in date_location_dict.items():
        if len(event_list) > 1:
            date, location = key.split('_', 1)
            same_date_location.append({
                'date': date,
                'location': location,
                'events': event_list
            })
    
    return same_date_location

def print_event_details(event):
    """Print formatted event details."""
    print(f"  Title: {event.get('title', 'Unknown')}")
    print(f"  Type: {event.get('type', 'Unknown')}")
    print(f"  Date: {event.get('datetime', 'Unknown').split()[0]}")
    print(f"  Location: {event.get('location', 'Unknown')}")
    print(f"  Source: {event.get('source', 'Unknown')}")
    if 'organizer' in event and event['organizer']:
        print(f"  Organizer: {event['organizer']}")
    if 'link' in event and event['link']:
        print(f"  Link: {event['link']}")
    print()

def check_duplicates(verbose=False, similarity_threshold=0.8):
    """Check for duplicate events in all_events.json."""
    print("Checking for duplicate events in all_events.json...")
    
    # Load events
    events = load_events()
    if not events:
        print("No events found or error loading events.")
        return
    
    print(f"Loaded {len(events)} events.\n")
    
    # Find exact duplicates
    exact_duplicates = find_exact_duplicates(events)
    if exact_duplicates:
        print(f"Found {len(exact_duplicates)} exact duplicates (same title and date):")
        for i, dup in enumerate(exact_duplicates, 1):
            print(f"\nDuplicate #{i}: {dup['event_id']}")
            
            print("\nOriginal event:")
            print_event_details(dup['original'])
            
            print("Duplicate event:")
            print_event_details(dup['duplicate'])
    else:
        print("No exact duplicates found (good!).\n")
    
    # Find similar titles
    similar_events = find_similar_titles(events, similarity_threshold)
    if similar_events:
        print(f"\nFound {len(similar_events)} events with similar titles (but different dates):")
        for i, sim in enumerate(similar_events, 1):
            print(f"\nSimilar pair #{i} (similarity: {sim['similarity']:.2f}):")
            
            print("\nEvent 1:")
            print_event_details(sim['event1'])
            
            print("Event 2:")
            print_event_details(sim['event2'])
            
            if not verbose and i >= 5:
                print(f"... and {len(similar_events) - 5} more similar pairs. Use --verbose to see all.")
                break
    else:
        print("No events with similar titles found.\n")
    
    # Find events on the same date at the same location
    same_date_location = find_same_date_location(events)
    if same_date_location:
        print(f"\nFound {len(same_date_location)} locations with multiple events on the same day:")
        for i, sdl in enumerate(same_date_location, 1):
            print(f"\nLocation #{i}: {sdl['location']} on {sdl['date']}")
            print(f"Number of events: {len(sdl['events'])}")
            
            for j, event in enumerate(sdl['events'], 1):
                print(f"\nEvent {j}:")
                print_event_details(event)
            
            if not verbose and i >= 5:
                print(f"... and {len(same_date_location) - 5} more locations. Use --verbose to see all.")
                break
    else:
        print("No locations with multiple events on the same day found.\n")
    
    print("\nDuplicate check complete.")

def main():
    parser = argparse.ArgumentParser(description='Check for duplicate events in all_events.json')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all duplicates')
    parser.add_argument('--threshold', '-t', type=float, default=0.8, 
                        help='Similarity threshold for title comparison (0.0-1.0, default: 0.8)')
    args = parser.parse_args()
    
    check_duplicates(verbose=args.verbose, similarity_threshold=args.threshold)

if __name__ == "__main__":
    main() 