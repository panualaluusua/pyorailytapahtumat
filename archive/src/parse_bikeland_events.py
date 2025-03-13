import re
from bs4 import BeautifulSoup
import json
from datetime import datetime

def parse_bikeland_events():
    print("Parsing Bikeland events from HTML...")
    
    # Read the HTML file
    with open('bikeland_response.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # List to store all events
    events = []
    
    # Find all event containers - based on the example HTML structure
    # Look for h5 elements that might contain event names
    event_name_elements = soup.find_all(['h5', 'h3', 'h4'])
    
    print(f"Found {len(event_name_elements)} potential event name elements")
    
    for name_elem in event_name_elements:
        try:
            # Extract event name
            event_name_text = name_elem.get_text(strip=True)
            
            if not event_name_text or len(event_name_text) < 3:
                continue
                
            print(f"\nProcessing potential event: {event_name_text}")
            
            # Get the parent container that might contain all event information
            parent_container = name_elem.parent
            while parent_container and parent_container.name not in ['div', 'article', 'section']:
                parent_container = parent_container.parent
                
            if not parent_container:
                continue
                
            # Look for event type (MAANTIE, GRAVEL, MTB)
            event_type = "Unknown"
            type_pattern = re.compile(r'(MAANTIE|GRAVEL|MTB)', re.IGNORECASE)
            type_elements = parent_container.find_all(text=type_pattern)
            
            if type_elements:
                event_type = type_elements[0].strip()
            else:
                # Try to determine type from event name
                if 'MTB' in event_name_text:
                    event_type = "MTB"
                elif 'Gravel' in event_name_text or 'GRVL' in event_name_text:
                    event_type = "GRAVEL"
                elif 'Road' in event_name_text or 'Maantie' in event_name_text:
                    event_type = "MAANTIE"
            
            # Look for event date
            event_date = "Unknown Date"
            # Finnish date format pattern (e.g., "11. heinäk. 2025")
            date_pattern = re.compile(r'\d{1,2}\.\s+\w+\.\s+\d{4}')
            date_elements = parent_container.find_all(text=date_pattern)
            
            if date_elements:
                event_date = date_elements[0].strip()
            
            # Look for event location
            event_location = "Unknown Location"
            # Common Finnish locations
            locations = ["Helsinki", "Espoo", "Tampere", "Oulu", "Turku", "Jyväskylä", 
                         "Lahti", "Kuopio", "Kouvola", "Pori", "Joensuu", "Lappeenranta",
                         "Hämeenlinna", "Vaasa", "Seinäjoki", "Rovaniemi", "Mikkeli", 
                         "Kotka", "Salo", "Porvoo", "Lohja", "Nuorgam", "Utsjoki", "Posio",
                         "Sipoo", "Anttola", "Koli", "Saariselkä", "Vuokatti", "Kainuu",
                         "Rukatunturi", "Syöte", "Sappee", "Imatra", "Kiuruvesi", "Tuusula"]
            
            location_pattern = re.compile('|'.join(locations), re.IGNORECASE)
            location_elements = parent_container.find_all(text=location_pattern)
            
            if location_elements:
                event_location = location_elements[0].strip()
            
            # Look for event description
            event_description = ""
            # Find paragraphs that might contain descriptions
            p_elements = parent_container.find_all('p')
            
            for p in p_elements:
                p_text = p.get_text(strip=True)
                if len(p_text) > 50 and event_name_text in p_text:
                    event_description = p_text
                    break
            
            # Look for event link
            event_link = ""
            link_elements = parent_container.find_all('a', href=True)
            
            for link in link_elements:
                href = link.get('href', '')
                if href and 'http' in href and not href.endswith('.fi/tapahtumat'):
                    event_link = href
                    break
            
            # Only add events with a valid name and at least some information
            if event_name_text and (event_type != "Unknown" or event_date != "Unknown Date" or event_location != "Unknown Location"):
                events.append({
                    'name': event_name_text,
                    'type': event_type,
                    'datetime': event_date,
                    'location': event_location,
                    'description': event_description,
                    'link': event_link
                })
                print(f"Added event: {event_name_text} ({event_type}) on {event_date} at {event_location}")
            
        except Exception as e:
            print(f"Error processing event: {e}")
    
    # Remove duplicates based on event name
    unique_events = []
    seen_names = set()
    
    for event in events:
        if event['name'] not in seen_names:
            seen_names.add(event['name'])
            unique_events.append(event)
    
    print(f"\nFound {len(unique_events)} unique events")
    
    # Create the template file
    with open('parsed_bikeland_events.txt', 'w', encoding='utf-8') as f:
        for event in unique_events:
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
    
    print("Template file created: parsed_bikeland_events.txt")

if __name__ == "__main__":
    parse_bikeland_events() 