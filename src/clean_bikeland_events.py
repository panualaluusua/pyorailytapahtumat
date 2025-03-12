import re
import json

def clean_events():
    print("Cleaning up Bikeland events...")
    
    # Read the HTML file to extract event information directly
    with open('bikeland_response.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract event information using regex patterns
    # Look for event names
    event_names = set()
    event_data = []
    
    # Common cycling event names in Finland
    known_events = [
        "Tour De Tuusulanjärvi",
        "Gravel Primavera",
        "Nordic Gravel Series",
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
        "Dirty Sipoo",
        "Puss Weekend",
        "Luonterin pyöräily",
        "FNLD GRVL",
        "Sorahiisi",
        "Saariselkä MTB Stages",
        "Falling Leaves Lahti"
    ]
    
    # Extract event information
    for event_name in known_events:
        if event_name in html_content:
            event_names.add(event_name)
            
            # Try to find event type
            event_type = "Unknown"
            if "MTB" in event_name or "MTB" in html_content.split(event_name)[1][:100]:
                event_type = "MTB"
            elif "Gravel" in event_name or "GRVL" in event_name or "GRAVEL" in html_content.split(event_name)[1][:100]:
                event_type = "GRAVEL"
            elif "Road" in event_name or "MAANTIE" in html_content.split(event_name)[1][:100]:
                event_type = "MAANTIE"
            
            # Try to find event date
            date_pattern = r'\d{1,2}\.\d{1,2}\.\d{4}'
            date_matches = re.findall(date_pattern, html_content.split(event_name)[1][:500])
            event_date = date_matches[0] if date_matches else "Unknown Date"
            
            # Try to find event location
            location = "Unknown Location"
            
            # Try to find event link
            link_pattern = r'https?://[^\s"\'<>]+' + re.escape(event_name.lower().replace(' ', '').replace('ä', 'a').replace('ö', 'o')) + r'[^\s"\'<>]*'
            link_matches = re.findall(link_pattern, html_content.lower())
            
            if not link_matches:
                # Try a more general approach
                parts = html_content.split(event_name)
                if len(parts) > 1:
                    after_event = parts[1][:500]
                    link_pattern = r'href="(https?://[^"]+)"'
                    link_matches = re.findall(link_pattern, after_event)
            
            event_link = link_matches[0] if link_matches else ""
            
            # Clean up the link
            if event_link.startswith('href="'):
                event_link = event_link[6:-1]
            
            event_data.append({
                'name': event_name,
                'type': event_type,
                'datetime': event_date,
                'location': location,
                'description': "",
                'link': event_link
            })
    
    print(f"Found {len(event_data)} unique events")
    
    # Create a clean template file
    with open('clean_bikeland_events.txt', 'w', encoding='utf-8') as f:
        for event in event_data:
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
    
    print("Clean template file created: clean_bikeland_events.txt")

if __name__ == "__main__":
    clean_events() 