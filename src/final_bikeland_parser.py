import re
from bs4 import BeautifulSoup
import json

def parse_bikeland_events():
    print("Parsing Bikeland events with the specific HTML structure for Saimaa Cycle Tour...")
    
    # Read the HTML file
    with open('bikeland_response.html', 'r', encoding='utf-8') as f:
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
            location_pattern = r'class="wixui-rich-text__text">([A-Za-z]+)</span></span></p></div>'
            location_match = re.search(location_pattern, event_section)
            
            if location_match:
                event_location = location_match.group(1).strip()
            
            # Extract event date
            event_date = "Unknown Date"
            
            # Pattern for date as seen in Saimaa Cycle Tour example
            date_pattern = r'class="color_42 wixui-rich-text__text">(\d{1,2}\.\s+\w+\.\s+\d{4})</span>'
            date_match = re.search(date_pattern, event_section)
            
            if date_match:
                event_date = date_match.group(1).strip()
            else:
                # Try a more general date pattern
                date_pattern = r'(\d{1,2}\.\s+\w+\.\s+\d{4})'
                date_match = re.search(date_pattern, event_section)
                if date_match:
                    event_date = date_match.group(1).strip()
            
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
    
    # Create the template file
    with open('final_bikeland_events.txt', 'w', encoding='utf-8') as f:
        for event in events:
            event_link_text = f"Lisätietoja: {event['link']}" if event['link'] else ""
            
            template = f"""/create 
title: {event['name']} ({event['type']})
channel: #ulkotapahtumat_listaus  
datetime: {event['datetime']}   
description: {event['name']} on {event['datetime']} at {event['location']} {event['description']}  {event_link_text}

💡 **Ohjeet:** Klikkaa haluamaasi emojia ilmoittaaksesi osallistumisesi tai kiinnostuksesi. Emojin valinnan jälkeen sivupalkkiin avautuu chätti, jossa voit keskustella muiden osallistujien kanssa. 

"""
            f.write(template)
            f.write("\n---\n\n")  # Separator between events
    
    print("Template file created: final_bikeland_events.txt")

if __name__ == "__main__":
    parse_bikeland_events() 