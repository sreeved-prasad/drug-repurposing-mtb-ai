import collections
import collections.abc
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import pptx.oxml.ns as ns
from lxml import etree

# ─── Color Palette ──────────────────────────────────────────────
BG_DARK     = RGBColor(0x0D, 0x1B, 0x2A)   # Deep navy
ACCENT_TEAL = RGBColor(0x00, 0xC9, 0xA7)   # Vibrant teal
ACCENT_GOLD = RGBColor(0xFF, 0xD6, 0x00)   # Gold
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY  = RGBColor(0xCC, 0xD6, 0xE0)
CARD_BG     = RGBColor(0x1A, 0x2E, 0x44)   # Slightly lighter navy

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

def set_slide_bg(slide, color: RGBColor):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_rect(slide, left, top, width, height, fill_color=None, line_color=None, line_width=Pt(0)):
    shape = slide.shapes.add_shape(
        pptx.enum.shapes.MSO_SHAPE_TYPE.AUTO_SHAPE if False else 1,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.line.width = line_width
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
    else:
        shape.line.fill.background()
    return shape

def add_text_box(slide, text, left, top, width, height,
                 font_size=18, bold=False, color=WHITE,
                 align=PP_ALIGN.LEFT, italic=False, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font_name
    return txBox

def add_multi_line_textbox(slide, lines, left, top, width, height,
                           font_size=16, color=WHITE, bold_first=False, font_name="Calibri"):
    """lines: list of (text, level, bold, color_override)"""
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    first = True
    for (txt, level, bold, col) in lines:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.level = level
        p.space_before = Pt(4)
        run = p.add_run()
        run.text = txt
        run.font.size = Pt(font_size - level * 1.5)
        run.font.bold = bold
        run.font.color.rgb = col if col else color
        run.font.name = font_name
    return txBox

# ════════════════════════════════════════════════════════════════
# SLIDE 1: TITLE
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
set_slide_bg(slide, BG_DARK)

# Top accent bar
add_rect(slide, 0, 0, 13.33, 0.08, fill_color=ACCENT_TEAL)
# Bottom accent bar
add_rect(slide, 0, 7.42, 13.33, 0.08, fill_color=ACCENT_TEAL)

# Left decorative side panel
add_rect(slide, 0, 0, 0.5, 7.5, fill_color=CARD_BG)

# DNA / molecule decorative circle
add_rect(slide, 8.5, 1.0, 4.0, 5.5, fill_color=CARD_BG, line_color=ACCENT_TEAL, line_width=Pt(1.5))

# Main title
add_text_box(slide, "AI-Driven Drug", 1.0, 1.2, 7.2, 1.2, font_size=48, bold=True, color=WHITE)
add_text_box(slide, "Repurposing Pipeline", 1.0, 2.3, 7.2, 1.2, font_size=48, bold=True, color=ACCENT_TEAL)

# Subtitle
add_text_box(slide, "A Deep Learning Approach to Accelerating", 1.0, 3.8, 7.2, 0.6, font_size=20, color=LIGHT_GRAY)
add_text_box(slide, "Tuberculosis Drug Discovery", 1.0, 4.3, 7.2, 0.6, font_size=20, color=LIGHT_GRAY)

# Divider line
add_rect(slide, 1.0, 3.65, 6.0, 0.04, fill_color=ACCENT_GOLD)

# Right panel content
add_text_box(slide, "🎯 Target", 8.8, 1.4, 3.5, 0.4, font_size=13, color=ACCENT_GOLD, bold=True)
add_text_box(slide, "TrxB2 / P9WHH1\n(PDB: 2A87)", 8.8, 1.8, 3.5, 0.7, font_size=14, color=WHITE)
add_rect(slide, 8.7, 2.55, 3.6, 0.03, fill_color=ACCENT_TEAL)

add_text_box(slide, "🦠 Disease", 8.8, 2.7, 3.5, 0.4, font_size=13, color=ACCENT_GOLD, bold=True)
add_text_box(slide, "Tuberculosis (TB)\nMycobacterium tuberculosis", 8.8, 3.1, 3.5, 0.7, font_size=14, color=WHITE)
add_rect(slide, 8.7, 3.85, 3.6, 0.03, fill_color=ACCENT_TEAL)

add_text_box(slide, "💊 Benchmark", 8.8, 4.0, 3.5, 0.4, font_size=13, color=ACCENT_GOLD, bold=True)
add_text_box(slide, "Auranofin\n(FDA-Approved, ROC-AUC: 0.943)", 8.8, 4.4, 3.5, 0.7, font_size=14, color=WHITE)

add_text_box(slide, "Stage 3 Enhanced Pipeline  |  2026", 1.0, 6.9, 7.0, 0.4, font_size=12, color=LIGHT_GRAY, italic=True)

# ════════════════════════════════════════════════════════════════
# SLIDE 2: DISEASE & TARGET
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_rect(slide, 0, 0, 13.33, 0.08, fill_color=ACCENT_TEAL)
add_rect(slide, 0, 7.42, 13.33, 0.08, fill_color=ACCENT_TEAL)

# Slide number tag
add_rect(slide, 12.5, 6.9, 0.75, 0.4, fill_color=ACCENT_TEAL)
add_text_box(slide, "02", 12.5, 6.9, 0.75, 0.4, font_size=14, bold=True, color=BG_DARK, align=PP_ALIGN.CENTER)

# Title
add_rect(slide, 0, 0.3, 0.5, 0.9, fill_color=ACCENT_TEAL)
add_text_box(slide, "Disease & Target", 0.7, 0.3, 8.0, 0.9, font_size=36, bold=True, color=WHITE)
add_rect(slide, 0.7, 1.25, 4.5, 0.04, fill_color=ACCENT_GOLD)

# Left panel — Disease
add_rect(slide, 0.5, 1.5, 5.8, 5.5, fill_color=CARD_BG, line_color=ACCENT_TEAL, line_width=Pt(1.0))
add_text_box(slide, "🦠  DISEASE", 0.8, 1.65, 5.2, 0.5, font_size=14, bold=True, color=ACCENT_TEAL)
add_rect(slide, 0.8, 2.1, 5.2, 0.03, fill_color=ACCENT_TEAL)

disease_lines = [
    ("Tuberculosis (TB)", 0, True, WHITE),
    ("• Leading infectious disease killer worldwide", 1, False, LIGHT_GRAY),
    ("• Caused by Mycobacterium tuberculosis", 1, False, LIGHT_GRAY),
    ("• MDR-TB strains demand novel treatments", 1, False, LIGHT_GRAY),
    ("• Global burden: 10M+ new cases per year", 1, False, LIGHT_GRAY),
]
add_multi_line_textbox(slide, disease_lines, 0.8, 2.2, 5.3, 3.5, font_size=16)

# Right panel — Target
add_rect(slide, 6.8, 1.5, 6.0, 5.5, fill_color=CARD_BG, line_color=ACCENT_GOLD, line_width=Pt(1.0))
add_text_box(slide, "🎯  TARGET PROTEIN", 7.1, 1.65, 5.4, 0.5, font_size=14, bold=True, color=ACCENT_GOLD)
add_rect(slide, 7.1, 2.1, 5.4, 0.03, fill_color=ACCENT_GOLD)

target_lines = [
    ("TrxB2 — Thioredoxin Reductase", 0, True, WHITE),
    ("UniProt: P9WHH1  |  PDB: 2A87", 1, False, ACCENT_TEAL),
    ("• Maintains redox homeostasis in pathogen", 1, False, LIGHT_GRAY),
    ("• Inhibition → oxidative stress → cell death", 1, False, LIGHT_GRAY),
    ("• FAD/NAD binding core (Cys145, Cys148)", 1, False, LIGHT_GRAY),
    ("", 0, False, WHITE),
    ("Benchmark Drug: Auranofin", 0, True, ACCENT_GOLD),
    ("• Au-S coordination with Cys residues", 1, False, LIGHT_GRAY),
    ("• FDA-approved (Rheumatoid Arthritis)", 1, False, LIGHT_GRAY),
    ("• Validated inhibitor of thioredoxin system", 1, False, LIGHT_GRAY),
]
add_multi_line_textbox(slide, target_lines, 7.1, 2.2, 5.4, 4.5, font_size=15)

# ════════════════════════════════════════════════════════════════
# SLIDE 3: WORKFLOW
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_rect(slide, 0, 0, 13.33, 0.08, fill_color=ACCENT_TEAL)
add_rect(slide, 0, 7.42, 13.33, 0.08, fill_color=ACCENT_TEAL)

add_rect(slide, 12.5, 6.9, 0.75, 0.4, fill_color=ACCENT_TEAL)
add_text_box(slide, "03", 12.5, 6.9, 0.75, 0.4, font_size=14, bold=True, color=BG_DARK, align=PP_ALIGN.CENTER)

add_rect(slide, 0, 0.3, 0.5, 0.9, fill_color=ACCENT_TEAL)
add_text_box(slide, "Pipeline Workflow", 0.7, 0.3, 8.0, 0.9, font_size=36, bold=True, color=WHITE)
add_rect(slide, 0.7, 1.25, 5.0, 0.04, fill_color=ACCENT_GOLD)

steps = [
    ("1", "Data Collection & Featurization",
     "2182-dim Drug (ECFP4 + GNN + Descriptors)\n684-dim Protein (ESM-2 + AAC + Conjoint Triads)",
     ACCENT_TEAL, 0.5),
    ("2", "Dual-Encoder DTI Prediction",
     "Cross-Attention DualEncoderDTI neural network\nfusing drug & protein latent representations",
     ACCENT_GOLD, 3.7),
    ("3", "ADMET & Explainability",
     "Lipinski / Veber / PAINS filters + SHAP &\nIntegrated Gradients attribution heatmaps",
     RGBColor(0xFF, 0x6B, 0x6B), 6.9),
    ("4", "Ensemble & MD Stability",
     "RF + XGBoost + DTI stacked ensemble\nMM-GBSA free energy + RMSD stability scoring",
     RGBColor(0x9B, 0x59, 0xB6), 10.1),
]

for (num, heading, body, color, left) in steps:
    add_rect(slide, left, 1.6, 3.0, 0.45, fill_color=color)
    add_text_box(slide, f"  STEP {num}", left, 1.6, 3.0, 0.45, font_size=13, bold=True, color=BG_DARK)
    add_rect(slide, left, 2.05, 3.0, 4.8, fill_color=CARD_BG, line_color=color, line_width=Pt(1.5))
    add_text_box(slide, heading, left + 0.15, 2.2, 2.7, 0.7, font_size=15, bold=True, color=color)
    add_rect(slide, left + 0.15, 2.9, 2.7, 0.03, fill_color=color)
    add_text_box(slide, body, left + 0.15, 3.0, 2.7, 1.8, font_size=13, color=LIGHT_GRAY)

# Arrows between steps
for ax in [3.5, 6.7, 9.85]:
    add_text_box(slide, "▶", ax, 3.5, 0.35, 0.5, font_size=22, bold=True, color=ACCENT_TEAL)

# ════════════════════════════════════════════════════════════════
# SLIDE 4: WHERE HAVE WE REACHED?
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_rect(slide, 0, 0, 13.33, 0.08, fill_color=ACCENT_TEAL)
add_rect(slide, 0, 7.42, 13.33, 0.08, fill_color=ACCENT_TEAL)

add_rect(slide, 12.5, 6.9, 0.75, 0.4, fill_color=ACCENT_TEAL)
add_text_box(slide, "04", 12.5, 6.9, 0.75, 0.4, font_size=14, bold=True, color=BG_DARK, align=PP_ALIGN.CENTER)

add_rect(slide, 0, 0.3, 0.5, 0.9, fill_color=ACCENT_TEAL)
add_text_box(slide, "Where Have We Reached?", 0.7, 0.3, 10.0, 0.9, font_size=36, bold=True, color=WHITE)
add_rect(slide, 0.7, 1.25, 6.0, 0.04, fill_color=ACCENT_GOLD)

achievements = [
    ("✅", "Pipeline Completed", "Stages 1, 2 & 3 are fully operational, tested, and automated end-to-end.", ACCENT_TEAL),
    ("🏆", "Top Drug Hits Identified", "Auranofin: 94.2% binding  |  Clofazimine: 83.5% binding probability vs TrxB2.", ACCENT_GOLD),
    ("🧪", "ADMET Safety Screening", "All 10 drug candidates assessed for oral bioavailability, toxicity, and drug-likeness.", RGBColor(0xFF, 0x6B, 0x6B)),
    ("📊", "Ensemble ROC-AUC: 0.943", "Stacking RF + XGBoost + DualEncoderDTI outperforms all individual models.", RGBColor(0x9B, 0x59, 0xB6)),
    ("🖥️", "Dashboard Generated", "Automated HTML dashboard with embedded visualizations and prediction rankings.", ACCENT_TEAL),
    ("💾", "Models Saved", "Checkpoints saved: dual_encoder_dti.pt and ensemble_stage3.pkl.", LIGHT_GRAY),
]

for i, (icon, heading, body, color) in enumerate(achievements):
    row = i // 2
    col = i % 2
    left = 0.5 + col * 6.5
    top  = 1.55 + row * 1.9
    add_rect(slide, left, top, 6.0, 1.7, fill_color=CARD_BG, line_color=color, line_width=Pt(1.2))
    add_text_box(slide, icon, left + 0.15, top + 0.15, 0.6, 0.6, font_size=22, color=WHITE)
    add_text_box(slide, heading, left + 0.8, top + 0.15, 4.9, 0.45, font_size=15, bold=True, color=color)
    add_text_box(slide, body, left + 0.8, top + 0.6, 4.9, 0.9, font_size=12, color=LIGHT_GRAY)

# ════════════════════════════════════════════════════════════════
# SLIDE 5: TEAM CONTRIBUTIONS
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_rect(slide, 0, 0, 13.33, 0.08, fill_color=ACCENT_TEAL)
add_rect(slide, 0, 7.42, 13.33, 0.08, fill_color=ACCENT_TEAL)

add_rect(slide, 12.5, 6.9, 0.75, 0.4, fill_color=ACCENT_TEAL)
add_text_box(slide, "05", 12.5, 6.9, 0.75, 0.4, font_size=14, bold=True, color=BG_DARK, align=PP_ALIGN.CENTER)

add_rect(slide, 0, 0.3, 0.5, 0.9, fill_color=ACCENT_TEAL)
add_text_box(slide, "Team Contributions", 0.7, 0.3, 10.0, 0.9, font_size=36, bold=True, color=WHITE)
add_rect(slide, 0.7, 1.25, 5.5, 0.04, fill_color=ACCENT_GOLD)

members = [
    ("👤", "[Member 1]", ACCENT_TEAL,
     ["Pipeline Architecture & Design",
      "DualEncoderDTI Neural Network (Cross-Attention Fusion)",
      "Stacking Ensemble Model (RF + XGBoost + DTI)",
      "Training Pipeline & Model Checkpointing"]),
    ("👤", "[Member 2]", ACCENT_GOLD,
     ["ADMET & Drug-Likeness Filtering Module",
      "Lipinski, Veber, PAINS, Toxicity Alerts",
      "Molecular Dynamics (MM-GBSA / RMSD) Module",
      "Per-residue Energy Decomposition"]),
    ("👤", "[Member 3]", RGBColor(0xFF, 0x6B, 0x6B),
     ["Protein Feature Extraction (ESM-2, AAC, Conjoint Triads)",
      "Drug Features (ECFP4, PyG GNN, 3D Conformers)",
      "Explainability (SHAP + Integrated Gradients)",
      "HTML Dashboard & Visualization Generation"]),
]

card_width = 3.8
for i, (icon, name, color, tasks) in enumerate(members):
    left = 0.5 + i * 4.2
    add_rect(slide, left, 1.55, card_width, 5.5, fill_color=CARD_BG, line_color=color, line_width=Pt(1.5))
    # Header
    add_rect(slide, left, 1.55, card_width, 0.7, fill_color=color)
    add_text_box(slide, f"{icon}  {name}", left + 0.1, 1.6, card_width - 0.2, 0.6,
                 font_size=16, bold=True, color=BG_DARK)
    # Tasks
    y = 2.45
    for task in tasks:
        add_rect(slide, left + 0.2, y, 0.18, 0.18, fill_color=color)
        add_text_box(slide, task, left + 0.5, y - 0.05, card_width - 0.65, 0.4,
                     font_size=12, color=LIGHT_GRAY)
        y += 0.9

add_text_box(slide, "* Please update member names before submission",
             0.5, 7.1, 12.0, 0.3, font_size=11, italic=True, color=LIGHT_GRAY)

# ════════════════════════════════════════════════════════════════
# SLIDE 6: RESULTS SUMMARY
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)
add_rect(slide, 0, 0, 13.33, 0.08, fill_color=ACCENT_TEAL)
add_rect(slide, 0, 7.42, 13.33, 0.08, fill_color=ACCENT_TEAL)

add_rect(slide, 12.5, 6.9, 0.75, 0.4, fill_color=ACCENT_TEAL)
add_text_box(slide, "06", 12.5, 6.9, 0.75, 0.4, font_size=14, bold=True, color=BG_DARK, align=PP_ALIGN.CENTER)

add_rect(slide, 0, 0.3, 0.5, 0.9, fill_color=ACCENT_TEAL)
add_text_box(slide, "Results Summary", 0.7, 0.3, 10.0, 0.9, font_size=36, bold=True, color=WHITE)
add_rect(slide, 0.7, 1.25, 4.0, 0.04, fill_color=ACCENT_GOLD)

# Model comparison table header
headers = ["Model", "ROC-AUC", "PR-AUC", "F1-Score"]
col_widths = [4.5, 2.0, 2.0, 2.0]
col_starts = [0.5, 5.2, 7.3, 9.4]
top = 1.55

add_rect(slide, 0.5, top, 11.0, 0.5, fill_color=ACCENT_TEAL)
for j, (h, w, s) in enumerate(zip(headers, col_widths, col_starts)):
    add_text_box(slide, h, s + 0.1, top + 0.08, w, 0.38, font_size=14, bold=True, color=BG_DARK)

rows = [
    ("Random Forest Baseline",     "0.9356", "0.8252", "0.7273", CARD_BG),
    ("DualEncoderDTI (Stage 2)",   "0.9145", "0.8272", "0.7895", CARD_BG),
    ("Stage 3 Stacking Ensemble",  "0.9430", "0.8556", "0.7692", RGBColor(0x10, 0x35, 0x30)),
]
for r_i, (model, roc, pr, f1, bg) in enumerate(rows):
    y = top + 0.5 + r_i * 0.6
    add_rect(slide, 0.5, y, 11.0, 0.58, fill_color=bg)
    is_best = (r_i == 2)
    tc = ACCENT_GOLD if is_best else LIGHT_GRAY
    add_text_box(slide, ("⭐ " if is_best else "   ") + model, 0.6, y + 0.08, 4.5, 0.45, font_size=13, bold=is_best, color=tc)
    for val, s in [(roc, 5.2), (pr, 7.3), (f1, 9.4)]:
        add_text_box(slide, val, s + 0.1, y + 0.08, 1.8, 0.45, font_size=13, bold=is_best, color=tc, align=PP_ALIGN.CENTER)

# Top Candidates
add_text_box(slide, "Top Drug Repurposing Candidates", 0.5, 3.55, 12.0, 0.5, font_size=18, bold=True, color=WHITE)
add_rect(slide, 0.5, 3.95, 12.0, 0.03, fill_color=ACCENT_TEAL)

candidates = [
    ("🥇 Auranofin",    "94.2%", "Rheumatoid Arthritis → TB TrxB2 Inhibitor (Benchmark)", ACCENT_GOLD),
    ("🥈 Clofazimine",  "83.5%", "Leprosy / DR-TB → Multi-target Anti-mycobacterial",    LIGHT_GRAY),
    ("🥉 Niclosamide",  "21.4%", "Anthelmintic → Emerging TB Repurposing Candidate",      LIGHT_GRAY),
]
for c_i, (name, prob, note, col) in enumerate(candidates):
    y = 4.1 + c_i * 0.95
    add_rect(slide, 0.5, y, 12.0, 0.85, fill_color=CARD_BG)
    add_rect(slide, 0.5, y, 0.12, 0.85, fill_color=col)
    add_text_box(slide, name, 0.75, y + 0.1, 3.0, 0.5, font_size=14, bold=True, color=col)
    add_text_box(slide, f"Binding Prob: {prob}", 4.0, y + 0.1, 2.5, 0.5, font_size=13, bold=True, color=ACCENT_TEAL)
    add_text_box(slide, note, 6.7, y + 0.1, 5.6, 0.5, font_size=12, color=LIGHT_GRAY)

# Save
out_path = r"c:\Users\HP\Pictures\Drug in AI\AI_Drug_Repurposing_Pipeline.pptx"
prs.save(out_path)
print(f"Presentation saved to:\n{out_path}")
