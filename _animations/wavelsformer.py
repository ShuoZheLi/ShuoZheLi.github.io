"""WaveLSFormer: learnable wavelet filter bank -> low-guided high-frequency injection -> Transformer -> long/short position."""

import math
import sys

import numpy as np
from svganim import C, anim, fade, text, group, svg_doc, caption_track, arrow_marker

DUR = 16.0
W, H = 480, 300
OUT = 15.5
rng = np.random.default_rng(7)

LX0, LX1 = 30, 262
N = 140
xs = np.linspace(LX0, LX1, N)
tt = np.linspace(0, 1, N)
trend = 0.9 * np.sin(2 * math.pi * 1.1 * tt + 0.4) + 0.5 * np.sin(2 * math.pi * 0.45 * tt + 1.0)
noise = rng.normal(0, 0.55, N)
sig = trend + noise
# a simple smoothing filter stands in for the learned low-pass branch
k = np.exp(-0.5 * (np.arange(-9, 10) / 3.6) ** 2)
k /= k.sum()
pad = np.pad(sig, 9, mode="edge")
low = np.convolve(pad, k, mode="valid")
high = sig - low


def path(vals, yc, amp):
    pts = [(x, yc - amp * v) for x, v in zip(xs, vals)]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts), sum(
        math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)
    )


def drawn(d, L, color, width, t0, t1, t_out, dash_in=True, opacity=1.0):
    el = (
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" '
        f'stroke-dasharray="{L:.1f} {L:.1f}" opacity="{opacity}">'
        + anim("stroke-dashoffset", [(t0, L), (t1, 0)], DUR, ease=False)
        + "</path>"
    )
    return group(el, anims=fade(t0, t_out, DUR, f=0.15))


body = []
defs = arrow_marker("aw", C["muted"]) + arrow_marker("abl", C["blue"]) + arrow_marker("aor", C["orange"])

body.append(
    caption_track(
        [
            (0.0, 3.15, "1", "Noisy hourly returns of related assets"),
            (3.25, 6.55, "2", "Learnable wavelet filters split low / high frequency"),
            (6.65, 10.25, "3", "LGHI: low-band attention injects high-band cues"),
            (10.35, OUT, "4", "Transformer → long/short position, trained on returns"),
        ],
        DUR,
    )
)

Y0, Y1, Y2 = 94, 180, 242
# lane labels
body.append(group(text(LX0, Y0 - 26, "log returns xₜ", size=11.5, fill=C["muted"], weight=600), anims=fade(0.2, OUT, DUR)))
# related assets (faint) + target asset
for j, off in enumerate((0.35, -0.3)):
    other = trend * (0.8 + 0.2 * j) + rng.normal(0, 0.55, N)
    d, L = path(other, Y0 + 3 * (j + 1), 12)
    body.append(drawn(d, L, C["faint"], 1, 0.3, 2.4, OUT, opacity=0.55))
d0, L0 = path(sig, Y0, 12)
body.append(drawn(d0, L0, C["ink"], 1.5, 0.3, 2.6, OUT))

# filters
FX = LX0 + 4
filt = (
    f'<rect x="{FX}" y="{Y0+24}" width="92" height="20" rx="10" fill="{C["blue_l"]}" stroke="{C["blue"]}"/>'
    + text(FX + 46, Y0 + 38, "low-pass hₗ(θ)", size=11, fill=C["blue"], weight=700, anchor="middle")
    + f'<rect x="{FX+104}" y="{Y0+24}" width="96" height="20" rx="10" fill="{C["orange_l"]}" stroke="{C["orange"]}"/>'
    + text(FX + 152, Y0 + 38, "high-pass hₕ(θ)", size=11, fill=C["orange"], weight=700, anchor="middle")
)
body.append(group(filt, anims=fade(3.3, OUT, DUR)))
d1, L1 = path(low, Y1, 12)
d2, L2 = path(high, Y2, 12)
body.append(drawn(d1, L1, C["blue"], 2.4, 3.8, 5.4, OUT))
body.append(drawn(d2, L2, C["orange"], 1.4, 4.0, 5.6, OUT))
body.append(group(text(LX0, Y1 - 22, "low band L (trend)", size=11.5, fill=C["blue"], weight=600), anims=fade(3.8, OUT, DUR)))
body.append(group(text(LX0, Y2 - 22, "high band H (residual)", size=11.5, fill=C["orange"], weight=600), anims=fade(4.0, OUT, DUR)))

# fused low band Y = L + beta * Z (phase 3): a slightly sharper purple line
fused = low + 0.35 * np.convolve(np.pad(high, 2, mode="edge"), np.ones(5) / 5, mode="valid")
d3, L3 = path(fused, Y1, 12)
body.append(drawn(d3, L3, C["purple"], 1.8, 8.6, 9.8, OUT))

RX = 284
body.append(f'<line x1="{RX-8}" y1="58" x2="{RX-8}" y2="286" stroke="{C["line"]}"/>')

# ---- phase 2 panel: frequency responses
fx0, fx1, fy0, fy1 = RX + 14, RX + 176, 86, 176
om = np.linspace(0, 1, 60)
lowr = 1 / (1 + np.exp((om - 0.42) * 16))
highr = 1 / (1 + np.exp(-(om - 0.58) * 16))


def resp(vals):
    return "M" + " L".join(f"{fx0 + (fx1-fx0)*o:.1f},{fy1 - (fy1-fy0)*v:.1f}" for o, v in zip(om, vals))


fr = (
    f'<line x1="{fx0}" y1="{fy1}" x2="{fx1+6}" y2="{fy1}" stroke="{C["faint"]}" marker-end="url(#aw)"/>'
    + f'<line x1="{fx0}" y1="{fy1}" x2="{fx0}" y2="{fy0-8}" stroke="{C["faint"]}" marker-end="url(#aw)"/>'
    + f'<path d="{resp(lowr)}" fill="none" stroke="{C["blue"]}" stroke-width="2.4"/>'
    + f'<path d="{resp(highr)}" fill="none" stroke="{C["orange"]}" stroke-width="2.4"/>'
    + text(fx0 + 4, fy0 - 2, "|H(ω)| = |rFFT(θ)|", size=11, fill=C["muted"])
    + text(fx1 + 2, fy1 + 15, "frequency ω", size=10.5, fill=C["muted"], anchor="end")
    + text(RX + 2, 210, "FIR kernels θ are learned end", size=11, fill=C["ink"])
    + text(RX + 2, 226, "to end; spectral regularizers", size=11, fill=C["ink"])
    + text(RX + 2, 242, "keep the two bands separated", size=11, fill=C["ink"])
)
body.append(group(fr, anims=fade(4.2, 6.55, DUR)))

# ---- phase 3 panel: LGHI
hm_x, hm_y, cs = RX + 10, 84, 13
heat = ""
A = np.abs(rng.normal(0, 1, (5, 5))) + np.eye(5) * 1.6
A = A / A.sum(1, keepdims=True)
for i in range(5):
    for j in range(5):
        a = float(A[i, j]) / float(A.max())
        heat += f'<rect x="{hm_x + j*cs}" y="{hm_y + i*cs}" width="{cs-1}" height="{cs-1}" fill="{C["blue"]}" fill-opacity="{0.12 + 0.85*a:.2f}"/>'
lg = (
    heat
    + text(hm_x + 32, hm_y + 82, "A(L) from", size=11, fill=C["blue"], weight=700, anchor="middle")
    + text(hm_x + 32, hm_y + 95, "low band only", size=11, fill=C["blue"], anchor="middle")
    + text(hm_x + 78, hm_y + 38, "×", size=20, fill=C["ink"], anchor="middle")
)
vx = hm_x + 94
for i in range(5):
    v = 0.3 + 0.7 * abs(math.sin(i * 1.7 + 0.5))
    lg += f'<rect x="{vx}" y="{hm_y + i*cs}" width="{cs*1.6:.1f}" height="{cs-1}" fill="{C["orange"]}" fill-opacity="{v:.2f}"/>'
lg += text(vx + 10, hm_y + 82, "H Wᵥ", size=11, fill=C["orange"], weight=700, anchor="middle")
lg += text(vx + 10, hm_y + 95, "values", size=11, fill=C["orange"], anchor="middle")
lg += text(vx + 46, hm_y + 38, "= Z", size=14, fill=C["ink"], weight=700, anchor="middle")
lg += (
    f'<rect x="{RX+2}" y="226" width="182" height="34" rx="8" fill="{C["purple_l"]}" stroke="{C["purple"]}"/>'
    + text(RX + 93, 248, "Y = L + σ(γ) · Z", size=14, fill=C["purple"], weight=700, anchor="middle")
    + text(RX + 2, 280, "stable trend + gated high-band cues", size=10.5, fill=C["muted"])

)
body.append(group(lg, anims=fade(6.7, 10.25, DUR)))
# arrows from lanes into LGHI panel
arr = (
    f'<path d="M{LX1+4},{Y1-6} C {RX-4},{Y1-30} {RX-14},{hm_y+40} {hm_x-4},{hm_y+32}" fill="none" stroke="{C["blue"]}" stroke-width="1.4" marker-end="url(#abl)"/>'
    + f'<path d="M{LX1+4},{Y2-8} C {LX1+40},{Y2-50} {vx+10},{hm_y+150} {vx+10},{hm_y+102}" fill="none" stroke="{C["orange"]}" stroke-width="1.4" marker-end="url(#aor)"/>'
)
body.append(group(arr, anims=fade(7.2, 10.25, DUR)))
body.append(group(text(LX1, Y1 + 30, "fused Y", size=11, fill=C["purple"], weight=700, anchor="end"), anims=fade(9.0, OUT, DUR)))

# ---- phase 4 panel: Transformer -> position gauge + equity curve
tb = (
    f'<rect x="{RX+2}" y="70" width="182" height="26" rx="8" fill="{C["gray_l"]}" stroke="{C["faint"]}"/>'
    + text(RX + 93, 87, "Transformer encoder", size=12, fill=C["ink"], weight=700, anchor="middle")
    + f'<line x1="{RX+93}" y1="97" x2="{RX+93}" y2="110" stroke="{C["muted"]}" marker-end="url(#aw)"/>'
)
gcx, gcy, gr = RX + 93, 160, 44
gauge = (
    f'<path d="M{gcx-gr},{gcy} A{gr},{gr} 0 0 1 {gcx+gr},{gcy}" fill="none" stroke="{C["line"]}" stroke-width="10"/>'
    + f'<path d="M{gcx-gr},{gcy} A{gr},{gr} 0 0 1 {gcx},{gcy-gr}" fill="none" stroke="{C["red_l"]}" stroke-width="10"/>'
    + f'<path d="M{gcx},{gcy-gr} A{gr},{gr} 0 0 1 {gcx+gr},{gcy}" fill="none" stroke="{C["green_l"]}" stroke-width="10"/>'
    + text(gcx - gr, gcy + 15, "short", size=10.5, fill=C["red"], weight=700, anchor="middle")
    + text(gcx + gr, gcy + 15, "long", size=10.5, fill=C["green"], weight=700, anchor="middle")
    + text(gcx, gcy + 30, "position w = tanh(p/2) ∈ [−1, 1]", size=10.5, fill=C["ink"], weight=600, anchor="middle")
)
# needle angle: 0 deg = straight up; rotate between -70 (short) and +70 (long)
ang = [(10.6, 0), (11.3, 55), (12.1, -40), (12.9, 35), (13.6, 62), (14.4, -25), (15.2, 20), (OUT, 0)]
needle = (
    f'<g><line x1="{gcx}" y1="{gcy}" x2="{gcx}" y2="{gcy-gr+8}" stroke="{C["ink"]}" stroke-width="3" stroke-linecap="round"/>'
    f'<circle cx="{gcx}" cy="{gcy}" r="5" fill="{C["ink"]}"/>'
    + f'<animateTransform attributeName="transform" type="rotate" dur="{DUR}s" repeatCount="indefinite" '
    + 'keyTimes="' + ";".join(f"{t/DUR:.4f}" for t in [0] + [a for a, _ in ang] + [DUR]) + '" '
    + 'values="' + ";".join(f"{v} {gcx} {gcy}" for v in [0] + [b for _, b in ang] + [0]) + '"/></g>'
)
ex0, ex1, ey0, ey1 = RX + 8, RX + 180, 220, 262
eq = np.linspace(0, 1, 60) ** 1.1 + 0.05 * np.cumsum(np.random.default_rng(3).normal(0, 0.35, 60))
eq = (eq - eq.min()) / (eq.max() - eq.min())
epts = [(ex0 + (ex1 - ex0) * i / 59, ey1 - (ey1 - ey0) * v) for i, v in enumerate(eq)]
ed = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in epts)
EL = sum(math.dist(epts[i], epts[i + 1]) for i in range(59))
equity = (
    f'<line x1="{ex0}" y1="{ey1}" x2="{ex1}" y2="{ey1}" stroke="{C["faint"]}"/>'
    + text(ex0, ey0 - 8, "strategy equity", size=11, fill=C["muted"], weight=600)
    + f'<path d="{ed}" fill="none" stroke="{C["green"]}" stroke-width="2" stroke-dasharray="{EL:.1f} {EL:.1f}">'
    + anim("stroke-dashoffset", [(10.8, EL), (15.0, 0)], DUR, ease=False)
    + "</path>"
    + text(RX + 2, 282, "trained on return + Sharpe, not MSE", size=10.5, fill=C["ink"], weight=600)
)
body.append(group(tb + gauge + needle + equity, anims=fade(10.4, OUT, DUR)))

svg = svg_doc(
    W,
    H,
    "".join(body),
    defs=defs,
    title="WaveLSFormer: learnable wavelet Transformer for long-short trading",
    desc="Noisy hourly returns pass through a learnable low-pass and high-pass filter bank kept apart by spectral "
    "regularizers; low-guided high-frequency injection computes attention from the low band and injects gated "
    "high-band values; a Transformer outputs a long or short position trained directly on a risk-aware return objective.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes")
