"""
Batch geocoder for event locations.

Called from update.py after events are combined so that the Streamlit app
only needs to read pre-computed coordinates from geocache.json — no live
Nominatim calls during page load.

Retry logic:
- Locations not yet in cache are geocoded fresh.
- Locations cached as null with comma/dash separators are retried using
  progressive suffix/prefix fallback (e.g. "Tahkokangas, Oulu" → "Oulu").
- Definitively unresolvable locations (no separator, cached null) are skipped.
"""
import json
import os
import time
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

CACHE_FILE = "data/geocache.json"
EVENTS_FILE = "data/all_events.json"


def _build_candidates(location: str) -> list[str]:
    """Return geocoding candidates for a location string, best-first.

    Comma-separated: try each suffix right-to-left (city is rightmost).
      "Tahkokangas, Oulu" → ["Tahkokangas, Oulu", "Oulu"]
      "Käyrälammentie 20, 45200 Kouvola" → [..., "45200 Kouvola", "Kouvola"]

    Dash-separated: try each individual token left-to-right (start city first).
      "Lahti - Pajulahti" → ["Lahti - Pajulahti", "Lahti", "Pajulahti"]
    """
    if "," in location:
        parts = [p.strip() for p in location.split(",") if p.strip()]
        return [location] + [", ".join(parts[i:]) for i in range(1, len(parts))]
    if " - " in location:
        parts = [p.strip() for p in location.split(" - ") if p.strip()]
        return [location] + parts
    return [location]


def _should_retry_null(location: str) -> bool:
    """Return True if a null-cached location is worth retrying with fallback."""
    return "," in location or " - " in location


def geocode_all_events(verbose: bool = True) -> dict:
    """Geocode all event locations that are missing from the cache.

    Returns a summary dict: {ok, retried_ok, failed, skipped}.
    """
    # Load events
    if not os.path.exists(EVENTS_FILE):
        if verbose:
            print("  geocode_events: events file not found, skipping.")
        return {}

    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)

    unique_locations = sorted({
        (e.get("location") or "").strip()
        for e in events
        if (e.get("location") or "").strip()
    })

    # Load existing cache
    cache: dict = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass

    # Determine what needs geocoding
    to_geocode = []
    to_retry = []
    for loc in unique_locations:
        if loc not in cache:
            to_geocode.append(loc)
        elif cache[loc] is None and _should_retry_null(loc):
            to_retry.append(loc)

    if not to_geocode and not to_retry:
        if verbose:
            print(f"  Geocoding: all {len(unique_locations)} locations already cached.")
        return {"ok": 0, "retried_ok": 0, "failed": 0, "skipped": 0}

    if verbose:
        print(f"  Geocoding: {len(to_geocode)} new + {len(to_retry)} null-retry locations...")

    geolocator = Nominatim(user_agent="pyorailytapahtumat-update", timeout=10)
    geocode_fn = RateLimiter(
        geolocator.geocode, min_delay_seconds=1.5, max_retries=2, error_wait_seconds=3.0
    )

    ok = retried_ok = failed = skipped = 0

    def _try_geocode(location: str, is_retry: bool) -> bool:
        nonlocal ok, retried_ok, failed
        candidates = _build_candidates(location)
        for candidate in candidates:
            # Use cached result for this candidate if already known
            if candidate in cache:
                if cache[candidate] is not None:
                    cache[location] = cache[candidate]
                    tag = "retry-via-cache" if is_retry else "via-cache"
                    if verbose:
                        print(f"    {tag}: {location!r} → {candidate!r}")
                    if is_retry:
                        retried_ok += 1
                    else:
                        ok += 1
                    return True
                continue  # null cached, skip to next candidate

            search = (
                candidate
                if ("Finland" in candidate or "Suomi" in candidate)
                else f"{candidate}, Finland"
            )
            try:
                info = geocode_fn(search)
            except Exception as e:
                if verbose:
                    print(f"    API error for {candidate!r}: {e}")
                continue

            if info:
                result = [info.latitude, info.longitude]
                cache[candidate] = result  # cache working candidate too
                cache[location] = result
                suffix = f" (via {candidate!r})" if candidate != location else ""
                tag = "retry-ok" if is_retry else "ok"
                if verbose:
                    print(f"    {tag}: {location!r}{suffix}")
                if is_retry:
                    retried_ok += 1
                else:
                    ok += 1
                return True

        # All candidates exhausted
        cache[location] = None
        if verbose:
            print(f"    FAIL: {location!r}")
        failed += 1
        return False

    for loc in to_geocode:
        _try_geocode(loc, is_retry=False)

    for loc in to_retry:
        _try_geocode(loc, is_retry=True)

    # Persist updated cache
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  WARNING: could not write geocache: {e}")

    if verbose:
        print(
            f"  Geocoding done: {ok} new OK, {retried_ok} retried OK, "
            f"{failed} failed, {skipped} skipped."
        )

    return {"ok": ok, "retried_ok": retried_ok, "failed": failed, "skipped": skipped}


if __name__ == "__main__":
    geocode_all_events(verbose=True)
