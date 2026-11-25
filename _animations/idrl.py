"""Iterative Dual-RL: iteratively drop zero-weight transitions using the corrected visitation ratio, then weighted BC."""

import sys
from svganim import C, anim, fade, text, group, svg_doc, caption_track

DUR = 16.0
W, H = 480, 300
OUT = 15.5

GX0, GY0, CELL, NC, NR = 22, 64, 36, 7, 5


def ctr(c, r):
    return GX0 + CELL * c + CELL / 2, GY0 + CELL * r + CELL / 2


OPT = [((0, 4), (1, 4)), ((1, 4), (2, 4)), ((2, 4), (2, 3)), ((2, 3), (3, 3)), ((3, 3), (4, 3)), ((4, 3), (4, 2)),
       ((4, 2), (5, 2)), ((5, 2), (5, 1)), ((5, 1), (6, 1)), ((6, 1), (6, 0))]
DETOUR = [((2, 3), (2, 2)), ((2, 2), (2, 1)), ((2, 1), (3, 1)), ((3, 1), (3, 0)), ((3, 0), (4, 0)), ((4, 0), (5, 0)),
          ((5, 0), (6, 0)), ((0, 4), (0, 3)), ((0, 3), (1, 3)), ((1, 3), (1, 2)), ((1, 2), (2, 2))]
BAD = [((2, 4), (3, 4)), ((3, 4), (4, 4)), ((4, 4), (5, 4)), ((5, 4), (6, 4)), ((6, 4), (6, 3)), ((1, 2), (0, 2)),
       ((0, 2), (0, 1)), ((0, 1), (0, 0)), ((0, 0), (1, 0)), ((3, 3), (3, 4)), ((4, 2), (3, 2)), ((3, 2), (3, 3))]
N1, N2, N3 = len(OPT) + len(DETOUR) + len(BAD), len(OPT) + len(DETOUR), len(OPT)

T_IT1_FLAG, T_IT1_DROP = 4.2, 5.4
T_IT2_FLAG, T_IT2_DROP = 8.0, 9.2
T_BC = 11.0

body = []
body.append(
    caption_track(
        [
            (0.0, 3.25, "1", "Offline dataset: transitions of mixed quality"),
            (3.35, 7.05, "2", "Iteration 1: Dual-RL ratio w(s,a); drop w = 0"),
            (7.15, 10.85, "3", "Iteration 2: rerun on what is left; drop w = 0"),
            (10.95, OUT, "4", "Weighted BC on the rest → near-optimal policy"),
        ],
        DUR,
    )
)

# grid
grid = f'<rect x="{GX0}" y="{GY0}" width="{CELL*NC}" height="{CELL*NR}" rx="6" fill="{C["card"]}" stroke="{C["line"]}"/>'
for c in range(1, NC):
    grid += f'<line x1="{GX0+CELL*c}" y1="{GY0}" x2="{GX0+CELL*c}" y2="{GY0+CELL*NR}" stroke="{C["line"]}"/>'
for r in range(1, NR):
    grid += f'<line x1="{GX0}" y1="{GY0+CELL*r}" x2="{GX0+CELL*NC}" y2="{GY0+CELL*r}" stroke="{C["line"]}"/>'
sx, sy = ctr(0, 4)
gx, gy = ctr(6, 0)
grid += f'<circle cx="{sx}" cy="{sy}" r="10" fill="{C["blue_l"]}" stroke="{C["blue"]}" stroke-width="2"/>'
grid += text(sx, sy + 4, "S", size=11, fill=C["blue"], weight=700, anchor="middle")
grid += f'<circle cx="{gx}" cy="{gy}" r="10" fill="{C["red_l"]}" stroke="{C["red"]}" stroke-width="2"/>'
grid += text(gx, gy + 4, "G", size=11, fill=C["red"], weight=700, anchor="middle")
body.append(grid)


def arrow(a, b, color, width):
    (x1, y1), (x2, y2) = ctr(*a), ctr(*b)
    dx, dy = x2 - x1, y2 - y1
    L = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / L, dy / L
    sxp, syp = x1 + ux * 8, y1 + uy * 8
    ex, ey = x2 - ux * 8, y2 - uy * 8
    hx, hy = ex - ux * 7, ey - uy * 7
    px_, py_ = -uy * 4.5, ux * 4.5
    return (
        f'<line x1="{sxp:.1f}" y1="{syp:.1f}" x2="{hx:.1f}" y2="{hy:.1f}" stroke-width="{width}" stroke-linecap="round"/>'
        f'<polygon points="{ex:.1f},{ey:.1f} {hx+px_:.1f},{hy+py_:.1f} {hx-px_:.1f},{hy-py_:.1f}" stroke="none"/>'
    )


GREEN_LIGHT, GREEN_MID, GREEN_DARK = "#86efac", "#22c55e", "#15803d"


def add_arrows(edges, kind):
    for k, (a, b) in enumerate(edges):
        t_in = 0.3 + 0.05 * (hash((a, b)) % 40)
        if kind == "bad":
            col = [(0, GREEN_LIGHT), (T_IT1_FLAG, GREEN_LIGHT), (T_IT1_FLAG + 0.3, C["red"])]
            op = [(0, 0), (t_in, 0), (t_in + 0.4, 1), (T_IT1_DROP, 1), (T_IT1_DROP + 0.6, 0)]
        elif kind == "detour":
            col = [(0, GREEN_LIGHT), (T_IT1_DROP + 0.6, GREEN_LIGHT), (T_IT1_DROP + 1.0, GREEN_MID),
                   (T_IT2_FLAG, GREEN_MID), (T_IT2_FLAG + 0.3, C["red"])]
            op = [(0, 0), (t_in, 0), (t_in + 0.4, 1), (T_IT2_DROP, 1), (T_IT2_DROP + 0.6, 0)]
        else:
            col = [(0, GREEN_LIGHT), (T_IT1_DROP + 0.6, GREEN_LIGHT), (T_IT1_DROP + 1.0, GREEN_MID),
                   (T_IT2_DROP + 0.6, GREEN_MID), (T_IT2_DROP + 1.0, GREEN_DARK)]
            op = [(0, 0), (t_in, 0), (t_in + 0.4, 1), (OUT, 1), (OUT + 0.4, 0)]
        body.append(
            f'<g stroke="{GREEN_LIGHT}" fill="{GREEN_LIGHT}" opacity="0">'
            + anim("opacity", op, DUR)
            + anim("stroke", col, DUR, ease=False)
            + anim("fill", col, DUR, ease=False)
            + arrow(a, b, GREEN_LIGHT, 2.6)
            + "</g>"
        )


add_arrows(BAD, "bad")
add_arrows(DETOUR, "detour")
add_arrows(OPT, "opt")

# final policy rollout (weighted BC)
path_pts = [ctr(*OPT[0][0])] + [ctr(*b) for _, b in OPT]
poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in path_pts)
L = sum(((path_pts[i + 1][0] - path_pts[i][0]) ** 2 + (path_pts[i + 1][1] - path_pts[i][1]) ** 2) ** 0.5 for i in range(len(path_pts) - 1))
roll = (
    f'<polyline points="{poly}" fill="none" stroke="{C["red"]}" stroke-width="3.2" stroke-linejoin="round" '
    f'stroke-linecap="round" stroke-dasharray="{L:.1f} {L:.1f}" opacity="0.85">'
    + anim("stroke-dashoffset", [(T_BC + 0.6, L), (T_BC + 3.0, 0)], DUR, ease=False)
    + "</polyline>"
)
body.append(group(roll, anims=fade(T_BC + 0.5, OUT, DUR, f=0.2)))
kx, ky = [], []
seg_t = (3.0 - 0.6) / (len(path_pts) - 1)
for i, (x, y) in enumerate(path_pts):
    kx.append((T_BC + 0.6 + i * seg_t, x))
    ky.append((T_BC + 0.6 + i * seg_t, y))
agent = (
    f'<circle r="7" cx="{path_pts[0][0]}" cy="{path_pts[0][1]}" fill="{C["red"]}" stroke="#fff" stroke-width="2">'
    + anim("cx", kx, DUR, ease=False)
    + anim("cy", ky, DUR, ease=False)
    + "</circle>"
)
body.append(group(agent, anims=fade(T_BC + 0.5, OUT, DUR, f=0.2)))

# ---- right panel
RX = 288
body.append(text(RX, 76, "dataset size", size=11.5, fill=C["muted"], weight=600))
for n, t_in, t_out, lab in ((N1, 0.4, T_IT1_DROP + 0.3, "D₁"), (N2, T_IT1_DROP + 0.4, T_IT2_DROP + 0.3, "D₂"),
                            (N3, T_IT2_DROP + 0.4, OUT, "D₃")):
    body.append(group(text(RX, 102, f"|{lab}| = {n} transitions", size=15, fill=C["ink"], weight=700), anims=fade(t_in, t_out, DUR, f=0.3)))

p2 = (
    text(RX, 130, "Dual-RL learns w(a|s) = π*/μ;", size=11.5, fill=C["ink"])
    + text(RX, 146, "IDRL corrects it to the", size=11.5, fill=C["ink"])
    + text(RX, 162, "visitation ratio", size=11.5, fill=C["ink"])
    + text(RX, 182, "w(s,a) = w(s) · w(a|s)", size=13, fill=C["purple"], weight=700)
    + text(RX, 204, "transitions with w = 0", size=11.5, fill=C["red"], weight=700)
    + text(RX, 220, "are removed", size=11.5, fill=C["red"], weight=700)
)
body.append(group(p2, anims=fade(3.5, 7.0, DUR)))
p3 = (
    text(RX, 130, "Each round replaces the", size=11.5, fill=C["ink"])
    + text(RX, 146, "behavior distribution with the", size=11.5, fill=C["ink"])
    + text(RX, 162, "optimized one → a curriculum", size=11.5, fill=C["ink"])
    + text(RX, 178, "toward the optimal", size=11.5, fill=C["ink"])
    + text(RX, 194, "discriminator weight", size=11.5, fill=C["ink"])
    + text(RX, 216, "suboptimal detours removed", size=11.5, fill=C["red"], weight=700)
)
body.append(group(p3, anims=fade(7.3, 10.8, DUR)))
p4 = (
    text(RX, 130, "Discriminator-weighted BC:", size=11.5, fill=C["ink"])
    + text(RX, 152, "max E[ w(s,a) log π(a|s) ]", size=13, fill=C["purple"], weight=700)
    + text(RX, 176, "only expert-like transitions", size=11.5, fill=C["ink"])
    + text(RX, 192, "remain, so the policy does", size=11.5, fill=C["ink"])
    + text(RX, 208, "not average in bad modes", size=11.5, fill=C["ink"])
)
body.append(group(p4, anims=fade(11.1, OUT, DUR)))

legend = (
    f'<line x1="{RX}" y1="262" x2="{RX+22}" y2="262" stroke="{GREEN_DARK}" stroke-width="3"/>'
    + text(RX + 28, 266, "transition (darker = higher w)", size=10, fill=C["muted"])
    + f'<line x1="{RX}" y1="280" x2="{RX+22}" y2="280" stroke="{C["red"]}" stroke-width="3"/>'
    + text(RX + 28, 284, "flagged w = 0 / final policy", size=10, fill=C["muted"])
)
body.append(group(legend, anims=fade(0.5, OUT, DUR)))

svg = svg_doc(
    W,
    H,
    "".join(body),
    title="Iterative Dual-RL (IDRL)",
    desc="In a grid world, an offline dataset contains good, detouring and dead-end transitions. Each IDRL iteration runs "
    "Dual-RL, corrects the learned ratio into a state-action visitation ratio, and removes zero-weight transitions; after "
    "two iterations only near-optimal transitions remain and weighted behavior cloning recovers a path from start to goal.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes", N1, N2, N3)
