"""DynaBARN: obstacle motion profiles from random polynomial paths + per-segment sampled speeds; environments
of varying difficulty; a ground robot must reach the goal through the moving obstacles."""

import math
import random
import sys

import numpy as np

from svganim import C, anim, anim_tf, fade, text, group, svg_doc, caption_track

DUR = 16.0
W, H = 480, 300
OUT = 15.5
T1, T2, T3 = 3.6, 7.2, 10.8

WX0, WY0, WS = 20, 54, 226  # world square on screen (20 m x 20 m)
PPM = WS / 20.0
OBS_R = 0.5  # m
ROB_R = 0.35  # m (Jackal ~0.5 x 0.43 m)


def sx(X):
    return WX0 + (X + 10) * PPM


def sy(Y):
    return WY0 + (10 - Y) * PPM


# ---------------------------------------------------------------- Algorithm 1 (obstacle trajectory generation)
def gen_traj(rng, order_rng, speed_rng, std_rng):
    n = rng.randint(*order_rng)
    pts = [(rng.uniform(-9, 9), rng.uniform(-9, 9)) for _ in range(n + 1)]
    xs = np.array([p[0] for p in pts])
    ys = np.array([p[1] for p in pts])
    coef = np.polyfit(xs, ys, n)
    p = np.poly1d(coef)
    way = [(float(x), float(p(x))) for x in range(-10, 11)]
    # edge intersections with y = +-10
    for yb in (-10.0, 10.0):
        for r in (p - yb).r:
            if abs(r.imag) < 1e-9 and -10 <= r.real <= 10:
                way.append((float(r.real), yb))
    way = [w for w in way if -10 <= w[1] <= 10]
    way.sort(key=lambda w: w[0])
    if rng.random() < 0.5:
        way.reverse()
    # timestamps
    t = [0.0]
    speeds = []
    for a, b in zip(way, way[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        mu = rng.uniform(*speed_rng)
        sd = rng.uniform(*std_rng)
        s = min(max(rng.gauss(mu, sd), speed_rng[0]), speed_rng[1])
        speeds.append(s)
        t.append(t[-1] + d / s)
    return dict(n=n, pts=pts, way=way, t=t, speeds=speeds)


def contiguous(tr):
    """reject paths whose kept waypoints jump (curve left and re-entered the grid)"""
    w = tr["way"]
    for a, b in zip(w, w[1:]):
        if math.hypot(b[0] - a[0], b[1] - a[1]) > 3.2:
            return False
    return len(w) >= 12


def pick(seed, order_rng, speed_rng, std_rng):
    rng = random.Random(seed)
    while True:
        tr = gen_traj(rng, order_rng, speed_rng, std_rng)
        if contiguous(tr):
            return tr


def pos_at(tr, tt):
    t, w = tr["t"], tr["way"]
    if tt <= t[0]:
        return w[0]
    if tt >= t[-1]:
        return w[-1]
    i = max(k for k in range(len(t)) if t[k] <= tt)
    u = (tt - t[i]) / (t[i + 1] - t[i])
    return (w[i][0] + (w[i + 1][0] - w[i][0]) * u, w[i][1] + (w[i + 1][1] - w[i][1]) * u)


HARD = ((3, 4), (1.0, 2.0), (0.1, 0.2))

# ---------------------------------------------------------------- demo obstacle (steps 1-2)
demo = pick(11, (3, 3), *HARD[1:])
D_T0, D_T1 = 3.8, 7.0
K_DEMO = (D_T1 - D_T0) / demo["t"][-1]  # animation seconds per real second


def demo_anim_t(treal):
    return D_T0 + treal * K_DEMO


# ---------------------------------------------------------------- environment (steps 3-4)
K_ENV = 0.3  # animation seconds per real second
ENV_T0, ENV_T1 = 7.3, OUT
env = []
offsets = [2.0, 9.0, 5.0, 13.0, 1.0, 7.0, 11.0]
seeds = [3, 8, 21, 34, 55, 89, 144]
for sd, off in zip(seeds, offsets):
    env.append(dict(tr=pick(sd, *HARD), off=off))


def env_pos(o, ta):
    """obstacle o at animation time ta (real time = (ta-ENV_T0)/K_ENV + off), looping along its path"""
    tr = o["tr"]
    treal = (ta - ENV_T0) / K_ENV + o["off"]
    treal = treal % (tr["t"][-1] + 1.5)
    return pos_at(tr, treal) if treal <= tr["t"][-1] else None


# ---------------------------------------------------------------- robot: greedy planner with lookahead
START, GOAL = (0.0, -9.3), (0.0, 9.3)
R_T0, R_TMAX = 11.1, 15.1
VMAX = 2.0
SAFE = OBS_R + ROB_R + 0.45


def clear_at(p, ta):
    best = 99.0
    for o in env:
        q = env_pos(o, ta)
        if q is None:
            continue
        best = min(best, math.hypot(p[0] - q[0], p[1] - q[1]))
    return best


def plan():
    dt_a = 0.05
    dt_r = dt_a / K_ENV
    p = START
    path = [(R_T0, p)]
    ta = R_T0
    cands = [(0.0, 0.0)]
    for sp in (0.5, 1.0, 1.5, 2.0):
        for ang in range(-75, 76, 15):
            a = math.radians(90 + ang)
            cands.append((sp * math.cos(a), sp * math.sin(a)))
    for sp in (0.6, 1.2):
        for ang in (0, 180):
            a = math.radians(ang)
            cands.append((sp * math.cos(a), sp * math.sin(a)))
        cands.append((0.0, -sp))
    while ta < R_TMAX and math.hypot(p[0] - GOAL[0], p[1] - GOAL[1]) > 0.2:
        best, bscore = None, -1e9
        for vx, vy in cands:
            ok = True
            for k in range(1, 9):
                q = (p[0] + vx * dt_r * k, p[1] + vy * dt_r * k)
                if abs(q[0]) > 9.3 or q[1] < -9.8 or q[1] > 9.8 or clear_at(q, ta + dt_a * k) < SAFE:
                    ok = False
                    break
            if not ok:
                continue
            q = (p[0] + vx * dt_r, p[1] + vy * dt_r)
            score = -math.hypot(q[0] - GOAL[0], q[1] - GOAL[1]) - 0.08 * abs(q[0])
            if score > bscore:
                best, bscore = q, score
        if best is None:
            best = p
        dg = math.hypot(GOAL[0] - best[0], GOAL[1] - best[1])
        if dg < VMAX * dt_r:
            best = GOAL
        p = best
        ta += dt_a
        path.append((round(ta, 3), p))
    return path


rpath = plan()
min_clear = min(clear_at(p, t) for t, p in rpath)
R_TG = rpath[-1][0]
reached = math.hypot(rpath[-1][1][0] - GOAL[0], rpath[-1][1][1] - GOAL[1]) < 0.25

# ---------------------------------------------------------------- drawing
body = []
body.append(
    caption_track(
        [
            (0.0, T1 - 0.1, "1", "Fit a random polynomial path for an obstacle"),
            (T1, T2 - 0.1, "2", "Sample a speed for every path segment"),
            (T2, T3 - 0.1, "3", "Mix motion profiles → graded difficulty"),
            (T3, OUT, "4", "The robot must reach the goal without collision"),
        ],
        DUR,
    )
)

# world grid
g = f'<rect x="{WX0}" y="{WY0}" width="{WS}" height="{WS}" rx="4" fill="{C["card"]}" stroke="{C["muted"]}" stroke-width="1"/>'
for k in range(1, 10):
    v = WX0 + WS * k / 10
    g += f'<line x1="{v:.1f}" y1="{WY0}" x2="{v:.1f}" y2="{WY0+WS}" stroke="{C["line"]}"/>'
    v = WY0 + WS * k / 10
    g += f'<line x1="{WX0}" y1="{v:.1f}" x2="{WX0+WS}" y2="{v:.1f}" stroke="{C["line"]}"/>'
g += text(WX0 + WS - 4, WY0 + WS - 5, "20 m × 20 m", size=9.5, fill=C["faint"], anchor="end")
body.append(g)
body.append(f'<clipPath id="dbClip"><rect x="{WX0}" y="{WY0}" width="{WS}" height="{WS}" rx="4"/></clipPath>')


def polyline(way):
    return " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in way)


def plen(way):
    return sum(math.hypot(sx(b[0]) - sx(a[0]), sy(b[1]) - sy(a[1])) for a, b in zip(way, way[1:]))


# -- step 1: sample points, fitted curve, integer-x waypoints
dw = demo["way"]
L = plen(dw)
curve = (
    f'<polyline points="{polyline(dw)}" fill="none" stroke="{C["blue"]}" stroke-width="2" stroke-linejoin="round" '
    f'stroke-dasharray="{L:.1f} {L:.1f}">'
    + anim("stroke-dashoffset", [(0, L), (1.5, L), (2.6, 0)], DUR, ease=True)
    + "</polyline>"
)
body.append(group(curve, anims=fade(1.45, T2 - 0.1, DUR, f=0.15)))
for i, (x, y) in enumerate(demo["way"]):
    t_in = 2.7 + 0.025 * i
    body.append(
        group(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="2.2" fill="{C["blue"]}"/>', anims=fade(t_in, T2 - 0.1, DUR, f=0.15))
    )
for i, (x, y) in enumerate(demo["pts"]):
    t_in = 0.4 + 0.3 * i
    body.append(
        group(
            f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="5" fill="#f472b6" stroke="#be185d" stroke-width="1.2"/>',
            anims=fade(t_in, T2 - 0.1, DUR, f=0.2),
        )
    )

# -- step 2: obstacle moves with per-segment speeds, trail dots at equal time steps
kx, ky = [], []
for tr_, (x, y) in zip(demo["t"], demo["way"]):
    kx.append((demo_anim_t(tr_), round(sx(x), 1)))
    ky.append((demo_anim_t(tr_), round(sy(y), 1)))
ob = (
    f'<circle r="{OBS_R*PPM+1:.1f}" cx="{kx[0][1]}" cy="{ky[0][1]}" fill="{C["red"]}" stroke="#7f1d1d" stroke-width="1">'
    + anim("cx", kx, DUR, ease=False)
    + anim("cy", ky, DUR, ease=False)
    + "</circle>"
)
body.append(group(ob, anims=fade(D_T0 - 0.2, T2 - 0.1, DUR, f=0.2)))
step_real = 1.0
nsteps = int(demo["t"][-1] / step_real)
for k in range(1, nsteps + 1):
    x, y = pos_at(demo, k * step_real)
    ta = demo_anim_t(k * step_real)
    body.append(
        group(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="2.6" fill="{C["red"]}" fill-opacity="0.55"/>',
              anims=fade(ta, T2 - 0.1, DUR, f=0.1))
    )

# -- steps 3-4: environment obstacles (paths faint) + moving obstacles
envg = ""
for o in env:
    envg += f'<polyline points="{polyline(o["tr"]["way"])}" fill="none" stroke="#fca5a5" stroke-width="1.2" stroke-dasharray="3 3"/>'
body.append(group(envg, extra='clip-path="url(#dbClip)"', anims=fade(T2 + 0.1, OUT, DUR)))
ts = [round(ENV_T0 + 0.05 * i, 3) for i in range(int((ENV_T1 + 0.3 - ENV_T0) / 0.05) + 1)]
for o in env:
    xs_, ys_, op_ = [], [], []
    last = (sx(0), sy(0))
    for ta in ts:
        q = env_pos(o, ta)
        if q is None:
            op_.append((ta, 0))
            xs_.append((ta, round(last[0], 1)))
            ys_.append((ta, round(last[1], 1)))
        else:
            last = (sx(q[0]), sy(q[1]))
            op_.append((ta, 1))
            xs_.append((ta, round(last[0], 1)))
            ys_.append((ta, round(last[1], 1)))
    el = (
        f'<circle r="{OBS_R*PPM+1:.1f}" cx="{xs_[0][1]}" cy="{ys_[0][1]}" fill="{C["red"]}" stroke="#7f1d1d" stroke-width="1">'
        + anim("cx", [(0, xs_[0][1])] + xs_, DUR, ease=False)
        + anim("cy", [(0, ys_[0][1])] + ys_, DUR, ease=False)
        + anim("opacity", [(0, op_[0][1])] + op_, DUR, discrete=True)
        + "</circle>"
    )
    body.append(group(el, extra='clip-path="url(#dbClip)"', anims=fade(T2 + 0.1, OUT, DUR)))

# start/goal + robot
sg = (
    f'<circle cx="{sx(GOAL[0])}" cy="{sy(GOAL[1])}" r="6" fill="{C["green"]}"/>'
    + text(sx(GOAL[0]) + 10, sy(GOAL[1]) + 4, "goal", size=10.5, fill=C["green"], weight=700)
    + f'<rect x="{sx(START[0])-7}" y="{sy(START[1])-7}" width="14" height="14" rx="2" fill="none" stroke="{C["muted"]}" stroke-dasharray="2 2"/>'
    + text(sx(START[0]) + 11, sy(START[1]) + 4, "start", size=10.5, fill=C["muted"], weight=700)
)
body.append(group(sg, anims=fade(T3 - 0.3, OUT, DUR)))
rxk = [(0, round(sx(START[0]), 1))] + [(t, round(sx(p[0]), 1)) for t, p in rpath]
ryk = [(0, round(sy(START[1]), 1))] + [(t, round(sy(p[1]), 1)) for t, p in rpath]
# heading from motion
hk = [(0, -90.0)]
prev_h = -90.0
for (t0, p0), (t1, p1) in zip(rpath, rpath[1:]):
    dx, dy = sx(p1[0]) - sx(p0[0]), sy(p1[1]) - sy(p0[1])
    if math.hypot(dx, dy) > 0.3:
        prev_h = math.degrees(math.atan2(dy, dx))
    hk.append((t1, round(prev_h, 1)))
robot = (
    "<g>"
    + anim_tf("translate", [(t, (x, y)) for (t, x), (_, y) in zip(rxk, ryk)], DUR, ease=False)
    + "<g>"
    + anim_tf("rotate", [(t, h) for t, h in hk], DUR, ease=False)
    + f'<rect x="-7" y="-6" width="14" height="12" rx="2.5" fill="#facc15" stroke="#1f2937" stroke-width="1.4"/>'
    + f'<path d="M7,-3 L10,0 L7,3 z" fill="#1f2937"/>'
    + "</g></g>"
)
body.append(group(robot, anims=fade(T3 - 0.3, OUT, DUR)))
# robot trail
trail_pts = " ".join(f"{sx(p[0]):.1f},{sy(p[1]):.1f}" for _, p in rpath)
Lr = plen([p for _, p in rpath])
trail = (
    f'<polyline points="{trail_pts}" fill="none" stroke="#ca8a04" stroke-width="1.6" stroke-dasharray="{Lr:.1f} {Lr:.1f}" '
    f'stroke-linecap="round" stroke-linejoin="round">'
    + anim("stroke-dashoffset", [(0, Lr)] + [(t, round(Lr - plen([p for _, p in rpath[: i + 1]]), 1)) for i, (t, p) in enumerate(rpath) if i % 4 == 0 or i == len(rpath) - 1], DUR, ease=False)
    + "</polyline>"
)
body.append(group(trail, anims=fade(T3 - 0.3, OUT, DUR)))
okr = text(sx(GOAL[0]) - 10, sy(GOAL[1]) + 4, "✓", size=13, fill=C["green"], weight=700, anchor="end")
body.append(group(okr, anims=fade(R_TG, OUT, DUR, f=0.2)))

# ---------------------------------------------------------------- right panel
RX = 262


def lines(rows, t_in, t_out, y0=74, dy=16.5):
    out, y = "", y0
    for s, kind in rows:
        if kind == "eq":
            out += text(RX, y + 1, s, size=12.5, fill=C["purple"], weight=700)
            y += dy + 3
        elif kind == "b":
            out += text(RX, y, s, size=11.5, fill=C["ink"], weight=700)
            y += dy
        elif kind == "m":
            out += text(RX, y, s, size=10.5, fill=C["muted"])
            y += dy - 1
        else:
            out += text(RX, y, s, size=11.5, fill=C["ink"])
            y += dy
    body.append(group(out, anims=fade(t_in, t_out, DUR)))


lines(
    [
        ("Obstacle motion profile:", "b"),
        ("order n ~ U{min, max}", "eq"),
        ("sample n+1 points (pink)", ""),
        ("fit the degree-n polynomial", ""),
        ("waypoints at every integer x", ""),
        ("(blue); random direction", ""),
        ("hard profile here: n = 3", "m"),
    ],
    0.2,
    T1 - 0.1,
)
lines(
    [
        ("Time-stamp each waypoint:", "b"),
        ("s ~ N(μ, σ²),  μ ~ U[s_min, s_max]", "eq"),
        ("tᵢ = tᵢ₋₁ + dᵢ / s", "eq"),
        ("dots: one per second, so", ""),
        ("gaps show the speed changes", ""),
    ],
    T1,
    T2 - 0.1,
)
# speed bars (step 2)
SB_X, SB_Y, SB_H = RX, 252, 52
nseg = len(demo["speeds"])
bw = min(8.0, (200 - 4) / nseg - 1.5)
sb = f'<line x1="{SB_X}" y1="{SB_Y}" x2="{SB_X + nseg*(bw+1.5)}" y2="{SB_Y}" stroke="{C["muted"]}"/>'
sb += text(SB_X, SB_Y - SB_H - 6, "segment speed (1–2 m/s)", size=10, fill=C["muted"])
body.append(group(sb, anims=fade(T1 + 0.1, T2 - 0.1, DUR)))
for i, s in enumerate(demo["speeds"]):
    h = SB_H * (s / 2.0)
    t_in = demo_anim_t(demo["t"][i])
    bar = f'<rect x="{SB_X + i*(bw+1.5):.1f}" y="{SB_Y-h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{C["red"]}" fill-opacity="0.7"/>'
    body.append(group(bar, anims=fade(t_in, T2 - 0.1, DUR, f=0.1)))

# step 3: table + difficulty
tb = text(RX, 74, "Motion profiles (Table I)", size=11.5, fill=C["ink"], weight=700)
cols = [RX, RX + 82, RX + 146]
tb += text(cols[1], 92, "easy", size=10.5, fill=C["green"], weight=700) + text(cols[2], 92, "hard", size=10.5, fill=C["red"], weight=700)
rows = [("order", "1–2", "3–4"), ("speed m/s", "0.5–1", "1–2"), ("speed σ", "0.01–0.1", "0.1–0.2")]
for k, (a, b, c) in enumerate(rows):
    y = 109 + 16 * k
    tb += text(cols[0], y, a, size=10.5, fill=C["muted"]) + text(cols[1], y, b, size=10.5) + text(cols[2], y, c, size=10.5)
tb += f'<line x1="{RX}" y1="164" x2="{RX+200}" y2="164" stroke="{C["line"]}"/>'
tb += text(RX, 182, "Difficulty = #obstacles × profile", size=11.5, fill=C["ink"], weight=700)
dif = [("few · easy", "easy", C["green"]), ("few · hard  or  many · easy", "medium", C["amber"]), ("many · hard", "hard", C["red"])]
for k, (a, b, col) in enumerate(dif):
    y = 200 + 17 * k
    tb += text(RX, y, a, size=10.5, fill=C["ink"]) + text(RX + 200, y, "→ " + b, size=10.5, fill=col, weight=700, anchor="end")
tb += text(RX, 260, "shown: a hard world", size=10.5, fill=C["muted"])
body.append(group(tb, anims=fade(T2, T3 - 0.1, DUR)))

lines(
    [
        ("Benchmark in Gazebo:", "b"),
        ("Jackal robot, max 2 m/s", ""),
        ("60 worlds: 20 easy / 20 medium", ""),
        ("/ 20 hard, plus 60 human", ""),
        ("demonstrations", ""),
        ("Baselines: DWA, TEB, RL, BC", "b"),
        ("RL is best overall; TEB nearly", ""),
        ("fails in hard worlds", ""),
    ],
    T3,
    OUT,
)

svg = svg_doc(
    W,
    H,
    "".join(body),
    title="DynaBARN: navigation among dynamic obstacles",
    desc="In a 20 m by 20 m world, random points are sampled and a polynomial is fit through them to form an obstacle "
    "path; each path segment gets a sampled speed, so the obstacle speeds up and slows down. Many obstacles with easy "
    "or hard motion profiles make worlds of graded difficulty, and a ground robot drives from start to goal while "
    "avoiding them.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes; demo order", demo["n"], "len", round(demo["t"][-1], 1), "s;",
      "robot reached", reached, "at", R_TG, "min clearance", round(min_clear, 2), "needed", SAFE - 0.45)
