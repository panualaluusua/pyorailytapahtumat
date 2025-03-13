import re
import os
from datetime import datetime
from collections import Counter, defaultdict

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
                        current_event['organizer'] = "Unknown Organizer"
                
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

def analyze_events(events):
    """Analyze events and generate statistics."""
    print("\nAnalyzing events...")
    
    # Initialize counters and data structures
    total_events = len(events)
    events_by_month = Counter()
    events_by_location = Counter()
    events_by_type = Counter()
    events_by_organizer = Counter()
    locations = set()
    organizers = set()
    event_types = set()
    
    # Events by day of week
    days_of_week = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }
    events_by_day = Counter()
    
    # Events by season
    seasons = {
        "Winter": [12, 1, 2],
        "Spring": [3, 4, 5],
        "Summer": [6, 7, 8],
        "Fall": [9, 10, 11]
    }
    events_by_season = Counter()
    
    # Monthly distribution
    monthly_distribution = defaultdict(list)
    
    # Process each event
    for event in events:
        # Extract date components
        try:
            date_str = event.get('datetime', '').split()[0]  # Get just the date part
            if date_str and date_str != "Unknown Date":
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Count by month
                month_name = date_obj.strftime('%B')  # Full month name
                events_by_month[month_name] += 1
                
                # Add to monthly distribution
                monthly_distribution[month_name].append(event['title'])
                
                # Count by day of week
                day_of_week = days_of_week[date_obj.weekday()]
                events_by_day[day_of_week] += 1
                
                # Count by season
                month_num = date_obj.month
                for season, months in seasons.items():
                    if month_num in months:
                        events_by_season[season] += 1
                        break
        except Exception as e:
            print(f"Error processing date for event {event.get('title', 'Unknown')}: {e}")
        
        # Count by location
        location = event.get('location', 'Unknown Location')
        if location != "Unknown Location":
            events_by_location[location] += 1
            locations.add(location)
        
        # Count by type
        event_type = event.get('type', 'Unknown')
        if event_type != "Unknown":
            events_by_type[event_type] += 1
            event_types.add(event_type)
        
        # Count by organizer
        organizer = event.get('organizer', 'Unknown Organizer')
        if organizer != "Unknown Organizer":
            events_by_organizer[organizer] += 1
            organizers.add(organizer)
    
    # Find busiest month, location, etc.
    busiest_month = events_by_month.most_common(1)[0] if events_by_month else ("None", 0)
    busiest_location = events_by_location.most_common(1)[0] if events_by_location else ("None", 0)
    most_common_type = events_by_type.most_common(1)[0] if events_by_type else ("None", 0)
    most_active_organizer = events_by_organizer.most_common(1)[0] if events_by_organizer else ("None", 0)
    busiest_day = events_by_day.most_common(1)[0] if events_by_day else ("None", 0)
    busiest_season = events_by_season.most_common(1)[0] if events_by_season else ("None", 0)
    
    # Calculate summer events (June, July, August)
    summer_events = sum(events_by_month[month] for month in ['June', 'July', 'August'])
    
    # Return the statistics
    return {
        "total_events": total_events,
        "unique_locations": len(locations),
        "unique_organizers": len(organizers),
        "unique_event_types": len(event_types),
        "events_by_month": dict(events_by_month),
        "events_by_location": dict(events_by_location),
        "events_by_type": dict(events_by_type),
        "events_by_organizer": dict(events_by_organizer),
        "events_by_day": dict(events_by_day),
        "events_by_season": dict(events_by_season),
        "busiest_month": busiest_month,
        "busiest_location": busiest_location,
        "most_common_type": most_common_type,
        "most_active_organizer": most_active_organizer,
        "busiest_day": busiest_day,
        "busiest_season": busiest_season,
        "summer_events": summer_events,
        "monthly_distribution": dict(monthly_distribution)
    }

def create_summary_report(stats):
    """Create a summary report with the statistics."""
    print("\nCreating summary report...")
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    with open('output/event_statistics.txt', 'w', encoding='utf-8') as f:
        f.write("# Pyöräilytapahtumien tilastot 2025\n\n")
        
        # General statistics
        f.write("## Yleiset tilastot\n\n")
        f.write(f"- Tapahtumia yhteensä: {stats['total_events']}\n")
        f.write(f"- Eri paikkakuntia: {stats['unique_locations']}\n")
        f.write(f"- Eri järjestäjiä: {stats['unique_organizers']}\n")
        f.write(f"- Eri tapahtumatyyppejä: {stats['unique_event_types']}\n")
        f.write(f"- Kesän tapahtumia (kesä-elokuu): {stats['summer_events']}\n")
        f.write("\n")
        
        # Busiest periods
        f.write("## Kiireisimmät ajanjaksot\n\n")
        f.write(f"- Kiireisin kuukausi: {stats['busiest_month'][0]} ({stats['busiest_month'][1]} tapahtumaa)\n")
        f.write(f"- Kiireisin viikonpäivä: {stats['busiest_day'][0]} ({stats['busiest_day'][1]} tapahtumaa)\n")
        f.write(f"- Kiireisin vuodenaika: {stats['busiest_season'][0]} ({stats['busiest_season'][1]} tapahtumaa)\n")
        f.write("\n")
        
        # Most popular locations and types
        f.write("## Suosituimmat paikkakunnat ja tyypit\n\n")
        f.write(f"- Suosituin paikkakunta: {stats['busiest_location'][0]} ({stats['busiest_location'][1]} tapahtumaa)\n")
        f.write(f"- Yleisin tapahtumatyyppi: {stats['most_common_type'][0]} ({stats['most_common_type'][1]} tapahtumaa)\n")
        f.write(f"- Aktiivisin järjestäjä: {stats['most_active_organizer'][0]} ({stats['most_active_organizer'][1]} tapahtumaa)\n")
        f.write("\n")
        
        # Events by month
        f.write("## Tapahtumat kuukausittain\n\n")
        for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']:
            count = stats['events_by_month'].get(month, 0)
            f.write(f"- {month}: {count} tapahtumaa\n")
        f.write("\n")
        
        # Events by season
        f.write("## Tapahtumat vuodenajoittain\n\n")
        for season in ['Winter', 'Spring', 'Summer', 'Fall']:
            count = stats['events_by_season'].get(season, 0)
            f.write(f"- {season}: {count} tapahtumaa\n")
        f.write("\n")
        
        # Top 10 locations
        f.write("## Top 10 paikkakunnat\n\n")
        for location, count in sorted(stats['events_by_location'].items(), key=lambda x: x[1], reverse=True)[:10]:
            f.write(f"- {location}: {count} tapahtumaa\n")
        f.write("\n")
        
        # Top 10 event types
        f.write("## Top 10 tapahtumatyypit\n\n")
        for event_type, count in sorted(stats['events_by_type'].items(), key=lambda x: x[1], reverse=True)[:10]:
            f.write(f"- {event_type}: {count} tapahtumaa\n")
        f.write("\n")
        
        # Events by day of week
        f.write("## Tapahtumat viikonpäivittäin\n\n")
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            count = stats['events_by_day'].get(day, 0)
            f.write(f"- {day}: {count} tapahtumaa\n")
        f.write("\n")
        
        # Monthly event listings
        f.write("## Tapahtumat kuukausittain (listaus)\n\n")
        for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']:
            events = stats['monthly_distribution'].get(month, [])
            if events:
                f.write(f"### {month} ({len(events)} tapahtumaa)\n\n")
                for event in events:
                    f.write(f"- {event}\n")
                f.write("\n")
    
    print(f"Summary report created: output/event_statistics.txt")

def main():
    print("Starting event statistics analysis...")
    
    # Read combined events
    events = read_combined_events()
    
    # Analyze events
    stats = analyze_events(events)
    
    # Create summary report
    create_summary_report(stats)
    
    print("Done! Check output/event_statistics.txt for the statistics report.")

if __name__ == "__main__":
    main() 