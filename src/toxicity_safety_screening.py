"""
NEW MODULE — Requirement 3: Toxicity & Safety Screening of Non-Anticancer Candidates
======================================================================================
Evaluates the shortlisted non-anticancer drug candidates from Requirement 2 for
toxicity and safety using ADMET predictions and structural alerts.  Integrates with
the existing admet_filtering.py module and extends it with:

  1. Extended toxicity alert panels (nephrotoxicity, reproductive toxicity, skin
     sensitisation, QTc prolongation alerts)
  2. ProTox-style oral rat LD50 estimation
  3. Comparison table: binding prediction vs safety profile vs experimental data
  4. Final tiered ranking: Safe-Prioritised → Caution → Flagged (Unsafe)
  5. Full visualisations: radar chart, safety heatmap, final ranked table figure

REUSED COMPONENTS:
  - admet_filtering.py: ALL existing predictors reused unchanged
      compute_full_admet_profile(), run_admet_screening(),
      predict_hepatotoxicity(), predict_herg_liability(),
      predict_ames_mutagenicity(), check_pains()
  - polypharmacology.py: DRUG_LIBRARY (original baseline)
  - drugbank_screening.py: EXTENDED_DRUG_LIBRARY, ANTICANCER_KEYWORDS

NEWLY IMPLEMENTED:
  - predict_nephrotoxicity(): renal tubule alert SMARTS patterns
  - predict_reproductive_toxicity(): teratogenicity structural alerts
  - predict_skin_sensitisation(): Michael acceptor / electrophilic alerts
  - estimate_oral_ld50_class(): ProTox-inspired MW/LogP/TPSA rule estimation
  - compute_extended_safety_profile(): full composite safety score (10 endpoints)
  - run_toxicity_safety_screening(): main orchestrator
  - generate_safety_comparison_table(): CSV comparing binding + safety
  - generate_safety_heatmap(): 2D heatmap of safety endpoints × drugs
  - generate_final_tier_ranking(): tiered output with Pass/Caution/Fail labels
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Reuse existing modules ────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# Import ALL existing ADMET functions (Requirement: reuse existing modules)
from admet_filtering import (
    compute_full_admet_profile,
    compute_lipinski_properties,
    compute_veber_properties,
    check_pains,
    predict_gi_absorption,
    predict_bbb_permeability,
    predict_cyp_metabolism,
    predict_herg_liability,
    predict_hepatotoxicity,
    predict_ames_mutagenicity,
    _get_pains_catalog,
    HEPATOTOX_SMARTS,
    AMES_ALERT_SMARTS,
    HERG_ALERT_SMARTS,
)

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT_DIR    = os.path.dirname(os.path.dirname(__file__))
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
PRED_DIR    = os.path.join(RESULTS_DIR, "predictions")
FIG_DIR     = os.path.join(RESULTS_DIR, "figures")
SAFE_DIR    = os.path.join(RESULTS_DIR, "safety")

# ══════════════════════════════════════════════════════════════════════════════
# NEW Toxicity Alert SMARTS (not in existing admet_filtering.py)
# ══════════════════════════════════════════════════════════════════════════════

NEPHROTOX_SMARTS = [
    "[SX2]-[SX2]",                           # Disulfide (thiol reactive metabolite)
    "[NX3][CX3](=O)[NX3]",                   # Urea (renal accumulation risk)
    "[#6]~[#6](=O)~[Br,I]",                  # Alpha-haloketone
    "c1ccc(NC(=O)c2ccccc2)cc1",              # Acetaminophen-like (NAPQI precursor)
    "[OX2][CX4][OX2]",                        # Glycol ether (nephrotoxic metabolite)
]

REPRO_TOX_SMARTS = [
    "[NX3](=O)=O",                            # Nitro group (reproductive hazard)
    "C1=CC=CC=C1-[Cl,Br,I]",                 # Halogenated aromatics
    "O=C1NC(=O)c2ccccc21",                   # Thalidomide-like imide
    "[CH2]=[CH2]",                             # Simple alkene (potential mutagen)
    "[SX2][NX3]",                             # Sulfonamide-N reactive
]

SKIN_SENSITISATION_SMARTS = [
    "[CX3](=O)[Cl,Br]",                       # Acyl halide
    "[CX3](=O)-[OX2]-[CX3](=O)",             # Anhydride
    "[NX2]=[CX3]",                             # Isocyanate/iminium
    "[#6]=C-C=O",                              # Michael acceptor (alpha-beta unsat)
    "[OX2][CX4][Cl,Br]",                      # Alkyl halide ether
]

QTC_PROLONGATION_SMARTS = [
    "c1ccc2c(c1)N=C(N2)N",                   # Aminobenzimidazole (hERG-related)
    "[NX3]CCCC[NX3]",                          # Bis-amine chain (antipsychotic-like)
    "c1ccncc1",                                # Pyridine-containing (CYP/hERG risk)
    "[nX3]1cccn1",                             # Imidazole ring
]


# ══════════════════════════════════════════════════════════════════════════════
# NEW Toxicity Predictors (extending admet_filtering.py)
# ══════════════════════════════════════════════════════════════════════════════

def predict_nephrotoxicity(mol) -> dict:
    """
    Predict nephrotoxicity risk based on renal toxic structural alerts.
    NEW — not present in existing admet_filtering.py.
    """
    if mol is None:
        return {"Nephrotox_Risk": "Unknown", "Nephrotox_Score": 0.5}
    alerts = []
    for smarts in NEPHROTOX_SMARTS:
        patt = Chem.MolFromSmarts(smarts)
        if patt and mol.HasSubstructMatch(patt):
            alerts.append(smarts)
    n = len(alerts)
    if n == 0:
        return {"Nephrotox_Risk": "Low", "Nephrotox_Score": 0.90}
    elif n == 1:
        return {"Nephrotox_Risk": "Moderate", "Nephrotox_Score": 0.55}
    else:
        return {"Nephrotox_Risk": "High", "Nephrotox_Score": 0.20}


def predict_reproductive_toxicity(mol) -> dict:
    """
    Predict reproductive / developmental toxicity based on structural alerts.
    NEW — not present in existing admet_filtering.py.
    """
    if mol is None:
        return {"ReproTox_Risk": "Unknown", "ReproTox_Score": 0.5}
    alerts = []
    for smarts in REPRO_TOX_SMARTS:
        patt = Chem.MolFromSmarts(smarts)
        if patt and mol.HasSubstructMatch(patt):
            alerts.append(smarts)
    n = len(alerts)
    if n == 0:
        return {"ReproTox_Risk": "Low", "ReproTox_Score": 0.90}
    elif n == 1:
        return {"ReproTox_Risk": "Moderate", "ReproTox_Score": 0.55}
    else:
        return {"ReproTox_Risk": "High", "ReproTox_Score": 0.20}


def predict_skin_sensitisation(mol) -> dict:
    """
    Predict skin sensitisation potential based on electrophilic reactivity alerts.
    NEW — not present in existing admet_filtering.py.
    """
    if mol is None:
        return {"SkinSens_Risk": "Unknown", "SkinSens_Score": 0.5}
    alerts = []
    for smarts in SKIN_SENSITISATION_SMARTS:
        patt = Chem.MolFromSmarts(smarts)
        if patt and mol.HasSubstructMatch(patt):
            alerts.append(smarts)
    n = len(alerts)
    if n == 0:
        return {"SkinSens_Risk": "Low", "SkinSens_Score": 0.90}
    elif n == 1:
        return {"SkinSens_Risk": "Moderate", "SkinSens_Score": 0.60}
    else:
        return {"SkinSens_Risk": "High", "SkinSens_Score": 0.25}


def predict_qtc_prolongation(mol, logp: float) -> dict:
    """
    Predict QTc prolongation risk (cardiac arrhythmia via hERG-adjacent mechanisms).
    Extends hERG prediction in admet_filtering.py with additional QTc-specific alerts.
    NEW — not present in existing admet_filtering.py.
    """
    if mol is None:
        return {"QTc_Risk": "Unknown", "QTc_Score": 0.5}
    alert_count = 0
    for smarts in QTC_PROLONGATION_SMARTS:
        patt = Chem.MolFromSmarts(smarts)
        if patt and mol.HasSubstructMatch(patt):
            alert_count += 1

    # High LogP + aromatic ring system = elevated QTc risk
    ring_info = mol.GetRingInfo()
    n_aromatic = sum(1 for ring in ring_info.AtomRings()
                     if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring))

    if alert_count >= 2 or (logp > 4 and n_aromatic >= 2):
        return {"QTc_Risk": "High", "QTc_Score": 0.20}
    elif alert_count == 1 or (logp > 3 and n_aromatic >= 1):
        return {"QTc_Risk": "Moderate", "QTc_Score": 0.55}
    else:
        return {"QTc_Risk": "Low", "QTc_Score": 0.88}


def estimate_oral_ld50_class(mw: float, logp: float, tpsa: float) -> dict:
    """
    ProTox-inspired oral rat LD50 toxicity class estimation.
    Uses MW/LogP/TPSA heuristics to assign GHS oral toxicity class.

    Classes: I (≤5 mg/kg), II (5–50), III (50–300), IV (300–2000),
             V (2000–5000), VI (>5000 — essentially non-toxic).
    NEW — not present in existing admet_filtering.py.
    """
    # Heuristic: low MW + high LogP + low TPSA → higher absorption → potentially more toxic
    absorption_proxy = max(0.0, (1.0 - tpsa / 150.0) * min(logp / 5.0, 1.0))

    if mw < 150 and logp > 2:
        tox_class = "III (50–300 mg/kg)"
        tox_score = 0.60
    elif absorption_proxy > 0.6 and logp > 3.5:
        tox_class = "III (50–300 mg/kg)"
        tox_score = 0.60
    elif absorption_proxy > 0.3:
        tox_class = "IV (300–2000 mg/kg)"
        tox_score = 0.75
    elif mw > 500 or tpsa > 120:
        tox_class = "V (2000–5000 mg/kg) — Low Toxicity"
        tox_score = 0.90
    else:
        tox_class = "IV (300–2000 mg/kg)"
        tox_score = 0.75

    return {"LD50_Class": tox_class, "LD50_Safety_Score": tox_score}


# ══════════════════════════════════════════════════════════════════════════════
# Extended Safety Profile (Integrates existing + new predictors)
# ══════════════════════════════════════════════════════════════════════════════

def compute_extended_safety_profile(smiles, drug_name="Unknown",
                                    predicted_prob=None,
                                    indication=""):
    """
    Compute full 10-endpoint extended safety profile.

    REUSES (from admet_filtering.py — unchanged):
        compute_lipinski_properties, compute_veber_properties, check_pains,
        predict_gi_absorption, predict_bbb_permeability, predict_cyp_metabolism,
        predict_herg_liability, predict_hepatotoxicity, predict_ames_mutagenicity

    ADDS (new endpoints):
        predict_nephrotoxicity, predict_reproductive_toxicity,
        predict_skin_sensitisation, predict_qtc_prolongation, estimate_oral_ld50_class
    """
    mol = None
    if HAS_RDKIT:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            mol = Chem.MolFromSmiles(smiles, sanitize=False)
            if mol is not None:
                try:
                    mol.UpdatePropertyCache(strict=False)
                    Chem.FastFindRings(mol)
                except Exception:
                    mol = None

    profile = {
        "Drug Name":            drug_name,
        "SMILES":               smiles,
        "Original Indication":  indication,
        "Predicted_DTI_Prob":   round(predicted_prob, 4) if predicted_prob is not None else None,
    }

    # ── Existing ADMET endpoints (all reused from admet_filtering.py) ──────────
    lip  = compute_lipinski_properties(mol)
    veb  = compute_veber_properties(mol)
    pains = check_pains(mol)
    gi   = predict_gi_absorption(lip["MW"], lip["LogP"], veb["TPSA"], lip["HBD"])
    bbb  = predict_bbb_permeability(lip["MW"], lip["LogP"], veb["TPSA"], lip["HBD"])
    cyp  = predict_cyp_metabolism(mol)
    herg = predict_herg_liability(mol, lip["LogP"])
    hep  = predict_hepatotoxicity(mol)
    ames = predict_ames_mutagenicity(mol)

    profile.update(lip)
    profile.update(veb)
    profile["PAINS_Free"]    = pains["PAINS_Free"]
    profile["PAINS_Alerts"]  = "; ".join(pains["PAINS_Alerts"]) if pains["PAINS_Alerts"] else "None"
    profile.update(gi)
    profile.update(bbb)
    profile["CYP_Risk"]          = cyp["CYP_Risk"]
    profile["CYP_Score"]         = cyp["CYP_Score"]
    profile.update(herg)
    profile["Hepatotox_Risk"]    = hep["Hepatotox_Risk"]
    profile["Hepatotox_Score"]   = hep["Hepatotox_Score"]
    profile.update(ames)

    # ── NEW Extended Toxicity Endpoints ───────────────────────────────────────
    neph = predict_nephrotoxicity(mol)
    repro= predict_reproductive_toxicity(mol)
    skin = predict_skin_sensitisation(mol)
    qtc  = predict_qtc_prolongation(mol, lip["LogP"])
    ld50 = estimate_oral_ld50_class(lip["MW"], lip["LogP"], veb["TPSA"])

    profile.update(neph)
    profile.update(repro)
    profile.update(skin)
    profile.update(qtc)
    profile.update(ld50)

    # ── Composite Extended Safety Score (all 10 endpoints, 0–1, higher = safer) ─
    lipinski_score = 1.0 if lip["Lipinski_Pass"] else max(0, 1.0 - lip["Lipinski_Violations"] * 0.25)
    veber_score    = 1.0 if veb["Veber_Pass"] else 0.5
    pains_score    = 1.0 if pains["PAINS_Free"] else 0.2

    safety_composite = (
        0.08 * lipinski_score +
        0.05 * veber_score +
        0.08 * pains_score +
        0.10 * gi["GI_Score"] +
        0.03 * bbb["BBB_Score"] +
        0.08 * cyp["CYP_Score"] +
        0.12 * herg["hERG_Score"] +           # Cardiac safety — high weight
        0.12 * hep["Hepatotox_Score"] +       # Hepatotoxicity — high weight
        0.10 * ames["Ames_Score"] +
        0.08 * neph["Nephrotox_Score"] +
        0.06 * repro["ReproTox_Score"] +
        0.05 * skin["SkinSens_Score"] +
        0.05 * qtc["QTc_Score"]               # Cardiac QTc — added
    ) / 1.00  # weights sum to 1.00
    # Normalise in case weights don't add to exactly 1
    total_weight = (0.08 + 0.05 + 0.08 + 0.10 + 0.03 + 0.08 + 0.12 + 0.12 + 0.10 + 0.08 + 0.06 + 0.05 + 0.05)
    safety_composite /= total_weight

    profile["Extended_Safety_Score"] = round(float(safety_composite), 4)

    # ── Safety Tier ───────────────────────────────────────────────────────────
    high_risk_flags = sum([
        hep["Hepatotox_Risk"] == "High",
        herg["hERG_Risk"] == "High",
        ames["Ames_Risk"] == "Positive (Alert)",
        neph["Nephrotox_Risk"] == "High",
        repro["ReproTox_Risk"] == "High",
        qtc["QTc_Risk"] == "High",
        not pains["PAINS_Free"],
    ])

    if safety_composite >= 0.70 and high_risk_flags == 0:
        profile["Safety_Tier"]  = "✅ Safe-Prioritised"
        profile["Safety_Color"] = "green"
    elif safety_composite >= 0.50 and high_risk_flags <= 1:
        profile["Safety_Tier"]  = "⚠️  Caution"
        profile["Safety_Color"] = "orange"
    else:
        profile["Safety_Tier"]  = "🚫 Flagged (Unsafe)"
        profile["Safety_Color"] = "red"

    profile["High_Risk_Flag_Count"] = high_risk_flags

    return profile


# ══════════════════════════════════════════════════════════════════════════════
# Visualisations
# ══════════════════════════════════════════════════════════════════════════════

SAFETY_ENDPOINTS = [
    ("GI_Score",            "GI Absorption"),
    ("CYP_Score",           "CYP Safety"),
    ("hERG_Score",          "hERG/Cardiac"),
    ("Hepatotox_Score",     "Hepatotox"),
    ("Ames_Score",          "Ames Mutagenic"),
    ("Nephrotox_Score",     "Nephrotox"),
    ("ReproTox_Score",      "ReproTox"),
    ("SkinSens_Score",      "Skin Sensitise"),
    ("QTc_Score",           "QTc Prolong"),
    ("LD50_Safety_Score",   "LD50 Safety"),
]


def plot_safety_heatmap(df: pd.DataFrame) -> None:
    """2D heatmap: safety endpoints × drugs (top 20 by safety score)."""
    os.makedirs(FIG_DIR, exist_ok=True)
    score_cols = [c for c, _ in SAFETY_ENDPOINTS if c in df.columns]
    label_cols = [l for c, l in SAFETY_ENDPOINTS if c in df.columns]

    top20 = df.head(20)
    matrix = top20[score_cols].values.astype(float)
    drugs  = top20["Drug Name"].tolist()

    fig, ax = plt.subplots(figsize=(14, 9), dpi=200)
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=0.0, vmax=1.0)
    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.01)
    cbar.set_label("Safety Score (1.0 = Safest)", fontsize=10)

    ax.set_xticks(range(len(label_cols)))
    ax.set_xticklabels(label_cols, fontsize=9, fontweight="bold", rotation=30, ha="right")
    ax.set_yticks(range(len(drugs)))
    ax.set_yticklabels(drugs, fontsize=9)

    for i in range(len(drugs)):
        for j in range(len(score_cols)):
            val = matrix[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    color="black" if 0.3 <= val <= 0.7 else "white", fontsize=8)

    ax.set_title("Extended Safety Profile Heatmap — Non-Anticancer TB Drug Candidates\n"
                 "(Green = Safe, Red = Risk; sorted by Extended Safety Score)",
                 fontsize=11, fontweight="bold", pad=10)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "extended_safety_heatmap.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"[Figure] Extended safety heatmap → {out}")


def plot_safety_radar(df: pd.DataFrame, top_n: int = 6) -> None:
    """Radar chart for top N safe candidates across all safety endpoints."""
    os.makedirs(FIG_DIR, exist_ok=True)
    score_cols = [c for c, _ in SAFETY_ENDPOINTS if c in df.columns]
    label_cols = [l for c, l in SAFETY_ENDPOINTS if c in df.columns]
    N = len(score_cols)
    if N < 3:
        return

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True), dpi=200)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(label_cols, fontsize=10, fontweight="bold", color="#374151")
    ax.set_rlabel_position(0)
    ax.set_yticks([0.25, 0.50, 0.75, 1.0])
    ax.set_yticklabels(["0.25", "0.50", "0.75", "1.00"], color="grey", size=8)
    ax.set_ylim(0, 1.05)

    palette = ["#2563eb", "#16a34a", "#dc2626", "#d97706", "#7c3aed", "#0891b2"]
    top_safe = df[df["Safety_Tier"] == "✅ Safe-Prioritised"].head(top_n)

    for idx, (_, row) in enumerate(top_safe.iterrows()):
        values = [row.get(c, 0.5) for c in score_cols]
        values += values[:1]
        c = palette[idx % len(palette)]
        ax.plot(angles, values, linewidth=2, linestyle="solid",
                label=row["Drug Name"], color=c)
        ax.fill(angles, values, color=c, alpha=0.07)

    ax.set_title(f"Extended Safety Radar — Top {len(top_safe)} Safe-Prioritised Candidates\n"
                 "(Non-Anticancer TB Drugs, 10-Endpoint Assessment)",
                 fontsize=12, fontweight="bold", y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.4, 1.1), fontsize=10, frameon=True)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "extended_safety_radar.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"[Figure] Extended safety radar → {out}")


def plot_final_tier_ranking(df: pd.DataFrame) -> None:
    """
    Horizontal bar chart of final ranked candidates, colour-coded by safety tier.
    X-axis = combined score (DTI probability × extended safety score).
    """
    os.makedirs(FIG_DIR, exist_ok=True)
    top30 = df.head(30).copy()
    if "Predicted_DTI_Prob" in top30.columns and top30["Predicted_DTI_Prob"].notna().any():
        top30["Combined_Score"] = (top30["Predicted_DTI_Prob"] * top30["Extended_Safety_Score"]).round(4)
    else:
        top30["Combined_Score"] = top30["Extended_Safety_Score"]

    top30 = top30.sort_values("Combined_Score", ascending=True)
    names   = top30["Drug Name"].tolist()
    scores  = top30["Combined_Score"].tolist()
    tiers   = top30["Safety_Tier"].tolist()

    color_map = {
        "✅ Safe-Prioritised": "#16a34a",
        "⚠️  Caution":         "#f59e0b",
        "🚫 Flagged (Unsafe)": "#ef4444",
    }
    bar_colors = [color_map.get(t, "#94a3b8") for t in tiers]

    fig, ax = plt.subplots(figsize=(12, 10), dpi=200)
    bars = ax.barh(range(len(names)), scores, color=bar_colors, edgecolor="#1e293b", linewidth=0.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Combined Score (DTI Probability × Safety Score)", fontsize=11, fontweight="bold")
    ax.set_title("Final Tiered Ranking: Non-Anticancer M. tuberculosis Drug Candidates\n"
                 "(Combined: Binding Efficacy × Extended Safety Score)",
                 fontsize=11, fontweight="bold")
    ax.set_xlim(0, 1.05)
    for bar, s in zip(bars, scores):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{s:.3f}", va="center", fontsize=8, fontweight="bold")

    patches = [mpatches.Patch(color=v, label=k) for k, v in color_map.items()]
    ax.legend(handles=patches, loc="lower right", fontsize=9, frameon=True)
    ax.set_facecolor("#f8fafc")
    ax.grid(axis="x", alpha=0.2)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "final_tiered_ranking.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"[Figure] Final tiered ranking chart → {out}")


def plot_binding_vs_safety_scatter(df: pd.DataFrame) -> None:
    """Scatter: DTI Probability (x) vs Extended Safety Score (y), coloured by tier."""
    if "Predicted_DTI_Prob" not in df.columns or df["Predicted_DTI_Prob"].isna().all():
        return
    os.makedirs(FIG_DIR, exist_ok=True)

    color_map = {
        "✅ Safe-Prioritised": "#16a34a",
        "⚠️  Caution":         "#f59e0b",
        "🚫 Flagged (Unsafe)": "#ef4444",
    }
    fig, ax = plt.subplots(figsize=(9, 7), dpi=200)
    for tier, group in df.groupby("Safety_Tier"):
        ax.scatter(
            group["Predicted_DTI_Prob"], group["Extended_Safety_Score"],
            c=color_map.get(tier, "#94a3b8"), label=tier,
            s=80, alpha=0.8, edgecolors="#1e293b", linewidths=0.5
        )
        for _, row in group.iterrows():
            ax.annotate(row["Drug Name"],
                        (row["Predicted_DTI_Prob"], row["Extended_Safety_Score"]),
                        textcoords="offset points", xytext=(4, 3), fontsize=7, alpha=0.9)

    ax.axvline(0.5,  color="#2563eb", linestyle="--", linewidth=1.0, alpha=0.5, label="DTI threshold = 0.5")
    ax.axhline(0.70, color="#16a34a", linestyle="--", linewidth=1.0, alpha=0.5, label="Safety threshold = 0.70")
    ax.set_xlabel("Predicted DTI Probability", fontsize=11, fontweight="bold")
    ax.set_ylabel("Extended Safety Score", fontsize=11, fontweight="bold")
    ax.set_title("Drug Efficacy vs Safety: M. tuberculosis Non-Anticancer Candidates\n"
                 "(Top-right quadrant = best candidates)",
                 fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9, frameon=True)
    ax.set_facecolor("#f8fafc")
    ax.grid(alpha=0.2)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "efficacy_vs_safety_scatter.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"[Figure] Efficacy vs safety scatter → {out}")


# ══════════════════════════════════════════════════════════════════════════════
# Main Orchestrator
# ══════════════════════════════════════════════════════════════════════════════

def run_toxicity_safety_screening(df_screening=None,
                                  drug_library=None):
    """
    Main entry point for Requirement 3.

    Parameters
    ----------
    df_screening : pd.DataFrame | None
        Output of drugbank_screening.run_drugbank_screening() — TrxB2 screening results.
        If None, falls back to the EXTENDED_DRUG_LIBRARY from drugbank_screening.py.
    drug_library : list | None
        Extended drug library. Used when df_screening is None.

    Returns
    -------
    df_safety : pd.DataFrame — full extended safety assessment, ranked.
    """
    print("\n" + "=" * 65)
    print("  REQUIREMENT 3 — EXTENDED TOXICITY & SAFETY SCREENING")
    print("  Endpoints: 10 (existing ADMET + 5 new endpoints)")
    print("  Reuses: ALL existing admet_filtering.py predictors")
    print("=" * 65 + "\n")

    os.makedirs(SAFE_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    # ── Build drug list from screening results ────────────────────────────────
    if df_screening is not None and len(df_screening) > 0:
        # Only screen non-anticancer candidates from Requirement 2
        is_ac_col = "Is Anticancer"
        if is_ac_col in df_screening.columns:
            candidates = df_screening[~df_screening[is_ac_col]].copy()
        else:
            candidates = df_screening.copy()
        print(f"  Screening {len(candidates)} non-anticancer candidates from DrugBank screening.")

        drug_list = []
        for _, row in candidates.iterrows():
            drug_list.append({
                "drug_name":  row.get("Drug Name", "Unknown"),
                "smiles":     row.get("SMILES", ""),
                "indication": row.get("Original Indication", ""),
                "predicted_prob": row.get("Predicted Probability", None),
            })
    else:
        # Fallback: use the imported EXTENDED_DRUG_LIBRARY
        from drugbank_screening import EXTENDED_DRUG_LIBRARY
        drug_list = [
            {"drug_name": d["drug_name"], "smiles": d["smiles"],
             "indication": d["indication"], "predicted_prob": None}
            for d in EXTENDED_DRUG_LIBRARY
            if not d.get("is_anticancer", False)
        ]
        print(f"  Screening {len(drug_list)} drugs from EXTENDED_DRUG_LIBRARY (fallback).")

    # ── Run extended safety profile per compound ──────────────────────────────
    profiles = []
    for drug in drug_list:
        print(f"  Assessing: {drug['drug_name']}...")
        try:
            profile = compute_extended_safety_profile(
                smiles=drug["smiles"],
                drug_name=drug["drug_name"],
                predicted_prob=drug.get("predicted_prob"),
                indication=drug["indication"],
            )
        except Exception as exc:
            print(f"  [WARN] {drug['drug_name']} skipped — {exc}")
            profile = {
                "Drug Name": drug["drug_name"],
                "SMILES": drug["smiles"],
                "Original Indication": drug["indication"],
                "Predicted_DTI_Prob": drug.get("predicted_prob"),
                "Safety_Tier": "Flagged",
                "Extended_Safety_Score": 0.0,
                "Skip_Reason": str(exc),
            }
        profiles.append(profile)

    df_safety = pd.DataFrame(profiles)

    # Rank by Extended Safety Score (primary), then DTI Probability (secondary)
    sort_cols = ["Extended_Safety_Score"]
    if "Predicted_DTI_Prob" in df_safety.columns and df_safety["Predicted_DTI_Prob"].notna().any():
        sort_cols.append("Predicted_DTI_Prob")

    df_safety = df_safety.sort_values(sort_cols, ascending=[False, False] if len(sort_cols) == 2 else [False])
    df_safety = df_safety.reset_index(drop=True)
    df_safety.index += 1
    df_safety.index.name = "Safety_Rank"

    # ── Save full results ─────────────────────────────────────────────────────
    safety_csv = os.path.join(SAFE_DIR, "extended_safety_profiles.csv")
    df_safety.to_csv(safety_csv)
    print(f"\n[Saved] Extended safety profiles → {safety_csv}")

    # ── Tier summary ──────────────────────────────────────────────────────────
    tier_counts = df_safety["Safety_Tier"].value_counts()

    # ── Comparison table: binding + safety ───────────────────────────────────
    comparison_cols = [
        "Drug Name", "Original Indication", "Predicted_DTI_Prob",
        "Extended_Safety_Score", "Safety_Tier",
        "Hepatotox_Risk", "hERG_Risk", "Ames_Risk",
        "Nephrotox_Risk", "ReproTox_Risk", "QTc_Risk",
        "Lipinski_Pass", "PAINS_Free",
    ]
    display_cols = [c for c in comparison_cols if c in df_safety.columns]
    comp_table = df_safety[display_cols]
    comp_csv = os.path.join(SAFE_DIR, "binding_vs_safety_comparison.csv")
    comp_table.to_csv(comp_csv)
    print(f"[Saved] Binding vs safety comparison table → {comp_csv}")

    # ── Console output ────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  FINAL SAFETY SCREENING RESULTS")
    print("=" * 65)
    print(comp_table.to_string())

    print("\n── Safety Tier Summary ──────────────────────────────────────")
    for tier, count in tier_counts.items():
        print(f"  {tier}: {count} compounds")

    safe_drugs = df_safety[df_safety["Safety_Tier"] == "✅ Safe-Prioritised"]
    if len(safe_drugs) > 0:
        print(f"\n── Safe-Prioritised Candidates (Recommended for Experimental Follow-up) ──")
        for _, row in safe_drugs.iterrows():
            dti = f"DTI={row['Predicted_DTI_Prob']:.3f}" if pd.notna(row.get("Predicted_DTI_Prob")) else ""
            print(f"  {row['Drug Name']:25s}  Safety={row['Extended_Safety_Score']:.3f}  {dti}  "
                  f"[{row['Original Indication'][:40]}]")

    # ── Flagged/unsafe candidates ─────────────────────────────────────────────
    flagged = df_safety[df_safety["Safety_Tier"] == "🚫 Flagged (Unsafe)"]
    if len(flagged) > 0:
        print(f"\n── Flagged Compounds (Filtered from Recommendation List) ──")
        for _, row in flagged.iterrows():
            reasons = []
            for col in ["Hepatotox_Risk", "hERG_Risk", "Ames_Risk", "Nephrotox_Risk", "ReproTox_Risk"]:
                if col in row and row[col] in ["High", "Positive (Alert)"]:
                    reasons.append(col.replace("_Risk", ""))
            print(f"  🚫 {row['Drug Name']:25s} — High risk: {', '.join(reasons) or 'Multiple alerts'}")

    # ── Visualisations ────────────────────────────────────────────────────────
    plot_safety_heatmap(df_safety)
    plot_safety_radar(df_safety)
    plot_final_tier_ranking(df_safety)
    plot_binding_vs_safety_scatter(df_safety)

    print("\n[Requirement 3 Complete] Extended toxicity & safety screening finished.")
    print(f"  Compounds assessed          : {len(df_safety)}")
    print(f"  Safe-Prioritised            : {tier_counts.get('✅ Safe-Prioritised', 0)}")
    print(f"  Caution                     : {tier_counts.get('⚠️  Caution', 0)}")
    print(f"  Flagged (Unsafe)            : {tier_counts.get('🚫 Flagged (Unsafe)', 0)}")
    print(f"  Figures generated           : safety heatmap, radar, tier ranking, scatter")

    return df_safety


if __name__ == "__main__":
    # Can be run standalone — will fallback to EXTENDED_DRUG_LIBRARY
    df_safety = run_toxicity_safety_screening()
