# Simple Events Format

This document explains how to use the simple events format to add cycling events manually.

## Overview

The simple events format is designed to be easy to edit and maintain. It uses a straightforward key-value format where each event is separated by a blank line.

## File Location

Events should be added to the `data/simple_events.txt` file.

## Event Format

Each event must include the following required fields:

```
Title: Event Name
Type: Event Type
Date: DD.MM.YYYY
Location: City or Location
```

And can optionally include:

```
Organizer: Event Organizer
Link: https://example.com/event-url
Description: Additional details about the event.
```

## Example

Here's an example of a properly formatted event:

```
Title: Helsinki MTB Marathon
Type: MTB XCM
Date: 15.06.2025
Location: Helsinki
Organizer: Cycle Club Helsinki
Link: https://example.com/helsinki-mtb
Description: Challenging mountain bike marathon through the forests of Helsinki.
```

## Adding Multiple Events

To add multiple events, separate each event with a blank line:

```
Title: Event 1
Type: MTB
Date: 01.06.2025
Location: Helsinki
Organizer: Organizer 1

Title: Event 2
Type: Gravel
Date: 15.06.2025
Location: Turku
Organizer: Organizer 2
```

## Event Types

Common event types include:
- MTB XCM (Mountain Bike Marathon)
- MTB XCO (Mountain Bike Cross-Country Olympic)
- Gravel
- Maantie (Road)
- Cyclocross
- Downhill
- Enduro
- Tempo (Time Trial)

## Processing Events

After adding or editing events in the simple format, run the manual events processor:

```
python src/manual_events.py
```

This will:
1. Read the events from `data/simple_events.txt`
2. Process them and check for duplicates
3. Save them to `data/manual_events.json`

To combine with other event sources and generate the output for the Streamlit app, run:

```
python src/event_manager.py
```

## Running the App

After processing the events, run the Streamlit app to see your changes:

```
python -m streamlit run src/event_map_app.py
```

## Tips

- Make sure to include all required fields for each event
- Use the correct date format: DD.MM.YYYY (e.g., 15.06.2025)
- Separate events with a blank line
- The script will automatically sort events by date 