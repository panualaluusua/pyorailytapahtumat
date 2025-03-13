# Archive Directory

This directory contains files that were used during the development of the Bikeland Event Scraper project but are no longer needed for the current streamlined version.

## Contents

### src/
This directory contains old Python scripts that were used for various tasks:
- Parsing Bikeland events
- Cleaning event data
- Generating statistics
- Other development and testing scripts

### output/
This directory contains old output files generated during development:
- Various versions of parsed Bikeland events
- Event statistics
- Intermediate processing files

These files are kept for reference purposes but are not used by the current version of the application.

## Current Project Structure

The current project uses a simplified structure with just a few core scripts:
- `src/event_manager.py`: Main script that combines all event sources
- `src/bikeland_events.py`: Script for scraping events from Bikeland.fi
- `src/csv_events.py`: Script for processing events from CSV files
- `src/manual_events.py`: Script for processing manually added events
- `src/event_map_app.py`: Streamlit app for visualizing events on a map
- `src/simple_events_format.py`: Script for processing events in the simple format
- `src/convert_to_simple_format.py`: Utility script for converting events to the simple format

For more information, see the main README.md file in the project root directory. 