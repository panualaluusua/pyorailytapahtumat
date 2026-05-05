# Project Description: Pyöräilytapahtumat Suomessa

Tämä projekti syntyi sivutuotteena, kun tein Ride Club Finlandille Discord-listauksen kaikista ulkopyöräilytapahtumista Suomessa. Listauksen pohjalta nousi tarve tarjota tapahtumat myös visuaalisessa ja helposti selattavassa muodossa.

## Tarkoitus

Pyöräilytapahtumien tiedot ovat hajallaan kymmenissä eri lähteissä — seurojen omilla sivuilla, Facebookissa, Bikelandissa, pyoraily.fi:ssä. Tämä projekti kokoaa ne automaattisesti yhteen paikkaan ja näyttää ne kartalla.

## Datalähteet ja tekninen toteutus

### pyoraily.fi (pääasiallinen lähde)
Suomen Pyöräilyn virallinen tapahtumakalenteri. Käyttää julkista Django REST API:a osoitteessa `tulokset.pyoraily.fi/api/events/`. API-avain on upotettu sivun HTML:ään. Palauttaa kattavasti maantie-, MTB-, gravel- ja cyclocross-tapahtumat.

### Bikeland.fi
Ei REST API:a — data haetaan sivulle upotetusta JavaScript-muuttujasta `upcoming_eventdata`. Sisältää pääasiassa suurempia massatapahtumia.

### Pyöräilyseurat (yleinen scraper)
Generinen WordPress REST API + RSS -scraper Finnish cycling club -sivustoille. Seurat konfiguroidaan `data/club_sources.json`-tiedostossa. Scraper:
- Tunnistaa automaattisesti WordPress-kategoriat joiden nimi/slug viittaa tapahtumiin (*tapahtumat*, *kilpailut*, *ajot* jne.)
- Parsii suomalaiset päivämääräformaatit: `dd.mm.yyyy`, `dd.mm.` ja `dd.mm` (ilman pistettä)
- Käyttää 8 kuukauden ikkunaa lyhyille päivämäärille (ilman vuotta) virheiden välttämiseksi
- Tukee sekä WordPress REST API:a että RSS-syötteitä

### Manuaaliset tapahtumat
`data/simple_events.txt` — yksinkertainen tekstimuoto tapahtumille joita ei löydy automaattisesti.

### Admin-paneeli
Streamlit-pohjainen ylläpitoliittymä tapahtumien muokkaamiseen, piilottamiseen ja käsin lisäämiseen.

## Prioriteettijärjestys duplikaattien hallinnassa

Kun sama tapahtuma löytyy useammasta lähteestä, korkein prioriteetti voittaa:

`admin-paneeli` > `manuaalinen` > `pyoraily.fi` > `bikeland` > `seurat`

## Automaatio

`update.py` on yksi ajettava skripti joka:
1. Hakee tapahtumat kaikista lähteistä
2. Yhdistää ja deduploi
3. Commitoi muuttuneet datatiedostot
4. Pushaa GitHubiin → Streamlit Cloud päivittyy automaattisesti

Ajetaan viikoittain cowork-automaatiolla.

## Jatkosuunnitelmat

- Lisätä enemmän pyöräilyseuroja `club_sources.json`-listaan
- Mahdollisesti laajentaa muihin kestävyysurheilulajeihin (juoksu, triathlon)
