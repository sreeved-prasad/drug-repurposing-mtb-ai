"""
run_professor_requirements.py
=================================
Unified runner for the three professor-requested additions to the existing
AI-Driven Drug Repurposing Pipeline for Mycobacterium tuberculosis.

USAGE:
    python run_professor_requirements.py              # all three requirements
    python run_professor_requirements.py --req 1      # requirement 1 only
    python run_professor_requirements.py --req 2      # requirement 2 only
    python run_professor_requirements.py --req 3      # requirement 3 only
    python run_professor_requirements.py --req 1 2 3  # explicit selection

REQUIREMENTS:
    1. Experimental Inhibitor Data  → src/experimental_inhibitor_data.py (NEW)
    2. DrugBank Screening & Analysis → src/drugbank_screening.py (NEW)
    3. Toxicity & Safety Screening  → src/toxicity_safety_screening.py (NEW)

REUSED (UNCHANGED):
    model.py, drug_features.py, protein_features.py, polypharmacology.py,
    admet_filtering.py, prediction.py, preprocessing.py, data_collection.py
"""

import os
import sys
import argparse
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def print_banner(title: str, req_num: int) -> None:
    width = 70
    print("\n" + "█" * width)
    print(f"█  REQUIREMENT {req_num}: {title}")
    print("█" * width)


def run_requirement_1():
    print_banner("EXPERIMENTAL INHIBITOR DATA COLLECTION & NORMALISATION", 1)
    from experimental_inhibitor_data import collect_experimental_inhibitors
    df_inhibitors, df_summary = collect_experimental_inhibitors()
    return df_inhibitors, df_summary


def run_requirement_2(exp_df=None):
    print_banner("DRUGBANK SCREENING & CHEMICAL PATTERN ANALYSIS", 2)
    from drugbank_screening import run_drugbank_screening
    df_trxb2, df_all = run_drugbank_screening(exp_df=exp_df)
    return df_trxb2, df_all


def run_requirement_3(df_trxb2=None):
    print_banner("TOXICITY & SAFETY SCREENING OF NON-ANTICANCER CANDIDATES", 3)
    from toxicity_safety_screening import run_toxicity_safety_screening
    df_safety = run_toxicity_safety_screening(df_screening=df_trxb2)
    return df_safety


def print_completion_summary(selected_reqs, results: dict, elapsed: float) -> None:
    import pandas as pd

    print("\n\n" + "═" * 70)
    print("  PROFESSOR REQUIREMENTS — EXECUTION COMPLETE")
    print("═" * 70)

    if 1 in selected_reqs and "inhibitors" in results:
        df_i = results["inhibitors"]
        if df_i is not None and len(df_i) > 0:
            print(f"\n  REQ 1 — Experimental Inhibitor Data:")
            print(f"    Clean records collected  : {len(df_i)}")
            print(f"    Unique compounds         : {df_i['molecule_chembl_id'].nunique()}")
            print(f"    Targets covered          : {df_i['target_gene'].nunique()}")
            ic50_n = (df_i["measurement_type"] == "IC50").sum()
            ki_n   = (df_i["measurement_type"] == "Ki").sum()
            print(f"    IC50 records             : {ic50_n}")
            print(f"    Ki records               : {ki_n}")
            print(f"    Output: results/experimental/mtb_experimental_inhibitors.csv")
            print(f"    Output: results/experimental/mtb_inhibitor_summary.csv")
            print(f"    Figure: results/figures/experimental_pic50_distribution.png")
            print(f"    Figure: results/figures/scaffold_diversity_mtb.png")

    if 2 in selected_reqs and "df_trxb2" in results:
        df_t = results["df_trxb2"]
        if df_t is not None and len(df_t) > 0:
            top_nac = df_t[~df_t["Is Anticancer"]].head(1)
            print(f"\n  REQ 2 — DrugBank Screening:")
            print(f"    Drugs screened           : {len(df_t)}")
            print(f"    Non-anticancer drugs     : {(~df_t['Is Anticancer']).sum()}")
            if len(top_nac) > 0:
                print(f"    Top non-AC hit (TrxB2)  : {top_nac.iloc[0]['Drug Name']} "
                      f"(p={top_nac.iloc[0]['Predicted Probability']:.4f})")
            print(f"    Output: results/predictions/drugbank_trxb2_screening.csv")
            print(f"    Output: results/predictions/drugbank_multitarget_screening.csv")
            print(f"    Figure: results/figures/drugbank_screening_non_anticancer.png")
            print(f"    Figure: results/figures/drugbank_multitarget_heatmap.png")
            print(f"    Figure: results/figures/inhibitor_property_profile.png")
            print(f"    Figure: results/figures/anticancer_vs_nonac_scores.png")

    if 3 in selected_reqs and "df_safety" in results:
        df_s = results["df_safety"]
        if df_s is not None and len(df_s) > 0:
            tier_counts = df_s["Safety_Tier"].value_counts()
            print(f"\n  REQ 3 — Toxicity & Safety Screening:")
            print(f"    Compounds assessed       : {len(df_s)}")
            print(f"    ✅ Safe-Prioritised      : {tier_counts.get('✅ Safe-Prioritised', 0)}")
            print(f"    ⚠️  Caution              : {tier_counts.get('⚠️  Caution', 0)}")
            print(f"    🚫 Flagged (Unsafe)      : {tier_counts.get('🚫 Flagged (Unsafe)', 0)}")
            print(f"    Output: results/safety/extended_safety_profiles.csv")
            print(f"    Output: results/safety/binding_vs_safety_comparison.csv")
            print(f"    Figure: results/figures/extended_safety_heatmap.png")
            print(f"    Figure: results/figures/extended_safety_radar.png")
            print(f"    Figure: results/figures/final_tiered_ranking.png")
            print(f"    Figure: results/figures/efficacy_vs_safety_scatter.png")

    print(f"\n  Total elapsed time: {elapsed:.1f} seconds")
    print("\n  REUSED (UNCHANGED) MODULES:")
    print("    model.py, drug_features.py, protein_features.py,")
    print("    admet_filtering.py, polypharmacology.py,")
    print("    prediction.py, preprocessing.py, data_collection.py")
    print("\n  NEWLY CREATED MODULES:")
    print("    src/experimental_inhibitor_data.py  (Req 1)")
    print("    src/drugbank_screening.py           (Req 2)")
    print("    src/toxicity_safety_screening.py    (Req 3)")
    print("    run_professor_requirements.py       (Orchestrator)")
    print("═" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run professor requirements for AI Drug Repurposing Pipeline")
    parser.add_argument("--req", nargs="+", type=int, choices=[1, 2, 3],
                        default=[1, 2, 3], help="Which requirements to run (1, 2, 3 or combination)")
    args = parser.parse_args()
    selected = sorted(set(args.req))

    print("\n" + "█" * 70)
    print("█  AI-DRIVEN DRUG REPURPOSING — PROFESSOR REQUIREMENT ADDITIONS")
    print("█  Mycobacterium tuberculosis | DualEncoderDTI Pipeline")
    print(f"█  Running Requirements: {selected}")
    print("█" * 70)

    start = time.time()
    results = {}

    exp_df  = None
    df_trxb2 = None

    if 1 in selected:
        df_inhibitors, df_summary = run_requirement_1()
        results["inhibitors"] = df_inhibitors
        results["summary"]    = df_summary
        exp_df = df_inhibitors

    if 2 in selected:
        df_trxb2, df_all = run_requirement_2(exp_df=exp_df)
        results["df_trxb2"] = df_trxb2
        results["df_all"]   = df_all

    if 3 in selected:
        df_safety = run_requirement_3(df_trxb2=df_trxb2)
        results["df_safety"] = df_safety

    elapsed = time.time() - start
    print_completion_summary(selected, results, elapsed)


if __name__ == "__main__":
    main()

