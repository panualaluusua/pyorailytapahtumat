# Event Sources

Tama dokumentti kuvaa projektin nykyiset aktiiviset tapahtumalahteet, niiden teknisen toteutuksen ja yhdistelyjarjestyksen.

Paivitetty: 2026-05-11

## Nykyiset lahteet

### 1. pyoraily.fi

- Toteutus: suora API-haku
- Koodi: `src/pyorailyfi_events.py`
- Tulosdata: `data/pyorailyfi_events.json`
- Huomio: projektin kattavin yksittainen lahde

### 2. RaceResult

- Toteutus: julkisen tapahtumahakemiston haku maantieteellisella rajauksella
- Koodi: `src/raceresult_events.py`
- Tulosdata: `data/raceresult_events.json`
- Huomio: loytaa erityisesti ajanotto- ja ilmoittautumisalustoilla julkaistuja tapahtumia; koordinaatittomia tapahtumia ei loyda

### 3. PP Timing

- Toteutus: HTML-parsinta pptiming.fi-etusivulta, ankkurilinkkien teksteista poimitaan suomalaiset paivamaarat
- Koodi: `src/pptiming_events.py`
- Tulosdata: `data/pptiming_events.json`
- Huomio: kattaa suomalaisia maantie-, kriteerium- ja gravel-kilpailuja seka SM-kilpailuja, joita ei loydy RaceResult-API:sta (puuttuvat koordinaatit RaceResult-jarjestelmassa)

### 4. Monesko

- Toteutus: The Events Calendar REST API, varalla iCalendar-vienti
- Koodi: `src/monesko_events.py`
- Tulosdata: `data/monesko_events.json`
- Huomio: rajaus pyorailykategoriaan; jos venue-kentta on tyhja API-vastauksessa, sijainti paatetaan tapahtuman nimen avainsanasta (`_KNOWN_LOCATIONS`-sanakirja)

### 5. Bikeland.fi

- Toteutus: HTML-sivulle upotetun JavaScript-datan parsinta
- Koodi: `src/bikeland_events.py`
- Tulosdata: `data/bikeland_events.json`

### 6. Webscorer

- Toteutus: HTML-haku Webscorerin Suomen pyorailytapahtumien listauksesta
- Koodi: `src/webscorer_events.py`
- Tulosdata: `data/webscorer_events.json`

### 7. Pyorailyseurojen sivut

- Toteutus: WordPress REST API / RSS
- Koodi: `src/club_events.py`
- Tulosdata: `data/club_events.json`
- Konfiguraatio: `data/club_sources.json`

### 8. Manuaaliset tapahtumat

- Toteutus: paikallinen tekstisyote
- Koodi: `src/manual_events.py`
- Syote: `data/simple_events.txt`
- Tulosdata: `data/manual_events.json`

### 9. Admin-muokkaukset

- Toteutus: kasin tehdyt lisaykset, korjaukset tai piilotukset
- Koodi: `src/event_admin.py`
- Tulosdata: `data/manual_edits.json`
- Huomio: korkein prioriteetti yhdistelyssa

## Yhdistely ja prioriteetit

Kaikki lahteet yhdistetaan tiedostossa `src/event_manager.py`, joka kirjoittaa lopullisen datan tiedostoon `data/all_events.json`.

Lahdeprioriteetti on:

`manual_edit` > `manual` > `pyorailyfi` > `raceresult` > `pptiming` > `monesko` > `bikeland` > `webscorer` > `club_wp`

Tama tarkoittaa, etta jos sama tapahtuma loytyy useasta lahteesta samalla deduplikointiavaimella, korkeamman prioriteetin lahde voittaa.

## Deduplikointi

Projektin ensisijainen deduplikointiavain on:

- `title + event date`

Kaytannossa avain muodostetaan tapahtuman otsikosta ja paivamaarasta.

## Geokoodaus

Yhdistelyn jalkeen `update.py` ajaa tiedoston `src/geocode_events.py`, joka paivittaa tapahtumien koordinaatit ja geokoodausvalimuistin tiedostossa `data/geocache.json`.

Tapahtumat ilman sijaintia (tyhja `location`-kentta tai koordinaattivirhe) nakyvat sovelluksessa aina tapahtumakorttilistauksen lopussa erillisessa `Sijainti ei tiedossa`-osiossa, eivatka katoa etaisyyssuodatuksen takia.

## Lahdekohtaiset periaatteet

- Suosi API:a ennen HTML-scrapea aina kun mahdollista.
- Pida lahdekohtainen parseri omassa tiedostossaan muodossa `src/*_events.py`.
- Kirjoita lahdekohtainen tulos tiedostoon `data/*_events.json`.
- Suodata vanhat tapahtumat jo lahdehakijassa, jos se on luotettavasti mahdollista.
- Kayta varalahteita, kuten ICS- tai RSS-syotteita, jos ensisijainen rajapinta ei aina ole vakaa.
