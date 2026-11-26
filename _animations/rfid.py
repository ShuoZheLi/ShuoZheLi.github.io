"""TIMU: rotation sensing with one passive RFID tag and one linearly polarized reader antenna. Polarization
mismatch makes RSS/phase periodic; matching an analytical model gives the rotation axis, peak counting the speed."""

import math
import random
import sys

import numpy as np

from svganim import C, anim, fade, text, group, svg_doc, caption_track

DUR = 16.0
W, H = 480, 300
OUT = 15.5
T1, T2, T3 = 3.6, 7.2, 10.8
PER = 1.6  # s per revolution (divides the 16 s loop) -> 37.5 RPM
NK = 64  # keyframes per revolution

BC, BR = (78.0, 150.0), 44.0  # ball center / radius on screen
ANT = (186.0, 150.0)
LAM, RB = 0.33, 0.11  # wavelength (915 MHz) and ball radius in m


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rot(v, a, th):
    a = unit(a)
    return v * math.cos(th) + np.cross(a, v) * math.sin(th) + a * np.dot(a, v) * (1 - math.cos(th))


A_TRUE = unit([0.30, 0.38, 0.875])
P0 = unit(np.cross(A_TRUE, [0, 1.0, 0]))
D0 = unit(np.cross(A_TRUE, P0))


def state(t, axis=A_TRUE):
    th = 2 * math.pi * t / PER
    return rot(P0, axis, th), rot(D0, axis, th)


def rss(d):
    return d[1] ** 4  # rho^2 with rho = cos^2(gamma), times tag gain ~ |d_perp|^4  ->  d_y^4


def phase(p, d):
    gamma = math.atan2(d[2], d[1])
    return (4 * math.pi * (1.0 - RB * p[0]) / LAM + 2 * gamma) % (2 * math.pi)


def scr(v, r=BR):
    return (BC[0] + r * v[0], BC[1] - r * v[1])


body = []
body.append(
    caption_track(
        [
            (0.0, T1 - 0.1, "1", "A battery-free RFID tag spins with the ball"),
            (T1, T2 - 0.1, "2", "Polarization mismatch γ shapes RSS and phase"),
            (T2, T3 - 0.1, "3", "Fit the signal model → rotation axis"),
            (T3, OUT, "4", "Count RSS peaks → rotation speed"),
        ],
        DUR,
    )
)

# ---------------------------------------------------------------- ball
body.append(
    f'<circle cx="{BC[0]}" cy="{BC[1]}" r="{BR}" fill="url(#rfBall)" stroke="#94a3b8" stroke-width="1.2"/>'
)
# surface dots rotating about the true axis (period PER)
e1 = unit(np.cross(A_TRUE, [1.0, 0, 0]))
e2 = np.cross(A_TRUE, e1)
dots = []
for lat in (-0.55, 0.0, 0.55):
    for k in range(8):
        ang = 2 * math.pi * k / 8 + lat
        v = A_TRUE * math.sin(lat) + math.cos(lat) * (math.cos(ang) * e1 + math.sin(ang) * e2)
        dots.append(unit(v))
kt = [PER * i / NK for i in range(NK + 1)]
for v0 in dots:
    xs, ys, ops = [], [], []
    for t in kt:
        v = rot(v0, A_TRUE, 2 * math.pi * t / PER)
        x, y = scr(v)
        xs.append((t, round(x, 1)))
        ys.append((t, round(y, 1)))
        ops.append((t, round(0.7 * max(0.0, v[2]) ** 0.7, 2)))
    body.append(
        f'<circle r="1.8" cx="{xs[0][1]}" cy="{ys[0][1]}" fill="#475569">'
        + anim("cx", xs, PER, ease=False)
        + anim("cy", ys, PER, ease=False)
        + anim("opacity", ops, PER, ease=False)
        + "</circle>"
    )

# axis lines: unknown (steps 1-2), candidates (step 3), estimated (step 4)


def axis_line(a, color, dash, width=1.6):
    a = unit(a)
    x1, y1 = scr(a, BR * 1.3)
    x2, y2 = scr(-a, BR * 1.3)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"{da}/>'


body.append(
    group(
        axis_line(A_TRUE, C["faint"], "4 3")
        + text(BC[0], BC[1] + BR + 26, "axis &amp; speed unknown", size=10.5, fill=C["muted"], weight=700, anchor="middle"),
        anims=fade(0.2, T2 - 0.1, DUR),
    )
)

# tag (dipole + chip), period PER
tx1, ty1, tx2, ty2, tcx, tcy, top = [], [], [], [], [], [], []
for t in kt:
    p, d = state(t)
    cx, cy = scr(p)
    dx, dy = d[0] * 11, -d[1] * 11
    tx1.append((t, round(cx - dx, 1)))
    ty1.append((t, round(cy - dy, 1)))
    tx2.append((t, round(cx + dx, 1)))
    ty2.append((t, round(cy + dy, 1)))
    tcx.append((t, round(cx - 2.5, 1)))
    tcy.append((t, round(cy - 2.5, 1)))
    top.append((t, 1.0 if p[2] > 0 else 0.3))
tag = (
    f'<g>{anim("opacity", top, PER, ease=False)}'
    f'<line x1="{tx1[0][1]}" y1="{ty1[0][1]}" x2="{tx2[0][1]}" y2="{ty2[0][1]}" stroke="{C["red"]}" stroke-width="3" stroke-linecap="round">'
    + anim("x1", tx1, PER, ease=False) + anim("y1", ty1, PER, ease=False)
    + anim("x2", tx2, PER, ease=False) + anim("y2", ty2, PER, ease=False)
    + "</line>"
    + f'<rect width="5" height="5" x="{tcx[0][1]}" y="{tcy[0][1]}" fill="#7f1d1d">'
    + anim("x", tcx, PER, ease=False) + anim("y", tcy, PER, ease=False)
    + "</rect></g>"
)
body.append(tag)
body.append(text(BC[0] - BR + 2, BC[1] - BR - 6, "ball + RFID tag", size=10.5, fill=C["red"], weight=700))

# ---------------------------------------------------------------- reader antenna + waves
ax, ay = ANT
ant = (
    f'<rect x="{ax-5}" y="{ay-30}" width="10" height="60" rx="2" fill="{C["ink"]}"/>'
    f'<line x1="{ax+14}" y1="{ay-20}" x2="{ax+14}" y2="{ay+20}" stroke="{C["blue"]}" stroke-width="2" '
    f'marker-start="url(#rfArr)" marker-end="url(#rfArr)"/>'
    + text(ax + 2, ay + 46, "reader antenna", size=10, fill=C["ink"], weight=700, anchor="middle")
    + text(ax + 2, ay + 58, "linear polarization ↕", size=10, fill=C["blue"], anchor="middle")
)
body.append(ant)
waves = ""
for k in range(3):
    off = k * 0.6
    waves += (
        f'<g opacity="0"><animate attributeName="opacity" dur="1.8s" begin="{off}s" repeatCount="indefinite" '
        f'keyTimes="0;0.1;0.8;1" values="0;0.8;0.15;0"/>'
        f'<animateTransform attributeName="transform" type="translate" dur="1.8s" begin="{off}s" '
        f'repeatCount="indefinite" values="0 0;-50 0"/>'
        f'<path d="M{ax-12},{ay-18} Q{ax-24},{ay} {ax-12},{ay+18}" fill="none" stroke="{C["blue"]}" stroke-width="1.5"/></g>'
    )
body.append(waves)

# ---------------------------------------------------------------- plots
PX0, PX1 = 238, 462
RY0, RY1 = 66, 118  # RSS
QY0, QY1 = 154, 198  # phase
T_W0, T_W1 = 3.6, 3.6 + 2 * PER  # data window = two revolutions
NS = 160
tw = [T_W0 + (T_W1 - T_W0) * i / NS for i in range(NS + 1)]
xw = [PX0 + (PX1 - PX0) * i / NS for i in range(NS + 1)]
RMAX = 0.8
rng = random.Random(2)
meas = [rss(state(t)[1]) + rng.gauss(0, 0.012) for t in tw]


def ry(v):
    return RY1 - (RY1 - RY0) * max(0.0, min(v, RMAX)) / RMAX


def qy(v):
    return QY1 - (QY1 - QY0) * v / (2 * math.pi)


frame = (
    f'<rect x="{PX0}" y="{RY0-4}" width="{PX1-PX0}" height="{RY1-RY0+8}" fill="{C["card"]}" stroke="{C["line"]}"/>'
    f'<rect x="{PX0}" y="{QY0-4}" width="{PX1-PX0}" height="{QY1-QY0+8}" fill="{C["card"]}" stroke="{C["line"]}"/>'
    + text(PX0, RY0 - 9, "RSS", size=10.5, fill=C["muted"], weight=700)
    + text(PX0, QY0 - 9, "phase (0–2π)", size=10.5, fill=C["muted"], weight=700)
    + text(PX1, RY0 - 9, "time →", size=9.5, fill=C["faint"], anchor="end")
)
body.append(frame)
meas_pts = " ".join(f"{x:.1f},{ry(v):.1f}" for x, v in zip(xw, meas))
# phase: split at wraps
segs, cur = [], []
prev = None
for t, x in zip(tw, xw):
    p, d = state(t)
    v = phase(p, d)
    if prev is not None and abs(v - prev) > math.pi:
        segs.append(cur)
        cur = []
    cur.append((x, qy(v)))
    prev = v
segs.append(cur)
ph = "".join(
    f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in s)}" fill="none" stroke="{C["teal"]}" stroke-width="1.6"/>'
    for s in segs if len(s) > 1
)
reveal = (
    f'<clipPath id="rfRev"><rect x="{PX0}" y="0" width="0" height="{H}">'
    + anim("width", [(0, 0), (T_W0, 0), (T_W1, PX1 - PX0), (OUT + 0.2, PX1 - PX0), (OUT + 0.3, 0)], DUR, ease=False)
    + "</rect></clipPath>"
)
traces = (
    reveal
    + '<g clip-path="url(#rfRev)">'
    + f'<polyline points="{meas_pts}" fill="none" stroke="{C["red"]}" stroke-width="1.8" stroke-linejoin="round"/>'
    + ph
    + "</g>"
)
body.append(group(traces, anims=fade(T_W0 - 0.1, OUT, DUR, f=0.2)))
pen = (
    f'<line x1="{PX0}" x2="{PX0}" y1="{RY0-4}" y2="{QY1+4}" stroke="{C["ink"]}" stroke-width="1" stroke-dasharray="2 2">'
    + anim("x1", [(0, PX0), (T_W0, PX0), (T_W1, PX1)], DUR, ease=False)
    + anim("x2", [(0, PX0), (T_W0, PX0), (T_W1, PX1)], DUR, ease=False)
    + "</line>"
)
body.append(group(pen, anims=fade(T_W0, T_W1 + 0.1, DUR, f=0.1)))

# ---------------------------------------------------------------- step 3: candidate axes vs model
cands = [
    (unit([0, 1.0, 0]), "#f59e0b", 7.4),
    (unit([1.0, 0.25, 0.2]), C["purple"], 8.3),
    (A_TRUE, C["green"], 9.2),
]
for a, col, t_in in cands:
    model = [rss(rot(D0, a, 2 * math.pi * t / PER)) for t in tw]
    err = math.sqrt(sum((m - v) ** 2 for m, v in zip(model, meas)) / len(model))
    pts_ = " ".join(f"{x:.1f},{ry(v):.1f}" for x, v in zip(xw, model))
    good = a is A_TRUE
    t_out = OUT if good else t_in + 0.85
    curve = f'<polyline points="{pts_}" fill="none" stroke="{col}" stroke-width="2" stroke-dasharray="5 3"/>'
    body.append(group(curve, anims=fade(t_in, t_out if not good else T3 + 0.2, DUR, f=0.25)))
    body.append(group(axis_line(a, col, "5 3", 2), anims=fade(t_in, t_out if not good else T3 + 0.2, DUR, f=0.25)))
    lab = text(PX1, QY0 - 9, f"model error {err:.2f}", size=10.5, fill=col, weight=700, anchor="end")
    body.append(group(lab, anims=fade(t_in, (t_in + 0.85) if not good else T3 - 0.1, DUR, f=0.25)))
body.append(group(axis_line(A_TRUE, C["green"], "", 2.4), anims=fade(T3 + 0.1, OUT, DUR)))
body.append(group(text(BC[0], BC[1] + BR + 26, "estimated axis ✓", size=10.5, fill=C["green"], weight=700, anchor="middle"),
                  anims=fade(T3 + 0.1, OUT, DUR)))

# ---------------------------------------------------------------- step 4: peaks + revolution bracket
peaks = []
for i in range(1, NS):
    if meas[i] >= meas[i - 1] and meas[i] >= meas[i + 1] and meas[i] > 0.5:
        if not peaks or xw[i] - peaks[-1][0] > 20:
            peaks.append((xw[i], ry(meas[i])))
pk = ""
for k, (x, y) in enumerate(peaks):
    pk += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="none" stroke="{C["ink"]}" stroke-width="1.6"/>'
body.append(group(pk, anims=fade(T3 + 0.4, OUT, DUR)))
# bracket for one revolution (two peaks)
x_a = PX0
x_b = PX0 + (PX1 - PX0) * PER / (T_W1 - T_W0)
br = (
    f'<path d="M{x_a:.1f},{RY1+6} L{x_a:.1f},{RY1+10} L{x_b:.1f},{RY1+10} L{x_b:.1f},{RY1+6}" fill="none" stroke="{C["ink"]}" stroke-width="1.2"/>'
    + text(x_b + 6, RY1 + 14, f"1 turn = 2 peaks ({PER:.1f} s)", size=10, fill=C["ink"], weight=700)
)
body.append(group(br, anims=fade(T3 + 0.8, OUT, DUR)))

# ---------------------------------------------------------------- bottom-right text
TX, TY = 238, 222


def para(rows, t_in, t_out):
    out, y = "", TY
    for s, kind in rows:
        col = {"b": C["ink"], "p": C["purple"], "g": C["green"], "": C["ink"]}[kind]
        size = 12 if kind == "p" else 11
        out += text(TX, y, s, size=size, fill=col, weight=700 if kind else 400)
        y += 16
    body.append(group(out, anims=fade(t_in, t_out, DUR)))


para([("One COTS reader, one antenna", "b"), ("Tag and antenna are both linearly", ""),
      ("polarized: the signal depends on how", ""), ("the tag is oriented as the ball turns", "")], 0.2, T1 - 0.1)
para([("Polarization loss ρ = cos²γ", "p"), ("RSS peaks when tag ∥ antenna,", ""),
      ("dips when tag ⊥ antenna", ""), ("phase = 4πr/λ + 2γ + c  (mod 2π)", "")], T1, T2 - 0.1)
para([("Model → expected RSS &amp; phase per axis", "b"), ("a DNN gives the initial axis guess;", ""),
      ("optimization + temporal smoothing", ""), ("refine it to the best match", "")], T2, T3 - 0.1)
para([(f"≈ {60/PER:.1f} RPM from the peak spacing", "g"), ("Translation, same antenna:", "b"),
      ("phase change → distance change,", ""), ("frequency hopping → absolute range", "")], T3, OUT)

# ---------------------------------------------------------------- dial: tag dipole seen by the antenna (y-z plane)
dial_c = (150.0, 262.0)
dr = 20.0
dial = (
    f'<circle cx="{dial_c[0]}" cy="{dial_c[1]}" r="{dr}" fill="#ffffff" stroke="{C["line"]}"/>'
    f'<line x1="{dial_c[0]}" y1="{dial_c[1]-dr}" x2="{dial_c[0]}" y2="{dial_c[1]+dr}" stroke="{C["blue"]}" stroke-width="1.4" stroke-dasharray="3 2"/>'
)
lx1, ly1, lx2, ly2 = [], [], [], []
for t in kt:
    p, d = state(t)
    # view from the antenna looking at the ball (-x): screen-right = -z, up = y
    vx, vy = -d[2], d[1]
    lx1.append((t, round(dial_c[0] - dr * 0.9 * vx, 1)))
    ly1.append((t, round(dial_c[1] + dr * 0.9 * vy, 1)))
    lx2.append((t, round(dial_c[0] + dr * 0.9 * vx, 1)))
    ly2.append((t, round(dial_c[1] - dr * 0.9 * vy, 1)))
dial += (
    f'<line x1="{lx1[0][1]}" y1="{ly1[0][1]}" x2="{lx2[0][1]}" y2="{ly2[0][1]}" stroke="{C["red"]}" stroke-width="3" stroke-linecap="round">'
    + anim("x1", lx1, PER, ease=False) + anim("y1", ly1, PER, ease=False)
    + anim("x2", lx2, PER, ease=False) + anim("y2", ly2, PER, ease=False)
    + "</line>"
    + text(dial_c[0] - dr - 6, dial_c[1] - 4, "γ", size=13, fill=C["ink"], weight=700, anchor="end", italic=True)
    + text(dial_c[0] - dr - 6, dial_c[1] + 10, "dial", size=9.5, fill=C["muted"], anchor="end")
)
body.append(group(dial, anims=fade(T1 + 0.2, T2 - 0.1, DUR)))

defs = (
    '<radialGradient id="rfBall" cx="0.38" cy="0.35" r="0.75"><stop offset="0" stop-color="#ffffff"/>'
    '<stop offset="0.7" stop-color="#e2e8f0"/><stop offset="1" stop-color="#cbd5e1"/></radialGradient>'
    f'<marker id="rfArr" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C["blue"]}"/></marker>'
)

svg = svg_doc(
    W,
    H,
    "".join(body),
    title="Rotation sensing with passive RFID tags (TIMU)",
    desc="A ball carrying a passive RFID tag spins in front of one linearly polarized reader antenna. As the tag "
    "turns, the polarization mismatch γ changes, so the received signal strength and phase rise and fall periodically. "
    "Model curves for candidate rotation axes are compared with the measured signal and the best match gives the axis; "
    "counting RSS peaks gives the rotation speed.",
    defs=defs,
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes; peaks", len(peaks))
