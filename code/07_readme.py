"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, ab, us, de, jp, c, w, inst, pl = R["source"], R["abroad"], R["us"], R["germany"], R["japan"], R["countries"], R["women"], R["institutions"], R["peace_lit"]
N = lambda v: f"{round(v):,}"
readme = f"""# The Nobel brain drain

Where Nobel laureates were born against where they were working when they won: {N(ab['n'])} prizes in physics, chemistry, physiology or medicine and economic sciences, 1901 to {s['y1']}, on one flow map, with the net gain and loss of every country, the United States as the great importer, Germany before and after 1933, the rise of Japan, the leading institutions, the share of women and the share born abroad by decade.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Born abroad: {ab['abroad']} of {ab['n']} prizes ({ab['pct']:.1f}%) went to someone working outside their present-day birth country; the share stayed between {ab['min_dec']['pct']:.0f}% ({ab['min_dec']['dec']}s) and {ab['max_dec']['pct']:.0f}% ({ab['max_dec']['dec']}s) in every decade.
- The great importer: {us['n']} prizes were won by people working in the United States and {us['born']} by people born there, a net gain of +{us['net']}. {us['pct']:.1f}% of American prizes went to people born abroad, from {us['n_orig']} countries, and the US received {us['share_imports']:.0f}% of all prizes won outside the laureate's birth country. Only {c['n_gain']} countries have a net gain; the next largest is Switzerland (+{c['che']['net']}).
- Germany: {de['work_share_to1932']:.1f}% of prizes up to 1932 went to people working in Germany, {de['work_share_since1933']:.1f}% since 1933. {de['early_abroad_pct']:.0f}% of German-born laureates (German lands of the day) who won up to 1932 were working abroad, {de['late_abroad_pct']:.0f}% of those who won from 1933.
- Japan: {jp['before2000']} science laureates before 2000, {jp['since2000']} since, the third most common birth country since 2000; {jp['n_abroad']} of {jp['n']} won in the United States.
- Institutions: Harvard ({inst['top'][0]['n']}), MIT ({inst['top'][1]['n']}), Stanford ({inst['top'][2]['n']}) and Berkeley ({inst['top'][3]['n']}) lead; {inst['top10_us']} of the top ten are American.
- Women: {w['before1960_pct']:.1f}% of prizes to people before 1960, {w['d2020']['pct']:.1f}% in the 2020s so far.
- Peace and Literature (no affiliations): {pl['pct']:.0f}% of the {pl['placed']} with a country of residence lived outside their birth country.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/laureates.csv` | One row per prize awarded to a person ({s['n_recs']:,}): Nobel ID, Wikidata ID, name, sex, birth year, prize, year, share, birthplace and birth country (then and now), birth point and method, primary affiliation, city and country, work point and method, Wikidata employer used, number and countries of affiliations, residence (Peace, Literature), whether in the flow analysis and born abroad, how it matched Wikidata, nobelprize.org link. |
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

- Records: one per prize awarded to a person in the Nobel Prize API ({s['n_recs']:,}; organisations excluded). Names, prizes, years, sex, birthplaces and affiliations at the award come from the API.
- Flow analysis: physics, chemistry, medicine and economics records with a birthplace and an affiliation ({ab['n']} of {s['n_sci']}). The primary affiliation is the first the API lists that has a place. Peace and Literature have no affiliations and are analysed by country of residence.
- Matching: physics, chemistry and medicine laureates matched to Wikidata by Wikidata ID with prize and year checked ({s['n_match_id']} of {s['n_sci3']}; the other two by name, prize and year).
- Points (method column on every row): birthplaces at Wikidata coordinates ({s['n_b_wd']}), else the API's city point ({s['n_b_api']}), a Natural Earth town ({s['n_b_ne']}) or the country centre ({s['n_b_country']}). Workplaces at a Wikidata employer matching the affiliation within 60 km of the API's city ({s['n_w_emp']} of {ab['n']}), else the API's city point ({s['n_w_api']}) or a hand-set point ({s['n_w_manual']}).
- Countries are present-day ones from the API; the Germany section uses the birth country named at the time.
- Caveats: affiliation at the award is not always where the winning work was done; birth country is not nationality; Nobel prizes are a small, selective sample.

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib, fontTools and Pillow, xelatex (TeX Gyre Pagella, Inter) and pdftotext; node with Playwright for the QA screenshots. Raw inputs are read in place (paths in `code/common.py`): `nobel_api_laureates.json` (Nobel Prize API v2.1), `wikidata_nobel.tsv` (QLever query on Wikidata), the Wikipedia list of laureates by university affiliation, and Natural Earth countries and populated places, all retrieved {RETRIEVED}. Intermediate files go to `/dev/shm/nobel/work` (set `NOBELTMP` to change).

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
- Wikipedia, List of Nobel laureates by university affiliation (revision {inst['wiki_revid']}), used only to cross-check institution counts. CC BY-SA 4.0; no text or table is redistributed.
- Natural Earth countries and populated places (public domain).
- Base map tiles on the page: © Esri.

Derived data, text and figures: CC BY 4.0, subject to the Nobel Prize API terms for the laureate fields. Code: MIT (see LICENSE).

## Citation

Hotham, T. (2026) The Nobel brain drain: where laureates were born and where they won. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in readme, bad
assert "--" not in readme.replace("|---|---|", "")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. They are derived from the Nobel
Prize API (Nobel Prize Outreach; see its terms of use on nobelprize.org for
the laureate fields), Wikidata (CC0) and Natural Earth (public domain).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] The Nobel brain drain: {us['pct']:.0f}% of Nobel prizes won in the US went to people born abroad, and the US gained {us['net']} more laureates than it grew. Only {c['n_gain']} countries come out ahead

## Body

I drew a line from birthplace to prize for every Nobel laureate in physics, chemistry, medicine and economics, 1901 to {s['y1']} ({ab['n']} prizes), using the Nobel Prize's own API for birthplaces and affiliations at the award and Wikidata for coordinates. {ab['pct']:.0f}% went to someone working outside their birth country. The US hosted {us['n']} prizes but grew only {us['born']} laureates (+{us['net']}); after it, the biggest net gain is Switzerland's +{c['che']['net']}. Germany took {de['work_share_to1932']:.0f}% of prizes up to 1932 and {de['work_share_since1933']:.1f}% since 1933. Japan went from {jp['before2000']} science laureates in the 20th century to {jp['since2000']} since 2000, and unlike most countries it keeps them. Caveats: affiliation at the award is not always where the winning work was done, birth country is not nationality, and Poland's big "loss" is mostly Germans born in places that are Polish today. Interactive flow map with prize, decade and sex filters: {PAGE}

## Source comment

Source: Nobel Prize API v2.1 (Nobel Prize Outreach), 2026: every prize to a person, with birthplace and affiliations at the award; Wikidata (CC0) via QLever for birthplace and institution coordinates, matched by Wikidata ID with prize and year checked; Natural Earth. Present-day countries. Peace and Literature have no affiliations and are left out of the flows. Map labels were placed by a script that checks each one sits on plain sea and covers no line or dot.

Tools: Python (shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for bad in ("—", "–", "--"):
    assert bad not in post, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words; post", len(post.split()), "words")
