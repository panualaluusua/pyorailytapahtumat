"""
Pyöräilytapahtumat Suomessa
Cycling event aggregator with card feed, filters and map view.
"""
import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import os
from datetime import datetime, timedelta, date
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import json
import math

try:
    from streamlit_geolocation import streamlit_geolocation
    HAS_GEOLOCATION = True
except ImportError:
    HAS_GEOLOCATION = False

st.set_page_config(
    page_title="Pyöräilytapahtumat Suomessa",
    page_icon="🚲",
    layout="centered",
)

TYPE_COLORS = {
    "MTB":        {"bg": "#e6f4ea", "fg": "#1e4d2b", "dot": "#5a9d6a"},
    "Maantie":    {"bg": "#e6ecf5", "fg": "#1e3a5f", "dot": "#4a7bb8"},
    "Gravel":     {"bg": "#fbf0e2", "fg": "#7a4a1a", "dot": "#c98a3e"},
    "Cyclocross": {"bg": "#fae9e2", "fg": "#7a3a1a", "dot": "#c97a4e"},
    "BMX":        {"bg": "#f4e6f0", "fg": "#5a1e4d", "dot": "#a64e98"},
    "Muu":        {"bg": "#f0f0f0", "fg": "#404040", "dot": "#909090"},
}

# Only discipline categories appear as filter pills; "Muu" is intentionally excluded.
ALL_CATEGORIES = ["MTB", "Maantie", "Gravel", "Cyclocross", "BMX"]

SOURCE_NAMES = {
    "manual_edit": "Admin",
    "manual":      "Manuaalinen",
    "pyorailyfi":  "pyoraily.fi",
    "raceresult":  "RaceResult",
    "pptiming":    "PP Timing",
    "monesko":     "Monesko",
    "bikeland":    "Bikeland.fi",
    "webscorer":   "Webscorer",
    "club_wp":     "Pyöräilyseura",
}

WEEKDAYS_FI = ["Ma", "Ti", "Ke", "To", "Pe", "La", "Su"]
MONTHS_FI_GEN = [
    "tammikuuta", "helmikuuta", "maaliskuuta", "huhtikuuta",
    "toukokuuta", "kesäkuuta", "heinäkuuta", "elokuuta",
    "syyskuuta", "lokakuuta", "marraskuuta", "joulukuuta",
]


def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp {
    font-family: "Inter Tight", system-ui, sans-serif !important;
}
.block-container {
    max-width: 720px !important;
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
}
.date-header {
    font-size: 0.75rem;
    font-weight: 700;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    padding: 6px 0 4px 0;
    border-bottom: 1px solid #e8e8e8;
    margin-top: 1.4rem;
    margin-bottom: 0.2rem;
}
.card-title {
    font-weight: 600;
    font-size: 0.96rem;
    line-height: 1.35;
    margin-bottom: 3px;
}
.card-meta {
    font-size: 0.82rem;
    color: #555;
    margin: 2px 0;
}
.cat-pill {
    display: inline-block;
    border-radius: 10px;
    padding: 1px 7px;
    font-size: 0.73rem;
    font-weight: 600;
    margin-right: 4px;
    vertical-align: middle;
}
.status-bar {
    font-size: 0.84rem;
    color: #777;
    padding: 2px 0 10px 0;
}
</style>
""", unsafe_allow_html=True)


def sanitize_text(text):
    """Sanitize text by removing or replacing problematic characters."""
    if not isinstance(text, str):
        return text
    text = text.replace('`', "'")
    replacements = {
        '“': '"', '”': '"',
        '‘': "'", '’': "'",
        '—': '-', '–': '-',
        '…': '...', '​': '', '\xa0': ' ',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')
    return text


@st.cache_data
def geocode_location(location):
    """Geocode a location to coordinates. JSON file cache + progressive suffix fallback.

    For compound locations like "Tahkokangas, Oulu" tries each suffix right-to-left
    ("Oulu, Finland") so the event appears in city-based radius searches.
    Null-cached compound locations are retried via already-cached suffixes.
    """
    if not isinstance(location, str) or not location.strip():
        return None

    location = location.strip()
    cache_file = "data/geocache.json"
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception:
            pass

    # Build progressive fallback candidates.
    # Comma-separated ("Tahkokangas, Oulu"): try suffixes right-to-left — city is rightmost.
    # Dash-separated ("Lahti - Pajulahti", multi-city routes): try each individual part
    #   left-to-right — city/start-point is leftmost.
    # Full address ("Käyrälammentie 20, 45200 Kouvola"): comma suffixes → "Kouvola".
    if ',' in location:
        parts = [p.strip() for p in location.split(',') if p.strip()]
        candidates = [location] + [', '.join(parts[i:]) for i in range(1, len(parts))]
    elif ' - ' in location:
        parts = [p.strip() for p in location.split(' - ') if p.strip()]
        candidates = [location] + parts  # try each city individually, left-to-right
    else:
        candidates = [location]

    # Check JSON cache for the original key first
    if location in cache:
        cached = cache[location]
        if cached is not None:
            return (cached[0], cached[1])
        # Cached as null — check if a suffix is already cached with coords
        for candidate in candidates[1:]:
            if candidate in cache and cache[candidate] is not None:
                return (cache[candidate][0], cache[candidate][1])
        return None

    # Not cached — try Nominatim with progressive fallback
    result = None
    try:
        geolocator = Nominatim(user_agent="pyorailytapahtumat-app", timeout=10)
        geocode_fn = RateLimiter(
            geolocator.geocode, min_delay_seconds=1.5, max_retries=2, error_wait_seconds=2.0
        )
        for candidate in candidates:
            # Use suffix from existing cache if available
            if candidate in cache:
                if cache[candidate] is not None:
                    result = (cache[candidate][0], cache[candidate][1])
                    break
                continue  # cached null, skip to next suffix
            search = (
                candidate if ("Finland" in candidate or "Suomi" in candidate)
                else f"{candidate}, Finland"
            )
            info = geocode_fn(search)
            if info:
                result = (info.latitude, info.longitude)
                if candidate != location:
                    cache[candidate] = result  # cache the working suffix too
                break
    except Exception as e:
        st.warning(f"Geokoodausvirhe ({location}): {e}")

    cache[location] = result
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"Välimuistin kirjoitus epäonnistui: {e}")
    return result


def categorize_type(type_str, source=None, title=None):
    """Map raw type string (and optionally title) to one of the discipline categories.

    Checks type_str first; if that yields no discipline match, falls back to
    scanning the event title so that e.g. "EVOC MTB" (type="Kilpailu") is
    correctly classified as MTB.
    """
    def _classify(text):
        t = text.lower()
        if any(x in t for x in ['mtb', 'mountain', 'maasto', 'xco', 'xcm', 'xce',
                                  'xcl', 'downhill', 'enduro', 'mtn', 'cross-country',
                                  'xc cup', 'xc tour']):
            return "MTB"
        if 'gravel' in t:
            return "Gravel"
        if any(x in t for x in ['cyclocross', 'cyclo-cross', 'cyclo cross']):
            return "Cyclocross"
        if 'bmx' in t:
            return "BMX"
        if any(x in t for x in ['road', 'maantie', 'aika-ajo', 'rata', 'track',
                                  'criterium', 'etappiajo', 'kortteliajo',
                                  'muistoajo', 'tempo', 'tour de ']):
            return "Maantie"
        if 'nordic gravel' in t:
            return "Gravel"
        return None

    result = _classify(str(type_str) if type_str else "")
    if result:
        return result
    if title:
        result = _classify(str(title))
        if result:
            return result
    return "Muu"


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def format_date_header(d: date) -> str:
    today = date.today()
    if d == today:
        return "Tänään"
    if d == today + timedelta(days=1):
        return "Huomenna"
    wday = WEEKDAYS_FI[d.weekday()]
    month = MONTHS_FI_GEN[d.month - 1]
    return f"{wday} {d.day}. {month}"


@st.cache_data(ttl=60)
def load_events():
    """Load and prepare events from all_events.json."""
    try:
        json_path = 'data/all_events.json'
        if not os.path.exists(json_path):
            return pd.DataFrame(), "Ei tiedostoa"
        mod_time = os.path.getmtime(json_path)
        last_updated = datetime.fromtimestamp(mod_time).strftime('%d.%m.%Y %H:%M')

        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read().replace('`', "'")
        events_data = json.loads(content)

        for e in events_data:
            for field in ['title', 'type', 'location', 'organizer', 'description', 'link']:
                if field in e:
                    e[field] = sanitize_text(e[field])

        df = pd.DataFrame(events_data)
        df.attrs['last_updated'] = last_updated

        # Parse dates — keep date_obj for grouping and filtering
        def parse_date_row(x):
            try:
                s = x.split()[0] if isinstance(x, str) else ""
                d = datetime.strptime(s, '%Y-%m-%d')
                return d.date(), d.strftime('%d.%m.%Y')
            except Exception:
                return None, "Tuntematon"

        parsed = df['datetime'].apply(parse_date_row)
        df['date_obj'] = parsed.apply(lambda x: x[0])
        df['date'] = parsed.apply(lambda x: x[1])

        # Filter out past events
        today = date.today()
        df = df[df['date_obj'].apply(lambda d: d is not None and d >= today)].copy()

        # Drop exact duplicates
        df = df.drop_duplicates(subset=['title', 'date'], keep='first')

        # Geocode locations (cached per location string)
        df['coordinates'] = df['location'].apply(geocode_location)
        df['latitude'] = df['coordinates'].apply(lambda x: x[0] if x else None)
        df['longitude'] = df['coordinates'].apply(lambda x: x[1] if x else None)

        # Categorize event types (type_str first, then title as fallback)
        df['category'] = df.apply(
            lambda r: categorize_type(r.get('type'), r.get('source'), r.get('title')), axis=1
        )

        df = df.sort_values('date_obj').reset_index(drop=True)
        return df, last_updated

    except Exception as e:
        st.error(f"Virhe tapahtumien latauksessa: {e}")
        return pd.DataFrame(), "Virhe"


def create_map(df, origin_coords=None, radius_km=None):
    """Create folium map with event markers, optional user location and radius circle."""
    center = list(origin_coords) if origin_coords else [65.0, 25.0]
    zoom = 6 if origin_coords else 5
    m = folium.Map(location=center, zoom_start=zoom, control_scale=True)

    if origin_coords and radius_km:
        folium.Circle(
            location=list(origin_coords),
            radius=radius_km * 1000,
            color='#e05050',
            fill=True,
            fill_opacity=0.05,
            weight=1.5,
        ).add_to(m)
        folium.Marker(
            location=list(origin_coords),
            tooltip="Sijaintisi",
            icon=folium.Icon(color='red', icon='home', prefix='fa'),
        ).add_to(m)

    location_counts = {}
    for _, row in df.iterrows():
        if pd.isna(row.get('latitude')) or pd.isna(row.get('longitude')):
            continue
        cat = row.get('category', 'Muu')
        colors = TYPE_COLORS.get(cat, TYPE_COLORS['Muu'])

        popup_html = (
            f'<div style="max-width:300px;font-family:system-ui;font-size:13px">'
            f'<b>{sanitize_text(str(row["title"]))}</b><br>'
            f'<span style="color:#555">{row.get("date", "")} · '
            f'{sanitize_text(str(row.get("location", "")))}'
        )
        if row.get('organizer'):
            popup_html += f'<br>Järjestäjä: {sanitize_text(str(row["organizer"]))}'
        if row.get('link'):
            popup_html += f'<br><a href="{sanitize_text(str(row["link"]))}" target="_blank">Lisätiedot →</a>'
        popup_html += '</span></div>'

        key = f"{row['latitude']:.5f},{row['longitude']:.5f}"
        count = location_counts.get(key, 0)
        location_counts[key] = count + 1
        mlat, mlon = row['latitude'], row['longitude']
        if count > 0:
            angle = count * 1.2
            offset = 0.05 * (1 + count * 0.3)
            mlat += offset * math.sin(angle)
            mlon += offset * math.cos(angle)

        folium.CircleMarker(
            location=[mlat, mlon],
            radius=8,
            color=colors['dot'],
            fill=True,
            fill_color=colors['dot'],
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=sanitize_text(str(row['title'])),
        ).add_to(m)

    return m


def display_recent_events(df):
    """Show the 5 most recently added events (used in Tallennetut tab)."""
    st.markdown("#### Viimeksi lisätyt tai muutetut")
    if 'added_timestamp' not in df.columns or df.empty:
        st.info("Ei viimeaikaisia tapahtumia.")
        return
    try:
        recent = df.sort_values('added_timestamp', ascending=False).head(5)
        for _, ev in recent.iterrows():
            with st.expander(f"{ev['title']} ({ev['date']})"):
                st.write(f"**Tyyppi:** {ev.get('type', '')}")
                st.write(f"**Sijainti:** {ev.get('location', '')}")
                if ev.get('organizer'):
                    st.write(f"**Järjestäjä:** {ev['organizer']}")
                if ev.get('link') and str(ev['link']) not in ('nan', ''):
                    st.markdown(f"[Lisätiedot]({ev['link']})")
                if ev.get('added_timestamp'):
                    try:
                        ts = datetime.fromisoformat(ev['added_timestamp'])
                        st.caption(f"Lisätty: {ts.strftime('%d.%m.%Y %H:%M')}")
                    except Exception:
                        pass
    except Exception as e:
        st.error(f"Virhe: {e}")


def render_event_card(event, show_distance=True, key_prefix="card"):
    """Render a single event card inside a bordered container."""
    eid = f"{event['title']}_{event['date']}"
    cat = event.get('category', 'Muu')
    colors = TYPE_COLORS.get(cat, TYPE_COLORS['Muu'])

    dist_badge = ""
    if show_distance:
        d = event.get('distance_km')
        try:
            if d is not None and d != float('inf') and not math.isnan(float(d)):
                dist_badge = f" · <b>{d:.0f}&nbsp;km</b>"
        except (TypeError, ValueError):
            pass

    loc = sanitize_text(str(event.get('location') or ''))
    org = sanitize_text(str(event.get('organizer') or ''))
    title = sanitize_text(str(event.get('title') or ''))
    source_key = event.get('source', '')
    source_label = SOURCE_NAMES.get(source_key, source_key)

    loc_part = f" · {loc}" if loc else " · <span style='color:#aaa;font-style:italic'>sijainti ei tiedossa</span>"
    org_part = (
        f'<div class="card-meta" style="color:#999;font-size:0.78rem">Järjestäjä: {org}</div>'
        if org else ""
    )
    source_part = (
        f'<div class="card-meta" style="color:#bbb;font-size:0.73rem">Lähde: {source_label}</div>'
        if source_label else ""
    )

    with st.container(border=True):
        st.markdown(
            f'<div style="border-left:4px solid {colors["dot"]};padding-left:10px;margin-bottom:4px">'
            f'<div class="card-title">{title}</div>'
            f'<div class="card-meta">'
            f'<span class="cat-pill" style="background:{colors["dot"]};color:#fff">{cat}</span>'
            f'{loc_part}{dist_badge}'
            f'</div>'
            f'{org_part}'
            f'{source_part}'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_save, col_link = st.columns([1, 2])
        saved_set = st.session_state.get("saved", set())
        with col_save:
            is_saved = st.checkbox(
                "★ Tallennettu" if eid in saved_set else "☆ Tallenna",
                value=eid in saved_set,
                key=f"{key_prefix}_save_{eid}",
            )
            if is_saved:
                st.session_state["saved"].add(eid)
            else:
                st.session_state["saved"].discard(eid)

        with col_link:
            link = event.get('link', '')
            if link and str(link) not in ('nan', ''):
                st.markdown(f"[Lisätiedot →]({sanitize_text(str(link))})")


def main():
    inject_css()

    # Initialize session state
    if "saved" not in st.session_state:
        st.session_state["saved"] = set()
    if "show_all" not in st.session_state:
        st.session_state["show_all"] = False
    if "origin_city" not in st.session_state:
        st.session_state["origin_city"] = "Helsinki"
    if "origin_coords" not in st.session_state:
        st.session_state["origin_coords"] = geocode_location("Helsinki")
    if "_last_geocoded_city" not in st.session_state:
        st.session_state["_last_geocoded_city"] = "Helsinki"

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown("## 🚲 Pyöräilytapahtumat Suomessa")
    st.caption("Loyda Suomen pyorailytapahtumat yhdesta paikasta kartalla ja selattavana listana.")

    # ── Load data ────────────────────────────────────────────────────────────
    with st.spinner("Ladataan tapahtumia..."):
        df, last_updated = load_events()

    if df.empty:
        st.error("Tapahtumia ei löydy. Tarkista data/all_events.json.")
        return

    # ── Suodattimet ──────────────────────────────────────────────────────────
    # Location input + optional GPS button
    if HAS_GEOLOCATION:
        col_loc, col_gps = st.columns([5, 1])
    else:
        col_loc = st.container()

    with col_loc:
        displayed_city = (
            st.session_state["origin_city"]
            if st.session_state["origin_city"] != "GPS-sijainti"
            else "Helsinki"
        )
        city_input = st.text_input("Lähtöpaikka", value=displayed_city, placeholder="Kaupunki, esim. Tampere")

    if HAS_GEOLOCATION:
        with col_gps:
            st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
            geo = streamlit_geolocation()
            st.markdown("</div>", unsafe_allow_html=True)
            if geo and isinstance(geo, dict) and geo.get("latitude"):
                if st.session_state.get("_gps_lat") != geo["latitude"]:
                    st.session_state["_gps_lat"] = geo["latitude"]
                    st.session_state["origin_coords"] = (geo["latitude"], geo["longitude"])
                    st.session_state["origin_city"] = "GPS-sijainti"
                    st.session_state["_last_geocoded_city"] = "GPS-sijainti"

    # Geocode text input when it changes
    if city_input and city_input != st.session_state["_last_geocoded_city"]:
        with st.spinner(f"Paikannetaan {city_input}..."):
            coords = geocode_location(city_input)
        if coords:
            st.session_state["origin_coords"] = coords
            st.session_state["origin_city"] = city_input
        else:
            st.warning(f"Paikkakuntaa '{city_input}' ei löydy — tarkista kirjoitus.")
        st.session_state["_last_geocoded_city"] = city_input
        st.session_state["show_all"] = False

    origin_coords = st.session_state["origin_coords"]
    origin_city = st.session_state["origin_city"]

    # Radius + time window
    col_r, col_t = st.columns([2, 3])
    with col_r:
        radius_km = st.slider("Etäisyys", 20, 500, 100, step=10, format="%d km")
    with col_t:
        time_window = st.segmented_control(
            "Aikaväli",
            ["Viikko", "Kuukausi", "3 kk", "Kaikki"],
            default="Kuukausi",
        )

    # Category pills
    selected_cats = st.pills(
        "Tapahtumatyypit",
        ALL_CATEGORIES,
        selection_mode="multi",
        default=["MTB", "Maantie", "Gravel", "Kilpailu"],
    )
    if not selected_cats:
        selected_cats = []

    # ── Distance computation ─────────────────────────────────────────────────
    df = df.copy()
    if origin_coords:
        def _dist(row):
            if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
                return haversine(origin_coords[0], origin_coords[1],
                                 row['latitude'], row['longitude'])
            return None  # None = no coordinates, not "far away"
        df['distance_km'] = df.apply(_dist, axis=1)
    else:
        df['distance_km'] = None

    # ── Filtering ────────────────────────────────────────────────────────────
    today = date.today()
    fdf = df.copy()

    if time_window == "Viikko":
        fdf = fdf[fdf['date_obj'] <= today + timedelta(days=7)]
    elif time_window == "Kuukausi":
        fdf = fdf[fdf['date_obj'] <= today + timedelta(days=30)]
    elif time_window == "3 kk":
        fdf = fdf[fdf['date_obj'] <= today + timedelta(days=90)]

    if selected_cats:
        fdf = fdf[fdf['category'].isin(selected_cats)]

    # Split: events with known coordinates vs. those without.
    # No-location events are always shown (at the bottom) regardless of radius.
    no_loc_mask = fdf['latitude'].isna() | fdf['longitude'].isna()
    if origin_coords:
        fdf_loc = fdf[~no_loc_mask & (fdf['distance_km'] <= radius_km)].copy()
        fdf_no_loc = fdf[no_loc_mask].copy()
    else:
        fdf_loc = fdf[~no_loc_mask].copy()
        fdf_no_loc = fdf[no_loc_mask].copy()

    fdf_loc = fdf_loc.sort_values(['distance_km', 'date_obj'], na_position='last').reset_index(drop=True)
    fdf_no_loc = fdf_no_loc.sort_values('date_obj', na_position='last').reset_index(drop=True)

    total_count = len(fdf_loc) + len(fdf_no_loc)

    # ── Status bar ───────────────────────────────────────────────────────────
    parts = [f"**{total_count}** tapahtumaa"]
    if origin_coords:
        parts.append(f"{radius_km} km")
    parts.append(origin_city)
    st.markdown(f'<div class="status-bar">{" · ".join(parts)}</div>', unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    n_saved = len(st.session_state["saved"])
    tab_browse, tab_saved = st.tabs([f"Selaa ({total_count})", f"Tallennetut ({n_saved})"])

    # ── Selaa ────────────────────────────────────────────────────────────────
    with tab_browse:
        show_map = st.toggle("Näytä kartta", value=True)
        if show_map:
            if not fdf_loc.empty:
                m = create_map(
                    fdf_loc,
                    origin_coords=origin_coords,
                    radius_km=radius_km if origin_coords else None,
                )
                folium_static(m, width=700, height=220)
            else:
                st.info("Kartoitettavia tapahtumia ei löydy valituilla suodattimilla.")

        if fdf_loc.empty and fdf_no_loc.empty:
            st.info("Ei tapahtumia — kokeile suurempaa sädettä tai laajempaa aikaväliä.")
        else:
            CARDS_PER_PAGE = 60
            show_all = st.session_state.get("show_all", False)
            display_df = fdf_loc if show_all else fdf_loc.head(CARDS_PER_PAGE)

            current_label = None
            for i, (_, event) in enumerate(display_df.iterrows()):
                d = event.get('date_obj')
                label = format_date_header(d) if d else "Tuntematon päivä"
                if label != current_label:
                    current_label = label
                    st.markdown(f'<div class="date-header">{label}</div>', unsafe_allow_html=True)
                render_event_card(event, show_distance=bool(origin_coords), key_prefix=f"b{i}")

            if not show_all and len(fdf_loc) > CARDS_PER_PAGE:
                remaining = len(fdf_loc) - CARDS_PER_PAGE
                if st.button(f"Näytä lisää ({remaining} tapahtumaa)", use_container_width=True):
                    st.session_state["show_all"] = True
                    st.rerun()

            # ── Events without known location ────────────────────────────────
            if not fdf_no_loc.empty:
                st.markdown(
                    '<div class="date-header" style="color:#888;font-size:0.82rem">'
                    f'📍 Sijainti ei tiedossa ({len(fdf_no_loc)})'
                    '</div>',
                    unsafe_allow_html=True,
                )
                for i, (_, event) in enumerate(fdf_no_loc.iterrows()):
                    render_event_card(event, show_distance=False, key_prefix=f"nl{i}")

    # ── Tallennetut ──────────────────────────────────────────────────────────
    with tab_saved:
        saved_ids = st.session_state.get("saved", set())
        if not saved_ids:
            st.info("Et ole tallentanut tapahtumia. Paina ☆ Tallenna tapahtuman kortissa.")
        else:
            saved_df = df[
                df.apply(lambda r: f"{r['title']}_{r['date']}" in saved_ids, axis=1)
            ].copy()
            if saved_df.empty:
                st.info("Tallennettuja tapahtumia ei löydy.")
            else:
                st.markdown(f"**{len(saved_df)}** tallennettua tapahtumaa")
                for i, (_, event) in enumerate(saved_df.iterrows()):
                    render_event_card(event, show_distance=bool(origin_coords), key_prefix=f"s{i}")

        st.divider()
        display_recent_events(df)
        st.caption(f"Viimeksi päivitetty: {last_updated}")


if __name__ == "__main__":
    main()
