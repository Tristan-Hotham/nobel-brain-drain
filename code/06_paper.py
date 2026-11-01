"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). Facts stated in words are checked here."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_The_Nobel_Brain_Drain"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# ---------- facts stated in words in the paper ----------
c, s, ab = R["countries"], R["source"], R["abroad"]
assert [x["iso"] for x in c["loss"][:2]] == ["POL", "CAN"] and all(c[k]["net"] == -8 for k in ("aut", "hun", "nld", "rus"))
assert c["deu"]["born"] == c["deu"]["worked"] and c["gbr"]["top_dest"][0][2] == "USA"
assert len(s["sci_noaff"]) == 7 and sum(("Hayek" in x or "Myrdal" in x or "Marie Curie" in x) for x in s["sci_noaff"]) == 3   # 'and four others'
B = {b["dec"]: b for b in ab["by_dec"]}
assert max((b for b in ab["by_dec"] if b["us_n"] >= 10), key=lambda b: b["us_pct"])["dec"] == 1940
assert B[2000]["us_pct"] < B[2010]["us_pct"] and B[2000]["us_pct"] < B[1990]["us_pct"]
co = R["germany"]["cohorts"]
assert co[0]["pct"] < co[1]["pct"] < co[2]["pct"]
assert s["n_match_id"] + 2 == s["n_sci3"]
pre = [b for b in R["germany"]["by_dec"] if b["dec"] < 1940]


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    return tex(str(v))


def table(cap, lab, spec, head, rows):
    return (f"\\begin{{table}}[tbp]\\centering\\small\\caption{{{cap}}}\\label{{tab:{lab}}}\\begin{{tabular}}{{{spec}}}\\toprule {head}\\\\\\midrule\n"
            + "".join(" & ".join(str(x) for x in r) + "\\\\\n" for r in rows) + "\\bottomrule\\end{tabular}\\end{table}")


TP = table("From sources to the flow analysis.", "pipe", "p{10.5cm}r", "Step & Count", [
    ["Laureates in the Nobel Prize API", f"{s['n_api']:,}"], ["\\quad of which organisations (excluded)", s["n_org"]],
    ["Prizes awarded to people (records)", f"{s['n_recs']:,}"], ["\\quad physics, chemistry, medicine, economics", s["n_sci"]],
    ["\\quad\\quad with no affiliation in the API", s["n_sci_noaff"]], ["\\quad\\quad with no birthplace in the API", s["n_sci_nobirth"]],
    ["\\quad\\quad in the flow analysis", ab["n"]], ["\\quad peace and literature", s["n_pl"]],
    ["\\quad\\quad with a country of residence", R["peace_lit"]["placed"]],
    ["Wikidata rows (physics, chemistry, medicine)", f"{s['n_wd_rows']:,}"], ["\\quad people", s["n_wd_people"]],
    ["\\quad matched to API records (identifier, prize and year)", s["n_match_id"]], ["\\quad matched by name, prize and year only", s["n_match_any"] - s["n_match_id"]]])
hb, hw = s["how_b"], s["how_w"]
TM = table("How points were placed: birthplaces of all records, workplaces of the flow analysis.", "methods", "p{10.5cm}r", "Method & Records", [
    ["\\textbf{Birthplace}", ""], ["Wikidata birthplace coordinates", s["n_b_wd"]], ["Nobel API present-day city point", s["n_b_api"]],
    ["Natural Earth town of the same name", s["n_b_ne"]], ["Country label point (birthplace vague)", s["n_b_country"]], ["No birthplace", hb.get("null", 0)],
    ["\\textbf{Workplace (flow analysis)}", ""], ["Wikidata employer matched to the affiliation", s["n_w_emp"]], ["Nobel API city point (city centroid)", s["n_w_api"]],
    ["Hand-set point", s["n_w_manual"]]])
TF = table("The largest flows from birth country to country of affiliation (present-day borders).", "flows", "llr", "Born in & Won in & Prizes",
           [[tex(f["from_name"]), tex(f["to_name"]), f["n"]] for f in R["flows"]["top"][:15]])
crow = sorted({x["iso"]: x for x in c["gain"] + c["loss"] + c["top_born"] + c["top_worked"]}.values(), key=lambda x: (-x["worked"] - x["born"]))[:22]
crow.sort(key=lambda x: -x["net"])
TC = table("Countries with most laureates: born there, won there (affiliation at the award), net gain, born there and won abroad, born abroad and won there.", "countries", "lrrrrr",
           "Country & Born & Won & Net & Left & Arrived", [[tex(x["name"]), x["born"], x["worked"], f"{x['net']:+d}", x["left"], x["arrived"]] for x in crow])
TG = table("German-born laureates (German lands of the day) born 1880 to 1929 who won while working abroad.", "germany", "lllp{5.4cm}", "Laureate & Born & Prize & Affiliation at the award",
           [[tex(e["n"]), f"{e['by']}, {tex(e['bp'])}", f"{tex(e['cat'])} {e['y']}", f"{tex(e['aff'])}, {tex(e['to'])}"] for e in R["germany"]["exiles"]])
TW = table("Institution counts compared with Wikipedia's list (top 20 there).", "wiki", "lrr", "Institution (Wikipedia name) & Wikipedia & This study",
           [[tex(x["wiki"]), x["wiki_n"], x["mine"] if x["mine"] is not None else "not matched"] for x in R["institutions"]["wiki"]])
W = {x["dec"]: x for x in R["women"]["by_dec"]}
TD = table("By award decade: records in the flow analysis, share born abroad, share won in the United States and the foreign-born share of those; prizes to people of all six kinds and the share won by women.", "decades", "lrrrrrr",
           "Decade & Flow & Born abroad & In US & US born abroad & All prizes & Women", [[f"{b['dec']}s", b["n"], f"{b['pct']:.1f}\\%", f"{b['us_share']:.1f}\\%",
           f"{b['us_pct']:.1f}\\%" if b["us_n"] >= 10 else "", W[b["dec"]]["n"], f"{W[b['dec']]['pct']:.1f}\\%"] for b in ab["by_dec"]])
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("{{meta.doi}}", "@@DOI@@")
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("PIPELINE", TP), ("METHODS", TM), ("FLOWS", TF), ("COUNTRIES", TC), ("GERMANY", TG), ("WIKI", TW), ("DECADES", TD)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t
for bad in ("DSIT", "DCMS"):
    assert bad not in t
# the DOI placeholder stays literal for the publisher; LaTeX needs its braces escaped
t = t.replace("\\href{https://doi.org/@@DOI@@}{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}").replace("\\url{https://doi.org/@@DOI@@}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "@@DOI@@" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
