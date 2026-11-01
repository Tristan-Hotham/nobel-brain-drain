"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23857487, https://doi.org/10.5281/zenodo.23857487 and https://blog.tristanhotham.com/2026/10/31/nobel-brain-drain/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_The_Nobel_Brain_Drain"

# facts stated in words in the blog (alt text included); the page build checks the rest
import importlib.util
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
B = {b["dec"]: b for b in R["abroad"]["by_dec"]}
assert all(B[d]["us_share"] < 10 for d in (1900, 1910, 1920)) and round(B[1930]["us_share"]) == 26 and B[1940]["us_share"] == 50
assert all(59.5 <= B[d]["us_share"] <= 76.5 for d in range(1980, 2030, 10)) and round(B[1940]["us_pct"]) == 47 and round(B[2000]["us_pct"]) == 28 and round(B[2020]["us_pct"]) == 38
assert all(23.5 <= B[d]["pct"] <= 38 for d in range(1900, 2030, 10))
G = {g["dec"]: g for g in R["germany"]["by_dec"]}
assert all(24 <= G[d]["work_de_pct"] <= 34 for d in range(1900, 1940, 10)) and all(G[d]["work_de_pct"] < 12 for d in range(1940, 2030, 10))
assert R["germany"]["prewar_home_n"] >= .85 * R["germany"]["prewar_n"]
W = {w["dec"]: w for w in R["women"]["by_dec"]}
assert all(W[d]["pct"] < 8 for d in range(1900, 2000, 10)) and round(W[2000]["pct"]) == 9 and round(W[2010]["pct"]) == 11 and 11 <= W[2020]["sci_pct"] <= 12.5
assert [j["born"] for j in R["japan"]["by_dec"]] == [0, 0, 0, 0, 1, 0, 1, 1, 2, 0, 8, 10, 4]
T = R["institutions"]["top"]
assert T[4]["n"] == T[5]["n"] and {T[4]["name"], T[5]["name"]} == {"California Institute of Technology", "University of Chicago"}
assert [T[i]["name"] for i in (6, 7, 8, 9)] == ["Columbia University", "Rockefeller University", "Princeton University", "University of Cambridge"]
L = {c["iso"]: c["net"] for c in R["countries"]["loss"]}
assert L["ZAF"] == -4 and L["AUS"] == -4 and min(v for k, v in L.items() if k != "POL") == -9
assert len(R["japan"]["abroad"]) == 7      # 'one of the seven'

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for ln in post.splitlines():
    if "{{IMG|" in ln:
        assert ln.startswith("{{IMG|") and ln.endswith("}}"), ln[:60]
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "The Nobel brain drain: where laureates were born, and where they won",
        "slug": "nobel-brain-drain",
        "excerpt": f"I drew a line from birthplace to prize for {R['abroad']['n']} Nobel prizes in the sciences and economics. {R['abroad']['pct']:.0f}% went to someone working outside their birth country, the United States gained {R['us']['net']} more laureates than it grew, Germany's share fell from {R['germany']['work_share_to1932']:.0f}% to {R['germany']['work_share_since1933']:.0f}% after 1933, and Japan became a late riser that keeps its laureates.",
        "seo_description": "A flow map of Nobel laureates from birthplace to prize: the US as the great importer, Germany after 1933, Japan's rise and the top universities.",
        "tags": ["Nobel Prize", "science history", "migration", "brain drain", "maps", "data visualisation", "Wikidata", "open data"],
        "header_alt": f"Title card reading 'The Nobel brain drain' in black and red on cream paper, beside a world map of curved lines from laureates' birthplaces to where they won, most of them red lines from Europe to the United States. Text: where {R['abroad']['n']} laureates were born and where they did the work that won the prize; {R['us']['pct']:.0f}% of prizes won in the US went to people born abroad."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"{SLUG}/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "reddit/collage.py"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~", " ")
zmeta = {"title": "The Nobel Brain Drain: Where Nobel Laureates Were Born and Where They Were Working When They Won, 1901 to " + str(R["source"]["y1"]),
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/nobel-brain-drain/}}.</p><p>Data: Nobel Prize API v2.1 (Nobel Prize Outreach; the downloaded file carries no licence statement, see the terms of use on nobelprize.org); Wikidata (CC0); Wikipedia, List of Nobel laureates by university affiliation (CC BY-SA 4.0, used only as a cross-check); Natural Earth (public domain).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["Nobel Prize", "scientific migration", "brain drain", "history of science", "Wikidata", "open data", "flow maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://api.nobelprize.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
st = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in st, bad
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
