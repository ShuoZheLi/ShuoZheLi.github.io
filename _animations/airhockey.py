"""Robot Air Hockey testbed: dynamic puck tasks with one shared interface across a 2D sim, a 3D sim and a real
UR5e robot; benchmarked with behavior cloning, offline RL (IQL) and online RL."""

import math
import sys

from svganim import C, anim, fade, text, group, svg_doc, caption_track

DUR = 16.0
W, H = 480, 300
OUT = 15.5
T1, T2, T3 = 3.6, 7.2, 10.8
DT = 0.05

# table geometry (66 x 24 in  ->  280 x 102 px)
TX0, TY0, TW, TH = 30, 74, 280, 102
TX1, TY1 = TX0 + TW, TY0 + TH
PUCK_R, PAD_R = 6, 9
BASE = (12.0, 125.0)
L1 = L2 = 72.0


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def piecewise(keys, t, ease=True):
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, pa), (tb, pb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            u = (t - ta) / (tb - ta) if tb > ta else 1.0
            return lerp(pa, pb, smooth(u) if ease else u)
    return keys[-1][1]


def samples(f, t0=0.0, t1=DUR, dt=DT):
    n = int(round((t1 - t0) / dt))
    return [(round(t0 + i * dt, 4), f(t0 + i * dt)) for i in range(n + 1)]


def xy_anims(pts, ax="cx", ay="cy"):
    return anim(ax, [(t, round(p[0], 1)) for t, p in pts], DUR, ease=False) + anim(
        ay, [(t, round(p[1], 1)) for t, p in pts], DUR, ease=False
    )


# ---------------- episode A (2D sim): hit the puck into the goal region
GOAL = (262.0, 100.0)
A_START, A_HIT = (296.0, 152.0), (112.0, 136.0)
A_T0, A_TH, A_TG = 0.5, 1.9, 2.75
dA = (GOAL[0] - A_HIT[0], GOAL[1] - A_HIT[1])
nA = math.hypot(*dA)
uA = (dA[0] / nA, dA[1] / nA)
A_PAD = (A_HIT[0] - (PUCK_R + PAD_R) * uA[0], A_HIT[1] - (PUCK_R + PAD_R) * uA[1])


def puck_a(t):
    if t <= A_T0:
        return A_START
    if t <= A_TH:
        return lerp(A_START, A_HIT, (t - A_T0) / (A_TH - A_T0))
    u = min(1.0, (t - A_TH) / (A_TG - A_TH))
    return lerp(A_HIT, GOAL, 1 - (1 - u) ** 2)


# ---------------- episode B (3D sim): hit the puck into a block
B_START, B_HIT = (300.0, 92.0), (118.0, 112.0)
B_T0, B_TH, B_TC, B_TE = 4.0, 5.4, 6.1, 6.8
BLOCK = (240.0, 140.0, 20.0)
uB = (0.961, 0.277)
B_PAD = (B_HIT[0] - (PUCK_R + PAD_R) * uB[0], B_HIT[1] - (PUCK_R + PAD_R) * uB[1])
sB = (BLOCK[0] - PUCK_R - B_HIT[0]) / uB[0]
B_COL = (B_HIT[0] + uB[0] * sB, B_HIT[1] + uB[1] * sB)
B_REST = (208.0, 152.0)


def puck_b(t):
    if t <= B_T0:
        return B_START
    if t <= B_TH:
        return lerp(B_START, B_HIT, (t - B_T0) / (B_TH - B_T0))
    if t <= B_TC:
        return lerp(B_HIT, B_COL, (t - B_TH) / (B_TC - B_TH))
    u = min(1.0, (t - B_TC) / (B_TE - B_TC))
    return lerp(B_COL, B_REST, 1 - (1 - u) ** 2)


def block_shift(t):
    u = min(1.0, max(0.0, (t - B_TC) / 0.5))
    k = 1 - (1 - u) ** 2
    return (18 * k, 5 * k)


# ---------------- episode C (real robot): juggling on the tilted table (gravity pulls the puck to the robot)
ACC = 300.0  # px/s^2 toward the robot
X_HIT = 110.0
C_T0, C_X0 = 7.4, 300.0
C_TF = C_T0 + math.sqrt(2 * (C_X0 - X_HIT) / ACC)
PERIOD = 2.0
V_OUT = ACC * PERIOD / 2
HITS = [C_TF + PERIOD * k for k in range(4)]
Y_HIT = [128.0, 116.0, 134.0, 120.0, 126.0]


def puck_c(t):
    if t <= C_T0:
        return (C_X0, 140.0)
    if t <= C_TF:
        tau = t - C_T0
        return (C_X0 - 0.5 * ACC * tau * tau, 140.0 + (Y_HIT[0] - 140.0) * tau / (C_TF - C_T0))
    k = min(int((t - C_TF) // PERIOD), len(HITS) - 1)
    tau = t - HITS[k]
    x = X_HIT + V_OUT * tau - 0.5 * ACC * tau * tau
    y = Y_HIT[k] + (Y_HIT[k + 1] - Y_HIT[k]) * min(1.0, tau / PERIOD)
    return (x, y)


# ---------------- paddle (shared across episodes)
REST = (60.0, 125.0)
pk = [
    (0.0, REST), (0.9, REST), (1.6, (80.0, 142.0)), (A_TH, A_PAD),
    (A_TH + 0.15, (A_PAD[0] + 9 * uA[0], A_PAD[1] + 9 * uA[1])), (3.0, (62.0, 126.0)),
    (4.6, (62.0, 126.0)), (5.15, (88.0, 104.0)), (B_TH, B_PAD),
    (B_TH + 0.15, (B_PAD[0] + 8 * uB[0], B_PAD[1] + 8 * uB[1])), (6.5, (64.0, 124.0)),
]
prev = 6.5
for k, th in enumerate(HITS):
    yh = Y_HIT[k]
    pk += [(max(prev + 0.05, th - 0.4), (78.0, yh + 2)), (th, (X_HIT - PUCK_R - PAD_R, yh)),
           (th + 0.08, (X_HIT - PUCK_R - PAD_R + 7, yh)), (th + 0.7, (76.0, yh))]
    prev = th + 0.7
pk += [(15.7, REST), (DUR, REST)]


def paddle(t):
    return piecewise(pk, t)


def elbow(p):
    dx, dy = p[0] - BASE[0], p[1] - BASE[1]
    d = min(math.hypot(dx, dy), L1 + L2 - 0.5)
    phi = math.atan2(dy, dx)
    a = math.acos(d / (2 * L1))
    return (BASE[0] + L1 * math.cos(phi - a), BASE[1] + L1 * math.sin(phi - a))


body = []
body.append(
    caption_track(
        [
            (0.0, T1 - 0.1, "1", "Dynamic task: strike a moving puck into a goal"),
            (T1, T2 - 0.1, "2", "Same task interface in a 3D robot simulator"),
            (T2, T3 - 0.1, "3", "Real UR5e: an overhead camera tracks the puck"),
            (T3, OUT, "4", "Benchmark BC, offline RL and online RL"),
        ],
        DUR,
    )
)

# ---- table
tbl_fill = [(0, "#eaf4ff"), (T1 - 0.2, "#eaf4ff"), (T1 + 0.3, "#dde9f7"), (T2 - 0.2, "#dde9f7"),
            (T2 + 0.3, "#f8fafc"), (OUT, "#f8fafc"), (OUT + 0.4, "#eaf4ff")]
tbl = (
    f'<rect x="{TX0-5}" y="{TY0-5}" width="{TW+10}" height="{TH+10}" rx="12" fill="#334155"/>'
    f'<rect x="{TX0}" y="{TY0}" width="{TW}" height="{TH}" rx="8" fill="#eaf4ff">'
    + anim("fill", tbl_fill, DUR, ease=False)
    + "</rect>"
)
mx = TX0 + TW / 2
tbl += f'<line x1="{mx}" y1="{TY0}" x2="{mx}" y2="{TY1}" stroke="#93c5fd" stroke-width="1.5"/>'
tbl += f'<circle cx="{mx}" cy="{TY0+TH/2}" r="16" fill="none" stroke="#93c5fd" stroke-width="1.5"/>'
for gx in (TX0 - 5, TX1 + 1):
    tbl += f'<rect x="{gx}" y="{TY0+TH/2-17}" width="4" height="34" fill="#0f172a"/>'
body.append(tbl)
# air holes (real table only)
holes = "".join(
    f'<circle cx="{x}" cy="{y}" r="0.9" fill="#94a3b8"/>'
    for x in range(TX0 + 10, TX1 - 4, 12)
    for y in range(TY0 + 8, TY1 - 2, 12)
)
body.append(group(holes, anims=fade(T2 + 0.1, OUT, DUR, f=0.4)))
# 3D-sim shading
shade = (
    f'<rect x="{TX0}" y="{TY0}" width="{TW}" height="{TH}" rx="8" fill="url(#ahShade)"/>'
)
body.append(group(shade, anims=fade(T1 + 0.1, T2 - 0.1, DUR, f=0.4)))

# ---- episode A goal region
gA = (
    f'<circle cx="{GOAL[0]}" cy="{GOAL[1]}" r="17" fill="{C["green_l"]}" fill-opacity="0.6" stroke="{C["green"]}" '
    f'stroke-width="1.6" stroke-dasharray="4 3"/>'
)
body.append(group(gA, anims=fade(0.3, T1 - 0.3, DUR)))
okA = text(GOAL[0], GOAL[1] + 32, "✓ in goal", size=11.5, fill=C["green"], weight=700, anchor="middle")
body.append(group(okA, anims=fade(A_TG + 0.05, T1 - 0.3, DUR, f=0.2)))

# ---- episode B block
bx0, by0, bs = BLOCK
blk_pts = samples(lambda t: block_shift(t), B_TC - 0.05, B_TC + 0.6)
blk = (
    f'<rect x="{bx0}" y="{by0}" width="{bs}" height="{bs}" rx="3" fill="{C["orange"]}" stroke="#9a3412" stroke-width="1.2">'
    + anim("x", [(0, bx0)] + [(t, round(bx0 + p[0], 1)) for t, p in blk_pts], DUR, ease=False)
    + anim("y", [(0, by0)] + [(t, round(by0 + p[1], 1)) for t, p in blk_pts], DUR, ease=False)
    + "</rect>"
)
body.append(group(blk, anims=fade(T1 + 0.1, T2 - 0.2, DUR)))
okB = text(bx0 + 4, by0 - 10, "✓ block moved", size=11.5, fill=C["orange"], weight=700, anchor="middle")
body.append(group(okB, anims=fade(B_TC + 0.5, T2 - 0.2, DUR, f=0.2)))


# ---- pucks
def puck_el(fn, t_in, t_out, t0, t1):
    pts = samples(fn, t0, t1)
    el = (
        f'<circle r="{PUCK_R}" cx="{pts[0][1][0]:.1f}" cy="{pts[0][1][1]:.1f}" fill="{C["red"]}" stroke="#7f1d1d" '
        f'stroke-width="1">' + xy_anims([(0.0, pts[0][1])] + pts) + "</circle>"
    )
    return group(el, anims=fade(t_in, t_out, DUR, f=0.2))


body.append(puck_el(puck_a, 0.35, T1 - 0.35, 0.4, 3.4))
body.append(puck_el(puck_b, 3.85, T2 - 0.35, 3.9, 7.0))
body.append(puck_el(puck_c, 7.3, OUT - 0.2, 7.3, 15.6))

# camera detection box (real)
cpts = samples(puck_c, 7.3, 15.6)
det = (
    f'<rect width="20" height="20" x="0" y="0" fill="none" stroke="{C["amber"]}" stroke-width="1.4" stroke-dasharray="3 2">'
    + anim("x", [(0.0, 290.0)] + [(t, round(p[0] - 10, 1)) for t, p in cpts], DUR, ease=False)
    + anim("y", [(0.0, 130.0)] + [(t, round(p[1] - 10, 1)) for t, p in cpts], DUR, ease=False)
    + "</rect>"
)
body.append(group(det, anims=fade(7.6, OUT - 0.2, DUR, f=0.2)))
cam = (
    f'<rect x="{mx-9}" y="50" width="18" height="12" rx="2" fill="{C["ink"]}"/>'
    f'<circle cx="{mx}" cy="56" r="3.5" fill="{C["amber"]}"/>'
    + text(mx + 15, 60, "overhead camera, 60 Hz → puck state", size=10.5, fill=C["amber"], weight=700)
)
body.append(group(cam, anims=fade(T2 + 0.1, T3 - 0.1, DUR)))

# ---- paddle + arm
ppts = samples(paddle)
epts = [(t, elbow(p)) for t, p in ppts]
arm = (
    f'<circle cx="{BASE[0]}" cy="{BASE[1]}" r="10" fill="#475569"/>'
    f'<line x1="{BASE[0]}" y1="{BASE[1]}" x2="0" y2="0" stroke="#64748b" stroke-width="9" stroke-linecap="round">'
    + xy_anims(epts, "x2", "y2")
    + "</line>"
    + f'<line x1="0" y1="0" x2="0" y2="0" stroke="#94a3b8" stroke-width="7" stroke-linecap="round">'
    + xy_anims(epts, "x1", "y1")
    + xy_anims(ppts, "x2", "y2")
    + "</line>"
    + f'<circle r="5.5" cx="0" cy="0" fill="#334155">'
    + xy_anims(epts)
    + "</circle>"
)
body.append(group(arm, anims=fade(T1 + 0.1, OUT, DUR, f=0.4)))
pad = (
    f'<circle r="{PAD_R}" cx="{REST[0]}" cy="{REST[1]}" fill="{C["blue"]}" stroke="#1e3a8a" stroke-width="1.5">'
    + xy_anims(ppts)
    + "</circle>"
)
body.append(pad)

# ---- right panel: three domains
RX, RW = 330, 136
doms = [
    ("2D sim", "Box2D, paddle only", 0.0, T1),
    ("3D sim", "robosuite / MuJoCo arm", T1, T2),
    ("Real robot", "UR5e + camera", T2, T3),
]
for i, (name, sub, t_on, t_off) in enumerate(doms):
    y = 62 + 42 * i
    fill = [(0, "#ffffff")]
    stroke = [(0, C["line"])]
    if t_on > 0:
        fill += [(t_on - 0.05, "#ffffff")]
        stroke += [(t_on - 0.05, C["line"])]
    fill += [(t_on + 0.25, C["blue_l"]), (t_off - 0.05, C["blue_l"]), (t_off + 0.25, "#ffffff"),
             (T3 + 0.2, "#ffffff"), (T3 + 0.5, C["gray_l"]), (OUT, C["gray_l"]), (OUT + 0.3, "#ffffff")]
    stroke += [(t_on + 0.25, C["blue"]), (t_off - 0.05, C["blue"]), (t_off + 0.25, C["line"])]
    card = (
        f'<rect x="{RX}" y="{y}" width="{RW}" height="34" rx="8" fill="#ffffff" stroke="{C["line"]}" stroke-width="1.4">'
        + anim("fill", fill, DUR, ease=False)
        + anim("stroke", stroke, DUR, ease=False)
        + "</rect>"
        + text(RX + 10, y + 15, name, size=12, fill=C["ink"], weight=700)
        + text(RX + 10, y + 28, sub, size=10, fill=C["muted"])
    )
    body.append(card)
    if i < 2:
        body.append(text(RX + RW - 12, y + 40, "↓", size=11, fill=C["faint"], weight=700, anchor="middle"))
body.append(text(RX + RW - 22, 56, "fidelity", size=9.5, fill=C["faint"], anchor="end"))
shared = text(RX + RW / 2, 202, "one state / action / reward API", size=10.5, fill=C["blue"], weight=700, anchor="middle")
body.append(group(shared, anims=fade(T3 + 0.3, OUT, DUR)))

# ---- bottom: task chips (steps 1-3)
tasks = [["Reach", "Reach + vel.", "Touch", "Strike", "Strike crowd"],
         ["Juggle", "Puck vel.", "Move block", "Hit goal", "Goal + vel."]]
active = {"Hit goal": (0.0, T1), "Move block": (T1, T2), "Juggle": (T2, T3)}
chips = text(TX0 - 6, 206, "10 tasks, easy → hard", size=11, fill=C["muted"], weight=700)
cy0 = 216
act_layers = []
for r, row in enumerate(tasks):
    x = TX0 - 6
    for name in row:
        w = 12 + 6.3 * len(name)
        y = cy0 + 30 * r
        chips += (
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="22" rx="11" fill="{C["gray_l"]}" stroke="{C["line"]}"/>'
            + text(x + w / 2, y + 15, name, size=11, fill=C["ink"], anchor="middle")
        )
        if name in active:
            a0, a1 = active[name]
            hl = (
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="22" rx="11" fill="{C["ink"]}"/>'
                + text(x + w / 2, y + 15, name, size=11, fill="#fff", weight=700, anchor="middle")
            )
            act_layers.append(group(hl, anims=fade(a0 + 0.2, a1 - 0.2, DUR, f=0.25)))
        x += w + 7
body.append(group(chips + "".join(act_layers), anims=fade(0.1, T3 - 0.1, DUR)))

# ---- bottom: learning (step 4)
LY = 210
lb = ""


def box(x, y, w, h, title, sub, col, col_l):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{col_l}" stroke="{col}" stroke-width="1.3"/>'
    s += text(x + 8, y + 15, title, size=11.5, fill=C["ink"], weight=700)
    if sub:
        s += text(x + 8, y + 28, sub, size=9.8, fill=C["muted"])
    return s


lb += box(24, LY, 138, 34, "Teleop demos", "mouse + shadow, 8 players", C["amber"], C["amber_l"])
lb += box(24, LY + 44, 138, 34, "Env. interaction", "reward only, from scratch", C["teal"], C["teal_l"])
lrn = [("Behavior cloning", LY - 2), ("Offline RL (IQL)", LY + 26), ("Online RL (PPO, SAC)", LY + 54)]
for name, y in lrn:
    lb += f'<rect x="196" y="{y}" width="132" height="22" rx="11" fill="#ffffff" stroke="{C["ink"]}" stroke-width="1.2"/>'
    lb += text(262, y + 15, name, size=11, fill=C["ink"], weight=700, anchor="middle")
arr = f'stroke="{C["muted"]}" stroke-width="1.3" marker-end="url(#ahArr)" fill="none"'
lb += f'<path d="M162,{LY+14} L192,{LY+9}" {arr}/>'
lb += f'<path d="M162,{LY+20} L192,{LY+37}" {arr}/>'
lb += f'<path d="M162,{LY+61} L192,{LY+65}" {arr}/>'
lb += text(342, LY + 8, "sim: online RL is best", size=11, fill=C["ink"], weight=700)
lb += text(342, LY + 26, "real: IQL beats BC on", size=11, fill=C["ink"])
lb += text(342, LY + 41, "most tasks; even humans", size=11, fill=C["ink"])
lb += text(342, LY + 56, "struggle to juggle", size=11, fill=C["ink"])
lb += text(342, LY + 74, "→ room for better RL", size=11, fill=C["purple"], weight=700)
body.append(group(lb, anims=fade(T3 + 0.2, OUT, DUR)))

defs = (
    '<linearGradient id="ahShade" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#ffffff" stop-opacity="0.55"/>'
    '<stop offset="1" stop-color="#1e3a8a" stop-opacity="0.12"/></linearGradient>'
    f'<marker id="ahArr" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C["muted"]}"/></marker>'
)

svg = svg_doc(
    W,
    H,
    "".join(body),
    title="Robot Air Hockey testbed",
    desc="Top-down air hockey table. In a 2D simulator the paddle strikes a moving puck into a goal region; in a 3D "
    "simulator a robot arm hits the puck into a block; on the real UR5e an overhead camera tracks the puck while the "
    "robot juggles it on the tilted table. The same ten tasks and interface are used to benchmark behavior cloning, "
    "offline RL (IQL) and online RL.",
    defs=defs,
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes", "first juggle hit", round(C_TF, 2))
