"""
Generic scraper for Finnish cycling club websites.
Supports WordPress REST API and RSS feeds.

Clubs are configured in data/club_sources.json.
Events are detected by finding future Finnish dates in post titles/content.
"""
import calendar
import requests
import re
import os
import json
import html
from datetime import datetime, date
from urllib.parse import urlparse

SOURCES_FILE = "data/club_sources.json"
OUTPUT_FILE = "data/club_events.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
}
TIMEOUT = 12

# Finnish date patterns: "30.5.2026", "30.5.", "TI 5.5 18:00"
DATE_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")
DATE_SHORT_RE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.\s")  # "30.5. " with trailing dot
DATE_BARE_RE = re.compile(r"(?<!\d)(\d{1,2})\.(\d{1,2})(?![\d.])\s")  # "5.5 " no trailing dot
STRIP_TAGS = re.compile(r"<[^>]+>")

MONTH_FI = {
    "tammikuu": 1, "tammikuuta": 1, "helmikuu": 2, "helmikuuta": 2,
    "maaliskuu": 3, "maaliskuuta": 3, "huhtikuu": 4, "huhtikuuta": 4,
    "toukokuu": 5, "toukokuuta": 5, "kesäkuu": 6, "kesäkuuta": 6,
    "heinäkuu": 7, "heinäkuuta": 7, "elokuu": 8, "elokuuta": 8,
    "syyskuu": 9, "syyskuuta": 9, "lokakuu": 10, "lokakuuta": 10,
    "marraskuu": 11, "marraskuuta": 11, "joulukuu": 12, "joulukuuta": 12,
}

# Keywords that suggest a post is about an event
# WP category slugs/names that indicate event content
EVENT_CATEGORY_PATTERNS = re.compile(
    r"tapahtumat?|kilpailut?|ajot?|viikkoajot?|kruisinki|retket?|race|event",
    re.IGNORECASE,
)

EVENT_KEYWORDS = re.compile(
    r"\btapahtuma\w*|\bkilpailu\w*|\bretki\w*|\bkisa\w*|\brace\b|\bcup\b"
    r"|\bmarathon\b|\btour\b|\bgran.fondo\b|\bfestivaal\w*|\bleiri\w*"
    r"|\bcamp\b|\bharjoitus\w*|\bavajais\w*|\bviikkoajo\w*|\blähtö\w*",
    re.IGNORECASE,
)

NEGATIVE_KEYWORDS = re.compile(
    r"\btilaus\b|\btarjous\b|\billmoittaudu\b|\bjäsenmaksu\b|\brekisteröi\b",
    re.IGNORECASE,
)


def _clean(text: str) -> str:
    text = STRIP_TAGS.sub(" ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _find_future_dates(text: str, today: date) -> list[date]:
    """Extract all future Finnish dates from a text string.
    Full dates (dd.mm.yyyy) are accepted up to 12 months out.
    Short dates (dd.mm or dd.mm.) without explicit year are only accepted
    up to 8 months out, since ambiguous year inference beyond that is unreliable."""
    found = []
    current_year = today.year
    max_future = date(today.year + 1, today.month, today.day)
    # Short dates without explicit year: cap at 8 months to avoid assigning
    # stale past-month posts (e.g. March weekly rides) to next year
    max_short_month = today.month + 8
    max_short_year = today.year + (max_short_month - 1) // 12
    max_short_month = (max_short_month - 1) % 12 + 1
    max_short_day = min(today.day, calendar.monthrange(max_short_year, max_short_month)[1])
    max_short_future = date(max_short_year, max_short_month, max_short_day)

    for m in DATE_RE.finditer(text):
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            d = date(year, month, day)
            if today <= d <= max_future:
                found.append(d)
        except ValueError:
            pass

    def _try_short_date(day: int, month: int) -> None:
        try:
            d_this = date(current_year, month, day)
            if d_this >= today:
                found.append(d_this)
                return
            d_next = date(current_year + 1, month, day)
            if d_next <= max_short_future:
                found.append(d_next)
        except ValueError:
            pass

    # "30.5. " with trailing dot
    for m in DATE_SHORT_RE.finditer(text):
        _try_short_date(int(m.group(1)), int(m.group(2)))

    # "5.5 18:00" / "TI 5.5 " — bare day.month without trailing dot
    for m in DATE_BARE_RE.finditer(text):
        _try_short_date(int(m.group(1)), int(m.group(2)))

    return sorted(set(found))


def _post_to_event(post_title: str, post_content: str, post_link: str,
                   club_name: str, today: date,
                   require_keyword_in_title: bool = True) -> dict | None:
    """Try to extract an event from a WP post or RSS item."""
    title = _clean(post_title)
    content = _clean(post_content)
    combined = f"{title} {content}"

    # Keyword check: require in title when no event category was used
    search_target = title if require_keyword_in_title else combined
    if not EVENT_KEYWORDS.search(search_target):
        return None

    # Skip posts that are clearly about orders, offers, registrations
    if NEGATIVE_KEYWORDS.search(title):
        return None

    # Prefer dates found in the title (more likely to be the actual event date)
    title_dates = _find_future_dates(title, today)
    content_dates = _find_future_dates(content[:500], today)
    dates = title_dates or content_dates
    if not dates:
        return None

    # If the title contains a past full date (dd.mm.yyyy), skip — event is over
    for m in DATE_RE.finditer(title):
        try:
            d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if d < today:
                return None
        except ValueError:
            pass

    # If the title contains a past short date (dd.mm. or dd.mm) with no future match, skip
    for pattern in (DATE_SHORT_RE, DATE_BARE_RE):
        for m in pattern.finditer(title):
            try:
                d_this = date(today.year, int(m.group(2)), int(m.group(1)))
                if d_this < today and not title_dates:
                    return None
            except ValueError:
                pass

    event_date = dates[0]

    # Try to find a location: look for "Paikka:", "paikkakunta:" or city after "|"
    location = ""
    loc_match = re.search(
        r"(?:paikka|paikkakunta|sijainti|venue)[:\s]+([A-ZÄÖÅ][^\n,.<]{2,30})",
        combined, re.IGNORECASE
    )
    if loc_match:
        location = loc_match.group(1).strip()
    else:
        # Fallback: use club's home city if we can infer it
        if "oulu" in club_name.lower():
            location = "Oulu"
        elif "jyväskylä" in club_name.lower() or "jyps" in club_name.lower():
            location = "Jyväskylä"
        elif "tampere" in club_name.lower():
            location = "Tampere"
        elif "lahti" in club_name.lower() or "lahden" in club_name.lower():
            location = "Lahti"
        elif "lappeenranta" in club_name.lower():
            location = "Lappeenranta"
        elif "kuopio" in club_name.lower() or "kuopys" in club_name.lower():
            location = "Kuopio"
        elif "espoo" in club_name.lower() or "ik-32" in club_name.lower():
            location = "Espoo"

    return {
        "title": title,
        "type": "Seura",
        "datetime": f"{event_date.isoformat()} 08:00",
        "location": location,
        "organizer": club_name,
        "description": content[:300] if len(content) > 50 else "",
        "link": post_link,
        "source": "club_wp",
    }


# ── WP REST API ──────────────────────────────────────────────────────────────

def _get_event_category_ids(base: str) -> list[int]:
    """Return WP category IDs that look event-related."""
    try:
        resp = requests.get(
            f"{base}/wp-json/wp/v2/categories?per_page=50&_fields=id,name,slug",
            headers=HEADERS, timeout=TIMEOUT,
        )
        cats = resp.json()
        if not isinstance(cats, list):
            return []
        return [
            c["id"] for c in cats
            if EVENT_CATEGORY_PATTERNS.search(c.get("slug", "") + " " + c.get("name", ""))
        ]
    except Exception:
        return []


def _scrape_wp(club: dict, today: date) -> list[dict]:
    base = club["url"].rstrip("/")

    # Try to find event-specific categories first
    cat_ids = _get_event_category_ids(base)
    if cat_ids:
        cat_param = ",".join(str(i) for i in cat_ids)
        url = f"{base}/wp-json/wp/v2/posts?per_page=30&categories={cat_param}&_fields=title,date,link,content,excerpt"
        print(f"    Using event categories: {cat_ids}")
    else:
        url = f"{base}/wp-json/wp/v2/posts?per_page=30&_fields=title,date,link,content,excerpt"
        print(f"    No event categories found, scanning all recent posts")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        posts = resp.json()
    except Exception as e:
        print(f"  WP API error for {club['name']}: {e}")
        return []

    events = []
    for post in posts:
        try:
            post_date = datetime.fromisoformat(post["date"]).date()
            # If we have event categories, look back further (180 days for scheduled events)
            lookback = 180 if cat_ids else 60
            if (today - post_date).days > lookback:
                continue
        except Exception:
            pass

        title = post.get("title", {}).get("rendered", "")
        content = post.get("content", {}).get("rendered", "") or \
                  post.get("excerpt", {}).get("rendered", "")
        link = post.get("link", "")

        ev = _post_to_event(title, content, link, club["name"], today,
                            require_keyword_in_title=not bool(cat_ids))
        if ev:
            events.append(ev)

    return events


# ── RSS ──────────────────────────────────────────────────────────────────────

def _scrape_rss(club: dict, today: date) -> list[dict]:
    base = club["url"].rstrip("/")
    url = f"{base}/feed/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        xml = resp.text
    except Exception as e:
        print(f"  RSS error for {club['name']}: {e}")
        return []

    events = []
    # Parse items with simple regex (avoids xml dependency issues with encodings)
    items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
    for item in items:
        title_m = re.search(r"<title><!\[CDATA\[(.*?)\]\]>|<title>(.*?)</title>", item, re.DOTALL)
        link_m = re.search(r"<link>(.*?)</link>", item, re.DOTALL)
        desc_m = re.search(r"<description><!\[CDATA\[(.*?)\]\]>|<description>(.*?)</description>", item, re.DOTALL)
        pub_m = re.search(r"<pubDate>(.*?)</pubDate>", item)

        title = (title_m.group(1) or title_m.group(2) or "").strip() if title_m else ""
        link = link_m.group(1).strip() if link_m else ""
        desc = (desc_m.group(1) or desc_m.group(2) or "").strip() if desc_m else ""

        # Skip old items
        if pub_m:
            try:
                from email.utils import parsedate_to_datetime
                pub_date = parsedate_to_datetime(pub_m.group(1).strip()).date()
                if (today - pub_date).days > 60:
                    continue
            except Exception:
                pass

        ev = _post_to_event(title, desc, link, club["name"], today)
        if ev:
            events.append(ev)

    return events


# ── Main ─────────────────────────────────────────────────────────────────────

def fetch_club_events() -> int:
    """Fetch events from all configured club sources. Returns count of new events."""
    print("Fetching events from cycling club websites...")
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(SOURCES_FILE):
        print(f"No club sources config found at {SOURCES_FILE}")
        return 0

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        clubs = json.load(f)

    existing = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass

    existing_ids = {
        f"{e['title']}_{e['datetime'].split()[0]}"
        for e in existing if "title" in e and "datetime" in e
    }

    today = datetime.now().date()
    new_events = []

    for club in clubs:
        print(f"  {club['name']} ({club['type']})...")
        method = club.get("type", "wp_api")

        if method == "wp_api":
            found = _scrape_wp(club, today)
        elif method == "rss":
            found = _scrape_rss(club, today)
        else:
            print(f"    Unknown type '{method}', skipping")
            continue

        for ev in found:
            eid = f"{ev['title']}_{ev['datetime'].split()[0]}"
            if eid not in existing_ids:
                new_events.append(ev)
                existing_ids.add(eid)
                print(f"    + {ev['title']} ({ev['datetime'][:10]}) @ {ev['location']}")

        if not found:
            print(f"    No events found")

    # Keep only future events
    all_events = [
        e for e in existing + new_events
        if _is_future(e.get("datetime", ""), today)
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"\nNew club events: {len(new_events)}, total: {len(all_events)}")
    print(f"Saved to {OUTPUT_FILE}")
    return len(new_events)


def _is_future(datetime_str: str, today: date) -> bool:
    try:
        return datetime.strptime(datetime_str.split()[0], "%Y-%m-%d").date() >= today
    except (ValueError, AttributeError):
        return True


if __name__ == "__main__":
    fetch_club_events()
