import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

BASE_DIR = r"c:\Users\HP\Pictures\Drug in AI"
OUT_FILE = os.path.join(BASE_DIR, "How_The_Code_Works_Viva_Guide.docx")

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_step_box(doc, step_num, title, files, input_data, what_code_does, output_data, why_setting):
    # Step Heading
    p_h = doc.add_paragraph()
    p_h.paragraph_format.space_before = Pt(14)
    p_h.paragraph_format.space_after = Pt(4)
    p_h.paragraph_format.keep_with_next = True
    r_num = p_h.add_run(f"STEP {step_num}: ")
    r_num.font.name = "Calibri"
    r_num.font.bold = True
    r_num.font.size = Pt(13)
    r_num.font.color.rgb = RGBColor(0, 150, 136) # Teal
    
    r_t = p_h.add_run(title)
    r_t.font.name = "Calibri"
    r_t.font.bold = True
    r_t.font.size = Pt(13)
    r_t.font.color.rgb = RGBColor(13, 27, 42) # Navy

    # Table for clear 1-glance summary
    tbl = doc.add_table(rows=5, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    w_col1 = Inches(1.8)
    w_col2 = Inches(4.7)

    rows_info = [
        ("File(s) Used", files, "0D1B2A", True),
        ("Where Input Comes From", input_data, "F7F9FB", False),
        ("What The Code Does", what_code_does, "FFFFFF", False),
        ("Output Generated", output_data, "F7F9FB", False),
        ("Why This Setting Was Used", why_setting, "FFFFFF", False)
    ]

    for idx, (label, val, bg, is_hdr) in enumerate(rows_info):
        row = tbl.rows[idx]
        
        # Col 1: Label
        cell1 = row.cells[0]
        cell1.width = w_col1
        set_cell_background(cell1, "E0F2F1" if not is_hdr else "0D1B2A")
        set_cell_margins(cell1)
        p1 = cell1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(label)
        r1.font.name = "Calibri"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(13, 27, 42) if not is_hdr else RGBColor(255, 255, 255)

        # Col 2: Content
        cell2 = row.cells[1]
        cell2.width = w_col2
        set_cell_background(cell2, bg if not is_hdr else "0D1B2A")
        set_cell_margins(cell2)
        p2 = cell2.paragraphs[0]
        p2.paragraph_format.space_after = Pt(2)
        r2 = p2.add_run(val)
        r2.font.name = "Calibri"
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = RGBColor(40, 40, 40) if not is_hdr else RGBColor(255, 255, 255)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_simple_guide():
    doc = Document()

    # 1 inch margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin = Inches(0.9)
        sec.right_margin = Inches(0.9)

    # Title
    p_t = doc.add_paragraph()
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t.paragraph_format.space_before = Pt(6)
    p_t.paragraph_format.space_after = Pt(2)
    r_t = p_t.add_run("HOW THE PROJECT CODE WORKS: STEP-BY-STEP EXPLANATION")
    r_t.font.name = "Calibri"
    r_t.font.size = Pt(16)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(13, 27, 42)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)
    r_s = p_sub.add_run("A Simple, Direct Guide for Presentations and Viva Reviews")
    r_s.font.name = "Calibri"
    r_s.font.size = Pt(11)
    r_s.font.bold = True
    r_s.font.color.rgb = RGBColor(0, 150, 136)

    # Intro Speech line
    p_speech = doc.add_paragraph()
    p_speech.paragraph_format.space_after = Pt(8)
    r_sp = p_speech.add_run(
        "One-Sentence Summary to Say in Review: 'Our project takes existing approved drugs, converts both the drug and the "
        "tuberculosis protein into AI-readable numbers, uses a neural network to predict if they bind, filters out any toxic drugs, "
        "and checks the 3D binding using molecular docking.'"
    )
    r_sp.font.name = "Calibri"
    r_sp.font.size = Pt(10.5)
    r_sp.font.italic = True
    r_sp.font.color.rgb = RGBColor(100, 100, 100)

    # ==========================================
    # STEPS
    # ==========================================
    add_step_box(
        doc,
        step_num="1",
        title="Collect Real Lab Data from ChEMBL (Requirement 1)",
        files="src/experimental_inhibitor_data.py",
        input_data="Internet / ChEMBL REST API (online database of published laboratory experiments)",
        what_code_does="Automatically downloads 675 real lab measurements (IC50 and Ki) for 7 tuberculosis proteins. It cleans invalid chemicals and converts raw numbers to standard pIC50 and pKi values.",
        output_data="results/experimental/mtb_experimental_inhibitors.csv\nresults/experimental/mtb_inhibitor_summary.csv",
        why_setting="• Used assay_type='B' and standard_relation='=' so we only get exact binding measurements, not approximate guesses.\n• Kept IC50 and Ki separate because they measure different biological interactions."
    )

    add_step_box(
        doc,
        step_num="2",
        title="Convert Drugs and Proteins into Numbers (Feature Extraction)",
        files="src/drug_features.py\nsrc/protein_features.py",
        input_data="• Drug SMILES text strings (e.g., CC(=O)Oc1ccccc1C(=O)O)\n• Protein amino acid sequence (e.g., MKLKNTIVVV... from UniProt)",
        what_code_does="Computes 2,182 numbers for each drug (chemical fingerprints + graph neural network embeddings + 2D properties) and 684 numbers for each protein (using Meta's ESM-2 AI protein model + amino acid composition).",
        output_data="data/processed/features_cache_stage2.npz (saved arrays)\ndata/processed/esm_protein_cache.pt (saved protein numbers)",
        why_setting="• AI cannot read chemical structures or letters; it only understands numbers.\n• Used ESM-2 because it was trained on millions of evolutionary proteins and understands protein folding."
    )

    add_step_box(
        doc,
        step_num="3",
        title="Train the AI Model to Predict Drug-Protein Binding",
        files="src/model.py (DualEncoderDTI)\nsrc/train.py\nsrc/ensemble_model.py",
        input_data="The numbers created in Step 2 from 2,150 known drug-protein pairs (data/processed/dti_dataset.csv).",
        what_code_does="Trains a deep neural network with Cross-Attention so the drug features and protein features talk to each other. It then combines the neural network with Random Forest and XGBoost into an Ensemble.",
        output_data="results/models/dual_encoder_dti.pt (6.5 MB saved AI model)\nresults/models/ensemble_stage3.pkl (saved ensemble model)",
        why_setting="• Cross-Attention lets the AI find which part of the drug hits which part of the protein pocket.\n• The 3-model Ensemble prevents mistakes and achieved a high 0.943 ROC-AUC score."
    )

    add_step_box(
        doc,
        step_num="4",
        title="Screen 62 Approved Drugs Against TB Targets (Requirement 2)",
        files="src/drugbank_screening.py",
        input_data="A library of 62 FDA-approved drugs from DrugBank + 5 M.tb protein targets (TrxB2, InhA, PknB, etc.).",
        what_code_does="Passes all 62 drugs through our trained AI model. It boosts non-cancer drugs (+10%) and penalizes cancer drugs (-15%) to find the best safe hits.",
        output_data="results/predictions/drugbank_trxb2_screening.csv\nresults/predictions/drugbank_multitarget_screening.csv\nresults/figures/drugbank_multitarget_heatmap.png",
        why_setting="• We prioritized non-cancer drugs because cancer drugs are toxic cell-killers and cannot be taken daily for 6 months by TB patients.\n• Top hit identified: Auranofin (94.2% binding probability)."
    )

    add_step_box(
        doc,
        step_num="5",
        title="Filter Out Dangerous & Toxic Drugs (Requirement 3)",
        files="src/toxicity_safety_screening.py\nsrc/admet_filtering.py",
        input_data="The shortlisted candidates from Step 4.",
        what_code_does="Tests each drug across 10 safety checkpoints (heart risk / hERG, liver toxicity, DNA mutagenicity / Ames test, kidney risk, and lethal dose). Scores each drug from 0 to 1.",
        output_data="results/safety/extended_safety_profiles.csv\nresults/safety/binding_vs_safety_comparison.csv\nresults/figures/final_tiered_ranking.png",
        why_setting="• Divided drugs into 3 Tiers: 41 Safe-Prioritized, 17 Caution, 4 Flagged.\n• Flagged & eliminated drugs like Hydroxychloroquine and Verapamil because they fail the hERG test (cause fatal heart attacks)."
    )

    add_step_box(
        doc,
        step_num="6",
        title="3D Molecular Docking Validation",
        files="src/docking.py",
        input_data="• 3D structure of TB TrxB2 protein (results/docking/2A87.pdb from PDB)\n• 3D structure of top drug Auranofin",
        what_code_does="Runs AutoDock Vina simulation. Physically fits Auranofin into the TrxB2 protein pocket like a key in a lock and measures the binding energy.",
        output_data="results/docking/auranofin_docked.pdb (-7.729 kcal/mol binding energy)\nresults/docking/auranofin_trxb2_docking_report.json",
        why_setting="• Proves physically that the drug actually touches the two exact amino acids (Cys145 and Cys148) the bacteria needs to survive."
    )

    add_step_box(
        doc,
        step_num="7",
        title="Interactive Dashboard & Presentation",
        files="src/dashboard.py\ngenerate_amrita_report.py\ngenerate_ppt.py",
        input_data="All the CSV tables and PNG charts generated in Steps 1 to 6.",
        what_code_does="Builds a standalone website dashboard (results/dashboard.html) with a 3D viewer, generates the official Word report (.docx), and creates the PPT presentation.",
        output_data="results/dashboard.html (3.74 MB interactive dashboard)\nProject_Report_Amrita_Template.docx\nAI_Drug_Repurposing_Pipeline.pptx",
        why_setting="• All images and 3D protein data are baked directly into the HTML file, so it opens instantly on any computer without needing an internet connection or extra software."
    )

    # Footer note
    p_f = doc.add_paragraph()
    p_f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_f.paragraph_format.space_before = Pt(12)
    r_f = p_f.add_run("AI in Drug Design • Code Review & Viva Reference Guide • 2026")
    r_f.font.name = "Calibri"
    r_f.font.size = Pt(9)
    r_f.font.color.rgb = RGBColor(120, 120, 120)

    doc.save(OUT_FILE)
    print(f"[Success] Generated Simple Viva Guide: {OUT_FILE}")

if __name__ == "__main__":
    build_simple_guide()
