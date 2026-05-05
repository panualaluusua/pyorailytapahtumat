# Suomen pyöräilyseurat — masterlist

Tähän tiedostoon kerätään tiedossa olevia suomalaisia pyöräilyseuroja yhteystietoineen.
Tähtimerkatut (**) seurat ovat jo mukana automaattisessa scraperissa (`data/club_sources.json`).

---

## Pääkaupunkiseutu

| Seura | Kotisivu | Laji | Scraper |
|-------|----------|------|---------|
| IK-32 Espoo | https://www.ik-32.org | Maantie, MTB | ** wp_api |
| MTB Club Finland (MTBCF) | https://www.mtbcf.net | MTB | ** wp_api |
| Korson Kaiku | https://www.korsonkaiku.fi | Maantie | ** rss |
| Helsinki Cycling | https://www.helsinkicycling.fi | Maantie | |
| Porin Pyöräilijät | | | |

## Tampere

| Seura | Kotisivu | Laji | Scraper |
|-------|----------|------|---------|
| Kaupin Kanuunat | https://www.kaupinkanuunat.fi | Maantie, MTB | ** rss |
| Team Velo Cycling | https://www.teamvelocycling.fi | Maantie | ** wp_api |

## Oulu

| Seura | Kotisivu | Laji | Scraper |
|-------|----------|------|---------|
| OTC Oulu (Oulun Tarmo Cycling) | https://www.otcoulu.fi | Maantie, MTB | |

## Jyväskylä

| Seura | Kotisivu | Laji | Scraper |
|-------|----------|------|---------|
| JYPS Jyväskylä | https://www.jyps.fi | Maantie | ** wp_api |

## Lahti

| Seura | Kotisivu | Laji | Scraper |
|-------|----------|------|---------|
| Lahden Pyöräilijät | https://www.lahdenpyorailijat.fi | Maantie | ** wp_api |

## Lappeenranta

| Seura | Kotisivu | Laji | Scraper |
|-------|----------|------|---------|
| Lappeenrannan Pyöräilijät | https://www.lappeenrannanpyorailijat.fi | Maantie | ** wp_api |

## Kuopio

| Seura | Kotisivu | Laji | Scraper |
|-------|----------|------|---------|
| Kuopion Pyöräilijät (KuoPyS) | https://www.kuopys.fi | Maantie | ** wp_api |

---

## Tutkittavat / selvittämättä

Seurat joiden sivuja tai lajia ei vielä tunneta:

- Turun Urheiluliitto (pyöräily)
- Tampereen Pyörintä
- Joensuun Kataja (pyöräily)
- Vaasan pyöräilyseurat

---

## Muistiinpanot alustatyypeistä

- **WordPress REST API** (`wp_api`): yleisin. Toimii jos sivustolla on `/wp-json/wp/v2/posts`.
- **RSS** (`rss`): vaihtoehto WP-sivustoille tai muille. Haetaan `/feed/`-osoitteesta.
- **Yhdistysavain**: oma alusta, ei REST API:a eikä RSS:ää. Ei tue scraper-integraatiota.
- **Sporttisaitti**: oma alusta, ei tue scraper-integraatiota.
- **Facebook**: ei julkista API:a. Tapahtumat lisättävä manuaalisesti.
