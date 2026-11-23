## What is where

| Path                                                  | Purpose                                                                                                        |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `index.html`, `assets/resume.*`                       | The web resume (Jekyll/Liquid). Themes auto, dark, light, e-ink; entries fold; prints black on white.          |
| `_data/*.json`                                        | The content: `personal`, `edu`, `exp`, `proj`, `pubs`. One source for the web page, the PDF and the Word file. |
| `dev/tex/main.tex`, `dev/lua/`                        | The PDF resume (LuaLaTeX); `dev/lua/parser.lua` prints the JSON as LaTeX.                                      |
| `dev/tex/publications.tex`                            | The list of publications as PDF.                                                                               |
| `dev/scripts/make_docx.py`                            | The Word versions (resume with a 35 x 45 mm photo box, publications).                                          |
| `dev/scripts/preview.py`, `dev/scripts/print_html.py` | Local render of the Liquid page, and HTML to PDF (A5, zoom 30 %) for review.                                   |
| `files/intro.html`, `assets/deck.*`                   | The intro presentation: keys `←` `→`, `f` fullscreen, `n` notes, `t` theme, `p` print.                         |
| `linkedin/`                                           | LinkedIn banner (1584 x 396) in dark, light and e-ink: SVG, PDF, PNG.                                          |
| `files/STYLESHEET.html`                               | The design rules and kits behind all of it.                                                                    |
| `files/`                                              | The published documents (resume PDF and Word). Tracked in git, linked from this README and the site.           |
| `info/`                                               | Personal documents (redacted CV, publications PDF, `contact.json`). Git-ignored.                               |

## Build

```sh
make doctor     # check the toolchain
make            # resume PDF, publications PDF, both Word files
make preview    # render the web page into _site/ (index.html is Liquid: do not open it from disk)
make static     # files/resume.html: one self-contained page (CSS/JS inlined); opens from disk, works without JavaScript
make serve      # preview + http://localhost:8000
make htmlpdf    # the page as PDF on A5 at 30 % zoom (PAPER=A4 ZOOM=100 to change)
make banner     # LinkedIn banners into linkedin/out/
```

`index.html` is a Jekyll/Liquid template: opened straight from disk (for example in the VS Code browser) it shows raw `{{ }}` placeholders. Open `files/resume.html` or `dev/_site/index.html` instead. Without JavaScript the pages still show all content; only the theme, fold-all and print controls need it (they are hidden then), and the intro deck shows every slide one under the other.

Options live in `_data/personal.json` under `options` and can be overridden per run:

| Option                       | Override                                      | Effect                                                                                                                                                       |
| ---------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `show_languages`             | `RESUME_LANGS=0\|1`                           | show or hide the language/technology tags                                                                                                                    |
| `languages_as_list`          | `RESUME_LANGS_LIST=0\|1`                      | tags as a `Tech: a · b` line under the text instead of in the heading                                                                                        |
| `max_line_chars`             | `RESUME_MAX_CHARS=80`                         | strict characters per line for skills, Tech lines and languages                                                                                              |
| `show_abstract`              | `RESUME_ABSTRACT=0\|1`                        | show abstracts in the publications                                                                                                                           |
| `photo_placeholder`, `photo` | `RESUME_PHOTO=0\|1`, `RESUME_PHOTO_FILE=path` | the photo box in the Word resume                                                                                                                             |
| `contact_placeholders`       | `RESUME_CONTACT=0\|1`                         | `Phone:` / `Address:` placeholder lines in the Word resume; real values come from the git-ignored `info/contact.json` (`{"phone": "...", "address": "..."}`) |

Example: `make resume RESUME_LANGS_LIST=0 RESUME_MAX_CHARS=80`.

`make` writes the resume PDF and Word file to `files/`, which is the one folder where `*.pdf` and `*.docx` are not git-ignored (`.gitignore` has `!files/*.pdf` and `!files/*.docx`), so `git add files/` publishes them and the links above work. Everything else generated (`build/`, `_site/`, `linkedin/out/`, `info/`) stays out of git. `PUBS_DIR=files make pubs` publishes the publications PDF the same way.
