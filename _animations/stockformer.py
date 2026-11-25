"""Stockformer: multivariate correlated-stock input -> 1D-CNN token embedding -> ProbSparse attention with distilling -> tanh position."""

import math
import sys

import numpy as np
from svganim import C, anim, anim_tf, fade, text, group, svg_doc, caption_track, arrow_marker

DUR = 16.0
W, H = 480, 300
OUT = 15.5
rng = np.random.default_rng(11)

body = []
defs = arrow_marker("ak", C["muted"]) + arrow_marker("ap", C["purple"])

body.append(
    caption_track(
        [
            (0.0, 3.35, "1", "Input: hourly returns of correlated stocks"),
            (3.45, 7.05, "2", "1D-CNN token embedding per time step"),
            (7.15, 10.85, "3", "Encoder: ProbSparse attention + distilling"),
            (10.95, OUT, "4", "Next-hour position = tanh(output), loss = −ROI"),
        ],
        DUR,
    )
)

# ---------------- left: four correlated stocks (oil industry example from the paper)
TICK = ["XOM", "CVX", "COP", "BP"]
LX0, LX1 = 58, 222
N = 90
xs = np.linspace(LX0, LX1, N)
common = np.cumsum(rng.normal(0, 1, N))
common = (common - common.mean()) / common.std()
lanes = []
for j in range(4):
    lag = j * 2
    s = np.roll(common, lag) * 0.8 + 0.45 * np.cumsum(rng.normal(0, 0.35, N)) / 3
    s = (s - s.mean()) / (s.std() + 1e-9)
    lanes.append(s)
LY = [92, 134, 176, 218]
for j, (yc, s) in enumerate(zip(LY, lanes)):
    pts = [(x, yc - 9 * v) for x, v in zip(xs, s)]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    L = sum(math.dist(pts[i], pts[i + 1]) for i in range(N - 1))
    col = C["blue"] if j == 0 else C["muted"]
    wdt = 2.2 if j == 0 else 1.4
    line = (
        f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{wdt}" stroke-dasharray="{L:.1f} {L:.1f}">'
        + anim("stroke-dashoffset", [(0.3 + 0.2 * j, L), (2.2 + 0.2 * j, 0)], DUR, ease=False)
        + "</path>"
    )
    lab = text(LX0 - 6, yc + 4, TICK[j], size=11.5, fill=col, weight=700, anchor="end")
    body.append(group(line + lab, anims=fade(0.2, OUT, DUR)))
body.append(group(text(LX0, 246, "peers are Granger-causal for target XOM", size=10, fill=C["muted"]), anims=fade(1.5, 7.0, DUR)))

# sliding input window over the last n hours
WX0 = LX1 - 62
win = f'<rect x="{WX0}" y="72" width="64" height="164" rx="6" fill="{C["amber"]}" fill-opacity="0.08" stroke="{C["amber"]}" stroke-width="1.6" stroke-dasharray="5 3"/>'
win += text(WX0 + 32, 66, "last n hours", size=10.5, fill=C["amber"], weight=700, anchor="middle")
body.append(group(win, anims=fade(2.4, OUT, DUR)))

# next-hour prediction on the target lane (phase 4)
nx = LX1 + 14
ny_now = LY[0] - 9 * lanes[0][-1]
pred = (
    f'<line x1="{LX1}" y1="{ny_now:.1f}" x2="{nx}" y2="{ny_now-14:.1f}" stroke="{C["green"]}" stroke-width="2.2" stroke-dasharray="3 2"/>'
    + f'<circle cx="{nx}" cy="{ny_now-14:.1f}" r="4.5" fill="{C["green"]}"/>'
    + text(nx + 2, ny_now - 22, "t+1 ↑", size=11, fill=C["green"], weight=700, anchor="middle")
)
body.append(group(pred, anims=fade(11.4, OUT, DUR)))

RX = 240
body.append(f'<line x1="{RX}" y1="58" x2="{RX}" y2="286" stroke="{C["line"]}"/>')

# ---------------- phase 2: 1D-CNN over the window (4 channels x 12 steps)
GX0, GY0, CS, NT = 262, 82, 14, 12
grid = ""
vals = rng.normal(0, 1, (4, NT))
for j in range(4):
    for t in range(NT):
        v = vals[j, t]
        col = C["green"] if v > 0 else C["red"]
        grid += f'<rect x="{GX0 + t*CS}" y="{GY0 + j*CS}" width="{CS-1}" height="{CS-1}" fill="{col}" fill-opacity="{min(0.15 + 0.3*abs(v), 0.85):.2f}"/>'
    grid += text(GX0 - 4, GY0 + j * CS + 10, TICK[j], size=8.5, fill=C["muted"], anchor="end")
grid += text(GX0, GY0 - 6, "window: 4 securities × n steps", size=10.5, fill=C["muted"])
body.append(group(grid, anims=fade(3.5, 7.05, DUR)))
# kernel (size 3) sliding over time
kx = [(4.0 + 0.24 * t, GX0 + (t - 1) * CS) for t in range(NT)]
kern = (
    f'<rect x="0" y="{GY0-2}" width="{3*CS+1}" height="{4*CS+3}" rx="3" fill="none" stroke="{C["purple"]}" stroke-width="2.2"/>'
)
kern_g = (
    f'<g>{anim_tf("translate", [(t, (x, 0)) for t, x in kx], DUR, ease=False)}{kern}</g>'
)
body.append(group(kern_g, anims=fade(3.95, 7.0, DUR, f=0.2)))
body.append(group(text(GX0 + NT * CS + 4, GY0 + 34, "k = 3,", size=10, fill=C["purple"], weight=700), anims=fade(4.0, 7.0, DUR)))
body.append(group(text(GX0 + NT * CS + 4, GY0 + 46, "circular", size=10, fill=C["purple"]), anims=fade(4.0, 7.0, DUR)))
body.append(group(text(GX0 + NT * CS + 4, GY0 + 58, "padding", size=10, fill=C["purple"]), anims=fade(4.0, 7.0, DUR)))

# embedded tokens row
EY = 160
for t in range(NT):
    tok = f'<rect x="{GX0 + t*CS}" y="{EY}" width="{CS-1}" height="{CS-1}" rx="2" fill="{C["purple"]}" fill-opacity="0.75"/>'
    body.append(group(tok, anims=fade(4.15 + 0.24 * t, 10.6, DUR, f=0.2)))
body.append(group(text(GX0, EY + 26, "tokens (sequence length kept)", size=10.5, fill=C["purple"]), anims=fade(5.5, 7.0, DUR)))

# ---------------- phase 3: ProbSparse attention arcs + distilling pyramid
active = [2, 6, 9]  # only a few "active" queries attend in ProbSparse attention
arcs = ""
for q in active:
    for kk in (0, 4, 8, 11):
        if kk == q:
            continue
        x1 = GX0 + q * CS + CS / 2
        x2 = GX0 + kk * CS + CS / 2
        h = 10 + abs(x2 - x1) * 0.35
        arcs += f'<path d="M{x1},{EY-1} Q{(x1+x2)/2},{EY-1-h} {x2},{EY-1}" fill="none" stroke="{C["purple"]}" stroke-width="1.1" stroke-opacity="0.7"/>'
    arcs += f'<rect x="{GX0 + q*CS - 1}" y="{EY-1}" width="{CS+1}" height="{CS+1}" rx="3" fill="none" stroke="{C["amber"]}" stroke-width="2"/>'
body.append(group(arcs, anims=fade(7.4, 10.6, DUR)))
pnote = (
    text(GX0, 88, "only top-u “active” queries attend:", size=10.5, fill=C["ink"], weight=600)
    + text(GX0, 101, "O(L log L) instead of O(L²)", size=10.5, fill=C["ink"])
)
body.append(group(pnote, anims=fade(7.6, 10.6, DUR)))
# distilling: 12 -> 6 -> 3 (max-pool, stride 2)
rows = [(12, EY), (6, EY + 36), (3, EY + 72)]
for (n_prev, y_prev), (n, y), t0 in zip(rows[:-1], rows[1:], (8.3, 9.2)):
    w_tok = CS * 2 ** (rows.index((n, y)))
    x0 = GX0
    seg = ""
    for t in range(n):
        x = x0 + t * w_tok
        seg += f'<rect x="{x}" y="{y}" width="{w_tok-1}" height="{CS-1}" rx="2" fill="{C["purple"]}" fill-opacity="0.85"/>'
        seg += f'<path d="M{x + w_tok/4},{y_prev+CS} L{x + w_tok/2},{y-1} L{x + 3*w_tok/4},{y_prev+CS}" fill="none" stroke="{C["purple"]}" stroke-width="0.9" stroke-opacity="0.6"/>'
    body.append(group(seg, anims=fade(t0, 10.6, DUR)))
body.append(group(text(GX0, EY + 104, "distilling: max-pool halves the length", size=10, fill=C["purple"], weight=700), anims=fade(8.4, 10.6, DUR)))

# ---------------- phase 4: position + cumulative ROI
ox = RX + 14
outp = (
    f'<rect x="{ox}" y="74" width="214" height="54" rx="10" fill="{C["green_l"]}" stroke="{C["green"]}"/>'
    + text(ox + 12, 96, "output → position = tanh(out)", size=12, fill=C["green"], weight=700)
    + text(ox + 12, 116, "+0.6 → long 60% of the portfolio", size=11.5, fill=C["ink"])
    + text(ox, 152, "trained to maximize realized return:", size=11, fill=C["ink"], weight=600)
    + text(ox, 170, "loss = −exp( Σₜ tanh(outₜ) · ℓₜ )", size=12.5, fill=C["purple"], weight=700)
    + text(ox, 188, "(not MSE on the price)", size=11, fill=C["muted"])
)
ex0, ex1, ey0, ey1 = ox, ox + 208, 206, 266
eq = np.linspace(0, 1, 50) + 0.06 * np.cumsum(np.random.default_rng(5).normal(0, 0.3, 50))
eq = (eq - eq.min()) / (eq.max() - eq.min())
epts = [(ex0 + (ex1 - ex0) * i / 49, ey1 - (ey1 - ey0) * v) for i, v in enumerate(eq)]
ed = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in epts)
EL = sum(math.dist(epts[i], epts[i + 1]) for i in range(49))
outp += (
    f'<line x1="{ex0}" y1="{ey1}" x2="{ex1}" y2="{ey1}" stroke="{C["faint"]}"/>'
    + text(ex1, ey1 + 14, "cumulative ROI →", size=10, fill=C["muted"], anchor="end")
    + f'<path d="{ed}" fill="none" stroke="{C["green"]}" stroke-width="2" stroke-dasharray="{EL:.1f} {EL:.1f}">'
    + anim("stroke-dashoffset", [(11.6, EL), (15.0, 0)], DUR, ease=False)
    + "</path>"
)
body.append(group(outp, anims=fade(11.0, OUT, DUR)))

svg = svg_doc(
    W,
    H,
    "".join(body),
    defs=defs,
    title="Stockformer: Transformer-based time-series forecasting for stock",
    desc="Hourly returns of several correlated oil stocks enter a sliding window; a 1D-CNN with kernel size 3 embeds each "
    "time step; an encoder with ProbSparse attention lets only a few active queries attend and max-pool distilling halves "
    "the sequence layer by layer; the output is turned into a position with tanh and the model is trained to maximize "
    "realized return rather than price error.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes")
