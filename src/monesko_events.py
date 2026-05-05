import html
import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

API_URL = "https://monesko.fi/wp-json/tribe/events/v1/events"
ICS_URL = "https://monesko.fi/tapahtumat/category/pyoraily/?ical=1"
OUTPUT_FILE = "data/monesko_events.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/calendar, text/html, */*",
}
TIMEOUT = 20


def _clean_html(value):
    if not value:
        return ""
    text = BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _format_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return None


def _is_future(datetime_str, today):
    try:
        return datetime.strptime(datetime_str.split()[0], "%Y-%m-%d").date() >= today
    except Exception:
        return False


def _build_type(categories):
    names = []
    for category in categories or []:
        name = (category or {}).get("name", "").strip()
        if not name or name.lower() == "pyöräily" or name.lower() == "pyoraily":
            continue
        names.append(name)
    return ", ".join(dict.fromkeys(names)) or "Pyöräily"


def _build_location(venue):
    if isinstance(venue, list) and venue:
        venue = venue[0]
    if isinstance(venue, dict):
        parts = [
            venue.get("venue"),
            venue.get("city"),
            venue.get("stateprovince"),
            venue.get("country"),
        ]
        location = ", ".join(part.strip() for part in parts if part and str(part).strip())
        if location:
            return location
    return ""


def _api_event_to_local(item):
    start = _format_datetime(item.get("start_date"))
    if not start:
        return None

    description = _clean_html(item.get("description") or item.get("excerpt"))
    organizer = ""
    organizers = item.get("organizer") or []
    if isinstance(organizers, list) and organizers:
        organizer = (organizers[0] or {}).get("organizer", "") or ""

    link = item.get("website") or item.get("url") or ""
    return {
        "title": (item.get("title") or "").strip(),
        "type": _build_type(item.get("categories")),
        "datetime": start,
        "location": _build_location(item.get("venue")),
        "organizer": organizer.strip(),
        "description": description,
        "link": link.strip(),
        "source": "monesko",
    }


def _fetch_api_events():
    events = []
    page = 1

    while True:
        response = requests.get(
            API_URL,
            headers=HEADERS,
            params={"categories": "pyoraily", "per_page": 100, "page": page},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        page_events = payload.get("events", [])
        events.extend(page_events)

        total_pages = int(payload.get("total_pages") or 1)
        if page >= total_pages:
            break
        page += 1

    return events


def _parse_ics_datetime(raw_value):
    value = raw_value.strip()
    for candidate in ("%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            parsed = datetime.strptime(value, candidate)
            if candidate == "%Y%m%d":
                parsed = parsed.replace(hour=8, minute=0)
            return parsed.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    return None


def _parse_ics_text(raw_value):
    value = raw_value.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";")
    return html.unescape(value).strip()


def _iter_vevents(ics_text):
    unfolded_lines = []
    for line in ics_text.splitlines():
        if line.startswith((" ", "\t")) and unfolded_lines:
            unfolded_lines[-1] += line[1:]
        else:
            unfolded_lines.append(line.rstrip())

    current = None
    for line in unfolded_lines:
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current:
                yield current
            current = None
            continue
        if current is None or ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.split(";", 1)[0]
        current.setdefault(key, []).append(value)


def _fetch_ics_events():
    response = requests.get(ICS_URL, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()

    events = []
    for item in _iter_vevents(response.text):
        start = _parse_ics_datetime((item.get("DTSTART") or [""])[0])
        title = _parse_ics_text((item.get("SUMMARY") or [""])[0])
        if not start or not title:
            continue

        description = _parse_ics_text((item.get("DESCRIPTION") or [""])[0])
        location = _parse_ics_text((item.get("LOCATION") or [""])[0])
        link = _parse_ics_text((item.get("URL") or [""])[0])

        events.append(
            {
                "title": title,
                "type": "Pyöräily",
                "datetime": start,
                "location": location,
                "organizer": "Monesko",
                "description": description,
                "link": link,
                "source": "monesko",
            }
        )

    return events


def fetch_monesko_events():
    """
    Fetch cycling events from Monesko and save them to a JSON file.
    Uses the Tribe API first and falls back to the iCalendar export if needed.
    Returns the number of new events found.
    """
    print("Fetching events from Monesko...")
    os.makedirs("data", exist_ok=True)

    existing_events = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_events = json.load(f)
            print(f"Loaded {len(existing_events)} existing events")
        except Exception as e:
            print(f"Error loading existing events: {e}")

    existing_ids = {
        f"{event['title']}_{event['datetime'].split()[0]}"
        for event in existing_events
        if "title" in event and "datetime" in event
    }

    today = datetime.now().date()

    try:
        raw_events = _fetch_api_events()
        parsed_events = [_api_event_to_local(item) for item in raw_events]
        parsed_events = [event for event in parsed_events if event and _is_future(event["datetime"], today)]
        print(f"Fetched {len(parsed_events)} events from Monesko API")
    except Exception as e:
        print(f"API fetch failed, falling back to iCalendar export: {e}")
        try:
            parsed_events = [event for event in _fetch_ics_events() if _is_future(event["datetime"], today)]
            print(f"Fetched {len(parsed_events)} events from Monesko iCalendar export")
        except Exception as ics_error:
            print(f"Error fetching Monesko events: {ics_error}")
            return 0

    new_events = []
    merged_by_id = {
        f"{event['title']}_{event['datetime'].split()[0]}": event
        for event in existing_events
        if "title" in event and "datetime" in event and _is_future(event["datetime"], today)
    }

    for event in parsed_events:
        event_id = f"{event['title']}_{event['datetime'].split()[0]}"
        if event_id not in existing_ids:
            new_events.append(event)
            print(f"Added new event: {event['title']} on {event['datetime']} at {event.get('location', '')}")
        merged_by_id[event_id] = event
        existing_ids.add(event_id)

    all_events = sorted(merged_by_id.values(), key=lambda event: event.get("datetime", "9999-99-99"))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"\nNew events: {len(new_events)}, total: {len(all_events)}")
    print(f"Saved to {OUTPUT_FILE}")
    return len(new_events)


if __name__ == "__main__":
    fetch_monesko_events()
