import json
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import bikeland_events
import club_events
import event_manager
import manual_events
import monesko_events
import pyorailyfi_events
import raceresult_events
import webscorer_events


class FakeResponse:
    def __init__(self, *, json_data=None, text="", status_code=200):
        self._json_data = json_data
        self.text = text
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@contextmanager
def temporary_cwd():
    previous = os.getcwd()
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        try:
            yield Path(temp_dir)
        finally:
            os.chdir(previous)


def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class BikelandSourceTests(unittest.TestCase):
    def test_scrape_bikeland_events_parses_upcoming_eventdata(self):
        html = """
        <script>
        var upcoming_eventdata = {
          "1": {
            "title": "Test Gravel",
            "dates": {"0": ["15.06.2099 | Helsinki"]},
            "categories": ["Gravel", "MTB"],
            "ingress": "<p>Ajettava tapahtuma</p>",
            "url": "https://example.com/test-gravel"
          }
        };
        </script>
        """
        with temporary_cwd():
            with patch.object(
                bikeland_events.requests,
                "get",
                return_value=FakeResponse(text=html),
            ):
                count = bikeland_events.scrape_bikeland_events()

            self.assertEqual(count, 1)
            stored = read_json("data/bikeland_events.json")
            self.assertEqual(stored[0]["title"], "Test Gravel")
            self.assertEqual(stored[0]["datetime"], "2099-06-15 08:00")
            self.assertEqual(stored[0]["location"], "Helsinki")
            self.assertEqual(stored[0]["type"], "GRAVEL, MTB")
            self.assertEqual(stored[0]["source"], "bikeland")


class PyorailyFiSourceTests(unittest.TestCase):
    def test_fetch_pyorailyfi_events_filters_and_maps_fields(self):
        payload = [
            {
                "title": "Kevatajo",
                "start_date": "2099-05-20",
                "locality": {"name": "Turku"},
                "category": {"title": "Maantie"},
                "event_type": "CMP",
                "organizer": {"name": "Testiseura", "url": "https://example.com/org"},
                "additional_info": "Lisatiedot https://example.com/event",
            },
            {
                "title": "Vanha ajo",
                "start_date": "2000-01-01",
                "locality": {"name": "Lahti"},
                "category": {"title": "Gravel"},
                "event_type": "CMP",
                "organizer": {"name": "Vanhaseura", "url": "https://example.com/old"},
                "additional_info": "",
            },
        ]
        with temporary_cwd():
            with patch.object(
                pyorailyfi_events.requests,
                "get",
                return_value=FakeResponse(json_data=payload),
            ):
                count = pyorailyfi_events.fetch_pyorailyfi_events()

            self.assertEqual(count, 1)
            stored = read_json("data/pyorailyfi_events.json")
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["title"], "Kevatajo")
            self.assertEqual(stored[0]["type"], "Maantie")
            self.assertEqual(stored[0]["link"], "https://example.com/event")
            self.assertEqual(stored[0]["organizer"], "Testiseura")
            self.assertEqual(stored[0]["source"], "pyorailyfi")


class RaceResultSourceTests(unittest.TestCase):
    def test_fetch_raceresult_events_keeps_only_finnish_cycling_events(self):
        payload = [
            {
                "Events": [
                    [123, None, "Nordic Gravel", "2099-07-01", "2099-07-01", "Oulu", "FI", 0, 0, None, "Cycling"],
                    [124, None, "Juoksu", "2099-07-01", "2099-07-01", "Oulu", "FI", 0, 0, None, "Running"],
                    [125, None, "Sweden Ride", "2099-07-01", "2099-07-01", "Stockholm", "SE", 0, 0, None, "Cycling"],
                ],
                "HasMore": False,
            }
        ]
        with temporary_cwd():
            with patch.object(
                raceresult_events.requests,
                "get",
                return_value=FakeResponse(json_data=payload),
            ):
                count = raceresult_events.fetch_raceresult_events()

            self.assertEqual(count, 1)
            stored = read_json("data/raceresult_events.json")
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["title"], "Nordic Gravel")
            self.assertEqual(stored[0]["location"], "Oulu")
            self.assertEqual(stored[0]["link"], "https://my.raceresult.com/123")
            self.assertEqual(stored[0]["source"], "raceresult")


class MoneskoSourceTests(unittest.TestCase):
    def test_fetch_monesko_events_uses_api_payload(self):
        api_events = [
            {
                "title": "Monesko Gravel",
                "start_date": "2099-08-10T18:30:00",
                "description": "<p>Soratieajo</p>",
                "categories": [{"name": "Pyoraily"}, {"name": "Gravel"}],
                "venue": {"venue": "Keskus", "city": "Helsinki", "country": "Finland"},
                "organizer": [{"organizer": "Monesko ry"}],
                "website": "https://example.com/monesko",
            }
        ]
        with temporary_cwd():
            with patch.object(monesko_events, "_fetch_api_events", return_value=api_events):
                count = monesko_events.fetch_monesko_events()

            self.assertEqual(count, 1)
            stored = read_json("data/monesko_events.json")
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["title"], "Monesko Gravel")
            self.assertEqual(stored[0]["type"], "Gravel")
            self.assertEqual(stored[0]["datetime"], "2099-08-10 18:30")
            self.assertEqual(stored[0]["location"], "Keskus, Helsinki, Finland")
            self.assertEqual(stored[0]["source"], "monesko")

    def test_fetch_monesko_events_falls_back_to_ics(self):
        ics_events = [
            {
                "title": "Fallback Ride",
                "type": "Pyoraily",
                "datetime": "2099-09-01 08:00",
                "location": "Tampere",
                "organizer": "Monesko",
                "description": "Fallback source",
                "link": "https://example.com/fallback",
                "source": "monesko",
            }
        ]
        with temporary_cwd():
            with patch.object(monesko_events, "_fetch_api_events", side_effect=RuntimeError("boom")):
                with patch.object(monesko_events, "_fetch_ics_events", return_value=ics_events):
                    count = monesko_events.fetch_monesko_events()

            self.assertEqual(count, 1)
            stored = read_json("data/monesko_events.json")
            self.assertEqual(stored[0]["title"], "Fallback Ride")
            self.assertEqual(stored[0]["source"], "monesko")


class WebscorerSourceTests(unittest.TestCase):
    def test_fetch_webscorer_events_parses_finnish_cycling_rows(self):
        future = date.today() + timedelta(days=30)
        future_label = future.strftime("%b %d, %Y")
        html = """
        <table>
          <tr>
            <td><a href="/register?raceid=555"><span class="hm-racename">Forest Loop</span></a></td>
            <td><div class="hm-raceDate">__FUTURE_DATE__</div></td>
            <td><span class='cityStateSpan'>Espoo</span><br/>Finland</td>
            <td>Cycling</td>
          </tr>
          <tr>
            <td><a href="/register?raceid=556"><span class="hm-racename">Run Event</span></a></td>
            <td><div class="hm-raceDate">__FUTURE_DATE__</div></td>
            <td><span class='cityStateSpan'>Espoo</span><br/>Finland</td>
            <td>Running</td>
          </tr>
        </table>
        """.replace("__FUTURE_DATE__", future_label)
        with temporary_cwd():
            with patch.object(
                webscorer_events.requests,
                "get",
                return_value=FakeResponse(text=html),
            ):
                count = webscorer_events.fetch_webscorer_events()

            self.assertEqual(count, 1)
            stored = read_json("data/webscorer_events.json")
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["title"], "Forest Loop")
            self.assertEqual(stored[0]["location"], "Espoo")
            self.assertEqual(stored[0]["link"], "https://www.webscorer.com/register?raceid=555")
            self.assertEqual(stored[0]["source"], "webscorer")


class ClubSourceTests(unittest.TestCase):
    def test_fetch_club_events_parses_wordpress_source(self):
        future = date.today() + timedelta(days=30)
        future_title = f"Kevatretki {future.day}.{future.month}.{future.year}"
        post_date = date.today().isoformat() + "T12:00:00"
        clubs = [{"name": "Testiseura", "url": "https://example.com", "type": "wp_api"}]
        posts = [
            {
                "date": post_date,
                "title": {"rendered": future_title},
                "content": {"rendered": "<p>Tapahtuma Paikka: Helsinki</p>"},
                "excerpt": {"rendered": ""},
                "link": "https://example.com/kevatretki",
            }
        ]

        def fake_get(url, **kwargs):
            if "/categories?" in url:
                return FakeResponse(json_data=[{"id": 7, "name": "Tapahtumat", "slug": "tapahtumat"}])
            if "/posts?" in url:
                return FakeResponse(json_data=posts)
            raise AssertionError(f"Unexpected URL: {url}")

        with temporary_cwd():
            os.makedirs("data", exist_ok=True)
            with open("data/club_sources.json", "w", encoding="utf-8") as handle:
                json.dump(clubs, handle)

            with patch.object(club_events.requests, "get", side_effect=fake_get):
                count = club_events.fetch_club_events()

            self.assertEqual(count, 1)
            stored = read_json("data/club_events.json")
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["title"], future_title)
            self.assertEqual(stored[0]["location"], "Helsinki")
            self.assertEqual(stored[0]["source"], "club_wp")


class ManualSourceTests(unittest.TestCase):
    def test_process_manual_events_creates_json_from_text_input(self):
        content = """
Title: Oma tapahtuma
Type: Gravel
Date: 15.06.2099
Time: 10:00
Location: Jyvaskyla
Organizer: Oma seura
Link: https://example.com/oma
Description: Testikuvaus
""".strip()
        with temporary_cwd():
            os.makedirs("data", exist_ok=True)
            with open("data/simple_events.txt", "w", encoding="utf-8") as handle:
                handle.write(content)

            count = manual_events.process_manual_events()

            self.assertEqual(count, 1)
            stored = read_json("data/manual_events.json")
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["title"], "Oma tapahtuma")
            self.assertEqual(stored[0]["datetime"], "2099-06-15 08:00")
            self.assertEqual(stored[0]["source"], "manual")


class EventManagerSourcePriorityTests(unittest.TestCase):
    def test_manual_edits_override_other_sources_for_same_event(self):
        event_date = "2099-06-15 08:00"
        base_event = {
            "title": "Yhteinen tapahtuma",
            "type": "Gravel",
            "datetime": event_date,
            "location": "Turku",
            "organizer": "",
            "description": "Alempi prioriteetti",
            "link": "https://example.com/base",
            "source": "bikeland",
        }
        edited_event = {
            "title": "Yhteinen tapahtuma",
            "type": "Gravel",
            "datetime": event_date,
            "location": "Helsinki",
            "organizer": "Admin",
            "description": "Korkein prioriteetti",
            "link": "https://example.com/edited",
            "source": "manual_edit",
        }

        with temporary_cwd():
            os.makedirs("data", exist_ok=True)
            with open("data/bikeland_events.json", "w", encoding="utf-8") as handle:
                json.dump([base_event], handle)
            with open("data/manual_edits.json", "w", encoding="utf-8") as handle:
                json.dump([edited_event], handle)

            with patch.object(event_manager.bikeland_events, "scrape_bikeland_events", return_value=0):
                with patch.object(event_manager.manual_events, "process_manual_events", return_value=0):
                    with patch.object(event_manager.pyorailyfi_events, "fetch_pyorailyfi_events", return_value=0):
                        with patch.object(event_manager.raceresult_events, "fetch_raceresult_events", return_value=0):
                            with patch.object(event_manager.monesko_events, "fetch_monesko_events", return_value=0):
                                with patch.object(event_manager.webscorer_events, "fetch_webscorer_events", return_value=0):
                                    with patch.object(event_manager.club_events, "fetch_club_events", return_value=0):
                                        total = event_manager.combine_all_events()

            self.assertEqual(total, 1)
            stored = read_json("data/all_events.json")
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["source"], "manual_edit")
            self.assertEqual(stored[0]["location"], "Helsinki")
            self.assertEqual(stored[0]["description"], "Korkein prioriteetti")


if __name__ == "__main__":
    unittest.main()
