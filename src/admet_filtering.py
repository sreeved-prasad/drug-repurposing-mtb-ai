"""
Stage 3 Module 1: ADMET & Drug-Likeness Filtering
===================================================
Comprehensive drugability assessment combining:
  - Lipinski Rule-of-5 (MW, LogP, HBD, HBA)
  - Veber Rules (Rotatable Bonds, TPSA)
  - PAINS Substructure Filter (Pan-Assay Interference)
  - Predicted ADMET Property Scoring (Absorption, Metabolism, Toxicity)
  - Composite Drugability Index (weighted 0-1 score)

Integrates with the drug repurposing candidate library to rank compounds
by drugability alongside binding affinity predictions.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, FilterCatalog
from rdkit.Chem.FilterCatalog import FilterCatalogParams

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
FIG_DIR = os.path.join(RESULTS_DIR, "figures")
PRED_DIR = os.path.join(RESULTS_DIR, "predictions")

# ─────────────────────────────────────────────────────────────────────
# PAINS Filter Catalog (singleton)
# ─────────────────────────────────────────────────────────────────────
_PAINS_CATALOG = None

def _get_pains_catalog():
    """Initialize PAINS A/B/C filter catalog (singleton)."""
    global _PAINS_CATALOG
    if _PAINS_CATALOG is None:
        params = FilterCatalogParams()
        params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_A)
        params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_B)
        params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_C)
        _PAINS_CATALOG = FilterCatalog.FilterCatalog(params)
    return _PAINS_CATALOG

# ─────────────────────────────────────────────────────────────────────
# Toxicophore / Reactive Metabolite SMARTS Patterns
# ─────────────────────────────────────────────────────────────────────
HEPATOTOX_SMARTS = [
    "[N;X2]=O",                         # Nitroso
    "[N;X3](=O)=O",                     # Nitro group
    "[#6]=[#6]-[#6]=O",                 # Michael acceptor (α,β-unsaturated carbonyl)
    "[F,Cl,Br,I]-[CX4]",               # Alkyl halide
    "[SX2]C=O",                         # Thioester (reactive metabolite)
    "[#6]-[CH2]-[Cl,Br,I]",            # Activated halide
]

AMES_ALERT_SMARTS = [
    "[N;X3](=O)=O",                     # Nitro aromatic
    "[NH2]-[c]",                        # Primary aromatic amine
    "[c]-[N]=[N]-[c]",                  # Azo dye
    "[#6]1:[#6]:[#6]:[#6]:[#6]:[#6]:1-[N;X3](=O)=O",  # Nitroaromatic ring
]

HERG_ALERT_SMARTS = [
    "[NX3;!$(NC=O)]([CH2][CH2])[CH2][CH2]",  # Basic tertiary amine with long chain
    "c1ccc2c(c1)CCN2",                       # Indoline / dihydroquinoline
]

CYP_SUBSTRATE_SMARTS = [
    "[c]1[c][c][c][c][c]1-[OX2H]",     # Phenol (CYP2D6 substrate indicator)
    "[NX3H2]-c",                        # Primary aromatic amine (CYP1A2)
    "[c]1[c][c]([c][c][c]1)-[NX3]",     # Aniline derivative (CYP2D6/3A4)
]


# ═════════════════════════════════════════════════════════════════════
# Core ADMET Property Calculators
# ═════════════════════════════════════════════════════════════════════

def compute_lipinski_properties(mol):
    """
    Compute Lipinski Rule-of-5 properties.
    Returns dict with individual values and overall pass/fail.
    """
    if mol is None:
        return {"MW": 0, "LogP": 0, "HBD": 0, "HBA": 0, "Lipinski_Pass": False, "Lipinski_Violations": 4}

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)

    violations = 0
    if mw > 500: violations += 1
    if logp > 5: violations += 1
    if hbd > 5: violations += 1
    if hba > 10: violations += 1

    return {
        "MW": round(mw, 2),
        "LogP": round(logp, 2),
        "HBD": int(hbd),
        "HBA": int(hba),
        "Lipinski_Pass": violations <= 1,
        "Lipinski_Violations": violations
    }


def compute_veber_properties(mol):
    """
    Compute Veber oral bioavailability rules.
    Rotatable bonds ≤ 10, TPSA ≤ 140 Å².
    """
    if mol is None:
        return {"RotBonds": 0, "TPSA": 0, "Veber_Pass": False}

    rot = Descriptors.NumRotatableBonds(mol)
    tpsa = Descriptors.TPSA(mol)

    return {
        "RotBonds": int(rot),
        "TPSA": round(tpsa, 2),
        "Veber_Pass": rot <= 10 and tpsa <= 140
    }


def check_pains(mol):
    """
    Screen molecule against PAINS A/B/C filter catalogs.
    Returns True if PAINS-free (clean), False if PAINS alert detected.
    """
    if mol is None:
        return {"PAINS_Free": False, "PAINS_Alerts": ["Invalid molecule"]}

    catalog = _get_pains_catalog()
    entry = catalog.GetFirstMatch(mol)

    if entry is None:
        return {"PAINS_Free": True, "PAINS_Alerts": []}
    else:
        alerts = []
        for match in catalog.GetMatches(mol):
            alerts.append(match.GetDescription())
        return {"PAINS_Free": False, "PAINS_Alerts": alerts[:5]}


def predict_gi_absorption(mw, logp, tpsa, hbd):
    """
    Predict GI absorption using the Egan/Veber absorption model.
    High absorption: TPSA ≤ 131 Å² AND LogP in [-0.4, 5.6].
    """
    if tpsa <= 131 and -0.4 <= logp <= 5.6 and mw <= 600:
        score = 1.0 - (tpsa / 200.0) * 0.3 - max(0, logp - 3) * 0.1
        return {"GI_Absorption": "High", "GI_Score": round(min(max(score, 0.3), 1.0), 3)}
    else:
        score = 0.3 - (max(0, tpsa - 131) / 100.0) * 0.2
        return {"GI_Absorption": "Low", "GI_Score": round(max(score, 0.05), 3)}


def predict_bbb_permeability(mw, logp, tpsa, hbd):
    """
    Predict BBB permeability using simplified Clark model.
    BBB permeable: MW ≤ 450, TPSA ≤ 90, LogP in [1, 5], HBD ≤ 3.
    """
    if mw <= 450 and tpsa <= 90 and 1 <= logp <= 5 and hbd <= 3:
        return {"BBB_Permeable": True, "BBB_Score": round(0.8 + (3.0 - abs(logp - 3.0)) * 0.05, 3)}
    else:
        penalty = 0
        if mw > 450: penalty += 0.2
        if tpsa > 90: penalty += 0.25
        if logp < 1 or logp > 5: penalty += 0.15
        if hbd > 3: penalty += 0.15
        return {"BBB_Permeable": False, "BBB_Score": round(max(0.05, 0.6 - penalty), 3)}


def predict_cyp_metabolism(mol):
    """
    Predict CYP450 metabolism risk based on structural alerts.
    Flags potential CYP3A4/2D6/1A2 substrate motifs.
    """
    if mol is None:
        return {"CYP_Risk": "Unknown", "CYP_Score": 0.5, "CYP_Alerts": []}

    alerts = []
    for i, smarts in enumerate(CYP_SUBSTRATE_SMARTS):
        patt = Chem.MolFromSmarts(smarts)
        if patt is not None and mol.HasSubstructMatch(patt):
            labels = ["CYP2D6_Phenol", "CYP1A2_AromaticAmine", "CYP2D6_3A4_Aniline"]
            alerts.append(labels[i] if i < len(labels) else f"CYP_Alert_{i}")

    n_alerts = len(alerts)
    if n_alerts == 0:
        return {"CYP_Risk": "Low", "CYP_Score": 0.9, "CYP_Alerts": []}
    elif n_alerts == 1:
        return {"CYP_Risk": "Moderate", "CYP_Score": 0.6, "CYP_Alerts": alerts}
    else:
        return {"CYP_Risk": "High", "CYP_Score": 0.3, "CYP_Alerts": alerts}


def predict_herg_liability(mol, logp):
    """
    Predict hERG channel inhibition liability (cardiotoxicity risk).
    """
    if mol is None:
        return {"hERG_Risk": "Unknown", "hERG_Score": 0.5}

    has_herg_motif = False
    for smarts in HERG_ALERT_SMARTS:
        patt = Chem.MolFromSmarts(smarts)
        if patt is not None and mol.HasSubstructMatch(patt):
            has_herg_motif = True
            break

    # High LogP + basic nitrogen = higher hERG risk
    mw = Descriptors.MolWt(mol)
    if has_herg_motif and logp > 3.5:
        return {"hERG_Risk": "High", "hERG_Score": 0.2}
    elif logp > 4.5 or has_herg_motif:
        return {"hERG_Risk": "Moderate", "hERG_Score": 0.5}
    else:
        return {"hERG_Risk": "Low", "hERG_Score": 0.85}


def predict_hepatotoxicity(mol):
    """
    Predict hepatotoxicity risk based on reactive metabolite structural alerts.
    """
    if mol is None:
        return {"Hepatotox_Risk": "Unknown", "Hepatotox_Score": 0.5, "Hepatotox_Alerts": []}

    alerts = []
    for smarts in HEPATOTOX_SMARTS:
        patt = Chem.MolFromSmarts(smarts)
        if patt is not None and mol.HasSubstructMatch(patt):
            alerts.append(smarts)

    n = len(alerts)
    if n == 0:
        return {"Hepatotox_Risk": "Low", "Hepatotox_Score": 0.9, "Hepatotox_Alerts": []}
    elif n <= 2:
        return {"Hepatotox_Risk": "Moderate", "Hepatotox_Score": 0.5, "Hepatotox_Alerts": alerts}
    else:
        return {"Hepatotox_Risk": "High", "Hepatotox_Score": 0.15, "Hepatotox_Alerts": alerts}


def predict_ames_mutagenicity(mol):
    """
    Predict Ames test mutagenicity risk based on known mutagenic substructure alerts.
    """
    if mol is None:
        return {"Ames_Risk": "Unknown", "Ames_Score": 0.5}

    for smarts in AMES_ALERT_SMARTS:
        patt = Chem.MolFromSmarts(smarts)
        if patt is not None and mol.HasSubstructMatch(patt):
            return {"Ames_Risk": "Positive (Alert)", "Ames_Score": 0.2}

    return {"Ames_Risk": "Negative", "Ames_Score": 0.9}


# ═════════════════════════════════════════════════════════════════════
# Composite ADMET Assessment
# ═════════════════════════════════════════════════════════════════════

def compute_full_admet_profile(smiles, drug_name="Unknown"):
    """
    Compute complete ADMET and drug-likeness profile for a single molecule.
    Returns a flat dictionary with all properties and composite drugability score.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        # Try lenient parsing
        mol = Chem.MolFromSmiles(smiles, sanitize=False)
        if mol is not None:
            try:
                mol.UpdatePropertyCache(strict=False)
            except Exception:
                mol = None

    profile = {"Drug_Name": drug_name, "SMILES": smiles}

    # 1. Lipinski
    lip = compute_lipinski_properties(mol)
    profile.update(lip)

    # 2. Veber
    veb = compute_veber_properties(mol)
    profile.update(veb)

    # 3. PAINS
    pains = check_pains(mol)
    profile["PAINS_Free"] = pains["PAINS_Free"]
    profile["PAINS_Alerts"] = "; ".join(pains["PAINS_Alerts"]) if pains["PAINS_Alerts"] else "None"

    # 4. Predicted ADMET
    gi = predict_gi_absorption(lip["MW"], lip["LogP"], veb["TPSA"], lip["HBD"])
    profile.update(gi)

    bbb = predict_bbb_permeability(lip["MW"], lip["LogP"], veb["TPSA"], lip["HBD"])
    profile.update(bbb)

    cyp = predict_cyp_metabolism(mol)
    profile["CYP_Risk"] = cyp["CYP_Risk"]
    profile["CYP_Score"] = cyp["CYP_Score"]

    herg = predict_herg_liability(mol, lip["LogP"])
    profile.update(herg)

    hepat = predict_hepatotoxicity(mol)
    profile["Hepatotox_Risk"] = hepat["Hepatotox_Risk"]
    profile["Hepatotox_Score"] = hepat["Hepatotox_Score"]

    ames = predict_ames_mutagenicity(mol)
    profile.update(ames)

    # 5. Composite Drugability Score (weighted average)
    lipinski_score = 1.0 if lip["Lipinski_Pass"] else max(0, 1.0 - lip["Lipinski_Violations"] * 0.25)
    veber_score = 1.0 if veb["Veber_Pass"] else 0.5
    pains_score = 1.0 if pains["PAINS_Free"] else 0.2

    composite = (
        0.20 * lipinski_score +
        0.10 * veber_score +
        0.10 * pains_score +
        0.15 * gi["GI_Score"] +
        0.05 * bbb["BBB_Score"] +
        0.10 * cyp["CYP_Score"] +
        0.10 * herg["hERG_Score"] +
        0.10 * hepat["Hepatotox_Score"] +
        0.10 * ames["Ames_Score"]
    )
    profile["Drugability_Score"] = round(composite, 4)

    return profile


def run_admet_screening(drug_library=None):
    """
    Run full ADMET screening across the drug repurposing candidate library.
    Returns a ranked DataFrame sorted by Drugability Score.
    """
    if drug_library is None:
        from polypharmacology import DRUG_LIBRARY
        drug_library = DRUG_LIBRARY

    print("\n=======================================================")
    print("      STAGE 3: ADMET & DRUG-LIKENESS SCREENING")
    print("      Lipinski | Veber | PAINS | ADMET Property Scoring")
    print("=======================================================\n")

    profiles = []
    for drug in drug_library:
        name = drug.get("drug_name", "Unknown")
        smiles = drug.get("smiles", "")
        print(f"  Screening: {name}...")
        profile = compute_full_admet_profile(smiles, drug_name=name)
        profile["Original_Indication"] = drug.get("indication", "Unknown")
        profiles.append(profile)

    df = pd.DataFrame(profiles)
    df = df.sort_values(by="Drugability_Score", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"

    # Save results
    os.makedirs(PRED_DIR, exist_ok=True)
    csv_path = os.path.join(PRED_DIR, "admet_druglikeness_profiles.csv")
    df.to_csv(csv_path)

    # Display summary
    display_cols = [
        "Drug_Name", "Drugability_Score", "Lipinski_Pass", "Veber_Pass",
        "PAINS_Free", "GI_Absorption", "CYP_Risk", "hERG_Risk",
        "Hepatotox_Risk", "Ames_Risk"
    ]
    print("\n================ ADMET & DRUG-LIKENESS RANKINGS ================\n")
    print(df[display_cols].to_string())
    print(f"\n[ADMET Screening Complete] Profiles saved to: {csv_path}")

    # Generate Visualizations
    generate_admet_figures(df)

    return df


# ═════════════════════════════════════════════════════════════════════
# Visualization
# ═════════════════════════════════════════════════════════════════════

def generate_admet_figures(df):
    """Generate ADMET radar charts and drugability comparison bar chart."""
    os.makedirs(FIG_DIR, exist_ok=True)

    # 1. Drugability Score Comparison Bar Chart
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    drug_names = df["Drug_Name"].tolist()
    scores = df["Drugability_Score"].tolist()

    colors = []
    for s in scores:
        if s >= 0.75:
            colors.append("#10b981")
        elif s >= 0.55:
            colors.append("#f59e0b")
        else:
            colors.append("#ef4444")

    bars = ax.barh(range(len(drug_names)), scores, color=colors, edgecolor="#1e293b", linewidth=0.8)
    ax.set_yticks(range(len(drug_names)))
    ax.set_yticklabels(drug_names, fontsize=11, fontweight="bold")
    ax.set_xlabel("Composite Drugability Score", fontsize=12, fontweight="bold")
    ax.set_title("ADMET & Drug-Likeness Composite Ranking", fontsize=14, fontweight="bold")
    ax.set_xlim(0, 1.05)
    ax.axvline(x=0.75, color="#10b981", linestyle="--", alpha=0.5, label="High Drugability (≥0.75)")
    ax.axvline(x=0.55, color="#f59e0b", linestyle="--", alpha=0.5, label="Moderate (≥0.55)")
    ax.legend(loc="lower right", fontsize=9)
    ax.invert_yaxis()

    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f"{score:.3f}", va="center", fontsize=10, fontweight="bold")

    ax.set_facecolor("#f8fafc")
    fig.patch.set_facecolor("#ffffff")
    ax.grid(axis="x", alpha=0.2)
    plt.tight_layout()

    bar_path = os.path.join(FIG_DIR, "admet_drugability_ranking.png")
    plt.savefig(bar_path)
    plt.close()
    print(f"[Figure Generated] Drugability ranking chart saved to: {bar_path}")

    # 2. ADMET Radar Charts for top candidates
    categories = ["GI Absorption", "BBB Permeability", "CYP Safety",
                   "hERG Safety", "Hepatotox Safety", "Ames Safety"]
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True), dpi=300)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11, fontweight="bold", color="#475569")
    ax.set_rlabel_position(0)
    ax.set_yticks([0.25, 0.50, 0.75, 1.0])
    ax.set_yticklabels(["0.25", "0.50", "0.75", "1.00"], color="grey", size=9)
    ax.set_ylim(0, 1.05)

    palette = ["#e11d48", "#2563eb", "#16a34a", "#d97706", "#8b5cf6", "#06b6d4"]
    top_drugs = df.head(6)

    for idx, (_, row) in enumerate(top_drugs.iterrows()):
        values = [
            row.get("GI_Score", 0.5),
            row.get("BBB_Score", 0.5),
            row.get("CYP_Score", 0.5),
            row.get("hERG_Score", 0.5),
            row.get("Hepatotox_Score", 0.5),
            row.get("Ames_Score", 0.5),
        ]
        values += values[:1]
        c = palette[idx % len(palette)]
        ax.plot(angles, values, linewidth=2, linestyle="solid",
                label=row["Drug_Name"], color=c)
        ax.fill(angles, values, color=c, alpha=0.08)

    ax.set_title("ADMET Safety Profile Radar\n(Higher = Safer)",
                 fontsize=14, fontweight="bold", y=1.08, color="#1e293b")
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=10, frameon=True)
    plt.tight_layout()

    radar_path = os.path.join(FIG_DIR, "admet_safety_radar.png")
    plt.savefig(radar_path, bbox_inches="tight")
    plt.close()
    print(f"[Figure Generated] ADMET safety radar saved to: {radar_path}")


# ═════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    df = run_admet_screening()
    print("\n[Stage 3 ADMET Module] All ADMET profiles computed and visualizations generated.")
