#!/usr/bin/env python3
"""ATLAS SSOT · RTL Generator — dark/formal one-pager (English) with per-stage
components. Chain: INPUT → SSOT-AGENT → OUTPUT(SSOT) → RTL-AGENT → OUTPUT(RTL).
Components grounded in workflow/ssot-gen, workflow/rtl-gen, core/atlas_db.py.
Run: python3 scripts/make_agent_pipeline_dark.py
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

BG     = RGBColor(0x0D, 0x14, 0x22)
PANEL  = RGBColor(0x18, 0x21, 0x36)
PANEL2 = RGBColor(0x12, 0x1A, 0x2C)
EDGE   = RGBColor(0x2B, 0x38, 0x52)
TEAL   = RGBColor(0x35, 0xC4, 0xAE)
AMBER  = RGBColor(0xEA, 0xA8, 0x3A)
BLUE   = RGBColor(0x5A, 0x97, 0xF5)
GREEN  = RGBColor(0x4F, 0xC2, 0x84)
VIOLET = RGBColor(0x9B, 0x8C, 0xF0)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
MUTE   = RGBColor(0x9A, 0xAA, 0xC6)
FAINT  = RGBColor(0x6B, 0x79, 0x95)
DARKTX = RGBColor(0x0D, 0x14, 0x22)

prs = Presentation()
prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
s = prs.slides.add_slide(prs.slide_layouts[6])


def shape(kind, x, y, w, h, *, fill=None, line=None, line_w=1.0):
    shp = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.shadow.inherit = False
    if fill is None: shp.fill.background()
    else: shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None: shp.line.fill.background()
    else: shp.line.color.rgb = line; shp.line.width = Pt(line_w)
    return shp


def text(x, y, w, h, lines, *, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, spacing=2):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for i, (t, sz, b, c) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; r = p.add_run(); r.text = t
        r.font.size = Pt(sz); r.font.bold = b; r.font.color.rgb = c; r.font.name = "Calibri"
        p.space_after = Pt(spacing)
    return tb


def arrow(x, y, w, c):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(0.2))
    a.fill.solid(); a.fill.fore_color.rgb = c; a.line.fill.background(); a.shadow.inherit = False


# ── background ──
shape(MSO_SHAPE.RECTANGLE, 0, 0, 13.333, 7.5, fill=BG)

# ── header: title + purpose (english) ──
shape(MSO_SHAPE.RECTANGLE, 0.55, 0.5, 0.07, 1.05, fill=TEAL)
text(0.8, 0.42, 12, 0.34, [("ATLAS", 11, True, FAINT)], align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
text(0.78, 0.68, 12, 0.6, [("SSOT · RTL Generator", 26, True, WHITE)], align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
text(0.80, 1.24, 12.3, 0.5,
     [("An AI agent that turns existing DB knowledge and Q&A into a standardized spec (SSOT),",
       12, False, MUTE)], align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
text(0.80, 1.5, 12.3, 0.32,
     [("then automatically generates synthesizable RTL from it.", 12, False, MUTE)],
     align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
shape(MSO_SHAPE.RECTANGLE, 0.0, 1.98, 13.333, 0.012, fill=EDGE)
text(0.8, 2.04, 12.0, 0.28, [("■ AGENT  AI-executed      ▢ OUTPUT  artifact      ▸ key components", 9.5, True, FAINT)],
     align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.TOP)

# ── agent / IO chain with components ──
AG = MSO_SHAPE.ROUNDED_RECTANGLE
DOC = MSO_SHAPE.FLOWCHART_DOCUMENT
y = 2.45; h = 2.55
nodes = [
    ("input", "Requirements", "INPUT", VIOLET,
     ["▸ AtlasDB (existing DB)", "▸ import_document (PDF→req)", "▸ Deep Interview (Q&A)"]),
    ("agent", "SSOT-AGENT", "spec generation", TEAL,
     ["▸ ssot-gen worker (LLM)", "▸ verify_ssot.py", "▸ check_ssot_disk.sh"]),
    ("out", "SSOT", "OUTPUT", TEAL,
     ["▸ <ip>.ssot.yaml", "▸ standard spec, 20 sections", "▸ io / function_model ..."]),
    ("agent", "RTL-AGENT", "RTL generation", AMBER,
     ["▸ ssot_to_rtl.py (LLM)", "▸ rtl_compile_report.py", "▸ build_gate.sh"]),
    ("out", "RTL", "OUTPUT", AMBER,
     ["▸ <ip>.sv (implementation)", "▸ list/<ip>.f", "▸ rtl_compile.json"]),
]
widths = [2.62, 2.32, 2.42, 2.32, 2.42]
gap = 0.22
total = sum(widths) + gap*(len(nodes)-1)
x = (13.333 - total) / 2
for i, (kind, label, sub, accent, comps) in enumerate(nodes):
    w = widths[i]
    if kind == "agent":
        shape(AG, x, y, w, h, fill=accent)
        text(x, y+0.16, w, 0.3, [("◇ AI AGENT", 8.5, True, DARKTX)])
        text(x, y+0.48, w, 0.75, [(label, 14, True, DARKTX), (sub, 11, False, DARKTX)])
        shape(MSO_SHAPE.RECTANGLE, x+0.28, y+1.42, w-0.56, 0.014, fill=RGBColor(0x0D,0x14,0x22))
        text(x+0.22, y+1.5, w-0.4, 1.0, [(c, 9, False, DARKTX) for c in comps],
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=3)
    elif kind == "out":
        shape(DOC, x, y, w, h+0.1, fill=PANEL, line=accent, line_w=2.25)
        text(x, y+0.18, w, 0.3, [("OUTPUT", 9, True, accent)])
        text(x, y+0.5, w, 0.5, [(label, 17, True, accent)])
        shape(MSO_SHAPE.RECTANGLE, x+0.28, y+1.3, w-0.56, 0.012, fill=EDGE)
        text(x+0.22, y+1.4, w-0.4, 1.0, [(c, 9, False, MUTE) for c in comps],
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=3)
    else:
        shape(MSO_SHAPE.RECTANGLE, x, y, w, h, fill=PANEL2, line=EDGE, line_w=1.5)
        shape(MSO_SHAPE.RECTANGLE, x, y, w, 0.08, fill=VIOLET)
        text(x, y+0.2, w, 0.3, [("INPUT", 9.5, True, VIOLET)])
        text(x, y+0.52, w, 0.5, [(label, 15, True, WHITE)])
        shape(MSO_SHAPE.RECTANGLE, x+0.28, y+1.3, w-0.56, 0.012, fill=EDGE)
        text(x+0.22, y+1.4, w-0.4, 1.0, [(c, 9, False, MUTE) for c in comps],
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=3)
    if i < len(nodes)-1:
        ac = TEAL if i == 1 else (AMBER if i == 3 else FAINT)
        arrow(x + w - 0.01, y + h/2 - 0.1, gap+0.08, ac)
    x += w + gap

# ── divider + expected impact ──
shape(MSO_SHAPE.RECTANGLE, 0.0, 5.28, 13.333, 0.012, fill=EDGE)
text(0.78, 5.36, 12, 0.32, [("EXPECTED IMPACT", 13, True, MUTE)], align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
impacts = [
    ("Design productivity", "Automates spec & RTL authoring,\ncutting repetitive engineering time", TEAL),
    ("Standardization & reuse", "One standard SSOT (20 sections) per IP\n— less quality variance, more reuse", BLUE),
    ("Traceability & auto-checks", "RTL derived from spec + stage gates\ncatch defects early; fully auditable", GREEN),
    ("Knowledge as an asset", "Captures DB & Q&A as a formal spec —\ndesign knowledge becomes reusable", AMBER),
]
iw = 2.98; ig = 0.25; ix = (13.333-(4*iw+3*ig))/2
iy = 5.78; ih = 1.4
for i, (t_i, b_i, c) in enumerate(impacts):
    x = ix + i*(iw+ig)
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, iy, iw, ih, fill=PANEL, line=EDGE, line_w=1.0)
    shape(MSO_SHAPE.RECTANGLE, x, iy, 0.1, ih, fill=c)
    text(x+0.3, iy+0.16, iw-0.45, 0.4, [(t_i, 12.5, True, c)], align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
    text(x+0.3, iy+0.58, iw-0.5, 0.75, [(b_i, 9.5, False, MUTE)], align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)

import os
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "doc", "agent_pipeline_dark.pptx")
prs.save(out); print("saved:", out)
