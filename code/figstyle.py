"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the medal-and-paper palette, Natural Earth outlines in the Equal Earth projection, and flow arcs."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#67626C", "axes.labelcolor": "#1D1B22",
                     "xtick.color": "#67626C", "ytick.color": "#67626C"})
BG, FG, MUT, LAND, RULE, SEA = "#F7F3EC", "#1D1B22", "#67626C", "#E4DDCD", "#E2DBCD", "#F7F3EC"
RED, BLUE, GOLD, GREEN, PURP, TEAL = "#A3202E", "#2F5D8C", "#C8961E", "#3E8E5E", "#7A4E9E", "#2A9BA8"
GAIN, LOSS = "#2F5D8C", "#A3202E"
DEST = [("USA", "to the United States", RED), ("EUR", "to Europe", BLUE), ("OTH", "to anywhere else", GOLD)]
PCOL = {"Physics": BLUE, "Chemistry": GREEN, "Physiology or Medicine": RED, "Economic Sciences": GOLD, "Literature": PURP, "Peace": TEAL}

EE = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in W["features"]:
    for ring in rings(f["geometry"]):
        x, y = EE.transform(np.clip(ring[:, 0], -179.9, 179.9), ring[:, 1])
        SHAPES.append((f["properties"]["iso"], np.column_stack([x, y])))
WORLD_EXT = (-12.3e6, 15.6e6, -5.6e6, 8.4e6)


def world(ax, colour_of=lambda iso: None, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1):
    for iso, p in SHAPES:
        c = colour_of(iso)
        ax.add_patch(MPoly(p, closed=True, fc=land if c is None else c, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def proj(lon, lat):
    return EE.transform(np.asarray(lon), np.asarray(lat))


def arc(p0, p1, bend=.16, n=40):
    """A curved path between two projected points, bowed to the left of the direction of travel."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0; L = np.hypot(*d)
    if L == 0:
        return np.array([p0, p1])
    nrm = np.array([-d[1], d[0]]) / L
    c = (p0 + p1) / 2 + nrm * L * bend * (1 if L < 8e6 else 8e6 / L)
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1


def dest_group(w_iso, cont):
    return "USA" if w_iso == "USA" else "EUR" if cont == "Europe" else "OTH"


def flows(ax, rows, cont_of, lw=.9, alpha=.55, dot=6, home=True, ext=None, z=4, home_col="#8C8478"):
    """Draw flow arcs (born abroad) and home dots (worked in their birth country). rows: points.json rows."""
    out = []
    for r in rows:
        if not r[15] or not r[6] or not r[9]:
            continue
        x0, y0 = proj(*r[6]); x1, y1 = proj(*r[9])
        if r[7] != r[10]:
            g = dest_group(r[10], cont_of(r[10]))
            col = dict((k, c) for k, _, c in DEST)[g]
            out.append((g, (x0, y0), (x1, y1), col))
    if home:
        H = [proj(*r[9]) for r in rows if r[15] and r[9] and r[7] == r[10]]
        if H:
            H = np.array(H)
            ax.scatter(H[:, 0], H[:, 1], s=dot * .9, c=home_col, lw=0, alpha=.75, zorder=z - 1)
    order = {"OTH": 0, "EUR": 1, "USA": 2}
    for g, a, b, col in sorted(out, key=lambda t: order[t[0]]):
        P = arc(a, b)
        ax.plot(P[:, 0], P[:, 1], color=col, lw=lw, alpha=alpha, solid_capstyle="round", zorder=z)
        ax.scatter([a[0]], [a[1]], s=dot * .55, facecolor="none", edgecolor=col, lw=.6, alpha=.8, zorder=z + 1)
        ax.scatter([b[0]], [b[1]], s=dot, color=col, lw=0, alpha=.9, zorder=z + 1)
    return out


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
