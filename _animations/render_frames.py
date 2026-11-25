"""Render frames of SMIL-animated SVGs at given times and assemble a contact sheet.

usage: python3 render_frames.py out.png file.svg t1 t2 t3 ...
"""

import sys
import pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw


def main():
    out = sys.argv[1]
    svg = pathlib.Path(sys.argv[2]).resolve()
    times = [float(t) for t in sys.argv[3:]]
    frames = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 480, "height": 300}, device_scale_factor=1.5)
        page.goto(svg.as_uri())
        page.wait_for_timeout(200)
        for t in times:
            page.evaluate("t => { const s = document.documentElement; s.pauseAnimations(); s.setCurrentTime(t); }", t)
            page.wait_for_timeout(60)
            tmp = f"/tmp/frame_{t:.2f}.png"
            page.screenshot(path=tmp)
            frames.append((t, Image.open(tmp).convert("RGB")))
        browser.close()
    w, h = frames[0][1].size
    cols = 3 if len(frames) > 4 else 2
    rows = (len(frames) + cols - 1) // cols
    pad = 10
    sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + 30) + pad), "#d0d4da")
    d = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(frames):
        r, c = divmod(i, cols)
        x = pad + c * (w + pad)
        y = pad + r * (h + pad + 30)
        d.text((x + 4, y + 4), f"t = {t:.1f}s", fill="#000")
        sheet.paste(im, (x, y + 26))
    sheet.save(out)
    print("saved", out, sheet.size)


if __name__ == "__main__":
    main()
