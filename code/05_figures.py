"""Header card (header.png), blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png)."""
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json"); PTS = jload(f"{DATA}/points.json")["rows"]
CONT = lambda iso: SITE["cont"].get(iso)
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
DL = lambda d: f"{d}s"


def both(fig, name):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def clean(ax, left=False):
    for s in ("top", "right") + (("left",) if not left else ()):
        ax.spines[s].set_visible(False)
    ax.set_facecolor(BG)


def dest_legend(ax, x, y, fs=10.5, home=True, loc="lower left"):
    hs = [Line2D([0], [0], color=c, lw=2.4, label=f"Born abroad, won {l}") for _, l, c in DEST]
    if home:
        hs.append(Line2D([0], [0], marker="o", ls="", color="#8C8478", ms=5, label="Born in the country they worked in"))
    lg = ax.legend(handles=hs, loc=loc, bbox_to_anchor=(x, y), frameon=False, fontsize=fs, handlelength=1.8)
    return lg


# 1. the flow map
fig = plt.figure(figsize=(12, 7.4), facecolor=BG)
ax = fig.add_axes([0, .17, 1, .83]); world(ax, lw=.25)
flows(ax, PTS, CONT, lw=.8, alpha=.5, dot=7)
dest_legend(ax, .01, -.2, fs=10)
ax.text(.99, -.04, f"Physics, Chemistry, Medicine and Economics, 1901 to {R['source']['y1']}: {R['abroad']['n']:,} prizes,\n{R['abroad']['abroad']:,} ({R['abroad']['pct']:.0f}%) to people working outside their birth country.",
        transform=ax.transAxes, ha="right", va="top", fontsize=10, color=MUT)
both(fig, "flowmap")

# 2. net gain and loss by country
def netbars(ax, rows, cap=22, fs=11):
    y = np.arange(len(rows))[::-1]
    for yy, c in zip(y, rows):
        v = c["net"]; vv = max(-cap, min(cap, v))
        ax.barh(yy, vv, color=GAIN if v > 0 else LOSS, height=.7)
        if abs(v) > cap:
            xb = np.sign(v) * cap * .86
            ax.plot([xb - .5, xb + .5], [yy - .45, yy + .45], color=BG, lw=3.2, zorder=3)
        ax.text(vv + (.6 if v > 0 else -.6), yy, f"{v:+d}", va="center", ha="left" if v > 0 else "right", fontsize=fs - 1, color=FG, fontweight="medium")
        ax.text(-cap - 1.5, yy, c["name"], va="center", ha="right", fontsize=fs, color=FG)
        ax.text(cap + 15, yy, f"{c['born']} / {c['worked']}", va="center", ha="right", fontsize=fs - 2, color=MUT)
    ax.axvline(0, color=FG, lw=.8)
    ax.set_xlim(-cap - 15, cap + 15.5); ax.set_ylim(-.7, len(rows) - .2); ax.axis("off")
    ax.text(cap + 15, len(rows) - .45, "born / won there", ha="right", va="bottom", fontsize=fs - 2, color=MUT)


NET = R["countries"]["gain"][:5] + R["countries"]["loss"][:12][::-1]
NET = sorted(NET, key=lambda c: -c["net"])
fig = plt.figure(figsize=(10, 7.4), facecolor=BG)
ax = fig.add_axes([.03, .03, .95, .8]); netbars(ax, NET)
fig.text(.02, .955, "Net gain or loss of Nobel laureates, by country", fontproperties=DISPB, fontsize=19, color=FG)
fig.text(.02, .915, "Prizes won by people working in a country minus prizes won by people born there (present-day\nborders; physics, chemistry, medicine and economics). The United States bar is cut short: its\nnet gain is +" + str(R["us"]["net"]) + ".", fontsize=9.5, color=MUT, va="top")
both(fig, "net")

# 3. the United States: share of prizes and share born abroad, by decade
B = R["abroad"]["by_dec"]; xs = np.arange(len(B))
fig = plt.figure(figsize=(12, 5), facecolor=BG)
a1 = fig.add_axes([.06, .14, .4, .7]); a2 = fig.add_axes([.56, .14, .4, .7])
a1.bar(xs, [b["us_share"] for b in B], color=RED, width=.72)
for x, b in zip(xs, B):
    a1.text(x, b["us_share"] + 1.2, f"{b['us_share']:.0f}%", ha="center", fontsize=8.5, color=FG)
a1.set_ylim(0, 80); a1.set_xticks(xs); a1.set_xticklabels([f"'{str(b['dec'])[2:]}" for b in B], fontsize=9.5); a1.set_yticks([])
clean(a1)
a1.set_title("Share of prizes won by people working in the US", loc="left", fontsize=12, color=FG, pad=10)
a2.plot(xs, [b["pct"] for b in B], color=FG, lw=2.2, marker="o", ms=4, label="All prizes (science and economics)")
U = [(x, b["us_pct"]) for x, b in zip(xs, B) if b["us_n"] >= 10]
a2.plot([u[0] for u in U], [u[1] for u in U], color=RED, lw=2.4, marker="o", ms=4, label="Prizes won in the United States")
a2.set_ylim(0, 60); a2.set_yticks([0, 20, 40, 60]); a2.set_yticklabels(["0%", "20%", "40%", "60%"], fontsize=9.5)
a2.set_xticks(xs); a2.set_xticklabels([f"'{str(b['dec'])[2:]}" for b in B], fontsize=9.5); clean(a2, left=True)
a2.grid(axis="y", color=RULE); a2.set_axisbelow(True)
a2.legend(frameon=False, fontsize=9.5, loc="upper left", bbox_to_anchor=(0, 1.02))
a2.set_title("Share born in another country", loc="left", fontsize=12, color=FG, pad=10)
fig.text(.06, .03, "Award decade. US line shown for decades with 10 or more US prizes.", fontsize=9, color=MUT)
both(fig, "us")

# 4. Germany
G = R["germany"]["by_dec"]; xs = np.arange(len(G))
fig = plt.figure(figsize=(12, 5), facecolor=BG)
a1 = fig.add_axes([.06, .14, .4, .7]); a2 = fig.add_axes([.56, .14, .4, .7])
a1.bar(xs, [g["work_de_pct"] for g in G], color=[RED if g["dec"] < 1940 else "#C9BFAE" for g in G], width=.72)
for x, g in zip(xs, G):
    a1.text(x, g["work_de_pct"] + 1, f"{g['work_de_pct']:.0f}%", ha="center", fontsize=8.5, color=FG)
a1.set_ylim(0, 40); a1.set_yticks([]); a1.set_xticks(xs); a1.set_xticklabels([f"'{str(g['dec'])[2:]}" for g in G], fontsize=9.5); clean(a1)
a1.set_title("Share of prizes won by people working in Germany", loc="left", fontsize=12, color=FG, pad=10)
a2.bar(xs, [g["born_de_home"] for g in G], color="#8C8478", width=.72, label="worked in Germany")
a2.bar(xs, [g["born_de_abroad"] for g in G], bottom=[g["born_de_home"] for g in G], color=BLUE, width=.72, label="worked abroad")
a2.set_xticks(xs); a2.set_xticklabels([f"'{str(g['dec'])[2:]}" for g in G], fontsize=9.5); clean(a2, left=True)
a2.set_yticks([0, 5, 10, 15]); a2.grid(axis="y", color=RULE); a2.set_axisbelow(True)
a2.legend(frameon=False, fontsize=9.5, loc="upper right")
a2.set_title("Laureates born in the German lands of the day", loc="left", fontsize=12, color=FG, pad=10)
fig.text(.06, .03, "Award decade. Right: born in a place the Nobel Prize API names as Germany or a German state at the time of birth, including places now in Poland, Russia and France.", fontsize=9, color=MUT)
both(fig, "germany")

# 5. Japan
J = R["japan"]["by_dec"]; xs = np.arange(len(J))
fig = plt.figure(figsize=(12, 4.6), facecolor=BG)
a1 = fig.add_axes([.06, .15, .9, .68])
home = [j["worked"] for j in J]; tot = [j["born"] for j in J]
ab = [t - h if t >= h else 0 for t, h in zip(tot, home)]
jh = [sum(1 for r in PTS if r[15] and r[7] == "JPN" and r[10] == "JPN" and r[3] // 10 * 10 == j["dec"]) for j in J]
ja = [sum(1 for r in PTS if r[15] and r[7] == "JPN" and r[10] != "JPN" and r[3] // 10 * 10 == j["dec"]) for j in J]
a1.bar(xs, jh, color=GOLD, width=.7, label="born in Japan, worked in Japan")
a1.bar(xs, ja, bottom=jh, color=RED, width=.7, label="born in Japan, worked in the United States")
for x, h, a in zip(xs, jh, ja):
    if h + a:
        a1.text(x, h + a + .25, str(h + a), ha="center", fontsize=10, color=FG)
a1.set_xticks(xs); a1.set_xticklabels([DL(j["dec"]) for j in J], fontsize=10); a1.set_yticks([]); clean(a1)
a1.legend(frameon=False, fontsize=10, loc="upper left")
a1.set_title("Japanese-born Nobel laureates in physics, chemistry and medicine, by award decade", loc="left", fontsize=12.5, color=FG, pad=10)
both(fig, "japan")

# 6. institutions
T = R["institutions"]["top"][:15]
fig = plt.figure(figsize=(10, 6.6), facecolor=BG)
ax = fig.add_axes([.38, .05, .58, .82])
y = np.arange(len(T))[::-1]
cols = [RED if t["iso"] == "USA" else BLUE if t["iso"] == "GBR" else GOLD for t in T]
ax.barh(y, [t["n"] for t in T], color=cols, height=.72)
for yy, t in zip(y, T):
    ax.text(t["n"] + .3, yy, str(t["n"]), va="center", fontsize=10, color=FG)
ax.set_yticks(y); ax.set_yticklabels([t["name"] for t in T], fontsize=10.5); ax.tick_params(length=0); ax.set_xticks([])
clean(ax); ax.spines["bottom"].set_visible(False)
fig.text(.02, .94, "Prizes by institution at the time of the award", fontproperties=DISPB, fontsize=17, color=FG)
fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in (RED, BLUE, GOLD)], labels=["United States", "United Kingdom", "elsewhere"], frameon=False, ncol=3, fontsize=10, loc="upper left", bbox_to_anchor=(.02, .925))
both(fig, "universities")

# 7. women
Wd = R["women"]["by_dec"]; xs = np.arange(len(Wd))
fig = plt.figure(figsize=(12, 4.8), facecolor=BG)
ax = fig.add_axes([.06, .14, .9, .7])
ax.bar(xs, [w["pct"] for w in Wd], color=PURP, width=.7, alpha=.9, label="all six prizes")
ax.plot(xs, [w["sci_pct"] for w in Wd], color=FG, lw=2, marker="o", ms=4, label="physics, chemistry, medicine and economics")
for x, w in zip(xs, Wd):
    ax.text(x, w["pct"] + .8, f"{w['pct']:.0f}%", ha="center", fontsize=9.5, color=PURP)
ax.set_xticks(xs); ax.set_xticklabels([DL(w["dec"]) for w in Wd], fontsize=10); ax.set_ylim(0, 25); ax.set_yticks([0, 10, 20]); ax.set_yticklabels(["0%", "10%", "20%"])
clean(ax, left=True); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=10, loc="upper left")
ax.set_title("Women's share of Nobel prizes awarded to people, by decade", loc="left", fontsize=12.5, color=FG, pad=10)
fig.text(.06, .03, f"2020s: {R['source']['y1'] - 2019} years so far.", fontsize=9, color=MUT)
both(fig, "women")

# 8. Europe close-up of flows (paper)
fig = plt.figure(figsize=(12, 7.2), facecolor=BG)
x0, y0 = proj(-12, 34); x1, y1 = proj(42, 62)
ax = fig.add_axes([0, .08, 1, .92]); world(ax, lw=.4, ext=(x0, x1, y0, y1))
flows(ax, PTS, CONT, lw=1, alpha=.55, dot=12)
dest_legend(ax, .01, -.1, fs=10)
both(fig, "europe")

# ---------- header card ----------
fig = plt.figure(figsize=(12, 6.3), facecolor=BG)
ax = fig.add_axes([.34, .06, .66, .88]); world(ax, lw=.2, ext=(-11.5e6, 14.5e6, -4.6e6, 8.4e6))
flows(ax, PTS, CONT, lw=.7, alpha=.5, dot=4, home=False)
fig.text(.045, .79, "The Nobel", fontproperties=DISP, fontsize=46, color=FG)
fig.text(.045, .66, "brain drain", fontproperties=DISP, fontsize=46, color=RED)
fig.text(.045, .55, f"Where {R['abroad']['n']:,} laureates were born,\nand where they did the work\nthat won the prize", fontproperties=SERP, fontsize=19, color=FG, va="top", linespacing=1.5)
fig.text(.045, .3, f"{R['us']['pct']:.0f}%", fontproperties=DISP, fontsize=40, color=RED, va="top")
fig.text(.045, .19, "of prizes won in the US went\nto people born abroad", fontsize=11.5, color=FG, va="top", linespacing=1.4)
fig.text(.045, .045, f"maps.tristanhotham.com/{SLUG}", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)))
