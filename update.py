"""
Weekly update script for pyöräilytapahtumat.

Fetches events from all sources, then commits and pushes changed data
to the main branch so Streamlit Cloud picks up the update automatically.

Usage:
    python update.py            # fetch + commit + push
    python update.py --dry-run  # fetch only, no git operations
"""
import os
import sys
import subprocess
import importlib.util
from datetime import datetime

DRY_RUN = "--dry-run" in sys.argv

DATA_FILES = [
    "data/all_events.json",
    "data/bikeland_events.json",
    "data/monesko_events.json",
    "data/pyorailyfi_events.json",
    "data/raceresult_events.json",
    "data/pptiming_events.json",
    "data/webscorer_events.json",
    "data/club_events.json",
    "data/manual_events.json",
    "data/geocache.json",
]


def import_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_event_manager():
    src = os.path.join(os.path.dirname(__file__), "src", "event_manager.py")
    manager = import_module("event_manager", src)
    return manager.combine_all_events()


def run_geocoder():
    src = os.path.join(os.path.dirname(__file__), "src", "geocode_events.py")
    geocoder = import_module("geocode_events", src)
    return geocoder.geocode_all_events(verbose=True)


def git_has_changes():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--"] + DATA_FILES,
        capture_output=True,
    )
    # exit code 1 = changes exist, 0 = no changes
    return result.returncode != 0


def git_commit_and_push():
    date_str = datetime.now().strftime("%Y-%m-%d")

    existing = [f for f in DATA_FILES if os.path.exists(f)]
    subprocess.run(["git", "add", "--"] + existing, check=True)

    subprocess.run(
        ["git", "commit", "-m", f"chore: update events {date_str}"],
        check=True,
    )
    subprocess.run(["git", "push", "origin", "main"], check=True)


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"=== Pyöräilytapahtumat Update {ts}{' [DRY RUN]' if DRY_RUN else ''} ===\n")

    print("Fetching events from all sources...")
    total = run_event_manager()
    print(f"\nFetching done - {total} events in total.\n")

    print("Geocoding event locations...")
    run_geocoder()
    print()

    if DRY_RUN:
        print("Dry run: skipping git operations.")
        return

    print("Checking for changes in data files...")
    if git_has_changes():
        print("Changes detected - committing and pushing to main...")
        try:
            git_commit_and_push()
            print("Done! Streamlit Cloud will pick up the update shortly.")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: git operation failed: {e}")
            sys.exit(1)
    else:
        print("No changes detected - nothing to commit.")


if __name__ == "__main__":
    main()
