# Event Sources

Tama dokumentti kokoaa yhteen projektin tapahtumalähteet, niihin liittyvat tekniset havainnot seka ehdotetut seuraavat integraatiot.

Paivitetty: 2026-05-05

## Nykyiset lahteet

Projektissa on talla hetkella kaytossa seuraavat lahteet:

- `Bikeland.fi`
  - Toteutus: HTML-sivun scraping
  - Koodi: `src/bikeland_events.py`
  - Tulosdata: `data/bikeland_events.json`

- `pyoraily.fi`
  - Toteutus: suora API-haku
  - Koodi: `src/pyorailyfi_events.py`
  - Tulosdata: `data/pyorailyfi_events.json`

- `Pyorailyseurojen sivut`
  - Toteutus: WordPress REST API / RSS
  - Koodi: `src/club_events.py`
  - Tulosdata: `data/club_events.json`

- `Manuaaliset tapahtumat`
  - Toteutus: paikallinen tekstisyote
  - Koodi: `src/manual_events.py`
  - Tulosdata: `data/manual_events.json`

- `Monesko`
  - Toteutus: suora API-haku, varalla iCalendar-vienti
  - Koodi: `src/monesko_events.py`
  - Tulosdata: `data/monesko_events.json`

Kaikki lahteet yhdistetaan tiedostossa `src/event_manager.py`, joka kirjoittaa lopullisen yhdistetyn datan tiedostoon `data/all_events.json`.

## Monesko-integraatio

Moneskon pyorailytapahtumille loytyi toimiva koneellinen lahde.

### Ensisijainen rajapinta

Monesko kayttaa The Events Calendar -pohjaista WordPress-ratkaisua, josta loytyy julkinen REST-rajapinta:

- Tapahtumat:
  - `https://monesko.fi/wp-json/tribe/events/v1/events?categories=pyoraily&per_page=100`
- Kategoriat:
  - `https://monesko.fi/wp-json/tribe/events/v1/categories`

Havaintoja:

- `categories=pyoraily` toimii oikein.
- Myos kategorian id loytyi:
  - `Pyoraily` slug `pyoraily`
  - category id `220`
- API palauttaa tapahtumille valmiit kentat kuten:
  - `title`
  - `start_date`
  - `url`
  - `website`
  - `categories`
  - `venue`
  - `organizer`
  - `description`

### Varalahde

Moneskon pyorailykategorialla on myos iCalendar-vienti:

- `https://monesko.fi/tapahtumat/category/pyoraily/?ical=1`

Tata kaytetaan varalahteena, jos API-haku epaonnistuu.

### Toteutus projektissa

Monesko lisattiin mukaan seuraavasti:

- uusi hakija: `src/monesko_events.py`
- mukaan yhdistelyyn: `src/event_manager.py`
- mukaan paivitysskriptiin: `update.py`

Hakijan toiminta:

1. Hakee tapahtumat ensisijaisesti Moneskon API:sta.
2. Jos API ei vastaa, hakee tapahtumat iCalendar-viennista.
3. Muuntaa datan projektin yhteiseen skeemaan.
4. Tallentaa tuloksen tiedostoon `data/monesko_events.json`.

### Vahvistettu toiminta

Integraatio testattiin 2026-05-05.

Tulokset:

- Moneskon API vastasi `200 OK`
- kategoriarajaus `categories=pyoraily` toimi
- iCalendar-vienti vastasi `200 OK`
- projektin paikallinen Monesko-hakija toi sisaan 9 tapahtumaa
- koko tapahtumaputki meni onnistuneesti lapi

## Nettihaulla loydetyt muut aggregaattorilahteet

Moneskon lisaksi etsittiin muita pyorailytapahtumia keskittavia sivuja tai alueellisia tapahtuma-alustoja, joista voisi hakea dataa koneellisesti.

### 1. my.raceresult.com

Lahteet:

- `https://my.raceresult.com/?lang=fi`
- esimerkkitapahtuma:
  - `https://my.raceresult.com/380418/contact`
- virallinen taustadokumentaatio:
  - `https://www.raceresult.com/en-us/support/kbexport2?id=2979`
  - `https://www.raceresult.com/es/support/kbexport2?id=4949`

Havainto:

- `my.raceresult.com` on julkinen tapahtemahakemisto, jossa voi selata tapahtumia:
  - maittain
  - paivittain
  - lajityypeittain
- palvelussa on suoraan lajikategoriat kuten:
  - `Mountain Bike`
  - `Cycling`
  - `Bike Tour`
- suomalaisia pyorailytapahtumia loytyy palvelusta, esimerkiksi:
  - `Yllas-Levi MTB`
  - `Dirty Sipoo`
  - `Falling Leaves Lahti`
- virallinen dokumentaatio vahvistaa, etta tapahtumat voidaan julkaista my.raceresultin tapahtumakalenteriin
- loytyi virallinen `Settings API`, mutta haussa ei vahvistunut yleista julkista tapahtumalista-API:a samalla tasolla kuin Moneskon tai Satakunta Eventsin tapauksessa

Arvio:

- Hyodyllinen integraatiokandidaatti
- Soveltuu erityisesti tapahtumien loytamiseen, joilla on ajanotto- tai ilmoittautumisalusta RACE RESULTissa
- Tekninen riski on se, etta julkinen tapahtumahakemisto voi vaatia HTML-parsintaa, jos avointa yleista hakurajapintaa ei ole
- Kannattaa lisata dokumentoituun backlogiin, mutta toteuttaa vasta dokumentoidut API-lahteet ensin

Toteutussuositus:

- ensisijaisesti yritetaan loytaa vakaa, dokumentoitu haku- tai export-endpoint
- jos sellaista ei ole, rajattu HTML-haku voi olla mahdollinen
- suodatus kannattaa tehda ainakin:
  - `country = Finland`
  - `sport in Cycling / Mountain Bike / Bike Tour`
  - tekstihaku avainsanoilla kuten `gravel`, `mtb`, `pyoraily`, `bikepacking`


### 7. Webscorer

Lahteet:

- `https://www.webscorer.com/`
- suomalaisia esimerkkijarjestajia:
  - `https://www.webscorer.com/hel_cx?pg=start`
  - `https://www.webscorer.com/op-p`
  - `https://www.webscorer.com/vlkmtb`

Havainto:

- Webscorerissa on runsaasti suomalaisia pyorailyjarjestajia ja tapahtumien starttilistoja, tuloksia ja sarjoja
- palvelu nayttaa toimivan enemman jarjestaja- ja tapahtumakohtaisina sivuina kuin yhtena selvana julkisena pyorailykalenterina
- haku osoittaa, etta alustalla on kaytossa:
  - `registrations`
  - `start lists`
  - `results`
  - `series standings`

Arvio:

- Potentiaalinen lisalahde varsinkin pienemmille kilpailuille
- Parempi todennakoinen kayttotapa on jarjestajakohtainen integraatio kuin koko palvelun laaja yleisscrape
- Ei nayta yhta suoraviivaiselta aggregaattorilta kuin my.raceresult tai aluekalenteri-API:t

### 8. Datasport

Lahteet:

- `https://datasport.com/en/sport-events/series/bike-marathon-classics/`
- `https://datasport.com/en/essentials/overview-of-cycling-events/`

Havainto:

- Datasport julkaisee pyorailytapahtumien koonti- ja sarjasivuja
- palvelu on selvasti tapahtuma- ja ilmoittautumisalusta
- hakutuloksissa nakyi pyorailyyn liittyvia koontisivuja ja tapahtumasivuja

Arvio:

- Hyodyllinen referenssi saman kategorian alustoista
- Suomen tapahtumien kattavuus vaikuttaa taman haun perusteella rajallisemmalta kuin my.raceresultissa tai Webscorerissa
- Ei ole ensisijainen integraatiokohde tälle projektille

### 9. RaceID

Lahde:

- `https://raceid.com/`

Havainto:

- RaceID on ulkoilutapahtumien ja kilpailujen alusta, jossa on tapahtuma- ja seurantakomponentteja
- haussa ei vahvistunut tasta projektista katsottuna suora, hyvin dokumentoitu julkinen tapahtumahakemisto samalla tavalla kuin my.raceresultissa

Arvio:

- Kiinnostava alusta markkinan kannalta
- Ei talla hetkella tarpeeksi vahva integraatiokandidaatti ilman lisatutkimusta julkisesta tapahtumahakemistosta tai rajapinnasta

## Suositeltu toteutusjarjestys

Jos uusia aggregaattorilahteita lisataan projektiin, toteutusjarjestys kannattaa olla:

1. `Satakunta Events API`
2. `Keski-Suomi Events API`
3. `my.raceresult.com`
4. `Webscorer`
5. `Helsinki Linked Events`
6. `Espoo Linked Events`
7. `Menoinfo`, jos julkinen rajapinta tai muu vakaa koneellinen syote varmistuu

Perustelut:

- Satakunta Events ja Keski-Suomi Events tarjoavat suoraan dokumentoidun API:n.
- my.raceresult.com on kaytannossa relevantti pyorailytapahtumien hakemisto, mutta sen yleinen julkinen haku-API ei ole viela vahvistunut.
- Webscorerissa on paljon suomalaisia pyorailyjarjestajia ja tapahtumia, mutta se voi olla kaytannossa realistisempi jarjestajakohtaisena integraationa kuin yhtena globaalina hakuintegraationa.
- Helsinki ja Espoo tarjoavat laadukkaan avoimen rajapinnan, mutta vaativat enemman sisallollista filtterointia.
- Menoinfo on kiinnostava, mutta tekninen liittymapinta on viela epaselvempi.

## Toteutussuositus uusille lahteille

Uusissa integraatioissa kannattaa noudattaa samaa rakennetta kuin nykyisissa lahteissa:

1. Yksi lahde = yksi `src/*_events.py`
2. Tulos kirjoitetaan tiedostoon `data/*_events.json`
3. Lahde lisataan `src/event_manager.py`:hin
4. Lahde lisataan `update.py`:n paivitettaviin tiedostoihin

Suositus teknisesti:

- Suosi API:a ennen HTML-scrapea
- Kayta ICS/RSS-syotteita varalahteena, jos niita on tarjolla
- Pida lahdekohtainen parseri erillaan yhdistelylogiikasta
- Suodata vanhat tapahtumat jo lahdehakijassa
- Pidä `title + event date` ensimmaisena deduplikointiavaimena nykyisen mallin mukaisesti

## Seuraava konkreettinen askel

Seuraava paras lisatyo olisi toteuttaa `Satakunta Events` omaksi lahteekseen ja hakea sielta pyorailyyn liittyvat tapahtumat esimerkiksi tekstisuodatuksella kuten `pyoraily`, `gravel`, `mtb`, `maantie`, `bikepacking`.

Taman jalkeen seuraava kaytannollinen tutkimus olisi:

1. selvittaa, loytyyko `my.raceresult.com`:lle vakaa tapahtumahaku- tai export-rajapinta
2. arvioida `Webscorer`-integraatio ensin muutamalle tunnetulle suomalaiselle jarjestajalle
3. jos `my.raceresult.com`:lle ei loydy API:a, arvioida rajattu HTML-pohjainen integraatio vain Suomen pyorailylajeihin
