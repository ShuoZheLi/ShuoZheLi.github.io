"""GASP: Guided Adversarial Self-Play (polluter vs. agent within one model, with in-distribution repair guidance)."""

import sys
from svganim import C, anim, anim_tf, fade, text, group, svg_doc, caption_track, arrow_marker

DUR = 16.0
W, H = 480, 300
OUT = 15.55

body = []
defs = arrow_marker("ag", C["muted"]) + arrow_marker("ab", C["blue"]) + arrow_marker("ar", C["red"])

body.append(
    caption_track(
        [
            (0.0, 2.75, "1", "Sample a correct trace on a problem it can solve"),
            (2.85, 5.45, "2", "Polluter (the same model) corrupts a local window"),
            (5.55, 9.45, "3", "Agent must continue from the polluted context"),
            (9.55, 13.25, "4", "Guidance: imitate the model's own repair"),
            (13.35, OUT, "", "One model, two roles → an adaptive curriculum"),
        ],
        DUR,
    )
)


def block(x, y, w, h, label, fill, stroke, tcol, size=12.5, weight=700):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
        + text(x + w / 2, y + h / 2 + 4.5, label, size=size, fill=tcol, weight=weight, anchor="middle")
    )


# ---- Row A: clean trace ------------------------------------------------------
BW, BH, GAP = 56, 28, 10
X0, YA = 47, 56
xs = [X0 + i * (BW + GAP) for i in range(6)]
labels = ["q", "s₁", "s₂", "s₃", "s₄", "a* ✓"]
for i, x in enumerate(xs):
    t_in = 0.3 + 0.32 * i
    if i == 0:
        b = block(x, YA, BW, BH, "q", C["gray_l"], C["faint"], C["ink"])
    elif i == 5:
        b = block(x, YA, BW, BH, labels[i], C["green_l"], C["green"], C["green"])
    else:
        b = block(x, YA, BW, BH, labels[i], "#f0fdf4", "#86efac", C["ink"])
    t_out = 3.75 if i >= 4 else OUT  # clean continuation after the window is removed
    body.append(group(b, anims=fade(t_in, t_out, DUR, f=0.3)))

# prefix / window brackets
br = (
    f'<path d="M{xs[0]},{YA+BH+5} v5 H{xs[2]+BW} v-5" fill="none" stroke="{C["muted"]}" stroke-width="1.2"/>'
    + text((xs[0] + xs[2] + BW) / 2, YA + BH + 20, "shared prefix c₀:α", size=11, fill=C["muted"], anchor="middle")
    + f'<path d="M{xs[3]},{YA+BH+5} v5 H{xs[3]+BW} v-5" fill="none" stroke="{C["muted"]}" stroke-width="1.2"/>'
    + text(xs[3] + BW / 2, YA + BH + 20, "window", size=11, fill=C["muted"], anchor="middle")
)
body.append(group(br, anims=fade(2.1, 5.4, DUR)))

# ---- polluted window drops onto s3 ----------------------------------------------
poll = block(xs[3], YA, BW, BH, "s₃′ ✗", C["red_l"], C["red"], C["red"])
body.append(
    group(
        poll,
        anims=fade(3.15, OUT, DUR, f=0.3) + anim_tf("translate", [(3.15, (0, -18)), (3.75, (0, 0))], DUR),
    )
)
ptag = (
    f'<rect x="{xs[3]+BW+8}" y="{YA+2}" width="126" height="24" rx="12" fill="{C["red"]}"/>'
    + text(xs[3] + BW + 71, YA + 18.5, "polluter: misleading", size=11, fill="#fff", weight=700, anchor="middle")
)
body.append(group(ptag, anims=fade(3.9, 5.4, DUR)))

# ---- Row B / C: agent rollouts ----------------------------------------------------
YB, YC = 112, 158
RX = xs[4]  # rollouts start where s4 used to be
SW, SG = 44, 6
cx3 = xs[3] + BW / 2


def elbow(y, t_in, color):
    return group(
        f'<path d="M{cx3},{YA+BH} V{y+BH/2} H{RX-3}" fill="none" stroke="{color}" stroke-width="1.6" marker-end="url(#ag)"/>',
        anims=fade(t_in, OUT, DUR, f=0.3),
    )


body.append(elbow(YB, 5.8, C["faint"]))
b1 = block(RX, YB, SW, BH, "s₄′", C["red_l"], C["red"], C["red"], size=12)
b2 = block(RX + SW + SG, YB, SW, BH, "a ✗", C["red_l"], C["red"], C["red"], size=12)
body.append(group(b1, anims=fade(6.05, OUT, DUR, f=0.3)))
body.append(group(b2, anims=fade(6.4, OUT, DUR, f=0.3)))
labB = (
    text(xs[0], YB + 12, "follows the error", size=12, fill=C["red"], weight=700)
    + text(xs[0], YB + 26, "→ polluter reward +1", size=11.5, fill=C["muted"])
)
body.append(group(labB, anims=fade(6.7, OUT, DUR)))

body.append(elbow(YC, 7.3, C["faint"]))
c1 = block(RX, YC, SW, BH, "wait!", C["amber_l"], C["amber"], C["amber"], size=11.5)
c2 = block(RX + SW + SG, YC, SW, BH, "fix", C["blue_l"], C["blue"], C["blue"], size=12)
c3 = block(RX + 2 * (SW + SG), YC, SW, BH, "a* ✓", C["green_l"], C["green"], C["green"], size=12)
body.append(group(c1, anims=fade(7.55, OUT, DUR, f=0.3)))
body.append(group(c2, anims=fade(7.95, OUT, DUR, f=0.3)))
body.append(group(c3, anims=fade(8.35, OUT, DUR, f=0.3)))
labC = (
    text(xs[0], YC + 12, "detects and repairs", size=12, fill=C["green"], weight=700)
    + text(xs[0], YC + 26, "→ agent reward +1  (rare at first)", size=11.5, fill=C["muted"])
)
body.append(group(labC, anims=fade(8.6, OUT, DUR)))

# glow on the fix block during guidance
glow = (
    f'<rect x="{RX+SW+SG-4}" y="{YC-4}" width="{SW+8}" height="{BH+8}" rx="9" fill="none" stroke="{C["blue"]}" stroke-width="2.5">'
    + anim("stroke-opacity", [(10.6, 0), (11.0, 1), (11.5, 0.25), (12.0, 1), (12.5, 0.25), (13.0, 1), (13.25, 0)], DUR)
    + "</rect>"
)
body.append(group(glow, anims=fade(10.5, 13.3, DUR)))

# ---- bottom panels ----------------------------------------------------------------------
PY = 204
# phase 3: rewards
rew = (
    f'<rect x="{xs[0]}" y="{PY}" width="386" height="74" rx="10" fill="{C["card"]}" stroke="{C["line"]}"/>'
    + text(xs[0] + 14, PY + 24, "Outcome rewards only (no human labels, no teacher):", size=12, fill=C["ink"], weight=600)
    + text(xs[0] + 14, PY + 46, "agent:     r = 1[ a = a* ]", size=12.5, fill=C["blue"], weight=700)
    + text(xs[0] + 14, PY + 64, "polluter: r = 1 − r_agent", size=12.5, fill=C["red"], weight=700)
    + text(xs[0] + 372, PY + 56, "both trained with GRPO", size=11, fill=C["muted"], anchor="end")
)
body.append(group(rew, anims=fade(6.0, 9.4, DUR)))

# phase 4: in-distribution repair guidance
g = (
    f'<rect x="{xs[0]}" y="{PY}" width="386" height="88" rx="10" fill="{C["card"]}" stroke="{C["line"]}"/>'
    + text(xs[0] + 12, PY + 20, "Shown clean s₃ vs. polluted s₃′, the model", size=11.5, fill=C["ink"])
    + text(xs[0] + 12, PY + 35, "writes its own fix; the agent imitates it", size=11.5, fill=C["ink"])
    + text(xs[0] + 12, PY + 50, "under the polluted context:", size=11.5, fill=C["ink"])
    + text(xs[0] + 12, PY + 69, "↑ log πθ( fix | q, prefix, s₃′ )", size=12.5, fill=C["blue"], weight=700)
)
# likelihood comparison bars
LX = xs[0] + 262
g += text(LX + 55, PY + 18, "πθ(fix | polluted ctx)", size=10.5, fill=C["muted"], anchor="middle")
g += f'<line x1="{LX}" y1="{PY+70}" x2="{LX+112}" y2="{PY+70}" stroke="{C["faint"]}"/>'
bar_self = (
    f'<rect x="{LX+12}" y="{PY+70}" width="30" height="0" rx="3" fill="{C["blue"]}">'
    + anim("height", [(10.3, 0), (11.0, 40), (OUT, 40)], DUR)
    + anim("y", [(10.3, PY + 70), (11.0, PY + 30), (OUT, PY + 30)], DUR)
    + "</rect>"
)
bar_teacher = (
    f'<rect x="{LX+68}" y="{PY+70}" width="30" height="0" rx="3" fill="{C["faint"]}">'
    + anim("height", [(10.3, 0), (11.0, 5), (OUT, 5)], DUR)
    + anim("y", [(10.3, PY + 70), (11.0, PY + 65), (OUT, PY + 65)], DUR)
    + "</rect>"
)
g += bar_self + bar_teacher
g += text(LX + 27, PY + 83, "self fix", size=10, fill=C["blue"], weight=700, anchor="middle")
g += text(LX + 83, PY + 83, "teacher fix", size=10, fill=C["muted"], anchor="middle")
body.append(group(g, anims=fade(9.7, 13.3, DUR)))

# phase 5: roles loop
cxL, cxR, cy = 150, 330, PY + 36
loop = (
    f'<rect x="{cxL-62}" y="{cy-17}" width="124" height="34" rx="17" fill="{C["red_l"]}" stroke="{C["red"]}" stroke-width="1.5"/>'
    + text(cxL, cy + 5, "Polluter πθ", size=13, fill=C["red"], weight=700, anchor="middle")
    + f'<rect x="{cxR-62}" y="{cy-17}" width="124" height="34" rx="17" fill="{C["blue_l"]}" stroke="{C["blue"]}" stroke-width="1.5"/>'
    + text(cxR, cy + 5, "Agent πθ", size=13, fill=C["blue"], weight=700, anchor="middle")
    + f'<path d="M{cxL+40},{cy-19} C{cxL+80},{cy-44} {cxR-80},{cy-44} {cxR-40},{cy-19}" fill="none" stroke="{C["red"]}" stroke-width="1.6" marker-end="url(#ar)"/>'
    + text(240, cy - 47, "harder corruptions", size=11, fill=C["red"], weight=600, anchor="middle")
    + f'<path d="M{cxR-40},{cy+19} C{cxR-80},{cy+44} {cxL+80},{cy+44} {cxL+40},{cy+19}" fill="none" stroke="{C["blue"]}" stroke-width="1.6" marker-end="url(#ab)"/>'
    + text(240, cy + 50, "stronger detect-and-repair", size=11, fill=C["blue"], weight=600, anchor="middle")
    + text(240, cy + 5, "shared θ", size=11.5, fill=C["muted"], anchor="middle")
)
body.append(group(loop, anims=fade(13.4, OUT, DUR)))

svg = svg_doc(
    W,
    H,
    "".join(body),
    defs=defs,
    title="Guided Adversarial Self-Play (GASP)",
    desc="A single model plays a polluter that corrupts a window of its own correct reasoning trace and an agent that must "
    "detect and repair the corruption to reach the right answer, trained with outcome rewards; self-generated repairs are "
    "imitated as in-distribution guidance.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes")
