# Publication animations

Each `*.py` script writes one looping, SMIL-animated SVG used as a publication preview
(`preview = {name.svg}` in `_bibliography/papers.bib`). The SVGs need no JavaScript and play inside
a plain `<img>` tag.

```bash
cd _animations
python3 dap.py ../assets/img/publication_preview/dap.svg        # needs numpy for some scripts
python3 render_frames.py /tmp/sheet.png ../assets/img/publication_preview/dap.svg 2 5 8 11   # contact sheet (playwright + Chrome)
```

`svganim.py` holds the shared helpers: `anim()` turns a list of `(time, value)` key points into a
SMIL `<animate>`, `fade()` builds fade-in/fade-out opacity tracks, and `caption_track()` draws the
numbered step captions. Underscore folders are not published by Jekyll.
