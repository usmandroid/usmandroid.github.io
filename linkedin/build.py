#!/usr/bin/env python3
"""LinkedIn banner (1584 x 396) in the three themes of the style sheet: dark, light, e-ink.

    python3 linkedin/build.py                          # all themes -> linkedin/out/banner-<theme>.svg
    python3 linkedin/build.py --theme light
    python3 linkedin/build.py --set title.text="Jane Doe" --set rows.0.1="what I do"
    python3 linkedin/build.py --config my.json --out /tmp/banners

Everything lives in banner.json (texts, sizes, colours, photo area); --set overrides one key
(dotted path, list index allowed) without editing the file. `make -C linkedin` then turns every
SVG into a PDF (Inkscape, text converted to outlines) and a PNG (pdftoppm).

Style: one monospace grid, only text / bold / dim, the rounded dim frame drawn with box characters.
The left part (photo_safe_px) is kept empty: LinkedIn puts the profile photo there.
"""

import argparse
import json
import math
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))


def set_path(cfg, path, raw):
    keys = path.split(".")
    node = cfg
    for k in keys[:-1]:
        node = node[int(k)] if isinstance(node, list) else node[k]
    last = keys[-1]
    try:
        value = json.loads(raw)
    except ValueError:
        value = raw
    if isinstance(node, list):
        node[int(last)] = value
    else:
        node[last] = value


def build(cfg, theme_name):
    th = cfg["themes"][theme_name]
    W, H = cfg["size"]
    f = cfg["font"]
    size, cell, line = f["size"], f["cell"] * f["size"], f["size"] * f["line"]
    m = cfg["margin"]
    cols = int((W - 2 * m) // cell)
    rows = int((H - 2 * m) // line)
    x0 = m + ((W - 2 * m) - cols * cell) / 2  # centre the grid
    y0 = m + ((H - 2 * m) - rows * line) / 2

    def X(col):
        return x0 + col * cell

    def Y(row, s=size):
        return y0 + row * line + (line + s * 0.72) / 2  # baseline inside the row

    out = []

    def text(col, row, s, bold=False, dim=False, anchor="start", s_size=None):
        s_size = s_size or size
        attrs = f'x="{X(col):.2f}" y="{Y(row, s_size):.2f}" font-size="{s_size}"'
        if anchor != "start":
            attrs += f' text-anchor="{anchor}"'
        if bold:
            attrs += f' font-weight="{th["bold"]}"'
        if dim:
            attrs += f' fill-opacity="{th["dim"]}"'
        out.append(f'<text {attrs} xml:space="preserve">{escape(s)}</text>')

    # frame: the rounded dim panel of the style sheet. Box characters do not join across the
    # line gaps of a banner, so it is one rounded rectangle on the character grid.
    if cfg.get("frame", True):
        fx, fy = X(0) + cell / 2, y0 + line / 2
        fw, fh = (cols - 1) * cell, (rows - 1) * line
        out.append(
            f'<rect x="{fx:.2f}" y="{fy:.2f}" width="{fw:.2f}" height="{fh:.2f}" rx="{cell * 1.2:.1f}" '
            f'fill="none" stroke="{th["fg"]}" stroke-opacity="{th["dim"]}" stroke-width="1.5"/>'
        )

    c0 = max(3, math.ceil((cfg["photo_safe_px"] - x0) / cell))  # first content column

    t = cfg["title"]
    title_rows = max(1, math.ceil(t["size"] * 1.2 / line))
    r = 2
    tx = f'x="{X(c0):.2f}" y="{y0 + r * line + t["size"] * 0.82:.2f}" font-size="{t["size"]}" font-weight="{th["bold"]}"'
    out.append(f'<text {tx} xml:space="preserve">{escape(t["text"])}</text>')
    r += title_rows
    text(c0, r, cfg["subtitle"], dim=True)
    r += 2

    kv = cfg["rows"]
    keyw = max(len(k) for k, _ in kv)
    for k, v in kv:  # the About pattern: dim right-aligned key, plain value
        text(c0 + keyw, r, k, dim=True, anchor="end")
        text(c0 + keyw + 2, r, v)
        r += 1

    foot_row = rows - 2
    text(c0, foot_row, cfg["footer"], dim=True)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
        f'<title>{escape(t["text"])} - LinkedIn banner ({theme_name})</title>\n'
        f'<rect width="{W}" height="{H}" fill="{th["bg"]}"/>\n'
        f'<g font-family="{escape(f["family"])}" fill="{th["fg"]}">\n'
        + "\n".join(out)
        + "\n</g>\n</svg>\n"
    )
    return svg


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--config", default=os.path.join(HERE, "banner.json"))
    ap.add_argument("--theme", default="all", help="dark | light | eink | all")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--set", action="append", default=[], metavar="PATH=VALUE")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as fh:
        cfg = json.load(fh)
    for item in args.set:
        path, _, raw = item.partition("=")
        set_path(cfg, path, raw)

    names = list(cfg["themes"]) if args.theme == "all" else [args.theme]
    os.makedirs(args.out, exist_ok=True)
    for name in names:
        path = os.path.join(args.out, f"banner-{name}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(build(cfg, name))
        print("wrote", path)


if __name__ == "__main__":
    main()
