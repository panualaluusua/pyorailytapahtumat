# Bikeland Event Scraper

A Python tool for scraping cycling events from Bikeland.fi and other sources, parsing them, and generating a clean list of events.

## Features

- Scrapes cycling events from Bikeland.fi
- Parses event details (title, date, location, description)
- Cleans and formats event data
- Combines events from multiple sources
- Generates statistics about cycling events
- Interactive map visualization of events

## Output Files

- `bikeland_events.txt`: Raw scraped events from Bikeland.fi
- `clean_bikeland_events.txt`: Cleaned events from Bikeland.fi
- `parsed_bikeland_events.txt`: Parsed events with structured data
- `specific_bikeland_events.txt`: Events with specific details extracted
- `final_bikeland_events.txt`: Final formatted events
- `clean_final_bikeland_events.txt`: Clean final events
- `final_clean_bikeland_events.txt`: Final clean events
- `datetime_bikeland_events.txt`: Events with parsed datetime
- `combined_events.txt`: Combined events from multiple sources
- `duplicate_events.txt`: List of duplicate events found
- `clean_combined_events.txt`: Combined events with clean, fluid descriptions
- `event_statistics.txt`: Statistical report about the events

## Installation

1. Clone this repository
2. Install the required packages:

```
pip install -r requirements.txt
```

## Usage

### Scraping Events

To scrape events from Bikeland.fi:

```
python src/scrape_bikeland_events.py
```

### Cleaning Events

To clean the scraped events:

```
python src/clean_bikeland_events.py
```

### Parsing Events

To parse the cleaned events:

```
python src/parse_bikeland_events.py
```

### Combining Events from Multiple Sources

To combine events from multiple sources:

```
python src/combine_events.py
```

### Creating Clean Combined Events

To create a clean version of the combined events with more fluid descriptions:

```
python src/clean_combined_events.py
```

### Generating Event Statistics

To generate statistics about the events:

```
python src/event_statistics.py
```

### Interactive Map Visualization

To launch the interactive map application:

```
streamlit run src/event_map_app.py
```

The Streamlit app provides:
- Interactive map of all cycling events in Finland
- Filtering by month, event type, and location
- Find events nearest to your location
- Tabular view of all events
- Statistical visualizations

## Parser Features

The parser includes several scripts for different stages of the event processing:

- `scrape_bikeland_events.py`: Scrapes events directly from the website
- `clean_bikeland_events.py`: Cleans the raw scraped data
- `parse_bikeland_events.py`: Parses the cleaned data into structured format
- `specific_bikeland_events.py`: Extracts specific details from events
- `final_bikeland_events.py`: Creates the final formatted events
- `clean_final_bikeland_events.py`: Cleans the final events
- `final_clean_bikeland_events.py`: Creates the final clean events
- `datetime_bikeland_events.py`: Parses dates and times from events
- `combine_events.py`: Combines events from multiple sources and checks for duplicates
- `clean_combined_events.py`: Creates clean, fluid descriptions for combined events
- `event_statistics.py`: Generates statistics about the events
- `event_map_app.py`: Interactive Streamlit app for visualizing events on a map

## Troubleshooting

- If you encounter issues with date parsing, check the format of the dates in the source files.
- If the website structure changes, the scraper may need to be updated.
- For CSV file encoding issues, try using UTF-8-SIG encoding when reading the files.