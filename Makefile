# Build the resume and the publications list (LuaLaTeX + Lua), Word versions, and a local
# preview of the Jekyll page. Run from the repository root.
#
#   make              resume + pubs PDFs and both .docx files
#   make resume       dev/tex/main.tex -> files/sheikhUsmanAli_resume.pdf   (files/ is tracked; the site links to it)
#   make pubs         dev/tex/publications.tex -> "info/Publications -- Ali.pdf" (the previous file is kept once as "... (original).pdf");
#                     PUBS_DIR=files make pubs publishes it next to the resume
#   make docx         Word versions -> files/sheikhUsmanAli_resume.docx, "info/Publications -- Ali.docx"
#   make preview      render index.html (Liquid) into _site/ so it can be opened locally (dev/_site/)
#   make static       files/resume.html: one self-contained page (CSS/JS inlined) that opens from disk and shows without JavaScript
#   make serve        preview + http://localhost:8000
#   make htmlpdf      print the rendered page to PDF with Chrome: A5, zoom 30% (PAPER=A4 ZOOM=100 to change)
#   make banner       LinkedIn banners (dark/light/e-ink) -> linkedin/out/*.{svg,pdf,png}, see linkedin/Makefile
#   make fmt          format everything: black (python), prettier (json css js md yml), stylua (lua)
#   make lint         the same checks without changing files (non-zero exit when something is off)
#   make profile      banner.md (GitHub profile README, monospace panel) from dev/config/profile.json
#   make doctor       check that the toolchain is complete
#   make clean        remove build/ (generated PDFs/DOCX in the root are kept); make distclean also _site/ and .venv/
#
# Language/technology tags in the resume (web, PDF, DOCX): defaults live in _data/personal.json
# "options"; override per run with
#   make resume RESUME_LANGS=0            hide the tags
#   make resume RESUME_LANGS_LIST=1       show them as a "Tech: ..." line under the text instead of in the heading
#   make resume RESUME_MAX_CHARS=80      strict limit of characters per line for lists (skills, Tech lines,
#                                        languages): they wrap to a new line between items; default 90
#   make docx RESUME_CONTACT=0          drop the Phone / Address placeholder lines (options.contact_placeholders); real values go
#                                        into the git-ignored info/contact.json {"phone": "...", "address": "..."}
#   make docx RESUME_PHOTO=0            drop the bordered 35 x 45 mm photo box in the Word resume (options.photo_placeholder);
#   make docx RESUME_PHOTO_FILE=info/me.jpg   put a real photo in it (or set options.photo)
#   make pubs RESUME_ABSTRACT=1          show abstracts (they are placeholders now: fill "abstract" in _data/pubs.json)
# Publications: _data/pubs.json has placeholders for abstract, doi and links (Paper, PDF, Code, Slides);
# empty values are not shown. options.show_abstract (default false) switches abstracts on or off.
# (RESUME_LANGS, RESUME_LANGS_LIST, RESUME_MAX_CHARS, RESUME_ABSTRACT work for resume, docx and preview alike;
#  defaults live in _data/personal.json "options": show_languages, languages_as_list, max_line_chars)
#
# index.html contains Liquid ({{ }}, {% %}): opening it straight from disk shows the raw
# placeholders. Use `make preview` (or GitHub Pages) to see the rendered page.

SHELL    := /bin/bash
BUILD    := dev/build
VENV     := dev/.venv
PY       := $(VENV)/bin/python
LATEXMK  := latexmk -lualatex -interaction=nonstopmode -halt-on-error -outdir=$(BUILD) -g
DATA     := $(wildcard _data/*.json)
LUA      := $(wildcard dev/lua/*.lua)
# published documents go to files/ (tracked in git); personal ones to info/ (git-ignored)
FILES    := files
RESUME   := $(FILES)/sheikhUsmanAli_resume
PAPER    ?= A5
ZOOM     ?= 30
# info/ is git-ignored (personal documents)
PUBS_DIR ?= info
PUBS     := $(PUBS_DIR)/Publications -- Ali

.PHONY: all resume pubs docx static htmlpdf banner profile preview serve doctor clean distclean venv devtools fmt lint

all: resume pubs docx static

# ---- PDFs (latexmk -g forces a run: the Lua data reads are not tracked by latexmk) -------------
resume:
	@mkdir -p $(BUILD) $(FILES)
	$(LATEXMK) dev/tex/main.tex
	cp $(BUILD)/main.pdf "$(RESUME).pdf"

pubs:
	@mkdir -p $(BUILD) $(PUBS_DIR)
	$(LATEXMK) dev/tex/publications.tex
	@[ ! -f "$(PUBS).pdf" ] || [ -f "$(PUBS) (original).pdf" ] || cp "$(PUBS).pdf" "$(PUBS) (original).pdf"
	cp $(BUILD)/publications.pdf "$(PUBS).pdf"

# ---- Word -------------------------------------------------------------------------------------
docx: venv
	@mkdir -p $(FILES)
	$(PY) dev/scripts/make_docx.py resume "$(RESUME).docx"
	@mkdir -p $(PUBS_DIR)
	$(PY) dev/scripts/make_docx.py pubs "$(PUBS).docx"

htmlpdf: preview
	$(PY) dev/scripts/print_html.py --paper $(PAPER) --zoom $(ZOOM) -o "$(BUILD)/resume-html-$(PAPER)-$(ZOOM)pct.pdf"

# ---- LinkedIn banner ---------------------------------------------------------------------------
banner:
	$(MAKE) -C linkedin publish

profile: venv
	$(PY) dev/scripts/make_profile.py

# ---- local preview of the Jekyll page ---------------------------------------------------------
preview: venv
	@if command -v jekyll >/dev/null; then jekyll build -d dev/_site; else $(PY) dev/scripts/preview.py; fi
	@echo "open dev/_site/index.html"

static: venv
	$(PY) dev/scripts/preview.py --standalone

serve: preview
	cd dev/_site && python3 -m http.server 8000

# ---- tooling ----------------------------------------------------------------------------------
venv: $(VENV)/.ok

$(VENV)/.ok: dev/scripts/requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet -r dev/scripts/requirements.txt
	@touch $@

# ---- formatting and linting (same commands as the VS Code tasks in .vscode/tasks.json) --------
PRETTIER := npx --yes prettier@3 --config dev/config/prettierrc.json --ignore-path dev/config/prettierignore
STYLUA   := npx --yes @johnnymorganz/stylua-bin
PRETTIER_GLOB := '**/*.{json,css,js,md,yml,yaml}'

devtools: venv $(VENV)/.dev

$(VENV)/.dev: dev/scripts/requirements-dev.txt
	$(VENV)/bin/pip install --quiet -r dev/scripts/requirements-dev.txt
	@touch $@

fmt: devtools
	$(PY) -m black --config dev/config/pyproject.toml .
	$(PRETTIER) --write $(PRETTIER_GLOB)
	$(STYLUA) --config-path dev/config/stylua.toml dev/lua

lint: devtools
	$(PY) -m black --config dev/config/pyproject.toml --check --diff .
	$(PRETTIER) --check $(PRETTIER_GLOB)
	$(STYLUA) --config-path dev/config/stylua.toml --check dev/lua
	texlua dev/lua/selftest.lua

doctor:
	@ok=1; for t in lualatex latexmk texlua python3; do \
	  if command -v $$t >/dev/null; then echo "ok       $$t"; else echo "MISSING  $$t"; ok=0; fi; done; \
	for f in hyperref.sty titlesec.sty enumitem.sty marvosym.sty tgpagella.sty tgtermes.sty; do \
	  if kpsewhich $$f >/dev/null; then echo "ok       $$f"; else echo "MISSING  $$f (sudo apt install texlive-latex-extra texlive-fonts-recommended)"; ok=0; fi; done; \
	if kpsewhich Alegreya.sty >/dev/null; then echo "ok       Alegreya"; \
	else echo "note     Alegreya not installed: using TeX Gyre Pagella (sudo apt install texlive-fonts-extra for the original look)"; fi; \
	if kpsewhich luaotfload-main.lua >/dev/null; then echo "ok       luaotfload"; \
	else echo "note     texlive-luatex not installed: fine, the sources use Type1 fonts and pure-Lua JSON (no fontspec/luacode)"; fi; \
	texlua dev/lua/selftest.lua; \
	[ $$ok = 1 ] && echo "ready: make" || { echo "fix the MISSING items above"; exit 1; }

clean:
	rm -rf $(BUILD)

distclean: clean
	rm -rf dev/_site $(VENV)
