import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import re
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import matplotlib.pyplot as plt
import json
import time

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
@st.cache_data
def load_events():
    """Load events from the clean combined events file."""
    events = []
    current_event = {}
    in_event = False
    
    try:
        with open('output/clean_combined_events.txt', 'r', encoding='utf-8') as f:
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
                    
                    # Parse the datetime
                    try:
                        date_obj = datetime.strptime(current_event['datetime'], '%Y-%m-%d %H:%M')
                        current_event['date'] = date_obj.strftime('%d.%m.%Y')
                        current_event['month'] = date_obj.strftime('%B')
                        current_event['month_num'] = date_obj.month
                    except:
                        current_event['date'] = current_event['datetime']
                        current_event['month'] = "Unknown"
                        current_event['month_num'] = 0
                
                elif line.startswith('description:') and in_event:
                    desc = line.replace('description:', '').strip()
                    current_event['description'] = desc
                    
                    # Extract location from description
                    loc_match = re.search(r'järjestetään \d+\.\d+\.\d+ paikkakunnalla (.*?)\.', desc)
                    if loc_match:
                        current_event['location'] = loc_match.group(1).strip()
                    else:
                        # Try alternative pattern
                        alt_match = re.search(r'at\s+(.*?)(?:\s+Järjestäjä:|\s+Lisätietoja:|$)', desc)
                        if alt_match:
                            current_event['location'] = alt_match.group(1).strip()
                        else:
                            current_event['location'] = "Unknown Location"
                    
                    # Extract organizer from description
                    org_match = re.search(r'Järjestäjänä toimii (.*?)\.', desc)
                    if org_match:
                        current_event['organizer'] = org_match.group(1).strip()
                    else:
                        # Try alternative pattern
                        alt_match = re.search(r'Järjestäjä:\s*(.*?)(?:\s+Lisätietoja:|$)', desc)
                        if alt_match:
                            current_event['organizer'] = alt_match.group(1).strip()
                        else:
                            current_event['organizer'] = ""
                    
                    # Extract link from description
                    link_match = re.search(r'Lisätietoja tapahtumasta: (https?://[^\s]+)', desc)
                    if link_match:
                        current_event['link'] = link_match.group(1).strip()
                    else:
                        # Try alternative pattern
                        alt_match = re.search(r'Lisätietoja:\s*(https?://[^\s]+)', desc)
                        if alt_match:
                            current_event['link'] = alt_match.group(1).strip()
                        else:
                            current_event['link'] = ""
                
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
        st.error(f"Error reading events: {e}")
    
    # Convert to DataFrame
    df = pd.DataFrame(events)
    
    # Add coordinates
    df['coordinates'] = df['location'].apply(geocode_location)
    
    # Filter out events with no coordinates
    df = df[df['coordinates'].notna()]
    
    # Split coordinates into latitude and longitude
    df['latitude'] = df['coordinates'].apply(lambda x: x[0] if x else None)
    df['longitude'] = df['coordinates'].apply(lambda x: x[1] if x else None)
    
    return df

def create_map(df, center=[65.0, 25.0], zoom=5):
    """Create a folium map with event markers."""
    m = folium.Map(location=center, zoom_start=zoom, control_scale=True)
    
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
            
            # Add marker
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row['title'],
                icon=folium.Icon(color=color, icon='bicycle', prefix='fa')
            ).add_to(m)
    
    return m

def main():
    st.title("🚲 Pyöräilytapahtumat Suomessa 2025")
    
    # Load events
    with st.spinner("Ladataan tapahtumia..."):
        df = load_events()
    
    # Sidebar filters
    st.sidebar.header("Suodata tapahtumia")
    
    # Filter by month
    months = ["All"] + sorted(df['month'].unique().tolist(), key=lambda x: datetime.strptime(x, '%B').month if x != "Unknown" else 0)
    selected_month = st.sidebar.selectbox("Kuukausi", months)
    
    # Filter by event type
    event_types = ["All"] + sorted(df['type'].unique().tolist())
    selected_type = st.sidebar.selectbox("Tapahtumatyyppi", event_types)
    
    # Filter by location
    locations = ["All"] + sorted(df['location'].unique().tolist())
    selected_location = st.sidebar.selectbox("Paikkakunta", locations)
    
    # Apply filters
    filtered_df = df.copy()
    if selected_month != "All":
        filtered_df = filtered_df[filtered_df['month'] == selected_month]
    if selected_type != "All":
        filtered_df = filtered_df[filtered_df['type'] == selected_type]
    if selected_location != "All":
        filtered_df = filtered_df[filtered_df['location'] == selected_location]
    
    # Display number of events
    st.sidebar.write(f"Näytetään {len(filtered_df)} tapahtumaa {len(df)} tapahtumasta")
    
    # Create tabs for map and table views
    tab1, tab2, tab3 = st.tabs(["Kartta", "Taulukko", "Tilastot"])
    
    with tab1:
        # Create map
        if not filtered_df.empty:
            # Center on Finland
            m = create_map(filtered_df)
            
            # Display map
            folium_static(m, width=1000, height=600)
        else:
            st.warning("Ei tapahtumia näytettäväksi valituilla suodattimilla.")
    
    with tab2:
        # Display events in a table
        if not filtered_df.empty:
            # Select columns to display
            display_df = filtered_df[['title', 'type', 'date', 'location', 'organizer']].copy()
            
            # Rename columns
            display_df.columns = ['Tapahtuma', 'Tyyppi', 'Päivämäärä', 'Paikkakunta', 'Järjestäjä']
            
            # Display table
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("Ei tapahtumia näytettäväksi valituilla suodattimilla.")
    
    with tab3:
        # Display statistics
        if not df.empty:
            st.subheader("Tapahtumat kuukausittain")
            
            # Count events by month
            month_counts = df.groupby('month_num')['title'].count().reset_index()
            month_counts = month_counts.sort_values('month_num')
            
            # Map month numbers to names
            month_names = {
                1: 'Tammikuu', 2: 'Helmikuu', 3: 'Maaliskuu',
                4: 'Huhtikuu', 5: 'Toukokuu', 6: 'Kesäkuu',
                7: 'Heinäkuu', 8: 'Elokuu', 9: 'Syyskuu',
                10: 'Lokakuu', 11: 'Marraskuu', 12: 'Joulukuu'
            }
            
            month_counts['month_name'] = month_counts['month_num'].map(month_names)
            
            # Create bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(month_counts['month_name'], month_counts['title'], color='skyblue')
            
            # Add labels and title
            ax.set_xlabel('Kuukausi')
            ax.set_ylabel('Tapahtumien määrä')
            ax.set_title('Pyöräilytapahtumat kuukausittain 2025')
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}',
                        ha='center', va='bottom')
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
            
            # Adjust layout
            plt.tight_layout()
            
            # Display chart
            st.pyplot(fig)
            
            # Event types pie chart
            st.subheader("Tapahtumatyypit")
            
            # Count events by type
            type_counts = df['type'].value_counts()
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            
            # Display chart
            st.pyplot(fig)
            
            # Top locations
            st.subheader("Suosituimmat paikkakunnat")
            
            # Count events by location
            location_counts = df['location'].value_counts().head(10)
            
            # Create bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.barh(location_counts.index, location_counts.values, color='lightgreen')
            
            # Add labels and title
            ax.set_xlabel('Tapahtumien määrä')
            ax.set_ylabel('Paikkakunta')
            ax.set_title('Top 10 paikkakunnat')
            
            # Add value labels
            for i, v in enumerate(location_counts.values):
                ax.text(v + 0.1, i, str(v), va='center')
            
            # Adjust layout
            plt.tight_layout()
            
            # Display chart
            st.pyplot(fig)
        else:
            st.warning("Ei tapahtumia näytettäväksi.")

if __name__ == "__main__":
    main() 