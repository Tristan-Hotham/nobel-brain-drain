"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded; data/points.json is loaded by the
page. Facts stated in words (page, blog, paper, collage) are checked here. The full-screen map snippet
(code/fullscreen_snippet.html) is pasted before </body>."""
import csv
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
L = {(r["name"], int(r["year"]), r["prize"]): r for r in csv.DictReader(open(f"{DATA}/laureates.csv", encoding="utf-8"))}
byname = {}
for r in L.values():
    byname.setdefault(r["name"], r)

# ---------- facts stated in words ----------
c, us, de, jp, ab, w, inst = R["countries"], R["us"], R["germany"], R["japan"], R["abroad"], R["women"], R["institutions"]
assert [x["iso"] for x in c["gain"]] == ["USA", "CHE", "GBR", "DNK", "SWE"] and c["n_gain"] == 5 and c["dnk"]["net"] == 1 and c["swe"]["net"] == 1
assert c["loss"][0]["iso"] == "POL" and c["pol"]["worked"] == 0 and c["pol_de_then"] > c["pol"]["born"] / 2
assert {x["iso"] for x in c["loss"][:10]} >= {"CAN", "AUT", "HUN", "NLD", "RUS", "CHN", "JPN"}
assert c["can"]["top_dest"][0][2] == "USA" and c["can"]["top_dest"][0][1] == c["can"]["left"]
assert c["chn"]["worked"] <= 1 and c["ind"]["worked"] <= 1 and c["chn"]["born"] >= 6 and c["ind"]["born"] >= 5     # 'lost almost all'
assert de["hungary"]["abroad"] / de["hungary"]["n"] >= .75 and de["austria"]["abroad"] / de["austria"]["n"] >= .6
tw = c["top_work_by_dec"]
assert all(t["iso"] == "DEU" for t in tw[:4]) and all(t["iso"] == "USA" for t in tw[4:])        # 'Germany led the first four decades', 'US every decade since the 1940s'
assert us["first_dec_lead"] == 1940 and us["pre1940_share"] < 15
assert [o[2] for o in us["orig"][:5]] == ["GBR", "CAN", "DEU", "FRA", "JPN"]
B = {b["dec"]: b for b in ab["by_dec"]}
assert all(B[d]["us_pct"] < min(B[2010]["us_pct"], B[2020]["us_pct"]) for d in range(1960, 2010, 10)) and B[1950]["us_pct"] > B[2020]["us_pct"]   # 'higher than any decade since the 1950s'
assert 30 <= us["since1950_abroad_pct"] <= 36                      # 'a third of those'
assert de["early_abroad_pct"] < 15 and de["late_abroad_pct"] > 40
N = de["named"]
assert N["Otto Stern"]["to"] == "United States" and N["Hans Krebs"]["to"] == "United Kingdom" and N["Max Born"]["to"] == "United Kingdom" and N["Hans Bethe"]["to"] == "United States"
assert 1950 <= N["Hans Krebs"]["y"] <= 1959 and 1950 <= N["Max Born"]["y"] <= 1959 and all(N[k]["then"] for k in ("Otto Stern", "Hans Krebs", "Max Born", "Hans Bethe"))
assert jp["rank_since2000_born"] == 3 and [x["iso"] for x in jp["since2000_top_born"][:3]] == ["USA", "GBR", "JPN"]
assert all(a["to"] == "United States" for a in jp["abroad"]) and jp["first_name"] == "Hideki Yukawa" and jp["abroad"][0]["aff"] == "Columbia University"
names_abroad = [a["n"] for a in jp["abroad"]]
assert {"Yoichiro Nambu", "Shuji Nakamura", "Syukuro Manabe"} <= set(names_abroad)
assert R["people"]["Yoichiro Nambu"]["aff"].endswith("University of Chicago") and R["people"]["Syukuro Manabe"]["aff"] == "Princeton University"
jhome = [r for r in L.values() if r["birth_iso3"] == "JPN" and r["work_iso3"] == "JPN" and r["in_flow_analysis"] == "1"]
assert len(jhome) > len(jp["abroad"]) * 2
assert sum("Kyoto University" == r["affiliation"] for r in jhome) >= 3 and sum("Nagoya" in r["affiliation"] for r in jhome) >= 2 and sum("Tokyo" in r["affiliation"] for r in jhome) >= 3
assert any("Shimadzu" in r["affiliation"] for r in jhome) and any("Asahi Kasei" in r["affiliation"] for r in jhome)
CC = [r for r in csv.DictReader(open(f"{DATA}/countries.csv", encoding="utf-8")) if int(r["born_there"]) >= 10 and r["iso3"] != "USA"]
stay = {r["iso3"]: int(r["stayed"]) / int(r["born_there"]) for r in CC}
assert sum(stay["JPN"] > v for k, v in stay.items() if k != "JPN") >= 2 / 3 * (len(stay) - 1)     # 'unlike most other countries, Japan keeps its laureates'
assert inst["top10_us"] == 9 and inst["top"][9]["name"] == "University of Cambridge" and all(x["iso"] == "USA" for x in inst["top"][:9])
assert [x["name"] for x in inst["top"][:4]] == ["Harvard University", "Massachusetts Institute of Technology", "Stanford University", "University of California, Berkeley"]
bp = [p["pct"] for p in ab["by_prize"]]
assert bp[1] > bp[0] > bp[3] > bp[2] and max(bp) - min(bp) < 7     # order as written, 'much alike'
assert R["people"]["Marie Curie 1911"]["b_iso"] == "POL" and R["people"]["Marie Curie 1911"]["w_iso"] == "FRA"
assert "Marie Curie (Physics, 1903)" in R["source"]["sci_noaff"] and "Friedrich von Hayek (Economic Sciences, 1974)" in R["source"]["sci_noaff"]
assert R["source"]["n_multi_prize"] == 5 and set(R["source"]["wd_unmatched"]) == {"", "Sheldon Cooper"}
assert R["peace_lit"]["pct"] < ab["pct"] / 1.5
assert abs(w["flow_w_abroad_pct"] - w["flow_m_abroad_pct"]) < 6     # 'about as likely'


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    assert "{{" not in html.replace("10.5281/zenodo.23857487", "").replace("https://blog.tristanhotham.com/2026/10/31/nobel-brain-drain/", "")
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
