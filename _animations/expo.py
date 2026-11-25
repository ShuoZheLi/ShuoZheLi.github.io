"""ExPO: self-explanations conditioned on the ground-truth answer as in-distribution positive samples."""

import math
import sys
from svganim import C, anim, fade, text, group, svg_doc, caption_track, arrow_marker

DUR = 16.0
W, H = 480, 300
OUT = 15.5

X0, X1 = 40, 460
AX = 228            # axis y
PEAK = 116          # peak height in px
SIG = 58.0
MU0, MU1 = 178.0, 322.0
GREEN_X = 282       # correct region starts here
T_SHIFT0, T_SHIFT1 = 11.0, 12.6

body = []
defs = arrow_marker("ae", C["muted"]) + arrow_marker("ab", C["blue"])

body.append(
    caption_track(
        [
            (0.0, 3.45, "1", "Hard problem: every sampled answer is wrong"),
            (3.55, 6.85, "2", "Expert CoT: correct, but far off-policy"),
            (6.95, 10.65, "3", "ExPO: let the model explain the known answer"),
            (10.75, OUT, "4", "Train on it → policy moves to correct reasoning"),
        ],
        DUR,
    )
)


def density(x, mu):
    return PEAK * math.exp(-0.5 * ((x - mu) / SIG) ** 2)


XS = [X0 + (X1 - X0) * i / 70 for i in range(71)]


def curve_d(mu, closed=False):
    pts = [(x, AX - density(x, mu)) for x in XS]
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f} " + " ".join(f"L{x:.1f},{y:.1f}" for x, y in pts[1:])
    if closed:
        d += f" L{X1},{AX} L{X0},{AX} Z"
    return d


# regions on the axis
regions = (
    f'<rect x="{X0}" y="{AX+3}" width="{GREEN_X-X0}" height="7" fill="{C["red_l"]}" stroke="{C["red"]}" stroke-width="0.8"/>'
    + f'<rect x="{GREEN_X}" y="{AX+3}" width="{X1-GREEN_X}" height="7" fill="{C["green_l"]}" stroke="{C["green"]}" stroke-width="0.8"/>'
    + text((X0 + GREEN_X) / 2, AX + 25, "reasoning paths → wrong answer", size=11.5, fill=C["red"], weight=600, anchor="middle")
    + text((GREEN_X + X1) / 2, AX + 25, "→ correct answer a*", size=11.5, fill=C["green"], weight=600, anchor="middle")
    + f'<line x1="{X0}" y1="{AX}" x2="{X1}" y2="{AX}" stroke="{C["faint"]}"/>'
)
body.append(group(regions, anims=fade(0.15, OUT, DUR)))

# policy density (area + line), shifting in phase 4
N_SH = 10
shift, shift_c = [(0, curve_d(MU0)), (T_SHIFT0, curve_d(MU0))], [(0, curve_d(MU0, True)), (T_SHIFT0, curve_d(MU0, True))]
for k in range(1, N_SH + 1):
    u = k / N_SH
    u_e = 0.5 - 0.5 * math.cos(math.pi * u)  # ease in-out on the mean
    mu = MU0 + (MU1 - MU0) * u_e
    t = T_SHIFT0 + (T_SHIFT1 - T_SHIFT0) * u
    shift.append((t, curve_d(mu)))
    shift_c.append((t, curve_d(mu, True)))
shift += [(OUT, curve_d(MU1)), (OUT + 0.45, curve_d(MU0))]
shift_c += [(OUT, curve_d(MU1, True)), (OUT + 0.45, curve_d(MU0, True))]
area = f'<path d="{curve_d(MU0, True)}" fill="{C["blue_l"]}" fill-opacity="0.75">' + anim("d", shift_c, DUR, ease=False) + "</path>"
line = f'<path d="{curve_d(MU0)}" fill="none" stroke="{C["blue"]}" stroke-width="2.4">' + anim("d", shift, DUR, ease=False) + "</path>"
label = text(MU0 - 48, AX - PEAK + 14, "policy πθ(c | q)", size=12, fill=C["blue"], weight=700, anchor="end")
body.append(group(area + line, anims=fade(0.1, OUT, DUR, f=0.4)))
body.append(group(label, anims=fade(0.3, T_SHIFT0 - 0.2, DUR)))
label2 = text(MU1 - 48, AX - PEAK + 14, "updated policy", size=12, fill=C["blue"], weight=700, anchor="end")
body.append(group(label2, anims=fade(T_SHIFT1, OUT, DUR)))


def sample_marks(xs, t0, t_out, mu_for_y):
    out = ""
    for k, x in enumerate(xs):
        ok = x >= GREEN_X
        col = C["green"] if ok else C["red"]
        sym = "✓" if ok else "✗"
        ti = t0 + 0.16 * k
        y_curve = AX - density(x, mu_for_y)
        dot = (
            f'<circle cx="{x}" cy="{y_curve}" r="4.2" fill="{col}" stroke="#fff" stroke-width="1"/>'
            + f'<line x1="{x}" y1="{y_curve+5}" x2="{x}" y2="{AX-2}" stroke="{col}" stroke-width="1" stroke-dasharray="2 2"/>'
            + text(x, y_curve - 8, sym, size=12, fill=col, weight=700, anchor="middle")
        )
        out += group(dot, anims=fade(ti, t_out, DUR, f=0.2))
    return out


# phase 1: on-policy samples, all wrong
body.append(sample_marks([112, 140, 158, 172, 186, 200, 222, 246], 0.6, 3.35, MU0))
p1 = (
    text(462, 70, "all samples wrong → GRPO", size=12, fill=C["red"], weight=700, anchor="end")
    + text(462, 85, "advantage = 0: no learning signal", size=12, fill=C["red"], anchor="end")
)
body.append(group(p1, anims=fade(1.9, 3.4, DUR)))

# phase 2: expert CoT star far in the tail
XE = 440


def star(cx, cy, r, fill):
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append(f"{cx + rr*math.cos(ang):.1f},{cy + rr*math.sin(ang):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="#fff" stroke-width="1"/>'


exp_el = (
    star(XE, AX - 2, 9, C["muted"])
    + text(XE + 8, AX - 50, "expert CoT", size=12, fill=C["ink"], weight=700, anchor="end")
    + text(XE + 8, AX - 35, "πθ(c) ≈ 0 → tiny update", size=11.5, fill=C["muted"], anchor="end")
    + f'<line x1="{XE}" y1="{AX-30}" x2="{XE}" y2="{AX-14}" stroke="{C["muted"]}" stroke-width="1.2" marker-end="url(#ae)"/>'
)
body.append(group(exp_el, anims=fade(3.7, 10.5, DUR)))
exp_note = text(462, 70, "ΔJ ∝ πθ(c) · ‖∇log πθ(c)‖²", size=12, fill=C["muted"], weight=600, anchor="end")
body.append(group(exp_note, anims=fade(4.6, 6.8, DUR)))

# phase 3: self-explanation conditioned on a*
XS_ = 300
ys = AX - density(XS_, MU0)
prompt = (
    f'<rect x="262" y="52" width="200" height="44" rx="9" fill="{C["blue_l"]}" stroke="{C["blue"]}" stroke-width="1.3"/>'
    + text(362, 70, "prompt: question q + answer a*", size=11.5, fill=C["blue"], weight=700, anchor="middle")
    + text(362, 86, "→ self-explanation c̃ ~ πθ(· | q, a*)", size=11.5, fill=C["blue"], anchor="middle")
)
body.append(group(prompt, anims=fade(7.0, 10.6, DUR)))
arr = f'<path d="M335,98 C 330,130 312,150 {XS_+2},{ys-14}" fill="none" stroke="{C["blue"]}" stroke-width="1.5" marker-end="url(#ab)"/>'
body.append(group(arr, anims=fade(7.6, 10.6, DUR)))
self_star = (
    star(XS_, ys, 9, C["blue"])
    + f'<line x1="{XS_}" y1="{ys+8}" x2="{XS_}" y2="{AX-2}" stroke="{C["blue"]}" stroke-width="1.2" stroke-dasharray="2 2"/>'
)
body.append(group(self_star, anims=fade(8.0, T_SHIFT0, DUR)))
p3 = (
    text(X0 + 4, 70, "c̃ is likely under πθ (in-distribution)", size=11.5, fill=C["ink"], weight=600)
    + text(X0 + 4, 85, "and raises πθ(a* | q, c̃)", size=11.5, fill=C["ink"], weight=600)
)
body.append(group(p3, anims=fade(8.6, 10.6, DUR)))

# phase 4: positive sample -> shift; new samples now mixed / mostly correct
body.append(sample_marks([250, 272, 296, 310, 324, 338, 352, 372], 12.8, OUT, MU1))
p4 = (
    text(X0 + 4, 70, "c̃ used as a positive sample", size=11.5, fill=C["ink"], weight=600)
    + text(X0 + 4, 85, "in GRPO / DPO", size=11.5, fill=C["ink"], weight=600)
)
body.append(group(p4, anims=fade(10.8, OUT, DUR)))
p5 = text(462, 85, "correct samples appear → RL takes off", size=12, fill=C["green"], weight=700, anchor="end")
body.append(group(p5, anims=fade(13.9, OUT, DUR)))

svg = svg_doc(
    W,
    H,
    "".join(body),
    defs=defs,
    title="ExPO: self-explanation policy optimization",
    desc="On a hard problem all of the model's own samples are wrong, so GRPO gets no signal; an expert chain of thought is "
    "correct but has almost zero probability under the policy. ExPO conditions on the ground-truth answer to produce a "
    "self-explanation that is likely under the policy and makes the correct answer likely; training on it shifts the "
    "policy toward correct reasoning.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes")
