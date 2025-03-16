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
        
        # Load events from JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            events_data = json.load(f)
        
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
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    finnish_date = date_obj.strftime('%d.%m.%Y')
                    english_month = date_obj.strftime('%B')
                    month_fi = month_names_fi.get(english_month, english_month)
                    month_num = date_obj.month
                    return finnish_date, month_fi, month_num
                return "Tuntematon", "Tuntematon", 0
            except:
                return "Tuntematon", "Tuntematon", 0
        
        # Apply date processing
        date_info = df['date'].apply(process_date)
        df['date'] = date_info.apply(lambda x: x[0])
        df['month'] = date_info.apply(lambda x: x[1])
        df['month_num'] = date_info.apply(lambda x: x[2])
        
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
    m = folium.Map(location=center, zoom_start=zoom, control_scale=True)
    
    # Create a dictionary to track locations and count events at each location
    location_counts = {}
    
    # Add markers for each event
    for idx, row in df.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            # Create popup content
            popup_content = f"""
            <b>{row['title']}</b> ({row['type']})<br>
            <b>Date:</b> {row['date']}<br>
            <b>Location:</b> {row['location']}<br>
            """
            
            if row['organizer']:
                popup_content += f"<b>Organizer:</b> {row['organizer']}<br>"
                
            if row['link']:
                popup_content += f"<a href='{row['link']}' target='_blank'>More information</a>"
            
            # Determine marker color based on event type
            if 'MTB' in row['type']:
                color = 'green'
            elif 'Gravel' in row['type'] or 'GRAVEL' in row['type']:
                color = 'orange'
            elif 'Maantie' in row['type'] or 'MAANTIE' in row['type']:
                color = 'blue'
            else:
                color = 'red'
            
            # Check if we already have events at this location
            location_key = f"{row['latitude']:.6f},{row['longitude']:.6f}"
            if location_key in location_counts:
                count = location_counts[location_key]
                location_counts[location_key] += 1
                
                # Create a spiral pattern that grows with more events
                # This allows for more events to be visible without overlapping
                spiral_factor = 1 + (count - 1) * 0.3  # Increased growth factor 3x (was 0.1)
                
                # Add some randomness to the angle and distance
                random.seed(f"{row['title']}_{row['date']}")  # Use consistent seed for each event
                angle = count * 0.8 + random.uniform(-0.4, 0.4)  # Add randomness to angle
                
                # Base offset distance with some randomness - SIGNIFICANTLY INCREASED
                offset_distance = 0.075 * spiral_factor * random.uniform(0.8, 1.2)  # About 7.5km offset (was 0.025)
                
                # Calculate offset with slight randomness in the oval shape
                oval_factor = 0.7 * random.uniform(0.9, 1.1)  # Add ±10% randomness to oval shape
                lat_offset = offset_distance * oval_factor * math.sin(angle)
                lng_offset = offset_distance * math.cos(angle)
                
                # Add a tiny bit of additional random noise
                lat_offset += random.uniform(-0.003, 0.003)  # About ±300m random noise (was 0.001)
                lng_offset += random.uniform(-0.003, 0.003)  # About ±300m random noise (was 0.001)
                
                marker_lat = row['latitude'] + lat_offset
                marker_lng = row['longitude'] + lng_offset
            else:
                location_counts[location_key] = 1
                marker_lat = row['latitude']
                marker_lng = row['longitude']
            
            # Add marker
            folium.Marker(
                location=[marker_lat, marker_lng],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row['title'],
                icon=folium.Icon(color=color, icon='bicycle', prefix='fa')
            ).add_to(m)
    
    return m

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