import re
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

def parse_bikeland_events():
    print("Parsing Bikeland events with the specific HTML structure and converting dates to ISO format...")
    
    # Read the HTML file
    with open('data/bikeland_response.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
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
        'tammi': '01',
        'tammi.': '01',
        'helmik': '02',
        'helmik.': '02',
        'maalis': '03',
        'maalis.': '03',
        'huhti': '04',
        'huhti.': '04',
        'touko': '05',
        'touko.': '05',
        'kesä': '06',
        'kesä.': '06',
        'kesäk': '06',
        'kesäk.': '06',
        'heinä': '07',
        'heinä.': '07',
        'heinäk': '07',
        'heinäk.': '07',
        'elo': '08',
        'elo.': '08',
        'elok': '08',
        'elok.': '08',
        'syys': '09',
        'syys.': '09',
        'loka': '10',
        'loka.': '10',
        'marras': '11',
        'marras.': '11',
        'joulu': '12',
        'joulu.': '12'
    }
    
    # Function to convert Finnish date format to ISO format
    def convert_date_to_iso(finnish_date):
        try:
            # Extract day, month, and year from the Finnish date format
            # Example: "11. heinäk. 2025" -> day=11, month=heinäk, year=2025
            parts = finnish_date.split()
            if len(parts) != 3:
                return "Unknown Date"
            
            day = parts[0].replace('.', '').strip().zfill(2)  # Ensure 2 digits with leading zero if needed
            month_name = parts[1].lower()
            year = parts[2].strip()
            
            # Get the month number from the mapping
            month = None
            for key, value in finnish_months.items():
                if month_name.startswith(key):
                    month = value
                    break
            
            if not month:
                return "Unknown Date"
            
            # Format as ISO date with default time 08:00
            return f"{year}-{month}-{day} 08:00"
        except Exception as e:
            print(f"Error converting date: {e}")
            return "Unknown Date"
    
    # List to store all events
    events = []
    
    # Process each known event
    for event_name in known_events:
        print(f"\nLooking for event: {event_name}")
        
        # Find the event in the HTML
        if event_name not in html_content:
            print(f"Event not found in HTML: {event_name}")
            continue
        
        # Extract event information based on the specific HTML structure
        try:
            # Get the section of HTML that contains the event
            event_start_index = html_content.find(event_name)
            event_section = html_content[event_start_index:event_start_index + 5000]
            
            # Extract event type (MAANTIE, GRAVEL, MTB)
            event_type = "Unknown"
            
            # Pattern for event type as seen in Saimaa Cycle Tour example
            type_pattern = r'class="wixui-rich-text__text"><span class="color_42 wixui-rich-text__text">(.*?)</span></span></p>'
            type_match = re.search(type_pattern, event_section)
            
            if type_match:
                event_type = type_match.group(1).strip()
            else:
                # Try alternative patterns
                if 'MTB' in event_name:
                    event_type = "MTB"
                elif 'Gravel' in event_name or 'GRVL' in event_name:
                    event_type = "GRAVEL"
                elif 'Road' in event_name:
                    event_type = "MAANTIE"
            
            # Extract event location
            event_location = "Unknown Location"
            
            # Pattern for location as seen in Saimaa Cycle Tour example
            location_pattern = r'class="wixui-rich-text__text">([A-Za-z\-,\s]+)</span></span></p></div>'
            location_match = re.search(location_pattern, event_section)
            
            if location_match:
                event_location = location_match.group(1).strip()
            
            # Extract event date
            event_date = "Unknown Date"
            
            # Pattern for date as seen in Saimaa Cycle Tour example
            date_pattern = r'class="color_42 wixui-rich-text__text">(\d{1,2}\.\s+\w+\.\s+\d{4})</span>'
            date_match = re.search(date_pattern, event_section)
            
            if date_match:
                finnish_date = date_match.group(1).strip()
                event_date = convert_date_to_iso(finnish_date)
            else:
                # Try a more general date pattern
                date_pattern = r'(\d{1,2}\.\s+\w+\.\s+\d{4})'
                date_match = re.search(date_pattern, event_section)
                if date_match:
                    finnish_date = date_match.group(1).strip()
                    event_date = convert_date_to_iso(finnish_date)
            
            # Extract event description
            event_description = ""
            
            # Pattern for description as seen in Saimaa Cycle Tour example
            desc_pattern = r'<span class="color_25 wixui-rich-text__text">(.*?)</span></p></div>'
            desc_match = re.search(desc_pattern, event_section)
            
            if desc_match:
                event_description = desc_match.group(1).strip()
                # Only use the description if it's long enough and contains the event name
                if len(event_description) < 50 or event_name not in event_description:
                    # Try another pattern
                    desc_pattern2 = r'<p class="font_9 wixui-rich-text__text"[^>]*><span class="color_25 wixui-rich-text__text">(.*?)</span></p>'
                    desc_match2 = re.search(desc_pattern2, event_section)
                    if desc_match2:
                        event_description = desc_match2.group(1).strip()
            
            # Clean up the description - remove HTML tags
            if event_description:
                # Use BeautifulSoup to parse and clean the HTML
                soup = BeautifulSoup(f"<p>{event_description}</p>", 'html.parser')
                event_description = soup.get_text()
            
            # Extract event link
            event_link = ""
            
            # Pattern for link as seen in Saimaa Cycle Tour example
            link_pattern = r'href="(https?://[^"]+)"'
            link_matches = re.findall(link_pattern, event_section)
            
            if link_matches:
                for link in link_matches:
                    if 'bikeland.fi' not in link and 'wix' not in link:
                        event_link = link
                        break
            
            # Add the event to the list
            events.append({
                'name': event_name,
                'type': event_type,
                'datetime': event_date,
                'location': event_location,
                'description': event_description,
                'link': event_link
            })
            
            print(f"Added event: {event_name} ({event_type}) on {event_date} at {event_location}")
            if event_link:
                print(f"Link: {event_link}")
            if event_description:
                print(f"Description: {event_description[:100]}...")
            
        except Exception as e:
            print(f"Error processing event {event_name}: {e}")
    
    print(f"\nFound {len(events)} events")
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Create the template file
    with open('output/datetime_bikeland_events.txt', 'w', encoding='utf-8') as f:
        for event in events:
            event_link_text = f"Lisätietoja: {event['link']}" if event['link'] else ""
            
            # Create a clean description without repeating the location
            clean_description = ""
            if event['description'] and event['location'] in event['description']:
                # Remove the location from the description to avoid repetition
                clean_description = event['description'].replace(event['location'], "").strip()
            else:
                clean_description = event['description']
            
            template = f"""/create 
title: {event['name']} ({event['type']})
channel: #ulkotapahtumat_listaus  
datetime: {event['datetime']}   
description: {event['name']} on {event['datetime']} at {event['location']} {clean_description}  {event_link_text}

💡 **Ohjeet:** Klikkaa haluamaasi emojia ilmoittaaksesi osallistumisesi tai kiinnostuksesi. Emojin valinnan jälkeen sivupalkkiin avautuu chätti, jossa voit keskustella muiden osallistujien kanssa. 

"""
            f.write(template)
            f.write("\n---\n\n")  # Separator between events
    
    print("Template file created: output/datetime_bikeland_events.txt")

if __name__ == "__main__":
    parse_bikeland_events() 