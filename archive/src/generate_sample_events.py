import os
import random
from datetime import datetime, timedelta

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Sample event types
event_types = [
    "MTB XCM", "MTB XCO", "MTB Enduro", "MTB Marathon", "MTB Downhill",
    "Gravel", "GRAVEL", "Maantie", "MAANTIE", "Cyclocross",
    "Tempo", "Triathlon", "Duathlon", "Fatbike", "Bikepacking"
]

# Sample locations in Finland
locations = [
    "Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu",
    "Turku", "Jyväskylä", "Lahti", "Kuopio", "Pori",
    "Kouvola", "Joensuu", "Lappeenranta", "Hämeenlinna", "Vaasa",
    "Seinäjoki", "Rovaniemi", "Mikkeli", "Kotka", "Salo",
    "Porvoo", "Kokkola", "Lohja", "Hyvinkää", "Nurmijärvi",
    "Järvenpää", "Rauma", "Kajaani", "Tuusula", "Kirkkonummi",
    "Kerava", "Nokia", "Ylöjärvi", "Kaarina", "Kangasala",
    "Riihimäki", "Vihti", "Imatra", "Savonlinna", "Raisio"
]

# Sample organizers
organizers = [
    "JYPS", "HePo", "TWD", "Cycle Club Helsinki", "Pyöräilyunioni",
    "Fillari-lehti", "Gravel Grinding Finland", "Bike Shop Events",
    "Pyörä-Torppa", "Pyöräilykuntien verkosto", "Suomen Latu",
    "Helsingin Triathlon", "Vantaan Pyöräilijät", "Espoon Pyöräilijät",
    "Tampereen Pyöräilijät", "Turun Urheiluliitto", "Ounaksen Pyörä-Pojat"
]

# Generate random date between March and October 2025
def random_date():
    start_date = datetime(2025, 3, 1)
    end_date = datetime(2025, 10, 31)
    delta = end_date - start_date
    random_days = random.randrange(delta.days)
    event_date = start_date + timedelta(days=random_days)
    # Most events are on weekends
    if random.random() < 0.7:  # 70% chance for weekend
        # Adjust to nearest Saturday or Sunday
        weekday = event_date.weekday()
        if weekday < 5:  # Monday to Friday
            event_date += timedelta(days=(5 - weekday))  # Move to Saturday
    return event_date

# Generate a random event
def generate_event(index):
    event_date = random_date()
    event_type = random.choice(event_types)
    location = random.choice(locations)
    organizer = random.choice(organizers)
    
    # Generate event name
    name_types = [
        f"{location} {event_type}",
        f"{organizer} {event_type}",
        f"{location} Pyöräilytapahtuma",
        f"Tour de {location}",
        f"{location} Cycling Festival",
        f"{organizer} Cycling Challenge",
        f"{location} {random.choice(['Classic', 'Cup', 'Race', 'Challenge', 'Tour'])}"
    ]
    event_name = random.choice(name_types)
    
    # Format date in Finnish style
    date_fi = event_date.strftime("%d.%m.%Y")
    
    # Generate description
    description = f"{event_name} järjestetään {date_fi} paikkakunnalla {location}. "
    description += f"Järjestäjänä toimii {organizer}. "
    
    # Add random details
    details = [
        f"Tapahtuma on suunnattu kaikentasoisille pyöräilijöille.",
        f"Tapahtumassa on useita eri pituisia reittejä.",
        f"Tapahtuma on osa {random.choice(['Suomen Cup', 'Gravel Cup', 'MTB Cup', 'Maantiecup'])} -sarjaa.",
        f"Tapahtumassa on tarjolla huoltopalvelut ja ruokailu.",
        f"Ilmoittautuminen tapahtumaan alkaa kaksi kuukautta ennen tapahtumaa.",
        f"Osallistumismaksu on {random.randint(20, 80)} euroa."
    ]
    description += random.choice(details) + " "
    
    # Add link
    description += f"Lisätietoja tapahtumasta: https://example.com/events/{index}"
    
    # Format the event
    event = f"""/create 
title: {event_name} ({event_type})
channel: #ulkotapahtumat_listaus  
datetime: {event_date.strftime('%Y-%m-%d %H:%M')}   
description: {description}

💡 **Ohjeet:** Klikkaa haluamaasi emojia ilmoittaaksesi osallistumisesi tai kiinnostuksesi. Emojin valinnan jälkeen sivupalkkiin avautuu chätti, jossa voit keskustella muiden osallistujien kanssa. 
---
"""
    return event

# Generate 50 sample events
def generate_sample_events(num_events=50):
    events = []
    for i in range(num_events):
        events.append(generate_event(i+1))
    
    # Sort events by date
    events.sort(key=lambda x: x.split('datetime: ')[1].split('\n')[0])
    
    # Write to file
    with open('output/clean_combined_events.txt', 'w', encoding='utf-8') as f:
        f.write(''.join(events))
    
    print(f"Generated {num_events} sample events in output/clean_combined_events.txt")

if __name__ == "__main__":
    generate_sample_events(50) 