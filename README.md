# The Nobel brain drain

Where Nobel laureates were born against where they were working when they won: 760 prizes in physics, chemistry, physiology or medicine and economic sciences, 1901 to 2026, on one flow map, with the net gain and loss of every country, the United States as the great importer, Germany before and after 1933, the rise of Japan, the leading institutions, the share of women and the share born abroad by decade.

Interactive page: https://maps.tristanhotham.com/nobel-brain-drain/
Paper: https://doi.org/10.5281/zenodo.23857487
Blog post: https://blog.tristanhotham.com/2026/10/31/nobel-brain-drain/

## Headline results

- Born abroad: 237 of 760 prizes (31.2%) went to someone working outside their present-day birth country; the share stayed between 24% (1930s) and 38% (1900s) in every decade.
- The great importer: 402 prizes were won by people working in the United States and 271 by people born there, a net gain of +131. 33.6% of American prizes went to people born abroad, from 40 countries, and the US received 57% of all prizes won outside the laureate's birth country. Only 5 countries have a net gain; the next largest is Switzerland (+9).
- Germany: 31.3% of prizes up to 1932 went to people working in Germany, 6.5% since 1933. 10% of German-born laureates (German lands of the day) who won up to 1932 were working abroad, 49% of those who won from 1933.
- Japan: 5 science laureates before 2000, 22 since, the third most common birth country since 2000; 7 of 27 won in the United States.
- Institutions: Harvard (31), MIT (25), Stanford (24) and Berkeley (23) lead; 9 of the top ten are American.
- Women: 3.8% of prizes to people before 1960, 19.5% in the 2020s so far.
- Peace and Literature (no affiliations): 18% of the 224 with a country of residence lived outside their birth country.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/laureates.csv` | One row per prize awarded to a person (1,005): Nobel ID, Wikidata ID, name, sex, birth year, prize, year, share, birthplace and birth country (then and now), birth point and method, primary affiliation, city and country, work point and method, Wikidata employer used, number and countries of affiliations, residence (Peace, Literature), whether in the flow analysis and born abroad, how it matched Wikidata, nobelprize.org link. |
| `data/countries.csv` | Per present-day country: born there, won there, net gain, stayed, left, arrived, top destinations and origins. |
| `data/flows.csv` | Every birth country to work country pair, with counts. |
| `data/institutions.csv` | Every institution at the award, prizes by subject, laureates born in another country, names. |
| `data/decades.csv` | By award decade: prizes, women, flow records, born abroad, prizes won in the US and born abroad among them. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/points.json`, `data/site.json`, `data/world.json`, `data/cities.json` | Page data: laureates with points, country and institution summaries, outlines, city labels. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots from the last check of the page at desktop and phone widths. |

## Method in brief

- Records: one per prize awarded to a person in the Nobel Prize API (1,005; organisations excluded). Names, prizes, years, sex, birthplaces and affiliations at the award come from the API.
- Flow analysis: physics, chemistry, medicine and economics records with a birthplace and an affiliation (760 of 769). The primary affiliation is the first the API lists that has a place. Peace and Literature have no affiliations and are analysed by country of residence.
- Matching: physics, chemistry and medicine laureates matched to Wikidata by Wikidata ID with prize and year checked (666 of 668; the other two by name, prize and year).
- Points (method column on every row): birthplaces at Wikidata coordinates (664), else the API's city point (334), a Natural Earth town (1) or the country centre (6). Workplaces at a Wikidata employer matching the affiliation within 60 km of the API's city (474 of 760), else the API's city point (284) or a hand-set point (2).
- Countries are present-day ones from the API; the Germany section uses the birth country named at the time.
- Caveats: affiliation at the award is not always where the winning work was done; birth country is not nationality; Nobel prizes are a small, selective sample.

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib, fontTools and Pillow, xelatex (TeX Gyre Pagella, Inter) and pdftotext; node with Playwright for the QA screenshots. Raw inputs are read in place (paths in `code/common.py`): `nobel_api_laureates.json` (Nobel Prize API v2.1), `wikidata_nobel.tsv` (QLever query on Wikidata), the Wikipedia list of laureates by university affiliation, and Natural Earth countries and populated places, all retrieved 2026. Intermediate files go to `/dev/shm/nobel/work` (set `NOBELTMP` to change).

```
python3 code/01_parse.py        # parse the API and Wikidata, match people
python3 code/02_geo.py          # countries, birthplace and workplace points, outlines
python3 code/03_results.py      # results.json, CSV files and page data
python3 code/04_build_site.py   # index.html (checks the facts stated in words)
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage
node code/12_qa.js              # screenshots (serve the folder on port 8823 first)
```

## Sources and licences

- Nobel Prize API v2.1 (https://api.nobelprize.org/), Nobel Prize Outreach. The downloaded JSON carries no licence statement; check the API terms of use on nobelprize.org before reusing `data/laureates.csv` beyond this project.
- Wikidata, via QLever (https://qlever.cs.uni-freiburg.de/wikidata). CC0.
- Wikipedia, List of Nobel laureates by university affiliation (revision 1381233532), used only to cross-check institution counts. CC BY-SA 4.0; no text or table is redistributed.
- Natural Earth countries and populated places (public domain).
- Base map tiles on the page: © Esri.

Derived data, text and figures: CC BY 4.0, subject to the Nobel Prize API terms for the laureate fields. Code: MIT (see LICENSE).

## Citation

Hotham, T. (2026) The Nobel brain drain: where laureates were born and where they won. Zenodo. https://doi.org/10.5281/zenodo.23857487

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
