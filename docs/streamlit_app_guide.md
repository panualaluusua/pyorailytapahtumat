# Pyöräilytapahtumat Suomessa - Streamlit App Guide

This guide explains how to use the Streamlit app for visualizing cycling events in Finland.

## Getting Started

1. Make sure you have installed all the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the app using the provided batch file:
   ```
   run_streamlit_app.bat
   ```
   
   Alternatively, you can run it directly with:
   ```
   C:\Users\panua\AppData\Local\Programs\Python\Python313\Scripts\streamlit.exe run src/event_map_app.py
   ```

3. The app will open in your default web browser at `http://localhost:8501`

## Features

### Interactive Map

The main tab displays an interactive map of Finland with markers for all cycling events:
- **Green markers**: MTB (Mountain Bike) events
- **Orange markers**: Gravel events
- **Blue markers**: Road cycling events
- **Red markers**: Other event types

Click on any marker to see details about the event, including:
- Event name and type
- Date
- Location
- Organizer
- Link to more information (if available)

### Filtering Events

Use the sidebar to filter events by:
- **Month**: Select a specific month to see events during that time
- **Event Type**: Filter by cycling discipline (MTB, Gravel, Road, etc.)
- **Location**: See events in a specific city or town

The app will display how many events match your filters out of the total number of events.

### Finding Nearest Events

To find events closest to your location:
1. Enter your city or town in the "Sijaintisi (kaupunki)" field in the sidebar
2. The app will geocode your location and display it on the map
3. Use the slider to select how many nearest events you want to see
4. The sidebar will display a list of the nearest events with their distances from your location

### Table View

Switch to the "Taulukko" tab to see all events in a sortable table format. The table includes:
- Event name
- Event type
- Date
- Location
- Organizer

### Statistics

The "Tilastot" tab provides visualizations of the event data:
- **Events by month**: Bar chart showing the distribution of events throughout the year
- **Event types**: Pie chart showing the proportion of different cycling disciplines
- **Popular locations**: Bar chart of the top 10 locations with the most events

## Troubleshooting

- **Location not found**: If your location cannot be geocoded, try entering a larger nearby city or add "Finland" to the end of your location.
- **No events displayed**: Check if your filters are too restrictive. Try resetting them to "All".
- **Map not loading**: Ensure you have a stable internet connection, as the map tiles require internet access.
- **Slow performance**: If the app is running slowly, try reducing the number of events by applying filters.
- **Streamlit command not found**: Use the provided batch file or the full path to the Streamlit executable.

## Data Sources

The app uses event data from:
- Bikeland.fi events
- Pyoraily.fi events calendar
- Other cycling event sources

Events are combined and deduplicated to provide a comprehensive view of cycling events in Finland.

## Generating Sample Data

If you don't have real event data, you can generate sample data using:
```
python src/generate_sample_events.py
```

This will create 50 sample events in the `output/clean_combined_events.txt` file that the app can display.

## Feedback and Contributions

If you have suggestions for improving the app or want to contribute to its development, please:
1. Submit issues or feature requests on GitHub
2. Fork the repository and submit pull requests with your improvements
3. Contact the development team with your feedback 