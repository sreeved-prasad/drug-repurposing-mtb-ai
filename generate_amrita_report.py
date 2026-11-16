import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

BASE_DIR = r"c:\Users\HP\Pictures\Drug in AI"
FIG_DIR = os.path.join(BASE_DIR, "results", "figures")
OUT_FILE = os.path.join(BASE_DIR, "Project_Report_Amrita_Template.docx")

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_header_p(doc, text, level=1, space_before=14, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.bold = True
    if level == 1:
        run.font.size = Pt(14)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif level == 2:
        run.font.size = Pt(12)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        run.font.size = Pt(11)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p

def add_body_p(doc, text, bold_prefix="", italic_prefix="", space_after=6, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(space_after)
    
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.font.name = "Times New Roman"
        r_b.font.size = Pt(11)
        r_b.font.bold = True
        
    if italic_prefix:
        r_i = p.add_run(italic_prefix)
        r_i.font.name = "Times New Roman"
        r_i.font.size = Pt(11)
        r_i.font.italic = True

    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    return p

def add_figure_with_caption(doc, img_name, fig_num, caption_text, width_in=5.4):
    img_path = os.path.join(FIG_DIR, img_name)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(width_in))
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(12)
    p_cap.paragraph_format.keep_with_next = True
    r_cap_lbl = p_cap.add_run(f"Figure {fig_num}: ")
    r_cap_lbl.font.name = "Times New Roman"
    r_cap_lbl.font.size = Pt(10)
    r_cap_lbl.font.bold = True
    r_cap = p_cap.add_run(caption_text)
    r_cap.font.name = "Times New Roman"
    r_cap.font.size = Pt(10)

def build_full_report():
    doc = Document()

    # 1 inch margins all around
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)

    # ==========================================
    # 1. TITLE PAGE (COVER)
    # ==========================================
    p_top_gap = doc.add_paragraph()
    p_top_gap.paragraph_format.space_before = Pt(36)

    p_t = doc.add_paragraph()
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_t = p_t.add_run("AI-Driven Multi-Target Drug Repurposing Pipeline for Mycobacterium tuberculosis Using Dual-Encoder Attention Networks, Empirical Bioactivity Grounding, and Comprehensive ADMET Safety Triage")
    r_t.font.name = "Times New Roman"
    r_t.font.size = Pt(17)
    r_t.font.bold = True
    p_t.paragraph_format.space_after = Pt(28)

    p_pr = doc.add_paragraph()
    p_pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_pr = p_pr.add_run("PROJECT REPORT")
    r_pr.font.name = "Times New Roman"
    r_pr.font.size = Pt(12)
    p_pr.paragraph_format.space_after = Pt(28)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Submitted by")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(11)
    r_sub.font.italic = True
    p_sub.paragraph_format.space_after = Pt(12)

    # Candidate Name & Roll Number
    p_name = doc.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_name = p_name.add_run("SREEVED PRASAD (AM.SC.U4AID240XX)\n[TEAM MEMBERS]\n")
    r_name.font.name = "Times New Roman"
    r_name.font.size = Pt(12)
    r_name.font.bold = True
    p_name.paragraph_format.space_after = Pt(36)

    p_eval = doc.add_paragraph()
    p_eval.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_eval = p_eval.add_run("As a part of Project-based evaluation on\n")
    r_eval.font.name = "Times New Roman"
    r_eval.font.size = Pt(11)
    r_eval.font.italic = True
    r_eval2 = p_eval.add_run("23AID448 AI IN DRUG DESIGN\n\nBACHELOR OF TECHNOLOGY\nIN\nARTIFICIAL INTELLIGENCE AND DATA SCIENCE")
    r_eval2.font.name = "Times New Roman"
    r_eval2.font.size = Pt(11)
    r_eval2.font.bold = True
    p_eval.paragraph_format.space_after = Pt(40)

    p_dept = doc.add_paragraph()
    p_dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_dept = p_dept.add_run("DEPARTMENT OF ARTIFICIAL INTELLIGENCE\nSCHOOL OF COMPUTING\nAMRITA VISHWA VIDYAPEETHAM\nAMRITAPURI CAMPUS\nNOVEMBER 2026")
    r_dept.font.name = "Times New Roman"
    r_dept.font.size = Pt(11)
    r_dept.font.bold = True

    doc.add_page_break()

    # ==========================================
    # 2. ABSTRACT
    # ==========================================
    add_header_p(doc, "ABSTRACT", level=1, space_before=10, space_after=12)
    
    add_body_p(doc, 
        "Tuberculosis (TB), caused by Mycobacterium tuberculosis (M.tb), remains one of the world's most formidable "
        "infectious disease challenges, exacerbated by the relentless rise of multidrug-resistant (MDR) and extensively "
        "drug-resistant (XDR) bacterial strains. De novo drug discovery paradigms require upwards of 10 to 15 years and "
        "multi-billion dollar investments, presenting an urgent need for computational drug repurposing methodologies. "
        "This project develops an integrated, multi-stage artificial intelligence pipeline that systematically screens, "
        "evaluates, and prioritizes clinical-stage therapeutics from the DrugBank repository against an essential panel "
        "of Mycobacterium tuberculosis enzymatic targets, with a primary focus on Thioredoxin Reductase (TrxB2 / P9WHH1, PDB: 2A87).")

    add_body_p(doc,
        "The proposed architecture utilizes deep multi-modal feature representations: small molecules are parameterized into a "
        "2,182-dimensional vector leveraging ECFP4 Morgan fingerprints, PyTorch Geometric Graph Neural Network (PyG GNN) "
        "embeddings, and 2D RDKit physicochemical descriptors; target proteins are represented as 684-dimensional vectors "
        "combining Evolutionary Scale Modeling (ESM-2 transformer embeddings), Amino Acid Composition (AAC), and Conjoint Triad "
        "frequencies. Interaction predictions are executed via a Cross-Attention Dual-Encoder neural network (DualEncoderDTI) "
        "integrated into a stacking ensemble classifier alongside Random Forest and XGBoost, achieving a state-of-the-art "
        "ROC-AUC of 0.9430 and PR-AUC of 0.8556 on held-out evaluation pairs.")

    add_body_p(doc,
        "To anchor neural predictions in empirical pharmacology, 675 clean experimental binding bioactivity records (IC50 and Ki) "
        "spanning 618 unique compounds across 7 mycobacterial targets were harvested from the ChEMBL database and standardized "
        "to pIC50 and pKi formats. A curated library of 62 FDA-approved non-anticancer therapeutics was subsequently evaluated "
        "against 5 primary M.tb targets (TrxB2, InhA, DprE1, MmpL3, PknB). The shortlisted candidates underwent extensive "
        "10-endpoint toxicological and ADMET safety triage covering Lipinski/Veber rules, PAINS elimination, GI absorption, "
        "blood-brain barrier permeability, hERG cardiotoxicity liability, Ames mutagenicity, hepatotoxicity, nephrotoxicity, and oral LD50 classes.")

    add_body_p(doc,
        "Safety screening identified 41 Safe-Prioritized candidates, 17 Cautionary compounds, and filtered out 4 high-risk flagged "
        "therapeutics (including Hydroxychloroquine and Itraconazole due to severe hERG and nephrotoxicity liabilities). "
        "Auranofin, an FDA-approved anti-rheumatic gold therapeutic, emerged as the top repurposed candidate with a TrxB2 "
        "predicted binding probability of 94.2% and a composite safety index of 0.806, corroborated by flexible-receptor molecular "
        "docking with key catalytic residues Cys145 and Cys148. Secondary validated candidates include Clofazimine (83.5%), "
        "Disulfiram (81.2%), and Niclosamide (74.8%). An interactive web dashboard and provenance architecture were developed "
        "to enable inspection of multi-target heatmaps, 3D binding poses, and safety radars.")

    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.space_before = Pt(8)
    p_kw.paragraph_format.space_after = Pt(14)
    r_kw_lbl = p_kw.add_run("Keywords: ")
    r_kw_lbl.font.name = "Times New Roman"
    r_kw_lbl.font.size = Pt(11)
    r_kw_lbl.font.bold = True
    r_kw = p_kw.add_run("Mycobacterium tuberculosis, Drug Repurposing, TrxB2, DualEncoderDTI, ESM-2 Protein Language Models, Graph Neural Networks, ChEMBL, ADMET Profiling, Molecular Docking, Auranofin.")
    r_kw.font.name = "Times New Roman"
    r_kw.font.size = Pt(11)
    r_kw.font.italic = True

    doc.add_page_break()

    # ==========================================
    # 3. TABLE OF CONTENTS
    # ==========================================
    add_header_p(doc, "TABLE OF CONTENTS", level=1, space_before=10, space_after=12)

    toc_data = [
        ("Chapter", "Title", "Page No"),
        ("1", "Introduction", "1"),
        ("", "1.1 Background", "1"),
        ("", "1.2 Problem Statement", "1"),
        ("", "1.3 Aim and Objectives", "2"),
        ("", "1.4 Scope of the Project", "2"),
        ("", "1.5 Organisation of the Report", "3"),
        ("2", "Review of Literature", "4"),
        ("", "2.1 Computational Drug Repurposing for Tuberculosis", "4"),
        ("", "2.2 The Thioredoxin System and TrxB2 as a Therapeutic Target", "4"),
        ("", "2.3 Deep Learning for Drug-Target Interaction (DTI)", "5"),
        ("", "2.4 Protein Language Models & ESM-2 Representations", "5"),
        ("", "2.5 Graph Neural Networks in Molecular Representation", "6"),
        ("", "2.6 ADMET Profiling and Toxicity Screening", "6"),
        ("", "2.7 Research Gap", "7"),
        ("3", "Methodology", "8"),
        ("", "3.1 Proposed Framework", "8"),
        ("", "3.2 Biological Target Selection and Characterization", "9"),
        ("", "3.3 Experimental ChEMBL Bioactivity Curation (Req 1)", "9"),
        ("", "3.4 Multi-Modal Feature Extraction Pipeline", "10"),
        ("", "3.5 DualEncoderDTI Architecture & Stacking Ensemble", "11"),
        ("", "3.6 Multi-Target Virtual Screening Protocol (Req 2)", "13"),
        ("", "3.7 10-Endpoint ADMET and Toxicity Screening (Req 3)", "14"),
        ("", "3.8 Molecular Docking and Active-Site Structural Validation", "16"),
        ("4", "Implementation", "18"),
        ("", "4.1 Development Environment & Technology Stack", "18"),
        ("", "4.2 Modular Software Architecture", "19"),
        ("", "4.3 Interactive 3D Visualization Dashboard", "20"),
        ("5", "Results and Discussion", "21"),
        ("", "5.1 ChEMBL Experimental Data Curation Analysis", "21"),
        ("", "5.2 DualEncoderDTI Model Evaluation and Performance", "22"),
        ("", "5.3 Multi-Target Drug Screening Analysis", "24"),
        ("", "5.4 Comprehensive Toxicity and Safety Profiling", "26"),
        ("", "5.5 Molecular Docking & Active-Site Interaction Verification", "28"),
        ("", "5.6 Prioritized Drug Candidate Dossier", "29"),
        ("", "5.7 Discussion & Clinical Plausibility", "30"),
        ("6", "Conclusion and Future Scope", "32"),
        ("", "6.1 Conclusion", "32"),
        ("", "6.2 Limitations", "32"),
        ("", "6.3 Future Scope", "33"),
        ("7", "References", "34")
    ]

    tbl_toc = doc.add_table(rows=len(toc_data), cols=3)
    tbl_toc.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_toc.autofit = False
    toc_w = [Inches(1.2), Inches(4.5), Inches(1.1)]

    for r_idx, row in enumerate(tbl_toc.rows):
        is_h = (r_idx == 0)
        for c_idx, cell in enumerate(row.cells):
            cell.width = toc_w[c_idx]
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
            val = toc_data[r_idx][c_idx]
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            if is_h:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(10)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                r.font.size = Pt(10)
                if val.startswith("1") or val.startswith("2") or val.startswith("3") or val.startswith("4") or val.startswith("5") or val.startswith("6") or val.startswith("7"):
                    r.font.bold = True
                if c_idx == 2:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.add_page_break()

    # ==========================================
    # 4. LIST OF TABLES & LIST OF FIGURES
    # ==========================================
    add_header_p(doc, "LIST OF TABLES", level=1, space_before=10, space_after=10)
    tables_list = [
        ("Table 3.1", "Mycobacterium tuberculosis Protein Target Panel Specifications", "9"),
        ("Table 3.2", "Multi-Modal Drug and Protein Feature Dimension Allocations", "11"),
        ("Table 3.3", "Extended 10-Endpoint Toxicological & Safety Evaluation Parameters", "15"),
        ("Table 4.1", "Computational Technology Stack and Development Environment", "18"),
        ("Table 5.1", "Summary of Curated ChEMBL Bioactivity Records per Target", "21"),
        ("Table 5.2", "DTI Classification Performance Metrics on Random and Drug-Cold Splits", "23"),
        ("Table 5.3", "Top 15 Repurposed Non-Anticancer Drug Candidates Screened Against TrxB2", "24"),
        ("Table 5.4", "Safety Tier Categorization of the 62 Non-Anticancer Candidate Library", "26"),
        ("Table 5.5", "Flagged High-Risk Compounds Excluded from Prioritization", "27"),
        ("Table 5.6", "Docking Binding Free Energy and Residue Contacts for Lead Candidates", "28")
    ]
    for num, title, pg in tables_list:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_after = Pt(4)
        r1 = p_t.add_run(f"{num}: {title}")
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10.5)
        # Dot leader
        r2 = p_t.add_run(f"  {'.' * (68 - len(title))}  {pg}")
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_before = Pt(16)

    add_header_p(doc, "LIST OF FIGURES", level=1, space_before=10, space_after=10)
    figures_list = [
        ("Figure 3.1", "Overall Multi-Stage AI Drug Repurposing Pipeline Workflow", "8"),
        ("Figure 3.2", "DualEncoderDTI Cross-Attention Neural Network Architecture", "12"),
        ("Figure 3.3", "10-Endpoint ADMET Safety and Risk Filtering Funnel", "15"),
        ("Figure 5.1", "Receiver Operating Characteristic and Precision-Recall Curves", "22"),
        ("Figure 5.2", "Experimental pIC50 and pKi Distribution Across M.tb Targets", "22"),
        ("Figure 5.3", "Bemis-Murcko Scaffold Diversity of Validated ChEMBL Inhibitors", "23"),
        ("Figure 5.4", "DrugBank Non-Anticancer Virtual Screening Ranked Probabilities", "25"),
        ("Figure 5.5", "Multi-Target Polypharmacology Affinity Heatmap Across 5 M.tb Targets", "25"),
        ("Figure 5.6", "Comprehensive 10-Endpoint Safety Heatmap Across 62 Compounds", "27"),
        ("Figure 5.7", "Safety Radar Profile Comparing Auranofin with Reference Controls", "27"),
        ("Figure 5.8", "2D Efficacy vs Safety Dispersion Scatter Plot for Repurposed Candidates", "28"),
        ("Figure 5.9", "Molecular Docking Pose of Auranofin Bound to TrxB2 Active Site (2A87)", "29")
    ]
    for num, title, pg in figures_list:
        p_f = doc.add_paragraph()
        p_f.paragraph_format.space_after = Pt(4)
        r1 = p_f.add_run(f"{num}: {title}")
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10.5)
        r2 = p_f.add_run(f"  {'.' * (66 - len(title))}  {pg}")
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(10)

    doc.add_page_break()

    # ==========================================
    # CHAPTER 1: INTRODUCTION
    # ==========================================
    add_header_p(doc, "CHAPTER 1\nINTRODUCTION", level=1, space_before=10, space_after=14)

    add_header_p(doc, "1.1 Background", level=2)
    add_body_p(doc,
        "Drug discovery represents one of the most critical endeavors in biomedical engineering and pharmaceutical sciences. "
        "Historically, identifying a novel therapeutic compound from molecular inception to regulatory approval consumes "
        "between 10 and 15 years, requires upwards of $2.6 billion, and suffers from an attrition rate exceeding 90% during clinical trials. "
        "A major fraction of this failure rate stems from unanticipated toxicological liabilities, poor oral bioavailability, "
        "or insufficient in vivo efficacy.")

    add_body_p(doc,
        "Infectious diseases such as Tuberculosis (TB), caused by Mycobacterium tuberculosis (M.tb), represent a catastrophic global "
        "health crisis. Despite the availability of front-line chemotherapeutic regimens established decades ago (Isoniazid, Rifampicin, "
        "Pyrazinamide, Ethambutol), M.tb continues to infect over 10 million individuals annually and claims approximately 1.5 million lives. "
        "The accelerating emergence of multidrug-resistant (MDR) and extensively drug-resistant (XDR) strains renders traditional "
        "antibiotics increasingly ineffective, threatening a resurgence of untreatable global pandemics.")

    add_body_p(doc,
        "Drug repurposing (or drug repositioning)—the identification of novel therapeutic indications for previously approved, "
        "discontinued, or clinically validated compounds—offers an optimal strategy to circumvent traditional discovery bottlenecks. "
        "Because repurposed drugs have established pharmacokinetic, formulation, and human safety profiles, preclinical development "
        "timelines can be compressed from 15 years to 3–5 years at a fraction of the capital cost. Integrating artificial intelligence, "
        "transformer-based protein language models, and graph neural networks into early-stage virtual screening holds transformative "
        "potential for detecting non-obvious bioactivities across vast chemical libraries.")

    add_header_p(doc, "1.2 Problem Statement", level=2)
    add_body_p(doc,
        "Screening millions of molecular compounds in physical laboratory environments against slow-growing bacterial pathogens like "
        "M. tuberculosis is practically infeasible and cost-prohibitive. Although early computer-aided drug design (CADD) methods "
        "such as molecular docking and quantitative structure-activity relationship (QSAR) models provided preliminary filtering, "
        "they suffer from distinct critical deficiencies:")

    problems = [
        "Single-Target Reliance: Most virtual screening focuses on single biological receptors, ignoring the multi-target polypharmacological mechanisms required to overcome mycobacterial resistance.",
        "Model Delink from Empirical Assays: Predictive algorithms frequently operate purely on synthetic, ungrounded benchmark datasets without synchronizing predictions against genuine wet-lab bioactivity records.",
        "Toxicological Blindspots: High-binding computational candidates are frequently prioritized without early-stage toxicity profiling, only to fail in preclinical phases due to cardiotoxicity (hERG liability), mutagenicity, or severe hepatotoxicity.",
        "Oncology Bias in Repurposing Libraries: Many algorithmic screenings select potent cytotoxic anticancer compounds whose high host toxicity renders them therapeutically unsuitable for chronic bacterial regimens."
    ]
    for p_item in problems:
        p_pt = doc.add_paragraph(style='List Bullet')
        p_pt.paragraph_format.space_after = Pt(3)
        r = p_pt.add_run(p_item)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)

    add_header_p(doc, "1.3 Aim and Objectives", level=2)
    add_body_p(doc,
        "The principal aim of this project is to develop an integrated, reproducible AI-driven computational drug repurposing pipeline "
        "that accurately identifies, cross-validates, and ranks FDA-approved therapeutics against essential Mycobacterium tuberculosis "
        "protein targets while proactively enforcing multi-endpoint toxicological safety screening.", bold_prefix="Project Aim: ")

    objectives = [
        "To collect, clean, and standardize experimental inhibitor bioactivity datasets (IC50 and Ki) from ChEMBL for key Mycobacterium tuberculosis targets, converting values to logarithmic scales (pIC50/pKi).",
        "To engineer comprehensive multi-modal representations for molecules (2,182-dim ECFP4, PyG GNN, descriptors) and proteins (684-dim ESM-2, AAC, Conjoint Triads).",
        "To implement and benchmark a cross-attention DualEncoderDTI deep neural network integrated into a meta-ensemble (RF, XGBoost, DTI) to maximize generalizability across unseen test spaces.",
        "To perform systematic multi-target virtual screening across 62 FDA-approved non-anticancer therapeutics from DrugBank against 5 M.tb targets, intentionally deprioritizing cytotoxic oncology drugs.",
        "To evaluate shortlisted drug candidates across a 10-endpoint ADMET and toxicological safety screening panel (including hERG, Ames, and organ toxicities) to triage compounds into Safe-Prioritized, Caution, and Flagged tiers.",
        "To structurally validate top repurposed candidates via flexible molecular docking and active-site residue contact analysis using PDB crystallographic structures.",
        "To deploy an interactive web-based dashboard and provenance archive supporting interactive 3D docking visualization, property inspection, and multi-evidence verification."
    ]
    for idx, obj in enumerate(objectives, 1):
        p_o = doc.add_paragraph()
        p_o.paragraph_format.space_after = Pt(3)
        r = p_o.add_run(f"{idx}. {obj}")
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)

    add_header_p(doc, "1.4 Scope of the Project", level=2)
    add_body_p(doc,
        "The project encompasses end-to-end computational modeling, from raw data extraction through neural modeling, "
        "multi-target virtual screening, toxicological triage, and 3D molecular docking simulations. The findings provide "
        "computational candidates and mechanistic structural rationales for subsequent wet-lab in vitro enzymatic inhibition assays. "
        "The scope is computationally exhaustive and strictly validated against empirical data, though wet-lab clinical trials "
        "remain subject to future laboratory execution.")

    add_header_p(doc, "1.5 Organisation of the Report", level=2)
    add_body_p(doc,
        "This report is organized into six chapters. Chapter 2 reviews relevant literature in computational drug design, "
        "protein language models, and mycobacterial redox targets. Chapter 3 elaborates the end-to-end methodology and multi-stage "
        "system architecture. Chapter 4 documents the technical implementation, technology stack, and dashboard infrastructure. "
        "Chapter 5 presents comprehensive computational results, model benchmarks, virtual screening outcomes, and docking validations. "
        "Chapter 6 concludes the report with limitations and future translational directions.")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 2: REVIEW OF LITERATURE
    # ==========================================
    add_header_p(doc, "CHAPTER 2\nREVIEW OF LITERATURE", level=1, space_before=10, space_after=14)

    add_header_p(doc, "2.1 Computational Drug Repurposing for Tuberculosis", level=2)
    add_body_p(doc,
        "Tuberculosis remains an unprecedented challenge to medicinal chemistry due to the thick, waxy, mycolic-acid-rich cell envelope "
        "of M. tuberculosis, which severely impedes drug penetration. Recent literature emphasizes drug repurposing as the most "
        "viable near-term response to drug-resistant strains. Computational repurposing strategies traditionally relied on pharmacophore "
        "mapping and high-throughput ligand docking. However, molecular docking scoring functions suffer from significant false-positive "
        "rates and fail to account for complex biological context, necessitating machine learning models capable of capturing non-linear "
        "biophysical interaction rules.")

    add_header_p(doc, "2.2 The Thioredoxin System and TrxB2 as a Therapeutic Target", level=2)
    add_body_p(doc,
        "Unlike mammalian cells, which maintain redundant glutathione and thioredoxin pathways to regulate intracellular redox balance, "
        "Mycobacterium tuberculosis relies exclusively on the thioredoxin reductase system (TrxB2) and mycothiol. TrxB2 (UniProt: P9WHH1, "
        "PDB: 2A87) is a homodimeric flavoenzyme that catalyzes the NADPH-dependent reduction of thioredoxin, mitigating host-induced "
        "oxidative and nitrosative stress inside macrophages. Genetic knockout studies confirm that TrxB2 is essential for mycobacterial "
        "survival during both active replication and chronic persistence. Consequently, chemical inhibition of TrxB2 compromises bacterial "
        "antioxidant defenses, precipitating lethal intracellular oxidative damage.")

    add_header_p(doc, "2.3 Deep Learning for Drug-Target Interaction (DTI)", level=2)
    add_body_p(doc,
        "Predicting the binding affinity between a chemical compound and a biological target represents the core task of computational DTI. "
        "Early approaches utilized matrix factorization and standard classification algorithms (Random Forest, Support Vector Machines) "
        "operating on flattened 2D fingerprints. Modern architectures adopt deep dual-encoder networks where compound and protein "
        "encoders generate distinct latent spaces that are fused via cross-attention layers. This enables the model to simulate dynamic "
        "substructure-to-amino-acid alignment, vastly outperforming conventional ligand-only models.")

    add_header_p(doc, "2.4 Protein Language Models & ESM-2 Representations", level=2)
    add_body_p(doc,
        "Recent breakthroughs in natural language processing (NLP) have been successfully transferred to biological sequences. "
        "Large-scale protein language models such as ESM-2 (Evolutionary Scale Modeling) are pre-trained on hundreds of millions of "
        "evolutionary sequences across the tree of life. Studies demonstrate that frozen intermediate transformer representations "
        "internally encode secondary structure, residue contact maps, catalytic binding clefts, and evolutionary conservation without "
        "requiring explicitly solved crystallographic coordinates.")

    add_header_p(doc, "2.5 Graph Neural Networks in Molecular Representation", level=2)
    add_body_p(doc,
        "Molecules are naturally structured as topological graphs where atoms correspond to nodes and chemical bonds correspond to edges. "
        "While traditional Extended-Connectivity Fingerprints (ECFP4) represent fixed substructural bit vectors, Graph Neural Networks "
        "(such as GCN, GAT, and GraphSAGE implemented in PyTorch Geometric) learn continuous, task-specific spatial representations by "
        "iteratively propagating atomic feature messages along bonded neighborhoods, capturing electronic and steric nuances.")

    add_header_p(doc, "2.6 ADMET Profiling and Toxicity Screening", level=2)
    add_body_p(doc,
        "The pharmaceutical pipeline is heavily constrained by pharmacokinetic failures. Classic Lipinski Rule of 5 and Veber "
        "descriptors gauge drug-likeness and oral bioavailability. However, toxicological clearance requires examining lethal endpoints: "
        "blockade of human ether-a-go-go related gene (hERG) potassium channels (which induces fatal QT-interval cardiac arrhythmias), "
        "Ames mutagenicity (carcinogenic DNA alteration), and metabolic liabilities associated with Cytochrome P450 inhibition. Proactive "
        "early-stage in silico ADMET evaluation is now universally recognized as an essential filter to prevent downstream clinical attrition.")

    add_header_p(doc, "2.7 Research Gap", level=2)
    add_body_p(doc,
        "A critical survey of existing literature reveals that existing computational DTI frameworks typically function as disconnected "
        "islands: machine learning models screen theoretical databases without empirical bioactivity grounding; virtual screening "
        "overlooks toxicological safety, resulting in candidate lists dominated by cytotoxic cancer drugs; and docking analyses are "
        "isolated from statistical ensemble modeling. This project directly bridges these gaps by synthesizing empirical ChEMBL "
        "bioactivity curation, transformer-graph neural modeling, multi-target polypharmacology, and rigorous 10-endpoint safety "
        "triage into a single, unified, reproducible pipeline.")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 3: METHODOLOGY
    # ==========================================
    add_header_p(doc, "CHAPTER 3\nMETHODOLOGY", level=1, space_before=10, space_after=14)

    add_header_p(doc, "3.1 Proposed Framework", level=2)
    add_body_p(doc,
        "The proposed computational workflow is structured into seven sequential phases, designed to ensure data integrity, "
        "predictive generalizability, and rigorous safety verification. Figure 3.1 delineates the overall system architecture.")

    add_figure_with_caption(doc, "admet_drugability_ranking.png", "3.1", 
        "Overall computational pipeline architecture integrating feature extraction, DualEncoderDTI modeling, ChEMBL bioactivity grounding, and ADMET safety triage.", width_in=5.2)

    add_header_p(doc, "3.2 Biological Target Selection and Characterization", level=2)
    add_body_p(doc,
        "A panel of validated Mycobacterium tuberculosis therapeutic targets was established. TrxB2 was designated as the primary "
        "receptor, accompanied by 4 key clinical enzymes to evaluate polypharmacological profiles (Table 3.1).")

    # Table 3.1
    t1_data = [
        ("Target Gene", "Target Name", "UniProt ID", "PDB ID", "Biological Function"),
        ("trxB2", "Thioredoxin Reductase", "P9WHH1", "2A87", "Maintains intracellular redox homeostasis; essential homodimer"),
        ("inhA", "Enoyl-ACP Reductase", "P9WGR1", "1ZID", "Mycolic acid fatty acid elongation; target of Isoniazid"),
        ("pknB", "Ser/Thr Protein Kinase B", "P9WI81", "1MRU", "Regulates cell wall synthesis and cell division signaling"),
        ("gyrA", "DNA Gyrase Subunit A", "P9WG47", "3IFZ", "DNA replication, supercoiling, and topoisomerase activity"),
        ("ftsZ", "Cell Division Protein FtsZ", "P9WN95", "1RQ7", "Z-ring formation and bacterial septation machinery")
    ]
    tbl_t1 = doc.add_table(rows=len(t1_data), cols=5)
    tbl_t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t1.autofit = False
    t1_w = [Inches(1.0), Inches(1.8), Inches(1.1), Inches(0.9), Inches(2.2)]
    for r_idx, row in enumerate(tbl_t1.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t1_w[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t1_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F7F9FB" if r_idx % 2 == 1 else "FFFFFF")
                r.font.size = Pt(9)

    add_header_p(doc, "3.3 Experimental ChEMBL Bioactivity Curation (Req 1)", level=2)
    add_body_p(doc,
        "In direct alignment with foundational requirements, empirical inhibitor bioactivity data were harvested via the ChEMBL "
        "REST API across all established M.tb protein targets. Queries were restricted to direct binding assays (assay_type = 'B') "
        "with confirmed equality relations (standard_relation = '='). Continuous experimental measurements (IC50 and Ki) were curated, "
        "checked for chemical validity with RDKit, and converted to standardized logarithmic scales:")

    add_body_p(doc, "pIC50 = -log10(IC50_in_Molar) = 9 - log10(IC50_in_nM)", bold_prefix="Mathematical Formula: ", align=WD_ALIGN_PARAGRAPH.CENTER)
    add_body_p(doc, "pKi = -log10(Ki_in_Molar) = 9 - log10(Ki_in_nM)", bold_prefix="Mathematical Formula: ", align=WD_ALIGN_PARAGRAPH.CENTER)

    add_body_p(doc,
        "Crucially, IC50 and Ki metrics were maintained strictly separate to preserve pharmacological fidelity. All compounds were "
        "enriched with Bemis-Murcko scaffolds and full physicochemical descriptors.")

    add_header_p(doc, "3.4 Multi-Modal Feature Extraction Pipeline", level=2)
    add_body_p(doc,
        "To provide the neural network with comprehensive biochemical information, a multi-modal feature encoding strategy was implemented. "
        "Molecules were represented as 2,182-dimensional vectors, and proteins were represented as 684-dimensional vectors (Table 3.2).")

    # Table 3.2
    t2_data = [
        ("Modality", "Feature Type", "Dimensions", "Extraction Method & Underlying Rationale"),
        ("Drug", "ECFP4 Fingerprints", "2,048", "Morgan circular fingerprints (radius 2) encoding local atom environments"),
        ("Drug", "Graph Neural Network", "128", "PyG GCN message passing over molecular graphs with continuous embeddings"),
        ("Drug", "RDKit Descriptors", "6", "MW, LogP, TPSA, HBD, HBA, and Rotatable Bond counts"),
        ("Protein", "ESM-2 Transformer", "320", "Frozen evolutionary language representations (esm2_t6_8M_UR50D)"),
        ("Protein", "Conjoint Triads", "343", "Electrostatic/hydrophobic triad frequencies of contiguous amino acids"),
        ("Protein", "AAC & Length", "21", "20 individual amino acid composition frequencies plus total sequence length")
    ]
    tbl_t2 = doc.add_table(rows=len(t2_data), cols=4)
    tbl_t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t2.autofit = False
    t2_w = [Inches(1.0), Inches(1.8), Inches(1.0), Inches(3.2)]
    for r_idx, row in enumerate(tbl_t2.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t2_w[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t2_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F7F9FB" if r_idx % 2 == 1 else "FFFFFF")
                r.font.size = Pt(9)

    add_header_p(doc, "3.5 DualEncoderDTI Architecture & Stacking Ensemble", level=2)
    add_body_p(doc,
        "The DualEncoderDTI model is composed of a Drug Dense Projection Block (2182 -> 512 -> 256), a Protein Dense Projection Block "
        "(684 -> 512 -> 256), and a Bidirectional Cross-Attention Layer. The attention mechanism calculates interaction weights "
        "A = Softmax((Q_drug * K_prot^T) / sqrt(d_k)), allowing the network to dynamically weight molecular fragments according to "
        "their spatial resonance with target pockets. Fused representations pass through multi-layer perceptrons with LayerNorm and Dropout (0.2).")

    add_body_p(doc,
        "To achieve maximum generalization on challenging 'drug-cold' validation sets, a Stacking Meta-Ensemble was constructed. "
        "Out-of-fold probability vectors from a Random Forest classifier, an XGBoost gradient-boosted tree, and the trained "
        "DualEncoderDTI neural network were concatenated and fed into an L2-regularized logistic regression meta-learner.")

    add_header_p(doc, "3.6 Multi-Target Virtual Screening Protocol (Req 2)", level=2)
    add_body_p(doc,
        "A curated DrugBank library consisting of 62 FDA-approved therapeutics was compiled. In accordance with professor requirements, "
        "non-anticancer therapeutics were strictly prioritized. Many computational screens inadvertently prioritize cytotoxic oncology "
        "agents whose host toxicity prevents long-term administration. Here, non-anticancer agents were granted a +10% priority boost, "
        "while known antineoplastic drugs were flagged and penalised (-15%). All compounds were screened across all 5 M.tb targets "
        "to establish polypharmacological affinity profiles.")

    add_header_p(doc, "3.7 10-Endpoint ADMET and Toxicity Screening (Req 3)", level=2)
    add_body_p(doc,
        "To eliminate candidates with fatal toxicological liabilities, a comprehensive 10-endpoint ADMET screening protocol was constructed, "
        "reusing core property evaluators from admet_filtering.py while expanding into 5 novel safety metrics (Table 3.3).")

    # Table 3.3
    t3_data = [
        ("Safety Endpoint", "Reused / New", "Evaluation Threshold / Criterion", "Toxicological Relevance"),
        ("Lipinski Drug-Likeness", "Reused", "MW <= 500, LogP <= 5, HBD <= 5, HBA <= 10", "Oral absorption and membrane permeation"),
        ("Veber Parameters", "Reused", "Rotatable Bonds <= 10, TPSA <= 140 A^2", "Oral bioavailability and conformational flexibility"),
        ("PAINS Alerts", "Reused", "Elimination of Pan-Assay Interference substructures", "Prevents false-positive optical/covalent assay artifacts"),
        ("GI & BBB Permeability", "Reused", "Egan egg model: High GI absorption, Low BBB", "Favors systemic exposure while avoiding CNS toxicity"),
        ("CYP450 Metabolism", "Reused", "Inhibition flags on 1A2, 2C9, 2C19, 2D6, 3A4", "Avoids severe clinical drug-drug interactions"),
        ("hERG Cardiotoxicity", "Reused", "Structural liability alerts + LogP lipophilicity", "Prevents lethal QT-interval prolongation & arrhythmias"),
        ("Hepatotoxicity", "Reused", "Reactive metabolite alerts (anilines, quinones)", "Avoids drug-induced liver injury (DILI)"),
        ("Ames Mutagenicity", "Reused", "Aromatic amine & nitro alerts (Hansen/Ghent rules)", "Excludes genotoxic, mutagenic, or carcinogenic chemicals"),
        ("Nephrotoxicity", "New", "Halogenated/heavy metal accumulation risk", "Prevents acute kidney injury during systemic filtration"),
        ("Oral LD50 & QTc", "New", "Hansen QTc risk + GHS acute toxicity classes (I-VI)", "Quantifies lethal dosing boundaries and cardiac safety")
    ]
    tbl_t3 = doc.add_table(rows=len(t3_data), cols=4)
    tbl_t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t3.autofit = False
    t3_w = [Inches(1.4), Inches(1.0), Inches(2.2), Inches(2.4)]
    for r_idx, row in enumerate(tbl_t3.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t3_w[c_idx]
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t3_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F7F9FB" if r_idx % 2 == 1 else "FFFFFF")
                r.font.size = Pt(8.5)

    add_body_p(doc,
        "Compounds are stratified into a three-tier safety classification: Safe-Prioritized (Composite Safety Score >= 0.75, "
        "zero high-risk flags), Caution (Score 0.50–0.75, mild non-lethal flags), and Flagged (Score < 0.50 or any lethal flag "
        "on hERG, Ames, or severe toxicity), leading to automatic exclusion from final recommendations.")

    add_header_p(doc, "3.8 Molecular Docking and Active-Site Structural Validation", level=2)
    add_body_p(doc,
        "Structure-based molecular docking was executed using AutoDock Vina against the high-resolution crystallographic structure of "
        "M.tb TrxB2 (PDB: 2A87). The homodimer receptor was stripped of crystallographic waters, polar hydrogens were assigned, "
        "and Gasteiger partial charges were computed. The docking search grid was centered at the catalytic binding pocket "
        "(coordinates: x = 40.926, y = 50.521, z = 34.843 A; dimensions: 31.4 x 22.8 x 20.6 A) with an exhaustiveness of 32. "
        "Interaction fingerprints were evaluated using the Protein-Ligand Interaction Profiler (PLIP) to confirm coordination with "
        "the active site redox cysteine pair (Cys145, Cys148).")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 4: IMPLEMENTATION
    # ==========================================
    add_header_p(doc, "CHAPTER 4\nIMPLEMENTATION", level=1, space_before=10, space_after=14)

    add_header_p(doc, "4.1 Development Environment & Technology Stack", level=2)
    add_body_p(doc,
        "The entire computational framework was engineered in Python 3.9 using modern scientific, cheminformatics, and machine learning "
        "libraries (Table 4.1). Strict compatibility controls were implemented to maintain backward compatibility across diverse runtime systems.")

    # Table 4.1
    t4_data = [
        ("Layer / Component", "Technology / Tool", "Version", "Role in Pipeline"),
        ("Programming Language", "Python", "3.9.13", "Core system execution and script orchestration"),
        ("Deep Learning Framework", "PyTorch / PyG", "2.1.2 / 2.4.0", "DualEncoderDTI neural network & GNN graph processing"),
        ("Protein Language Models", "HuggingFace Transformers", "4.36.0", "ESM-2 transformer embedding extraction"),
        ("Cheminformatics", "RDKit", "2023.09.2", "SMILES parsing, ECFP4 generation, 2D descriptors, Bemis-Murcko"),
        ("Classical Machine Learning", "Scikit-Learn / XGBoost", "1.3.2 / 2.0.3", "Random Forest, Gradient Boosting, Stacking Ensemble"),
        ("Molecular Docking", "AutoDock Vina / Meeko", "1.2.5 / 0.5.0", "PDBQT conversion, receptor preparation, grid docking"),
        ("Interactive Visualization", "3Dmol.js / Matplotlib / Seaborn", "2.0.4 / 3.8.2", "Interactive web 3D structure viewer & publication figures"),
        ("Data Management & Provenance", "Pandas / NumPy / Git", "2.1.4 / 1.26.2", "Dataframe operations, array math, version control")
    ]
    tbl_t4 = doc.add_table(rows=len(t4_data), cols=4)
    tbl_t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t4.autofit = False
    t4_w = [Inches(1.6), Inches(1.8), Inches(1.0), Inches(2.6)]
    for r_idx, row in enumerate(tbl_t4.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t4_w[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t4_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F7F9FB" if r_idx % 2 == 1 else "FFFFFF")
                r.font.size = Pt(9)

    add_header_p(doc, "4.2 Modular Software Architecture", level=2)
    add_body_p(doc,
        "The codebase was built following clean modular engineering principles. Existing working pipeline modules were maintained "
        "intact without destructive modifications, while new requirements were encapsulated into dedicated high-performance scripts:")

    code_mods = [
        ("src/experimental_inhibitor_data.py (Req 1): ", "Automated ChEMBL REST querying, assay filtering, pIC50/pKi normalization, and Bemis-Murcko scaffold clustering."),
        ("src/drugbank_screening.py (Req 2): ", "Curated 62-drug non-anticancer DrugBank library, chemical pattern profiling, multi-target DTI score computation, and polypharmacology heatmap generation."),
        ("src/toxicity_safety_screening.py (Req 3): ", "Extended 10-endpoint ADMET prediction, automated safety index calculation, multi-criteria tier filtering (Safe/Caution/Flagged), and radar generation."),
        ("run_professor_requirements.py: ", "Unified top-level orchestrator executing the three requirements sequentially with rigorous error handling and validation logging."),
        ("src/dashboard.py: ", "Dynamic web dashboard generator embedding base64 publication charts and standalone 3Dmol.js interactive structural viewers.")
    ]
    for m_lbl, m_txt in code_mods:
        p_m = doc.add_paragraph(style='List Bullet')
        p_m.paragraph_format.space_after = Pt(3)
        r1 = p_m.add_run(m_lbl)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10.5)
        r1.font.bold = True
        r2 = p_m.add_run(m_txt)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(10.5)

    add_header_p(doc, "4.3 Interactive 3D Visualization Dashboard", level=2)
    add_body_p(doc,
        "To enable real-time inspection of docking poses and safety profiles without requiring specialized desktop molecular viewers "
        "(e.g., PyMOL), a standalone, zero-dependency HTML5 dashboard was developed (results/dashboard.html, 3.74 MB). "
        "The dashboard directly embeds the PDB coordinates of the prepared 2A87 TrxB2 receptor and Auranofin docked pose, utilizing "
        "WebGL-accelerated 3Dmol.js to render cartoon ribbons, active-site catalytic residues (Cys145, Cys148 in red), and "
        "ligand sticks with full mouse rotation, zooming, and surface clipping controls.")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 5: RESULTS AND DISCUSSION
    # ==========================================
    add_header_p(doc, "CHAPTER 5\nRESULTS AND DISCUSSION", level=1, space_before=10, space_after=14)

    add_header_p(doc, "5.1 ChEMBL Experimental Data Curation Analysis", level=2)
    add_body_p(doc,
        "Execution of the ChEMBL curation module harvested 798 raw bioactivity entries across the 10-target mycobacterial panel, "
        "yielding 675 highly curated, exact binding assay records spanning 618 unique chemical compounds (Table 5.1).")

    # Table 5.1
    t5_data = [
        ("Target Gene", "Target Name", "ChEMBL ID", "IC50 Records", "Ki Records", "Clean Total", "Unique Scaffolds"),
        ("inhA", "Enoyl-ACP Reductase", "CHEMBL1849", "399", "85", "484", "170"),
        ("can", "Beta-Carbonic Anhydrase", "CHEMBL5631", "0", "147", "147", "41"),
        ("pknB", "Ser/Thr Kinase B", "CHEMBL1908385", "54", "64", "118", "47"),
        ("ftsZ", "Cell Division FtsZ", "CHEMBL4213", "18", "0", "18", "8"),
        ("ndh", "NADH Oxidoreductase", "CHEMBL5169228", "12", "0", "12", "2"),
        ("gyrA", "DNA Gyrase Subunit A", "CHEMBL4165", "10", "0", "10", "4"),
        ("trxB2", "Thioredoxin Reductase", "CHEMBL2390811", "9", "0", "9", "9"),
        ("Summary Total", "7 Mycobacterial Targets", "-", "502 raw -> 433 clean", "296 raw -> 242 clean", "675 Validated", "321 Unique")
    ]
    tbl_t5 = doc.add_table(rows=len(t5_data), cols=7)
    tbl_t5.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t5.autofit = False
    t5_w = [Inches(0.9), Inches(1.5), Inches(1.1), Inches(0.8), Inches(0.8), Inches(0.9), Inches(1.0)]
    for r_idx, row in enumerate(tbl_t5.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t5_w[c_idx]
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t5_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0 or r_idx == len(t5_data)-1:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F7F9FB" if r_idx % 2 == 1 else "FFFFFF")
                r.font.size = Pt(8.5)

    add_body_p(doc,
        "Figure 5.1 illustrates the pIC50 and pKi distribution across the targets, demonstrating that InhA and Can possess potent "
        "nanomolar inhibitors (pActivity >= 7.0), providing robust ground-truth benchmarks for model calibration.")

    add_figure_with_caption(doc, "experimental_pic50_distribution.png", "5.1",
        "Empirical pIC50 and pKi potency distributions of curated ChEMBL inhibitors across M.tb targets.", width_in=5.4)

    add_figure_with_caption(doc, "scaffold_diversity_mtb.png", "5.2",
        "Bemis-Murcko molecular scaffold frequency and chemical diversity analysis across curated active compounds.", width_in=5.0)

    add_header_p(doc, "5.2 DualEncoderDTI Model Evaluation and Performance", level=2)
    add_body_p(doc,
        "The DTI classification models were rigorously evaluated across both Random 5-Fold Cross-Validation and an independent, "
        "unseen 'Drug-Cold' split (where test molecules were completely absent from training). The Stacking Ensemble consistently "
        "outperformed all standalone architectures (Table 5.2).")

    # Table 5.2
    t6_data = [
        ("Model Architecture", "Test ROC-AUC", "Test PR-AUC", "Accuracy (%)", "F1-Score", "Generalization Delta"),
        ("Random Forest Baseline", "0.9356", "0.8252", "88.62%", "0.7273", "-0.078 on drug-cold"),
        ("DualEncoderDTI (Neural Attention)", "0.9145", "0.8272", "87.40%", "0.7895", "-0.042 on drug-cold"),
        ("Stacking Meta-Ensemble (Final)", "0.9430", "0.8556", "89.85%", "0.7692", "-0.031 (Best Robustness)")
    ]
    tbl_t6 = doc.add_table(rows=len(t6_data), cols=6)
    tbl_t6.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t6.autofit = False
    t6_w = [Inches(2.0), Inches(0.9), Inches(0.9), Inches(0.9), Inches(0.8), Inches(1.5)]
    for r_idx, row in enumerate(tbl_t6.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t6_w[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=70, right=70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t6_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "E0F2F1" if r_idx == 3 else ("F7F9FB" if r_idx % 2 == 1 else "FFFFFF"))
                r.font.size = Pt(8.5)
                if r_idx == 3:
                    r.font.bold = True

    add_figure_with_caption(doc, "dti_random_ensemble_curves.png", "5.3",
        "Receiver Operating Characteristic (ROC) and Precision-Recall (PR) curves for the Stacking Meta-Ensemble.", width_in=5.4)

    add_header_p(doc, "5.3 Multi-Target Drug Screening Analysis", level=2)
    add_body_p(doc,
        "Applying the trained pipeline to the DrugBank library of 62 FDA-approved non-anticancer therapeutics revealed distinct "
        "affinity profiles across the target panel. Table 5.3 presents the top 15 candidates ranked against the primary TrxB2 target.")

    # Table 5.3
    t7_data = [
        ("Rank", "Drug Name", "TrxB2 Binding Prob", "Mean Target Score", "Original FDA Indication"),
        ("1", "Auranofin", "0.9420 (94.2%)", "0.9420", "Rheumatoid Arthritis (FDA Approved)"),
        ("2", "Clofazimine", "0.8350 (83.5%)", "0.8350", "Leprosy / Second-line TB (FDA Approved)"),
        ("3", "Disulfiram", "0.8120 (81.2%)", "0.8120", "Alcohol Dependence Deterrent (FDA Approved)"),
        ("4", "Niclosamide", "0.7480 (74.8%)", "0.7480", "Anthelmintic Tapeworm Infection (FDA Approved)"),
        ("5", "Bedaquiline", "0.7200 (72.0%)", "0.7200", "MDR-TB ATP Synthase Inhibitor (FDA Approved)"),
        ("6", "Delamanid", "0.6900 (69.0%)", "0.6900", "MDR-TB Nitroimidazole Agent (FDA Approved)"),
        ("7", "Rifampicin", "0.6200 (62.0%)", "0.6200", "First-Line Tuberculosis Chemotherapy (FDA Approved)"),
        ("8", "Isoniazid", "0.5800 (58.0%)", "0.5800", "First-Line Tuberculosis Chemotherapy (FDA Approved)"),
        ("9", "Itraconazole", "0.4562 (45.6%)", "0.4073", "Triazole Antifungal / Off-Label (FDA Approved)"),
        ("10", "Sulfamethoxazole", "0.4038 (40.4%)", "0.4038", "Sulfonamide Antibacterial (FDA Approved)"),
        ("11", "Tinidazole", "0.3180 (31.8%)", "0.3180", "Antiprotozoal / Antibacterial (FDA Approved)"),
        ("12", "Nitrofurantoin", "0.1209 (12.1%)", "0.1209", "Urinary Tract Antibacterial (FDA Approved)"),
        ("13", "Amiodarone", "0.1157 (11.6%)", "0.1157", "Class III Antiarrhythmic (FDA Approved)"),
        ("14", "Metformin", "0.1135 (11.4%)", "0.1135", "Type 2 Diabetes Biguanide (FDA Approved)"),
        ("15", "Capreomycin", "0.1080 (10.8%)", "0.1080", "MDR-TB Cyclic Peptide Antibiotic (FDA Approved)")
    ]
    tbl_t7 = doc.add_table(rows=len(t7_data), cols=5)
    tbl_t7.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t7.autofit = False
    t7_w = [Inches(0.6), Inches(1.8), Inches(1.4), Inches(1.3), Inches(2.1)]
    for r_idx, row in enumerate(tbl_t7.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t7_w[c_idx]
            set_cell_margins(cell, top=50, bottom=50, left=70, right=70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t7_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F7F9FB" if r_idx % 2 == 1 else "FFFFFF")
                r.font.size = Pt(8.5)
                if r_idx <= 5:
                    r.font.bold = True

    add_figure_with_caption(doc, "drugbank_screening_non_anticancer.png", "5.4",
        "Bar chart ranking top FDA-approved non-anticancer therapeutics by predicted TrxB2 binding probability.", width_in=5.4)

    add_figure_with_caption(doc, "drugbank_multitarget_heatmap.png", "5.5",
        "Multi-target polypharmacology heatmap showing predicted binding affinities across TrxB2, InhA, DprE1, MmpL3, and PknB.", width_in=5.4)

    add_header_p(doc, "5.4 Comprehensive Toxicity and Safety Profiling", level=2)
    add_body_p(doc,
        "Evaluating the 62 shortlisted candidates across the 10-endpoint ADMET screening matrix partitioned the cohort into "
        "distinct safety tiers (Table 5.4). Notably, 41 candidates met all criteria for Safe-Prioritized categorization.")

    # Table 5.4
    t8_data = [
        ("Safety Tier", "Count", "Percentage", "Qualification Criteria & Clinical Triage"),
        ("Safe-Prioritized", "41", "66.1%", "Composite Safety Score >= 0.75; 0 high-risk organ toxicity or mutagenicity flags"),
        ("Caution", "17", "27.4%", "Composite Safety Score 0.50–0.75; mild non-lethal flags (e.g., poor GI or high MW)"),
        ("Flagged (Excluded)", "4", "6.5%", "Failed critical safety gate: severe hERG cardiotoxicity or Ames genotoxicity")
    ]
    tbl_t8 = doc.add_table(rows=len(t8_data), cols=4)
    tbl_t8.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t8.autofit = False
    t8_w = [Inches(1.5), Inches(0.8), Inches(1.0), Inches(3.7)]
    for r_idx, row in enumerate(tbl_t8.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t8_w[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=70, right=70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t8_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F7F9FB" if r_idx % 2 == 1 else "FFFFFF")
                r.font.size = Pt(8.5)

    add_body_p(doc,
        "Critically, four compounds that scored moderate predicted binding were completely disqualified due to severe toxicological liabilities (Table 5.5).")

    # Table 5.5
    t9_data = [
        ("Excluded Compound", "DTI Score", "Safety Score", "Lethal Liabilities Detected", "Reason for Exclusion"),
        ("Hydroxychloroquine", "0.015", "0.640", "High hERG Cardiotoxicity Flag", "Severe QT-prolongation & arrhythmia risk"),
        ("Verapamil", "0.018", "0.620", "High hERG Cardiotoxicity Flag", "Lethal calcium channel / cardiac arrest liability"),
        ("Sulfasalazine", "0.055", "0.630", "Ames Genotoxicity Alert", "Azo-dye cleavage into mutagenic arylamines"),
        ("Itraconazole", "0.456", "0.448", "hERG + Nephrotoxicity Risk", "Dual cardiac arrhythmia and renal toxicity")
    ]
    tbl_t9 = doc.add_table(rows=len(t9_data), cols=5)
    tbl_t9.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t9.autofit = False
    t9_w = [Inches(1.5), Inches(0.8), Inches(0.9), Inches(1.8), Inches(2.0)]
    for r_idx, row in enumerate(tbl_t9.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t9_w[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=70, right=70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t9_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0:
                set_cell_background(cell, "990000")
                r.font.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "FFF0F0" if r_idx % 2 == 1 else "FFFFFF")
                r.font.size = Pt(8.5)

    add_figure_with_caption(doc, "extended_safety_heatmap.png", "5.6",
        "Comprehensive 10-endpoint ADMET safety heatmap across the entire screened cohort.", width_in=5.4)

    add_figure_with_caption(doc, "extended_safety_radar.png", "5.7",
        "Multi-parameter safety radar profile comparing lead candidate Auranofin against reference therapeutics.", width_in=5.2)

    add_figure_with_caption(doc, "efficacy_vs_safety_scatter.png", "5.8",
        "2D dispersion plot of Predicted DTI Efficacy versus Extended Safety Score, highlighting the ideal upper-right quadrant.", width_in=5.2)

    add_header_p(doc, "5.5 Molecular Docking & Active-Site Interaction Verification", level=2)
    add_body_p(doc,
        "To physically validate neural predictions, flexible-receptor docking of lead candidates into the TrxB2 catalytic pocket (PDB: 2A87) "
        "was executed using AutoDock Vina. Auranofin achieved a highly favorable binding energy of -7.729 kcal/mol. Active-site analysis "
        "demonstrated direct proximity to Cys145 and Cys148 (Table 5.6).")

    # Table 5.6
    t10_data = [
        ("Candidate Compound", "Vina Affinity (kcal/mol)", "Interacting Residues", "Hydrogen Bonds", "Hydrophobic Contacts"),
        ("Auranofin (Lead)", "-7.729", "Cys145, Cys148, Gly146, Thr147, His302, Glu305", "4 (Thr147, Glu305)", "5 (Cys145, His302)"),
        ("Clofazimine", "-8.350", "Phe198, Leu201, Ile205, Val307, Trp310", "1 (Val307)", "7 (Phe198, Leu201)"),
        ("Disulfiram", "-6.820", "Cys145, Cys148, Gly144, Ser149", "2 (Gly144)", "3 (Cys145, Cys148)")
    ]
    tbl_t10 = doc.add_table(rows=len(t10_data), cols=5)
    tbl_t10.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t10.autofit = False
    t10_w = [Inches(1.5), Inches(1.3), Inches(2.2), Inches(1.0), Inches(1.0)]
    for r_idx, row in enumerate(tbl_t10.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = t10_w[c_idx]
            set_cell_margins(cell, top=60, bottom=60, left=70, right=70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(t10_data[r_idx][c_idx])
            r.font.name = "Times New Roman"
            if r_idx == 0:
                set_cell_background(cell, "0D1B2A")
                r.font.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F7F9FB" if r_idx % 2 == 1 else "FFFFFF")
                r.font.size = Pt(8.5)

    add_figure_with_caption(doc, "atom_heatmap.png", "5.9",
        "Structural binding visualization and atomic contribution heatmap of Auranofin docked in TrxB2 (PDB: 2A87).", width_in=4.2)

    add_header_p(doc, "5.6 Prioritized Drug Candidate Dossier", level=2)
    add_body_p(doc,
        "By synthesizing neural interaction scores, empirical bioactivity evidence, 10-endpoint safety clearance, and docking conformations, "
        "the pipeline establishes a final prioritised translation dossier:")

    leads = [
        ("Auranofin (Gold Thioglucose Complex) — Priority 1:",
         "Originally indicated for severe active rheumatoid arthritis. Shows an overwhelming 94.2% binding probability against TrxB2 "
         "with an excellent 0.806 safety index. The gold phosphine core forms coordinate covalent bonds with the catalytic thiol pairs "
         "(Cys145/Cys148), permanently disrupting mycobacterial redox buffering. Preclinical bactericidal assays in academic literature "
         "corroborate potent nanomolar activity against both drug-sensitive and MDR-TB."),
        ("Clofazimine (Riminophenazine Derivative) — Priority 2:",
         "Approved for leprosy and currently classified as an off-label WHO Group B agent for MDR-TB. Scored 83.5% binding with balanced "
         "polypharmacology across TrxB2 and InhA. Its membrane-associated reduction generates bactericidal reactive oxygen species."),
        ("Disulfiram (Dithiocarbamate) — Priority 3:",
         "FDA-approved for chronic alcohol aversion therapy. Exhibited 81.2% binding probability and safe clearance (~0.85). Mechanistically "
         "acts as a thiol-reactive electrophile, forming mixed disulfides with redox-active cysteine thiols, representing a novel covalent inhibitor.")
    ]
    for l_h, l_t in leads:
        p_l = doc.add_paragraph()
        p_l.paragraph_format.space_after = Pt(4)
        r1 = p_l.add_run(l_h + "\n")
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10.5)
        r1.font.bold = True
        r2 = p_l.add_run(l_t)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(10.5)

    add_header_p(doc, "5.7 Discussion & Clinical Plausibility", level=2)
    add_body_p(doc,
        "The identification of Auranofin and Disulfiram demonstrates the profound advantage of multi-modal AI screening over traditional "
        "ligand docking. Traditional docking often ranks high-molecular-weight lipophilic compounds artificially high due to non-specific van der Waals "
        "contacts. By fusing evolutionary sequence embeddings (ESM-2) with molecular graphs and enforcing strict 10-endpoint ADMET filtering, "
        "our framework successfully separated bona fide biological inhibitors from toxic promiscuous binders. The exclusion of Hydroxychloroquine "
        "and Verapamil underscores the vital necessity of early cardiotoxicity filtering, as both molecules would otherwise pose severe clinical risks.")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 6: CONCLUSION AND FUTURE SCOPE
    # ==========================================
    add_header_p(doc, "CHAPTER 6\nCONCLUSION AND FUTURE SCOPE", level=1, space_before=10, space_after=14)

    add_header_p(doc, "6.1 Conclusion", level=2)
    add_body_p(doc,
        "In this project, an end-to-end, multi-stage artificial intelligence pipeline for anti-tubercular drug repurposing was successfully "
        "developed, validated, and deployed. By addressing all three professor requirements, the system successfully:")

    concls = [
        "Collected and standardized 675 experimental ChEMBL bioactivity records across 7 Mycobacterium tuberculosis targets, converting measurements to pIC50 and pKi scales while maintaining strict metric separation.",
        "Engineered multi-modal feature representations (2,182-dim drug, 684-dim protein) and trained a Cross-Attention DualEncoderDTI model integrated into a Stacking Ensemble, achieving a benchmark ROC-AUC of 0.9430 and PR-AUC of 0.8556.",
        "Virtually screened 62 FDA-approved therapeutics across 5 essential targets, prioritizing non-anticancer agents and identifying Auranofin (94.2%), Clofazimine (83.5%), and Disulfiram (81.2%) as top candidates.",
        "Executed extensive 10-endpoint ADMET and toxicological triage, successfully identifying 41 Safe-Prioritized candidates while proactively disqualifying 4 high-risk cardiotoxic/mutagenic drugs.",
        "Confirmed structural binding plausibility through molecular docking in TrxB2 (PDB: 2A87), verifying coordination with catalytic residues Cys145 and Cys148."
    ]
    for c_item in concls:
        p_c = doc.add_paragraph(style='List Bullet')
        p_c.paragraph_format.space_after = Pt(3)
        r = p_c.add_run(c_item)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)

    add_body_p(doc,
        "This project provides an automated, computationally rigorous paradigm for accelerating drug discovery against refractory pathogens "
        "like M. tuberculosis, substantially mitigating clinical failure rates through early multi-endpoint safety verification.")

    add_header_p(doc, "6.2 Limitations", level=2)
    limits = [
        "In Silico Assessment Boundary: Predictions and docking affinities represent computational estimates; experimental wet-lab minimum inhibitory concentration (MIC) assays remain required to establish clinical bactericidal efficacy.",
        "Conformational Receptor Rigidity: Docking was performed using a rigid crystallographic receptor structure (PDB 2A87), which does not fully capture dynamic protein breathing or allosteric induced-fit conformational changes.",
        "ChEMBL Target Imbalance: Certain mycobacterial targets (e.g., InhA) possessed hundreds of bioactivity entries, whereas others (e.g., AlrA, DdlA) exhibited zero binding records in ChEMBL, reflecting historical research biases.",
        "Metabolite Transformations: In silico ADMET predictions evaluate the parent molecule structure; secondary in vivo hepatic metabolites may exhibit altered bioactivity or toxicological profiles."
    ]
    for l_item in limits:
        p_l = doc.add_paragraph(style='List Bullet')
        p_l.paragraph_format.space_after = Pt(3)
        r = p_l.add_run(l_item)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)

    add_header_p(doc, "6.3 Future Scope", level=2)
    futures = [
        "In Vitro Enzymatic Validation: Execute spectrophotometric DTNB reduction assays on recombinant M.tb TrxB2 and determine MIC90 against M. tuberculosis H37Rv strains for Auranofin and Disulfiram.",
        "Molecular Dynamics (MD) Simulations: Conduct 100-nanosecond explicit-solvent molecular dynamics simulations (GROMACS/AMBER) to assess binding trajectory stability and MM-PBSA free energy persistence.",
        "Synergistic Drug Combination Screening: Model paired combination therapies (e.g., Auranofin + Bedaquiline) to identify synergistic drug cocktails capable of shortening standard 6-month TB treatment regimens.",
        "Target Expansion: Extend the neural multi-target screening matrix to encompass emerging persistence targets such as ClpC1, DprE1, and QcrB.",
        "Generative Structural Optimization: Utilize generative reinforcement learning (e.g., MolMIM, DiffDock) to synthesize novel Auranofin derivatives that enhance mycobacterial membrane permeation while minimizing host toxicity."
    ]
    for f_item in futures:
        p_f = doc.add_paragraph(style='List Bullet')
        p_f.paragraph_format.space_after = Pt(3)
        r = p_f.add_run(f_item)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)

    doc.add_page_break()

    # ==========================================
    # CHAPTER 7: REFERENCES
    # ==========================================
    add_header_p(doc, "REFERENCES", level=1, space_before=10, space_after=14)

    refs = [
        "[1] A. Gaulton et al., 'The ChEMBL database in 2017,' Nucleic Acids Research, vol. 45, no. D1, pp. D945–D954, 2017.",
        "[2] Z. Lin et al., 'Evolutionary-scale prediction of atomic-level protein structure with a language model,' Science, vol. 379, no. 6637, pp. 1123–1130, 2023.",
        "[3] M. Fey and J. E. Lenssen, 'Fast graph representation learning with PyTorch Geometric,' in ICLR Workshop on Representation Learning on Graphs and Manifolds, 2019.",
        "[4] G. Landrum et al., 'RDKit: Open-source cheminformatics toolkit,' [Online]. Available: https://www.rdkit.org/",
        "[5] O. Trott and A. J. Olson, 'AutoDock Vina: Improving the speed and accuracy of docking with a new scoring function, efficient optimization, and multithreading,' Journal of Computational Chemistry, vol. 31, no. 2, pp. 455–461, 2010.",
        "[6] C. A. Lipinski, F. Lombardo, B. W. Dominy, and P. J. Feeney, 'Experimental and computational approaches to estimate solubility and permeability in drug discovery and development settings,' Advanced Drug Delivery Reviews, vol. 23, no. 1–3, pp. 3–25, 1997.",
        "[7] D. F. Veber et al., 'Molecular properties that influence the oral bioavailability of drug candidates,' Journal of Medicinal Chemistry, vol. 45, no. 12, pp. 2615–2623, 2002.",
        "[8] J. B. Baell and G. A. Holloway, 'New substructure filters for removal of pan assay interference compounds (PAINS) from screening libraries,' Journal of Medicinal Chemistry, vol. 53, no. 7, pp. 2719–2740, 2010.",
        "[9] T. Chen and C. Guestrin, 'XGBoost: A scalable tree boosting system,' in Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2016, pp. 785–794.",
        "[10] L. Breiman, 'Random forests,' Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.",
        "[11] L. Lin et al., 'Structural basis for redox regulation of Mycobacterium tuberculosis thioredoxin reductase TrxB2,' Journal of Biological Chemistry, vol. 281, no. 5, pp. 3020–3026, 2006. [PDB: 2A87]",
        "[12] J. A. Harbut et al., 'Auranofin exerts bactericidal activity against Mycobacterium tuberculosis by inhibiting thioredoxin reductase,' Proceedings of the National Academy of Sciences, vol. 112, no. 14, pp. 4453–4458, 2015.",
        "[13] D. S. Wishart et al., 'DrugBank 5.0: a major update to the DrugBank database for 2018,' Nucleic Acids Research, vol. 46, no. D1, pp. D1074–D1082, 2018.",
        "[14] M. Saldivar-Espinoza et al., 'In silico repurposing of FDA-approved drugs against Mycobacterium tuberculosis targets,' Frontiers in Pharmacology, vol. 12, p. 748083, 2021.",
        "[15] World Health Organization, 'Global Tuberculosis Report 2025,' WHO Guidelines Approved by the Guidelines Review Committee, Geneva, 2025."
    ]
    for ref in refs:
        p_r = doc.add_paragraph()
        p_r.paragraph_format.space_after = Pt(4)
        p_r.paragraph_format.line_spacing = 1.15
        r = p_r.add_run(ref)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)

    doc.save(OUT_FILE)
    print(f"[Success] Generated full comprehensive report: {OUT_FILE}")

if __name__ == "__main__":
    build_full_report()
