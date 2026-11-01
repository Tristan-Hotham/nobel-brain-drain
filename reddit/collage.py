"""Reddit collage (r/dataisbeautiful style, light background), 2400 x 3400 px: the flow map from birthplace to prize,
net gain and loss bars, the US and German shares of prizes by decade, the top institutions, stat tiles, a full legend
and credits. Map labels are placed by a search over candidate positions: each must sit wholly on plain sea (no land,
no line, no dot under it, checked on the rendered pixels) and clear of the other labels. No leader lines are used.
The script stops if a label cannot be placed."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json"); PTS = jload(f"{DATA}/points.json")["rows"]
CONT = lambda iso: SITE["cont"].get(iso)
OUT = os.path.join(ROOT, "reddit", "nobel_brain_drain.png")
us, ab, de, jp = R["us"], R["abroad"], R["germany"], R["japan"]

fig = plt.figure(figsize=(24, 34), dpi=100, facecolor=BG)
# ---------------- title ----------------
fig.text(.035, .975, "The Nobel brain drain", fontproperties=DISP, fontsize=96, color=FG, va="top")
for k, ln in enumerate([f"Where {ab['n']:,} Nobel laureates in physics, chemistry, medicine and economics were born, and where they were",
                        f"working when they won, 1901 to {R['source']['y1']}. Each line runs from a birthplace to the institution at the time of the",
                        f"award, for the {ab['abroad']} prizes ({ab['pct']:.0f}%) won by someone working outside their birth country."]):
    fig.text(.035, .934 - k * .0135, ln, fontproperties=SERP, fontsize=25, color=FG, va="top")

# ---------------- map ----------------
EXT = (-15.8e6, 17.0e6, -5.9e6, 8.45e6)
axm = fig.add_axes([.005, .585, .99, .315]); axm.set_facecolor(BG)
world(axm, lw=.5, ext=EXT)
flows(axm, PTS, CONT, lw=1.5, alpha=.5, dot=30, home_col="#8C8478")
axm.set_xlim(*EXT[:2]); axm.set_ylim(*EXT[2:])

LABELS = [  # (search box lon0, lon1, lat0, lat1, preferred lon, lat), title, body, colour
    ((-178, -120, -5, 45, -165, 28), "United States", f"{us['n']} prizes won there,\n{us['abroad']} by people born abroad\n({us['pct']:.0f}%) from {us['n_orig']} countries", RED),
    ((143, 178, -12, 50, 150, 25), "Japan", f"{jp['n']} laureates born\nthere: {jp['before2000']} before\n2000, {jp['since2000']} since;\n{jp['n_abroad']} won in the US", GOLD),
    ((-45, 5, -50, -10, -35, -30), "Only {} countries gain".format(R['countries']['n_gain']), f"more laureates than they grow;\nthe US gains {us['net']}, the\nrest at most {R['countries']['gain'][1]['net']}", FG),
]


def cands(b):
    lon0, lon1, lat0, lat1, plon, plat = b
    g = [(lo, la) for lo in np.arange(lon0, lon1 + .1, 2) for la in np.arange(lat0, lat1 + .1, 1.5)]
    return [(plon, plat)] + sorted(g, key=lambda p: (p[0] - plon) ** 2 + (p[1] - plat) ** 2)


fig.canvas.draw()
rend = fig.canvas.get_renderer()
img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].astype(int)
H_ = img.shape[0]
bgc = np.array([int(BG[i:i + 2], 16) for i in (1, 3, 5)])
occ = np.abs(img - bgc).sum(axis=2) > 12            # anything that is not plain paper: land, lines, dots
mb = axm.get_window_extent(rend)
placed = []


def free(bb):
    x0, x1 = int(bb.x0), int(bb.x1); y0, y1 = int(H_ - bb.y1), int(H_ - bb.y0)
    if x0 < mb.x0 + 8 or x1 > mb.x1 - 8 or bb.y0 < mb.y0 + 8 or bb.y1 > mb.y1 - 8:
        return False
    if occ[y0:y1, x0:x1].any():
        return False
    return not any(bb.overlaps(p) for p in placed)


for cands_, title, body, col in LABELS:
    ok = False
    for lon, lat in cands(cands_):
        x, y = proj(lon, lat)
        t1 = axm.text(x, y, title, fontproperties=DISPB, fontsize=25, color=col, ha="left", va="bottom", zorder=20)
        t2 = axm.text(x, y, body, fontsize=16, color=FG, ha="left", va="top", linespacing=1.35, zorder=20)
        b1 = t1.get_window_extent(rend).expanded(1.06, 1.25); b2 = t2.get_window_extent(rend).expanded(1.06, 1.12)
        if free(b1) and free(b2):
            for t in (t1, t2):
                t.set_path_effects([pe.withStroke(linewidth=6, foreground=BG)])
            placed += [b1, b2]; ok = True; print(title, "at", round(float(lon)), round(float(lat)))
            break
        t1.remove(); t2.remove()
    if not ok:
        fig.savefig("/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/dbg.png", dpi=60)
        raise SystemExit(f"could not place label {title}")

# legend under the map
hs = [Line2D([0], [0], color=c, lw=4, label=l) for c, l in ((RED, "Born abroad, won while working in the United States"), (BLUE, "Born abroad, won while working in Europe"), (GOLD, "Born abroad, won while working anywhere else"))]
hs += [Line2D([0], [0], marker="o", ls="", mfc=BG, mec=FG, mew=1.5, ms=10, label="Birthplace"), Line2D([0], [0], marker="o", ls="", color=FG, ms=10, label="Institution at the award"),
       Line2D([0], [0], marker="o", ls="", color="#8C8478", ms=8, label="Won in the country they were born in")]
fig.legend(handles=hs, loc="upper left", bbox_to_anchor=(.035, .585), ncol=2, frameon=False, fontsize=19, handlelength=2.2, columnspacing=3, labelspacing=.8)
fig.text(.965, .58, "Present-day countries. Equal Earth projection.", fontsize=16, color=MUT, ha="right", va="top")

# ---------------- net gain and loss ----------------
axn = fig.add_axes([.035, .245, .46, .215])
NET = sorted(R["countries"]["gain"][:5] + R["countries"]["loss"][:12], key=lambda c: -c["net"])
cap = 22
yy = np.arange(len(NET))[::-1]
for y, c in zip(yy, NET):
    v = c["net"]; vv = max(-cap, min(cap, v))
    axn.barh(y, vv, color=GAIN if v > 0 else LOSS, height=.72)
    if abs(v) > cap:
        axn.plot([cap * .8 - .6, cap * .8 + .6], [y - .45, y + .45], color=BG, lw=5, zorder=3)
        axn.text(cap - 1, y, f"+{v}", va="center", ha="right", fontsize=17, color="white", fontweight="medium", zorder=4)
    else:
        axn.text(vv + (.6 if v > 0 else -.6), y, f"{v:+d}", va="center", ha="left" if v > 0 else "right", fontsize=17, color=FG)
    axn.text(-cap - 1, y, c["name"], va="center", ha="right", fontsize=17, color=FG)
axn.axvline(0, color=FG, lw=1)
axn.set_xlim(-cap - 15, cap + 1); axn.set_ylim(-.6, len(NET) - .4); axn.axis("off")
fig.text(.035, .515, "Net gain or loss of laureates", fontproperties=DISPB, fontsize=34, color=FG, va="top")
fig.text(.035, .5, "prizes won by people working in a country minus prizes won by people born there.\nBlue: gain; red: loss. The US bar is cut short. Poland's loss is mostly Germans\nborn in places that are Polish today.", fontsize=15.5, color=MUT, va="top", linespacing=1.4)

# ---------------- stat tiles ----------------
tiles = [(f"{ab['pct']:.0f}%", RED, "of prizes went to someone working\noutside their birth country"),
         (f"+{us['net']}", BLUE, f"US net gain: {us['n']} prizes won there,\n{us['born']} by people born there"),
         (f"{de['work_share_to1932']:.0f}% to {de['work_share_since1933']:.0f}%", GOLD, "Germany's share of prizes,\nup to 1932 and since 1933"),
         (f"{R['japan']['since2000']}", PURP, f"Japanese-born laureates since 2000;\n{R['japan']['before2000']} in the whole 20th century")]
for k, (big, col, small_) in enumerate(tiles):
    y = .5 - k * .064
    fig.text(.55, y, big, fontproperties=DISP, fontsize=58, color=col, va="top")
    fig.text(.55, y - .032, small_, fontsize=17, color=FG, va="top", linespacing=1.35)

# ---------------- bottom row: US v Germany, institutions ----------------
B = ab["by_dec"]; G = de["by_dec"]; xs = np.arange(len(B))
a1 = fig.add_axes([.06, .092, .38, .088])
a1.plot(xs, [b["us_share"] for b in B], color=RED, lw=4, marker="o", ms=8)
a1.plot(xs, [g["work_de_pct"] for g in G], color=BLUE, lw=4, marker="o", ms=8)
a1.text(xs[-1] + .3, B[-1]["us_share"], "United States", color=RED, fontsize=17, va="center")
a1.text(xs[-1] + .3, G[-1]["work_de_pct"], "Germany", color=BLUE, fontsize=17, va="center")
a1.set_xticks(xs[::2]); a1.set_xticklabels([f"{b['dec']}s" for b in B][::2], fontsize=14)
a1.set_yticks([0, 25, 50, 75]); a1.set_yticklabels(["0%", "25%", "50%", "75%"], fontsize=14); a1.set_ylim(0, 85)
for s in ("top", "right"): a1.spines[s].set_visible(False)
a1.set_facecolor(BG); a1.grid(axis="y", color=RULE); a1.set_axisbelow(True)
fig.text(.035, .215, "Share of prizes won by people working in...", fontproperties=DISPB, fontsize=27, color=FG, va="top")
fig.text(.035, .2, "by award decade", fontsize=15.5, color=MUT, va="top")

a2 = fig.add_axes([.72, .07, .25, .095])
T = R["institutions"]["top"][:8]
assert all(t["iso"] == "USA" for t in T)
y = np.arange(len(T))[::-1]
a2.barh(y, [t["n"] for t in T], color=[RED if t["iso"] == "USA" else BLUE for t in T], height=.72)
for yy_, t in zip(y, T):
    a2.text(t["n"] + .4, yy_, str(t["n"]), va="center", fontsize=15, color=FG)
short = {"Massachusetts Institute of Technology": "MIT", "University of California, Berkeley": "UC Berkeley", "California Institute of Technology": "Caltech"}
a2.set_yticks(y); a2.set_yticklabels([short.get(t["name"], t["name"]) for t in T], fontsize=15); a2.tick_params(length=0)
a2.set_xticks([]); a2.set_facecolor(BG)
for s in ("top", "right", "bottom", "left"): a2.spines[s].set_visible(False)
fig.text(.55, .215, "Top institutions at the award", fontproperties=DISPB, fontsize=27, color=FG, va="top")
fig.text(.55, .2, "prizes, every listed affiliation counted;\nthe top eight are all in the United States", fontsize=15.5, color=MUT, va="top", linespacing=1.35)

# ---------------- footer ----------------
fig.text(.035, .015, "Source: Nobel Prize API v2.1 (Nobel Prize Outreach), 2026: laureates, birthplaces and affiliations at the award;\n"
         "Wikidata (CC0) for birthplace and institution coordinates; Natural Earth. Peace and Literature have no affiliations and are left out.\n"
         "Affiliation at the award is not always where the winning work was done; birth country is not nationality.\n"
         f"Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/{SLUG}", fontsize=15, color=MUT, va="bottom", linespacing=1.6)
fig.savefig(OUT, dpi=100, facecolor=BG)
plt.close(fig)
from PIL import Image
print("collage", Image.open(OUT).size, "labels placed", len(placed) // 2)
