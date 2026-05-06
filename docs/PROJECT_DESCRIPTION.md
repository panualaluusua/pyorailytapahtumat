# Project Description: Pyorailytapahtumat Suomessa

Tama projekti kokoaa suomalaisia ulkopyorailytapahtumia useista lahteista yhteen paikkaan ja nayttaa ne kartalla.

## Tarkoitus

Pyorailytapahtumien tiedot ovat hajallaan eri palveluissa, jarjestajien omilla sivuilla ja tapahtuma-alustoilla. Projektin tavoite on:

- hakea tapahtumat koneellisesti eri lahteista
- yhdistaa ne yhteiseen skeemaan
- poistaa duplikaatit lahdeprioriteetin avulla
- tarjota lopputulos helposti selattavana datana ja karttanakymana

## Aktiiviset lahteet

### pyoraily.fi

Projektin kattavin yksittainen lahde. Kayttaa julkista Django REST API:a osoitteessa `tulokset.pyoraily.fi/api/events/`.

### RaceResult

`my.raceresult.com`-palvelusta haetaan Suomen tapahtumia julkisen tapahtemahakemiston kautta maantieteellisella rajauksella.

### Monesko

Moneskon pyorailykategorian tapahtumat haetaan ensisijaisesti The Events Calendar REST API:sta. Jos API-haku epaonnistuu, kaytetaan iCalendar-vientia varalahteena.

### Bikeland.fi

Tapahtumat haetaan Bikelandin sivulle upotetusta JavaScript-datasta.

### Webscorer

Webscorerin Suomen pyorailytapahtumia listaava haku parsitaan HTML-sivulta.

### Pyorailyseurat

Seurojen omat sivut haetaan yleisella WordPress REST API / RSS -scraperilla. Seurat maaritellaan tiedostossa `data/club_sources.json`.

### Manuaaliset tapahtumat

Tiedostoon `data/simple_events.txt` voi lisata tapahtumia, joita mikaan automaattinen lahde ei kata.

### Admin-paneelin muokkaukset

Admin-paneeli voi lisata, muokata tai piilottaa tapahtumia. Nama muutokset ovat korkeimmalla prioriteetilla.

## Prioriteettijarjestys

Kun sama tapahtuma loytyy useammasta lahteesta, lahteet jarjestetaan seuraavasti:

`admin-paneeli` > `manuaalinen` > `pyoraily.fi` > `raceresult` > `monesko` > `bikeland` > `webscorer` > `club_wp`

Prioriteetit on toteutettu tiedostossa `src/event_manager.py`.

## Automaatio

`update.py` on projektin paivitysskripti. Se:

1. ajaa kaikki aktiiviset lahdehakijat
2. yhdistaa tulokset tiedostoon `data/all_events.json`
3. tarkistaa, muuttuiko jokin datatiedosto
4. commitoi ja pushaa muutokset, ellei kayteta `--dry-run`-tilaa

## Kayttoliittyma

Kayttajalle lopputulos nakyy Streamlit-sovelluksessa tiedostossa `src/event_map_app.py`.

Lisaksi projektissa on Streamlit-pohjainen admin-nakyma tiedostossa `src/event_admin.py`.

## Jatkosuunnat

Luontevia seuraavia laajennuksia ovat esimerkiksi:

- uudet alueelliset tapahtuma-API:t
- lisa seuroja `club_sources.json`-tiedostoon
- laadukkaampi deduplikointi tapauksissa, joissa sama tapahtuma esiintyy eri nimivariaatioilla
