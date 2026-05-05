import os
import json
from datetime import datetime
import sys
import importlib.util

def import_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

current_dir = os.path.dirname(os.path.abspath(__file__))
bikeland_events = import_module_from_file("bikeland_events", os.path.join(current_dir, "bikeland_events.py"))
manual_events = import_module_from_file("manual_events", os.path.join(current_dir, "manual_events.py"))
pyorailyfi_events = import_module_from_file("pyorailyfi_events", os.path.join(current_dir, "pyorailyfi_events.py"))
club_events = import_module_from_file("club_events", os.path.join(current_dir, "club_events.py"))
raceresult_events = import_module_from_file("raceresult_events", os.path.join(current_dir, "raceresult_events.py"))

SOURCE_PRIORITY = ["manual_edit", "manual", "pyorailyfi", "raceresult", "bikeland", "club_wp"]

SOURCE_NAMES = {
    "manual_edit": "admin-paneeli",
    "manual": "manuaalinen syöttö",
    "pyorailyfi": "pyoraily.fi",
    "raceresult": "RaceResult",
    "bikeland": "Bikeland.fi",
    "club_wp": "Pyöräilyseura",
}


def create_event_id(event):
    if "title" in event and "datetime" in event:
        date_part = event["datetime"].split()[0] if " " in event["datetime"] else event["datetime"]
        return f"{event['title']}_{date_part}"
    return None


def add_timestamp_to_event(event, existing_events_dict=None):
    event_id = create_event_id(event)
    if existing_events_dict and event_id in existing_events_dict and "added_timestamp" in existing_events_dict[event_id]:
        event["added_timestamp"] = existing_events_dict[event_id]["added_timestamp"]
    elif "added_timestamp" not in event:
        event["added_timestamp"] = datetime.now().isoformat()
    return event


def combine_all_events():
    print("Fetching events from all sources...")

    os.makedirs("output", exist_ok=True)

    bikeland_count = bikeland_events.scrape_bikeland_events()
    manual_count = manual_events.process_manual_events()
    pyorailyfi_count = pyorailyfi_events.fetch_pyorailyfi_events()
    raceresult_count = raceresult_events.fetch_raceresult_events()
    club_count = club_events.fetch_club_events()

    print(f"\nNew events fetched:")
    print(f"  Bikeland:    {bikeland_count}")
    print(f"  pyoraily.fi: {pyorailyfi_count}")
    print(f"  RaceResult:  {raceresult_count}")
    print(f"  Seurat:      {club_count}")
    print(f"  Manual:      {manual_count}")

    # Load existing events to preserve timestamps
    existing_events_dict = {}
    if os.path.exists("data/all_events.json"):
        try:
            with open("data/all_events.json", "r", encoding="utf-8") as f:
                for event in json.load(f):
                    event_id = create_event_id(event)
                    if event_id:
                        existing_events_dict[event_id] = event
        except Exception as e:
            print(f"Warning: could not load existing events: {e}")

    all_events = []

    # Load sources in priority order (lowest first so higher priority can override)
    sources = [
        ("data/bikeland_events.json", "Bikeland"),
        ("data/pyorailyfi_events.json", "pyoraily.fi"),
        ("data/raceresult_events.json", "RaceResult"),
        ("data/club_events.json", "Seurat"),
        ("data/manual_events.json", "Manual"),
        ("data/manual_edits.json", "Admin edits"),
    ]

    for path, label in sources:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    events = json.load(f)
                for event in events:
                    add_timestamp_to_event(event, existing_events_dict)
                all_events.extend(events)
                print(f"Loaded {len(events):>4} events from {label}")
            except Exception as e:
                print(f"Warning: could not load {path}: {e}")

    # Load blacklist
    blacklist = set()
    if os.path.exists("data/event_blacklist.json"):
        try:
            with open("data/event_blacklist.json", "r", encoding="utf-8") as f:
                blacklist = set(json.load(f))
        except Exception as e:
            print(f"Warning: could not load blacklist: {e}")

    # Deduplicate: higher priority source wins
    unique_events = {}
    blacklisted_count = 0

    for event in all_events:
        event_id = create_event_id(event)
        if not event_id:
            continue
        if event_id in blacklist:
            blacklisted_count += 1
            continue

        if event_id not in unique_events:
            unique_events[event_id] = event
        else:
            existing_priority = SOURCE_PRIORITY.index(unique_events[event_id].get("source", "bikeland")) \
                if unique_events[event_id].get("source") in SOURCE_PRIORITY else 99
            new_priority = SOURCE_PRIORITY.index(event.get("source", "bikeland")) \
                if event.get("source") in SOURCE_PRIORITY else 99
            if new_priority < existing_priority:
                unique_events[event_id] = event

    combined = sorted(unique_events.values(), key=lambda x: x.get("datetime", "9999-99-99"))

    print(f"\nTotal unique events: {len(combined)}  (blacklisted: {blacklisted_count})")

    with open("data/all_events.json", "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    _generate_slack_output(combined)
    return len(combined)


def _generate_slack_output(events):
    os.makedirs("output", exist_ok=True)
    with open("output/clean_combined_events.txt", "w", encoding="utf-8") as f:
        for event in events:
            try:
                date_obj = datetime.strptime(event["datetime"].split()[0], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d.%m.%Y")
            except Exception:
                formatted_date = event.get("datetime", "")

            source_name = SOURCE_NAMES.get(event.get("source", ""), "tuntematon lähde")
            description = (
                f"{event['title']} järjestetään {formatted_date} "
                f"paikkakunnalla {event.get('location', '?')}."
            )
            if event.get("organizer"):
                description += f" Järjestäjänä toimii {event['organizer']}."
            description += f" (Lähde: {source_name})"
            if event.get("description"):
                description += f" Lisätiedot: {event['description']}"
            if event.get("link"):
                description += f" Lisätietoja tapahtumasta: {event['link']}"
            description += "\n\n⚠️ HOX! Tarkista aina tapahtumatiedot järjestäjän sivulta, varsinkin aloitusaika saattaa olla väärin."

            f.write(f"""/create
title: {event['title']} ({event.get('type', '')})
channel: #ulkotapahtumakalenteri
datetime: {event['datetime']}
description: {description}

💡 **Ohjeet:** Klikkaa haluamaasi emojia ilmoittaaksesi osallistumisesi tai kiinnostuksesi. Emojin valinnan jälkeen sivupalkkiin avautuu chätti, jossa voit keskustella muiden osallistujien kanssa.
---
""")


def main():
    print("=== Pyöräilytapahtumakalenteri - Event Manager ===")
    total = combine_all_events()
    print(f"\nValmis. Tapahtumia yhteensä: {total}")
    print("Käynnistä Streamlit-sovellus: python -m streamlit run src/event_map_app.py")


if __name__ == "__main__":
    main()
