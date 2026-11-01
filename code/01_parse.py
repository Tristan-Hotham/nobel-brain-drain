"""Parse the Nobel Prize API and the Wikidata query result, and match people across them.

Rules
- One record per prize awarded to a person (so Marie Curie, John Bardeen, Frederick Sanger, Linus Pauling and Karl Barry
  Sharpless each count once per prize). Organisations (Peace) have no birthplace and are left out, but counted.
- Names, prizes, years, sex, birthplaces as named and affiliations at the time of the award come from the Nobel API,
  which is authoritative for them.
- Wikidata rows (Physics, Chemistry and Physiology or Medicine only) are grouped per person. A Wikidata person matches an
  API laureate when the API's Wikidata ID is the same AND the prize category and award year agree; as a check, the same
  pairs are also matched by normalised name, year and prize, and the two matchings are compared.
- Wikidata supplies coordinates: the birthplace point (P19 coordinates) and the points of each employer (P108; its own
  coordinates, else its headquarters). Employers are matched to API affiliations by name in 02_geo.py.
"""
import csv, sys
from collections import defaultdict, Counter
from common import *

csv.field_size_limit(sys.maxsize)
POINT = re.compile(r"POINT\(([-\d.eE+]+) ([-\d.eE+]+)\)")
CAT_WD = {"Nobel Prize in Physics": "Physics", "Nobel Prize in Chemistry": "Chemistry", "Nobel Prize in Physiology or Medicine": "Physiology or Medicine"}


def en(d, k):
    v = (d or {}).get(k) or {}
    return v.get("en") if isinstance(v, dict) else None


def ll(d):
    c = (d or {}).get("cityNow") or {}
    if "latitude" in c and "longitude" in c:
        return [round(float(c["longitude"]), 5), round(float(c["latitude"]), 5)]
    return None


def place(d):
    """A place block from the API: city and country as named then and now, and the present-day city point."""
    d = d or {}
    return {"city": en(d, "city"), "country": en(d, "country"), "cityNow": en(d, "cityNow"), "countryNow": en(d, "countryNow"),
            "cont": en(d, "continent"), "pt": ll(d)}


API = jload(f"{RAW}/nobel_api_laureates.json")
recs, n_org, n_org_prizes = [], 0, 0
for x in API:
    if "orgName" in x:
        n_org += 1; n_org_prizes += len(x["nobelPrizes"]); continue
    b = x.get("birth") or {}
    bp = place(b.get("place"))
    q = (x.get("wikidata") or {}).get("id")
    for p in x["nobelPrizes"]:
        cat = p["category"]["en"]
        recs.append({
            "id": x["id"], "q": q, "name": en(x, "knownName") or en(x, "fullName"), "full": en(x, "fullName"),
            "sex": x.get("gender"), "born": b.get("date"), "by": int(b["year"]) if b.get("year") else None,
            "bp": bp, "year": int(p["awardYear"]), "cat": cat, "portion": p.get("portion"), "status": p.get("prizeStatus"),
            "motivation": (p.get("motivation") or {}).get("en", ""),
            "aff": [dict(place(a), name=en(a, "name"), nameNow=en(a, "nameNow")) for a in p.get("affiliations", [])],
            "res": [place(a) for a in p.get("residences", [])],
            "url": next((l["href"] for l in p.get("links", []) if "laureate facts" in (l.get("class") or [])), ""),
        })
print("API laureates", len(API), "organisations", n_org, "with", n_org_prizes, "prizes; person-prize records", len(recs))

# ---------- Wikidata ----------
rows = list(csv.reader(open(f"{RAW}/wikidata_nobel.tsv", encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
head = [h.lstrip("?") for h in rows[0]]


def val(v):
    v = (v or "").strip()
    if v.startswith("<" + WD):
        return v[len(WD) + 1:-1]
    m = re.match(r'^"(.*)"(@[\w-]+|\^\^<[^>]+>)?$', v, re.S)
    return m.group(1).replace('\\"', '"') if m else v


def pt(v):
    m = POINT.search(v or "")
    return [round(float(m.group(1)), 5), round(float(m.group(2)), 5)] if m else None


W = {}
for r in rows[1:]:
    r = dict(zip(head, [val(c) for c in r + [""] * (len(head) - len(r))]))
    w = W.setdefault(r["p"], {"q": r["p"], "name": r["pL"], "prizes": set(), "bp": Counter(), "bpL": {}, "emp": {}})
    cat = CAT_WD.get(r["prizeL"])
    yr = int(r["year"][:4]) if re.match(r"^\d{4}", r["year"] or "") else None
    if cat and yr:
        w["prizes"].add((cat, yr))
    b = pt(r["bpCoord"])
    if b:
        w["bp"][tuple(b)] += 1; w["bpL"][tuple(b)] = r["bpL"]
    if r["empL"]:
        e = pt(r["empCoord"]) or pt(r["empHQCoord"])
        if e and r["empL"] not in w["emp"]:
            w["emp"][r["empL"]] = (e, "own" if pt(r["empCoord"]) else "hq")
print("Wikidata rows", len(rows) - 1, "people", len(W), "people with a birthplace point", sum(1 for w in W.values() if w["bp"]),
      "with an employer point", sum(1 for w in W.values() if w["emp"]))

# ---------- match ----------
byq = {}
by_name = defaultdict(list)
for w in W.values():
    for c, y in w["prizes"]:
        by_name[(norm(w["name"]), c, y)].append(w["q"])
m_q = m_name = m_both = 0
mismatch = []
for r in recs:
    w = W.get(r["q"])
    ok_q = bool(w and (r["cat"], r["year"]) in w["prizes"])
    nm = by_name.get((norm(r["name"]), r["cat"], r["year"]), []) + by_name.get((norm(r["full"] or ""), r["cat"], r["year"]), [])
    ok_n = bool(nm)
    if ok_q:
        m_q += 1
    if ok_n:
        m_name += 1
    if ok_q and ok_n:
        m_both += 1
    if ok_n and not ok_q:
        mismatch.append((r["name"], r["year"], r["cat"], r["q"], nm))
    if not ok_q and ok_n and len(set(nm)) == 1:
        w = W[nm[0]]; ok_q = True       # name, year and prize agree but the IDs differ: accept and record
        r["wd_match"] = "name"
    elif ok_q:
        r["wd_match"] = "id" + ("+name" if ok_n else "")
    else:
        r["wd_match"] = ""
    if ok_q:
        r["wd_q"] = w["q"]
        r["wd_bp"] = list(w["bp"].most_common(1)[0][0]) if w["bp"] else None
        r["wd_bpL"] = w["bpL"].get(tuple(r["wd_bp"])) if r["wd_bp"] else None
        r["wd_nbp"] = len(w["bp"])
        r["wd_emp"] = [[k, v[0], v[1]] for k, v in w["emp"].items()]
sci3 = [r for r in recs if r["cat"] in CAT_WD.values()]
unmatched_w = set(W) - {r.get("wd_q") for r in recs}
print("science-3 records", len(sci3), "matched by ID+prize+year", m_q, "by name+prize+year", m_name, "both", m_both,
      "name-only matches", mismatch[:5], "Wikidata people unmatched", len(unmatched_w), [W[q]["name"] for q in list(unmatched_w)[:8]])
src = {"n_api": len(API), "n_org": n_org, "n_org_prizes": n_org_prizes, "n_recs": len(recs), "n_people": len({r["id"] for r in recs}),
       "n_wd_rows": len(rows) - 1, "n_wd_people": len(W), "n_sci3": len(sci3), "n_match_id": m_q, "n_match_name": m_name,
       "n_match_both": m_both, "n_match_any": sum(1 for r in recs if r["wd_match"]), "n_wd_unmatched": len(unmatched_w),
       "wd_unmatched": sorted(W[q]["name"] for q in unmatched_w)}
jsave({"src": src, "recs": recs}, f"{WORK}/recs.json")
