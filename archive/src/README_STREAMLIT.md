# Pyöräilytapahtumat Suomessa - Streamlit App

An interactive web application for visualizing cycling events in Finland on a map.

## Features

- Interactive map of cycling events across Finland
- Filter events by month, event type, and location
- Find events nearest to your location
- View events in a sortable table format
- Statistical visualizations of event data

## Installation

1. Ensure you have Python 3.6+ installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Running the App

Use the provided batch file:
```
run_streamlit_app.bat
```

Or run directly with:
```
C:\Users\panua\AppData\Local\Programs\Python\Python313\Scripts\streamlit.exe run src/event_map_app.py
```

## Generating Sample Data

If you don't have real event data, generate sample data:
```
python src/generate_sample_events.py
```

## Screenshots

The app includes three main views:

1. **Map View**: Interactive map with event markers
2. **Table View**: Sortable table of all events
3. **Statistics View**: Charts and visualizations of event data

## How It Works

The app reads event data from `output/clean_combined_events.txt`, which contains cycling events in a structured format. It geocodes the event locations to get coordinates, then displays them on an interactive map.

Users can filter events, find events nearest to their location, and view statistics about the events.

## Troubleshooting

If you encounter issues:

1. Make sure all required packages are installed
2. Check that the `output/clean_combined_events.txt` file exists
3. If Streamlit command is not found, use the full path to the executable
4. For geocoding issues, ensure you have an internet connection

For more detailed instructions, see the [Streamlit App Guide](../docs/streamlit_app_guide.md). 