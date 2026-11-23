# LinkedIn banner: banner.json -> SVG (build.py) -> PDF (Inkscape) -> PNG (pdftoppm), per theme.
#
#   make -C linkedin                 all three themes: out/banner-{dark,light,eink}.{svg,pdf,png}
#   make -C linkedin out/banner-dark_3168x792_192dpi.png
#   make -C linkedin SET='--set title.text="Jane Doe"'     override a value without editing banner.json
#   make -C linkedin publish         PNGs -> files/linkedin-banner-<theme>_<W>x<H>_<DPI>dpi.png (tracked, served by GitHub Pages)
#   make -C linkedin clean
#
# PNGs are high resolution and named after it:  banner-<theme>_<W>x<H>_<DPI>dpi.png
#   SCALE=2 (default)  3168 x 792 px at 192 dpi     SCALE=1  1584 x 396 at 96 dpi (the LinkedIn size)     SCALE=3  4752 x 1188 at 288 dpi
#   make -C linkedin SCALE=3
# The banner is drawn as vector (SVG -> PDF), so every scale is sharp. LinkedIn accepts the large file and scales it down.
#
# Needs: python3, inkscape, pdftoppm (poppler-utils).

THEMES  := dark light eink
OUT     := out
SET     ?=
CONFIG  := banner.json
SCALE   ?= 2
BASE_W  := 1584
BASE_H  := 396
W       := $(shell echo $$(( $(BASE_W) * $(SCALE) )))
H       := $(shell echo $$(( $(BASE_H) * $(SCALE) )))
DPI     := $(shell echo $$(( 96 * $(SCALE) )))
SIZE    := $(W)x$(H)_$(DPI)dpi

.PHONY: all svg pdf png publish clean
all: png
svg: $(THEMES:%=$(OUT)/banner-%.svg)
pdf: $(THEMES:%=$(OUT)/banner-%.pdf)
png: $(THEMES:%=$(OUT)/banner-%_$(SIZE).png)

$(OUT)/banner-%.svg: build.py $(CONFIG)
	python3 build.py --theme $* --out $(OUT) $(SET)

# text is converted to outlines so the PDF/PNG do not depend on the fonts of the machine
$(OUT)/banner-%.pdf: $(OUT)/banner-%.svg
	inkscape $< --export-type=pdf --export-filename=$@ --export-text-to-path

$(OUT)/banner-%_$(SIZE).png: $(OUT)/banner-%.pdf
	pdftoppm -png -singlefile -r $(DPI) $< $(OUT)/banner-$*_$(SIZE)

# copy the PNGs next to the other published documents (the profile README links to them)
publish: png
	mkdir -p ../files
	rm -f ../files/linkedin-banner-*.png
	for t in $(THEMES); do cp $(OUT)/banner-$${t}_$(SIZE).png ../files/linkedin-banner-$${t}_$(SIZE).png; done

clean:
	rm -rf $(OUT)
