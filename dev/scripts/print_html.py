#!/usr/bin/env python3
"""Print the rendered resume page (dev/_site/index.html) to PDF with headless Chrome/Chromium.

    python dev/scripts/print_html.py                       # A5, zoom 30 %  -> dev/build/resume-html-A5-30pct.pdf
    python dev/scripts/print_html.py --paper A4 --zoom 100 -o out.pdf

Chrome has no command line switch for paper size or scale, so both are injected as CSS into a
copy of the page (dev/_site/_print.html): `@page { size: <paper> }` and `html { zoom: <zoom>% }`.
At 30 % the layout width is the paper width / 0.3, so one A5 page holds what a few A4 pages hold:
useful to judge the overall layout, page breaks and alignment (the PDF stays vector: zoom in).
Run `make preview` first (the Makefile target `htmlpdf` does).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
site = os.path.join(root, "dev", "_site")

ap = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)
ap.add_argument("--paper", default="A5", help="A3, A4, A5, letter, ... (CSS @page size)")
ap.add_argument("--zoom", type=float, default=30, help="percent, 30 = 0.3")
ap.add_argument("--margin", default="6mm")
ap.add_argument(
    "-o", "--out", default=os.path.join(root, "dev", "build", "resume-html-A5-30pct.pdf")
)
args = ap.parse_args()

chrome = next(
    (
        c
        for c in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
        if shutil.which(c)
    ),
    None,
)
if not chrome:
    sys.exit("print_html.py: no Chrome/Chromium found")
src = os.path.join(site, "index.html")
if not os.path.exists(src):
    sys.exit("print_html.py: dev/_site/index.html missing, run `make preview` first")

page = open(src, encoding="utf-8").read()
style = (
    f'<style id="print-override">@page{{size:{args.paper};margin:{args.margin}}}'
    f"html{{zoom:{args.zoom / 100:g}}}</style>"
)
page = re.sub(
    r"</head>", style + "</head>", page, count=1
)  # after resume.css: wins over its A4 @page
tmp = os.path.join(site, "_print.html")
open(tmp, "w", encoding="utf-8").write(page)

os.makedirs(os.path.dirname(args.out), exist_ok=True)
subprocess.run(
    [
        chrome,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={args.out}",
        "file://" + tmp,
    ],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
os.remove(tmp)
print("wrote", args.out, f"({args.paper}, zoom {args.zoom:g}%)")
