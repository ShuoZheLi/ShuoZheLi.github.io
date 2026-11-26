"""phi-Balancing for MoE: track population expert load with an EMA m, price experts by q = grad phi(m),
and use L_aux = sum_e q_e p_e (instead of ST-MoE's noisy batch frequencies f_e) to reach balanced experts."""

import math
import random
import sys

from svganim import C, anim, fade, text, group, svg_doc, caption_track

DUR = 16.0
W, H = 480, 300
OUT = 15.5
E = 6
STEP = 0.5  # one training step per 0.5 s of animation
ETA = 0.35

T1, T2, T3 = 3.6, 7.2, 10.8  # caption boundaries
T_BAL0, T_BAL1 = 11.0, 14.2  # router shifts toward uniform during step 4

M0 = [0.30, 0.22, 0.17, 0.13, 0.10, 0.08]
U = 1.0 / E

BASE_Y, SCALE = 254, 330.0  # bar baseline, px per unit load
BX0, BW, BSTEP = 34, 28, 39
ROUTER = (152, 70)


def bx(e):
    return BX0 + BSTEP * e


def bcx(e):
    return bx(e) + BW / 2


def mean_load(t):
    if t <= T_BAL0:
        a = 0.0
    elif t >= T_BAL1:
        a = 1.0
    else:
        u = (t - T_BAL0) / (T_BAL1 - T_BAL0)
        a = u * u * (3 - 2 * u)
    return [(1 - a) * m + a * U for m in M0]


rng = random.Random(7)
times = [round(STEP * k, 3) for k in range(int(DUR / STEP) + 1)]
batch = []
for t in times:
    mu = mean_load(t)
    raw = [max(0.02, m + rng.gauss(0, 0.035)) for m in mu]
    s = sum(raw)
    batch.append([r / s for r in raw])

ema = []
m = list(batch[0])
for p in batch:
    m = [(1 - ETA) * mi + ETA * pi for mi, pi in zip(m, p)]
    ema.append(list(m))

body = []
body.append(
    caption_track(
        [
            (0.0, T1 - 0.1, "1", "Router spreads tokens; mini-batch loads are noisy"),
            (T1, T2 - 0.1, "2", "Track the population load with an EMA m"),
            (T2, T3 - 0.1, "3", "Price each expert: q = ∇ϕ(m)"),
            (T3, OUT, "4", "Loss Σ q·p moves tokens to cheap experts"),
        ],
        DUR,
    )
)

# ---- left panel: router, bars, uniform line, expert chips
rx, ry = ROUTER
body.append(
    f'<rect x="{rx-44}" y="{ry-12}" width="88" height="24" rx="12" fill="{C["ink"]}"/>'
    + text(rx, ry + 4.5, "router", size=12, fill="#fff", weight=700, anchor="middle")
)
frame = f'<line x1="{bx(0)-10}" y1="{BASE_Y}" x2="{bx(E-1)+BW+10}" y2="{BASE_Y}" stroke="{C["muted"]}" stroke-width="1.2"/>'
uy = BASE_Y - U * SCALE
frame += (
    f'<line x1="{bx(0)-10}" y1="{uy:.1f}" x2="{bx(E-1)+BW+10}" y2="{uy:.1f}" stroke="{C["green"]}" '
    f'stroke-width="1.4" stroke-dasharray="5 4"/>'
)
body.append(frame)

vis_in, vis_out = 0.25, OUT

# batch-load bars (discrete jumps every step)
for e in range(E):
    hs = [(t, batch[k][e] * SCALE) for k, t in enumerate(times)]
    ys = [(t, BASE_Y - h) for t, h in hs]
    bar = (
        f'<rect x="{bx(e)}" y="{ys[0][1]:.1f}" width="{BW}" height="{hs[0][1]:.1f}" rx="3" fill="{C["blue_l"]}" '
        f'stroke="{C["blue"]}" stroke-width="1">'
        + anim("height", hs, DUR, discrete=True)
        + anim("y", ys, DUR, discrete=True)
        + "</rect>"
    )
    body.append(group(bar, anims=fade(vis_in, vis_out, DUR, f=0.3)))

# EMA marker (smooth)
for e in range(E):
    ys = [(t + STEP * 0.999, BASE_Y - ema[k][e] * SCALE) for k, t in enumerate(times) if t + STEP <= DUR]
    ys = [(0.0, BASE_Y - ema[0][e] * SCALE)] + ys
    mk = (
        f'<line x1="{bx(e)-5}" x2="{bx(e)+BW+5}" y1="{ys[0][1]:.1f}" y2="{ys[0][1]:.1f}" stroke="{C["purple"]}" '
        f'stroke-width="3.2" stroke-linecap="round">'
        + anim("y1", ys, DUR, ease=False)
        + anim("y2", ys, DUR, ease=False)
        + "</line>"
    )
    body.append(group(mk, anims=fade(T1 + 0.2, OUT, DUR, f=0.4)))


# expert chips (colored by price from step 3)
def price_color(mval):
    dev = (mval - U) / U  # >0 over-used
    if dev >= 0:
        k = min(1.0, dev / 0.8)
        base, tgt = (255, 255, 255), (252, 165, 165)
    else:
        k = min(1.0, -dev / 0.5)
        base, tgt = (255, 255, 255), (134, 239, 172)
    c = tuple(round(b + (g - b) * k) for b, g in zip(base, tgt))
    return "#%02x%02x%02x" % c


for e in range(E):
    cols = [(0.0, "#ffffff"), (T2 - 0.05, "#ffffff")]
    for k, t in enumerate(times):
        if t >= T2:
            cols.append((t, price_color(ema[k][e])))
    cols.append((OUT + 0.3, cols[-1][1]))
    chip = (
        f'<rect x="{bx(e)-2}" y="{BASE_Y+6}" width="{BW+4}" height="20" rx="10" fill="#ffffff" stroke="{C["line"]}">'
        + anim("fill", cols, DUR, ease=False)
        + "</rect>"
        + text(bcx(e), BASE_Y + 20, f"E{e+1}", size=11, fill=C["ink"], weight=700, anchor="middle")
    )
    body.append(chip)

# price arrows (step 3 only): up-price on busy experts, down-price on idle experts
k3 = times.index(9.0)
for e in range(E):
    dev = ema[k3][e] - U
    if abs(dev) < 0.025:
        continue
    y_top = BASE_Y - max(ema[k3][e], max(batch[j][e] for j in range(k3 - 6, k3 + 4))) * SCALE - 8
    if dev > 0:
        s = text(bcx(e), y_top, "q↑", size=12, fill=C["red"], weight=700, anchor="middle")
    else:
        s = text(bcx(e), y_top, "q↓", size=12, fill=C["green"], weight=700, anchor="middle")
    body.append(group(s, anims=fade(T2 + 0.4, T3 + 0.9, DUR)))

# tokens flying from router into experts
trng = random.Random(3)
tok_times = [0.35 + 0.2 * i for i in range(int((OUT - 1.2) / 0.2))]
for i, t0 in enumerate(tok_times):
    mu = mean_load(t0 + 0.6)
    r = trng.random()
    acc, e = 0.0, 0
    for j, pj in enumerate(mu):
        acc += pj
        if r <= acc:
            e = j
            break
    x0 = rx + trng.uniform(-24, 24)
    y0 = ry + 12
    x1 = bcx(e) + trng.uniform(-6, 6)
    y1 = 112
    t1 = t0 + 0.75
    dot = (
        f'<circle r="3.4" cx="{x0:.1f}" cy="{y0}" fill="{C["blue"]}" opacity="0">'
        + anim("cx", [(t0, x0), (t1, x1)], DUR, ease=False)
        + anim("cy", [(t0, y0), (t1, y1)], DUR, ease=False)
        + anim("opacity", [(0, 0), (t0, 0), (t0 + 0.08, 0.9), (t1 - 0.15, 0.9), (t1, 0)], DUR, ease=False)
        + "</circle>"
    )
    body.append(dot)

# ---- right panel
RX = 292
body.append(f'<line x1="{RX-12}" y1="58" x2="{RX-12}" y2="284" stroke="{C["line"]}"/>')


def para(lines, t_in, t_out, y0=78, dy=17):
    out = ""
    y = y0
    for s, kind in lines:
        if kind == "eq":
            out += text(RX, y + 2, s, size=13, fill=C["purple"], weight=700)
            y += dy + 5
        elif kind == "b":
            out += text(RX, y, s, size=11.5, fill=C["ink"], weight=700)
            y += dy
        elif kind == "r":
            out += text(RX, y, s, size=11.5, fill=C["red"], weight=700)
            y += dy
        elif kind == "g":
            out += text(RX, y, s, size=11.5, fill=C["green"], weight=700)
            y += dy
        else:
            out += text(RX, y, s, size=11.5, fill=C["ink"])
            y += dy
    body.append(group(out, anims=fade(t_in, t_out, DUR)))


para(
    [
        ("ST-MoE balances each batch:", "b"),
        ("L = Σₑ fₑ · pₑ", "eq"),
        ("fₑ = hard token counts in", ""),
        ("this mini-batch → noisy and", ""),
        ("biased w.r.t. the population", ""),
        ("goal of balanced usage", ""),
    ],
    0.2,
    T1 - 0.1,
)
para(
    [
        ("Soft batch load pₜ (bars) →", "b"),
        ("m ← (1−η) m + η pₜ", "eq"),
        ("a stable estimate of the", ""),
        ("population load", ""),
        ("p̄ = E_x[ p(x) ] over all data", ""),
        ("(purple marks = m)", ""),
    ],
    T1,
    T2 - 0.1,
)
para(
    [
        ("ϕ strictly convex, symmetric", "b"),
        ("→ minimized at uniform load", ""),
        ("dual price q = ∇ϕ(m)", "eq"),
        ("neg. entropy: q = log m + 1", ""),
        ("busy expert → high price", "r"),
        ("idle expert → low price", "g"),
    ],
    T2,
    T3 - 0.1,
)
para(
    [
        ("Auxiliary loss (stop-grad m):", "b"),
        ("L = Σₑ ∇ϕ(m)ₑ · pₑ", "eq"),
        ("the only change to ST-MoE:", ""),
        ("fₑ  →  ∇ϕ(m)ₑ", "b"),
        ("routing drifts to uniform", "g"),
        ("with negligible overhead", ""),
    ],
    T3,
    OUT,
)

legend = (
    f'<rect x="{RX}" y="250" width="14" height="10" rx="2" fill="{C["blue_l"]}" stroke="{C["blue"]}"/>'
    + text(RX + 20, 259, "batch load pₜ", size=10, fill=C["muted"])
    + f'<line x1="{RX+92}" y1="255" x2="{RX+108}" y2="255" stroke="{C["purple"]}" stroke-width="3"/>'
    + text(RX + 113, 259, "EMA m", size=10, fill=C["muted"])
    + f'<line x1="{RX}" y1="275" x2="{RX+14}" y2="275" stroke="{C["green"]}" stroke-width="1.4" stroke-dasharray="4 3"/>'
    + text(RX + 20, 279, "uniform 1/E", size=10, fill=C["muted"])
)
body.append(legend)

svg = svg_doc(
    W,
    H,
    "".join(body),
    title="ϕ-Balancing for Mixture-of-Experts training",
    desc="A router sends tokens to six experts. Mini-batch expert loads jump around; an exponential moving average m "
    "tracks the population load. Each expert gets a price q = ∇ϕ(m), high for busy and low for idle experts, and the "
    "auxiliary loss Σ q·p shifts routing until every expert receives about 1/E of the tokens.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes")
