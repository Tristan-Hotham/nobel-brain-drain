"""All analysis: results.json (every number quoted anywhere), the CSV files and the page data.

Definitions
- Record: one prize awarded to a person (organisations excluded). Award decade: 1900s = 1901 to 1909, 2020s = 2020 to 2026.
- Flow analysis: Physics, Chemistry, Physiology or Medicine and Economic Sciences records with both a present-day birth
  country and a primary affiliation country. Born abroad = birth country differs from the affiliation country.
- Net gain of a country = records with an affiliation there minus records of people born there (flow analysis only).
- Germany then: born in a place the Nobel API names as Germany or a German state at the time of birth (Prussia, Bavaria,
  Mecklenburg ...), whatever its present country; used for the Germany section, which also gives present-day figures.
- Institutions: every affiliation listed for a record counts (as on the Wikipedia list); names as the API records them,
  with campuses of the University of California kept apart, the Rockefeller Institute counted as Rockefeller University,
  Bell Telephone Laboratories as Bell Labs and the Harvard laboratories as Harvard University.
"""
import csv
from collections import Counter, defaultdict
from common import *

D = jload(f"{WORK}/recs_geo.json"); G = jload(f"{WORK}/geo.json"); META = G["meta"]
REC = D["recs"]
CN = lambda iso: META[iso]["name"] if iso in META else iso
CONT = lambda iso: META[iso]["cont"] if iso in META else None
dec = lambda y: (y // 10) * 10
pc = lambda a, b: round(100 * a / b, 2) if b else None
for r in REC:
    r["dec"] = dec(r["year"])
    r["flow"] = r["cat"] in SCI and bool(r["aff"]) and bool(r["b_iso"]) and bool(r["w_iso"])
    r.setdefault("n_aff", len(r["aff"])); r.setdefault("aff_isos", [])
    r["abroad"] = r["flow"] and r["b_iso"] != r["w_iso"]
F = [r for r in REC if r["flow"]]
R = {"meta": {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "retrieved": RETRIEVED, "slug": SLUG}}
DECS = list(range(1900, 2030, 10))
sci = [r for r in REC if r["cat"] in SCI]
pl = [r for r in REC if r["cat"] not in SCI]

# ---------- source and placement ----------
s = dict(D["src"])
s.update({"n_flow": len(F), "n_sci": len(sci), "n_pl": len(pl),
          "n_sci_noaff": sum(1 for r in sci if not r["aff"]), "sci_noaff": sorted(f"{r['name']} ({r['cat']}, {r['year']})" for r in sci if not r["aff"]),
          "n_sci_nobirth": sum(1 for r in sci if not r["b_iso"]), "sci_nobirth": sorted(r["name"] for r in sci if not r["b_iso"]),
          "n_people_flow": len({r["id"] for r in F}), "y0": min(r["year"] for r in REC), "y1": max(r["year"] for r in REC),
          "n_women": sum(1 for r in REC if r["sex"] == "female"), "n_multi_prize": len([k for k, v in Counter(r["id"] for r in REC).items() if v > 1]),
          "how_b": D["how_b"], "how_w": D["how_w"], "agree_b": D["agree_b"], "agree_w": D["agree_w"], "bw_km_median": D["bw_km_median"], "bw_n": D["bw_n"]})
s["n_b_wd"] = D["how_b"].get("wikidata", 0); s["n_b_api"] = D["how_b"].get("api_city", 0) + D["how_b"].get("api_city_wikidata_elsewhere", 0)
s["n_b_country"] = D["how_b"].get("country", 0); s["n_b_ne"] = D["how_b"].get("ne_city", 0); s["n_b_none"] = D["how_b"].get("null", 0)
fw = Counter(r["w_how"] for r in F)
s["n_w_emp"], s["n_w_api"], s["n_w_manual"], s["n_w_ne"], s["n_w_country"] = fw["wikidata_employer"], fw["api_city"], fw["manual"], fw["ne_city"], fw["country"]
s["w_emp_pct"] = pc(fw["wikidata_employer"], len(F))
s["n_multi_aff"] = sum(1 for r in F if r["n_aff"] > 1)
s["n_multi_cty"] = sum(1 for r in F if len(r["aff_isos"]) > 1)
s["agree_b_pct"] = pc(D["agree_b"].get("same", 0), sum(D["agree_b"].values()))
s["sci_flow_pct"] = pc(len(F), len(sci))
R["source"] = s

# ---------- born abroad ----------
ab = sum(r["abroad"] for r in F)
by_dec = []
for d in DECS:
    rs = [r for r in F if r["dec"] == d]
    by_dec.append({"dec": d, "n": len(rs), "abroad": sum(r["abroad"] for r in rs), "pct": pc(sum(r["abroad"] for r in rs), len(rs)),
                   "us_n": sum(r["w_iso"] == "USA" for r in rs), "us_abroad": sum(r["w_iso"] == "USA" and r["abroad"] for r in rs)})
    by_dec[-1]["us_pct"] = pc(by_dec[-1]["us_abroad"], by_dec[-1]["us_n"])
    by_dec[-1]["us_share"] = pc(by_dec[-1]["us_n"], len(rs))
by_prize = []
for c in SCI:
    rs = [r for r in F if r["cat"] == c]
    by_prize.append({"cat": c, "short": PSHORT[c], "n": len(rs), "abroad": sum(r["abroad"] for r in rs), "pct": pc(sum(r["abroad"] for r in rs), len(rs))})
pre = [r for r in F if r["year"] < 1940]; post = [r for r in F if r["year"] >= 2000]
R["abroad"] = {"n": len(F), "abroad": ab, "pct": pc(ab, len(F)), "by_dec": by_dec, "by_prize": by_prize,
               "pre1940_pct": pc(sum(r["abroad"] for r in pre), len(pre)), "since2000_pct": pc(sum(r["abroad"] for r in post), len(post)),
               "d1900": by_dec[0], "d2020": by_dec[-1], "d2000": by_dec[10], "d2010": by_dec[11]}
R["abroad"]["max_dec"] = max((b for b in by_dec if b["n"] >= 20), key=lambda b: b["pct"])
R["abroad"]["min_dec"] = min((b for b in by_dec if b["n"] >= 20), key=lambda b: b["pct"])

# ---------- countries: born, worked, net ----------
C = defaultdict(lambda: {"born": 0, "worked": 0, "stayed": 0, "left": 0, "arrived": 0, "dest": Counter(), "orig": Counter(), "women_b": 0, "dec_b": Counter(), "dec_w": Counter()})
for r in F:
    b, w = C[r["b_iso"]], C[r["w_iso"]]
    b["born"] += 1; w["worked"] += 1; b["dec_b"][r["dec"]] += 1; w["dec_w"][r["dec"]] += 1
    if r["abroad"]:
        b["left"] += 1; w["arrived"] += 1; b["dest"][r["w_iso"]] += 1; w["orig"][r["b_iso"]] += 1
    else:
        b["stayed"] += 1
crow = []
for iso, c in C.items():
    crow.append({"iso": iso, "name": CN(iso), "cont": CONT(iso), "born": c["born"], "worked": c["worked"], "stayed": c["stayed"], "left": c["left"],
                 "arrived": c["arrived"], "net": c["worked"] - c["born"], "left_pct": pc(c["left"], c["born"]),
                 "arrived_pct": pc(c["arrived"], c["worked"]), "top_dest": [[CN(k), v, k] for k, v in c["dest"].most_common(4)],
                 "top_orig": [[CN(k), v, k] for k, v in c["orig"].most_common(5)],
                 "dec_b": {str(k): v for k, v in sorted(c["dec_b"].items())}, "dec_w": {str(k): v for k, v in sorted(c["dec_w"].items())}})
crow.sort(key=lambda c: (-c["net"], c["name"]))
CI = {c["iso"]: c for c in crow}
gain = [c for c in crow if c["net"] > 0]
loss = sorted([c for c in crow if c["net"] < 0], key=lambda c: (c["net"], c["name"]))
R["countries"] = {"n_born": len([c for c in crow if c["born"]]), "n_worked": len([c for c in crow if c["worked"]]), "gain": gain[:12], "loss": loss[:15],
                  "n_gain": len(gain), "n_loss": len(loss), "n_even": len([c for c in crow if c["net"] == 0]),
                  "top_born": sorted(crow, key=lambda c: -c["born"])[:15], "top_worked": sorted(crow, key=lambda c: -c["worked"])[:15]}
for iso, k in (("USA", "usa"), ("GBR", "gbr"), ("DEU", "deu"), ("JPN", "jpn"), ("CHE", "che"), ("FRA", "fra"), ("POL", "pol"), ("AUT", "aut"),
               ("HUN", "hun"), ("CAN", "can"), ("RUS", "rus"), ("SWE", "swe"), ("DNK", "dnk"), ("CHN", "chn"), ("ISR", "isr"), ("IND", "ind"), ("NLD", "nld")):
    R["countries"][k] = CI.get(iso, {"iso": iso, "name": CN(iso), "born": 0, "worked": 0, "net": 0, "left": 0, "arrived": 0})
R["countries"]["pol_de_then"] = sum(1 for r in F if r["b_iso"] == "POL" and r["de_then"])
R["countries"]["pol_de_then_to_de"] = sum(1 for r in F if r["b_iso"] == "POL" and r["de_then"] and r["w_iso"] == "DEU")
top_w = []
for d in DECS:
    cc = Counter(r["w_iso"] for r in F if r["dec"] == d).most_common(2)
    top_w.append({"dec": d, "iso": cc[0][0], "name": CN(cc[0][0]), "n": cc[0][1], "second": CN(cc[1][0]), "second_n": cc[1][1]})
R["countries"]["top_work_by_dec"] = top_w
pairs = Counter((r["b_iso"], r["w_iso"]) for r in F if r["abroad"])
R["flows"] = {"n_pairs": len(pairs), "top": [{"from": a, "to": b, "from_name": CN(a), "to_name": CN(b), "n": n} for (a, b), n in pairs.most_common(25)]}
R["flows"]["to_us"] = sum(n for (a, b), n in pairs.items() if b == "USA")
R["flows"]["to_us_pct"] = pc(R["flows"]["to_us"], ab)
R["flows"]["from_us"] = sum(n for (a, b), n in pairs.items() if a == "USA")

# ---------- the United States ----------
us = [r for r in F if r["w_iso"] == "USA"]
usd = [b for b in by_dec if b["us_n"]]
R["us"] = {"n": len(us), "abroad": sum(r["abroad"] for r in us), "pct": pc(sum(r["abroad"] for r in us), len(us)),
           "share": pc(len(us), len(F)), "born": CI["USA"]["born"], "net": CI["USA"]["net"],
           "first_dec_lead": next(t["dec"] for t in top_w if t["iso"] == "USA"),
           "orig": CI["USA"]["top_orig"], "n_orig": len(C["USA"]["orig"]),
           "pre1940_share": pc(sum(r["w_iso"] == "USA" for r in pre), len(pre)), "since2000_share": pc(sum(r["w_iso"] == "USA" for r in post), len(post)),
           "since1950_share": pc(sum(r["w_iso"] == "USA" for r in F if r["year"] >= 1950), sum(1 for r in F if r["year"] >= 1950)),
           "since1950_abroad_pct": pc(sum(r["abroad"] for r in us if r["year"] >= 1950), sum(1 for r in us if r["year"] >= 1950)),
           "d2020": by_dec[-1], "d2010": by_dec[-2], "d1950": by_dec[5], "d1930": by_dec[3]}
R["us"]["share_imports"] = pc(R["flows"]["to_us"], ab)

# ---------- Germany ----------
de = [r for r in F if r["de_then"]]
COH = [(0, 1879, "born before 1880"), (1880, 1909, "born 1880 to 1909"), (1910, 1929, "born 1910 to 1929"), (1930, 2100, "born 1930 or later")]
coh = []
for a, b, lab in COH:
    rs = [r for r in de if r["by"] and a <= r["by"] <= b]
    coh.append({"lab": lab, "n": len(rs), "abroad": sum(r["w_iso"] != "DEU" for r in rs), "pct": pc(sum(r["w_iso"] != "DEU" for r in rs), len(rs)),
                "us": sum(r["w_iso"] == "USA" for r in rs), "gbr": sum(r["w_iso"] == "GBR" for r in rs)})
exiles = [r for r in de if r["by"] and 1880 <= r["by"] <= 1929 and r["w_iso"] != "DEU"]
de_dec = []
for d in DECS:
    rs = [r for r in F if r["dec"] == d]
    de_dec.append({"dec": d, "n": len(rs), "born_de": sum(r["de_then"] for r in rs), "born_de_home": sum(r["de_then"] and r["w_iso"] == "DEU" for r in rs),
                   "born_de_abroad": sum(r["de_then"] and r["w_iso"] != "DEU" for r in rs), "work_de": sum(r["w_iso"] == "DEU" for r in rs),
                   "work_de_pct": pc(sum(r["w_iso"] == "DEU" for r in rs), len(rs))})
p1 = [r for r in F if r["year"] <= 1932]; p2 = [r for r in F if 1933 <= r["year"]]
dep = [r for r in de if r["year"] <= 1932]; dlt = [r for r in de if r["year"] >= 1933]
R["germany"] = {"n_then": len(de), "n_now": CI["DEU"]["born"], "abroad_then": sum(r["w_iso"] != "DEU" for r in de),
                "abroad_then_pct": pc(sum(r["w_iso"] != "DEU" for r in de), len(de)), "cohorts": coh, "by_dec": de_dec,
                "early_abroad_pct": pc(sum(r["w_iso"] != "DEU" for r in dep), len(dep)), "early_n": len(dep),
                "late_abroad_pct": pc(sum(r["w_iso"] != "DEU" for r in dlt), len(dlt)), "late_n": len(dlt),
                "work_share_to1932": pc(sum(r["w_iso"] == "DEU" for r in p1), len(p1)), "work_share_since1933": pc(sum(r["w_iso"] == "DEU" for r in p2), len(p2)),
                "work_to1932": sum(r["w_iso"] == "DEU" for r in p1), "n_to1932": len(p1),
                "exiles_n": len(exiles), "exiles_us": sum(r["w_iso"] == "USA" for r in exiles), "exiles_gbr": sum(r["w_iso"] == "GBR" for r in exiles),
                "exiles": [{"n": r["name"], "by": r["by"], "y": r["year"], "cat": PSHORT[r["cat"]], "to": CN(r["w_iso"]), "aff": r["w_name"], "bp": r["bp"]["city"]} for r in sorted(exiles, key=lambda r: r["year"])],
                "net_now": CI["DEU"]["net"]}
R["germany"]["work_share_d1900"] = de_dec[0]["work_de_pct"]; R["germany"]["work_share_d1910"] = de_dec[1]["work_de_pct"]
R["germany"]["work_share_d1920"] = de_dec[2]["work_de_pct"]; R["germany"]["work_share_d1950"] = de_dec[5]["work_de_pct"]
R["germany"]["prewar_home_n"] = sum(r["w_iso"] == "DEU" for r in de if r["year"] <= 1939)
R["germany"]["prewar_n"] = sum(1 for r in de if r["year"] <= 1939)
for nm in ("Hans Bethe", "Max Born", "Otto Stern", "Hans Krebs", "Arno Penzias", "Jack Steinberger", "Ernst Boris Chain", "Max Delbrück", "Bernard Katz", "Herbert Kroemer", "Gerhard Herzberg"):
    R["germany"].setdefault("named", {})[nm] = next(({"y": r["year"], "to": CN(r["w_iso"]), "aff": r["w_name"], "by": r["by"], "bp": r["bp"]["city"], "abroad": r["w_iso"] != "DEU", "then": r["de_then"]} for r in F if r["name"] == nm), None)
# Austria and Hungary as the other great losers of the period
for iso, k in (("AUT", "austria"), ("HUN", "hungary")):
    rs = [r for r in F if r["b_iso"] == iso]
    R["germany"][k] = {"n": len(rs), "abroad": sum(r["abroad"] for r in rs), "pct": pc(sum(r["abroad"] for r in rs), len(rs))}

# ---------- Japan ----------
jp = [r for r in F if r["b_iso"] == "JPN"]
jdec = [{"dec": d, "born": sum(r["dec"] == d for r in jp), "worked": sum(r["dec"] == d and r["w_iso"] == "JPN" for r in F),
         "share": pc(sum(r["dec"] == d for r in jp), sum(1 for r in F if r["dec"] == d))} for d in DECS]
jabroad = [r for r in jp if r["abroad"]]
since00 = [r for r in F if r["year"] >= 2000]
rank00 = Counter(r["b_iso"] for r in since00).most_common()
rank00w = Counter(r["w_iso"] for r in since00).most_common()
jp_all = [r for r in REC if r["b_iso"] == "JPN"]
R["japan"] = {"n": len(jp), "n_all": len(jp_all), "first": min(r["year"] for r in jp), "first_name": min(jp, key=lambda r: r["year"])["name"],
              "before2000": sum(r["year"] < 2000 for r in jp), "since2000": sum(r["year"] >= 2000 for r in jp), "by_dec": jdec,
              "abroad": [{"n": r["name"], "y": r["year"], "to": CN(r["w_iso"]), "aff": r["w_name"], "cat": PSHORT[r["cat"]]} for r in sorted(jabroad, key=lambda r: r["year"])],
              "n_abroad": len(jabroad), "abroad_pct": pc(len(jabroad), len(jp)), "net": CI["JPN"]["net"],
              "rank_since2000_born": [i for i, _ in rank00].index("JPN") + 1, "since2000_share": pc(sum(r["b_iso"] == "JPN" for r in since00), len(since00)),
              "since2000_top_born": [{"iso": i, "name": CN(i), "n": n} for i, n in rank00[:6]], "since2000_top_worked": [{"iso": i, "name": CN(i), "n": n} for i, n in rank00w[:6]],
              "pre2000_share": pc(sum(r["b_iso"] == "JPN" for r in F if r["year"] < 2000), sum(1 for r in F if r["year"] < 2000)),
              "d2000": jdec[10], "d2010": jdec[11], "d2020": jdec[12]}
R["japan"]["rank_since2000_worked"] = [i for i, _ in rank00w].index("JPN") + 1

# ---------- institutions ----------
def ikey(a):
    n = (a["name"] or "").replace("&eacute;", "é").replace("\xad", "")
    if n.startswith("University of California"):
        city = (a["city"] or "").split(",")[0]
        return f"University of California, {city}" if city else n
    if n.startswith("Rockefeller Institute"): return "Rockefeller University"
    if n.startswith("Bell ") or n.startswith("AT&T Bell"): return "Bell Labs"
    if n.startswith("Harvard University,"): return "Harvard University"
    return re.sub(r"\s*\((MIT|Caltech)\)", "", n)


I = defaultdict(lambda: {"n": 0, "city": None, "pt": None, "cats": Counter(), "dec": Counter(), "people": []})
MPG = {"n": 0}
for r in REC:
    if not r["aff"]:
        continue
    seen = set()
    for a in r["aff"]:
        k = ikey(a)
        if k in seen or not k:
            continue
        seen.add(k)
        i = I[k]; i["n"] += 1; i["cats"][PSHORT[r["cat"]]] += 1; i["dec"][r["dec"]] += 1
        i["city"] = i["city"] or a["cityNow"] or a["city"]
        if a["countryNow"]:
            i["cn"] = a["countryNow"]
        if r["w_name"] == a["name"] and r["w_pt"] and not i["pt"]:
            i["pt"] = r["w_pt"]
        i["people"].append([r["name"], r["year"], PSHORT[r["cat"]], r["b_iso"]])
    if any("Max-Planck" in (a["name"] or "") or "Max Planck" in (a["name"] or "") or "Kaiser-Wilhelm" in (a["name"] or "") for a in r["aff"]):
        MPG["n"] += 1
inst = []
for k, i in I.items():
    inst.append({"name": k, "n": i["n"], "city": dash(i["city"] or ""), "country": i.get("cn"), "pt": i["pt"], "cats": dict(i["cats"]),
                 "people": sorted(i["people"], key=lambda p: p[1])})
inst.sort(key=lambda x: (-x["n"], x["name"]))
# born abroad among each institution's laureates: birth country v the institution's present-day country
NAME2ISO = {}
for r in REC:
    for a in r["aff"]:
        if a["countryNow"] and r["w_name"] == a["name"] and r["w_iso"]:
            NAME2ISO[a["countryNow"]] = r["w_iso"]
for x in inst:
    ciso = NAME2ISO.get(x["country"])
    x["iso"] = ciso
    x["born_abroad"] = sum(1 for p in x["people"] if p[3] and ciso and p[3] != ciso)
    x["born_abroad_pct"] = pc(x["born_abroad"], sum(1 for p in x["people"] if p[3]))
top = inst[:25]
us_top = [x for x in inst[:20] if x["iso"] == "USA"]
R["institutions"] = {"n": len(inst), "top": [{k: v for k, v in x.items() if k != "people"} for x in top], "mpg": MPG["n"],
                     "top10_us": sum(1 for x in inst[:10] if x["iso"] == "USA"), "top20_us": len(us_top),
                     "top10_n": sum(x["n"] for x in inst[:10])}
# Wikipedia cross-check
wk = jload(f"{RAW}/wiki_List_of_Nobel_laureates_by_university_affiliation.json")["html"]
tab = wk[wk.find("<table"):wk.find("</table>")]
WP = []
for tr in re.findall(r"<tr>(.*?)</tr>", tab, re.S):
    cells = [re.sub(r"<[^>]+>|&#91;.*?&#93;", "", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
    if len(cells) >= 2 and cells[1].isdigit():
        WP.append((cells[0], int(cells[1])))
WPN = {"Massachusetts Institute of Technology": "Massachusetts Institute of Technology", "California Institute of Technology": "California Institute of Technology",
       "Heidelberg University": "University of Heidelberg", "Pasteur Institute": "Institut Pasteur", "Lebedev Physical Institute": "P.N. Lebedev Physical Institute"}
IN = {x["name"]: x["n"] for x in inst}
cmp_ = []
for nm, n in WP[:20]:
    mine = IN.get(WPN.get(nm, nm))
    cmp_.append({"wiki": nm, "wiki_n": n, "mine": mine})
R["institutions"]["wiki"] = cmp_
R["institutions"]["wiki_n"] = len(cmp_)
R["institutions"]["wiki_same"] = sum(1 for c in cmp_ if c["mine"] == c["wiki_n"])
R["institutions"]["wiki_revid"] = jload(f"{RAW}/wiki_List_of_Nobel_laureates_by_university_affiliation.json")["revid"]

# ---------- women ----------
wd = []
for d in DECS:
    rs = [r for r in REC if r["dec"] == d]
    wd.append({"dec": d, "n": len(rs), "w": sum(r["sex"] == "female" for r in rs), "pct": pc(sum(r["sex"] == "female" for r in rs), len(rs)),
               "sci_n": sum(r["cat"] in SCI for r in rs), "sci_w": sum(r["cat"] in SCI and r["sex"] == "female" for r in rs),
               "pl_n": sum(r["cat"] not in SCI for r in rs), "pl_w": sum(r["cat"] not in SCI and r["sex"] == "female" for r in rs)})
    wd[-1]["sci_pct"] = pc(wd[-1]["sci_w"], wd[-1]["sci_n"]); wd[-1]["pl_pct"] = pc(wd[-1]["pl_w"], wd[-1]["pl_n"])
wcat = [{"cat": c, "short": PSHORT[c], "n": sum(r["cat"] == c for r in REC), "w": sum(r["cat"] == c and r["sex"] == "female" for r in REC)} for c in PRIZES]
for x in wcat:
    x["pct"] = pc(x["w"], x["n"])
    firsts = sorted([r for r in REC if r["cat"] == x["cat"] and r["sex"] == "female"], key=lambda r: r["year"])
    x["first"] = firsts[0]["name"] if firsts else None; x["first_y"] = firsts[0]["year"] if firsts else None
wf = [r for r in F if r["sex"] == "female"]; mf = [r for r in F if r["sex"] == "male"]
R["women"] = {"n": s["n_women"], "pct": pc(s["n_women"], len(REC)), "by_dec": wd, "by_cat": wcat,
              "d1900": wd[0], "d2000": wd[10], "d2010": wd[11], "d2020": wd[12],
              "before1960": sum(r["sex"] == "female" for r in REC if r["year"] < 1960), "before1960_n": sum(1 for r in REC if r["year"] < 1960),
              "since2000": sum(r["sex"] == "female" for r in REC if r["year"] >= 2000), "since2000_n": sum(1 for r in REC if r["year"] >= 2000),
              "sci_since2000_pct": pc(sum(r["sex"] == "female" for r in sci if r["year"] >= 2000), sum(1 for r in sci if r["year"] >= 2000)),
              "sci_before2000_pct": pc(sum(r["sex"] == "female" for r in sci if r["year"] < 2000), sum(1 for r in sci if r["year"] < 2000)),
              "flow_w_abroad_pct": pc(sum(r["abroad"] for r in wf), len(wf)), "flow_m_abroad_pct": pc(sum(r["abroad"] for r in mf), len(mf)), "flow_w_n": len(wf)}
R["women"]["since2000_pct"] = pc(R["women"]["since2000"], R["women"]["since2000_n"])
R["women"]["before1960_pct"] = pc(R["women"]["before1960"], R["women"]["before1960_n"])

# ---------- Peace and Literature by residence ----------
plr = [r for r in pl if r["b_iso"] and r["w_iso"]]
R["peace_lit"] = {"n": len(pl), "placed": len(plr), "abroad": sum(r["b_iso"] != r["w_iso"] for r in plr), "pct": pc(sum(r["b_iso"] != r["w_iso"] for r in plr), len(plr)),
                  "no_res": len(pl) - len(plr), "with_aff": sum(1 for r in pl if r["aff"]),
                  "lit": pc(sum(r["b_iso"] != r["w_iso"] for r in plr if r["cat"] == "Literature"), sum(1 for r in plr if r["cat"] == "Literature")),
                  "pea": pc(sum(r["b_iso"] != r["w_iso"] for r in plr if r["cat"] == "Peace"), sum(1 for r in plr if r["cat"] == "Peace")),
                  "top": [{"from": CN(a), "to": CN(b), "n": n} for (a, b), n in Counter((r["b_iso"], r["w_iso"]) for r in plr if r["b_iso"] != r["w_iso"]).most_common(6)]}

# ---------- facts for named people (checked in the build scripts) ----------
def who(nm, cat=None):
    rs = [r for r in REC if r["name"] == nm and (cat is None or r["cat"] == cat)]
    if not rs:
        raise KeyError(nm)
    r = rs[0]
    return {"y": r["year"], "cat": PSHORT[r["cat"]], "b": CN(r["b_iso"]) if r["b_iso"] else None, "w": CN(r["w_iso"]) if r["w_iso"] else None,
            "bp": r["bp"]["city"], "aff": r["w_name"], "b_iso": r["b_iso"], "w_iso": r["w_iso"]}
R["people"] = {nm: who(nm) for nm in ("Albert Einstein", "Marie Curie", "Hideki Yukawa", "Yoichiro Nambu", "Shuji Nakamura", "Syukuro Manabe",
                                         "Abdus Salam", "Wilhelm Conrad Röntgen", "Fritz Haber", "Enrico Fermi", "Kazuo Ishiguro", "Har Gobind Khorana",
                                         "Subramanyan Chandrasekhar", "Ardem Patapoutian", "Abhijit Banerjee", "Demis Hassabis", "John Macleod", "Jack Kilby")
               if any(r["name"] == nm for r in REC)}
R["people"]["Marie Curie 1911"] = who("Marie Curie", "Chemistry")

# ---------- tables for the page and data files ----------
R["decades"] = {"rows": [{"dec": d, "n_all": sum(r["dec"] == d for r in REC), "n_flow": sum(r["dec"] == d for r in F)} for d in DECS]}
jsave(R, f"{DATA}/results.json", indent=1)

HOWB = {"wikidata": "wikidata", "api_city": "api_city", "api_city_wikidata_elsewhere": "api_city", "ne_city": "natural_earth_city", "country": "country_label_point"}
HOWW = {"wikidata_employer": "wikidata_employer", "api_city": "api_city", "ne_city": "natural_earth_city", "manual": "manual", "country": "country_label_point",
        "residence_city": "residence_city", "residence_country": "residence_country_label_point"}
with open(f"{DATA}/laureates.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nobel_id", "wikidata", "name", "sex", "birth_year", "prize", "year", "portion", "birth_place", "birth_country_then", "birth_country_now",
                "birth_iso3", "birth_lon", "birth_lat", "birth_method", "affiliation", "affiliation_city", "work_country", "work_iso3", "work_lon", "work_lat",
                "work_method", "wikidata_employer_used", "n_affiliations", "affiliation_countries", "residence_country", "in_flow_analysis", "born_abroad",
                "wikidata_match", "nobel_url"])
    for r in sorted(REC, key=lambda r: (r["year"], PRIZES.index(r["cat"]), r["name"])):
        w.writerow([r["id"], r["q"], r["name"], r["sex"], r["by"], r["cat"], r["year"], r["portion"], dash(r["bp"]["city"] or ""), dash(r["bp"]["country"] or ""),
                    dash(r["bp"]["countryNow"] or ""), r["b_iso"] or "", *(r["b_pt"] or ["", ""]), HOWB.get(r["b_how"], ""),
                    dash(r["w_name"] or "") if r["cat"] in SCI or r["aff"] else "", dash(r["w_city"] or ""), CN(r["w_iso"]) if r["w_iso"] else "", r["w_iso"] or "",
                    *(r["w_pt"] or ["", ""]), HOWW.get(r["w_how"], ""), dash(r["w_emp"] or ""), len(r["aff"]), ";".join(r.get("aff_isos", [])),
                    dash(r["res"][0]["countryNow"] or r["res"][0]["country"] or "") if r["res"] else "", int(r["flow"]), int(r["abroad"]), r.get("wd_match", ""), r["url"]])
with open(f"{DATA}/countries.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["iso3", "country", "continent", "born_there", "affiliated_there", "net_gain", "stayed", "left", "arrived", "left_pct", "arrived_pct", "top_destinations", "top_origins"])
    for c in sorted(crow, key=lambda c: (-c["net"], c["name"])):
        w.writerow([c["iso"], c["name"], c["cont"], c["born"], c["worked"], c["net"], c["stayed"], c["left"], c["arrived"], c["left_pct"] if c["left_pct"] is not None else "",
                    c["arrived_pct"] if c["arrived_pct"] is not None else "", "; ".join(f"{a} {b}" for a, b, _ in c["top_dest"]), "; ".join(f"{a} {b}" for a, b, _ in c["top_orig"])])
with open(f"{DATA}/flows.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["birth_iso3", "birth_country", "work_iso3", "work_country", "prizes"])
    for (a, b), n in pairs.most_common():
        w.writerow([a, CN(a), b, CN(b), n])
with open(f"{DATA}/institutions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["institution", "city", "country", "prizes", "physics", "chemistry", "medicine", "economics", "born_in_another_country", "laureates"])
    for x in inst:
        w.writerow([x["name"], x["city"], x["country"] or "", x["n"], *[x["cats"].get(k, 0) for k in ("Physics", "Chemistry", "Medicine", "Economics")], x["born_abroad"],
                    "; ".join(f"{p[0]} ({p[2]} {p[1]})" for p in x["people"])])
with open(f"{DATA}/decades.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["decade", "prizes_to_people", "women", "women_pct", "flow_records", "born_abroad", "born_abroad_pct", "affiliated_in_us", "us_born_abroad", "us_born_abroad_pct"])
    for a, b in zip(wd, by_dec):
        w.writerow([a["dec"], a["n"], a["w"], a["pct"], b["n"], b["abroad"], b["pct"], b["us_n"], b["us_abroad"], b["us_pct"] if b["us_pct"] is not None else ""])

# ---------- page data ----------
CAT_I = {c: i for i, c in enumerate(PRIZES)}
rows = []
for r in sorted(REC, key=lambda r: (r["year"], CAT_I[r["cat"]])):
    if not r["b_pt"] and not r["w_pt"]:
        continue
    rows.append([r["id"], r["name"], CAT_I[r["cat"]], r["year"], 1 if r["sex"] == "female" else 0, r["by"] or 0,
                 [round(v, 3) for v in r["b_pt"]] if r["b_pt"] else None, r["b_iso"] or "", dash(r["bp"]["city"] or ""),
                 [round(v, 3) for v in r["w_pt"]] if r["w_pt"] else None, r["w_iso"] or "", dash(r["w_name"] or ""), dash(r["w_city"] or ""),
                 {"wikidata": 0, "api_city": 1, "api_city_wikidata_elsewhere": 1, "ne_city": 2, "country": 3}.get(r["b_how"], 4),
                 {"wikidata_employer": 0, "api_city": 1, "ne_city": 2, "manual": 2, "country": 3, "residence_city": 5, "residence_country": 6}.get(r["w_how"], 4),
                 1 if r["flow"] else 0, r["q"] or "", r["url"].replace("https://www.nobelprize.org/prizes/", ""), dash(r["bp"]["country"] or "")])
jsave({"cols": ["id", "name", "prize", "year", "woman", "birth_year", "birth_pt", "birth_iso", "birth_place", "work_pt", "work_iso", "affiliation", "work_city",
                "birth_method", "work_method", "in_flow", "wikidata", "nobel_path", "birth_country_then"], "prizes": PRIZES, "rows": rows}, f"{DATA}/points.json")
site = {"cname": {iso: m["name"] for iso, m in META.items()}, "cont": {iso: m["cont"] for iso, m in META.items()},
        "cpos": {iso: [m["lx"], m["ly"], m["pop"]] for iso, m in META.items()},
        "c": {c["iso"]: {k: c[k] for k in ("born", "worked", "net", "stayed", "left", "arrived", "top_dest", "top_orig")} for c in crow},
        "inst": [{k: x[k] for k in ("name", "n", "city", "pt", "iso", "born_abroad")} for x in inst if x["pt"] and x["n"] >= 2]}
jsave(site, f"{DATA}/site.json")
print("flow", len(F), "abroad", R["abroad"]["pct"], "US", R["us"]["n"], R["us"]["pct"], "net", R["us"]["net"])
print("gain", [(c["name"], c["net"]) for c in gain[:8]]); print("loss", [(c["name"], c["net"]) for c in loss[:12]])
print("by dec", [(b["dec"], b["n"], b["pct"], b["us_pct"]) for b in by_dec])
print("germany", {k: v for k, v in R["germany"].items() if k not in ("exiles", "by_dec", "named")}); print([ (e["n"], e["y"], e["to"]) for e in R["germany"]["exiles"]])
print("japan", {k: v for k, v in R["japan"].items() if k not in ("by_dec",)})
print("inst", [(x["name"], x["n"], x["iso"], x["born_abroad"]) for x in top[:15]], "MPG", MPG["n"], "wiki", R["institutions"]["wiki_same"], cmp_)
print("women", [(x["dec"], x["pct"]) for x in wd], wcat)
print("peace/lit", R["peace_lit"])
print("flows", R["flows"]["top"][:10])
