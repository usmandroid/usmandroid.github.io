"""Render index.html (Jekyll/Liquid) into dev/_site/ without Jekyll: `make preview`."""

import argparse
import glob
import json
import os
import re
import shutil
import sys

from liquid import parse

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
site = os.path.join(root, "dev", "_site")

data = {}
for f in glob.glob(os.path.join(root, "_data", "*.json")):
    text = open(f, encoding="utf-8").read().strip()
    if text:  # work.json is empty
        data[os.path.basename(f)[:-5]] = json.loads(text)

# RESUME_LANGS=0|1 and RESUME_LANGS_LIST=0|1 override personal.json "options" (same as the PDF and DOCX builds)
opts = data["personal"][0].setdefault("options", {})
for var, key in (
    ("RESUME_LANGS", "show_languages"),
    ("RESUME_LANGS_LIST", "languages_as_list"),
    ("RESUME_ABSTRACT", "show_abstract"),
):
    if os.environ.get(var, "") != "":
        opts[key] = os.environ[var].lower() in ("1", "true", "yes")

if os.environ.get("RESUME_MAX_CHARS"):
    opts["max_line_chars"] = int(os.environ["RESUME_MAX_CHARS"])

src = open(os.path.join(root, "index.html"), encoding="utf-8").read()
src = re.sub(r"\A---\n.*?\n---\n", "", src, flags=re.S)  # drop the front matter

os.makedirs(site, exist_ok=True)
with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(parse(src).render({"site": {"data": data}}))

for folder in ("files", "assets"):  # published documents (pdf, docx, intro, style sheet) and css/js
    if os.path.isdir(os.path.join(root, folder)):
        shutil.copytree(os.path.join(root, folder), os.path.join(site, folder), dirs_exist_ok=True)

print("rendered", os.path.join(site, "index.html"))

# One self-contained file (CSS and JS inlined, links relative to files/) that opens from disk, e.g. in
# the VS Code browser, and shows everything without JavaScript: files/resume.html (`make static`).
if "--standalone" in sys.argv:
    page = open(os.path.join(site, "index.html"), encoding="utf-8").read()
    css = open(os.path.join(root, "assets", "resume.css"), encoding="utf-8").read()
    js = open(os.path.join(root, "assets", "resume.js"), encoding="utf-8").read()
    page = page.replace(
        '<link rel="stylesheet" href="assets/resume.css">', "<style>\n" + css + "</style>"
    )
    page = page.replace('<script src="assets/resume.js"></script>', "<script>\n" + js + "</script>")
    page = page.replace('href="files/', 'href="')
    os.makedirs(os.path.join(root, "files"), exist_ok=True)
    out = os.path.join(root, "files", "resume.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote", out)
