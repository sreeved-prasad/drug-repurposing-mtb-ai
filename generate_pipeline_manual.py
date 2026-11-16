import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

BASE_DIR = r"c:\Users\HP\Pictures\Drug in AI"
OUT_FILE = os.path.join(BASE_DIR, "Complete_Pipeline_Architecture_and_Execution_Guide.docx")

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
        run.font.color.rgb = RGBColor(13, 27, 42) # Navy
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif level == 2:
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0, 150, 136) # Teal
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(40, 40, 40)
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
        r_b.font.color.rgb = RGBColor(13, 27, 42)
        
    if italic_prefix:
        r_i = p.add_run(italic_prefix)
        r_i.font.name = "Times New Roman"
        r_i.font.size = Pt(11)
        r_i.font.italic = True
        r_i.font.color.rgb = RGBColor(100, 100, 100)

    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(40, 40, 40)
    return p

def create_styled_table(doc, headers, data, col_widths):
    tbl = doc.add_table(rows=len(data) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    # Header Row
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.width = col_widths[c_idx]
        set_cell_background(cell, "0D1B2A")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    for r_idx, row_values in enumerate(data):
        for c_idx, val in enumerate(row_values):
            cell = tbl.cell(r_idx + 1, c_idx)
            cell.width = col_widths[c_idx]
            bg_color = "F7F9FB" if r_idx % 2 == 1 else "FFFFFF"
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(40, 40, 40)
            if c_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def generate_pipeline_doc():
    doc = Document()

    # 1 inch margins all around
    for sec in doc.sections:
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)

    # ==========================================
    # TITLE & METADATA
    # ==========================================
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(4)
    r_t = p_title.add_run("COMPLETE PIPELINE ARCHITECTURE, FILE PROVENANCE, AND CONFIGURATION MANUAL")
    r_t.font.name = "Times New Roman"
    r_t.font.size = Pt(16)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(13, 27, 42)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(14)
    r_s = p_sub.add_run("End-to-End Technical Traceability for AI-Driven Drug Repurposing (Mycobacterium tuberculosis)")
    r_s.font.name = "Times New Roman"
    r_s.font.size = Pt(12)
    r_s.font.bold = True
    r_s.font.color.rgb = RGBColor(0, 150, 136)

    add_body_p(doc,
        "This document provides the definitive technical specification and operational trace of the AI-driven drug "
        "repurposing project for Mycobacterium tuberculosis. It maps out each phase of execution, detailing exactly "
        "where inputs originate, which specific code files and folders process the data, where resulting intermediate "
        "and final artifacts are deposited, and the scientific rationale behind key configuration parameters and hyperparameter choices.")

    # ==========================================
    # 1. HIGH-LEVEL PIPELINE EXECUTION MAP
    # ==========================================
    add_header_p(doc, "1. HIGH-LEVEL PIPELINE EXECUTION MAP", level=1)
    
    add_body_p(doc,
        "The project operates across seven coordinated phases. The entire system can be executed from scratch or run via modular checkpoints:")

    phases_flow = [
        ("Phase 1: Target & Bioactivity Data Acquisition ", "UniProt REST & ChEMBL API querying for M.tb target panel and empirical bioactivities."),
        ("Phase 2: Data Preprocessing & Molecular Curation ", "SMILES standardization, salt stripping, pIC50/pKi logarithmic conversions, and dataset partitioning."),
        ("Phase 3: Multi-Modal Feature Extraction ", "Generating 2,182-dim drug vectors (ECFP4 + PyG GNN + Descriptors) and 684-dim protein vectors (ESM-2 + Conjoint Triads + AAC)."),
        ("Phase 4: Deep Learning & Stacking Meta-Ensemble ", "Training Cross-Attention DualEncoderDTI, Random Forest, and XGBoost; combining them into a stacking meta-ensemble (ROC-AUC: 0.943)."),
        ("Phase 5: Multi-Target Virtual Screening (Req 2) ", "Evaluating 62 FDA-approved non-anticancer DrugBank therapeutics across 5 M.tb targets with non-anticancer prioritization."),
        ("Phase 6: 10-Endpoint ADMET & Toxicological Triage (Req 3) ", "Stratifying candidates into Safe-Prioritized (41), Caution (17), and Flagged (4) using 10 safety parameters."),
        ("Phase 7: Molecular Docking & Dashboard Deployment ", "Validating Auranofin active-site binding in TrxB2 (PDB 2A87) via AutoDock Vina, and rendering the 3D interactive dashboard.")
    ]
    for p_num, p_desc in phases_flow:
        p_pt = doc.add_paragraph(style='List Bullet')
        p_pt.paragraph_format.space_after = Pt(3)
        r1 = p_pt.add_run(p_num)
        r1.font.name = "Times New Roman"
        r1.font.bold = True
        r1.font.color.rgb = RGBColor(0, 150, 136)
        r2 = p_pt.add_run(p_desc)
        r2.font.name = "Times New Roman"

    # ==========================================
    # 2. PHASE-BY-PHASE TECHNICAL SPECIFICATION
    # ==========================================
    add_header_p(doc, "2. PHASE-BY-PHASE TECHNICAL SPECIFICATION", level=1)

    # ------------------------------------------
    # PHASE 1
    # ------------------------------------------
    add_header_p(doc, "Phase 1: Target & Bioactivity Data Acquisition", level=2)
    add_body_p(doc,
        "In this foundational phase, biological targets and empirical wet-lab measurements are fetched directly from official "
        "bioinformatics repositories rather than using arbitrary chemical collections.", bold_prefix="Phase Objective: ")

    p1_headers = ["Pipeline Element", "File / Resource Path", "Format / Size", "Description & Operational Purpose"]
    p1_data = [
        ["External Target Ingestion", "https://rest.uniprot.org/uniprotkb/P9WHH1.fasta", "REST API", "Primary target sequence retrieval for M.tb TrxB2 (P9WHH1, 334 amino acids)"],
        ["Target Crystallography", "https://files.rcsb.org/download/2A87.pdb", "PDB File", "High-resolution (1.9 A) X-ray crystal structure of M.tb TrxB2 homodimer"],
        ["Initial Bioactivities Fetch", "src/data_collection.py", "Python Script", "Initial downloader script querying ChEMBL for raw tuberculosis compound records"],
        ["Raw Bioactivities Dump", "data/raw/chembl_tb_bioactivities.csv", "CSV (288 KB)", "2,400+ uncurated historical bioactivity rows containing assorted assay types"],
        ["Target Metadata Manifest", "data/raw/chembl_tb_targets.csv", "CSV (7.2 KB)", "Summary table of M.tb targets registered in ChEMBL with matching organism IDs"],
        ["Empirical Inhibitors (Req 1)", "src/experimental_inhibitor_data.py", "Python Script", "Advanced ChEMBL REST harvester querying direct binding assays (assay_type='B', '=')"],
        ["Curated Inhibitors Dataset", "results/experimental/mtb_experimental_inhibitors.csv", "CSV (158 KB)", "675 clean records across 7 M.tb targets with standardized pIC50/pKi, scaffolds & 2D properties"],
        ["Target Summary Table", "results/experimental/mtb_inhibitor_summary.csv", "CSV (0.9 KB)", "Per-target record counts, mean potencies, nanomolar hits (>=7.0), and unique scaffold counts"]
    ]
    create_styled_table(doc, p1_headers, p1_data, [Inches(1.8), Inches(2.2), Inches(1.1), Inches(2.1)])

    add_body_p(doc,
        "Querying ChEMBL was restricted to assay_type='B' (direct binding assays) and standard_relation='=' (exact equality). "
        "Assays measuring percentage inhibition ('%') or approximate boundaries ('>', '<') were discarded because machine learning "
        "and QSAR models require exact concentration-dependent equilibrium values to avoid training noise.",
        bold_prefix="Configuration Rationale: ")

    # ------------------------------------------
    # PHASE 2
    # ------------------------------------------
    add_header_p(doc, "Phase 2: Data Preprocessing & Molecular Curation", level=2)
    add_body_p(doc,
        "Raw chemical data contains valence errors, counter-ions, non-standard SMILES, and duplicate structures that require rigorous sanitization.",
        bold_prefix="Phase Objective: ")

    p2_headers = ["Pipeline Element", "File / Resource Path", "Format / Size", "Description & Operational Purpose"]
    p2_data = [
        ["Preprocessing Engine", "src/preprocessing.py", "Python Script", "SMILES validation, salt stripping (RDKit SaltRemover), duplicate averaging, and data partitioning"],
        ["Standardized Dataset", "data/processed/dti_dataset.csv", "CSV (281 KB)", "2,150 model-ready drug-protein pairs with binary binding labels (1 = Active, 0 = Inactive)"],
        ["Split Strategy Config", "src/preprocessing.py (split_dataset)", "Parameters", "Random 80/20 train/test split + Scaffold-aware (Bemis-Murcko) split for 'Drug-Cold' evaluation"]
    ]
    create_styled_table(doc, p2_headers, p2_data, [Inches(1.8), Inches(2.2), Inches(1.1), Inches(2.1)])

    add_body_p(doc,
        "Standardizing to pIC50 = -log10(M) is mandatory because biochemical potency spans 6 orders of magnitude (from 1 nM to 1 mM). "
        "Linear IC50 values in nM skew loss gradients toward weak micromolar compounds, whereas logarithmic conversion provides a smooth, "
        "normally distributed optimization landscape. For binary DTI classification, an active cutoff of IC50 <= 10 uM (pIC50 >= 5.0) was "
        "adopted in alignment with standard medicinal chemistry hit-selection thresholds.",
        bold_prefix="Configuration Rationale: ")

    # ------------------------------------------
    # PHASE 3
    # ------------------------------------------
    add_header_p(doc, "Phase 3: Multi-Modal Feature Extraction", level=2)
    add_body_p(doc,
        "Neither raw SMILES text strings nor amino acid sequence letters can be consumed directly by neural networks. This phase maps "
        "both modalities into structured, high-dimensional vector spaces.", bold_prefix="Phase Objective: ")

    p3_headers = ["Pipeline Element", "File / Resource Path", "Format / Size", "Description & Operational Purpose"]
    p3_data = [
        ["Drug Featurizer Module", "src/drug_features.py", "Python Script", "Extracts 2,182-dim drug vectors: 2048-bit ECFP4 + 128-dim PyG GNN graph embedding + 6 RDKit descriptors"],
        ["Protein Featurizer Module", "src/protein_features.py", "Python Script", "Extracts 684-dim protein vectors: 320-dim ESM-2 transformer + 343-dim Conjoint Triads + 20-dim AAC + 1-dim length"],
        ["Molecular GNN Weights", "results/models/molecular_gnn_encoder.pt", "PyTorch Model (95 KB)", "Pre-trained Graph Convolutional Network weights used to project molecular graphs into 128-dim vectors"],
        ["ESM-2 Embedding Cache", "data/processed/esm_protein_cache.pt", "PyTorch Tensor (31 KB)", "Cached 320-dim tensor embeddings for the M.tb target panel to prevent repeated transformer inference"],
        ["Precomputed Feature Cache", "data/processed/features_cache_stage2.npz", "NumPy Archive (429 KB)", "Pre-extracted multimodal feature arrays for instant model training without re-featurization overhead"]
    ]
    create_styled_table(doc, p3_headers, p3_data, [Inches(1.8), Inches(2.2), Inches(1.1), Inches(2.1)])

    add_body_p(doc,
        "We selected the evolutionary transformer 'facebook/esm2_t6_8M_UR50D' (35M parameters, 6 layers). While larger 650M models exist, "
        "the 8M/35M variants strike the optimal balance between high biological representation fidelity and execution latency (allowing fast "
        "CPU/GPU inference without out-of-memory crashes on consumer machines). For drugs, combining circular Morgan fingerprints (ECFP4) "
        "with GNN graph embeddings ensures both discrete substructural pattern matching and continuous topological message passing are captured.",
        bold_prefix="Configuration Rationale: ")

    # ------------------------------------------
    # PHASE 4
    # ------------------------------------------
    add_header_p(doc, "Phase 4: Deep Learning & Stacking Meta-Ensemble", level=2)
    add_body_p(doc,
        "This phase trains, optimizes, and ensembles predictive models to achieve robust generalization across unseen compounds.",
        bold_prefix="Phase Objective: ")

    p4_headers = ["Pipeline Element", "File / Resource Path", "Format / Size", "Description & Operational Purpose"]
    p4_data = [
        ["Neural Network Model", "src/model.py", "Python Script", "PyTorch DualEncoderDTI architecture: Drug/Protein projection blocks + Cross-Attention fusion + MLP"],
        ["Training & Evaluation", "src/train.py & src/evaluate.py", "Python Scripts", "AdamW optimization, BCEWithLogitsLoss, learning rate scheduler, early stopping, and metric calculation"],
        ["Trained DTI Checkpoint", "results/models/dual_encoder_dti.pt", "PyTorch Weights (6.5 MB)", "Best saved checkpoint of the trained DualEncoderDTI neural network (test ROC-AUC: 0.9145)"],
        ["Stacking Meta-Ensemble", "src/ensemble_model.py", "Python Script", "Combines Random Forest, XGBoost, and DualEncoderDTI probability vectors into a logistic meta-learner"],
        ["Saved Ensemble Model", "results/models/ensemble_stage3.pkl", "Pickle File (0.7 KB)", "Serialised meta-classifier weights achieving test ROC-AUC: 0.9430 and PR-AUC: 0.8556"],
        ["Evaluation Curves", "results/figures/dti_random_ensemble_curves.png", "PNG Image (248 KB)", "Publication ROC and Precision-Recall evaluation curves comparing all architectures"],
        ["Benchmark Metrics CSV", "results/metrics/model_comparison_random.csv", "CSV (0.3 KB)", "Numerical comparison of Accuracy, Precision, Recall, F1, ROC-AUC, and PR-AUC across models"]
    ]
    create_styled_table(doc, p4_headers, p4_data, [Inches(1.8), Inches(2.2), Inches(1.1), Inches(2.1)])

    add_body_p(doc,
        "The Cross-Attention mechanism computes Attention(Q, K, V) = Softmax((Q_drug * K_prot^T) / sqrt(d_k)) * V_drug. "
        "Unlike naive concatenation (which assumes independent static features), cross-attention allows the model to dynamically weight "
        "which chemical functional groups interact with specific protein sequence motifs. The Stacking Ensemble uses L2-regularized Logistic "
        "Regression as the meta-learner to prevent any single algorithm (like Random Forest) from overfitting on dominant chemical scaffolds.",
        bold_prefix="Configuration Rationale: ")

    # ------------------------------------------
    # PHASE 5
    # ------------------------------------------
    add_header_p(doc, "Phase 5: Multi-Target Virtual Screening (Req 2)", level=2)
    add_body_p(doc,
        "Screening approved drugs to discover repurposing candidates against the M.tb target panel, strictly prioritizing non-anticancer agents.",
        bold_prefix="Phase Objective: ")

    p5_headers = ["Pipeline Element", "File / Resource Path", "Format / Size", "Description & Operational Purpose"]
    p5_data = [
        ["Virtual Screening Module", "src/drugbank_screening.py", "Python Script", "Screens 62 FDA-approved drugs across 5 M.tb targets; applies non-anticancer bonus/penalty; outputs ranking"],
        ["Target Library Definition", "src/polypharmacology.py (MTB_TARGETS)", "Config Dict", "Pre-set dictionary defining sequences and UniProt IDs for TrxB2, InhA, DprE1, MmpL3, and PknB"],
        ["TrxB2 Screening Output", "results/predictions/drugbank_trxb2_screening.csv", "CSV (9.3 KB)", "62 drugs ranked by predicted TrxB2 binding probability (Top: Auranofin = 0.9420)"],
        ["Multi-Target Screening", "results/predictions/drugbank_multitarget_screening.csv", "CSV (9.7 KB)", "Cross-target matrix containing individual probabilities, mean scores, and non-AC priority scores"],
        ["Screening Bar Chart", "results/figures/drugbank_screening_non_anticancer.png", "PNG Image (191 KB)", "Horizontal ranked bar chart of top candidates with FDA indications"],
        ["Polypharmacology Heatmap", "results/figures/drugbank_multitarget_heatmap.png", "PNG Image (217 KB)", "2D color-mapped matrix illustrating candidate binding specificity across all 5 M.tb targets"],
        ["Inhibitor Profile Chart", "results/figures/inhibitor_property_profile.png", "PNG Image (132 KB)", "Physicochemical property distribution (MW, LogP, TPSA) of active inhibitors"]
    ]
    create_styled_table(doc, p5_headers, p5_data, [Inches(1.8), Inches(2.2), Inches(1.1), Inches(2.1)])

    add_body_p(doc,
        "Cancer chemotherapy relies on general cellular cytotoxicity (DNA cross-linking, tubulin destruction) to kill rapidly proliferating cells. "
        "In chronic bacterial infections like tuberculosis (requiring 6+ months of daily treatment), administering cytotoxic oncology drugs "
        "induces severe bone marrow suppression, immunosuppression, and host mortality. Therefore, the pipeline applies a +10% priority boost "
        "to non-anticancer drugs and penalizes antineoplastics (-15%) to steer recommendations toward safe, long-term anti-infectives.",
        bold_prefix="Configuration Rationale: ")

    # ------------------------------------------
    # PHASE 6
    # ------------------------------------------
    add_header_p(doc, "Phase 6: 10-Endpoint ADMET & Toxicological Triage (Req 3)", level=2)
    add_body_p(doc,
        "Ensuring shortlisted high-binding molecules do not carry fatal toxicological, mutagenic, or cardiotoxic liabilities.",
        bold_prefix="Phase Objective: ")

    p6_headers = ["Pipeline Element", "File / Resource Path", "Format / Size", "Description & Operational Purpose"]
    p6_data = [
        ["Extended Safety Engine", "src/toxicity_safety_screening.py", "Python Script", "Evaluates 10 ADMET endpoints: 5 core from admet_filtering.py + 5 extended toxicological metrics"],
        ["Core ADMET Evaluator", "src/admet_filtering.py", "Python Script", "Reused functions calculating Lipinski, Veber, PAINS, GI, BBB, CYP metabolism, and hERG liability"],
        ["Extended Safety Profiles", "results/safety/extended_safety_profiles.csv", "CSV (20 KB)", "Comprehensive 42-column table reporting property values, flags, scores, and tiers for all 62 drugs"],
        ["Binding vs Safety Matrix", "results/safety/binding_vs_safety_comparison.csv", "CSV (8.1 KB)", "Integrated comparison table sorting candidates by Safety Tier and DTI binding probability"],
        ["Safety Heatmap Figure", "results/figures/extended_safety_heatmap.png", "PNG Image (318 KB)", "Color-coded matrix across all 10 endpoints showing risk profiles of the entire library"],
        ["Safety Radar Profile", "results/figures/extended_safety_radar.png", "PNG Image (293 KB)", "Multi-axis polygonal radar comparing Auranofin against reference antimycobacterials"],
        ["Tier Ranking Bar Chart", "results/figures/final_tiered_ranking.png", "PNG Image (199 KB)", "Grouped bar chart showing candidate distribution into Safe-Prioritized, Caution, and Flagged"],
        ["Efficacy vs Safety Scatter", "results/figures/efficacy_vs_safety_scatter.png", "PNG Image (223 KB)", "2D dispersion plot mapping DTI probability vs Extended Safety Score"]
    ]
    create_styled_table(doc, p6_headers, p6_data, [Inches(1.8), Inches(2.2), Inches(1.1), Inches(2.1)])

    add_body_p(doc,
        "Safety scoring applies normalized weighted penalties across 10 distinct biological endpoints. The tier thresholds are set at "
        "Safe-Prioritized (Score >= 0.75, zero high-risk flags), Caution (Score 0.50–0.75), and Flagged (Score < 0.50 or any high-risk flag on "
        "hERG, Ames, or organ failure). Compounds with hERG channel affinity are disqualified immediately because hERG blockade triggers "
        "fatal Torsades de Pointes ventricular arrhythmias, the #1 cause of post-market pharmaceutical withdrawal worldwide.",
        bold_prefix="Configuration Rationale: ")

    # ------------------------------------------
    # PHASE 7
    # ------------------------------------------
    add_header_p(doc, "Phase 7: Molecular Docking & Dashboard Deployment", level=2)
    add_body_p(doc,
        "Confirming biophysical binding poses and providing real-time interactive visualization of results.", bold_prefix="Phase Objective: ")

    p7_headers = ["Pipeline Element", "File / Resource Path", "Format / Size", "Description & Operational Purpose"]
    p7_data = [
        ["Docking Orchestrator", "src/docking.py", "Python Script", "Receptor preparation (PDB to PDBQT via Meeko), ligand 3D conformer generation, and AutoDock Vina execution"],
        ["Raw TrxB2 Crystal Structure", "results/docking/2A87.pdb", "PDB File (540 KB)", "X-ray crystallographic coordinates of M.tb TrxB2 homodimer downloaded from RCSB PDB"],
        ["Prepared Receptor", "results/docking/2A87_prepared.pdb", "PDB File (512 KB)", "Receptor stripped of crystallographic water molecules with assigned polar hydrogens and partial charges"],
        ["Docked Ligand Pose", "results/docking/auranofin_docked.pdb", "PDB File (2.8 KB)", "Lowest energy 3D binding conformation (-7.729 kcal/mol) of Auranofin within the TrxB2 pocket"],
        ["Complex Structure", "results/docking/2A87_auranofin_complex.pdb", "PDB File (515 KB)", "Combined coordinates of TrxB2 receptor and docked Auranofin for structural inspection"],
        ["Docking Metrics JSON", "results/docking/auranofin_trxb2_docking_report.json", "JSON File (1.5 KB)", "Detailed docking report listing affinity, RMSD, active-site residue distances, and PLIP contacts"],
        ["Standalone 3D HTML Viewer", "results/docking/auranofin_trxb2_interactive_3d.html", "HTML File (4.2 KB)", "Lightweight 3D viewer rendering the docking pocket using 3Dmol.js"],
        ["Comprehensive Web Dashboard", "src/dashboard.py -> results/dashboard.html", "HTML File (3.74 MB)", "Standalone zero-dependency dashboard embedding all 14 figures, summary tables, and WebGL 3D viewer"]
    ]
    create_styled_table(doc, p7_headers, p7_data, [Inches(1.8), Inches(2.2), Inches(1.1), Inches(2.1)])

    add_body_p(doc,
        "AutoDock Vina was executed with a search grid centered at (40.926, 50.521, 34.843) A with dimensions of 31.4 x 22.8 x 20.6 A "
        "and exhaustiveness = 32. Crystallographic waters were excluded ('dry receptor') to simulate direct coordinate covalent bonding "
        "with the catalytic nucleophilic thiolates Cys145 and Cys148. The dashboard embeds all assets as Base64 strings directly inside "
        "dashboard.html so that it functions completely offline without requiring local web servers or internet connectivity.",
        bold_prefix="Configuration Rationale: ")

    # ==========================================
    # 3. DIRECTORY STRUCTURE SUMMARY
    # ==========================================
    add_header_p(doc, "3. COMPLETE PROJECT FOLDER DIRECTORY MAP", level=1)
    
    add_body_p(doc,
        "Below is the complete physical folder tree of the repository, summarizing what each folder owns and stores:")

    folders_map = [
        ("data/raw/", "Stores uncurated raw downloads: ChEMBL initial CSV dumps, target lists, and UniProt JSON descriptors."),
        ("data/processed/", "Stores curated, sanitized datasets: model-ready DTI CSVs, ESM-2 tensor caches, and precomputed feature arrays."),
        ("src/", "Contains all 19 modular Python source files covering data ingestion, feature generation, deep learning, screening, safety, docking, and dashboarding."),
        ("results/experimental/", "Dedicated repository for Requirement 1 outputs: normalized ChEMBL inhibitor CSVs (675 records) and per-target summary metrics."),
        ("results/predictions/", "Dedicated repository for Requirement 2 outputs: DrugBank TrxB2 and multi-target screening ranking tables."),
        ("results/safety/", "Dedicated repository for Requirement 3 outputs: extended 10-endpoint ADMET profiles and safety-binding comparison tables."),
        ("results/models/", "Contains binary weights and serialized models: dual_encoder_dti.pt (PyTorch), molecular_gnn_encoder.pt, and ensemble_stage3.pkl."),
        ("results/docking/", "Stores crystallographic coordinates (PDB), prepared receptors, docked ligand poses, docking JSON reports, and PyMOL scripts."),
        ("results/figures/", "Houses all 14 high-resolution publication PNG visualizations (ROC curves, heatmaps, radars, distributions, and scatter plots)."),
        ("results/metrics/", "Stores model performance CSV records comparing Random Forest, XGBoost, and DualEncoderDTI across random and cold-drug splits."),
        ("root folder /", "Contains high-level orchestrator scripts (run_professor_requirements.py), automated Word/PPT generators, README.md, and PROJECT_PROGRESS.md.")
    ]
    for f_name, f_desc in folders_map:
        p_f = doc.add_paragraph(style='List Bullet')
        p_f.paragraph_format.space_after = Pt(3)
        r1 = p_f.add_run(f_name + " : ")
        r1.font.name = "Times New Roman"
        r1.font.bold = True
        r1.font.color.rgb = RGBColor(13, 27, 42)
        r2 = p_f.add_run(f_desc)
        r2.font.name = "Times New Roman"

    # ==========================================
    # 4. STEP-BY-STEP REPRODUCIBILITY COMMANDS
    # ==========================================
    add_header_p(doc, "4. STEP-BY-STEP REPRODUCIBILITY & EXECUTION COMMANDS", level=1)

    add_body_p(doc,
        "To reproduce the entire pipeline from scratch or execute individual stages independently, the following commands are used:")

    cmds = [
        ("Step 1: Execute Full Professor Requirements Pipeline",
         "cd 'c:\\Users\\HP\\Pictures\\Drug in AI'\npython run_professor_requirements.py",
         "Executes Req 1 (ChEMBL API harvesting) -> Req 2 (62-drug virtual screening) -> Req 3 (10-endpoint safety triage) in sequential automated flow."),
        ("Step 2: Generate Updated Web Dashboard",
         "python src/dashboard.py",
         "Re-reads all latest prediction and safety CSVs and generates the 3.74 MB standalone results/dashboard.html with embedded 3D viewer."),
        ("Step 3: Generate Formal Project Report (.docx)",
         "python generate_amrita_report.py",
         "Generates the full 34-page academic project report in the official Amrita template (Project_Report_Amrita_Template.docx)."),
        ("Step 4: Generate Updated Presentation (.pptx)",
         "python generate_ppt.py",
         "Builds the 9-slide presentation deck (AI_Drug_Repurposing_Pipeline.pptx) incorporating all newly generated requirement findings.")
    ]
    for c_title, c_code, c_note in cmds:
        p_c = doc.add_paragraph()
        p_c.paragraph_format.space_after = Pt(2)
        r1 = p_c.add_run(c_title + "\n")
        r1.font.name = "Times New Roman"
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = RGBColor(0, 150, 136)

        r2 = p_c.add_run(c_code + "\n")
        r2.font.name = "Courier New"
        r2.font.size = Pt(9.5)
        r2.font.bold = True
        r2.font.color.rgb = RGBColor(13, 27, 42)

        r3 = p_c.add_run("Explanation: " + c_note)
        r3.font.name = "Times New Roman"
        r3.font.size = Pt(10)
        r3.font.italic = True
        p_c.paragraph_format.space_after = Pt(8)

    # Footer note
    p_foot = doc.add_paragraph()
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.paragraph_format.space_before = Pt(20)
    r_foot = p_foot.add_run("AI-Driven Drug Repurposing Pipeline • Complete Technical Architecture Manual • 2026")
    r_foot.font.name = "Times New Roman"
    r_foot.font.size = Pt(9)
    r_foot.font.color.rgb = RGBColor(100, 100, 100)

    doc.save(OUT_FILE)
    print(f"[Success] Generated Complete Pipeline Word Document: {OUT_FILE}")

if __name__ == "__main__":
    generate_pipeline_doc()
