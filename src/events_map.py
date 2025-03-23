import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import logging
import sys
from folium.plugins import MarkerCluster
from datetime import datetime
import json
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add a StreamHandler to also show logs in Streamlit
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

@st.cache_data
def load_events():
    """Load events from JSON file and add coordinates if missing."""
    try:
        # Load events from JSON file
        with open('data/all_events.json', 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        logger.info(f"Loaded {len(events)} events from JSON file")
        
        # Convert to DataFrame
        df = pd.DataFrame(events)
        
        # Initialize geocoder
        geolocator = Nominatim(user_agent="ulkopyorailytapahtumat")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        
        # Add ", Finland" to locations to improve geocoding accuracy
        df['search_location'] = df['location'].apply(lambda x: f"{x}, Finland" if pd.notnull(x) else None)
        
        # Initialize coordinate columns
        if 'latitude' not in df.columns:
            df['latitude'] = None
        if 'longitude' not in df.columns:
            df['longitude'] = None
        
        # Geocode locations without coordinates
        locations_to_geocode = df[
            (df['latitude'].isnull() | df['longitude'].isnull()) & 
            (df['location'].notnull())
        ]
        
        if not locations_to_geocode.empty:
            logger.info(f"Geocoding {len(locations_to_geocode)} locations...")
            
            for idx, row in locations_to_geocode.iterrows():
                try:
                    location = geocode(row['search_location'])
                    if location:
                        df.at[idx, 'latitude'] = location.latitude
                        df.at[idx, 'longitude'] = location.longitude
                        logger.info(f"Geocoded {row['location']}: [{location.latitude}, {location.longitude}]")
                    else:
                        logger.warning(f"Could not geocode location: {row['location']}")
                except Exception as e:
                    logger.error(f"Error geocoding {row['location']}: {e}")
                time.sleep(1)  # Be nice to the geocoding service
        
        # Drop rows without coordinates
        df_with_coords = df.dropna(subset=['latitude', 'longitude'])
        logger.info(f"Final dataset has {len(df_with_coords)} events with coordinates")
        
        return df_with_coords
        
    except Exception as e:
        logger.error(f"Error loading events: {e}")
        return pd.DataFrame()

def create_map(df):
    """Create a Folium map with event data."""
    try:
        logger.info(f"Creating map with {len(df)} events")
        
        # Create map centered on Finland
        m = folium.Map(
            location=[64.5, 26.0],
            zoom_start=6,
            control_scale=True,
            tiles='CartoDB positron'
        )
        
        # Add tile layers
        tile_layers = {
            'Light Theme': {
                'CartoDB Positron': 'CartoDB positron',
                'OpenStreetMap': 'OpenStreetMap'
            },
            'Dark Theme': {
                'CartoDB Dark Matter': 'CartoDB dark_matter'
            },
            'Satellite': {
                'Esri Satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'Esri Streets': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
            }
        }
        
        # Add tile layers by category
        for category, layers in tile_layers.items():
            for name, tile in layers.items():
                try:
                    if 'http' in tile:
                        folium.TileLayer(
                            tiles=tile,
                            name=name,
                            attr='Esri',
                            control=True
                        ).add_to(m)
                    else:
                        folium.TileLayer(
                            tiles=tile,
                            name=name,
                            control=True
                        ).add_to(m)
                except Exception as e:
                    logger.warning(f"Failed to add {name} tile layer: {e}")
        
        # Add layer control
        folium.LayerControl(collapsed=True).add_to(m)
        
        # Create marker cluster
        marker_cluster = MarkerCluster().add_to(m)
        
        # Define event styles
        event_styles = {
            'MTB XCM': {'color': 'darkgreen', 'icon': 'bicycle'},
            'MTB XCO': {'color': 'green', 'icon': 'bicycle'},
            'MTB XCC': {'color': 'lightgreen', 'icon': 'bicycle'},
            'MTB': {'color': 'green', 'icon': 'bicycle'},
            'MTB Enduro': {'color': 'darkred', 'icon': 'bicycle'},
            'Downhill (DH)': {'color': 'darkred', 'icon': 'bicycle'},
            'Trial': {'color': 'purple', 'icon': 'bicycle'},
            'Gravel': {'color': 'orange', 'icon': 'bicycle'},
            'GRAVEL': {'color': 'orange', 'icon': 'bicycle'},
            'Maantie': {'color': 'blue', 'icon': 'bicycle'},
            'Cyclocross': {'color': 'purple', 'icon': 'bicycle'},
            'E-pyöräily': {'color': 'cadetblue', 'icon': 'bolt'},
            'Fat Bike - Multisport': {'color': 'darkblue', 'icon': 'bicycle'},
            'Unknown': {'color': 'gray', 'icon': 'question'},
            'default': {'color': 'red', 'icon': 'bicycle'}
        }
        
        # Add markers
        marker_count = 0
        for idx, row in df.iterrows():
            try:
                # Get style based on event type
                style = event_styles.get(row['type'], event_styles['default'])
                
                # Format date for display (datetime is already parsed in main)
                event_date = row['datetime'].strftime('%d.%m.%Y %H:%M')
                
                # Create popup content
                popup_content = f"""
                <div style="font-family: Arial, sans-serif; min-width: 200px;">
                    <h4 style="color: {style['color']};">{row['title']}</h4>
                    <p><b>Type:</b> {row['type']}</p>
                    <p><b>Date:</b> {event_date}</p>
                    <p><b>Location:</b> {row['location']}</p>
                    <p><b>Organizer:</b> {row.get('organizer', 'N/A')}</p>
                """
                
                # Add link if available
                if 'link' in row and row['link']:
                    popup_content += f'<p><a href="{row["link"]}" target="_blank">Event Details</a></p>'
                
                popup_content += "</div>"
                
                # Create marker
                folium.Marker(
                    location=[float(row['latitude']), float(row['longitude'])],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=row['title'],
                    icon=folium.Icon(
                        color=style['color'],
                        icon=style['icon'],
                        prefix='fa'
                    )
                ).add_to(marker_cluster)
                
                marker_count += 1
                
            except Exception as e:
                logger.error(f"Error adding marker for {row['title']}: {e}")
        
        logger.info(f"Successfully added {marker_count} markers to the map")
        return m, marker_count
        
    except Exception as e:
        logger.error(f"Error creating map: {e}")
        return None, 0

def main():
    st.title("🚲 Finnish Cycling Events")
    
    # Load event data
    df = load_events()
    
    if df.empty:
        st.error("Failed to load event data")
        return
    
    # Display data info
    st.sidebar.subheader("Event Information")
    st.sidebar.write(f"Total number of events: {len(df)}")
    
    # Add date range filter
    st.sidebar.subheader("Filter Events")
    
    # Convert datetime strings to datetime objects with mixed format support
    try:
        # First try parsing as ISO format
        df['datetime'] = pd.to_datetime(df['datetime'], format='mixed')
    except Exception as e:
        logger.error(f"Error parsing dates: {e}")
        try:
            # Fallback to trying Finnish format
            df['datetime'] = pd.to_datetime(df['datetime'].str.replace('.', '/'), format='%d/%m/%Y %H:%M')
        except Exception as e:
            logger.error(f"Error parsing dates with Finnish format: {e}")
            st.error("Failed to parse event dates")
            return
    
    # Get date range
    min_date = df['datetime'].min()
    max_date = df['datetime'].max()
    
    # Date range selector
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )
    
    # Filter by date range
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df['datetime'].dt.date >= start_date) & (df['datetime'].dt.date <= end_date)
        df_filtered = df.loc[mask]
    else:
        df_filtered = df
    
    # Get unique event types
    event_types = sorted(df_filtered['type'].unique())
    
    # Create filter controls with all selected by default
    selected_types = st.sidebar.multiselect(
        "Select Event Types",
        options=event_types,
        default=event_types,
        help="Choose which types of events to display on the map"
    )
    
    # Filter DataFrame based on selection
    df_filtered = df_filtered[df_filtered['type'].isin(selected_types)]
    
    # Display filtered count
    st.sidebar.write(f"Showing {len(df_filtered)} of {len(df)} events")
    
    # Create and display map
    st.subheader("Event Map")
    
    try:
        # Create map with filtered data
        m, marker_count = create_map(df_filtered)
        
        if m:
            # Display map
            folium_static(m, width=800, height=500)
            
            # Success message
            st.success(f"Map created successfully with {marker_count} filtered markers")
            
            # Add legend
            st.sidebar.subheader("Event Type Colors")
            for event_type in selected_types:
                style = event_styles.get(event_type, event_styles['default'])
                st.sidebar.markdown(
                    f"<div style='display: flex; align-items: center;'>"
                    f"<div style='width: 20px; height: 20px; background-color: {style['color']}; margin-right: 10px;'></div>"
                    f"{event_type}</div>",
                    unsafe_allow_html=True
                )
            
            # Add help text
            st.info("""
            If the map is not displaying correctly:
            1. Check the browser console (F12 > Console tab) for errors
            2. Try clearing your browser cache
            3. Check the logs in the sidebar for detailed information
            """)
            
        else:
            st.error("Failed to create map")
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        st.error(f"An error occurred: {str(e)}")
    
    # Display logs in sidebar
    st.sidebar.subheader("Debug Logs")
    log_output = st.sidebar.empty()
    
    # Create a string buffer for the logs
    import io
    log_buffer = io.StringIO()
    stream_handler.stream = log_buffer
    
    # Display the logs
    log_output.code(log_buffer.getvalue())

if __name__ == "__main__":
    main() 