"""
Scraper for Finnish cycling events from webscorer.com/findraces.

Fetches the registration listing filtered by country=Finland and sport=Cycling,
then parses the HTML table for upcoming Finnish cycling events.
"""
import requests
import re
import os
import json
from datetime import datetime, date

URL = "https://www.webscorer.com/findraces?pg=register&country=Finland&sport=Cycling"
OUTPUT_FILE = "data/webscorer_events.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

# Sport types to include (all contain "ycling" or "ountain" for MTB)
CYCLING_RE = re.compile(r"cycling|mountain bike|mtb", re.IGNORECASE)

STRIP_TAGS = re.compile(r"<[^>]+>")


def _parse_date(date_str: str) -> date | None:
    """Parse 'May 5, 2026' or 'Jan 1, 2022 - Dec 31, 2026' → first date."""
    m = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4})", date_str)
    if not m:
        return None
    try:
        return date(int(m.group(3)), MONTH_MAP[m.group(1)], int(m.group(2)))
    except ValueError:
        return None


def _parse_rows(html: str) -> list[dict]:
    """Extract race entries from HTML table rows."""
    rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.DOTALL)
    events = []
    for row in rows:
        if "register?raceid=" not in row:
            continue

        name_m = re.search(r'hm-racename">(.*?)</span>', row)
        date_m = re.search(r'hm-raceDate">(.*?)</div>', row)
        city_m = re.search(r"cityStateSpan'>(.*?)</span>", row)
        country_m = re.search(r"cityStateSpan.*?<br/>(.*?)</td>", row, re.DOTALL)
        raceid_m = re.search(r"raceid=(\d+)", row)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)

        if not (name_m and date_m and raceid_m and tds):
            continue

        country = STRIP_TAGS.sub("", country_m.group(1)).strip() if country_m else ""
        if country != "Finland":
            continue

        sport = STRIP_TAGS.sub("", tds[-1]).strip()
        if not CYCLING_RE.search(sport):
            continue

        events.append({
            "name": name_m.group(1).strip(),
            "date_str": date_m.group(1).strip(),
            "city": city_m.group(1).strip() if city_m else "",
            "sport": sport,
            "raceid": raceid_m.group(1),
        })
    return events


def fetch_webscorer_events() -> int:
    """Fetch Finnish cycling events from webscorer.com. Returns count of new events."""
    print("Fetching events from webscorer.com...")
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
        print(f"  Error fetching webscorer.com: {e}")
        return 0

    rows = _parse_rows(resp.text)
    print(f"  Found {len(rows)} Finnish cycling registrations")

    today = date.today()
    new_events = []

    for row in rows:
        event_date = _parse_date(row["date_str"])
        if not event_date:
            continue
        # Skip events more than 7 days in the past
        if (today - event_date).days > 7:
            continue
        # Skip events more than 12 months out (likely season-long series)
        if (event_date - today).days > 365:
            continue

        datetime_str = f"{event_date.isoformat()} 08:00"
        title = row["name"]
        link = f"https://www.webscorer.com/register?raceid={row['raceid']}"

        event = {
            "title": title,
            "type": row["sport"],
            "datetime": datetime_str,
            "location": row["city"],
            "organizer": "",
            "description": "",
            "link": link,
            "source": "webscorer",
        }

        eid = f"{title}_{event_date.isoformat()}"
        if eid not in existing_ids:
            new_events.append(event)
            existing_ids.add(eid)
            print(f"  + {title} ({row['sport']}) {event_date} @ {row['city']}")

    all_events = [
        e for e in existing + new_events
        if _is_future(e.get("datetime", ""), today)
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"  New: {len(new_events)}, total: {len(all_events)} — saved to {OUTPUT_FILE}")
    return len(new_events)


def _is_future(datetime_str: str, today: date) -> bool:
    try:
        return datetime.strptime(datetime_str.split()[0], "%Y-%m-%d").date() >= today
    except (ValueError, AttributeError):
        return True


if __name__ == "__main__":
    fetch_webscorer_events()
