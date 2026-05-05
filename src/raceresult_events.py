"""
Scraper for Finnish cycling events from my.raceresult.com.

Uses the undocumented /RREvents/list endpoint with geographic bounds
to find events within Finland, filtered to cycling sport types.
"""
import requests
import json
import os
from datetime import datetime

API_URL = "https://my.raceresult.com/RREvents/list"
OUTPUT_FILE = "data/raceresult_events.json"

# Finland's geographic bounding box
FINLAND_BOUNDS = "19.5,59.5,31.6,70.1"

CYCLING_SPORT_TYPES = {
    "Pyöräily",
    "Maastopyöräily",
    "Cycling",
    "Mountain Biking",
    "Mountain Bike",
    "Bike Tour",
    "Pyöräilyretki",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# Event array field indices from the API
IDX_ID       = 0
IDX_NAME     = 2
IDX_DATE_FROM= 3
IDX_DATE_TO  = 4
IDX_CITY     = 5
IDX_COUNTRY  = 6
IDX_LAT      = 7
IDX_LON      = 8
IDX_SPORT    = 10


def fetch_raceresult_events() -> int:
    """Fetch Finnish cycling events from my.raceresult.com. Returns count of new events."""
    print("Fetching events from my.raceresult.com...")
    os.makedirs("data", exist_ok=True)

    existing = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass

    existing_ids = {
        f"{e['title']}_{e['datetime'].split()[0]}"
        for e in existing
        if "title" in e and "datetime" in e
    }

    today = datetime.now().date()
    date_from = today.isoformat()
    date_to = f"{today.year + 1}-{today.month:02d}-{today.day:02d}"

    params = {
        "modes": "map",
        "bounds": FINLAND_BOUNDS,
        "lang": "fi",
        "limit": 200,
        "dateFrom": date_from,
        "dateTo": date_to,
    }

    try:
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  Error fetching raceresult.com: {e}")
        return 0

    # Response: list with one object containing Events array
    if not isinstance(data, list) or not data:
        print("  Unexpected response format")
        return 0

    raw_events = data[0].get("Events", [])
    has_more = data[0].get("HasMore", False)
    print(f"  Found {len(raw_events)} events in Finland bounds{' (HasMore=True)' if has_more else ''}")

    new_events = []
    for ev in raw_events:
        try:
            country = ev[IDX_COUNTRY]
            if country != "FI":
                continue

            sport = ev[IDX_SPORT]
            if sport not in CYCLING_SPORT_TYPES:
                continue

            name = ev[IDX_NAME].strip()
            date_str = ev[IDX_DATE_FROM]
            city = ev[IDX_CITY].strip()
            event_id = ev[IDX_ID]

            try:
                event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if event_date < today:
                    continue
            except ValueError:
                continue

            datetime_str = f"{date_str} 08:00"
            link = f"https://my.raceresult.com/{event_id}"

            event = {
                "title": name,
                "type": sport,
                "datetime": datetime_str,
                "location": city,
                "organizer": "",
                "description": "",
                "link": link,
                "source": "raceresult",
            }

            eid = f"{name}_{date_str}"
            if eid not in existing_ids:
                new_events.append(event)
                existing_ids.add(eid)
                print(f"  + {name} ({sport}) {date_str} @ {city}")

        except (IndexError, TypeError):
            continue

    all_events = [
        e for e in existing + new_events
        if _is_future(e.get("datetime", ""), today)
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"  New: {len(new_events)}, total: {len(all_events)} — saved to {OUTPUT_FILE}")
    return len(new_events)


def _is_future(datetime_str: str, today) -> bool:
    try:
        return datetime.strptime(datetime_str.split()[0], "%Y-%m-%d").date() >= today
    except (ValueError, AttributeError):
        return True


if __name__ == "__main__":
    fetch_raceresult_events()
