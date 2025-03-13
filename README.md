# Pyöräilytapahtumat Suomessa

Työkalu pyöräilytapahtumien keräämiseen, hallintaan ja visualisointiin kartalla.

## Pikaopas

### 1. Tapahtumien päivitys
Suorita: `update_events.bat`
- Hakee uudet tapahtumat eri lähteistä (Bikeland.fi, CSV, manuaaliset)
- Yhdistää tapahtumat ja poistaa duplikaatit
- Säilyttää hallintapaneelissa tehdyt muutokset

### 2. Tapahtumien katselu kartalla
Suorita: `run_streamlit_app.bat`
- Avaa selaimessa interaktiivisen karttasovelluksen
- Näyttää tapahtumat Suomen kartalla
- Voit suodattaa tapahtumia kuukauden, tyypin ja sijainnin mukaan

### 3. Tapahtumien hallinta
Suorita: `run_admin_panel.bat`
- Avaa selaimessa hallintapaneelin
- Voit selata, muokata ja lisätä tapahtumia
- Voit tunnistaa ja käsitellä duplikaatteja
- Voit estää ei-toivottuja tapahtumia

### 4. Duplikaattien tarkistus
Suorita: `check_duplicates.bat` tai `check_duplicates_verbose.bat`
- Tarkistaa tapahtumien duplikaatit komentoriviltä
- Näyttää tarkat duplikaatit, samankaltaiset tapahtumat ja samassa paikassa samana päivänä olevat tapahtumat

## Yksinkertaiset käyttöohjeet

### Tapahtumien päivittäminen
1. Kaksoisklikkaa `update_events.bat`-tiedostoa
2. Odota kunnes prosessi on valmis (komentorivi-ikkuna sulkeutuu)
3. Uudet tapahtumat on nyt lisätty järjestelmään

### Tapahtumien katselu kartalla
1. Kaksoisklikkaa `run_streamlit_app.bat`-tiedostoa
2. Selain avautuu automaattisesti karttasovellukseen
3. Käytä vasemman reunan suodattimia tapahtumien rajaamiseen
4. Klikkaa kartan merkkejä nähdäksesi tapahtuman tiedot
5. Taulukkonäkymä näyttää kaikki tapahtumat kartan alla

### Tapahtumien hallinta
1. Kaksoisklikkaa `run_admin_panel.bat`-tiedostoa
2. Selain avautuu automaattisesti hallintapaneeliin
3. Selaa tapahtumia "Kaikki tapahtumat" -välilehdellä
   - Käytä suodattimia ja hakua löytääksesi tapahtumia
   - Klikkaa "Muokkaa tapahtumaa" muokataksesi tapahtuman tietoja
   - Klikkaa ❌-painiketta estääksesi tapahtuman
4. Tarkista duplikaatit "Duplikaatit"-välilehdellä
   - Voit säilyttää alkuperäisen, duplikaatin tai estää molemmat
5. Tarkista samankaltaiset tapahtumat "Samankaltaiset tapahtumat"-välilehdellä
   - Säädä samankaltaisuuskynnystä liukusäätimellä
6. Tarkista samassa paikassa olevat tapahtumat "Tapahtumat samassa paikassa"-välilehdellä

### Tapahtumien lisääminen manuaalisesti
1. Voit lisätä tapahtumia kahdella tavalla:
   - Hallintapaneelin kautta: Klikkaa "Lisää uusi tapahtuma" sivupalkissa
   - Muokkaamalla tiedostoa `data/simple_events.txt` seuraavassa muodossa:
```
Title: Tapahtuman nimi
Type: Tapahtuman tyyppi
Date: PP.KK.VVVV
Location: Kaupunki
Organizer: Järjestäjä
Link: https://example.com/tapahtuma
Description: Lisätiedot
```

### Tärkeää tietää
- Hallintapaneelissa tehdyt muutokset säilyvät, vaikka ajaisit tapahtumien päivityksen
- Estetyt tapahtumat eivät näy kartalla tai taulukossa
- Voit tuoda ja viedä estolistan hallintapaneelin sivupalkista

## Asennus
1. Kloonaa tämä repositorio
2. Asenna tarvittavat paketit: `pip install -r requirements.txt`

## Tiedostorakenne
- `src/`: Python-skriptit
- `data/`: Syötetiedostot ja JSON-data
- `output/`: Generoidut tulostiedostot

## Vianmääritys
- Päivämäärämuoto-ongelmia? Tarkista PP.KK.VVVV-muoto manuaalisissa tapahtumissa
- Verkkosivun rakenne muuttunut? Jäsennin saattaa tarvita päivitystä
- CSV-koodausongelmat? Kokeile UTF-8-SIG-koodausta
- Streamlit-virheitä? Varmista, että käytät versiota 1.32.0 tai uudempaa
- Näetkö varoituksen "folium_static is deprecated"? Voit korjata tämän muokkaamalla src/event_map_app.py tiedostoa ja korvaamalla `folium_static(m, width=1000, height=600)` koodilla `st_folium(m, width=1000, height=600, returned_objects=[])`