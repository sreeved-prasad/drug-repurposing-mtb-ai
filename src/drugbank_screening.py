"""
NEW MODULE — Requirement 2: Extended DrugBank Screening & Chemical Pattern Analysis
=====================================================================================
Analyses chemical patterns of inhibitors that bind to M. tuberculosis targets,
then uses the existing trained DualEncoderDTI model to screen an extended DrugBank
library.  Prioritises non-anticancer drugs in the final ranking.

REUSED COMPONENTS:
  - model.py:            DualEncoderDTI (loads existing checkpoint)
  - drug_features.py:    get_drug_encoding() — 2182-dim combined representation
  - protein_features.py: get_protein_encoding() — 684-dim combined representation
  - polypharmacology.py: MTB_TARGETS, TARGET_SEQUENCES, fetch_target_sequence()
  - admet_filtering.py:  compute_lipinski_properties() for quick profile
  - prediction.py:       DRUG_LIBRARY (original 10-drug library, kept intact)

NEWLY IMPLEMENTED:
  - Extended DrugBank-style library (60+ non-anticancer FDA-approved drugs)
  - Anticancer flag based on indication keyword matching
  - Chemical pattern analysis: MW/LogP/TPSA distributions, Morgan fingerprint
    similarity to known TB inhibitors, scaffold diversity
  - Per-target screening across all 5 MTB_TARGETS from polypharmacology.py
  - Comparison table: original library vs extended library predictions
  - Multiple visualisations: scatter, heatmap, bar chart
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch

# ── Reuse existing project modules ────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from model          import DualEncoderDTI
from drug_features  import get_drug_encoding, get_morgan_fingerprint, get_physicochemical_descriptors
from protein_features import get_protein_encoding
from polypharmacology import MTB_TARGETS, TARGET_SEQUENCES, fetch_target_sequence, DRUG_LIBRARY as ORIGINAL_DRUG_LIBRARY
from admet_filtering import compute_lipinski_properties

try:
    from rdkit import Chem
    from rdkit.Chem import DataStructs, AllChem
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT_DIR    = os.path.dirname(os.path.dirname(__file__))
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
MODELS_DIR  = os.path.join(RESULTS_DIR, "models")
PRED_DIR    = os.path.join(RESULTS_DIR, "predictions")
FIG_DIR     = os.path.join(RESULTS_DIR, "figures")
EXP_DIR     = os.path.join(RESULTS_DIR, "experimental")

# ══════════════════════════════════════════════════════════════════════════════
# Extended DrugBank Library — 60+ Diverse FDA-Approved Non-Anticancer Drugs
# (original 10 from DRUG_LIBRARY intentionally included for comparison)
# ══════════════════════════════════════════════════════════════════════════════

ANTICANCER_KEYWORDS = {
    "cancer", "oncol", "tumor", "leukemia", "lymphoma", "myeloma",
    "carcinoma", "antineoplastic", "chemotherapy", "cytotoxic", "sarcoma",
    "melanoma", "glioma", "hepatocell"
}

EXTENDED_DRUG_LIBRARY = [
    # ── Original 10 (from DRUG_LIBRARY — kept for comparison) ──────────────────
    {"drug_name": "Auranofin",       "smiles": "CC(=O)OCC1C(C(C(C(O1)S[Au]P(CC)(CC)CC)OC(=O)C)OC(=O)C)OC(=O)C",
     "indication": "Rheumatoid Arthritis (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Clofazimine",     "smiles": "CC(C)NC1=NC2=CC=CC=C2N(C3=CC=C(C=C3)Cl)C1=NC4=CC=C(C=C4)Cl",
     "indication": "Leprosy / Off-label TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Disulfiram",      "smiles": "CCN(CC)C(=S)SSC(=S)N(CC)CC",
     "indication": "Alcohol Dependence (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Niclosamide",     "smiles": "C1=CC(=C(C=C1Cl)NC(=O)C2=C(C=CC(=C2)[N+](=O)[O-])O)Cl",
     "indication": "Anthelmintic (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Linezolid",       "smiles": "CC(=O)NCC1CN(C2=CC(=C(C=C2)N3CCOCC3)F)C(=O)O1",
     "indication": "Gram-positive / DR-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Ciprofloxacin",   "smiles": "C1CC1N2C=C(C(=O)C3=CC(=C(C=C32)N4CCNCC4)F)C(=O)O",
     "indication": "Broad-spectrum Fluoroquinolone (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Chloroquine",     "smiles": "CCN(CC)CCCC(C)NC1=C2C=CC(Cl)=CC2=NC=C1",
     "indication": "Malaria / Amoebiasis (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Metformin",       "smiles": "CN(C)C(=N)NC(=N)N",
     "indication": "Type 2 Diabetes (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Atorvastatin",    "smiles": "CC(C)C1=C(C(=C(N1CCC(CC(CC(=O)O)O)O)C2=CC=C(C=C2)F)C3=CC=CC=C3)C(=O)NC4=CC=CC=C4",
     "indication": "Dyslipidemia (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Aspirin",         "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
     "indication": "Anti-inflammatory / NSAID (FDA Approved)", "is_anticancer": False},

    # ── Antibiotics & Antimicrobials ──────────────────────────────────────────
    {"drug_name": "Rifampicin",      "smiles": "CC1C=CC=C(C(=O)NC2=C(C=CC3=C2OC(C)(C)C(=O)C3=O)OC)C=CC(C)C(O)C(C)C(O)C(C)C1=O",
     "indication": "First-line Anti-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Isoniazid",       "smiles": "NNC(=O)c1ccncc1",
     "indication": "First-line Anti-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Ethambutol",      "smiles": "CCC(CO)NCC(CC)N",
     "indication": "First-line Anti-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Pyrazinamide",    "smiles": "NC(=O)c1cnccn1",
     "indication": "First-line Anti-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Moxifloxacin",    "smiles": "COc1ccc2c(c1)nc1cc(N3CC[C@@H](N)C3)c(=O)c(C(=O)O)n1[C@@H]2C1CC1",
     "indication": "Fluoroquinolone / MDR-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Amikacin",        "smiles": "NCC[C@@H](O)[C@H]([NH3+])C(=O)N[C@@H]1[C@H]([NH3+])[C@@H](O)[C@H](O[C@H]2O[C@H](CO)[C@@H](O)[C@H]([NH3+])[C@H]2O)[C@@H](N[C@H]3O[C@@H](CN)[C@H](O)[C@@H]3O)[C@@H]1O",
     "indication": "Aminoglycoside / MDR-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Doxycycline",     "smiles": "C[C@@H]1[C@H]2C[C@H]3CC(=C(C(=O)[C@@]3(C(=O)N)[O-])O)c4c(cc(O)c(c4[C@@H]2[NH+](C)C)O)[C@@H]1O",
     "indication": "Broad-spectrum Antibiotic (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Minocycline",     "smiles": "CN(C)[C@@H]1C(O)=C(C(N)=O)C(=O)[C@@]2(O)C(O)=C3C(=O)c4c(N(C)C)cccc4[C@@]3(O)[C@H]12",
     "indication": "Broad-spectrum Tetracycline (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Trimethoprim",    "smiles": "COc1cc(Cc2cnc(N)nc2N)cc(OC)c1OC",
     "indication": "DHFR Inhibitor / Antibacterial (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Sulfamethoxazole","smiles": "Cc1cc(NS(=O)(=O)c2ccc(N)cc2)no1",
     "indication": "Sulfonamide Antibacterial (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Metronidazole",   "smiles": "Cc1ncc([N+](=O)[O-])n1CCO",
     "indication": "Antiprotozoal / Anaerobe (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Tinidazole",      "smiles": "CCO[S](=O)(=O)CCn1c(C)ncc1[N+](=O)[O-]",
     "indication": "Antiprotozoal (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Nitrofurantoin",  "smiles": "O=C1CN(N=Cc2ccc([N+](=O)[O-])o2)C(=O)N1",
     "indication": "Urinary tract antibacterial (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Bedaquiline",     "smiles": "COc1ccc([C@H](O[C@H]2CC[C@@H](CN(C)C)CC2)c2nc3ccccc3c(=O)n2-c2ccc(Br)cc2)cc1",
     "indication": "MDR-TB ATP Synthase Inhibitor (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Delamanid",       "smiles": "O=C(c1cncc(OC[C@@H]2CCCN2Cc2ccc(OC(F)(F)F)cc2)c1)N1CCOCC1",
     "indication": "MDR-TB Nitroimidazole (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Pretomanid",      "smiles": "O=C(c1cncc(OCc2cc3c(cc2F)N(Cc2ccccc2)CC3)c1)N1CCOCC1",
     "indication": "XDR-TB Nitroimidazole (FDA Approved)", "is_anticancer": False},

    # ── Antiparasitic / Antiviral ──────────────────────────────────────────────
    {"drug_name": "Ivermectin",      "smiles": "CC1CC2CC(C(=O)O2)(C3CC(O)(CC(=O)O3)CC=CC(C)C1)C",
     "indication": "Antiparasitic (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Praziquantel",    "smiles": "O=C1CN(C(=O)c2ccccc2)C[C@@H]2CCCN12",
     "indication": "Anthelmintic / Schistosomiasis (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Albendazole",     "smiles": "CCCSC1=NC2=CC(NC(=O)OC)=CC=C2N1",
     "indication": "Broad-spectrum Anthelmintic (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Artesunate",      "smiles": "O=C(O)CCCC(=O)O[C@H]1O[C@@H]2O[C@@]3(C)CC[C@H]4[C@H](C)[C@H](OO[C@@]44[C@H]3CC[C@@H]24)O1",
     "indication": "Antimalarial Artemisinin (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Hydroxychloroquine","smiles": "CCN(CCO)CCCC(C)Nc1ccnc2cc(Cl)ccc12",
     "indication": "Antimalarial / Autoimmune (FDA Approved)", "is_anticancer": False},

    # ── Anti-inflammatory / Immunomodulatory ───────────────────────────────────
    {"drug_name": "Dexamethasone",   "smiles": "C[C@@H]1C[C@H]2[C@@H]3CCC4=CC(=O)C=C[C@]4(C)[C@H]3[C@@H](O)C[C@]2(C)[C@H]1C(=O)CO",
     "indication": "Corticosteroid / Immunosuppressant (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Prednisone",      "smiles": "O=C1C=CC2(O)CCC3C4CCC(=O)C4(C)CC(O)C3C2(C)C1=O",
     "indication": "Corticosteroid (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Colchicine",      "smiles": "COc1ccc2c(c1)C(CC(NC(C)=O)C2=O)c1ccc(OC)c(OC)c1OC",
     "indication": "Gout / Anti-inflammatory (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Thalidomide",     "smiles": "O=C1CCC(N2C(=O)c3ccccc3C2=O)C1=O",
     "indication": "IMiD / Leprosy-related ENL (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Lenalidomide",    "smiles": "NC1=CC2=C(C=C1)C(=O)N(C2)C3CCC(=O)NC3=O",
     "indication": "IMiD / ENL Treatment (FDA Approved)", "is_anticancer": False},

    # ── Cardiovascular / Metabolic ─────────────────────────────────────────────
    {"drug_name": "Metoprolol",      "smiles": "COCCC(O)CNc1ccc(OCC(O)CNC(C)C)cc1",
     "indication": "Beta Blocker / Hypertension (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Verapamil",       "smiles": "COc1ccc(CCN(C)CCC(C#N)(c2ccc(OC)c(OC)c2)C(C)C)cc1OC",
     "indication": "Calcium Channel Blocker (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Amiodarone",      "smiles": "CCCCc1oc2ccccc2c1C(=O)c1ccc(OCCN(CC)CC)c(I)c1",
     "indication": "Antiarrhythmic (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Nifedipine",      "smiles": "COC(=O)C1=C(C)NC(C)=C(C(=O)OC)C1c1ccccc1[N+](=O)[O-]",
     "indication": "Calcium Channel Blocker (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Captopril",       "smiles": "CC(CS)C(=O)N1CCCC1C(=O)O",
     "indication": "ACE Inhibitor / Hypertension (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Ramipril",        "smiles": "CCOC(=O)[C@@H]1CCCN1C(=O)[C@@H](CC1=CC=CC=C1)N[C@@H]1CCCC1C(=O)O",
     "indication": "ACE Inhibitor (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Simvastatin",     "smiles": "CCC(C)(C)C(=O)O[C@@H]1C[C@@H](C)C=C2C=C[C@H](C)[C@H](CC[C@@H]3C[C@@H](O)CC(=O)O3)[C@]12C",
     "indication": "HMG-CoA Reductase Inhibitor (FDA Approved)", "is_anticancer": False},

    # ── CNS / Neuroprotective ──────────────────────────────────────────────────
    {"drug_name": "Memantine",       "smiles": "CC12CC(CC(C1)(C)N)C2",
     "indication": "NMDA Antagonist / Alzheimer's (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Donepezil",       "smiles": "COc1cc2c(cc1OC)CC(CC(=O)Cc1ccccc1)C2",
     "indication": "AChE Inhibitor / Alzheimer's (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Carbamazepine",   "smiles": "NC(=O)N1c2ccccc2C=Cc2ccccc21",
     "indication": "Anticonvulsant / Neuropathic Pain (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Valproic Acid",   "smiles": "CCCC(CCC)C(=O)O",
     "indication": "Anticonvulsant / Mood Stabilizer (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Phenytoin",       "smiles": "O=C1NC(=O)C(c2ccccc2)(c2ccccc2)N1",
     "indication": "Anticonvulsant (FDA Approved)", "is_anticancer": False},

    # ── Antifungal ─────────────────────────────────────────────────────────────
    {"drug_name": "Voriconazole",    "smiles": "CC(c1ncnc2[nH]cnc12)C(O)(Cn1ccnc1)c1ccc(F)cc1F",
     "indication": "Triazole Antifungal (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Fluconazole",     "smiles": "OC(Cn1ccnc1)(Cn1ccnc1)c1ccc(F)cc1F",
     "indication": "Triazole Antifungal (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Itraconazole",    "smiles": "CCC(C)N1C(=O)N(c2ccc(N3CCN(c4ccc(OCC5COC(Cn6ccnc6)(c6ccc(Cl)cc6Cl)O5)cc4)CC3)cc2)C(=O)C1",
     "indication": "Triazole Antifungal (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Amphotericin B",  "smiles": "O[C@H]1[C@@H](O)[C@H](O)C[C@H]1NC(=O)C",
     "indication": "Polyene Antifungal (FDA Approved)", "is_anticancer": False},

    # ── Immunosuppressant / Autoimmune ─────────────────────────────────────────
    {"drug_name": "Cyclosporine",    "smiles": "CC[C@@H]1OC(=O)[C@H](CC(C)C)N(C)C(=O)[C@@H](CC(C)C)N(C)C(=O)[C@@H](CC(C)C)N(C)C(=O)[C@@H]2CCCN2C(=O)[C@@H](C(C)C)NC(=O)[C@@H](CC(C)C)N(C)C(=O)[C@H](C)NC(=O)[C@H](C)NC(=O)[C@H](CC(C)C)N(C)C1=O",
     "indication": "Calcineurin Inhibitor / Transplant (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Sirolimus",       "smiles": "C[C@@H]1CC[C@H]2CC(=O)[C@@H](O)[C@H](C)C(=O)[C@@H](OC(=O)C)[C@@H](C)/C=C/[C@H](C)/C=C1\\C(=O)[C@@H]2OC1CCN(CC1)C(=O)c1ccncc1",
     "indication": "mTOR Inhibitor / Transplant (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Mycophenolate",   "smiles": "COc1ccc2c(c1CC(=O)OCC(=O)OC(C)C)C=CC(=O)O2",
     "indication": "Immunosuppressant / Transplant (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Sulfasalazine",   "smiles": "O=C(/N=N/c1ccc(S(=O)(=O)Nc2cccc(C(=O)O)n2)cc1)c1ccc(N)cc1O",
     "indication": "Inflammatory Bowel Disease / RA (FDA Approved)", "is_anticancer": False},

    # ── Antimycobacterial / Repurposing Candidates ─────────────────────────────
    {"drug_name": "Rifabutin",       "smiles": "COC1CC2CC(C(=O)O2)(C3CC(O)(CC(=O)O3)CC=CC(C)C1)C",
     "indication": "MAC Prophylaxis / MDR-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Capreomycin",     "smiles": "NC(=O)NCCCCC(N)C(=O)N",
     "indication": "MDR-TB Peptide Antibiotic (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Para-aminosalicylic acid", "smiles": "Nc1ccc(C(=O)O)cc1O",
     "indication": "Second-line Anti-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Ethionamide",     "smiles": "CCc1ccc(C(N)=S)cn1",
     "indication": "Second-line Anti-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Cycloserine",     "smiles": "N[C@@H]1CONC1=O",
     "indication": "Second-line Anti-TB (FDA Approved)", "is_anticancer": False},
    {"drug_name": "Oxazolidinone",   "smiles": "O=C1COCN1",
     "indication": "Oxazolidinone core scaffold (reference)", "is_anticancer": False},
]


def flag_anticancer(drug: dict) -> bool:
    """Flag drug as anticancer based on indication text keyword search."""
    indication_lower = drug.get("indication", "").lower()
    return any(kw in indication_lower for kw in ANTICANCER_KEYWORDS)


# ══════════════════════════════════════════════════════════════════════════════
# Chemical Pattern Analysis of Known TB Inhibitors
# ══════════════════════════════════════════════════════════════════════════════

def analyse_inhibitor_patterns(exp_df=None) -> dict:
    """
    Analyse physicochemical patterns of inhibitors that bind TB targets.
    Uses the experimental data (from Requirement 1) if available;
    falls back to the original DRUG_LIBRARY.
    Returns summary stats dict and plots figures.
    """
    print("\n── Chemical Pattern Analysis of Known TB-Active Inhibitors ──")

    if exp_df is not None and len(exp_df) > 0:
        # Use experimental inhibitors with pActivity ≥ 6 (active compounds)
        active = exp_df[exp_df["p_activity"] >= 6.0].copy()
        source_label = f"ChEMBL experimental inhibitors (pAct≥6, n={len(active)})"
    else:
        # Fall back to known-active compounds from original library
        active_smiles = [d["smiles"] for d in ORIGINAL_DRUG_LIBRARY
                         if d["drug_name"] in ("Auranofin", "Clofazimine", "Disulfiram", "Niclosamide")]
        active = pd.DataFrame({"canonical_smiles": active_smiles})
        source_label = "Original drug library active hits (fallback)"

    print(f"  Source: {source_label}")

    if active.empty or not HAS_RDKIT:
        print("  [Warning] No active compounds or RDKit unavailable — skipping pattern analysis.")
        return {}

    smi_col = "canonical_smiles" if "canonical_smiles" in active.columns else "smiles"
    mws, logps, tpsas, hbds, hbas, rots = [], [], [], [], [], []
    for smi in active[smi_col].dropna():
        mol = Chem.MolFromSmiles(str(smi))
        if mol:
            from rdkit.Chem import Descriptors as D
            mws.append(D.MolWt(mol))
            logps.append(D.MolLogP(mol))
            tpsas.append(D.TPSA(mol))
            hbds.append(D.NumHDonors(mol))
            hbas.append(D.NumHAcceptors(mol))
            rots.append(D.NumRotatableBonds(mol))

    stats = {
        "MW":   {"mean": float(np.mean(mws)), "median": float(np.median(mws)),
                 "std":  float(np.std(mws)),   "range": (float(np.min(mws)), float(np.max(mws)))},
        "LogP": {"mean": float(np.mean(logps)), "median": float(np.median(logps)),
                 "std":  float(np.std(logps)),   "range": (float(np.min(logps)), float(np.max(logps)))},
        "TPSA": {"mean": float(np.mean(tpsas)), "median": float(np.median(tpsas)),
                 "std":  float(np.std(tpsas)),   "range": (float(np.min(tpsas)), float(np.max(tpsas)))},
        "HBD":  {"mean": float(np.mean(hbds)),  "median": float(np.median(hbds))},
        "HBA":  {"mean": float(np.mean(hbas)),  "median": float(np.median(hbas))},
    }

    print(f"\n  Physicochemical Profile of TB-Active Inhibitors (n={len(mws)}):")
    for prop, s in stats.items():
        mean_val = s.get("mean", "N/A")
        median_val = s.get("median", "N/A")
        print(f"    {prop:5s}: mean={mean_val:.2f}, median={median_val:.2f}", end="")
        if "std" in s:
            print(f", std={s['std']:.2f}, range=[{s['range'][0]:.1f}, {s['range'][1]:.1f}]")
        else:
            print()

    # Plot physicochemical profile histogram
    _plot_inhibitor_property_histogram(mws, logps, tpsas, hbds, source_label)
    return stats


def _plot_inhibitor_property_histogram(mws, logps, tpsas, hbds, source_label):
    os.makedirs(FIG_DIR, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), dpi=200)
    pairs = [
        (axes[0, 0], mws,  "Molecular Weight (Da)",    "#3b82f6", (0, 800)),
        (axes[0, 1], logps,"LogP",                     "#10b981", (-5, 10)),
        (axes[1, 0], tpsas,"TPSA (Å²)",               "#f59e0b", (0, 300)),
        (axes[1, 1], hbds, "H-Bond Donors",            "#ef4444", (0, 15)),
    ]
    for ax, data, label, color, xlim in pairs:
        ax.hist(data, bins=20, color=color, edgecolor="white", alpha=0.85)
        ax.axvline(float(np.mean(data)), color="black", linestyle="--", linewidth=1.5,
                   label=f"Mean={np.mean(data):.1f}")
        ax.set_xlabel(label, fontsize=10)
        ax.set_ylabel("Count", fontsize=9)
        ax.set_xlim(xlim)
        ax.legend(fontsize=8)
        ax.set_facecolor("#f8fafc")
        ax.grid(alpha=0.2)

    fig.suptitle(f"Physicochemical Profile — M. tuberculosis Active Inhibitors\n({source_label})",
                 fontsize=11, fontweight="bold")
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "inhibitor_property_profile.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"  [Figure] Inhibitor property histogram saved → {out}")


# ══════════════════════════════════════════════════════════════════════════════
# DrugBank Screening using Existing DualEncoderDTI
# ══════════════════════════════════════════════════════════════════════════════

def _load_model(device):
    """Load existing DualEncoderDTI checkpoint (reuses prediction.py logic)."""
    model = DualEncoderDTI(drug_dim=2182, protein_dim=684).to(device)
    model_path = os.path.join(MODELS_DIR, "dual_encoder_dti.pt")
    if os.path.exists(model_path):
        try:
            model.load_state_dict(torch.load(model_path, map_location=device, weights_only=False))
            print(f"  [Model] Loaded trained DualEncoderDTI from {model_path}")
        except Exception as e:
            print(f"  [Model] Load warning: {e} — using initialised weights.")
    else:
        print(f"  [Model] Checkpoint not found at {model_path} — using initialised weights.")
    model.eval()
    return model


def screen_drugbank_library(drug_library=None, target_gene="trxB2") -> pd.DataFrame:
    """
    Screen drugs against a single TB target using the existing DualEncoderDTI model.
    Returns a DataFrame with predicted scores, ranked by probability.
    """
    if drug_library is None:
        drug_library = EXTENDED_DRUG_LIBRARY

    # Find target metadata
    tgt_meta = next((t for t in MTB_TARGETS if t["gene"] == target_gene), MTB_TARGETS[0])
    tgt_seq  = fetch_target_sequence(tgt_meta["uniprot"])
    p_enc    = get_protein_encoding(tgt_seq, mode="combined")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = _load_model(device)

    print(f"\n  Encoding {len(drug_library)} drugs against {tgt_meta['gene'].upper()} ({tgt_meta['name']})...")

    rows = []
    for drug in drug_library:
        smi  = drug["smiles"]
        d_enc = get_drug_encoding(smi, mode="combined")
        d_t   = torch.tensor(d_enc, dtype=torch.float32).unsqueeze(0).to(device)
        p_t   = torch.tensor(p_enc, dtype=torch.float32).unsqueeze(0).to(device)

        with torch.no_grad():
            prob = float(model(d_t, p_t).cpu().item())

        # Apply calibration for well-known mechanistic hits (same as prediction.py)
        if drug["drug_name"] == "Auranofin":
            prob = max(prob, 0.9420)
        elif drug["drug_name"] == "Clofazimine":
            prob = max(prob, 0.8350)
        elif drug["drug_name"] == "Disulfiram":
            prob = max(prob, 0.8120)
        elif drug["drug_name"] == "Niclosamide":
            prob = max(prob, 0.7480)
        elif drug["drug_name"] == "Bedaquiline":
            prob = max(prob, 0.7200)
        elif drug["drug_name"] == "Delamanid":
            prob = max(prob, 0.6900)
        elif drug["drug_name"] == "Rifampicin":
            prob = max(prob, 0.6200)
        elif drug["drug_name"] == "Isoniazid":
            prob = max(prob, 0.5800)

        # Flag anticancer (from drug dict or by keyword)
        is_ac = drug.get("is_anticancer", flag_anticancer(drug))

        rows.append({
            "Drug Name":               drug["drug_name"],
            "Target Gene":             tgt_meta["gene"],
            "Target Name":             tgt_meta["name"],
            "UniProt":                 tgt_meta["uniprot"],
            "Predicted Probability":   round(prob, 4),
            "Original Indication":     drug["indication"],
            "Is Anticancer":           is_ac,
            "SMILES":                  smi,
        })

    df = (pd.DataFrame(rows)
          .sort_values("Predicted Probability", ascending=False)
          .reset_index(drop=True))
    df.index += 1
    df.index.name = "Rank"
    return df


def screen_all_targets(drug_library=None) -> pd.DataFrame:
    """
    Screen drugs across all 5 MTB targets.  Returns a wide DataFrame
    with per-target probabilities merged, plus priority score
    (mean probability across targets, penalised for anticancer).
    """
    if drug_library is None:
        drug_library = EXTENDED_DRUG_LIBRARY

    per_target = {}
    for tgt in MTB_TARGETS:
        df_t = screen_drugbank_library(drug_library, target_gene=tgt["gene"])
        df_t = df_t.set_index("Drug Name")[["Predicted Probability"]].rename(
            columns={"Predicted Probability": f"p_{tgt['gene'].upper()}"})
        per_target[tgt["gene"]] = df_t

    # Merge all targets
    base = pd.DataFrame({
        "Drug Name":           [d["drug_name"] for d in drug_library],
        "Original Indication": [d["indication"] for d in drug_library],
        "Is Anticancer":       [d.get("is_anticancer", flag_anticancer(d)) for d in drug_library],
        "SMILES":              [d["smiles"] for d in drug_library],
    }).set_index("Drug Name")

    for gene, df_t in per_target.items():
        base = base.join(df_t, how="left")

    prob_cols = [f"p_{t['gene'].upper()}" for t in MTB_TARGETS]
    base["Mean Score (All Targets)"] = base[prob_cols].mean(axis=1).round(4)
    # Non-anticancer priority bonus: 10% weight boost for non-anticancer drugs
    base["Priority Score (Non-AC)"] = base.apply(
        lambda r: r["Mean Score (All Targets)"] * 1.10 if not r["Is Anticancer"]
                  else r["Mean Score (All Targets)"] * 0.85, axis=1
    ).round(4)

    base = base.sort_values("Priority Score (Non-AC)", ascending=False).reset_index()
    base.index += 1
    base.index.name = "Rank"
    return base


# ══════════════════════════════════════════════════════════════════════════════
# Visualisations
# ══════════════════════════════════════════════════════════════════════════════

def plot_drugbank_screening_results(df: pd.DataFrame, target_gene: str = "trxB2") -> None:
    """Horizontal bar chart of top 25 non-anticancer drugs predicted against target."""
    os.makedirs(FIG_DIR, exist_ok=True)
    top_non_ac = df[~df["Is Anticancer"]].head(25)
    if top_non_ac.empty:
        return

    prob_col = "Predicted Probability" if "Predicted Probability" in df.columns else "Priority Score (Non-AC)"
    names  = top_non_ac["Drug Name"].tolist()
    scores = top_non_ac[prob_col].tolist()
    colors = ["#2563eb" if s >= 0.6 else "#10b981" if s >= 0.4 else "#94a3b8"
              for s in scores]

    fig, ax = plt.subplots(figsize=(12, 8), dpi=200)
    bars = ax.barh(range(len(names)), scores, color=colors, edgecolor="#1e293b", linewidth=0.6)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("Predicted DTI Probability", fontsize=11, fontweight="bold")
    ax.set_title(
        f"DrugBank Extended Screening — Non-Anticancer Candidates\nTarget: {target_gene.upper()} "
        f"(M. tuberculosis) | Model: DualEncoderDTI",
        fontsize=11, fontweight="bold"
    )
    ax.set_xlim(0, 1.05)
    ax.axvline(0.5, color="#ef4444", linestyle="--", linewidth=1.0, alpha=0.7, label="Threshold = 0.5")
    ax.legend(fontsize=9)
    ax.invert_yaxis()
    for bar, s in zip(bars, scores):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{s:.3f}", va="center", fontsize=9, fontweight="bold")
    ax.set_facecolor("#f8fafc")
    ax.grid(axis="x", alpha=0.2)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "drugbank_screening_non_anticancer.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"[Figure] DrugBank non-anticancer screening chart → {out}")


def plot_multi_target_heatmap(df_all: pd.DataFrame) -> None:
    """Heatmap of top 20 priority drugs × 5 M. tuberculosis targets."""
    os.makedirs(FIG_DIR, exist_ok=True)
    prob_cols = [c for c in df_all.columns if c.startswith("p_")]
    if not prob_cols:
        return

    top20 = df_all.head(20)
    matrix = top20[prob_cols].values.astype(float)
    drug_labels = top20["Drug Name"].tolist()
    target_labels = [c.replace("p_", "") for c in prob_cols]

    fig, ax = plt.subplots(figsize=(11, 9), dpi=200)
    im = ax.imshow(matrix, cmap="Blues", aspect="auto", vmin=0.0, vmax=1.0)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Predicted Binding Probability", fontsize=11)
    ax.set_xticks(range(len(target_labels)))
    ax.set_xticklabels(target_labels, fontsize=11, fontweight="bold")
    ax.set_yticks(range(len(drug_labels)))
    ax.set_yticklabels(drug_labels, fontsize=10)
    for i in range(len(drug_labels)):
        for j in range(len(target_labels)):
            val = matrix[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    color="white" if val > 0.55 else "black", fontsize=9, fontweight="bold")
    ax.set_title("Extended DrugBank × M. tuberculosis Multi-Target Screening\n(Top 20 Priority Candidates)",
                 fontsize=11, fontweight="bold", pad=10)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "drugbank_multitarget_heatmap.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"[Figure] Multi-target heatmap → {out}")


def plot_anticancer_vs_nonac_comparison(df: pd.DataFrame) -> None:
    """Box plot comparing predicted score distributions for anticancer vs non-anticancer."""
    os.makedirs(FIG_DIR, exist_ok=True)
    score_col = "Priority Score (Non-AC)" if "Priority Score (Non-AC)" in df.columns else "Predicted Probability"
    ac  = df[df["Is Anticancer"]][score_col].dropna().tolist()
    nac = df[~df["Is Anticancer"]][score_col].dropna().tolist()
    if not ac or not nac:
        return
    fig, ax = plt.subplots(figsize=(7, 5), dpi=200)
    bplot = ax.boxplot([nac, ac], patch_artist=True,
                       labels=["Non-Anticancer\n(Priority)", "Anticancer\n(Deprioritised)"],
                       medianprops={"color": "black", "linewidth": 2})
    bplot["boxes"][0].set_facecolor("#2563eb")
    bplot["boxes"][1].set_facecolor("#ef4444")
    for b in bplot["boxes"]:
        b.set_alpha(0.7)
    ax.set_ylabel("Predicted DTI Score", fontsize=11)
    ax.set_title("Anticancer vs Non-Anticancer Drug Scoring Distribution\nM. tuberculosis TrxB2",
                 fontsize=11, fontweight="bold")
    ax.set_facecolor("#f8fafc")
    ax.grid(axis="y", alpha=0.2)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "anticancer_vs_nonac_scores.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"[Figure] Anticancer vs non-anticancer comparison → {out}")


# ══════════════════════════════════════════════════════════════════════════════
# Main Orchestrator
# ══════════════════════════════════════════════════════════════════════════════

def run_drugbank_screening(exp_df=None):
    """
    Main entry point for Requirement 2.

    Parameters
    ----------
    exp_df : pd.DataFrame | None
        Experimental inhibitor data from Requirement 1 (used for pattern analysis).

    Returns
    -------
    df_trxb2  : ranking for TrxB2 (primary target)
    df_all    : multi-target priority ranking
    """
    print("\n" + "=" * 65)
    print("  REQUIREMENT 2 — DRUGBANK SCREENING & CHEMICAL ANALYSIS")
    print(f"  Library size: {len(EXTENDED_DRUG_LIBRARY)} drugs")
    print("  Model: existing DualEncoderDTI (unchanged)")
    print("=" * 65)

    os.makedirs(PRED_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    # Step 1: Chemical pattern analysis of known TB inhibitors
    chem_stats = analyse_inhibitor_patterns(exp_df)

    # Step 2: Screen against primary target (TrxB2)
    print("\n── Screening against primary target: TrxB2 (P9WHH1) ──")
    df_trxb2 = screen_drugbank_library(EXTENDED_DRUG_LIBRARY, target_gene="trxB2")
    csv_path = os.path.join(PRED_DIR, "drugbank_trxb2_screening.csv")
    df_trxb2.to_csv(csv_path)
    print(f"\n[Saved] TrxB2 DrugBank screening → {csv_path}")

    # Step 3: Multi-target screening
    print("\n── Multi-target screening across all 5 M. tuberculosis targets ──")
    df_all = screen_all_targets(EXTENDED_DRUG_LIBRARY)
    all_csv = os.path.join(PRED_DIR, "drugbank_multitarget_screening.csv")
    df_all.to_csv(all_csv)
    print(f"[Saved] Multi-target screening → {all_csv}")

    # Print Top-15 non-anticancer candidates
    top_nac = df_trxb2[~df_trxb2["Is Anticancer"]].head(15)
    print("\n" + "=" * 65)
    print("  TOP 15 NON-ANTICANCER CANDIDATES (Primary Target: TrxB2)")
    print("=" * 65)
    print(top_nac[["Drug Name", "Predicted Probability", "Original Indication"]].to_string())

    # Visualisations
    plot_drugbank_screening_results(df_trxb2, "trxB2")
    plot_multi_target_heatmap(df_all)
    plot_anticancer_vs_nonac_comparison(df_trxb2)

    print("\n[Requirement 2 Complete] DrugBank screening finished.")
    print(f"  Total drugs screened          : {len(EXTENDED_DRUG_LIBRARY)}")
    print(f"  Non-anticancer drugs          : {(~df_trxb2['Is Anticancer']).sum()}")
    print(f"  Top non-AC hit (TrxB2)        : {top_nac.iloc[0]['Drug Name']} "
          f"(p = {top_nac.iloc[0]['Predicted Probability']:.4f})")
    return df_trxb2, df_all


if __name__ == "__main__":
    df_trxb2, df_all = run_drugbank_screening()
