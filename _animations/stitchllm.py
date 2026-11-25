"""StitchLLM: bottom blocks of a large LLM + trained stitching layer + top blocks of a small LLM; the stitch point adapts to load."""

import sys
from svganim import C, anim, fade, text, group, svg_doc, caption_track, arrow_marker

DUR = 16.0
W, H = 480, 300
OUT = 15.5

L = 8
LH, LG = 17, 5
YBOT = 258
AX0, AW = 44, 82      # large-model tower
BX0, BW = 206, 48     # small-model tower
ACX, BCX = AX0 + AW / 2, BX0 + BW / 2

# stitch point schedule: (time, i) = number of bottom layers taken from the large model
SCHED = [(0.0, 6), (8.0, 4), (10.3, 2), (13.1, 6)]
TR = 0.45  # transition time


def i_at(t):
    cur = SCHED[0][1]
    for ts, i in SCHED:
        if t >= ts:
            cur = i
    return cur


def layer_y(k):  # top y of layer k (1-based)
    return YBOT - k * (LH + LG)


def boundary_y(i):  # y between layer i and i+1
    return layer_y(i) - LG / 2


body = []
defs = arrow_marker("as", C["muted"]) + arrow_marker("ag", C["faint"])

body.append(
    caption_track(
        [
            (0.0, 3.15, "1", "Decoder blocks of a large and a small LLM"),
            (3.25, 6.35, "2", "A trained stitching layer joins them"),
            (6.45, 12.45, "3", "Load spikes → scheduler moves the stitch point"),
            (12.55, OUT, "", "Fine-grained accuracy–throughput trade-off"),
        ],
        DUR,
    )
)

# towers
for k in range(1, L + 1):
    y = layer_y(k)
    a = f'<rect x="{AX0}" y="{y}" width="{AW}" height="{LH}" rx="4" fill="{C["blue"]}"/>'
    b = f'<rect x="{BX0}" y="{y}" width="{BW}" height="{LH}" rx="4" fill="{C["teal"]}"/>'
    # before stitching (phase 1) all blocks are fully visible; afterwards opacity follows the schedule
    def track(is_active):
        pts = [(0, 1.0), (3.3, 1.0), (3.8, 1.0 if is_active(SCHED[0][1]) else 0.22)]
        for ts, i in SCHED[1:]:
            prev = pts[-1][1]
            pts += [(ts, prev), (ts + TR, 1.0 if is_active(i) else 0.22)]
        pts += [(OUT, pts[-1][1]), (OUT + 0.4, 1.0)]
        return pts

    pa = track(lambda i, k=k: k <= i)
    pb = track(lambda i, k=k: k > i)
    body.append(f"<g>{anim('opacity', pa, DUR)}{a}</g>")
    body.append(f"<g>{anim('opacity', pb, DUR)}{b}</g>")

tl = (
    text(ACX, YBOT + 16, "large LLM", size=12, fill=C["blue"], weight=700, anchor="middle")
    + text(ACX, YBOT + 30, "(e.g. 8B, hidden 4096)", size=10.5, fill=C["muted"], anchor="middle")
    + text(BCX, YBOT + 16, "small LLM", size=12, fill=C["teal"], weight=700, anchor="middle")
    + text(BCX, YBOT + 30, "(e.g. 1B, hidden 2048)", size=10.5, fill=C["muted"], anchor="middle")
)
body.append(tl)

# stitching layer: moves with the schedule
SX0, SX1 = AX0 + AW + 6, BX0 - 6


def stitch_shape(i):
    yb = boundary_y(i)
    return f"{SX0},{yb-10} {SX1},{yb-6} {SX1},{yb+6} {SX0},{yb+10}"


st_pts = [(0, stitch_shape(SCHED[0][1]))]
for ts, i in SCHED[1:]:
    st_pts += [(ts, st_pts[-1][1]), (ts + TR, stitch_shape(i))]
stitch = (
    f'<polygon points="{stitch_shape(SCHED[0][1])}" fill="{C["purple"]}">' + anim("points", st_pts, DUR) + "</polygon>"
)
s_lab_pts = [(0, boundary_y(SCHED[0][1]) - 14)]
for ts, i in SCHED[1:]:
    s_lab_pts += [(ts, s_lab_pts[-1][1]), (ts + TR, boundary_y(i) - 14)]
s_lab = (
    f'<text x="{(SX0+SX1)/2}" y="{s_lab_pts[0][1]}" font-family="Helvetica Neue, Helvetica, Arial, sans-serif" font-size="11" '
    f'font-weight="700" fill="{C["purple"]}" text-anchor="middle">stitch S' + anim("y", s_lab_pts, DUR) + "</text>"
)
body.append(group(stitch + s_lab, anims=fade(3.4, OUT, DUR)))
note = (
    text(300, 118, "S maps hidden 4096 \u2192 2048", size=11.5, fill=C["purple"], weight=700)
    + text(300, 134, "only S is trained;", size=11.5, fill=C["purple"])
    + text(300, 149, "all decoder blocks stay frozen", size=11.5, fill=C["purple"])
)
body.append(group(note, anims=fade(3.9, 6.4, DUR)))


# request token path for a given i
def token(i, t0, t1):
    yb = boundary_y(i)
    pts = [(ACX, YBOT + 2), (ACX, yb), (SX0, yb), (SX1, yb), (BCX, yb), (BCX, layer_y(L) - 6)]
    seg = [abs(pts[j + 1][0] - pts[j][0]) + abs(pts[j + 1][1] - pts[j][1]) for j in range(len(pts) - 1)]
    tot = sum(seg)
    kx, ky = [(t0, pts[0][0])], [(t0, pts[0][1])]
    acc = 0
    for j, s in enumerate(seg):
        acc += s
        t = t0 + (t1 - t0) * acc / tot
        kx.append((t, pts[j + 1][0]))
        ky.append((t, pts[j + 1][1]))
    dot = (
        f'<circle r="6" cx="{pts[0][0]}" cy="{pts[0][1]}" fill="{C["amber"]}" stroke="#fff" stroke-width="1.5">'
        + anim("cx", kx, DUR, ease=False)
        + anim("cy", ky, DUR, ease=False)
        + "</circle>"
    )
    trail = (
        f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="{C["amber"]}" '
        f'stroke-width="2" stroke-dasharray="4 3"/>'
    )
    return group(trail, anims=fade(t0, t1 + 0.6, DUR, f=0.25)) + group(dot, anims=fade(t0 - 0.1, t1 + 0.3, DUR, f=0.15))


body.append(token(6, 4.2, 6.0))
body.append(token(4, 8.7, 9.9))
body.append(token(2, 11.0, 12.2))
body.append(token(6, 13.8, 15.0))
out_lab = text(BCX, layer_y(L) - 12, "output", size=11, fill=C["amber"], weight=700, anchor="middle")
body.append(group(out_lab, anims=fade(4.2, OUT, DUR)))

# ---------------- right panel: load + accuracy/memory chart
RX = 300
body.append(f'<line x1="{RX-10}" y1="58" x2="{RX-10}" y2="286" stroke="{C["line"]}"/>')
load_lab = text(RX, 70, "request load", size=11.5, fill=C["muted"], weight=600)
LOADW = 160
load_bg = f'<rect x="{RX}" y="76" width="{LOADW}" height="12" rx="6" fill="{C["gray_l"]}"/>'
lw = [(0, 0.3 * LOADW), (7.0, 0.3 * LOADW), (8.0, 0.62 * LOADW), (10.0, 0.62 * LOADW), (10.4, 0.95 * LOADW), (12.8, 0.95 * LOADW), (13.3, 0.3 * LOADW)]
load_fill = f'<rect x="{RX}" y="76" width="{lw[0][1]}" height="12" rx="6" fill="{C["red"]}">' + anim("width", lw, DUR) + "</rect>"
body.append(group(load_lab + load_bg + load_fill, anims=fade(0.4, OUT, DUR)))

# chart
CX0, CX1, CY0, CY1 = RX + 10, RX + 160, 112, 236
chart = (
    f'<line x1="{CX0}" y1="{CY1}" x2="{CX1+6}" y2="{CY1}" stroke="{C["faint"]}" marker-end="url(#ag)"/>'
    + f'<line x1="{CX0}" y1="{CY1}" x2="{CX0}" y2="{CY0-8}" stroke="{C["faint"]}" marker-end="url(#ag)"/>'
    + text(CX1 + 4, CY1 + 14, "memory", size=10.5, fill=C["muted"], anchor="end")
    + text(CX0 + 5, CY0 - 2, "accuracy", size=10.5, fill=C["muted"])
)
P1B = (CX0 + 14, CY1 - 18)
P8B = (CX1 - 8, CY0 + 14)
CFG = {2: (CX0 + 58, CY1 - 50), 4: (CX0 + 92, CY1 - 76), 6: (CX0 + 122, CY1 - 96)}


def star_pts(cx, cy, r=7):
    import math

    out = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        out.append(f"{cx + rr*math.cos(a):.1f},{cy + rr*math.sin(a):.1f}")
    return " ".join(out)


chart += f'<polygon points="{star_pts(*P1B)}" fill="{C["teal"]}"/>' + text(P1B[0] + 9, P1B[1] + 4, "1B", size=10.5, fill=C["teal"], weight=700)
chart += f'<polygon points="{star_pts(*P8B)}" fill="{C["blue"]}"/>' + text(P8B[0] - 10, P8B[1] + 4, "8B", size=10.5, fill=C["blue"], weight=700, anchor="end")
for i, (x, y) in CFG.items():
    chart += f'<circle cx="{x}" cy="{y}" r="4.5" fill="{C["purple"]}"/>'
    chart += text(x - 8, y + 4, f"{i}/8", size=9.5, fill=C["purple"], anchor="end")
body.append(group(chart, anims=fade(6.5, OUT, DUR)))
chart_note = text(CX0, CY1 + 30, "★ original   ● stitched configs", size=10, fill=C["muted"])
body.append(group(chart_note, anims=fade(6.8, OUT, DUR)))

# ring on current config
ring_x = [(0, CFG[6][0])]
ring_y = [(0, CFG[6][1])]
for ts, i in SCHED[1:]:
    ring_x += [(ts, ring_x[-1][1]), (ts + TR, CFG[i][0])]
    ring_y += [(ts, ring_y[-1][1]), (ts + TR, CFG[i][1])]
ring = (
    f'<circle cx="{CFG[6][0]}" cy="{CFG[6][1]}" r="9" fill="none" stroke="{C["amber"]}" stroke-width="2.5">'
    + anim("cx", ring_x, DUR)
    + anim("cy", ring_y, DUR)
    + "</circle>"
)
body.append(group(ring, anims=fade(6.9, OUT, DUR)))

# model-level routing contrast
mlr = (
    f'<polyline points="{P8B[0]},{P8B[1]+10} {P8B[0]},{P1B[1]} {P1B[0]+30},{P1B[1]}" fill="none" '
    f'stroke="{C["muted"]}" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#as)"/>'
    + text(CX0 + 8, CY0 + 16, "model-level routing:", size=10, fill=C["muted"], weight=600)
    + text(CX0 + 8, CY0 + 29, "jumps 8B \u2192 1B", size=10, fill=C["muted"])
)
body.append(group(mlr, anims=fade(12.7, OUT, DUR)))

svg = svg_doc(
    W,
    H,
    "".join(body),
    defs=defs,
    title="StitchLLM: serving LLMs one block at a time",
    desc="A request passes through the bottom decoder blocks of a large LLM, a trained stitching layer that maps hidden "
    "size 4096 to 2048, and the top blocks of a small LLM. As the request load rises, the scheduler moves the stitch "
    "point to use fewer large-model blocks, trading accuracy gradually instead of jumping between model sizes.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes")
