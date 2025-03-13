# Pyöräilytapahtumat Suomessa

Työkalu pyöräilytapahtumien keräämiseen, hallintaan ja visualisointiin kartalla.

## Pikaopas

### 1. Tapahtumien päivitys
Suorita: `update_events.bat`

### 2. Tapahtumien katselu kartalla
Suorita: `run_streamlit_app.bat`

### 3. Tapahtumien hallinta
Suorita: `run_admin_panel.bat`

### 4. Duplikaattien tarkistus
Suorita: `check_duplicates.bat` tai `check_duplicates_verbose.bat`

## Mitä tämä työkalu tekee
- Kerää pyöräilytapahtumia useista lähteistä (Bikeland.fi, CSV, manuaaliset)
- Näyttää tapahtumat interaktiivisella Suomen kartalla
- Mahdollistaa tapahtumien suodattamisen kuukauden, tyypin ja sijainnin mukaan
- Tarjoaa hallintapaneelin tapahtumien muokkaamiseen ja duplikaattien käsittelyyn

## Asennus
1. Kloonaa tämä repositorio
2. Asenna tarvittavat paketit: `pip install -r requirements.txt`

## Tapahtumien lisääminen manuaalisesti

Muokkaa tiedostoa `data/simple_events.txt`:
```
Title: Tapahtuman nimi
Type: Tapahtuman tyyppi
Date: PP.KK.VVVV
Location: Kaupunki
Organizer: Järjestäjä
Link: https://example.com/tapahtuma
Description: Lisätiedot
```

## Hallintapaneelin ominaisuudet
- Kaikkien tapahtumien selaaminen ja muokkaaminen
- Duplikaattien tunnistaminen ja käsittely
- Samankaltaisten tapahtumien tunnistaminen
- Tapahtumien estäminen (blacklist)
- Estettyjen tapahtumien tuonti/vienti

## Karttasovelluksen ominaisuudet
- Interaktiivinen kartta tapahtumamerkeillä
- Suodatus kuukauden, tapahtumatyypin ja sijainnin mukaan
- Taulukkonäkymä kaikista tapahtumista
- Tilastot ja kaaviot

## Tiedostorakenne
- `src/`: Python-skriptit
- `data/`: Syötetiedostot ja JSON-data
- `output/`: Generoidut tulostiedostot

## Vianmääritys
- Päivämäärämuoto-ongelmia? Tarkista PP.KK.VVVV-muoto
- Verkkosivun rakenne muuttunut? Jäsennin saattaa tarvita päivitystä
- CSV-koodausongelmat? Kokeile UTF-8-SIG-koodausta
- Streamlit-virheitä? Varmista, että käytät versiota 1.32.0 tai uudempaa