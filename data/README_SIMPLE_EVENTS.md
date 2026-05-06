# Simple Events Format

This document explains how to use the simple events format to add cycling events manually.

## Overview

The simple events format is designed to be easy to edit and maintain. It uses a straightforward key-value format where each event is separated by a blank line.

## File Location

Add events to `data/simple_events.txt`.

## Event Format

Each event must include these required fields:

```text
Title: Event Name
Type: Event Type
Date: DD.MM.YYYY
Location: City or Location
```

Optional fields:

```text
Organizer: Event Organizer
Link: https://example.com/event-url
Description: Additional details about the event.
```

## Example

```text
Title: Helsinki MTB Marathon
Type: MTB XCM
Date: 15.06.2026
Location: Helsinki
Organizer: Cycle Club Helsinki
Link: https://example.com/helsinki-mtb
Description: Challenging mountain bike marathon through the forests of Helsinki.
```

## Adding Multiple Events

Separate events with a blank line:

```text
Title: Event 1
Type: MTB
Date: 01.06.2026
Location: Helsinki
Organizer: Organizer 1

Title: Event 2
Type: Gravel
Date: 15.06.2026
Location: Turku
Organizer: Organizer 2
```

## Processing Events

After editing `data/simple_events.txt`, run:

```bash
python src/manual_events.py
```

This will:

1. read events from `data/simple_events.txt`
2. preserve existing entries in `data/manual_events.json`
3. append new events that do not already exist with the same `title + date`

To run the full update pipeline without git operations, use:

```bash
python update.py --dry-run
```

## Notes

- The parser converts `Date: DD.MM.YYYY` into `YYYY-MM-DD 08:00`.
- Required fields are `Title`, `Type`, `Date`, and `Location`.
- Existing manual events are not removed automatically if you delete them from `simple_events.txt`; the processor preserves already stored entries.
