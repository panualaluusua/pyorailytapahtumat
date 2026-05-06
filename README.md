# Pyorailytapahtumat Suomessa

Tyokalu pyorailytapahtumien keraamiseen, hallintaan ja visualisointiin kartalla.

## Datalahteet

| Lahde | Tiedosto | Kuvaus |
|-------|----------|--------|
| **pyoraily.fi** | `data/pyorailyfi_events.json` | Suomen Pyorailyn virallinen tapahtumakalenteri. Django REST API (`tulokset.pyoraily.fi/api/events/`). Kattavin kilpailu- ja harrastetapahtumalahde. |
| **RaceResult** | `data/raceresult_events.json` | `my.raceresult.com`-hakemisto. Suomen tapahtumat haetaan julkisesta tapahtumalistasta maantieteellisella rajauksella. |
| **Monesko** | `data/monesko_events.json` | Moneskon pyorailykategorian tapahtumat. Ensisijaisesti The Events Calendar REST API, varalla iCalendar-vienti. |
| **Bikeland.fi** | `data/bikeland_events.json` | Bikelandin tapahtumasivu. Data haetaan sivulle upotetuista JavaScript-muuttujista. |
| **Webscorer** | `data/webscorer_events.json` | Webscorerin Suomen pyorailytapahtumia listaava haku, josta parsitaan kilpailuja HTML-sivulta. |
| **Pyorailyseurat** | `data/club_events.json` | Yksittaisten seurojen omat sivut. Tukee WordPress REST API:a ja RSS-syotteita. Seurat konfiguroidaan tiedostossa `data/club_sources.json`. |
| **Manuaaliset** | `data/manual_events.json` | Tapahtumat tiedostosta `data/simple_events.txt`. Kayta tapahtumille joita ei loydy automaattisesti. |
| **Admin-muokkaukset** | `data/manual_edits.json` | Admin-paneelista tehdyt muokkaukset. Korkein prioriteetti. |

### Lahdeprioriteetti

Kun sama tapahtuma loytyy useammasta lahteesta, korkein prioriteetti voittaa:

`admin-paneeli` > `manuaalinen` > `pyoraily.fi` > `raceresult` > `monesko` > `bikeland` > `webscorer` > `club_wp`

Toteutus on maaritelty tiedostossa `src/event_manager.py`.

### Seurojen lisaaminen

Lisaa uusi seura tiedostoon `data/club_sources.json` esimerkiksi muodossa:

```json
{ "name": "Seuran nimi", "url": "https://www.seura.fi", "type": "wp_api" }
```

`type`-kentta voi olla:

- `wp_api`
- `rss`

## Pikaopas

### Tapahtumien katselu kartalla

Suorita:

```bash
run_streamlit_app.bat
```

### Tapahtumien paivitys

Suorita:

```bash
update_events.bat
```

Tai suoraan:

```bash
python update.py
```

`update.py`:

1. hakee tapahtumat kaikista aktiivisista lahteista
2. yhdistaa ja deduploi tapahtumat
3. kirjoittaa `data/all_events.json`-tiedoston
4. commitoi ja pushaa muuttuneet datatiedostot, ellei kayteta `--dry-run`-lippua

Testiajo ilman git-operaatioita:

```bash
python update.py --dry-run
```

### Tapahtumien lisaaminen manuaalisesti

1. Avaa `data/simple_events.txt`
2. Lisaa tapahtuma muodossa:

```text
Title: Tapahtuman nimi
Type: Tapahtuman tyyppi
Date: PP.KK.VVVV
Time: HH:MM
Location: Kaupunki
Organizer: Jarjestaja
Link: https://example.com/tapahtuma
Description: Lisatiedot
```

3. Aja `python src/manual_events.py` tai koko putki komennolla `python update.py --dry-run`

## Asennus

1. Kloonaa repositorio
2. Asenna riippuvuudet:

```bash
pip install -r requirements.txt
```

## Tiedostorakenne

```text
src/
  event_map_app.py
  event_manager.py
  event_admin.py
  pyorailyfi_events.py
  raceresult_events.py
  monesko_events.py
  bikeland_events.py
  webscorer_events.py
  club_events.py
  manual_events.py

data/
  all_events.json
  pyorailyfi_events.json
  raceresult_events.json
  monesko_events.json
  bikeland_events.json
  webscorer_events.json
  club_events.json
  manual_events.json
  manual_edits.json
  club_sources.json
  event_blacklist.json
  geocache.json
  simple_events.txt
```
