# Project Description: Pyöräilytapahtumat Suomessa

Tämä projekti syntyi sivutuotteena, kun tein Ride Club Finlandille Discord-listauksen kaikista ulkopyöräilytapahtumista Suomessa. Listauksen pohjalta nousi tarve tarjota tapahtumat myös visuaalisessa ja helposti selattavassa muodossa.

## Purpose
Tämän projektin tavoitteena on helpottaa pyöräilytapahtumien löytämistä ja madaltaa kynnystä osallistua niihin Suomessa. Ongelmaksi tunnistettiin se, että pyöräilytapahtumien tiedot ovat hajallaan eri lähteissä, eikä käyttäjillä ollut helppoa tapaa nähdä, mitä tapahtumia järjestetään heidän lähellään ja milloin.

## Ratkaisu
Projektissa rakennettiin työkalu, joka:
- **Kerää tapahtumatietoja** automaattisesti eri lähteistä (esim. Bikeland.fi, CSV-tiedostot) sekä mahdollistaa manuaalisen syötön.
- **Yhdistää ja hallinnoi tapahtumatietoja**, poistaa duplikaatit ja mahdollistaa ylläpidon.
- **Visualisoi tapahtumat kartalla**, jossa käyttäjä voi suodattaa tapahtumia mm. kuukauden, tyypin ja sijainnin mukaan.
- **Tarjoaa helpon käyttöliittymän** tapahtumien selaamiseen ja päivittämiseen.

## Toteutus
- **Karttasovellus** (toteutettu Streamlitillä) näyttää tulevat tapahtumat Suomen kartalla ja mahdollistaa suodatukset.
- **Tietojen yhdistäminen** ja hallinta tapahtuu Python-skripteillä, jotka hakevat, yhdistävät ja käsittelevät tapahtumatiedot.
- **Tapahtumatiedot** tallennetaan ja päivitetään helposti käytettävien skriptien avulla.

## Projektin rakenne
- `src/`: Python-skriptit (karttasovellus, tapahtumien hallinta, tietojen haku eri lähteistä).
- `data/`: Tapahtumatiedot ja syötteet (esim. all_events.json, simple_events.txt).
- `requirements.txt`: Tarvittavat Python-kirjastot.
- `.bat`-skriptit: Sovelluksen ja tapahtumapäivitysten käynnistys.
- `README.md`: Käyttöohjeet ja pikaopas.

## Hyödyt käyttäjälle
Karttapohjainen visualisointi ja suodatus tekevät tapahtumien löytämisestä helppoa ja intuitiivista. Näet yhdellä silmäyksellä, mitä pyöräilytapahtumia järjestetään lähelläsi ja milloin – tämä madaltaa osallistumiskynnystä ja auttaa löytämään juuri sinulle sopivia tapahtumia.
