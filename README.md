# Pyorailytapahtumat Suomessa

Tyokalu suomalaisten ulkopyorailytapahtumien keruuseen, yhdistelyyn, geokoodaukseen ja visualisointiin kartalla.

## Mita projekti tekee

Projekti hakee tapahtumia useista lahteista, normalisoi ne yhteiseen skeemaan, poistaa duplikaatit lahdeprioriteetin perusteella ja kirjoittaa lopputuloksen tiedostoon `data/all_events.json`.

Paivitysputki tekee seuraavat vaiheet:

1. hakee tapahtumat kaikista aktiivisista lahteista
2. kasittelee manuaaliset tapahtumat tiedostosta `data/simple_events.txt`
3. yhdistaa ja deduplikoi tapahtumat tiedostossa `src/event_manager.py`
4. geokoodaa tapahtumien sijainnit tiedostossa `src/geocode_events.py`
5. commitoi ja pushaa paivittyneet datatiedostot, ellei kayteta `--dry-run`-tilaa

## Datalahteet

| Lahde | Tiedosto | Kuvaus |
|-------|----------|--------|
| `pyoraily.fi` | `data/pyorailyfi_events.json` | Suomen Pyorailyn julkinen tapahtuma-API. Projektin kattavin yksittainen lahde. |
| `RaceResult` | `data/raceresult_events.json` | `my.raceresult.com`-hakemisto maantieteellisella rajauksella Suomeen. |
| `Monesko` | `data/monesko_events.json` | Ensisijaisesti The Events Calendar REST API, varalla iCalendar-vienti. |
| `Bikeland.fi` | `data/bikeland_events.json` | Tapahtumasivulle upotettu JavaScript-data. |
| `Webscorer` | `data/webscorer_events.json` | HTML-listaus Suomen pyorailytapahtumista. |
| `Pyorailyseurat` | `data/club_events.json` | Seurojen omat sivut WordPress REST API:n tai RSS-syotteen kautta. Lahteet maaritellaan tiedostossa `data/club_sources.json`. |
| `Manuaaliset` | `data/manual_events.json` | Tapahtumat tiedostosta `data/simple_events.txt`. |
| `Admin-muokkaukset` | `data/manual_edits.json` | Admin-nakyman lisaamat tai muokkaamat tapahtumat. Korkein prioriteetti yhdistelyssa. |

### Lahdeprioriteetti

Kun sama tapahtuma loytyy useammasta lahteesta, korkeampi prioriteetti voittaa:

`manual_edit` > `manual` > `pyorailyfi` > `raceresult` > `monesko` > `bikeland` > `webscorer` > `club_wp`

Prioriteetit on maaritelty tiedostossa `src/event_manager.py`.

## Kaytto

### Karttasovellus

```bash
python -m streamlit run src/event_map_app.py
```

Windowsissa voit kayttaa myos:

```bash
run_streamlit_app.bat
```

### Tapahtumien paivitys

```bash
python update.py
```

Turvallinen testiajo ilman git-operaatioita:

```bash
python update.py --dry-run
```

Windowsissa voit kayttaa myos:

```bash
update_events.bat --dry-run
```

### Manuaalisten tapahtumien lisaaminen

Lisaa tapahtumat tiedostoon `data/simple_events.txt` muodossa:

```text
Title: Tapahtuman nimi
Type: Tapahtuman tyyppi
Date: PP.KK.VVVV
Location: Kaupunki tai tarkempi paikka
Organizer: Jarjestaja
Link: https://example.com/tapahtuma
Description: Lisatiedot
```

Pakolliset kentat ovat `Title`, `Type`, `Date` ja `Location`.

Kasittele manuaaliset tapahtumat:

```bash
python src/manual_events.py
```

Jos haluat ajaa koko putken ja paivittaa yhdistetyn datan:

```bash
python update.py --dry-run
```

## Asennus

Projekti vaatii Pythonin version `3.13` tai uudemman.

Asenna riippuvuudet:

```bash
pip install -r requirements.txt
```

## Tarkeimmat tiedostot

```text
src/
  event_map_app.py
  event_admin.py
  event_manager.py
  geocode_events.py
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

docs/
  EVENT_SOURCES.md
  PROJECT_DESCRIPTION.md
  LEARNINGS.md
```
