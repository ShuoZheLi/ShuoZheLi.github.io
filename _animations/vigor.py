"""VIGOR: recover a lost/corrupted cloud-gaming frame on the client using game states (projected object vertices):
decoder mask -> optical flow from game states t-1 -> t -> warp frame t-1, enhance + inpaint -> keep decoded blocks."""

import random
import sys

from svganim import C, anim, fade, text, group, svg_doc, caption_track

DUR = 16.0
W, H = 480, 300
OUT = 15.5
T1, T2, T3 = 3.6, 7.2, 10.8
FW, FH = 128, 72
PAN = 16  # camera pans right -> scene shifts left by PAN px between t-1 and t

A = (14, 58)  # frame t-1
B = (176, 58)  # frame t (corrupted)
E = (338, 58)  # recovered frame t
GC = (14, 178)  # game state t-1
GD = (176, 178)  # game state t

MB = 16
LOST = [(r, c) for r in range(5) for c in range(8) if r * 8 + c >= 2 * 8 + 3]  # contiguous slice loss


# ---------------------------------------------------------------- scene (frame-local coords, before camera offset)
def scene(off):
    s = f'<g transform="translate({off},0)">'
    s += '<polygon points="-10,46 10,30 26,38 44,24 66,40 90,28 118,42 140,30 170,46" fill="#cbd5e1"/>'
    s += '<rect x="-10" y="44" width="190" height="30" fill="#a3b18a"/>'
    s += '<path d="M-10,58 Q40,52 70,60 T180,56 L180,72 L-10,72 z" fill="#c2a27a"/>'
    # house
    s += '<rect x="18" y="28" width="30" height="20" fill="#b45309"/>'
    s += '<line x1="18" y1="33" x2="48" y2="33" stroke="#78350f" stroke-width="0.8"/>'
    s += '<line x1="18" y1="38" x2="48" y2="38" stroke="#78350f" stroke-width="0.8"/>'
    s += '<line x1="18" y1="43" x2="48" y2="43" stroke="#78350f" stroke-width="0.8"/>'
    s += '<polygon points="13,29 33,15 53,29" fill="#78350f"/>'
    s += '<rect x="29" y="38" width="7" height="10" fill="#451a03"/>'
    # tree
    s += '<rect x="70" y="34" width="4" height="14" fill="#713f12"/>'
    s += '<circle cx="72" cy="29" r="10" fill="#15803d"/><circle cx="66" cy="33" r="6" fill="#166534"/>'
    # torch / flag pole
    s += '<rect x="99" y="22" width="2.5" height="26" fill="#57534e"/>'
    s += '<polygon points="101.5,22 112,25 101.5,28" fill="#dc2626"/>'
    # new hut (only visible after the pan)
    s += '<rect x="136" y="32" width="24" height="16" fill="#a16207"/>'
    s += '<polygon points="132,33 148,22 164,33" fill="#713f12"/>'
    s += '<rect x="144" y="40" width="6" height="8" fill="#451a03"/>'
    s += "</g>"
    return s


def frame_bg():
    return f'<rect x="0" y="0" width="{FW}" height="{FH}" fill="url(#vgSky)"/>'


def framed(pos, inner, clip_id, border=C["muted"]):
    x, y = pos
    return (
        f'<g transform="translate({x},{y})">'
        f'<g clip-path="url(#{clip_id})">{inner}</g>'
        f'<rect x="0" y="0" width="{FW}" height="{FH}" rx="3" fill="none" stroke="{border}" stroke-width="1.2"/>'
        "</g>"
    )


# ---------------------------------------------------------------- game-state point clouds
rng = random.Random(5)
objects = [
    # (color, sampler list)
    ("#4ade80", [("rect", -10, 45, 190, 4, 140)]),  # grass band
    ("#9ca3af", [("rect", -10, 50, 190, 22, 70)]),  # ground
    ("#fdba74", [("rect", 18, 28, 30, 20, 60), ("tri", (13, 29), (33, 15), (53, 29), 30)]),  # house
    ("#86efac", [("circ", 72, 29, 10, 40), ("rect", 70, 34, 4, 14, 6)]),  # tree
    ("#f87171", [("rect", 99, 22, 3, 26, 10), ("tri", (101.5, 22), (112, 25), (101.5, 28), 10)]),  # flag
    ("#fcd34d", [("rect", 136, 32, 24, 16, 34), ("tri", (132, 33), (148, 22), (164, 33), 18)]),  # new hut
]


def sample_tri(a, b, c):
    while True:
        u, v = rng.random(), rng.random()
        if u + v <= 1:
            return (a[0] + u * (b[0] - a[0]) + v * (c[0] - a[0]), a[1] + u * (b[1] - a[1]) + v * (c[1] - a[1]))


pts = []
for col, prims in objects:
    for pr in prims:
        kind = pr[0]
        if kind == "rect":
            _, x, y, w, h, n = pr
            for _ in range(n):
                pts.append((x + rng.random() * w, y + rng.random() * h, col))
        elif kind == "circ":
            _, cx, cy, r, n = pr
            k = 0
            while k < n:
                px, py = cx + (2 * rng.random() - 1) * r, cy + (2 * rng.random() - 1) * r
                if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                    pts.append((px, py, col))
                    k += 1
        else:
            _, a, b, c, n = pr
            for _ in range(n):
                px, py = sample_tri(a, b, c)
                pts.append((px, py, col))


def gamestate(off):
    s = f'<rect x="0" y="0" width="{FW}" height="{FH}" fill="#0b0f19"/>'
    s += "".join(
        f'<rect x="{x+off:.1f}" y="{y:.1f}" width="1.3" height="1.3" fill="{c}"/>' for x, y, c in pts if -2 < x + off < FW + 2
    )
    return s


body = []
body.append(
    caption_track(
        [
            (0.0, T1 - 0.1, "1", "Late or lost packets corrupt frame t"),
            (T1, T2 - 0.1, "2", "Decoder mask + game states on the client"),
            (T2, T3 - 0.1, "3", "Optical flow from game states t−1 → t"),
            (T3, OUT, "4", "Warp t−1, enhance + inpaint, keep decoded"),
        ],
        DUR,
    )
)

clips = (
    f'<clipPath id="vgF"><rect x="0" y="0" width="{FW}" height="{FH}" rx="3"/></clipPath>'
    f'<clipPath id="vgL"><rect x="0" y="0" width="{FW-PAN}" height="{FH}"/></clipPath>'
    f'<clipPath id="vgR"><rect x="{FW-PAN}" y="0" width="{PAN}" height="{FH}"/></clipPath>'
)


def label(pos, s, t_in, t_out, dy=84, col=None):
    x, y = pos
    return group(text(x + FW / 2, y + dy, s, size=11, fill=col or C["ink"], weight=700, anchor="middle"),
                 anims=fade(t_in, t_out, DUR))


# ---- frame t-1
body.append(group(framed(A, frame_bg() + scene(0), "vgF"), anims=fade(0.3, OUT, DUR)))
body.append(label(A, "frame t−1 (received)", 0.3, OUT))

# ---- frame t (decoded then corrupted)
lost_rects = "".join(
    f'<rect x="{c*MB}" y="{r*MB}" width="{MB}" height="{MB}" fill="#6b7280"/>' for r, c in LOST
)
glitch = "".join(
    f'<rect x="{c*MB + 3}" y="{r*MB + 5}" width="10" height="3" fill="#4b5563"/>' for r, c in LOST if (r + c) % 2 == 0
)
corrupt = group(lost_rects + glitch, anims=fade(1.8, OUT, DUR, f=0.25))
mask_rects = "".join(
    f'<rect x="{c*MB+0.5}" y="{r*MB+0.5}" width="{MB-1}" height="{MB-1}" fill="#dc2626" fill-opacity="0.28" stroke="#dc2626" stroke-width="0.8"/>'
    for r, c in LOST
)
mask = group(mask_rects, anims=fade(T1 + 0.3, OUT, DUR))
body.append(group(framed(B, frame_bg() + scene(-PAN) + corrupt + mask, "vgF"), anims=fade(0.8, OUT, DUR)))
body.append(label(B, "frame t (corrupted)", 0.8, OUT))
body.append(group(text(B[0] + FW - 4, B[1] - 6, "✕ packets late / lost", size=10.5, fill=C["red"], weight=700, anchor="end"),
                  anims=fade(1.8, T1 - 0.1, DUR)))
body.append(group(text(B[0] + FW - 4, B[1] - 6, "mask: bad macroblocks", size=10.5, fill=C["red"], weight=700, anchor="end"),
                  anims=fade(T1 + 0.3, T2 - 0.1, DUR)))

# ---- game states
body.append(group(framed(GC, gamestate(0), "vgF", border="#334155"), anims=fade(4.4, OUT, DUR)))
body.append(label(GC, "game state t−1", 4.4, OUT))
body.append(group(framed(GD, gamestate(-PAN), "vgF", border="#334155"), anims=fade(5.0, OUT, DUR)))
body.append(label(GD, "game state t", 5.0, OUT))

# flow arrows on game state t (step 3+)
fl = ""
for x0, y0 in ((40, 36), (78, 28), (106, 30), (60, 52), (20, 56), (122, 40)):
    xs, xe = x0, x0 - PAN
    if xe < 2:
        continue
    fl += (
        f'<line x1="{GD[0]+xs}" y1="{GD[1]+y0}" x2="{GD[0]+xe+3}" y2="{GD[1]+y0}" stroke="#c084fc" stroke-width="2"/>'
        f'<polygon points="{GD[0]+xe},{GD[1]+y0} {GD[0]+xe+5},{GD[1]+y0-3} {GD[0]+xe+5},{GD[1]+y0+3}" fill="#c084fc"/>'
    )
body.append(group(fl, anims=fade(T2 + 0.8, OUT, DUR)))
ar = f'stroke="{C["purple"]}" stroke-width="1.6" fill="none" marker-end="url(#vgArrP)"'
cd = f'<path d="M{GC[0]+FW+4},{GC[1]+FH/2} L{GD[0]-4},{GD[1]+FH/2}" {ar}/>'
cd += text((GC[0] + FW + GD[0]) / 2, GC[1] + FH / 2 - 7, "flow", size=10.5, fill=C["purple"], weight=700, anchor="middle")
body.append(group(cd, anims=fade(T2 + 0.3, OUT, DUR)))

# ---- recovered frame (step 4 builds it)
ex, ey = E
outline = f'<rect x="{ex}" y="{ey}" width="{FW}" height="{FH}" rx="3" fill="{C["gray_l"]}" stroke="{C["muted"]}" stroke-width="1.2" stroke-dasharray="4 3"/>'
outline += text(ex + FW / 2, ey + FH / 2 + 5, "?", size=20, fill=C["faint"], weight=700, anchor="middle")
body.append(group(outline, anims=fade(0.3, T3 + 0.6, DUR)))
TW_, TE_, TD_, TOK = T3 + 0.3, T3 + 1.5, T3 + 2.7, T3 + 3.7
warped = f'<g clip-path="url(#vgL)">{frame_bg()}{scene(-PAN)}</g>'
haze = f'<rect x="0" y="0" width="{FW-PAN}" height="{FH}" fill="#ffffff" opacity="0.38">' + anim(
    "opacity", [(0, 0.38), (TE_, 0.38), (TE_ + 0.6, 0)], DUR) + "</rect>"
hole = (
    f'<rect x="{FW-PAN}" y="0" width="{PAN}" height="{FH}" fill="url(#vgHatch)"/>'
)
inpaint = group(f'<g clip-path="url(#vgR)">{frame_bg()}{scene(-PAN)}</g>', anims=fade(TE_, OUT, DUR, f=0.6))
inp_box = group(
    f'<rect x="{FW-PAN+0.8}" y="0.8" width="{PAN-1.6}" height="{FH-1.6}" fill="none" stroke="{C["green"]}" stroke-width="1.6"/>',
    anims=fade(TE_, TD_ + 0.4, DUR, f=0.3),
)
keep_rects = "".join(
    f'<rect x="{c*MB+0.6}" y="{r*MB+0.6}" width="{MB-1.2}" height="{MB-1.2}" fill="none" stroke="{C["blue"]}" stroke-width="0.8" stroke-opacity="0.75"/>'
    for r in range(5) for c in range(8) if (r, c) not in LOST and r * 16 < FH
)
keep = group(keep_rects, anims=fade(TD_, TOK + 0.3, DUR, f=0.3))
rec = (
    f'<g transform="translate({ex},{ey})"><g clip-path="url(#vgF)">'
    + group(warped + haze, anims=fade(TW_, OUT, DUR, f=0.5))
    + group(hole, anims=fade(TW_, TE_ + 0.6, DUR, f=0.5))
    + inpaint + inp_box + keep
    + "</g>"
    + f'<rect x="0" y="0" width="{FW}" height="{FH}" rx="3" fill="none" stroke="{C["muted"]}" stroke-width="1.2"/>'
    + "</g>"
)
body.append(group(rec, anims=fade(TW_, OUT, DUR)))
body.append(label(E, "recovered frame t", 0.3, T3 + 3.6))
body.append(label(E, "✓ recovered frame t", T3 + 3.7, OUT, col=C["green"]))

# stage tags above E during step 4
for t_in, t_out, s, col in (
    (TW_, TE_ - 0.05, "1 · warp t−1 by the flow", C["purple"]),
    (TE_, TD_ - 0.05, "2 · enhance + inpaint", C["green"]),
    (TD_, OUT, "3 · paste decoded blocks", C["blue"]),
):
    body.append(group(text(ex + FW / 2, ey - 6, s, size=10.5, fill=col, weight=700, anchor="middle"),
                      anims=fade(t_in, t_out, DUR, f=0.25)))

# arrows into E
ap = f'stroke="{C["purple"]}" stroke-width="1.6" fill="none" marker-end="url(#vgArrP)"'
warp_arc = f'<path d="M{A[0]+FW/2},{A[1]-3} C{A[0]+FW/2},{A[1]-18} {ex-14},{A[1]-18} {ex-4},{ey+12}" {ap}/>'
body.append(group(warp_arc, anims=fade(TW_, TE_ + 0.2, DUR)))
ag = f'stroke="{C["green"]}" stroke-width="1.6" fill="none" marker-end="url(#vgArrG)"'
body.append(group(f'<path d="M{GD[0]+FW+3},{GD[1]+10} L{ex-4},{ey+FH-8}" {ag}/>', anims=fade(TE_, TD_ + 0.2, DUR)))
ab = f'stroke="{C["blue"]}" stroke-width="1.6" fill="none" marker-end="url(#vgArrB)"'
body.append(group(f'<path d="M{B[0]+FW+3},{B[1]+FH/2} L{ex-4},{ey+FH/2}" {ab}/>', anims=fade(TD_, OUT, DUR)))

# ---- explanation text (bottom right)
TX, TY = 336, 196


def para(rows, t_in, t_out):
    out, y = "", TY
    for s, kind in rows:
        col = {"b": C["ink"], "r": C["red"], "p": C["purple"], "g": C["green"], "": C["ink"]}[kind]
        out += text(TX, y, s, size=10.5, fill=col, weight=700 if kind else 400)
        y += 15
    body.append(group(out, anims=fade(t_in, t_out, DUR)))


para([("Cloud gaming: &lt;80 ms", "b"), ("budget. Retransmits", ""), ("come too late; FEC", ""),
      ("wastes bandwidth.", ""), ("→ recover on the client", "r")], 0.2, T1 - 0.1)
para([("H.264 decoder (modified)", "b"), ("masks bad macroblocks.", ""), ("Game states: object", ""),
      ("vertices projected to", ""), ("2D on the client GPU", "")], T1, T2 - 0.1)
para([("Flow from clean game", "b"), ("states, not from the", ""), ("corrupted pixels", ""),
      ("(pyramid CNN, SPyNet", ""), ("initialization)", "")], T2, T3 - 0.1)
para([("Game states add up to", "b"), ("+5.4 dB PSNR", "g"), ("real time on iPhone 12", ""),
      ("and on a laptop", "")], T3, OUT)

defs = (
    '<linearGradient id="vgSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7dd3fc"/>'
    '<stop offset="0.6" stop-color="#e0f2fe"/></linearGradient>'
    '<pattern id="vgHatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
    '<rect width="6" height="6" fill="#e5e7eb"/><line x1="0" y1="0" x2="0" y2="6" stroke="#9ca3af" stroke-width="2"/></pattern>'
    + clips
    + "".join(
        f'<marker id="{mid}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
        for mid, col in (("vgArrP", C["purple"]), ("vgArrG", C["green"]), ("vgArrB", C["blue"]))
    )
)

svg = svg_doc(
    W,
    H,
    "".join(body),
    title="VIGOR: reviving cloud gaming sessions",
    desc="Frame t of a cloud-gamed scene arrives with missing macroblocks. The decoder marks them with a mask, and the "
    "client renders lightweight game states (projected object points) for frames t−1 and t. Optical flow computed "
    "from the game states warps frame t−1; enhancement and inpainting fill content that warping cannot reach, and "
    "the correctly decoded blocks of frame t are kept, giving the recovered frame.",
    defs=defs,
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes", len(pts), "points")
