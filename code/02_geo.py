"""Geography: countries, birthplace points and workplace points.

- world.json: light world outlines for the page and figures (Natural Earth 1:50m, simplified).
- Countries are the Nobel API's present-day country names ("countryNow"), matched to Natural Earth (ALIASES below).
  Birth country = the API's present-day birth country; work country = the present-day country of the affiliation
  at the time of the award. Scotland and Northern Ireland count as the United Kingdom, Guadeloupe as France and the
  Faroe Islands as Denmark, as the API itself names them.
- Birthplace point, in order of preference (column `birth_method`):
    wikidata       the Wikidata birthplace coordinates of the matched person (Physics, Chemistry, Medicine), when they
                   lie within 100 km of the API's city point, or inside the API's present-day birth country, or the API
                   has no city point (checked by hand: where the two disagree by more than 100 km the API point is
                   usually a namesake town, such as Cluny in France for John Macleod, born in Cluny, Scotland);
    api_city       the API's present-day city point;
    ne_city        a Natural Earth populated place with the same name in the same country;
    country        the country's Natural Earth label point (birthplace too vague or not given).
- Workplace point (column `work_method`), for the primary affiliation: the first affiliation listed by the Nobel API
  that has a place (the Howard Hughes Medical Institute and the LIGO/VIRGO Collaboration are listed without one, so a
  university listed beside them is used):
    wikidata_employer   a Wikidata employer (P108) of the same person whose name matches the affiliation and whose point
                        lies within 60 km of the API's city point (its own coordinates, else its headquarters);
    api_city            the API's present-day city point for the affiliation (a city centroid);
    ne_city             a Natural Earth populated place of the same name in that country;
    manual              a hand-set point for the few affiliations the API gives without a usable city (MANUAL below);
    country             the country's label point.
- Peace and Literature: the API usually gives no affiliation (four Peace prizes have one, and those are used) but a
  country of residence at the award. Those laureates
  are placed at their residence (city if given, else country label point; `work_method` residence_city or
  residence_country) and kept out of the main flow analysis, which covers the four prizes with affiliations.
- cities.json: place names for map labels.
"""
from collections import Counter
from difflib import SequenceMatcher
from shapely.geometry import shape, mapping, Point
from shapely.strtree import STRtree
from common import *

FIX = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "KAS": "IND"}
iso_of = lambda p: FIX.get(p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"], p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"])
ALIASES = {"USA": "USA", "United Kingdom": "GBR", "Scotland": "GBR", "Northern Ireland": "GBR", "the Netherlands": "NLD",
           "Faroe Islands (Denmark)": "DNK", "Guadeloupe, France": "FRA", "East Timor": "TLS", "Democratic Republic of the Congo": "COD",
           "Czech Republic": "CZE", "South Korea": "KOR", "Russia": "RUS", "Taiwan": "TWN", "Palestine": "PSE", "Iran": "IRN",
           "Vietnam": "VNM", "North Macedonia": "MKD", "Bosnia and Herzegovina": "BIH", "Trinidad and Tobago": "TTO", "Saint Lucia": "LCA",
           "Myanmar": "MMR", "Ivory Coast": "CIV", "Tibet": "CHN"}
# historical names of the German lands at birth (the API's birth "country" as it was then)
DE_THEN = {"Germany", "Prussia", "Bavaria", "Mecklenburg", "Hesse-Kassel", "Württemberg", "Schleswig", "East Friesland", "West Germany",
           "Free City of Danzig", "Hesse", "Saxony", "Baden", "Hanover", "Lübeck", "Hamburg", "Oldenburg"}
MANUAL = {  # affiliation name: (lon, lat, where), for affiliations the API gives without a usable city point
    "University of Delaware": (-75.7519, 39.6780, "Newark, Delaware"),
    "Argonne National Laboratory": (-87.9819, 41.7183, "Lemont, Illinois"),
    "Atomic Energy Research Establishment": (-1.3150, 51.5770, "Harwell, Oxfordshire"),
    "Francis Crick Institute": (-0.1287, 51.5316, "London"),
    "Clare Hall Laboratory": (-0.2135, 51.6901, "South Mimms, Hertfordshire"),
    "Konrad-Lorenz-Institut der Österreichischen Akademie der Wissenschaften, Forschungsstelle für Ethologie": (13.9500, 47.8500, "Grünau im Almtal"),
}
STOP = set("university universite universitat universidad universita of the for and de des du la le der die das fur institute institut instituto college school medical medicine center centre research laboratory laboratories national hospital society foundation".split())


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats = []
for f in W50["features"]:
    p = f["properties"]; iso = iso_of(p)
    g = shape(f["geometry"]).simplify(0.04, preserve_topology=True)
    if g.is_empty or iso == "ATA":
        continue
    gm = mapping(g)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")

W10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
meta, geoms, byname = {}, [], {}
for f in W10["features"]:
    p = f["properties"]; iso = iso_of(p)
    geoms.append((iso, shape(f["geometry"]).buffer(0)))
    for k in ("NAME", "NAME_EN", "ADMIN", "NAME_LONG", "FORMAL_EN"):
        if p.get(k):
            byname.setdefault(p[k], iso)
    if iso in meta and (meta[iso]["pop"] or 0) >= (p["POP_EST"] or 0):
        continue
    nm = (p["NAME_EN"] or p["NAME"]).replace("People's Republic of China", "China").replace("United States of America", "United States")
    nm = {"KOS": "Kosovo", "PSE": "Palestine", "CYP": "Cyprus", "TWN": "Taiwan", "CZE": "Czech Republic", "MKD": "North Macedonia",
          "COD": "DR Congo", "GBR": "United Kingdom", "KOR": "South Korea", "RUS": "Russia", "IRN": "Iran", "VNM": "Vietnam",
          "NLD": "Netherlands", "PHL": "Philippines", "TLS": "East Timor", "BIH": "Bosnia and Herzegovina", "TTO": "Trinidad and Tobago",
          "LCA": "Saint Lucia", "GMB": "Gambia", "BHS": "Bahamas"}.get(iso, nm)
    cont = p["CONTINENT"]
    if cont == "Seven seas (open ocean)":
        cont = "Africa" if p["SUBREGION"] in ("Eastern Africa", "Southern Africa") else "Asia" if "Asia" in p["SUBREGION"] else "Oceania"
    meta[iso] = {"name": nm, "cont": cont, "pop": p["POP_EST"], "lx": round(p["LABEL_X"], 3), "ly": round(p["LABEL_Y"], 3)}
tree = STRtree([g for _, g in geoms])


def at(lon, lat):
    pt_ = Point(lon, lat)
    hit = [geoms[i][0] for i in tree.query(pt_) if geoms[i][1].covers(pt_)]
    if hit:
        return hit[0]
    near = [(geoms[i][1].distance(pt_), geoms[i][0]) for i in tree.query(pt_.buffer(0.2))]
    near = [x for x in near if x[0] < 0.2]
    return min(near)[1] if near else None


def iso_name(n):
    if not n:
        return None
    if n in ALIASES:
        return ALIASES[n]
    if n in byname:
        return byname[n]
    raise KeyError(n)


P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
NEP = {}
for f in P:
    p = f["properties"]
    for k in ("name", "nameascii", "namealt"):
        if p.get(k):
            NEP.setdefault((norm(p[k]), p["adm0_a3"]), (round(p["longitude"], 4), round(p["latitude"], 4)))


def ne_city(city, iso):
    if not city:
        return None
    c = norm(re.split(r",| near ", city)[0])
    for a3 in {iso, {"SDS": "SSD"}.get(iso, iso)}:
        if (c, a3) in NEP:
            return list(NEP[(c, a3)])
    return None


def toks(s):
    return {t for t in norm(re.sub(r"\(.*?\)", " ", s or "")).split() if t not in STOP and len(t) > 2}


def emp_match(aff, emps):
    """Best Wikidata employer for an API affiliation: name similarity plus distance from the API city point."""
    best = None
    an = norm(re.sub(r"\(.*?\)", " ", aff["name"] or ""))
    for name, ept, kind in emps or []:
        en_ = norm(name)
        if aff["pt"]:
            d = km(aff["pt"][0], aff["pt"][1], ept[0], ept[1])
            if d > 60:
                continue
        else:
            d = None
        ratio = SequenceMatcher(None, an, en_).ratio()
        shared = toks(aff["name"]) & toks(name)
        contained = an and (an in en_ or en_ in an)
        if ratio >= .82 or contained or (shared and toks(aff["name"]) <= toks(name) and d is not None and d <= 25):
            score = ratio + (.3 if contained else 0) + .1 * len(shared) - (d or 0) / 600
            if best is None or score > best[0]:
                best = (score, name, ept, kind, d)
    return best


D = jload(f"{WORK}/recs.json")
how_b, how_w, agree_b, agree_w, dist_bw = Counter(), Counter(), Counter(), Counter(), []
for r in D["recs"]:
    # ---- birth ----
    bp = r["bp"]
    r["b_iso"] = iso_name(bp["countryNow"]) if bp["countryNow"] else None
    r["de_then"] = bool(bp["country"] in DE_THEN or (bp["country"] or "").startswith("Germany") or (bp["country"] or "").startswith("Prussia"))
    pt_, how = None, None
    wd = r.get("wd_bp")
    if wd and (not bp["pt"] or km(wd[0], wd[1], bp["pt"][0], bp["pt"][1]) <= 100 or at(*wd) == r["b_iso"]):
        pt_, how = wd, "wikidata"
        if bp["pt"]:
            dist_bw.append(km(wd[0], wd[1], bp["pt"][0], bp["pt"][1]))
    elif bp["pt"]:
        pt_, how = bp["pt"], "api_city"
        if wd:
            how_b["api_city_wikidata_elsewhere"] += 1
    elif ne_city(bp["cityNow"] or bp["city"], r["b_iso"]):
        pt_, how = ne_city(bp["cityNow"] or bp["city"], r["b_iso"]), "ne_city"
    elif r["b_iso"]:
        pt_, how = [meta[r["b_iso"]]["lx"], meta[r["b_iso"]]["ly"]], "country"
    r["b_pt"], r["b_how"] = pt_, how
    how_b[how] += 1
    if pt_ and r["b_iso"] and how != "country":
        agree_b["same" if at(*pt_) == r["b_iso"] else "different"] += 1
    # ---- work ----
    r["w_iso"], r["w_pt"], r["w_how"], r["w_name"], r["w_city"], r["w_emp"] = None, None, None, None, None, None
    if r["aff"]:
        located = [a for a in r["aff"] if a["city"] or a["pt"]] or [a for a in r["aff"] if a["countryNow"]]
        a = located[0] if located else None
        r["n_aff"] = len(r["aff"])
        r["aff_isos"] = sorted({iso_name(x["countryNow"]) for x in r["aff"] if x["countryNow"]})
        if a:
            r["w_iso"] = iso_name(a["countryNow"]); r["w_name"] = a["name"]; r["w_city"] = a["cityNow"] or a["city"]
            m = emp_match(a, r.get("wd_emp"))
            if m:
                r["w_pt"], r["w_how"], r["w_emp"] = m[2], "wikidata_employer", m[1]
            elif a["pt"]:
                r["w_pt"], r["w_how"] = a["pt"], "api_city"
            elif ne_city(a["cityNow"] or a["city"], r["w_iso"]):
                r["w_pt"], r["w_how"] = ne_city(a["cityNow"] or a["city"], r["w_iso"]), "ne_city"
            elif (a["name"] or "").replace("\xad", "") in MANUAL:
                mm = MANUAL[a["name"].replace("\xad", "")]; r["w_pt"], r["w_how"], r["w_city"] = [mm[0], mm[1]], "manual", mm[2]
            elif r["w_iso"]:
                r["w_pt"], r["w_how"] = [meta[r["w_iso"]]["lx"], meta[r["w_iso"]]["ly"]], "country"
            if r["w_pt"] and r["w_iso"] and r["w_how"] != "country":
                agree_w["same" if at(*r["w_pt"]) == r["w_iso"] else "different"] += 1
    elif r["res"]:
        a = r["res"][0]
        r["w_iso"] = iso_name(a["countryNow"]) if a["countryNow"] else {"Yugoslavia": "SRB"}.get(a["country"])
        r["w_city"] = a["cityNow"] or a["city"]
        if a["pt"]:
            r["w_pt"], r["w_how"] = a["pt"], "residence_city"
        elif ne_city(r["w_city"], r["w_iso"]):
            r["w_pt"], r["w_how"] = ne_city(r["w_city"], r["w_iso"]), "residence_city"
        elif r["w_iso"]:
            r["w_pt"], r["w_how"] = [meta[r["w_iso"]]["lx"], meta[r["w_iso"]]["ly"]], "residence_country"
    how_w[r["w_how"]] += 1
    for k in ("b_iso", "w_iso"):
        if r[k] and r[k] not in meta:
            raise KeyError((r["name"], k, r[k]))
dist_bw.sort()
print("birth points", dict(how_b), "point in API country", dict(agree_b), "median km wikidata to API city",
      round(dist_bw[len(dist_bw) // 2], 1) if dist_bw else None)
print("work points", dict(how_w), "point in API country", dict(agree_w))
print("unplaced science affiliations", [(r["name"], r["year"], [a["name"] for a in r["aff"]]) for r in D["recs"] if r["cat"] in SCI and r["aff"] and r["w_how"] in (None, "country")])
print("Wikidata employer matches, sample", [(r["w_name"], r["w_emp"]) for r in D["recs"] if r["w_how"] == "wikidata_employer"][:25])
D["how_b"], D["how_w"], D["agree_b"], D["agree_w"] = dict(how_b), dict(how_w), dict(agree_b), dict(agree_w)
D["bw_km_median"] = round(dist_bw[len(dist_bw) // 2], 1) if dist_bw else None
D["bw_n"] = len(dist_bw)
jsave(D, f"{WORK}/recs_geo.json")
jsave({"meta": meta}, f"{WORK}/geo.json")

cities = []
for f in P:
    p = f["properties"]; pop = p.get("pop_max") or 0
    if pop >= 150000 or p.get("adm0cap") == 1:
        cities.append({"name": re.sub(r"\s+", " ", p["name"]), "lat": round(p["latitude"], 3), "lon": round(p["longitude"], 3), "pop": int(pop)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
print("cities", len(cities), "countries", len(meta), "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB")
