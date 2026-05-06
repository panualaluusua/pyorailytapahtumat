# Project Description: Pyorailytapahtumat Suomessa

Tama projekti kokoaa suomalaisia ulkopyorailytapahtumia useista lahteista yhteen paikkaan ja nayttaa ne kartalla Streamlit-sovelluksessa.

## Tarkoitus

Pyorailytapahtumien tiedot ovat hajallaan eri palveluissa, jarjestajien omilla sivuilla ja tapahtuma-alustoilla. Projektin tavoite on:

- hakea tapahtumat koneellisesti eri lahteista
- muuntaa ne yhteiseen skeemaan
- poistaa duplikaatit lahdeprioriteetin avulla
- geokoodata sijainnit karttakayttoa varten
- tarjota lopputulos helposti selattavana datana ja karttanakymana

## Aktiiviset lahteet

### pyoraily.fi

Projektin kattavin yksittainen lahde. Kayttaa julkista API:a osoitteessa `tulokset.pyoraily.fi/api/events/`.

### RaceResult

`my.raceresult.com`-palvelusta haetaan Suomen tapahtumia julkisen hakemiston kautta.

### Monesko

Moneskon pyorailykategorian tapahtumat haetaan ensisijaisesti The Events Calendar REST API:sta. Jos API-haku epaonnistuu, kaytetaan iCalendar-vientia varalahteena.

### Bikeland.fi

Tapahtumat haetaan Bikelandin sivulle upotetusta JavaScript-datasta.

### Webscorer

Webscorerin Suomen pyorailytapahtumia listaava haku parsitaan HTML-sivulta.

### Pyorailyseurat

Seurojen omat sivut haetaan yleisella WordPress REST API / RSS -hakijalla. Seurat maaritellaan tiedostossa `data/club_sources.json`.

### Manuaaliset tapahtumat

Tiedostoon `data/simple_events.txt` voi lisata tapahtumia, joita mikaan automaattinen lahde ei kata. Parseri kirjoittaa ne tiedostoon `data/manual_events.json`.

### Admin-muokkaukset

Admin-nakyma voi lisata, muokata tai piilottaa tapahtumia tiedoston `data/manual_edits.json` kautta. Nama muutokset ovat korkeimmalla prioriteetilla.

## Prioriteettijarjestys

Kun sama tapahtuma loytyy useammasta lahteesta, lahteet jarjestetaan seuraavasti:

`manual_edit` > `manual` > `pyorailyfi` > `raceresult` > `monesko` > `bikeland` > `webscorer` > `club_wp`

Prioriteetit on toteutettu tiedostossa `src/event_manager.py`.

## Paivitysputki

Projektin paivitysskripti on `update.py`. Se:

1. ajaa kaikki aktiiviset lahdehakijat
2. yhdistaa tulokset tiedostoon `data/all_events.json`
3. geokoodaa tapahtumien sijainnit ja paivittaa `data/geocache.json`-tiedoston
4. tarkistaa, muuttuiko jokin seuratuista datatiedostoista
5. commitoi ja pushaa muutokset, ellei kayteta `--dry-run`-tilaa

## Kayttoliittymat

Kayttajalle lopputulos nakyy Streamlit-sovelluksessa tiedostossa `src/event_map_app.py`.

Lisaksi projektissa on Streamlit-pohjainen admin-nakyma tiedostossa `src/event_admin.py`.

## Jatkosuunnat

Luontevia seuraavia laajennuksia ovat esimerkiksi:

- uudet alueelliset tapahtuma-API:t
- lisa seuroja tiedostoon `data/club_sources.json`
- laadukkaampi deduplikointi tapauksissa, joissa sama tapahtuma esiintyy eri nimivariaatioilla
