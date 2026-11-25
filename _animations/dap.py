"""DAP: Distillation-Aware Pruning — rank by irrecoverable damage D - R instead of immediate damage D."""

import sys
from svganim import C, anim, fade, text, group, svg_doc, caption_track, _fmt

DUR = 15.0
W, H = 480, 300

D = [0.30, 0.20, 0.70, 0.25, 0.55, 0.15]
R = [0.05, 0.18, 0.65, 0.02, 0.10, 0.03]
I = [d - r for d, r in zip(D, R)]
CONV = sorted(range(6), key=lambda i: D[i])[:3]   # smallest immediate damage
DAPSEL = sorted(range(6), key=lambda i: I[i])[:3]  # smallest irrecoverable damage
assert sorted(CONV) == [1, 3, 5] and sorted(DAPSEL) == [1, 2, 5]

BASE = 228.0
S = 200.0  # px per damage unit (left)
XS = [58 + 42 * i for i in range(6)]
BW = 24

RED = "#ef4444"
GREEN = "#22c55e"

T_GROW = (0.5, 2.1)
T_REPAIR = (3.3, 4.9)
T_CONV = 6.0
T_DAP = 9.4
T_END = 12.6
T_OUT = 14.55

body = []

# captions
body.append(
    caption_track(
        [
            (0.0, 3.05, "1", "Pruning weight wᵢ causes immediate damage Dᵢ"),
            (3.15, 5.85, "2", "Distilling from the teacher repairs a part Rᵢ"),
            (5.95, 9.25, "3", "Conventional pruning: remove the smallest D"),
            (9.35, 12.45, "4", "DAP: remove the smallest D − R (irrecoverable)"),
            (12.55, T_OUT, "", "Prune what the teacher can repair"),
        ],
        DUR,
    )
)

# axis + weight cells
body.append(f'<line x1="34" y1="{BASE}" x2="300" y2="{BASE}" stroke="{C["faint"]}" stroke-width="1"/>')
body.append(text(34, 62, "damage", size=11, fill=C["muted"]))
for i, x in enumerate(XS):
    # bars: red full D (grows), green R at bottom (grows later)
    t0 = T_GROW[0] + 0.12 * i
    h = D[i] * S
    red = (
        f'<rect x="{x-BW/2}" y="{BASE}" width="{BW}" height="0" fill="{RED}" rx="2">'
        + anim("height", [(t0, 0), (t0 + 1.0, h), (T_OUT, h), (T_OUT + 0.4, 0)], DUR)
        + anim("y", [(t0, BASE), (t0 + 1.0, BASE - h), (T_OUT, BASE - h), (T_OUT + 0.4, BASE)], DUR)
        + "</rect>"
    )
    t1 = T_REPAIR[0] + 0.12 * i
    hr = R[i] * S
    green = (
        f'<rect x="{x-BW/2}" y="{BASE}" width="{BW}" height="0" fill="{GREEN}" rx="2">'
        + anim("height", [(t1, 0), (t1 + 1.0, hr), (T_OUT, hr), (T_OUT + 0.4, 0)], DUR)
        + anim("y", [(t1, BASE), (t1 + 1.0, BASE - hr), (T_OUT, BASE - hr), (T_OUT + 0.4, BASE)], DUR)
        + "</rect>"
    )
    body.append(red + green)

    # weight cell (teacher parameter) with prune markers
    cell = (
        f'<rect x="{x-12}" y="{BASE+7}" width="24" height="22" rx="4" fill="{C["purple_l"]}" stroke="{C["purple"]}" stroke-width="1.2"/>'
        + text(x, BASE + 22.5, f"w{i+1}", size=11, fill=C["purple"], weight=700, anchor="middle")
    )
    body.append(cell)

    # pruned cross (conventional, then DAP)
    for sel, t_a, t_b, col in ((CONV, T_CONV + 0.5, T_DAP - 0.15, C["orange"]), (DAPSEL, T_DAP + 0.5, T_OUT, C["teal"])):
        if i in sel:
            cross = (
                f'<path d="M{x-9},{BASE+10} L{x+9},{BASE+26} M{x+9},{BASE+10} L{x-9},{BASE+26}" stroke="{col}" stroke-width="2.4" stroke-linecap="round"/>'
            )
            top = BASE - D[i] * S - 7
            box = (
                f'<rect x="{x-17}" y="{top}" width="34" height="{BASE+34-top}" rx="6" fill="none" '
                f'stroke="{col}" stroke-width="2" stroke-dasharray="5 3"/>'
            )
            body.append(group(box + cross, anims=fade(t_a, t_b, DUR, f=0.3)))

# callout on w3 during the DAP phase
x3 = XS[2]
top3 = BASE - D[2] * S
callout = (
    text(x3 - 23, top3 + 10, "large D, but", size=11, fill=C["teal"], weight=700, anchor="end")
    + text(x3 - 23, top3 + 23, "the teacher can", size=11, fill=C["teal"], weight=700, anchor="end")
    + text(x3 - 23, top3 + 36, "repair most of it", size=11, fill=C["teal"], weight=700, anchor="end")
    + f'<path d="M{x3-21},{top3+19} L{x3-17},{top3+19}" stroke="{C["teal"]}" stroke-width="1.5"/>'
)
body.append(group(callout, anims=fade(T_DAP + 0.9, T_END - 0.1, DUR)))

# legend
legend = (
    f'<rect x="34" y="276" width="11" height="11" rx="2" fill="{RED}"/>'
    + text(50, 285.5, "irrecoverable  D − R", size=11, fill=C["muted"])
    + f'<rect x="170" y="276" width="11" height="11" rx="2" fill="{GREEN}"/>'
    + text(186, 285.5, "repaired by distillation  R", size=11, fill=C["muted"])
)
body.append(group(legend, anims=fade(T_REPAIR[0], T_OUT, DUR)))

# right panel: total damage of the pruned set, before -> after distillation
PX0 = 318
body.append(f'<line x1="{PX0}" y1="60" x2="{PX0}" y2="268" stroke="{C["line"]}" stroke-width="1"/>')
panel_title = (
    text(394, 62, "damage from the", size=11.5, fill=C["muted"], anchor="middle")
    + text(394, 76, "pruned weights", size=11.5, fill=C["muted"], anchor="middle")
)
body.append(group(panel_title, anims=fade(T_CONV, T_OUT, DUR)))
PS = 118.0
for k, (sel, t_start, xc, label, col) in enumerate(
    ((CONV, T_CONV + 0.7, 360, "Conv.", C["orange"]), (DAPSEL, T_DAP + 0.7, 430, "DAP", C["teal"]))
):
    dt = sum(D[i] for i in sel) * PS
    rt = sum(R[i] for i in sel) * PS
    it = sum(I[i] for i in sel) * PS
    tg0, tg1 = t_start, t_start + 0.8          # immediate damage appears
    tr0, tr1 = t_start + 1.05, t_start + 1.75  # teacher repair
    ts0, ts1 = t_start + 1.9, t_start + 2.5    # collapse to remaining damage
    red = (
        f'<rect x="{xc-17}" y="{BASE}" width="34" height="0" fill="{RED}" rx="3">'
        + anim("height", [(tg0, 0), (tg1, dt), (ts0, dt), (ts1, it), (T_OUT, it), (T_OUT + 0.4, 0)], DUR)
        + anim("y", [(tg0, BASE), (tg1, BASE - dt), (ts0, BASE - dt), (ts1, BASE - it), (T_OUT, BASE - it), (T_OUT + 0.4, BASE)], DUR)
        + "</rect>"
    )
    green = (
        f'<rect x="{xc-17}" y="{BASE}" width="34" height="0" fill="{GREEN}" rx="3">'
        + anim("height", [(tr0, 0), (tr1, rt), (ts0, rt), (ts1, 0)], DUR)
        + anim("y", [(tr0, BASE), (tr1, BASE - rt), (ts0, BASE - rt), (ts1, BASE)], DUR)
        + "</rect>"
    )
    lab = text(xc, BASE + 20, label, size=12.5, fill=col, weight=700, anchor="middle")
    body.append(red + green + group(lab, anims=fade(t_start, T_OUT, DUR)))
    # annotate stages
    stage1 = text(xc, BASE - dt - 6, "before", size=10, fill=C["muted"], anchor="middle")
    stage2 = text(xc, BASE - it - 6, "after", size=10, fill=C["muted"], anchor="middle")
    body.append(group(stage1, anims=fade(tg1, ts0, DUR, f=0.2)))
    body.append(group(stage2, anims=fade(ts1, T_OUT, DUR, f=0.2)))

# final verdict
verdict = (
    f'<rect x="333" y="104" width="122" height="20" rx="10" fill="{C["teal_l"]}"/>'
    + text(394, 118, "✓ DAP keeps less damage", size=10.5, fill=C["teal"], weight=700, anchor="middle")
)
body.append(group(verdict, anims=fade(T_END + 0.2, T_OUT, DUR)))

svg = svg_doc(
    W,
    H,
    "".join(body),
    title="Distillation-Aware Pruning (DAP)",
    desc="Conventional pruning removes the weights with the smallest immediate damage D. DAP removes the weights with the "
    "smallest irrecoverable damage D minus R, where R is what distillation from the teacher can repair, so the pruned "
    "student retains less damage after distillation.",
)
open(sys.argv[1], "w").write(svg)
print("wrote", sys.argv[1], len(svg), "bytes")
