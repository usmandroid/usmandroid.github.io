"""Word versions of the resume and the publications list, from _data/*.json.

    python dev/scripts/make_docx.py resume "sheikhUsmanAli_resume.docx"
    python dev/scripts/make_docx.py pubs   "Publications -- Ali.docx"

Style guide: only text, bold and dim (grey), one monospace face, no colour. The owner's
phone and address are never written (the public site keeps them out as well).
"""

import json
import os
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = "Consolas"
DIM = RGBColor(0x59, 0x59, 0x59)
TEXT_WIDTH = Cm(17.6)  # A4 21 cm minus 2 x 1.7 cm


def load(name):
    with open(os.path.join(ROOT, "_data", name + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


def new_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.7)
    sec.top_margin = sec.bottom_margin = Cm(1.6)
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    style.font.size = Pt(9.5)
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.line_spacing = 1.15
    return doc


def run(par, text, bold=False, dim=False, size=None):
    r = par.add_run(text)
    r.bold = bold
    r.font.name = FONT
    if dim:
        r.font.color.rgb = DIM
    if size:
        r.font.size = Pt(size)
    return r


def para(doc, before=0, after=0, left=0.0, hang=0.0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.left_indent = Cm(left + hang)
    if hang:
        pf.first_line_indent = Cm(-hang)
    return p


def heading(doc, text):
    p = para(doc, before=12, after=4)
    run(p, text, bold=True, size=12)
    border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "4"), ("w:space", "1"), ("w:color", "808080")):
        bottom.set(qn(k), v)
    border.append(bottom)
    p._p.get_or_add_pPr().append(border)
    p.paragraph_format.keep_with_next = True


def entry_header(doc, left1, right1, left2, right2, before=4):
    """Two lines in a borderless 2-column table: name | place, role | dates. Long text wraps in its cell."""
    gap = para(doc, before=before)
    gap.paragraph_format.keep_with_next = True
    table = doc.add_table(rows=2, cols=2)
    table.autofit = False
    widths = (Cm(12.6), Cm(5.0))
    for col, w in zip(table.columns, widths):  # grid columns too: Word and LibreOffice use these
        col.width = w
    for row, (l, r, bold) in zip(table.rows, ((left1, right1, True), (left2, right2, False))):
        for cell, w, text, is_left in zip(row.cells, widths, (l, r), (True, False)):
            cell.width = w
            p = cell.paragraphs[0]
            p.paragraph_format.keep_with_next = True
            if not is_left:
                p.alignment = 2  # right
            run(p, text, bold=(bold and is_left), dim=(not (bold and is_left)))
    return table


FLAGS = {
    "show": True,
    "list": False,
    "limit": 90,
    "abstract": False,
    "photo_box": True,
    "photo": "",
    "contact": True,
}


def wrap_items(prefix_len, items, sep_len, limit, indent=2):
    trail = (
        sep_len - 1 if sep_len > 2 else 1
    )  # the separator kept at the end of a wrapped line ("," or " ·")
    """Greedy wrap into lines of at most `limit` characters (prefix on the first line, indent on the
    others). An item longer than the limit stays alone on its line."""
    lines, cur, length = [], [], prefix_len
    for it in items:
        add = len(it) if not cur else sep_len + len(it)
        if cur and length + add + trail > limit:
            lines.append(cur)
            cur, length = [it], indent + len(it)
        else:
            cur.append(it)
            length += add
    lines.append(cur)
    return lines


def wrapped_runs(p, lines, sep, dim=False):
    for i, line in enumerate(lines):
        if i:
            p.add_run().add_break()
        run(p, sep.join(line) + (sep.rstrip() if i < len(lines) - 1 else ""), dim=dim)


def env_flag(name, default):
    v = os.environ.get(name, "")
    return default if v == "" else v.lower() in ("1", "true", "yes")


def set_flags(personal):
    """Language/technology tags: _data/personal.json options, or RESUME_LANGS / RESUME_LANGS_LIST = 0|1."""
    o = personal.get("options", {})
    FLAGS["show"] = env_flag("RESUME_LANGS", o.get("show_languages", True))
    FLAGS["list"] = env_flag("RESUME_LANGS_LIST", o.get("languages_as_list", False))
    FLAGS["contact"] = env_flag("RESUME_CONTACT", o.get("contact_placeholders", True))
    FLAGS["photo_box"] = env_flag("RESUME_PHOTO", o.get("photo_placeholder", True))
    FLAGS["photo"] = os.environ.get("RESUME_PHOTO_FILE") or o.get("photo", "")
    FLAGS["abstract"] = env_flag("RESUME_ABSTRACT", o.get("show_abstract", False))
    FLAGS["limit"] = int(os.environ.get("RESUME_MAX_CHARS") or o.get("max_line_chars", 90))


def detail_line(doc, title, tags, text):
    p = para(doc, before=3, left=0.0, hang=0.6)
    run(p, "↳ ", dim=True)
    run(p, title, bold=True)
    items = tags.split() if (tags and FLAGS["show"]) else []
    if items and not FLAGS["list"]:
        run(p, "  ·  " + " ".join(items), dim=True)
    p.paragraph_format.keep_with_next = True
    t = para(doc, left=0.6)
    run(t, text)
    if items and FLAGS["list"]:
        tp = para(doc, left=0.6, hang=0.6)
        run(tp, "Tech: ", dim=True)
        wrapped_runs(tp, wrap_items(6, items, 3, FLAGS["limit"]), " · ", dim=True)


def plain_line(doc, text, before=2):
    p = para(doc, before=before, left=0.0, hang=0.6)
    run(p, "↳ ", dim=True)
    run(p, text)


def authors_runs(par, authors, me):
    for i, a in enumerate(authors):
        run(par, a, bold=(a == me))
        if i < len(authors) - 1:
            run(par, ", ")


def venue_text(p, links=False):
    """Venue line. An empty doi / link url is a placeholder and is skipped."""
    s = p["venue"]
    if p.get("place"):
        s += ", " + p["place"]
    if p.get("pages"):
        s += ", " + p["pages"]
    s += "."
    if p.get("doi"):
        s += " DOI: " + p["doi"] + "."
    if links:
        ls = ["%s: %s" % (l["label"], l["url"]) for l in p.get("links", []) if l.get("url")]
        if ls:
            s += " Links: " + ", ".join(ls) + "."
    if p.get("note"):
        s += " " + p["note"] + "."
    return s


PHOTO_W, PHOTO_H = Cm(3.5), Cm(4.5)  # passport size used by the EU CV (Europass) layout


def set_cell_border(cell, color="808080", size=8):
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement("w:" + edge)
        for k, v in (
            ("w:val", "single"),
            ("w:sz", str(size)),
            ("w:space", "0"),
            ("w:color", color),
        ):
            el.set(qn(k), v)
        borders.append(el)
    cell._tc.get_or_add_tcPr().append(borders)


def add_private_contact(add_par):
    """Phone and address lines (EU CV layout). The public data has neither: they are placeholders
    in brackets, or the values of the git-ignored file info/contact.json {"phone": "...", "address": "..."}.
    """
    if not FLAGS["contact"]:
        return
    values = {}
    path = os.path.join(ROOT, "info", "contact.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            values = json.load(fh)
    for label, key, placeholder in (
        ("Phone", "phone", "[+49 000 0000000]"),
        ("Address", "address", "[Street 0, 00000 City, Country]"),
    ):
        p = add_par()
        run(p, label + ": ", dim=True)
        if values.get(key):
            run(p, values[key])
        else:
            run(p, placeholder, dim=True)


def photo_header(doc, me):
    """Name + contacts on the left, a bordered 35 x 45 mm photo box on the right (EU CV layout).
    A real photo (options.photo / RESUME_PHOTO_FILE) replaces the placeholder text."""
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    left, right = table.rows[0].cells
    widths = (TEXT_WIDTH - PHOTO_W - Cm(0.4), PHOTO_W + Cm(0.4))
    for col, w in zip(table.columns, widths):  # grid columns too: Word and LibreOffice use these
        col.width = w
    left.width, right.width = widths
    trpr = table.rows[0]._tr.get_or_add_trPr()
    height = OxmlElement("w:trHeight")
    height.set(qn("w:val"), str(int(PHOTO_H.twips)))
    height.set(qn("w:hRule"), "exact")
    trpr.append(height)

    p = left.paragraphs[0]
    run(p, me["name"], bold=True, size=20)
    c = left.add_paragraph()
    c.paragraph_format.space_before = Pt(2)
    run(
        c,
        "  ·  ".join(
            [
                me["email"],
                me["website"].replace("http://", ""),
                me["github"].replace("https://", ""),
                me["linkedin"].replace("https://www.", ""),
            ]
        ),
        dim=True,
    )
    add_private_contact(left.add_paragraph)

    photo = FLAGS["photo"]
    path = photo if os.path.isabs(photo) else os.path.join(ROOT, photo)
    box = right.paragraphs[0]
    box.alignment = 1
    if photo and os.path.exists(path):
        box.add_run().add_picture(path, width=PHOTO_W, height=PHOTO_H)
    else:
        set_cell_border(right)
        right.vertical_alignment = 1  # centre
        run(box, "PHOTO", bold=True, dim=True)
        sub = right.add_paragraph()
        sub.alignment = 1
        run(sub, "35 × 45 mm", dim=True, size=8)


def build_resume(out):
    me = load("personal")[0]
    set_flags(me)
    doc = new_document()

    if FLAGS["photo_box"] or FLAGS["photo"]:
        photo_header(doc, me)
    else:
        p = para(doc)
        run(p, me["name"], bold=True, size=20)
        c = para(doc, before=2)
        run(
            c,
            "  ·  ".join(
                [
                    me["email"],
                    me["website"].replace("http://", ""),
                    me["github"].replace("https://", ""),
                    me["linkedin"].replace("https://www.", ""),
                ]
            ),
            dim=True,
        )
        add_private_contact(lambda: para(doc))

    heading(doc, "Education")
    for e in load("edu"):
        entry_header(doc, e["school"], e["school_location"], e["degree"], e["time_period"])
        for d in e.get("details", []):
            plain_line(doc, d)

    heading(doc, "Experience")
    for e in load("exp"):
        entry_header(
            doc,
            e["company"],
            e["company_location"],
            e["role"] + "  ·  " + e["team"],
            e["time_duration"].strip(),
            before=5,
        )
        for d in e["details"]:
            detail_line(doc, d["title"], d["languages"], d["description"])

    heading(doc, "Publications")
    for i, pub in enumerate(load("pubs"), 1):
        p = para(doc, before=5, hang=0.9)
        run(p, "[%d] " % i, dim=True)
        run(p, pub["title"], bold=True)
        a = para(doc, left=0.9)
        authors_runs(a, pub["authors"], me["name"])
        v = para(doc, left=0.9)
        run(v, venue_text(pub), dim=True)

    heading(doc, "Projects")
    for pr in load("proj"):
        detail_line(doc, pr["title"], pr["languages"], pr["description"])

    heading(doc, "Technical Skills")
    for g in me.get("skill_groups", []):
        p = para(doc, before=1, hang=0.6)
        run(p, g["label"] + ": ", dim=True)
        wrapped_runs(p, wrap_items(len(g["label"]) + 2, g["items"], 2, FLAGS["limit"]), ", ")

    heading(doc, "Certificates")
    for cert in me.get("certificates", []):
        plain_line(doc, cert)

    heading(doc, "Languages")
    p = para(doc, hang=0.6)
    wrapped_runs(p, wrap_items(0, me.get("spoken_languages", []), 3, FLAGS["limit"]), " · ")

    doc.core_properties.author = me["name"]
    doc.core_properties.title = me["name"] + " - Resume"
    doc.save(out)


def build_pubs(out):
    personal = load("personal")[0]
    set_flags(personal)
    me = personal["name"]
    doc = new_document()
    t = para(doc)
    t.alignment = 1
    run(t, "LIST OF PUBLICATIONS", bold=True, size=14)
    n = para(doc, before=2, after=6)
    n.alignment = 1
    run(n, me, dim=True)

    for i, pub in enumerate(load("pubs"), 1):
        p = para(doc, before=9, hang=0.9)
        run(p, "%d. %s" % (i, pub["title"]), bold=True, size=10.5)
        a = para(doc, left=0.9)
        authors_runs(a, pub["authors"], me)
        v = para(doc, left=0.9)
        run(v, venue_text(pub, links=True), dim=True)
        if FLAGS["abstract"] and pub.get("abstract"):
            ab = para(doc, before=3, left=0.9)
            run(ab, "Abstract. ", bold=True, size=8.5)
            run(ab, pub["abstract"], size=8.5)
            if pub.get("keywords"):
                kw = para(doc, before=2, left=0.9)
                run(kw, "Keywords: ", bold=True, size=8.5)
                run(kw, "; ".join(pub["keywords"]), size=8.5)

    doc.core_properties.author = me
    doc.core_properties.title = "Publications - " + me
    doc.save(out)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("resume", "pubs"):
        sys.exit(__doc__)
    {"resume": build_resume, "pubs": build_pubs}[sys.argv[1]](sys.argv[2])
    print("wrote", sys.argv[2])
