# Event Sources

Tama dokumentti kuvaa projektin nykyiset aktiiviset tapahtumalahteet, niiden teknisen toteutuksen ja toteutusjarjestyksen yhdistelyputkessa.

Paivitetty: 2026-05-05

## Nykyiset lahteet

### 1. pyoraily.fi

- Toteutus: suora API-haku
- Koodi: `src/pyorailyfi_events.py`
- Tulosdata: `data/pyorailyfi_events.json`
- Huomio: projektin kattavin yksittainen lahde

### 2. RaceResult

- Toteutus: julkisen tapahtemahakemiston haku maantieteellisella rajauksella
- Koodi: `src/raceresult_events.py`
- Tulosdata: `data/raceresult_events.json`
- Huomio: loytaa erityisesti ajanotto- ja ilmoittautumisalustoilla julkaistuja tapahtumia

### 3. Monesko

- Toteutus: The Events Calendar REST API, varalla iCalendar-vienti
- Koodi: `src/monesko_events.py`
- Tulosdata: `data/monesko_events.json`
- Huomio: rajaus pyorailykategoriaan

### 4. Bikeland.fi

- Toteutus: HTML-sivulle upotetun JavaScript-datan parsing
- Koodi: `src/bikeland_events.py`
- Tulosdata: `data/bikeland_events.json`

### 5. Webscorer

- Toteutus: HTML-haku Webscorerin Suomen pyorailytapahtumien listauksesta
- Koodi: `src/webscorer_events.py`
- Tulosdata: `data/webscorer_events.json`

### 6. Pyorailyseurojen sivut

- Toteutus: WordPress REST API / RSS
- Koodi: `src/club_events.py`
- Tulosdata: `data/club_events.json`
- Konfiguraatio: `data/club_sources.json`

### 7. Manuaaliset tapahtumat

- Toteutus: paikallinen tekstisyote
- Koodi: `src/manual_events.py`
- Tulosdata: `data/manual_events.json`
- Syote: `data/simple_events.txt`

### 8. Admin-muokkaukset

- Toteutus: kasin tehdyt korjaukset ja lisaykset
- Tulosdata: `data/manual_edits.json`
- Huomio: korkein prioriteetti yhdistelyssa

## Yhdistely ja prioriteetit

Kaikki lahteet yhdistetaan tiedostossa `src/event_manager.py`, joka kirjoittaa lopullisen datan tiedostoon `data/all_events.json`.

Lahdeprioriteetti on:

`manual_edit` > `manual` > `pyorailyfi` > `raceresult` > `monesko` > `bikeland` > `webscorer` > `club_wp`

Tama tarkoittaa, etta jos sama tapahtuma loytyy useasta lahteesta samalla deduplikointiavaimella, korkeamman prioriteetin lahde voittaa.

## Deduplikointi

Projektin ensisijainen deduplikointiavain on:

- `title + event date`

Kaytannossa avain muodostetaan tapahtuman otsikosta ja paivamaarasta.

## Lahdekohtaiset periaatteet

- Suosi API:a ennen HTML-scrapea aina kun mahdollista.
- Pida lahdekohtainen parseri omassa tiedostossaan muodossa `src/*_events.py`.
- Kirjoita lahdekohtainen tulos tiedostoon `data/*_events.json`.
- Suodata vanhat tapahtumat jo lahdehakijassa, jos se on luotettavasti mahdollista.
- Kayta varalahteita, kuten ICS- tai RSS-syotteita, jos ensisijainen rajapinta ei aina ole vakaa.

## Toteutettu Monesko-integraatio

Monesko on aktiivinen tuotantolahde. Toteutus:

1. hakee tapahtumat ensisijaisesti API:sta
2. putoaa tarvittaessa iCalendar-vientiin
3. muuntaa datan projektin yhteiseen skeemaan
4. kirjoittaa tuloksen tiedostoon `data/monesko_events.json`

## Seuraavat mahdolliset lahteet

Toteutettuja lahteita ei enaa pideta backlog-listana tassa dokumentissa. Seuraavia tutkittavia lahteita voivat olla esimerkiksi:

- Satakunta Events API
- Keski-Suomi Events API
- muut Aluekalenteri-perheen instanssit
- muut alueelliset Linked Events -rajapinnat
