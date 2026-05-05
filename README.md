# Pyöräilytapahtumat Suomessa

Työkalu pyöräilytapahtumien keräämiseen, hallintaan ja visualisointiin kartalla.

## Datalähteet

| Lähde | Tiedosto | Kuvaus |
|-------|----------|--------|
| **pyoraily.fi** | `data/pyorailyfi_events.json` | Suomen Pyöräilyn virallinen tapahtumakalenteri. Django REST API (`tulokset.pyoraily.fi/api/events/`). Kattavin lähde: maantie, MTB, gravel, cyclocross. |
| **Bikeland.fi** | `data/bikeland_events.json` | Bikeland.fi:n tapahtumasivu. Data haetaan sivulle upotetuista JS-muuttujista (`upcoming_eventdata`). Pääasiassa suurempia massatapahtumia. |
| **RaceResult** | `data/raceresult_events.json` | my.raceresult.com — kansainvälinen ajanottojärjestelmä. Suomen tapahtumat haetaan `/RREvents/list`-endpointista maantieteellisellä rajauksella (bounds). Ei vaadi kirjautumista. |
| **Webscorer** | `data/webscorer_events.json` | webscorer.com — kilpailujen ajanotto- ja ilmoittautumisalusta. Haetaan `/findraces?pg=register&country=Finland&sport=Cycling` -sivu ja parsitaan HTML-taulukko. Löytää pieniä seuratason kilpailuja joita ei ole muissa lähteissä. |
| **Pyöräilyseurat** | `data/club_events.json` | Yksittäisten seurojen omat sivut. Seurat konfiguroidaan `data/club_sources.json`-tiedostossa. Tukee WordPress REST API:a ja RSS-syötteitä. |
| **Manuaaliset** | `data/manual_events.json` | Tapahtumat `data/simple_events.txt`-tiedostosta. Käytä tapahtumille joita ei löydy automaattisesti. |
| **Admin-muokkaukset** | `data/manual_edits.json` | Admin-paneelista tehdyt muokkaukset. Korkein prioriteetti — ylikirjoittaa muut lähteet. |

### Seurojen lisääminen

Lisää uusi seura `data/club_sources.json`-tiedostoon:

```json
{ "name": "Seuran nimi", "url": "https://www.seura.fi", "type": "wp_api" }
```

`type`-kentän arvot: `wp_api` (WordPress REST API) tai `rss` (RSS-syöte).

Scraper tunnistaa automaattisesti WordPress-kategoriat joiden nimi tai slug sisältää sanat kuten *tapahtumat*, *kilpailut*, *ajot*, *retket* jne.

### Prioriteettijärjestys (korkein ensin)

`admin-paneeli` > `manuaalinen` > `pyoraily.fi` > `raceresult` > `monesko` > `bikeland` > `webscorer` > `seurat`

---

## Pikaopas

### Tapahtumien katselu kartalla
Suorita: `run_streamlit_app.bat`

Avaa interaktiivisen karttasovelluksen selaimessa. Voit suodattaa tapahtumia kuukauden, tyypin ja sijainnin mukaan.

### Tapahtumien päivitys (manuaalinen)
Suorita: `update_events.bat`

Hakee uudet tapahtumat kaikista lähteistä, yhdistää ja commitoi muutokset GitHubiin.

### Viikoittainen automaatio
Ajamalla `python update.py` säännöllisesti (esim. cowork-automaatiolla) tapahtumakalenteri pysyy ajan tasalla automaattisesti. Skripti commitoi ja pushaa muutokset, jolloin Streamlit Cloud päivittyy automaattisesti.

Lisää `--dry-run`-lippu jos haluat testata ilman git-operaatioita:
```
python update.py --dry-run
```

### Tapahtumien lisääminen manuaalisesti
1. Avaa `data/simple_events.txt` tekstieditorissa.
2. Lisää tapahtuma muodossa:
```
Title: Tapahtuman nimi
Type: Tapahtuman tyyppi (esim. Maantie, MTB, Gravel)
Date: PP.KK.VVVV
Time: HH:MM (valinnainen)
Location: Kaupunki
Organizer: Järjestäjä (valinnainen)
Link: https://example.com/tapahtuma (valinnainen)

```
3. Suorita `update_events.bat`.

---

## Asennus

1. Kloonaa tämä repositorio.
2. Asenna paketit: `pip install -r requirements.txt`

## Tiedostorakenne

```
src/
  event_map_app.py      # Streamlit-karttasovellus
  event_manager.py      # Tapahtumien yhdistäminen ja deduplointi
  bikeland_events.py    # Bikeland.fi-scraper
  pyorailyfi_events.py  # pyoraily.fi REST API -haku
  club_events.py        # Yleinen WP/RSS-scraper seuroille
  manual_events.py      # Manuaalisten tapahtumien käsittely
  event_admin.py        # Admin-paneeli (Streamlit)

data/
  all_events.json       # Yhdistetty tapahtumalista (tämä menee Streamlitille)
  club_sources.json     # Seurojen URL-lista scraperille
  club_events.json      # Seuroilta haetut tapahtumat
  bikeland_events.json  # Bikelandista haetut tapahtumat
  pyorailyfi_events.json# pyoraily.fi:stä haetut tapahtumat
  manual_events.json    # Manuaaliset tapahtumat
  manual_edits.json     # Admin-paneelin muokkaukset
  event_blacklist.json  # Piilotetut tapahtumat
  geocache.json         # Geocoding-välimuisti (ei haeta uudelleen)
  simple_events.txt     # Manuaalisten tapahtumien syötetiedosto
```
