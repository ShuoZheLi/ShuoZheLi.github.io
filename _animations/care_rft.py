"""CARE-RFT: skew reverse KL gives a one-sided bounded penalty (capped for upward moves, unbounded for depletion)."""

import math
import sys
from svganim import C, anim, fade, text, group, svg_doc, caption_track, arrow_marker

DUR = 16.0
W, H = 480, 300
OUT = 15.5
ALPHA = 0.25

body = []
defs = arrow_marker("am", C["muted"])

body.append(
    caption_track(
        [
            (0.0, 3.45, "1", "KL penalty on a token vs. how far it moved"),
            (3.55, 6.85, "2", "CARE-RFT caps it for increases, not decreases"),
            (6.95, 11.45, "3", "RFT on a correct but low-probability token"),
            (11.55, OUT, "", "CARE-RFT: reasoning gains, calibration kept"),
        ],
        DUR,
    )
)

# ---------------------------------------------------------------- phase A: coefficient plot
PX0, PX1 = 64, 296          # log r in [-3, 3]
PYT, PYB = 66, 248          # C in [-2.4, 4.2]
CMIN, CMAX = -2.4, 4.2


def px(lr):
    return PX0 + (lr + 3) / 6 * (PX1 - PX0)


def py(c):
    return PYT + (CMAX - c) / (CMAX - CMIN) * (PYB - PYT)


def c_rkl(lr):
    return 1 + lr


def c_srkl(lr):
    r = math.exp(lr)
    m = r / (ALPHA * r + 1 - ALPHA)
    return math.log(m) + 1 - ALPHA * m


N = 60
lrs = [-3 + 6 * i / N for i in range(N + 1)]
rkl_pts = [(px(l), py(max(c_rkl(l), CMIN))) for l in lrs]
srkl_pts = [(px(l), py(c_srkl(l))) for l in lrs]


def poly(pts):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def path_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


A_OUT = 6.85
axes = (
    f'<line x1="{PX0}" y1="{py(0)}" x2="{PX1+6}" y2="{py(0)}" stroke="{C["faint"]}" stroke-width="1" marker-end="url(#am)"/>'
    + f'<line x1="{px(0)}" y1="{PYB}" x2="{px(0)}" y2="{PYT-4}" stroke="{C["faint"]}" stroke-width="1" marker-end="url(#am)"/>'
    + text(PX1 + 4, py(0) + 16, "log πθ/πref", size=11, fill=C["muted"], anchor="end")
    + text(px(0) + 6, PYT + 4, "penalty strength", size=11, fill=C["muted"])
    + text(px(1.6), PYB + 2, "token got more likely →", size=10.5, fill=C["muted"], anchor="middle")
    + text(px(-1.6), PYB + 2, "← token got depleted", size=10.5, fill=C["muted"], anchor="middle")
)
body.append(group(axes, anims=fade(0.2, A_OUT, DUR)))

for pts, col, dash, t0, label, lab_xy in (
    (rkl_pts, C["faint"], "6 4", 0.5, "reverse KL", None),
    (srkl_pts, C["orange"], "", 1.5, "CARE-RFT (skew RKL)", None),
):
    L = path_len(pts)
    stroke = f'stroke-dasharray="{L:.0f}"' if not dash else ""
    if dash:
        el = (
            f'<path d="{poly(pts)}" fill="none" stroke="{col}" stroke-width="2.4" stroke-dasharray="{dash}" '
            f'stroke-linecap="round"/>'
        )
        body.append(group(el, anims=fade(t0, A_OUT, DUR, f=0.6)))
    else:
        el = (
            f'<path d="{poly(pts)}" fill="none" stroke="{col}" stroke-width="3" stroke-linecap="round" '
            f'stroke-dasharray="{L:.1f} {L:.1f}">'
            + anim("stroke-dashoffset", [(t0, L), (t0 + 1.2, 0)], DUR)
            + "</path>"
        )
        body.append(group(el, anims=fade(t0, A_OUT, DUR, f=0.2)))

# cap line
cap_y = py(math.log(1 / ALPHA))
cap = (
    f'<line x1="{px(0.2)}" y1="{cap_y}" x2="{PX1}" y2="{cap_y}" stroke="{C["orange"]}" stroke-width="1" stroke-dasharray="2 3"/>'
    + text(PX1 + 6, cap_y + 4, "cap = log(1/α)", size=11, fill=C["orange"], weight=700)
)
body.append(group(cap, anims=fade(3.6, A_OUT, DUR)))

# annotations (right side panel)
ann = (
    text(312, 92, "reverse KL keeps growing:", size=11.5, fill=C["muted"], weight=700)
    + text(312, 107, "pulls reward-aligned", size=11.5, fill=C["muted"])
    + text(312, 121, "gains back down", size=11.5, fill=C["muted"])
)
body.append(group(ann, anims=fade(1.2, A_OUT, DUR)))
ann2 = (
    text(312, 182, "CARE-RFT is bounded", size=11.5, fill=C["orange"], weight=700)
    + text(312, 197, "for increases → room", size=11.5, fill=C["orange"])
    + text(312, 211, "to learn new reasoning", size=11.5, fill=C["orange"])
)
body.append(group(ann2, anims=fade(3.9, A_OUT, DUR)))
ann3 = (
    text(70, 128, "both unbounded below:", size=11.5, fill=C["ink"], weight=700)
    + text(70, 142, "resist probability", size=11.5, fill=C["ink"])
    + text(70, 156, "depletion", size=11.5, fill=C["ink"])
    + f'<path d="M{px(-2.3)},162 L{px(-2.3)},{py(c_srkl(-2.3))-8}" stroke="{C["ink"]}" stroke-width="1.3" marker-end="url(#am)"/>'
)
body.append(group(ann3, anims=fade(5.0, A_OUT, DUR)))

# moving dots: sweep log r 0 -> 3 -> -3 -> 0
sweep = [(2.9, 0.0), (4.4, 2.9), (4.9, 2.9), (6.2, -2.9), (6.6, -2.9)]


def dot_track(fn, col, r):
    pts_x, pts_y = [], []
    # densify the sweep so the dot follows the curve
    dense = []
    for (ta, la), (tb, lb) in zip(sweep, sweep[1:]):
        steps = 18
        for k in range(steps):
            u = k / steps
            dense.append((ta + (tb - ta) * u, la + (lb - la) * u))
    dense.append(sweep[-1])
    for t, l in dense:
        pts_x.append((t, round(px(l), 2)))
        pts_y.append((t, round(py(max(fn(l), CMIN)), 2)))
    return (
        f'<circle r="{r}" fill="{col}" stroke="#fff" stroke-width="1.5" cx="{px(0)}" cy="{py(fn(0))}">'
        + anim("cx", pts_x, DUR, ease=False)
        + anim("cy", pts_y, DUR, ease=False)
        + "</circle>"
    )


body.append(group(dot_track(c_rkl, C["muted"], 5), anims=fade(2.8, 6.7, DUR, f=0.2)))
body.append(group(dot_track(c_srkl, C["orange"], 6), anims=fade(2.8, 6.7, DUR, f=0.2)))

# ---------------------------------------------------------------- phase B: token distributions
REF = [0.20, 0.35, 0.25, 0.20]
COLS = [
    ("no KL", [0.94, 0.02, 0.02, 0.02], C["red"], "reasoning ↑", "overconfident"),
    ("reverse KL", [0.30, 0.31, 0.22, 0.17], C["muted"], "calibrated", "gains limited"),
    ("CARE-RFT", [0.64, 0.14, 0.12, 0.10], C["orange"], "reasoning ↑", "calibrated"),
]
CXS = [92, 240, 388]
BASE = 214
SC = 118.0
BWD, BG = 19, 7
TB0, TB1 = 7.2, 11.2  # RFT dynamics
TOK = ["✓", "b", "c", "d"]
for (name, fin, col, v1, v2), cx in zip(COLS, CXS):
    g = ""
    g += text(cx, 72, name, size=13.5, fill=col if name != "reverse KL" else C["ink"], weight=700, anchor="middle")
    g += f'<line x1="{cx-54}" y1="{BASE}" x2="{cx+54}" y2="{BASE}" stroke="{C["faint"]}"/>'
    x0 = cx - (4 * BWD + 3 * BG) / 2
    for k in range(4):
        x = x0 + k * (BWD + BG)
        fill = C["green"] if k == 0 else "#94a3b8"
        h0, h1 = REF[k] * SC, fin[k] * SC
        g += (
            f'<rect x="{x}" y="{BASE-h0}" width="{BWD}" height="{h0}" rx="2" fill="{fill}">'
            + anim("height", [(TB0 + 0.4, h0), (TB1, h1), (OUT, h1), (OUT + 0.4, h0)], DUR)
            + anim("y", [(TB0 + 0.4, BASE - h0), (TB1, BASE - h1), (OUT, BASE - h1), (OUT + 0.4, BASE - h0)], DUR)
            + "</rect>"
        )
        # reference outline (dashed)
        g += (
            f'<rect x="{x-1.5}" y="{BASE-h0}" width="{BWD+3}" height="{h0}" rx="2" fill="none" stroke="{C["ink"]}" '
            f'stroke-width="1.1" stroke-dasharray="3 2"/>'
        )
        g += text(x + BWD / 2, BASE + 14, TOK[k], size=11.5, fill=C["green"] if k == 0 else C["muted"], weight=700, anchor="middle")
    body.append(group(g, anims=fade(7.0, OUT, DUR)))
    good1 = v1 in ("reasoning ↑",)
    good2 = v2 in ("calibrated",)
    verdict = text(cx, BASE + 36, v1, size=11.5, fill=C["green"] if good1 else C["red"], weight=700, anchor="middle")
    verdict += text(cx, BASE + 51, v2, size=11.5, fill=C["green"] if good2 else C["red"], weight=700, anchor="middle")
    body.append(group(verdict, anims=fade(11.5, OUT, DUR)))

legend = (
    f'<rect x="150" y="281" width="16" height="9" rx="2" fill="none" stroke="{C["ink"]}" stroke-dasharray="3 2"/>'
    + text(171, 289, "πref", size=11, fill=C["muted"])
    + f'<rect x="212" y="281" width="16" height="9" rx="2" fill="{C["green"]}"/>'
    + text(233, 289, "reward-aligned token", size=11, fill=C["muted"])
)
body.append(group(legend, anims=fade(7.2, 11.4, DUR)))

# step counter during RFT
cnt = text(470, 258, "RFT steps →", size=11, fill=C["muted"], anchor="end")
body.append(group(cnt, anims=fade(TB0 + 0.2, TB1, DUR)))

svg = svg_doc(
    W,
    H,
    "".join(body),
    defs=defs,
    title="CARE-RFT: confidence-anchored reinforcement finetuning",
    desc="The reverse-KL penalty keeps growing as a token becomes more likely than under the reference model, while "
    "CARE-RFT's skew reverse KL caps it at log(1/alpha) and keeps an unbounded penalty against probability depletion. "
    "During reinforcement finetuning, no KL over-sharpens the distribution, reverse KL suppresses the reward-aligned "
    "token, and CARE-RFT lets it grow while the rest of the distribution keeps its mass.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes")
