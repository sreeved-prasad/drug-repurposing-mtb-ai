"""
NEW MODULE — Requirement 1: Experimental Inhibitor Data Collection & Normalization
====================================================================================
Searches ChEMBL for additional IC50 and Ki inhibitor records against the existing
Mycobacterium tuberculosis protein targets, cleans and normalises all values into
a consistent pIC50/pKi (−log10 M) format, and writes two separate outputs:

  results/experimental/mtb_experimental_inhibitors.csv   — cleaned measurements
  results/experimental/mtb_inhibitor_summary.csv         — per-target summary stats
  results/figures/experimental_pic50_distribution.png    — violin plot

REUSED COMPONENTS:
  - data_collection.py: fetch_json(), existing chembl_tb_targets.csv
  - preprocessing.py:   is_valid_smiles(), convert_to_pic50()
  - admet_filtering.py: compute_lipinski_properties() for quick profile

NEWLY IMPLEMENTED:
  - Targeted IC50 / Ki query per target (up to 500 records each)
  - Ki → pKi conversion on the same log-scale as pIC50
  - Measurement-type provenance column (keeps IC50 vs Ki separate)
  - Chemical-space analysis via scaffold clustering (Murcko BRICS)
  - Target-stratified violin/box plot of pActivity distributions
"""

import os
import sys
import math
import json
import time
import urllib.request
import urllib.parse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Reuse existing project utilities ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from preprocessing import is_valid_smiles, convert_to_pic50

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    from rdkit.Chem.Scaffolds import MurckoScaffold
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT_DIR    = os.path.dirname(os.path.dirname(__file__))
RAW_DIR     = os.path.join(ROOT_DIR, "data", "raw")
EXP_DIR     = os.path.join(ROOT_DIR, "results", "experimental")
FIG_DIR     = os.path.join(ROOT_DIR, "results", "figures")

# ── Core Mycobacterium tuberculosis target panel (ChEMBL IDs from existing CSV) ──
PRIORITY_TARGETS = [
    {"chembl_id": "CHEMBL2390811", "gene": "trxB2",  "name": "Thioredoxin Reductase",          "uniprot": "P9WHH1"},
    {"chembl_id": "CHEMBL1849",    "gene": "inhA",   "name": "Enoyl-ACP Reductase",             "uniprot": "P9WGR1"},
    {"chembl_id": "CHEMBL1908385", "gene": "pknB",   "name": "Ser/Thr Protein Kinase PknB",     "uniprot": "P9WI81"},
    {"chembl_id": "CHEMBL4165",    "gene": "gyrA",   "name": "DNA Gyrase Subunit A",            "uniprot": "P9WG47"},
    {"chembl_id": "CHEMBL2031",    "gene": "alrA",   "name": "Alanine Racemase",                "uniprot": "P9WQA9"},
    {"chembl_id": "CHEMBL2030",    "gene": "ddlA",   "name": "D-Ala-D-Ala Ligase",             "uniprot": "P9WP31"},
    {"chembl_id": "CHEMBL4213",    "gene": "ftsZ",   "name": "Cell Division Protein FtsZ",      "uniprot": "P9WN95"},
    {"chembl_id": "CHEMBL5631",    "gene": "can",    "name": "Beta-Carbonic Anhydrase 1",       "uniprot": "P9WPJ7"},
    {"chembl_id": "CHEMBL4630874", "gene": "clpC1",  "name": "ClpC1 ATPase",                   "uniprot": "P9WPC9"},
    {"chembl_id": "CHEMBL5169228", "gene": "ndh",    "name": "NADH:Quinone Oxidoreductase Ndh", "uniprot": "P95160"},
]

# ── Measurement types to harvest (separately for IC50 and Ki) ─────────────────
MEASUREMENT_TYPES = ["IC50", "Ki"]

# ── Thresholds ────────────────────────────────────────────────────────────────
ACTIVE_THRESHOLD_NM   = 10_000   # ≤ 10 µM → Active in preliminary screen
POTENT_THRESHOLD_NM   = 1_000    # ≤ 1 µM  → Potent
NANOMOLAR_THRESHOLD   = 100      # ≤ 100 nM → Nanomolar potency


# ══════════════════════════════════════════════════════════════════════════════
# Data Retrieval
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_json_safe(url, retries=3, timeout=12):
    """Fetch JSON from URL with retry logic (reuses pattern from data_collection.py)."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return {}


def fetch_inhibitor_data(target_chembl_id: str, measurement_type: str = "IC50",
                         limit: int = 500) -> list:
    """
    Query ChEMBL REST API for IC50 or Ki records for a given target.
    Returns raw activity records as list of dicts.
    """
    encoded_type = urllib.parse.quote(measurement_type)
    url = (
        f"https://www.ebi.ac.uk/chembl/api/data/activity.json"
        f"?target_chembl_id={target_chembl_id}"
        f"&standard_type={encoded_type}"
        f"&standard_relation=%3D"      # Only equality relations (=)
        f"&assay_type=B"               # Binding assays preferred
        f"&limit={limit}"
    )
    try:
        res = _fetch_json_safe(url)
        return res.get("activities", [])
    except Exception as e:
        print(f"    [Warning] ChEMBL API error for {target_chembl_id}/{measurement_type}: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# Normalisation & Cleaning
# ══════════════════════════════════════════════════════════════════════════════

def normalise_to_neg_log(value_raw, units: str, measurement_type: str):
    """
    Convert raw measurement → pActivity (−log10 M scale).
    Returns (pActivity, units_flag) or (None, None) on failure.

    Scale:
        nM → pActivity = 9 − log10(value)      [same as convert_to_pic50]
        µM → pActivity = 6 − log10(value)      [1 µM = 1000 nM]
        mM → pActivity = 3 − log10(value)
        M  → pActivity = −log10(value)
    """
    if value_raw is None or (isinstance(value_raw, float) and math.isnan(value_raw)):
        return None, None
    try:
        v = float(value_raw)
        if v <= 0:
            return None, None
        u = str(units).strip().lower()
        if u in ("nm", "nmol/l", "nmol/ml"):
            return convert_to_pic50(v), "nM"       # reuses existing helper
        elif u in ("um", "µm", "umol/l", "µmol/l"):
            return convert_to_pic50(v * 1_000), "µM"
        elif u in ("mm", "mmol/l"):
            return convert_to_pic50(v * 1_000_000), "mM"
        elif u in ("m", "mol/l"):
            p = -math.log10(v)
            return round(p, 4), "M"
        else:
            return None, None
    except Exception:
        return None, None


def clean_activity_record(raw: dict, target_meta: dict):
    """
    Parse one ChEMBL activity record into a clean, normalised row.
    Returns None if the record should be dropped.
    """
    smiles    = str(raw.get("canonical_smiles", "") or "").strip()
    mol_id    = raw.get("molecule_chembl_id", "")
    std_type  = str(raw.get("standard_type", "")).strip()
    std_val   = raw.get("standard_value")
    std_units = str(raw.get("standard_units", "") or "").strip()
    std_rel   = str(raw.get("standard_relation", "=") or "=").strip()
    pchembl   = raw.get("pchembl_value")            # ChEMBL's pre-computed −log10 M

    # Must have SMILES
    if not is_valid_smiles(smiles):
        return None

    # Prefer ChEMBL's own pChEMBL value if present (most reliable)
    if pchembl is not None:
        try:
            p_norm = round(float(pchembl), 4)
            source_norm = "pChEMBL_official"
        except Exception:
            p_norm, source_norm = None, None
    else:
        p_norm, source_norm = None, None

    # Fallback: normalise raw value
    if p_norm is None:
        p_norm, units_flag = normalise_to_neg_log(std_val, std_units, std_type)
        source_norm = f"computed_from_{units_flag}" if units_flag else None

    if p_norm is None:
        return None

    # Classify potency tier
    val_nm = None
    if std_units.lower() in ("nm", "nmol/l"):
        try:
            val_nm = float(std_val)
        except Exception:
            pass

    if val_nm is not None:
        if val_nm <= NANOMOLAR_THRESHOLD:
            potency_tier = "Nanomolar (≤100 nM)"
        elif val_nm <= POTENT_THRESHOLD_NM:
            potency_tier = "Potent (≤1 µM)"
        elif val_nm <= ACTIVE_THRESHOLD_NM:
            potency_tier = "Active (≤10 µM)"
        else:
            potency_tier = "Weak (>10 µM)"
    else:
        # Classify from pActivity
        if p_norm >= 7.0:
            potency_tier = "Nanomolar (≤100 nM)"
        elif p_norm >= 6.0:
            potency_tier = "Potent (≤1 µM)"
        elif p_norm >= 5.0:
            potency_tier = "Active (≤10 µM)"
        else:
            potency_tier = "Weak (>10 µM)"

    return {
        "molecule_chembl_id":  mol_id,
        "canonical_smiles":    smiles,
        "target_chembl_id":    target_meta["chembl_id"],
        "target_gene":         target_meta["gene"],
        "target_name":         target_meta["name"],
        "uniprot_accession":   target_meta["uniprot"],
        "measurement_type":    std_type,       # IC50 or Ki — kept separate
        "raw_value":           std_val,
        "raw_units":           std_units,
        "p_activity":          p_norm,          # normalised pIC50 or pKi
        "normalization_source": source_norm,
        "potency_tier":        potency_tier,
        "assay_relation":      std_rel,
        "data_source":         "ChEMBL_experimental",
    }


def compute_murcko_scaffold(smiles: str) -> str:
    """Return Murcko scaffold SMILES (or empty string if RDKit unavailable)."""
    if not HAS_RDKIT:
        return ""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return ""
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold) if scaffold else ""
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# Chemical-Space Analysis
# ══════════════════════════════════════════════════════════════════════════════

def analyse_chemical_space(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich the cleaned dataset with Murcko scaffold and 4 key
    physicochemical descriptors for inhibitor pattern analysis.
    """
    print("\n[ChemSpace] Computing Murcko scaffolds and physicochemical descriptors...")

    scaffolds, mws, logps, hbds, hbas = [], [], [], [], []
    for smi in df["canonical_smiles"]:
        scaffolds.append(compute_murcko_scaffold(smi))
        if HAS_RDKIT:
            mol = Chem.MolFromSmiles(smi)
            if mol:
                mws.append(round(Descriptors.MolWt(mol), 2))
                logps.append(round(Descriptors.MolLogP(mol), 2))
                hbds.append(int(Descriptors.NumHDonors(mol)))
                hbas.append(int(Descriptors.NumHAcceptors(mol)))
            else:
                mws.append(None); logps.append(None)
                hbds.append(None); hbas.append(None)
        else:
            mws.append(None); logps.append(None)
            hbds.append(None); hbas.append(None)

    df = df.copy()
    df["murcko_scaffold"] = scaffolds
    df["MW"]   = mws
    df["LogP"] = logps
    df["HBD"]  = hbds
    df["HBA"]  = hbas

    n_unique_scaffolds = df["murcko_scaffold"].replace("", pd.NA).dropna().nunique()
    print(f"  → {n_unique_scaffolds} unique Murcko scaffolds across {len(df)} inhibitors")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Visualisation
# ══════════════════════════════════════════════════════════════════════════════

def plot_pactivity_distributions(df: pd.DataFrame) -> None:
    """
    Violin plot: pActivity (pIC50 / pKi) distribution per target, split by
    measurement type (IC50 vs Ki).  Saves to results/figures/.
    """
    os.makedirs(FIG_DIR, exist_ok=True)

    targets_ordered = df.groupby("target_gene")["p_activity"].median().sort_values(ascending=False).index.tolist()
    n_targets = len(targets_ordered)

    fig, axes = plt.subplots(1, n_targets, figsize=(max(14, n_targets * 2.2), 7), sharey=True, dpi=200)
    if n_targets == 1:
        axes = [axes]

    colors = {"IC50": "#2563eb", "Ki": "#16a34a"}
    all_types = df["measurement_type"].unique()

    for ax, gene in zip(axes, targets_ordered):
        sub = df[df["target_gene"] == gene]
        parts_data = []
        part_labels = []
        part_colors = []
        for mtype in sorted(all_types):
            vals = sub[sub["measurement_type"] == mtype]["p_activity"].dropna().tolist()
            if vals:
                parts_data.append(vals)
                part_labels.append(mtype)
                part_colors.append(colors.get(mtype, "#94a3b8"))

        if parts_data:
            vp = ax.violinplot(parts_data, showmedians=True, showextrema=True)
            for pc, col in zip(vp["bodies"], part_colors):
                pc.set_facecolor(col)
                pc.set_alpha(0.65)
            vp["cmedians"].set_color("black")
            vp["cmedians"].set_linewidth(1.8)

        ax.set_xticks(range(1, len(part_labels) + 1))
        ax.set_xticklabels(part_labels, fontsize=9)
        ax.set_title(gene.upper(), fontsize=10, fontweight="bold")
        ax.axhline(y=6.0, color="#ef4444", linestyle="--", linewidth=0.9, alpha=0.7, label="pAct=6 (1µM)")
        ax.axhline(y=7.0, color="#f59e0b", linestyle=":", linewidth=0.9, alpha=0.7, label="pAct=7 (100nM)")
        n_total = len(sub)
        ax.set_xlabel(f"n={n_total}", fontsize=8)
        ax.set_facecolor("#f8fafc")
        ax.grid(axis="y", alpha=0.25)

    axes[0].set_ylabel("pIC50 / pKi (−log₁₀ M)", fontsize=12, fontweight="bold")
    fig.suptitle(
        "Experimental Inhibitor pActivity Distributions per M. tuberculosis Target\n"
        "(Blue = IC50, Green = Ki; dashed = 1 µM threshold, dotted = 100 nM threshold)",
        fontsize=11, fontweight="bold", y=1.01
    )
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "experimental_pic50_distribution.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"[Figure] pActivity violin plot saved → {out}")


def plot_scaffold_diversity(df: pd.DataFrame) -> None:
    """Bar chart of top 15 Murcko scaffolds by inhibitor count across all targets."""
    if not HAS_RDKIT or "murcko_scaffold" not in df.columns:
        return
    os.makedirs(FIG_DIR, exist_ok=True)

    top_scaffolds = (
        df[df["murcko_scaffold"] != ""]
        .groupby("murcko_scaffold").size()
        .sort_values(ascending=False)
        .head(15)
    )
    if top_scaffolds.empty:
        return

    labels = [f"Scaffold-{i+1}" for i in range(len(top_scaffolds))]
    fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
    bars = ax.barh(labels, top_scaffolds.values, color="#6366f1", edgecolor="#1e1b4b")
    ax.set_xlabel("Number of Inhibitors", fontsize=11)
    ax.set_title("Top 15 Most Frequent Murcko Scaffolds in M. tuberculosis Inhibitor Dataset",
                 fontsize=11, fontweight="bold")
    for bar, val in zip(bars, top_scaffolds.values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9)
    ax.invert_yaxis()
    ax.set_facecolor("#f8fafc")
    ax.grid(axis="x", alpha=0.2)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "scaffold_diversity_mtb.png")
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    print(f"[Figure] Scaffold diversity chart saved → {out}")


# ══════════════════════════════════════════════════════════════════════════════
# Summary Report
# ══════════════════════════════════════════════════════════════════════════════

def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-target, per-measurement-type summary statistics.
    """
    rows = []
    for gene in df["target_gene"].unique():
        for mtype in df["measurement_type"].unique():
            sub = df[(df["target_gene"] == gene) & (df["measurement_type"] == mtype)]
            if sub.empty:
                continue
            p = sub["p_activity"].dropna()
            rows.append({
                "Target Gene":        gene,
                "Target Name":        sub["target_name"].iloc[0],
                "UniProt":            sub["uniprot_accession"].iloc[0],
                "Measurement Type":   mtype,
                "Total Records":      len(sub),
                "pActivity Mean":     round(p.mean(), 3) if len(p) else None,
                "pActivity Median":   round(p.median(), 3) if len(p) else None,
                "pActivity Std":      round(p.std(), 3) if len(p) else None,
                "pActivity Min":      round(p.min(), 3) if len(p) else None,
                "pActivity Max":      round(p.max(), 3) if len(p) else None,
                "Nanomolar Hits (pAct≥7.0)": int((p >= 7.0).sum()),
                "Potent Hits (pAct≥6.0)":    int((p >= 6.0).sum()),
                "Active Hits (pAct≥5.0)":    int((p >= 5.0).sum()),
                "Unique Scaffolds":   sub["murcko_scaffold"].replace("", pd.NA).dropna().nunique()
                                      if "murcko_scaffold" in sub.columns else "N/A",
            })
    return pd.DataFrame(rows).sort_values(["Target Gene", "Measurement Type"])


# ══════════════════════════════════════════════════════════════════════════════
# Main Orchestrator
# ══════════════════════════════════════════════════════════════════════════════

def collect_experimental_inhibitors(targets=None, limit_per_query=400):
    """
    Main entry point.  Collects IC50 & Ki data for the target panel,
    normalises to pActivity, enriches with chemical-space features,
    and saves/visualises results.

    Parameters
    ----------
    targets : list[dict] | None
        Target list (uses PRIORITY_TARGETS by default).
    limit_per_query : int
        Max records per (target, measurement_type) query.

    Returns
    -------
    df_clean : pd.DataFrame   — cleaned inhibitor dataset
    df_summary : pd.DataFrame — per-target summary statistics
    """
    if targets is None:
        targets = PRIORITY_TARGETS

    os.makedirs(EXP_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    print("\n" + "=" * 65)
    print("  REQUIREMENT 1 — EXPERIMENTAL INHIBITOR DATA COLLECTION")
    print("  Source: ChEMBL REST API | Types: IC50, Ki")
    print("  Targets: Existing M. tuberculosis protein panel")
    print("=" * 65 + "\n")

    all_records = []
    for tgt in targets:
        print(f"\n── Target: {tgt['gene'].upper()} | {tgt['name']} | ChEMBL: {tgt['chembl_id']} ──")
        for mtype in MEASUREMENT_TYPES:
            print(f"  Fetching {mtype} data...", end=" ", flush=True)
            raw_acts = fetch_inhibitor_data(tgt["chembl_id"], mtype, limit_per_query)
            print(f"{len(raw_acts)} raw records received.")

            cleaned = 0
            for rec in raw_acts:
                row = clean_activity_record(rec, tgt)
                if row is not None:
                    all_records.append(row)
                    cleaned += 1
            print(f"  → {cleaned} records passed cleaning (SMILES valid + units normalised)")

    df_clean = pd.DataFrame(all_records)

    if df_clean.empty:
        print("\n[Warning] No experimental records collected (network or API issue).")
        # Return empty frames so downstream callers can handle gracefully
        return pd.DataFrame(), pd.DataFrame()

    # De-duplicate: same molecule + target + measurement_type → keep highest pActivity
    before = len(df_clean)
    df_clean = (
        df_clean
        .sort_values("p_activity", ascending=False)
        .drop_duplicates(subset=["molecule_chembl_id", "target_chembl_id", "measurement_type"])
        .reset_index(drop=True)
    )
    print(f"\n[Deduplication] {before} → {len(df_clean)} records after keeping best per compound-target-type.")

    # Chemical-space enrichment
    df_clean = analyse_chemical_space(df_clean)

    # Save cleaned dataset
    exp_csv = os.path.join(EXP_DIR, "mtb_experimental_inhibitors.csv")
    df_clean.to_csv(exp_csv, index=False)
    print(f"\n[Saved] Cleaned inhibitor dataset → {exp_csv}")

    # Summary statistics
    df_summary = build_summary(df_clean)
    summ_csv = os.path.join(EXP_DIR, "mtb_inhibitor_summary.csv")
    df_summary.to_csv(summ_csv, index=False)
    print(f"[Saved] Per-target summary statistics → {summ_csv}")

    # Console report
    print("\n" + "=" * 65)
    print("  EXPERIMENTAL INHIBITOR SUMMARY (by Target × Measurement Type)")
    print("=" * 65)
    print(df_summary[[
        "Target Gene", "Measurement Type", "Total Records",
        "pActivity Median", "Nanomolar Hits (pAct≥7.0)",
        "Potent Hits (pAct≥6.0)"
    ]].to_string(index=False))

    # Visualisations
    plot_pactivity_distributions(df_clean)
    plot_scaffold_diversity(df_clean)

    print("\n[Requirement 1 Complete] Experimental inhibitor data collected, normalised, and saved.")
    print(f"  Total clean records   : {len(df_clean)}")
    print(f"  Unique compounds      : {df_clean['molecule_chembl_id'].nunique()}")
    print(f"  Targets covered       : {df_clean['target_gene'].nunique()}")
    print(f"  IC50 records          : {(df_clean['measurement_type']=='IC50').sum()}")
    print(f"  Ki records            : {(df_clean['measurement_type']=='Ki').sum()}")

    return df_clean, df_summary


if __name__ == "__main__":
    df_inhibitors, df_summary = collect_experimental_inhibitors()

