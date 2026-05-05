import requests
import re
import os
import json
from datetime import datetime

URL = "https://www.bikeland.fi/tapahtumat/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _clean_html(raw):
    return re.sub(r"<.*?>", "", str(raw)).strip()


def _parse_date(date_str):
    """Return (iso_datetime, location) from a bikeland date string.

    Input examples:
      "23.05.2026 | Lohja"
      "03.07.2026-04.07.2026 | Saariselkä"
    """
    clean = _clean_html(date_str)
    # Extract first DD.MM.YYYY date
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", clean)
    if not m:
        return None, ""
    day, month, year = m.groups()
    iso = f"{year}-{month.zfill(2)}-{day.zfill(2)} 08:00"
    location = clean.split("|", 1)[1].strip() if "|" in clean else ""
    return iso, location


def scrape_bikeland_events():
    """Scrape upcoming events from Bikeland.fi. Returns count of new events."""
    print("Scraping events from Bikeland.fi...")
    os.makedirs("data", exist_ok=True)

    existing_events = []
    if os.path.exists("data/bikeland_events.json"):
        try:
            with open("data/bikeland_events.json", "r", encoding="utf-8") as f:
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
        response = requests.get(URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {URL}: {e}")
        return 0

    # Only use upcoming_eventdata — past events are already gone
    m = re.search(r"var upcoming_eventdata = ({.*?});", response.text, re.DOTALL)
    if not m:
        print("Could not find upcoming_eventdata in page source.")
        return 0

    try:
        raw_data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"Failed to parse upcoming_eventdata JSON: {e}")
        return 0

    print(f"Found {len(raw_data)} upcoming events on page")

    today = datetime.now().date()
    new_events = []

    for event_id, info in raw_data.items():
        title = info.get("title", "").strip()
        if not title:
            continue

        dates_obj = info.get("dates", {})
        datetime_str, location = None, ""
        for items in dates_obj.values():
            if items:
                datetime_str, location = _parse_date(items[0])
                break

        if not datetime_str:
            continue

        # Skip past events (shouldn't be in upcoming_eventdata, but just in case)
        try:
            event_date = datetime.strptime(datetime_str.split()[0], "%Y-%m-%d").date()
            if event_date < today:
                continue
        except ValueError:
            continue

        categories = info.get("categories", [])
        type_str = ", ".join(categories).upper() if categories else "Muu"

        event = {
            "title": title,
            "type": type_str,
            "datetime": datetime_str,
            "location": location,
            "organizer": "",
            "description": _clean_html(info.get("ingress", "")),
            "link": info.get("url", ""),
            "source": "bikeland",
        }

        eid = f"{title}_{datetime_str.split()[0]}"
        if eid not in existing_ids:
            new_events.append(event)
            existing_ids.add(eid)
            print(f"New: {title} ({type_str}) {datetime_str[:10]} @ {location}")

    all_events = existing_events + new_events

    # Drop events that are now in the past from the stored list
    all_events = [
        e for e in all_events
        if _date_is_future(e.get("datetime", ""), today)
    ]

    with open("data/bikeland_events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"\nNew events: {len(new_events)}, total stored: {len(all_events)}")
    print("Saved to data/bikeland_events.json")
    return len(new_events)


def _date_is_future(datetime_str, today):
    try:
        return datetime.strptime(datetime_str.split()[0], "%Y-%m-%d").date() >= today
    except (ValueError, AttributeError):
        return True  # keep events with unparseable dates


if __name__ == "__main__":
    scrape_bikeland_events()
