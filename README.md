# Bikeland Event Scraper

## Quick Start Guide

### 1. Add Cycling Events Manually
Edit `data/simple_events.txt` with your events:
```
Title: Event Name
Type: Event Type
Date: DD.MM.YYYY
Location: City
Organizer: Organizer Name
Link: https://example.com/event
Description: Additional details
```

### 2. Update All Events
Run: `update_events.bat`

### 3. View Events on Map
Run: `run_streamlit_app.bat`

## What This Tool Does
- Collects cycling events from multiple sources
- Shows them on an interactive map of Finland
- Lets you filter events by month, type, and location

## Installation
1. Clone this repository
2. Install required packages: `pip install -r requirements.txt`

## Detailed Usage

### Adding Events Manually
1. Edit `data/simple_events.txt`
2. Run `python src/manual_events.py`

### Scraping Bikeland.fi
Run `python src/bikeland_events.py`

### Processing CSV Data
1. Place CSV at `data/pyorailyfi-tapahtumat.csv`
2. Run `python src/csv_events.py`

### Combining All Events
Run `python src/event_manager.py`

### Map Visualization Features
- Interactive map with event markers
- Filter by month, event type, and location
- Table view of all events
- Statistics and charts

## File Structure
- `src/`: Python scripts
- `data/`: Input files and JSON data
- `output/`: Generated output files
- `archive/`: Old files (not needed)

## Troubleshooting
- Date format issues? Check DD.MM.YYYY format
- Website structure changed? The scraper may need updating
- CSV encoding issues? Try UTF-8-SIG encoding