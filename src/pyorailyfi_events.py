import requests
import re
import os
import json
from datetime import datetime

API_URL = "https://tulokset.pyoraily.fi/api/events/"
API_KEY = "7DK9gqUX.vjmNbW2PJlOXGrus7bSEsgCQc5wXfBiJ"

EVENT_TYPE_MAP = {
    "CMP": "Kilpailu",
    "TRA": "Harrastetapahtuma",
    "CAM": "Leiri",
    "OTH": "Muu",
}

def fetch_pyorailyfi_events():
    """
    Fetch cycling events from tulokset.pyoraily.fi API and save to JSON.
    Returns the number of new events found.
    """
    print("Fetching events from pyoraily.fi API...")

    os.makedirs("data", exist_ok=True)

    existing_events = []
    if os.path.exists("data/pyorailyfi_events.json"):
        try:
            with open("data/pyorailyfi_events.json", "r", encoding="utf-8") as f:
                existing_events = json.load(f)
            print(f"Loaded {len(existing_events)} existing events")
        except Exception as e:
            print(f"Error loading existing events: {e}")

    existing_ids = {
        f"{e['title']}_{e['datetime'].split()[0]}"
        for e in existing_events
        if "title" in e and "datetime" in e
    }

    try:
        response = requests.get(
            API_URL,
            headers={
                "Authorization": f"Api-Key {API_KEY}",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=30,
        )
        response.raise_for_status()
        raw_events = response.json()
        print(f"Fetched {len(raw_events)} events from API")
    except Exception as e:
        print(f"Error fetching events: {e}")
        return 0

    url_pattern = re.compile(r"https?://\S+")
    today = datetime.now().date()

    new_events = []
    for item in raw_events:
        start_date = item.get("start_date", "")
        if not start_date:
            continue

        try:
            event_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            continue

        if event_date < today:
            continue

        datetime_str = f"{start_date} 08:00"

        title = item.get("title", "").strip()
        if not title:
            continue

        locality = item.get("locality") or {}
        location = locality.get("name", "")

        category = item.get("category") or {}
        event_type_code = item.get("event_type", "")
        type_str = category.get("title") or EVENT_TYPE_MAP.get(event_type_code, event_type_code)

        organizer = item.get("organizer") or {}
        organizer_name = organizer.get("name", "")
        organizer_url = organizer.get("url", "") or ""

        additional_info = item.get("additional_info", "") or ""
        url_matches = url_pattern.findall(additional_info)
        link = url_matches[0] if url_matches else organizer_url

        event = {
            "title": title,
            "type": type_str,
            "datetime": datetime_str,
            "location": location,
            "organizer": organizer_name,
            "description": additional_info,
            "link": link,
            "source": "pyorailyfi",
        }

        event_id = f"{title}_{start_date}"
        if event_id not in existing_ids:
            new_events.append(event)
            existing_ids.add(event_id)
            print(f"New: {title} ({type_str}) {start_date} @ {location}")

    all_events = existing_events + new_events

    with open("data/pyorailyfi_events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"\nNew events: {len(new_events)}, total: {len(all_events)}")
    print("Saved to data/pyorailyfi_events.json")
    return len(new_events)


if __name__ == "__main__":
    fetch_pyorailyfi_events()
