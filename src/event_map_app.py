import streamlit as st
import folium
from streamlit_folium import folium_static, st_folium
import pandas as pd
import re
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import matplotlib.pyplot as plt
import json
import time
import math
import random

# Set page config
st.set_page_config(
    page_title="Pyöräilytapahtumat Suomessa 2025",
    page_icon="🚲",
    layout="wide"
)

def sanitize_text(text):
    """Sanitize text by removing or replacing problematic characters."""
    if not isinstance(text, str):
        return text
        
    # Replace backticks with single quotes
    text = text.replace('`', "'")
    
    # Replace other potentially problematic characters
    replacements = {
        '"': '"',  # Replace fancy quotes
        '"': '"',
        ''': "'",
        ''': "'",
        '—': '-',  # Replace em dash
        '–': '-',  # Replace en dash
        '…': '...',  # Replace ellipsis
        '\u200b': '',  # Remove zero-width space
        '\xa0': ' ',  # Replace non-breaking space with regular space
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove any other control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text

# Cache the geocoding results to avoid repeated API calls
@st.cache_data
def geocode_location(location):
    """Geocode a location to get its coordinates."""
    try:
        # Add "Finland" to the location to improve geocoding accuracy
        if "Finland" not in location and "Suomi" not in location:
            search_location = f"{location}, Finland"
        else:
            search_location = location
            
        geolocator = Nominatim(user_agent="pyorailytapahtumat-app")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        location_info = geocode(search_location)
        
        if location_info:
            return (location_info.latitude, location_info.longitude)
        else:
            # Try with just the city name
            city = location.split(',')[0].strip()
            if city != location:
                location_info = geocode(f"{city}, Finland")
                if location_info:
                    return (location_info.latitude, location_info.longitude)
            
            # If still not found, use a default location (center of Finland)
            return None
    except Exception as e:
        st.error(f"Error geocoding {location}: {e}")
        return None

# Cache the event data loading
@st.cache_data(ttl=10)  # Cache expires after 10 seconds
def load_events():
    """Load events from the all_events.json file."""
    try:
        # Get file modification time
        json_file_path = 'data/all_events.json'
        if os.path.exists(json_file_path):
            mod_time = os.path.getmtime(json_file_path)
            last_updated = datetime.fromtimestamp(mod_time).strftime('%d.%m.%Y %H:%M')
        else:
            last_updated = "Tuntematon"
        
        # Load and sanitize JSON content before parsing
        with open(json_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Replace problematic characters in the raw JSON string
            content = content.replace('`', "'")
            try:
                events_data = json.loads(content)
            except json.JSONDecodeError as e:
                st.error(f"Error parsing JSON: {e}")
                return pd.DataFrame()
            
        # Additional sanitization of text fields
        for event in events_data:
            for field in ['title', 'type', 'location', 'organizer', 'description', 'link']:
                if field in event:
                    event[field] = sanitize_text(event[field])
        
        # Store last updated time in the DataFrame metadata
        df = pd.DataFrame(events_data)
        df.attrs['last_updated'] = last_updated
        
        # Finnish month names
        month_names_fi = {
            "January": "Tammikuu",
            "February": "Helmikuu",
            "March": "Maaliskuu",
            "April": "Huhtikuu",
            "May": "Toukokuu",
            "June": "Kesäkuu",
            "July": "Heinäkuu",
            "August": "Elokuu",
            "September": "Syyskuu",
            "October": "Lokakuu",
            "November": "Marraskuu",
            "December": "Joulukuu",
            "Unknown": "Tuntematon"
        }
        
        # Process date information
        df['date'] = df['datetime'].apply(lambda x: x.split()[0] if isinstance(x, str) else "Unknown")
        
        # Convert ISO dates to Finnish format and extract month
        def process_date(date_str):
            try:
                if isinstance(date_str, str) and date_str != "Unknown Date":
                    try:
                        # Try ISO format first (YYYY-MM-DD)
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        try:
                            # Try Finnish format (DD.M.YYYY or DD.MM.YYYY)
                            date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                        except ValueError:
                            # Try Finnish format with single digit month
                            date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                    
                    finnish_date = date_obj.strftime('%d.%m.%Y')
                    english_month = date_obj.strftime('%B')
                    month_fi = month_names_fi.get(english_month, english_month)
                    month_num = date_obj.month
                    return finnish_date, month_fi, month_num, date_obj
                return "Tuntematon", "Tuntematon", 0, None
            except:
                return "Tuntematon", "Tuntematon", 0, None
        
        # Apply date processing
        date_info = df['date'].apply(process_date)
        df['date'] = date_info.apply(lambda x: x[0])
        df['month'] = date_info.apply(lambda x: x[1])
        df['month_num'] = date_info.apply(lambda x: x[2])
        df['date_obj'] = date_info.apply(lambda x: x[3])
        
        # Filter out old events (events before today)
        today = datetime.now().date()
        df = df[df['date_obj'].apply(lambda x: x.date() if x is not None else today) >= today]
        
        # Drop the temporary date_obj column
        df = df.drop('date_obj', axis=1)
        
        # Add coordinates
        df['coordinates'] = df['location'].apply(geocode_location)
        
        # Filter out events with no coordinates
        df = df[df['coordinates'].notna()]
        
        # Split coordinates into latitude and longitude
        df['latitude'] = df['coordinates'].apply(lambda x: x[0] if x else None)
        df['longitude'] = df['coordinates'].apply(lambda x: x[1] if x else None)
        
        return df
    
    except Exception as e:
        st.error(f"Error reading events: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

def create_map(df, center=[65.0, 25.0], zoom=5):
    """Create a folium map with event markers."""
    try:
        m = folium.Map(location=center, zoom_start=zoom, control_scale=True)
        
        # Create a dictionary to track locations and count events at each location
        location_counts = {}
        
        # Add markers for each event
        for idx, row in df.iterrows():
            try:
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    # Create popup content with sanitized text
                    popup_content = f"""
                    <b>{sanitize_text(str(row['title']))}</b> ({sanitize_text(str(row['type']))})<br>
                    <b>Date:</b> {row['date']}<br>
                    <b>Location:</b> {sanitize_text(str(row['location']))}<br>
                    """
                    
                    if row['organizer']:
                        popup_content += f"<b>Organizer:</b> {sanitize_text(str(row['organizer']))}<br>"
                        
                    if row['link']:
                        popup_content += f"<a href='{sanitize_text(str(row['link']))}' target='_blank'>More information</a>"
                    
                    # Determine marker color based on event type
                    if 'MTB' in row['type']:
                        color = 'green'
                    elif 'Gravel' in row['type'] or 'GRAVEL' in row['type']:
                        color = 'orange'
                    elif 'Maantie' in row['type'] or 'MAANTIE' in row['type']:
                        color = 'blue'
                    else:
                        color = 'red'
                    
                    # Location handling code...
                    location_key = f"{row['latitude']:.6f},{row['longitude']:.6f}"
                    if location_key in location_counts:
                        count = location_counts[location_key]
                        location_counts[location_key] += 1
                        
                        spiral_factor = 1 + (count - 1) * 0.3
                        random.seed(f"{row['title']}_{row['date']}")
                        angle = count * 0.8 + random.uniform(-0.4, 0.4)
                        
                        offset_distance = 0.075 * spiral_factor * random.uniform(0.8, 1.2)
                        
                        oval_factor = 0.7 * random.uniform(0.9, 1.1)
                        lat_offset = offset_distance * oval_factor * math.sin(angle)
                        lng_offset = offset_distance * math.cos(angle)
                        
                        lat_offset += random.uniform(-0.003, 0.003)
                        lng_offset += random.uniform(-0.003, 0.003)
                        
                        marker_lat = row['latitude'] + lat_offset
                        marker_lng = row['longitude'] + lng_offset
                    else:
                        location_counts[location_key] = 1
                        marker_lat = row['latitude']
                        marker_lng = row['longitude']
                    
                    # Add marker with error handling
                    try:
                        folium.Marker(
                            location=[marker_lat, marker_lng],
                            popup=folium.Popup(popup_content, max_width=300),
                            tooltip=sanitize_text(str(row['title'])),
                            icon=folium.Icon(color=color, icon='bicycle', prefix='fa')
                        ).add_to(m)
                    except Exception as e:
                        st.warning(f"Error adding marker for event '{row['title']}': {e}")
                        continue
                        
            except Exception as e:
                st.warning(f"Error processing event '{row.get('title', 'Unknown')}': {e}")
                continue
                
        return m
    except Exception as e:
        st.error(f"Error creating map: {e}")
        return None

def display_recent_events(df):
    """Display the 5 most recently added events in the sidebar."""
    st.sidebar.header("Viimeksi lisätyt tai muutetut tapahtumat")
    
    # Check if added_timestamp column exists
    if 'added_timestamp' not in df.columns or df.empty:
        st.sidebar.info("Ei viimeaikaisia tapahtumia saatavilla.")
        return
    
    # Sort events by added_timestamp in descending order
    try:
        recent_events = df.sort_values(by='added_timestamp', ascending=False).head(5)
        
        for _, event in recent_events.iterrows():
            with st.sidebar.expander(f"{event['title']} ({event['date']})"):
                st.write(f"**Tyyppi:** {event['type']}")
                st.write(f"**Sijainti:** {event['location']}")
                
                if not pd.isna(event['organizer']) and event['organizer']:
                    st.write(f"**Järjestäjä:** {event['organizer']}")
                
                if not pd.isna(event['link']) and event['link']:
                    st.write(f"[Lisätietoja]({event['link']})")
                
                # Format the timestamp to Finnish format
                if not pd.isna(event['added_timestamp']):
                    try:
                        timestamp = datetime.fromisoformat(event['added_timestamp'])
                        formatted_time = timestamp.strftime('%d.%m.%Y %H:%M')
                        st.caption(f"Lisätty: {formatted_time}")
                    except:
                        pass
    except Exception as e:
        st.sidebar.error(f"Virhe näytettäessä viimeaikaisia tapahtumia: {str(e)}")

def main():
    st.title("🚲 Pyöräilytapahtumat Suomessa 2025")
    
    # Load events
    with st.spinner("Ladataan tapahtumia..."):
        df = load_events()
    
    # Sidebar filters
    st.sidebar.header("Suodata tapahtumia")
    
    # Filter by month - sort by month number instead of name
    month_order = {}
    for _, row in df.iterrows():
        if row['month'] not in month_order and row['month'] != "Tuntematon":
            month_order[row['month']] = row['month_num']
    
    # Add "Tuntematon" at the end if it exists
    if "Tuntematon" in df['month'].unique():
        month_order["Tuntematon"] = 13
    
    # Sort months by their number
    sorted_months = ["Kaikki"] + sorted(df['month'].unique().tolist(), 
                                       key=lambda x: month_order.get(x, 99))
    
    selected_month = st.sidebar.selectbox("Kuukausi", sorted_months)
    
    # Filter by event type
    event_types = ["Kaikki"] + sorted(df['type'].unique().tolist())
    selected_type = st.sidebar.selectbox("Tapahtumatyyppi", event_types)
    
    # Filter by location
    locations = ["Kaikki"] + sorted(df['location'].unique().tolist())
    selected_location = st.sidebar.selectbox("Paikkakunta", locations)
    
    # Display recent events in sidebar (moved below filters)
    display_recent_events(df)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_month != "Kaikki":
        filtered_df = filtered_df[filtered_df['month'] == selected_month]
    
    if selected_type != "Kaikki":
        filtered_df = filtered_df[filtered_df['type'] == selected_type]
    
    if selected_location != "Kaikki":
        filtered_df = filtered_df[filtered_df['location'] == selected_location]
    
    # Display map
    st.subheader(f"Tapahtumat kartalla ({len(filtered_df)} kpl)")
    
    if not filtered_df.empty:
        # Create map
        m = create_map(filtered_df)
        
        # Display map
        folium_static(m, width=1200, height=600)
        
        # Display events in a table
        st.subheader("Tapahtumat listana")
        
        # Create a clean DataFrame for display
        display_df = filtered_df[['title', 'type', 'date', 'location', 'organizer']].copy()
        display_df.columns = ['Tapahtuma', 'Tyyppi', 'Päivämäärä', 'Paikkakunta', 'Järjestäjä']
        
        # Add link column if available
        if 'link' in filtered_df.columns:
            display_df['Linkki'] = filtered_df['link'].apply(
                lambda x: f'[Linkki]({x})' if pd.notna(x) and x else '')
        
        # Display the table
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Ei tapahtumia valituilla suodattimilla.")

if __name__ == "__main__":
    main() 