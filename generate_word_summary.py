import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_summary_word_doc(output_path):
    doc = Document()

    # Page Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles & Colors
    NAVY = RGBColor(13, 27, 42)      # #0D1B2A
    TEAL = RGBColor(0, 150, 136)     # #009688
    DARK_TEXT = RGBColor(40, 40, 40)
    MUTED = RGBColor(100, 100, 100)

    # Document Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("PROJECT EXECUTIVE SUMMARY")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(24)
    r_title.font.bold = True
    r_title.font.color.rgb = NAVY
    p_title.paragraph_format.space_after = Pt(4)

    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("AI-Driven Multi-Target Drug Repurposing Pipeline for Mycobacterium tuberculosis")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(13)
    r_sub.font.bold = True
    r_sub.font.color.rgb = TEAL
    p_sub.paragraph_format.space_after = Pt(2)

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_meta = p_meta.add_run("Focus: TrxB2 & Secondary Mycobacterial Targets | DualEncoderDTI & 10-Endpoint ADMET Triage")
    r_meta.font.name = "Calibri"
    r_meta.font.size = Pt(10)
    r_meta.font.italic = True
    r_meta.font.color.rgb = MUTED
    p_meta.paragraph_format.space_after = Pt(18)

    # Horizontal divider rule
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(14)
    r_div = p_div.add_run("―" * 58)
    r_div.font.color.rgb = TEAL
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Heading 1: Executive Abstract
    h1 = doc.add_paragraph()
    r_h1 = h1.add_run("1. Executive Abstract")
    r_h1.font.name = "Calibri"
    r_h1.font.size = Pt(15)
    r_h1.font.bold = True
    r_h1.font.color.rgb = NAVY
    h1.paragraph_format.space_before = Pt(10)
    h1.paragraph_format.space_after = Pt(6)

    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.line_spacing = 1.15
    p_abs.paragraph_format.space_after = Pt(10)
    r_abs1 = p_abs.add_run(
        "Tuberculosis (TB), caused by the bacterial pathogen Mycobacterium tuberculosis (M.tb), remains among "
        "the deadliest global infectious diseases. The continuous emergence of multidrug-resistant (MDR) and extensively "
        "drug-resistant (XDR) strains poses a critical challenge to existing healthcare regimens. Conventional de novo drug "
        "discovery workflows require upwards of 10 to 15 years and significant financial capital exceeding $2 billion. "
        "This project presents an artificial intelligence-driven drug repurposing pipeline designed to systematically identify, "
        "evaluate, and prioritize clinical-stage therapeutics for anti-tubercular application."
    )
    r_abs1.font.name = "Calibri"
    r_abs1.font.size = Pt(11)
    r_abs1.font.color.rgb = DARK_TEXT

    p_abs2 = doc.add_paragraph()
    p_abs2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs2.paragraph_format.line_spacing = 1.15
    p_abs2.paragraph_format.space_after = Pt(12)
    r_abs2 = p_abs2.add_run(
        "The primary biological investigation centers on Thioredoxin Reductase (TrxB2 / UniProt: P9WHH1; PDB: 2A87), "
        "an indispensable enzymatic target responsible for bacterial redox homeostasis, complemented by a multi-target panel "
        "including InhA, PknB, GyrA, and FtsZ. Using deep multi-modal representations (ESM-2 protein transformers and "
        "graph neural network molecular embeddings), cross-attention neural models, empirical ChEMBL grounding (675 records), "
        "and multi-endpoint toxicological safety screening, the pipeline discovered that Auranofin exhibits superior binding "
        "(94.2% probability) and strong safety (score: 0.806), establishing a viable, low-toxicity repurposing candidate."
    )
    r_abs2.font.name = "Calibri"
    r_abs2.font.size = Pt(11)
    r_abs2.font.color.rgb = DARK_TEXT

    # Heading 2: Project Architecture & Methodology
    h2 = doc.add_paragraph()
    r_h2 = h2.add_run("2. Methodology & Multi-Stage Architecture")
    r_h2.font.name = "Calibri"
    r_h2.font.size = Pt(15)
    r_h2.font.bold = True
    r_h2.font.color.rgb = NAVY
    h2.paragraph_format.space_before = Pt(12)
    h2.paragraph_format.space_after = Pt(6)

    methods = [
        ("Multi-Modal Feature Engineering: ",
         "Small molecules are converted into 2,182-dimensional vector spaces via ECFP4 Morgan fingerprints (2048-dim), "
         "PyTorch Geometric Graph Neural Network embeddings (128-dim), and RDKit 2D physicochemical descriptors (6-dim). "
         "Proteins are converted into 684-dimensional features using ESM-2 (facebook/esm2_t6_8M_UR50D, 320-dim), "
         "Conjoint Triads (343-dim), Amino Acid Composition (20-dim), and sequence length (1-dim)."),
        ("DualEncoderDTI & Stacking Ensemble: ",
         "A deep neural cross-attention network aligns drug substructural graphs with binding pockets. A meta-ensemble "
         "layer combining Random Forest, XGBoost, and DualEncoderDTI achieved an exceptional test ROC-AUC of 0.943 and "
         "PR-AUC of 0.856, demonstrating superior generalization over single-model architectures."),
        ("Empirical ChEMBL Bioactivity Grounding: ",
         "Extracted and cleaned 675 experimental binding assays (IC50 and Ki) across 7 M. tuberculosis targets from the "
         "ChEMBL REST API, normalizing values to logarithmic potency (pIC50 / pKi = -log10[M]) to ground AI predictions in "
         "verified wet-lab pharmacology."),
        ("Non-Anticancer Drug Screening: ",
         "Screened an extended library of 62 FDA-approved therapeutics from DrugBank across 5 M.tb targets, specifically "
         "rewarding non-oncology therapeutics to circumvent toxic cytotoxic mechanisms."),
        ("10-Endpoint ADMET & Safety Triage: ",
         "Evaluated candidate safety across Lipinski Rule of 5, Veber oral bioavailability, PAINS alerts, gastrointestinal "
         "absorption, blood-brain barrier permeability, hERG cardiotoxicity, Ames mutagenicity, hepatotoxicity, "
         "nephrotoxicity, and oral LD50 toxicity classes.")
    ]

    for title, desc in methods:
        p_m = doc.add_paragraph(style='List Bullet')
        p_m.paragraph_format.space_after = Pt(4)
        p_m.paragraph_format.line_spacing = 1.15
        r_mt = p_m.add_run(title)
        r_mt.font.name = "Calibri"
        r_mt.font.size = Pt(10.5)
        r_mt.font.bold = True
        r_mt.font.color.rgb = TEAL

        r_md = p_m.add_run(desc)
        r_md.font.name = "Calibri"
        r_md.font.size = Pt(10.5)
        r_md.font.color.rgb = DARK_TEXT

    # Heading 3: Summary Table
    h3 = doc.add_paragraph()
    r_h3 = h3.add_run("3. Key Performance Indicators & Project Metrics")
    r_h3.font.name = "Calibri"
    r_h3.font.size = Pt(15)
    r_h3.font.bold = True
    r_h3.font.color.rgb = NAVY
    h3.paragraph_format.space_before = Pt(12)
    h3.paragraph_format.space_after = Pt(6)

    table_data = [
        ("Parameter / Milestone", "Metric / Result", "Description & Significance"),
        ("Primary Target", "TrxB2 (P9WHH1 / 2A87)", "Mycobacterial Thioredoxin Reductase (Cys145, Cys148 active site)"),
        ("Secondary Target Panel", "InhA, PknB, GyrA, FtsZ", "Multi-target polypharmacology screening panel"),
        ("Model Performance", "ROC-AUC: 0.943 | PR-AUC: 0.856", "Stacking meta-ensemble (RF + XGBoost + DualEncoderDTI)"),
        ("Drug Featurization", "2,182 Dimensions", "ECFP4 (2048) + 2D Descriptors (6) + PyG GNN (128)"),
        ("Protein Featurization", "684 Dimensions", "ESM-2 Transformers (320) + Conjoint Triads (343) + AAC (20)"),
        ("Experimental Bioactivity", "675 Validated Records", "Curated ChEMBL binding records (433 IC50, 242 Ki) across 7 targets"),
        ("Virtual Library Screened", "62 FDA-Approved Drugs", "Curated DrugBank library of non-anticancer therapeutics"),
        ("Safety Triage Outcome", "41 Safe / 17 Caution / 4 Flagged", "10-endpoint ADMET filtering; high-risk toxic compounds excluded"),
        ("Top Ranked Candidate", "Auranofin (DTI: 0.942, Safety: 0.806)", "FDA-approved anti-rheumatic; validated via 3D docking into TrxB2")
    ]

    tbl = doc.add_table(rows=len(table_data), cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    col_widths = [Inches(1.8), Inches(2.2), Inches(2.5)]

    for row_idx, row in enumerate(tbl.rows):
        is_header = (row_idx == 0)
        for col_idx, cell in enumerate(row.cells):
            cell.width = col_widths[col_idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)

            val = table_data[row_idx][col_idx]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = "Calibri"

            if is_header:
                set_cell_background(cell, "0D1B2A")
                r.font.size = Pt(9.5)
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                bg_color = "F7F9FB" if row_idx % 2 == 1 else "FFFFFF"
                set_cell_background(cell, bg_color)
                r.font.size = Pt(9)
                r.font.color.rgb = DARK_TEXT
                if col_idx == 1:
                    r.font.bold = True

    # Heading 4: Prioritized Drug Candidates
    h4 = doc.add_paragraph()
    r_h4 = h4.add_run("4. Top Prioritized Candidates for Wet-Lab Translation")
    r_h4.font.name = "Calibri"
    r_h4.font.size = Pt(15)
    r_h4.font.bold = True
    r_h4.font.color.rgb = NAVY
    h4.paragraph_format.space_before = Pt(14)
    h4.paragraph_format.space_after = Pt(6)

    candidates = [
        ("1. Auranofin (DTI Score: 0.942 | Safety: 0.806 | Safe-Prioritized)",
         "Original Indication: Rheumatoid Arthritis. Mechanism: Gold-phosphin compound coordinating with the catalytic redox "
         "cysteine pair (Cys145/Cys148) in TrxB2, validated via flexible receptor 3D docking."),
        ("2. Clofazimine (DTI Score: 0.835 | Safety: ~0.850 | Safe-Prioritized)",
         "Original Indication: Leprosy / MDR-TB. Mechanism: Riminophenazine compound generating intracellular reactive oxygen "
         "species (ROS), exhibiting balanced polypharmacology across TrxB2 and InhA."),
        ("3. Disulfiram (DTI Score: 0.812 | Safety: ~0.850 | Safe-Prioritized)",
         "Original Indication: Chronic Alcoholism. Mechanism: Dithiocarbamate capable of forming mixed disulfides with essential "
         "thiol groups, presenting potent covalent inhibition of mycobacterial redox pathways."),
        ("4. Niclosamide (DTI Score: 0.748 | Safety: 0.792 | Safe-Prioritized)",
         "Original Indication: Anthelmintic. Mechanism: Salicylanilide demonstrating broad antimicrobial efficacy and membrane "
         "potential uncoupling with benign toxicological clearance."),
        ("5. Bedaquiline (DTI Score: 0.730 | Safety: ~0.830 | Safe-Prioritized)",
         "Original Indication: Multidrug-Resistant Tuberculosis. Mechanism: ATP synthase inhibitor acting as an experimental positive "
         "control, validating model calibration and real-world relevance.")
    ]

    for title, desc in candidates:
        p_c = doc.add_paragraph()
        p_c.paragraph_format.space_after = Pt(4)
        p_c.paragraph_format.line_spacing = 1.15
        r_ct = p_c.add_run(title + "\n")
        r_ct.font.name = "Calibri"
        r_ct.font.size = Pt(10.5)
        r_ct.font.bold = True
        r_ct.font.color.rgb = TEAL

        r_cd = p_c.add_run(desc)
        r_cd.font.name = "Calibri"
        r_cd.font.size = Pt(10)
        r_cd.font.color.rgb = DARK_TEXT

    # Heading 5: Conclusion & Translation
    h5 = doc.add_paragraph()
    r_h5 = h5.add_run("5. Conclusion & Translational Impact")
    r_h5.font.name = "Calibri"
    r_h5.font.size = Pt(15)
    r_h5.font.bold = True
    r_h5.font.color.rgb = NAVY
    h5.paragraph_format.space_before = Pt(12)
    h5.paragraph_format.space_after = Pt(6)

    p_conc = doc.add_paragraph()
    p_conc.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_conc.paragraph_format.line_spacing = 1.15
    r_conc = p_conc.add_run(
        "By systematically coupling deep sequence transformers (ESM-2) with molecular graph representations and an extensive "
        "10-endpoint safety filter, this research demonstrates that AI-driven repurposing can compress multi-year preclinical "
        "timelines into automated computational workflows. High-risk compounds (e.g., Hydroxychloroquine, Verapamil, and "
        "Sulfasalazine) were reliably filtered out due to hERG cardiotoxicity and Ames mutagenicity flags, safeguarding "
        "downstream experimental investments. The highlighted lead candidate, Auranofin, represents a mature, clinically viable "
        "therapeutic warranting immediate wet-lab in vitro enzymatic and microdilution assays against Mycobacterium tuberculosis."
    )
    r_conc.font.name = "Calibri"
    r_conc.font.size = Pt(11)
    r_conc.font.color.rgb = DARK_TEXT

    # Footer note
    p_foot = doc.add_paragraph()
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.paragraph_format.space_before = Pt(16)
    r_foot = p_foot.add_run("AI-Driven Drug Repurposing Pipeline • Academic Project Report Summary • 2026")
    r_foot.font.name = "Calibri"
    r_foot.font.size = Pt(8.5)
    r_foot.font.color.rgb = MUTED

    doc.save(output_path)
    print(f"Document saved successfully: {output_path}")

if __name__ == "__main__":
    out_dir = r"c:\Users\HP\Pictures\Drug in AI"
    out_file = os.path.join(out_dir, "Project_Report_Executive_Summary.docx")
    create_summary_word_doc(out_file)
