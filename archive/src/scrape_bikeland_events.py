import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import locale
import time
import os

# Set locale to Finnish for date parsing
try:
    locale.setlocale(locale.LC_TIME, 'fi_FI.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'fi_FI')
    except:
        print("Warning: Could not set Finnish locale, date parsing might not work correctly")

def scrape_bikeland_events():
    url = "https://www.bikeland.fi/tapahtumat"
    
    print(f"Fetching URL: {url}")
    
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Response status code: {response.status_code}")
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Save the HTML content to a file for debugging
        with open('data/bikeland_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print(f"Saved response HTML to data/bikeland_response.html")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the website: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Print the title of the page to verify we got the right content
    page_title = soup.title.text if soup.title else "No title found"
    print(f"Page title: {page_title}")
    
    events = []
    
    # Try different selectors to find event containers
    event_containers = []
    
    # Method 1: Look for div with event-container class
    containers1 = soup.find_all('div', class_=lambda c: c and 'event' in c.lower())
    if containers1:
        print(f"Found {len(containers1)} containers using method 1")
        event_containers = containers1
    
    # Method 2: Look for article or div elements that might contain events
    if not event_containers:
        containers2 = soup.find_all(['article', 'div'], class_=lambda c: c and ('event' in c.lower() or 'tapahtuma' in c.lower()))
        if containers2:
            print(f"Found {len(containers2)} containers using method 2")
            event_containers = containers2
    
    # Method 3: Look for any elements with date-like content
    if not event_containers:
        date_pattern = re.compile(r'\d{1,2}\.\d{1,2}\.\d{4}')
        containers3 = [elem.parent for elem in soup.find_all(text=date_pattern)]
        if containers3:
            print(f"Found {len(containers3)} containers using method 3")
            event_containers = containers3
    
    print(f"Total event containers found: {len(event_containers)}")
    
    # If no events found using the above methods, try a more generic approach
    if not event_containers:
        print("No event containers found with specific selectors. Trying a more generic approach...")
        
        # Look for sections or divs that might contain event information
        sections = soup.find_all(['section', 'div'], class_=lambda c: c and ('content' in c.lower() or 'main' in c.lower()))
        
        for section in sections:
            # Print the section's class for debugging
            if 'class' in section.attrs:
                print(f"Examining section with class: {section['class']}")
            
            # Look for potential event elements within this section
            potential_events = section.find_all(['div', 'article'], recursive=True)
            
            for potential_event in potential_events:
                # Check if this element has enough text content to be an event
                text_content = potential_event.get_text(strip=True)
                if len(text_content) > 100:  # Arbitrary threshold
                    event_containers.append(potential_event)
        
        print(f"Found {len(event_containers)} potential event containers using generic approach")
    
    # Manual extraction based on HTML structure
    if not event_containers:
        print("Attempting manual extraction based on common HTML patterns...")
        
        # Try to find all h2, h3, or h4 elements that might be event titles
        potential_titles = soup.find_all(['h2', 'h3', 'h4'])
        
        for title_elem in potential_titles:
            title_text = title_elem.get_text(strip=True)
            if title_text and len(title_text) > 3:  # Arbitrary minimum length for a title
                print(f"Potential event title found: {title_text}")
                
                # Look for date-like text near this title
                parent = title_elem.parent
                date_text = None
                
                # Search for date patterns in the siblings or children of the parent
                date_pattern = re.compile(r'\d{1,2}\.\d{1,2}\.\d{4}')
                date_matches = parent.find_all(text=date_pattern)
                
                if date_matches:
                    date_text = date_matches[0].strip()
                    print(f"  - Date found: {date_text}")
                    
                    # Create a simple event object
                    events.append({
                        'name': title_text,
                        'type': "Unknown",  # We don't know the type
                        'datetime': date_text,
                        'location': "Unknown Location",  # We don't know the location
                        'description': "",  # No description
                        'link': ""  # No link
                    })
    
    # Process the event containers if any were found
    for i, container in enumerate(event_containers):
        try:
            print(f"\nProcessing event container {i+1}:")
            
            # Print the HTML of the container for debugging
            container_html = str(container)[:200] + "..." if len(str(container)) > 200 else str(container)
            print(f"Container HTML snippet: {container_html}")
            
            # Extract event name - look for headings or strong text
            event_name_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])
            event_name = event_name_elem.text.strip() if event_name_elem else "Unknown Event"
            print(f"Event name: {event_name}")
            
            # Extract event type - look for specific class or pattern
            event_type = "Unknown"
            type_candidates = container.find_all(['span', 'div'], class_=lambda c: c and ('type' in c.lower() or 'category' in c.lower()))
            if type_candidates:
                event_type = type_candidates[0].text.strip()
            else:
                # Look for common event types in the text
                text = container.get_text().lower()
                if 'mtb' in text:
                    event_type = "MTB"
                elif 'gravel' in text:
                    event_type = "GRAVEL"
                elif 'maantie' in text:
                    event_type = "MAANTIE"
            print(f"Event type: {event_type}")
            
            # Extract event date - look for date patterns
            event_date_text = "Unknown Date"
            date_pattern = re.compile(r'\d{1,2}\.\d{1,2}\.\d{4}')
            date_matches = container.find_all(text=date_pattern)
            if date_matches:
                event_date_text = date_matches[0].strip()
            print(f"Event date: {event_date_text}")
            
            # Extract event location
            event_location = "Unknown Location"
            location_candidates = container.find_all(['span', 'div'], class_=lambda c: c and ('location' in c.lower() or 'place' in c.lower()))
            if location_candidates:
                event_location = location_candidates[0].text.strip()
            print(f"Event location: {event_location}")
            
            # Extract event description
            event_description = ""
            desc_candidates = container.find_all(['p', 'div'], class_=lambda c: c and ('description' in c.lower() or 'content' in c.lower()))
            if desc_candidates:
                event_description = desc_candidates[0].text.strip()
            print(f"Event description: {event_description[:50]}..." if len(event_description) > 50 else f"Event description: {event_description}")
            
            # Extract event link
            event_link = ""
            link_elem = container.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if not href.startswith('http'):
                    # Convert relative URL to absolute
                    if href.startswith('/'):
                        event_link = f"https://www.bikeland.fi{href}"
                    else:
                        event_link = f"https://www.bikeland.fi/{href}"
                else:
                    event_link = href
            print(f"Event link: {event_link}")
            
            events.append({
                'name': event_name,
                'type': event_type,
                'datetime': event_date_text,
                'location': event_location,
                'description': event_description,
                'link': event_link
            })
            
        except Exception as e:
            print(f"Error processing event container {i+1}: {e}")
    
    print(f"\nTotal events extracted: {len(events)}")
    return events

def create_template_file(events):
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    with open('output/bikeland_events.txt', 'w', encoding='utf-8') as f:
        for i, event in enumerate(events):
            print(f"Writing event {i+1} to file: {event['name']}")
            
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
    
    print(f"Template file created: output/bikeland_events.txt")

def main():
    print("Starting Bikeland event scraper...")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    events = scrape_bikeland_events()
    
    if events:
        print(f"\nFound {len(events)} events. Creating template file...")
        create_template_file(events)
        print("Done! Check output/bikeland_events.txt for the results.")
    else:
        print("\nNo events found or there was an error scraping the website.")

if __name__ == "__main__":
    main() 