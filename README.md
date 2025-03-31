# Pyöräilytapahtumat Suomessa

Työkalu pyöräilytapahtumien keräämiseen, hallintaan ja visualisointiin kartalla.

## Pikaopas

### 1. Tapahtumien katselu kartalla
Suorita: `run_streamlit_app.bat`
- Avaa selaimessa interaktiivisen karttasovelluksen.
- Näyttää tulevat tapahtumat Suomen kartalla.
- Voit suodattaa tapahtumia kuukauden, tyypin ja sijainnin mukaan.

### 2. Tapahtumien päivitys
Suorita: `update_events.bat`
- Hakee uudet tapahtumat eri lähteistä (Bikeland.fi, CSV, manuaaliset).
- Yhdistää tapahtumat ja poistaa duplikaatit.

### 3. Tapahtumien lisääminen manuaalisesti
1. Avaa `data/simple_events.txt` -tiedosto tekstieditorissa.
2. Lisää tapahtuma seuraavassa muodossa (muista jättää tyhjä rivi tapahtumien väliin):
```
Title: Tapahtuman nimi
Type: Tapahtuman tyyppi (esim. Maantie, MTB, Gravel)
Date: PP.KK.VVVV
Time: HH:MM (valinnainen)
Location: Kaupunki
Organizer: Järjestäjä (valinnainen)
Link: https://example.com/tapahtuma (valinnainen)

```
3. Suorita `update_events.bat` päivittääksesi tapahtumat.

## Asennus

1. Kloonaa tämä repositorio.
2. Asenna tarvittavat paketit: `pip install -r requirements.txt`

## Tiedostorakenne

- `src/`: Python-skriptit (karttasovellus, tapahtumien hallinta)
- `data/`: Tapahtumatiedot (`all_events.json`) ja syötetiedostot (`simple_events.txt`, `pyorailyfi-tapahtumat.csv`, `event_blacklist.json`)
- `requirements.txt`: Tarvittavat Python-paketit
- `*.bat`: Skriptit sovelluksen käynnistämiseen ja tapahtumien päivitykseen.