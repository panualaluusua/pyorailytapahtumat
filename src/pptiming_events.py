"""
Scraper for Finnish cycling events from pptiming.fi.

PP Timing is a Finnish timing company that manages road races, criteriums,
gravel and MTB events - including many SM-kilpailut (Finnish championships).
These events are NOT found via the RaceResult geographic bounds API because
they lack coordinate data in RaceResult's system.

The page lists upcoming events as anchor tags with Finnish date text
(D.M.YYYY or DD.M.YYYY) embedded in the link text.
"""
import requests
import re
import os
import json
from datetime import datetime, date

URL = "https://www.pptiming.fi/"
OUTPUT_FILE = "data/pptiming_events.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# Skip these link texts (results/live links on current event block)
SKIP_TEXT_RE = re.compile(
    r"l.ht.listat|liveseuranta|tulosarkisto", re.IGNORECASE
)

# Skip hrefs pointing back to pptiming results pages or navigation
SKIP_HREF_RE = re.compile(
    r"pptiming\.fi/(tulosarkisto|tunnistinohje|privacy|$)|"
    r"raceresult\.com/\d+/(results|participants)",
    re.IGNORECASE,
)

# Finnish date patterns: "16.5.2026" or "13.-14.6.2026" (range → use first date)
DATE_RE = re.compile(r"(\d{1,2})\.-?(?:\d{1,2}\.)?(\d{1,2})\.(20\d{2})")

# Clean serial number prefix like "14.", "18.", "68." from event names
SERIAL_RE = re.compile(r"^\d+\.\s*")


def _parse_date(text: str) -> date | None:
    """Extract the first Finnish date from text and return as date object."""
    m = DATE_RE.search(text)
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def _clean_name_and_location(text: str) -> tuple[str, str]:
    """
    Strip the date portion from link text, clean serial prefix,
    and try to extract a location from a trailing ', City' pattern.

    Returns (name, location).
    """
    # Remove the date (and surrounding punctuation/spaces) from text
    cleaned = DATE_RE.sub("", text).strip(" ,.-")

    # Remove a leading serial number like "14. " or "68. "
    cleaned = SERIAL_RE.sub("", cleaned).strip()

    # Try to extract trailing location: "Event Name, City"
    # Only split on the LAST comma to avoid splitting event names like "Porvoon Ajot & SM-kilpailut"
    location = ""
    if "," in cleaned:
        parts = cleaned.rsplit(",", 1)
        candidate_loc = parts[1].strip()
        # Accept as location if it's 2-30 chars and looks like a city (no date digits)
        if 2 <= len(candidate_loc) <= 30 and not re.search(r"\d", candidate_loc):
            location = candidate_loc
            cleaned = parts[0].strip()

    return cleaned, location


def _classify_type(name: str) -> str:
    """Classify event type based on name keywords."""
    n = name.lower()
    if re.search(r"gravel", n):
        return "Gravel"
    if re.search(r"maasto|mtb|xcо|xco|xcc|xce", n):
        return "Maastopyöräily"
    return "Maantie"


def _parse_events(html: str) -> list[dict]:
    """Extract upcoming events from PP Timing front page HTML."""
    events = []

    # Find all anchor tags in the page content
    for m in re.finditer(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
        href = m.group(1).strip()
        raw_text = re.sub(r"<[^>]+>", "", m.group(2))  # strip inner HTML
        raw_text = raw_text.replace("&amp;", "&").replace("&#8211;", "-").strip()

        # Skip navigation and results links
        if SKIP_HREF_RE.search(href):
            continue
        if SKIP_TEXT_RE.search(raw_text):
            continue

        # Must contain a recognisable date
        event_date = _parse_date(raw_text)
        if event_date is None:
            continue

        name, location = _clean_name_and_location(raw_text)
        if not name:
            continue

        events.append({
            "name": name,
            "date": event_date,
            "location": location,
            "href": href,
        })

    return events


def fetch_pptiming_events() -> int:
    """Fetch Finnish cycling events from pptiming.fi. Returns count of new events."""
    print("Fetching events from pptiming.fi...")
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

    try:
        resp = requests.get(URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Error fetching pptiming.fi: {e}")
        return 0

    parsed = _parse_events(resp.text)
    print(f"  Found {len(parsed)} upcoming events")

    today = date.today()
    new_events = []

    for row in parsed:
        event_date = row["date"]
        # Skip events more than 7 days in the past
        if (today - event_date).days > 7:
            continue

        datetime_str = f"{event_date.isoformat()} 08:00"
        name = row["name"]
        event_type = _classify_type(name)

        event = {
            "title": name,
            "type": event_type,
            "datetime": datetime_str,
            "location": row["location"],
            "organizer": "PP Timing",
            "description": "",
            "link": row["href"],
            "source": "pptiming",
        }

        eid = f"{name}_{event_date.isoformat()}"
        if eid not in existing_ids:
            new_events.append(event)
            existing_ids.add(eid)
            loc_str = f" @ {row['location']}" if row["location"] else ""
            print(f"  + {name} ({event_type}) {event_date}{loc_str}")

    all_events = [
        e for e in existing + new_events
        if _is_future(e.get("datetime", ""), today)
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"  New: {len(new_events)}, total: {len(all_events)} - saved to {OUTPUT_FILE}")
    return len(new_events)


def _is_future(datetime_str: str, today: date) -> bool:
    try:
        return datetime.strptime(datetime_str.split()[0], "%Y-%m-%d").date() >= today
    except (ValueError, AttributeError):
        return True


if __name__ == "__main__":
    fetch_pptiming_events()
