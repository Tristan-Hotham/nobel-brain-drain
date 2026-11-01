"""Shared paths and helpers for the nobel-brain-drain project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw8/nobel/nobel_api_laureates.json   The official Nobel Prize API (v2.1, api.nobelprize.org),
      every laureate (1,028, people and organisations) with knownName, gender, birth date and place (city and country as
      named at birth and now, with coordinates for the present-day city where the API has them) and, for every prize,
      year, category, portion, motivation, affiliations at the time of the award (name, city, country, with present-day
      city coordinates) and, mostly for Peace and Literature, residences. Retrieved 2026. The file itself carries no
      licence statement.
  /home/claude/newdata/raw8/nobel/wikidata_nobel.tsv   QLever query result on Wikidata (CC0), retrieved 2026: laureates of
      the Nobel Prizes in Physics, Chemistry and Physiology or Medicine with the prize, the year qualifier, place of birth
      (P19) with coordinates and country, and employers (P108) with their coordinates (P625) or headquarters coordinates.
      The affiliation (P1416) columns came back empty, so employers are used to place affiliations.
  /home/claude/newdata/raw8/nobel/wiki_List_of_Nobel_laureates_by_university_affiliation.json   Wikipedia, "List of
      Nobel laureates by university affiliation" (rendered HTML, CC BY-SA 4.0), used only to cross-check counts.
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_50m_admin_0_countries.geojson,
      ne_10m_populated_places_simple.geojson   Natural Earth (public domain).
"""
import json, gzip, os, re, unicodedata, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("NOBEL_RAW", "/home/claude/newdata/raw8/nobel")
GEO = os.environ.get("NOBEL_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("NOBEL_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("NOBELTMP", "/dev/shm/nobel"), "work")   # intermediates, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "nobel-brain-drain"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23857487"                  # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/nobel-brain-drain/"            # filled in by the publisher
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
WD = "http://www.wikidata.org/entity/"
# the four prizes whose laureates the Nobel API gives an affiliation at the time of the award
SCI = ["Physics", "Chemistry", "Physiology or Medicine", "Economic Sciences"]
PRIZES = SCI + ["Literature", "Peace"]
PCODE = {"Physics": "phy", "Chemistry": "che", "Physiology or Medicine": "med", "Economic Sciences": "eco", "Literature": "lit", "Peace": "pea"}
PSHORT = {"Physics": "Physics", "Chemistry": "Chemistry", "Physiology or Medicine": "Medicine", "Economic Sciences": "Economics", "Literature": "Literature", "Peace": "Peace"}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from source text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-").replace("\xad", "")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def km(lon1, lat1, lon2, lat2):
    a = math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(min(1, a)))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    raise ValueError(f)
