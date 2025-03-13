import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import difflib
import shutil

# Set page config
st.set_page_config(
    page_title="Pyöräilytapahtumat - Hallintapaneeli",
    page_icon="🚲",
    layout="wide"
)

# Constants
DATA_DIR = 'data'
EVENTS_FILE = os.path.join(DATA_DIR, 'all_events.json')
BLACKLIST_FILE = os.path.join(DATA_DIR, 'event_blacklist.json')

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize blacklist if it doesn't exist
if not os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

# Load events from JSON file
@st.cache_data
def load_events():
    try:
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            events = json.load(f)
        return events
    except Exception as e:
        st.error(f"Error loading events: {e}")
        return []

# Load blacklisted event IDs
def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
            blacklist = json.load(f)
        return blacklist
    except Exception as e:
        st.error(f"Error loading blacklist: {e}")
        return []

# Save events to JSON file
def save_events(events):
    # Create a backup first
    if os.path.exists(EVENTS_FILE):
        backup_file = f"{EVENTS_FILE}.bak"
        shutil.copy2(EVENTS_FILE, backup_file)
    
    try:
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving events: {e}")
        return False

# Save blacklist to JSON file
def save_blacklist(blacklist_to_save):
    """Save blacklisted event IDs to file"""
    try:
        # Load existing blacklist if it exists
        existing_blacklist = []
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                existing_blacklist = json.load(f)
        
        # If we're adding a few events to the blacklist
        if isinstance(blacklist_to_save, list) and len(blacklist_to_save) < 10:
            # Merge with existing blacklist and remove duplicates
            combined_blacklist = list(set(existing_blacklist + blacklist_to_save))
        else:
            # We're replacing the entire blacklist
            combined_blacklist = blacklist_to_save
            
        # Save the combined blacklist
        with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(combined_blacklist, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Virhe tallennettaessa estolistaa: {e}")
        return False

# Find exact duplicates
def find_exact_duplicates(events):
    event_dict = {}
    exact_duplicates = []
    
    for i, event in enumerate(events):
        if 'title' in event and 'datetime' in event:
            event_id = f"{event['title']}_{event['datetime'].split()[0]}"
            
            if event_id in event_dict:
                exact_duplicates.append({
                    'event_id': event_id,
                    'original_idx': event_dict[event_id],
                    'duplicate_idx': i
                })
            else:
                event_dict[event_id] = i
    
    return exact_duplicates

# Find similar events
def find_similar_events(events, threshold=0.8):
    similar_pairs = []
    
    for i, event1 in enumerate(events):
        for j, event2 in enumerate(events[i+1:], i+1):
            if 'title' in event1 and 'title' in event2:
                # Skip if dates are the same (these would be caught by exact duplicates)
                date1 = event1.get('datetime', '').split()[0]
                date2 = event2.get('datetime', '').split()[0]
                if date1 == date2:
                    continue
                
                # Calculate similarity
                similarity = difflib.SequenceMatcher(None, 
                                                    event1['title'].lower(), 
                                                    event2['title'].lower()).ratio()
                
                if similarity >= threshold:
                    similar_pairs.append({
                        'similarity': similarity,
                        'idx1': i,
                        'idx2': j
                    })
    
    # Sort by similarity (highest first)
    similar_pairs.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_pairs

# Find events at the same location on the same day
def find_same_location_date(events):
    date_location_dict = {}
    same_location_date = []
    
    for i, event in enumerate(events):
        if 'datetime' in event and 'location' in event:
            date = event.get('datetime', '').split()[0]
            location = event.get('location', '')
            
            if date and location:
                key = f"{date}_{location}"
                
                if key in date_location_dict:
                    date_location_dict[key].append(i)
                else:
                    date_location_dict[key] = [i]
    
    for key, indices in date_location_dict.items():
        if len(indices) > 1:
            date, location = key.split('_', 1)
            same_location_date.append({
                'date': date,
                'location': location,
                'indices': indices
            })
    
    return same_location_date

# Create a unique event ID
def create_event_id(event):
    """Create a unique ID for an event based on title and date"""
    if 'title' in event and 'datetime' in event:
        date_part = event['datetime'].split()[0] if ' ' in event['datetime'] else event['datetime']
        return f"{event['title']}_{date_part}"
    return None

# Main function
def main():
    st.title("🚲 Pyöräilytapahtumat - Hallintapaneeli")
    
    # Load data
    events = load_events()
    blacklist = load_blacklist()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Kaikki tapahtumat", 
        "Duplikaatit", 
        "Samankaltaiset tapahtumat",
        "Tapahtumat samassa paikassa"
    ])
    
    # Tab 1: All events
    with tab1:
        st.header("Kaikki tapahtumat")
        
        # Convert to DataFrame for easier display
        df = pd.DataFrame(events)
        
        # Add a column for event ID
        df['event_id'] = df.apply(lambda row: create_event_id(row), axis=1)
        
        # Mark blacklisted events
        df['blacklisted'] = df['event_id'].apply(lambda x: x in blacklist)
        
        # Filter options
        st.subheader("Suodata tapahtumia")
        
        # Add search functionality
        search_query = st.text_input("Hae tapahtumia (nimi, järjestäjä, kuvaus)", "")
        
        # Finnish month names
        finnish_months = {
            1: "Tammikuu",
            2: "Helmikuu",
            3: "Maaliskuu",
            4: "Huhtikuu",
            5: "Toukokuu",
            6: "Kesäkuu",
            7: "Heinäkuu",
            8: "Elokuu",
            9: "Syyskuu",
            10: "Lokakuu",
            11: "Marraskuu",
            12: "Joulukuu"
        }
        
        # Filter by month
        months = ["Kaikki"]
        month_mapping = {}  # To store mapping between display name and month number
        
        for event in events:
            if 'datetime' in event and event['datetime']:
                try:
                    date_parts = event['datetime'].split()
                    if len(date_parts) > 0:
                        date_str = date_parts[0]
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        month_num = date_obj.month
                        year = date_obj.year
                        month_name = f"{finnish_months[month_num]} {year}"
                        
                        if month_name not in months:
                            months.append(month_name)
                            month_mapping[month_name] = (month_num, year)
                except Exception as e:
                    pass
        
        # Sort months chronologically
        sorted_months = ["Kaikki"] + sorted(
            [m for m in months if m != "Kaikki"],
            key=lambda x: (month_mapping[x][1], month_mapping[x][0])
        )
        
        selected_month = st.selectbox("Kuukausi", sorted_months)
        
        # Filter by type
        types = ["Kaikki"] + sorted(list(set(event.get('type', '') for event in events if 'type' in event and event.get('type', ''))))
        selected_type = st.selectbox("Tapahtumatyyppi", types)
        
        # Filter by location
        locations = ["Kaikki"] + sorted(list(set(event.get('location', '') for event in events if 'location' in event and event.get('location', ''))))
        selected_location = st.selectbox("Paikkakunta", locations)
        
        # Filter by source
        sources = ["Kaikki"] + sorted(list(set(event.get('source', '') for event in events if 'source' in event and event.get('source', ''))))
        selected_source = st.selectbox("Lähde", sources)
        
        # Filter by blacklist status
        show_blacklisted = st.checkbox("Näytä myös estetyt tapahtumat", value=False)
        
        # Apply filters
        filtered_df = df.copy()
        
        # Apply search filter
        if search_query:
            search_query = search_query.lower()
            
            # Varmistetaan, että kaikki sarakkeet ovat olemassa ja käsitellään puuttuvat arvot
            for col in ['title', 'organizer', 'description']:
                if col not in filtered_df.columns:
                    filtered_df[col] = ""
                filtered_df[col] = filtered_df[col].fillna("")
            
            filtered_df = filtered_df[
                filtered_df['title'].str.lower().str.contains(search_query, na=False) |
                filtered_df['organizer'].str.lower().str.contains(search_query, na=False) |
                filtered_df['description'].str.lower().str.contains(search_query, na=False)
            ]
        
        # Apply month filter
        if selected_month != "Kaikki":
            month_num, year = month_mapping[selected_month]
            
            def match_month_year(datetime_str):
                try:
                    if not isinstance(datetime_str, str) or not datetime_str:
                        return False
                    
                    date_parts = datetime_str.split()
                    if len(date_parts) == 0:
                        return False
                        
                    date_str = date_parts[0]
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    return date_obj.month == month_num and date_obj.year == year
                except:
                    return False
            
            filtered_df = filtered_df[filtered_df['datetime'].apply(match_month_year)]
        
        # Apply other filters
        if selected_type != "Kaikki":
            filtered_df = filtered_df[filtered_df['type'] == selected_type]
        
        if selected_location != "Kaikki":
            filtered_df = filtered_df[filtered_df['location'] == selected_location]
        
        if selected_source != "Kaikki":
            filtered_df = filtered_df[filtered_df['source'] == selected_source]
        
        if not show_blacklisted:
            filtered_df = filtered_df[~filtered_df['blacklisted']]
        
        # Display filtered events
        st.subheader(f"Tapahtumat ({len(filtered_df)} / {len(df)})")
        
        # Select columns to display
        display_columns = ['title', 'type', 'datetime', 'location', 'source', 'blacklisted']
        
        if not filtered_df.empty:
            # Display as table with selection
            selected_indices = []
            
            for i, row in filtered_df.iterrows():
                col1, col2 = st.columns([0.9, 0.1])
                
                with col1:
                    expander = st.expander(f"{row['title']} - {row['datetime'].split()[0]} - {row['location']}")
                    with expander:
                        st.write(f"**Tyyppi:** {row.get('type', 'Ei tiedossa')}")
                        st.write(f"**Päivämäärä:** {row.get('datetime', 'Ei tiedossa').split()[0]}")
                        st.write(f"**Paikkakunta:** {row.get('location', 'Ei tiedossa')}")
                        st.write(f"**Järjestäjä:** {row.get('organizer', 'Ei tiedossa')}")
                        st.write(f"**Lähde:** {row.get('source', 'Ei tiedossa')}")
                        
                        if 'link' in row and row['link']:
                            st.write(f"**Linkki:** [{row['link']}]({row['link']})")
                        
                        if 'description' in row and row['description']:
                            st.write(f"**Kuvaus:** {row['description']}")
                        
                        # Edit event button
                        if st.button(f"Muokkaa tapahtumaa", key=f"edit_{i}"):
                            st.session_state.editing_event = i
                            st.session_state.event_data = events[i].copy()
                
                with col2:
                    # Blacklist/whitelist button
                    event_id = row['event_id']
                    if event_id in blacklist:
                        if st.button("✅", key=f"unbl_{i}", help="Poista estosta"):
                            # Create a new blacklist without this event
                            new_blacklist = [e for e in blacklist if e != event_id]
                            save_blacklist(new_blacklist)
                            st.rerun()
                    else:
                        if st.button("❌", key=f"bl_{i}", help="Estä tapahtuma"):
                            # Add to blacklist
                            save_blacklist([event_id])
                            st.rerun()
        else:
            st.warning("Ei tapahtumia valituilla suodattimilla.")
        
        # Event editing form
        if 'editing_event' in st.session_state:
            st.subheader("Muokkaa tapahtumaa")
            
            with st.form("edit_event_form"):
                idx = st.session_state.editing_event
                event = st.session_state.event_data
                
                title = st.text_input("Otsikko", value=event.get('title', ''))
                event_type = st.text_input("Tyyppi", value=event.get('type', ''))
                date_str = event.get('datetime', '').split()[0] if 'datetime' in event else ''
                date = st.date_input("Päivämäärä", 
                                    value=datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now())
                location = st.text_input("Paikkakunta", value=event.get('location', ''))
                organizer = st.text_input("Järjestäjä", value=event.get('organizer', ''))
                link = st.text_input("Linkki", value=event.get('link', ''))
                description = st.text_area("Kuvaus", value=event.get('description', ''))
                
                submitted = st.form_submit_button("Tallenna muutokset")
                cancel = st.form_submit_button("Peruuta")
                
                if submitted:
                    # Update event data
                    events[idx]['title'] = title
                    events[idx]['type'] = event_type
                    events[idx]['datetime'] = f"{date.strftime('%Y-%m-%d')} 08:00"
                    events[idx]['location'] = location
                    events[idx]['organizer'] = organizer
                    events[idx]['link'] = link
                    events[idx]['description'] = description
                    
                    # Save changes
                    if save_events(events):
                        st.success("Tapahtuma päivitetty onnistuneesti!")
                        del st.session_state.editing_event
                        del st.session_state.event_data
                        st.rerun()
                
                if cancel:
                    del st.session_state.editing_event
                    del st.session_state.event_data
                    st.rerun()
    
    # Tab 2: Exact duplicates
    with tab2:
        st.header("Tarkat duplikaatit")
        
        exact_duplicates = find_exact_duplicates(events)
        
        if exact_duplicates:
            st.write(f"Löytyi {len(exact_duplicates)} tarkkaa duplikaattia:")
            
            for i, dup in enumerate(exact_duplicates):
                st.subheader(f"Duplikaatti #{i+1}: {dup['event_id']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Alkuperäinen tapahtuma:**")
                    original = events[dup['original_idx']]
                    st.write(f"Otsikko: {original.get('title', 'Ei tiedossa')}")
                    st.write(f"Tyyppi: {original.get('type', 'Ei tiedossa')}")
                    st.write(f"Päivämäärä: {original.get('datetime', 'Ei tiedossa').split()[0]}")
                    st.write(f"Paikkakunta: {original.get('location', 'Ei tiedossa')}")
                    st.write(f"Järjestäjä: {original.get('organizer', 'Ei tiedossa')}")
                    st.write(f"Lähde: {original.get('source', 'Ei tiedossa')}")
                
                with col2:
                    st.write("**Duplikaatti:**")
                    duplicate = events[dup['duplicate_idx']]
                    st.write(f"Otsikko: {duplicate.get('title', 'Ei tiedossa')}")
                    st.write(f"Tyyppi: {duplicate.get('type', 'Ei tiedossa')}")
                    st.write(f"Päivämäärä: {duplicate.get('datetime', 'Ei tiedossa').split()[0]}")
                    st.write(f"Paikkakunta: {duplicate.get('location', 'Ei tiedossa')}")
                    st.write(f"Järjestäjä: {duplicate.get('organizer', 'Ei tiedossa')}")
                    st.write(f"Lähde: {duplicate.get('source', 'Ei tiedossa')}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Säilytä alkuperäinen", key=f"keep_orig_{i}"):
                        # Add duplicate to blacklist
                        event_id = create_event_id(duplicate)
                        if event_id and event_id not in blacklist:
                            save_blacklist([event_id])
                            st.success("Duplikaatti estetty!")
                            st.rerun()
                
                with col2:
                    if st.button("Säilytä duplikaatti", key=f"keep_dup_{i}"):
                        # Add original to blacklist
                        event_id = create_event_id(original)
                        if event_id and event_id not in blacklist:
                            save_blacklist([event_id])
                            st.success("Alkuperäinen estetty!")
                            st.rerun()
                
                with col3:
                    if st.button("Estä molemmat", key=f"block_both_{i}"):
                        # Add both to blacklist
                        orig_id = create_event_id(original)
                        dup_id = create_event_id(duplicate)
                        
                        # Create a list of IDs to blacklist
                        ids_to_blacklist = []
                        if orig_id and orig_id not in blacklist:
                            ids_to_blacklist.append(orig_id)
                        
                        if dup_id and dup_id not in blacklist:
                            ids_to_blacklist.append(dup_id)
                        
                        if ids_to_blacklist:
                            save_blacklist(ids_to_blacklist)
                            st.success("Molemmat tapahtumat estetty!")
                            st.rerun()
                
                st.markdown("---")
        else:
            st.success("Ei tarkkoja duplikaatteja! 🎉")
    
    # Tab 3: Similar events
    with tab3:
        st.header("Samankaltaiset tapahtumat")
        
        # Similarity threshold slider
        threshold = st.slider("Samankaltaisuuskynnys", min_value=0.5, max_value=1.0, value=0.8, step=0.05)
        
        similar_events = find_similar_events(events, threshold)
        
        if similar_events:
            st.write(f"Löytyi {len(similar_events)} samankaltaista tapahtumaparia:")
            
            for i, sim in enumerate(similar_events):
                st.subheader(f"Samankaltainen pari #{i+1} (samankaltaisuus: {sim['similarity']:.2f}):")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Tapahtuma 1:**")
                    event1 = events[sim['idx1']]
                    st.write(f"Otsikko: {event1.get('title', 'Ei tiedossa')}")
                    st.write(f"Tyyppi: {event1.get('type', 'Ei tiedossa')}")
                    st.write(f"Päivämäärä: {event1.get('datetime', 'Ei tiedossa').split()[0]}")
                    st.write(f"Paikkakunta: {event1.get('location', 'Ei tiedossa')}")
                    st.write(f"Järjestäjä: {event1.get('organizer', 'Ei tiedossa')}")
                    st.write(f"Lähde: {event1.get('source', 'Ei tiedossa')}")
                
                with col2:
                    st.write("**Tapahtuma 2:**")
                    event2 = events[sim['idx2']]
                    st.write(f"Otsikko: {event2.get('title', 'Ei tiedossa')}")
                    st.write(f"Tyyppi: {event2.get('type', 'Ei tiedossa')}")
                    st.write(f"Päivämäärä: {event2.get('datetime', 'Ei tiedossa').split()[0]}")
                    st.write(f"Paikkakunta: {event2.get('location', 'Ei tiedossa')}")
                    st.write(f"Järjestäjä: {event2.get('organizer', 'Ei tiedossa')}")
                    st.write(f"Lähde: {event2.get('source', 'Ei tiedossa')}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Estä tapahtuma 1", key=f"block_1_{i}"):
                        event_id = create_event_id(event1)
                        if event_id and event_id not in blacklist:
                            save_blacklist([event_id])
                            st.success("Tapahtuma 1 estetty!")
                            st.rerun()
                
                with col2:
                    if st.button("Estä tapahtuma 2", key=f"block_2_{i}"):
                        event_id = create_event_id(event2)
                        if event_id and event_id not in blacklist:
                            save_blacklist([event_id])
                            st.success("Tapahtuma 2 estetty!")
                            st.rerun()
                
                with col3:
                    if st.button("Estä molemmat", key=f"block_both_sim_{i}"):
                        event1_id = create_event_id(event1)
                        event2_id = create_event_id(event2)
                        
                        # Create a list of IDs to blacklist
                        ids_to_blacklist = []
                        if event1_id and event1_id not in blacklist:
                            ids_to_blacklist.append(event1_id)
                        
                        if event2_id and event2_id not in blacklist:
                            ids_to_blacklist.append(event2_id)
                        
                        if ids_to_blacklist:
                            save_blacklist(ids_to_blacklist)
                            st.success("Molemmat tapahtumat estetty!")
                            st.rerun()
                
                st.markdown("---")
        else:
            st.info(f"Ei samankaltaisia tapahtumia kynnyksellä {threshold}.")
    
    # Tab 4: Same location and date
    with tab4:
        st.header("Tapahtumat samassa paikassa")
        
        same_location_date = find_same_location_date(events)
        
        if same_location_date:
            st.write(f"Löytyi {len(same_location_date)} paikkaa, joissa on useita tapahtumia samana päivänä:")
            
            for i, sld in enumerate(same_location_date):
                st.subheader(f"Paikka #{i+1}: {sld['location']} ({sld['date']})")
                st.write(f"Tapahtumien määrä: {len(sld['indices'])}")
                
                for j, idx in enumerate(sld['indices']):
                    event = events[idx]
                    
                    expander = st.expander(f"Tapahtuma {j+1}: {event.get('title', 'Ei tiedossa')}")
                    with expander:
                        st.write(f"Otsikko: {event.get('title', 'Ei tiedossa')}")
                        st.write(f"Tyyppi: {event.get('type', 'Ei tiedossa')}")
                        st.write(f"Päivämäärä: {event.get('datetime', 'Ei tiedossa').split()[0]}")
                        st.write(f"Paikkakunta: {event.get('location', 'Ei tiedossa')}")
                        st.write(f"Järjestäjä: {event.get('organizer', 'Ei tiedossa')}")
                        st.write(f"Lähde: {event.get('source', 'Ei tiedossa')}")
                        
                        # Block button
                        event_id = create_event_id(event)
                        if event_id:
                            if event_id in blacklist:
                                if st.button("Poista estosta", key=f"unblock_loc_{i}_{j}"):
                                    # Create a new blacklist without this event
                                    new_blacklist = [e for e in blacklist if e != event_id]
                                    save_blacklist(new_blacklist)
                                    st.success("Tapahtuma poistettu estosta!")
                                    st.rerun()
                            else:
                                if st.button("Estä tapahtuma", key=f"block_loc_{i}_{j}"):
                                    save_blacklist([event_id])
                                    st.success("Tapahtuma estetty!")
                                    st.rerun()
                
                st.markdown("---")
        else:
            st.info("Ei paikkoja, joissa on useita tapahtumia samana päivänä.")
    
    # Sidebar
    st.sidebar.header("Toiminnot")
    
    # Add new event button
    if st.sidebar.button("Lisää uusi tapahtuma"):
        st.session_state.adding_event = True
    
    # Add new event form
    if 'adding_event' in st.session_state and st.session_state.adding_event:
        st.sidebar.subheader("Lisää uusi tapahtuma")
        
        with st.sidebar.form("add_event_form"):
            title = st.text_input("Otsikko")
            event_type = st.text_input("Tyyppi")
            date = st.date_input("Päivämäärä")
            location = st.text_input("Paikkakunta")
            organizer = st.text_input("Järjestäjä")
            link = st.text_input("Linkki")
            description = st.text_area("Kuvaus")
            
            submitted = st.form_submit_button("Lisää tapahtuma")
            cancel = st.form_submit_button("Peruuta")
            
            if submitted:
                # Create new event
                new_event = {
                    'title': title,
                    'type': event_type,
                    'datetime': f"{date.strftime('%Y-%m-%d')} 08:00",
                    'location': location,
                    'organizer': organizer,
                    'link': link,
                    'description': description,
                    'source': 'manual'
                }
                
                # Add to events
                events.append(new_event)
                
                # Save changes
                if save_events(events):
                    st.sidebar.success("Tapahtuma lisätty onnistuneesti!")
                    st.session_state.adding_event = False
                    st.rerun()
            
            if cancel:
                st.session_state.adding_event = False
                st.rerun()
    
    # Statistics
    st.sidebar.header("Tilastot")
    st.sidebar.write(f"Tapahtumia yhteensä: {len(events)}")
    st.sidebar.write(f"Estettyjä tapahtumia: {len(blacklist)}")
    
    # Refresh button
    if st.sidebar.button("Päivitä"):
        st.rerun()
    
    # Import/Export blacklist
    st.sidebar.header("Tuo/Vie estolista")
    
    # Export blacklist
    if st.sidebar.button("Vie estolista"):
        # Convert blacklist to CSV format
        if blacklist:
            csv_string = "\n".join(blacklist)
            st.sidebar.download_button(
                label="Lataa estolista CSV-muodossa",
                data=csv_string,
                file_name="event_blacklist.csv",
                mime="text/csv"
            )
        else:
            st.sidebar.info("Estolista on tyhjä.")
    
    # Import blacklist
    uploaded_file = st.sidebar.file_uploader("Tuo estolista CSV-tiedostosta", type="csv")
    if uploaded_file is not None:
        try:
            # Read the CSV file
            imported_blacklist = []
            for line in uploaded_file:
                event_id = line.decode('utf-8').strip()
                if event_id:  # Skip empty lines
                    imported_blacklist.append(event_id)
            
            if imported_blacklist:
                # Use the save_blacklist function to merge with existing blacklist
                if save_blacklist(imported_blacklist):
                    st.sidebar.success(f"Tuotu {len(imported_blacklist)} tapahtumaa estolistalle!")
                    st.rerun()
            else:
                st.sidebar.warning("Tuotu tiedosto ei sisältänyt tapahtumia.")
        except Exception as e:
            st.sidebar.error(f"Virhe tuotaessa estolistaa: {e}")

if __name__ == "__main__":
    main() 