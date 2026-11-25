"""Tiny helper for building looping SMIL-animated SVGs.

Every animated attribute is described by a list of (time_in_seconds, value) key points over
one loop of length DUR. Values hold before the first key point and after the last one, so the
loop is seamless as long as the first and last values agree.
"""

from __future__ import annotations

import html

FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"

C = {
    "ink": "#1f2937",
    "muted": "#6b7280",
    "faint": "#9ca3af",
    "line": "#e5e7eb",
    "card": "#f8fafc",
    "blue": "#2563eb",
    "blue_l": "#dbeafe",
    "green": "#16a34a",
    "green_l": "#dcfce7",
    "red": "#dc2626",
    "red_l": "#fee2e2",
    "orange": "#ea580c",
    "orange_l": "#ffedd5",
    "purple": "#7c3aed",
    "purple_l": "#ede9fe",
    "teal": "#0d9488",
    "teal_l": "#ccfbf1",
    "amber": "#d97706",
    "amber_l": "#fef3c7",
    "gray_l": "#f3f4f6",
}

EASE = "0.42 0 0.58 1"  # ease-in-out cubic bezier


def _fmt(v):
    if isinstance(v, float):
        s = f"{v:.3f}".rstrip("0").rstrip(".")
        return s if s not in ("-0", "") else "0"
    if isinstance(v, (tuple, list)):
        return " ".join(_fmt(x) for x in v)
    return str(v)


def _keys(points, dur):
    pts = sorted(points, key=lambda p: p[0])
    # clamp and make strictly increasing
    out = []
    for t, v in pts:
        t = min(max(t, 0.0), dur)
        if out and t <= out[-1][0]:
            t = out[-1][0] + 1e-3
        out.append((t, v))
    if out[0][0] > 0:
        out.insert(0, (0.0, out[0][1]))
    if out[-1][0] < dur:
        out.append((dur, out[-1][1]))
    if out[-1][0] > dur:  # epsilon spill-over
        t, v = out[-1]
        out[-1] = (dur, v)
    key_times = ";".join(_fmt(t / dur) for t, _ in out)
    values = ";".join(_fmt(v) for _, v in out)
    return key_times, values, len(out)


def anim(attr, points, dur, ease=True, discrete=False):
    kt, vals, n = _keys(points, dur)
    if discrete:
        mode = 'calcMode="discrete"'
    elif ease:
        mode = 'calcMode="spline" keySplines="' + ";".join([EASE] * (n - 1)) + '"'
    else:
        mode = 'calcMode="linear"'
    return (
        f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" '
        f'keyTimes="{kt}" values="{vals}" {mode}/>'
    )


def anim_tf(kind, points, dur, ease=True, additive=False):
    kt, vals, n = _keys(points, dur)
    mode = (
        'calcMode="spline" keySplines="' + ";".join([EASE] * (n - 1)) + '"' if ease else 'calcMode="linear"'
    )
    add = ' additive="sum"' if additive else ""
    return (
        f'<animateTransform attributeName="transform" type="{kind}" dur="{dur}s" '
        f'repeatCount="indefinite" keyTimes="{kt}" values="{vals}" {mode}{add}/>'
    )


def fade(t_in, t_out, dur, f=0.35, lo=0.0, hi=1.0):
    """Opacity animation: hidden, fade in at t_in, visible, fade out at t_out."""
    pts = [(0, lo), (t_in, lo), (t_in + f, hi), (t_out, hi), (t_out + f, lo)]
    return anim("opacity", pts, dur)


def esc(s):
    return html.escape(s, quote=False)


def text(x, y, s, size=13, fill=None, weight=400, anchor="start", extra="", children="", italic=False, family=None):
    fill = fill or C["ink"]
    style = ' font-style="italic"' if italic else ""
    fam = family or FONT
    return (
        f'<text x="{_fmt(x)}" y="{_fmt(y)}" font-family="{fam}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{style} {extra}>{s}{children}</text>'
    )


def group(content, extra="", anims=""):
    return f"<g {extra}>{anims}{content}</g>"


def svg_doc(w, h, body, title="", desc="", defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
        f"<title>{esc(title)}</title><desc>{esc(desc)}</desc>"
        f"<defs>{defs}</defs>"
        f'<rect x="0" y="0" width="{w}" height="{h}" rx="14" fill="#ffffff"/>'
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="none" stroke="{C["line"]}"/>'
        f"{body}</svg>"
    )


def caption_track(captions, dur, x=18, y=30, size=15, f=0.35):
    """captions: list of (t_in, t_out, step_label, text). Renders a numbered pill + text that cross-fade."""
    out = []
    for t_in, t_out, step, s in captions:
        pill = ""
        tx = x
        if step:
            pill = (
                f'<circle cx="{x+10}" cy="{y-5}" r="10" fill="{C["ink"]}"/>'
                + text(x + 10, y - 0.5, step, size=12, fill="#fff", weight=700, anchor="middle")
            )
            tx = x + 27
        out.append(group(pill + text(tx, y, s, size=size, weight=600), anims=fade(t_in, t_out, dur, f=f)))
    return "".join(out)


def arrow_marker(mid, color):
    return (
        f'<marker id="{mid}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>'
    )
