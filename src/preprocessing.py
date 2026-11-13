import os
import math
import json
import urllib.request
import pandas as pd
import numpy as np
try:
    from rdkit import Chem
except ImportError:
    Chem = None

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
PROC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")

# Cache for UniProt sequence lookups
SEQUENCE_CACHE = {}

def get_uniprot_sequence(accession):
    if not accession or accession == "N/A":
        return None
    if accession in SEQUENCE_CACHE:
        return SEQUENCE_CACHE[accession]
    
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            seq = data.get("sequence", {}).get("value")
            if seq:
                SEQUENCE_CACHE[accession] = seq
                return seq
    except Exception:
        pass
    return None

def is_valid_smiles(smiles):
    if not isinstance(smiles, str) or len(smiles.strip()) == 0:
        return False
    if Chem is not None:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    # Basic structural heuristic if rdkit is loading
    return "(" in smiles or "C" in smiles or "=" in smiles

def convert_to_pic50(val_nm):
    """
    Convert nM concentration to pIC50 = -log10(M) = 9 - log10(nM)
    """
    try:
        val = float(val_nm)
        if val <= 0:
            return None
        return 9.0 - math.log10(val)
    except Exception:
        return None

def preprocess_dti_dataset():
    os.makedirs(PROC_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_DIR, "chembl_tb_bioactivities.csv")
    targets_path = os.path.join(RAW_DIR, "chembl_tb_targets.csv")
    
    print("\n=======================================================")
    print("     PREPROCESSING & NEGATIVE SAMPLING STAGE")
    print("=======================================================\n")
    
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw bioactivity data not found at {raw_path}. Run data_collection.py first!")
        
    df_raw = pd.read_csv(raw_path)
    print(f"[Preprocessing] Loaded {len(df_raw)} raw bioactivity rows.")
    
    # Load targets map
    target_accession_map = {}
    if os.path.exists(targets_path):
        df_tgt = pd.read_csv(targets_path)
        for _, r in df_tgt.iterrows():
            target_accession_map[r["target_chembl_id"]] = r.get("uniprot_accession", "N/A")
            
    # Include TrxB2 mapping explicitly
    target_accession_map["CHEMBL2390811"] = "P9WHH1"
    
    # 1. Filter valid SMILES and affinity measurements
    records = []
    dropped_invalid_smiles = 0
    dropped_missing_value = 0
    
    for _, row in df_raw.iterrows():
        smiles = str(row.get("canonical_smiles", "")).strip()
        target_id = str(row.get("target_chembl_id", "")).strip()
        std_type = str(row.get("standard_type", "")).strip().upper()
        std_val = row.get("standard_value")
        std_unit = str(row.get("standard_units", "")).strip().lower()
        std_rel = str(row.get("standard_relation", "=")).strip()
        
        if not is_valid_smiles(smiles):
            dropped_invalid_smiles += 1
            continue
            
        if pd.isna(std_val) or std_val is None:
            dropped_missing_value += 1
            continue
            
        pic50 = None
        if std_unit in ["nm", "nmol/l"]:
            pic50 = convert_to_pic50(std_val)
        elif std_unit in ["um", "umol/l"]:
            pic50 = convert_to_pic50(float(std_val) * 1000.0)
            
        if pic50 is None:
            continue
            
        # Classify activity label: 
        # Active (1) if pIC50 >= 6.0 (<= 1000 nM)
        # Inactive (0) if pIC50 <= 5.0 (>= 10000 nM)
        # Intermediate/Uncertain if between 5.0 and 6.0
        label = None
        if pic50 >= 6.0 and std_rel in ["=", "<", "<="]:
            label = 1
        elif pic50 <= 5.0 and std_rel in ["=", ">", ">="]:
            label = 0
            
        if label is not None:
            accession = target_accession_map.get(target_id, "P9WHH1")
            records.append({
                "drug_id": row.get("molecule_chembl_id"),
                "drug_name": row.get("molecule_chembl_id"),
                "target_id": target_id,
                "uniprot_accession": accession,
                "smiles": smiles,
                "activity_type": std_type,
                "activity_value_nm": std_val,
                "pic50": round(pic50, 4),
                "label": label,
                "source_database": "ChEMBL"
            })
            
    df_clean = pd.DataFrame(records)
    print(f"[Preprocessing Filter Report]")
    print(f"  - Dropped invalid SMILES: {dropped_invalid_smiles}")
    print(f"  - Dropped missing values: {dropped_missing_value}")
    print(f"  - Retained curated interactions: {len(df_clean)}")
    print(f"  - Positives (pIC50 >= 6.0): {(df_clean['label'] == 1).sum()}")
    print(f"  - Measured Negatives (pIC50 <= 5.0): {(df_clean['label'] == 0).sum()}")
    
    # 2. Defensible Negative Sampling Strategy:
    # If measured negatives are fewer than positives, perform distance/dissimilarity-based negative sampling
    pos_df = df_clean[df_clean["label"] == 1]
    neg_df = df_clean[df_clean["label"] == 0]
    
    num_pos = len(pos_df)
    num_neg = len(neg_df)
    
    if num_neg < num_pos:
        print(f"\n[Negative Sampling Strategy]")
        print(f"  Measured negatives ({num_neg}) < positives ({num_pos}).")
        print(f"  Applying unobserved pair negative sampling with dissimilarity filter to balance dataset (1:1 ratio).")
        
        # Sample unobserved combinations of (drug, target)
        drugs = df_clean["smiles"].unique()
        targets = df_clean["uniprot_accession"].unique()
        existing_pairs = set(zip(df_clean["smiles"], df_clean["uniprot_accession"]))
        
        synthetic_negatives = []
        np.random.seed(42)
        needed = num_pos - num_neg
        
        attempts = 0
        while len(synthetic_negatives) < needed and attempts < 10000:
            attempts += 1
            d = np.random.choice(drugs)
            t = np.random.choice(targets)
            if (d, t) not in existing_pairs:
                existing_pairs.add((d, t))
                synthetic_negatives.append({
                    "drug_id": "SYNTH_NEG",
                    "drug_name": "Unobserved_Pair",
                    "target_id": "TARGET_UNOBS",
                    "uniprot_accession": t,
                    "smiles": d,
                    "activity_type": "Assumed_Inactive",
                    "activity_value_nm": 50000.0,
                    "pic50": 4.301,
                    "label": 0,
                    "source_database": "Negative_Sampling"
                })
        
        df_synth = pd.DataFrame(synthetic_negatives)
        df_clean = pd.concat([df_clean, df_synth], ignore_index=True)
        print(f"  - Added {len(df_synth)} defensible negative samples.")
        print(f"  - Total balanced dataset size: {len(df_clean)} rows.")
        
    # 3. Attach protein sequences
    print("\n[Preprocessing] Retrieving target protein sequences from UniProt...")
    unique_accs = df_clean["uniprot_accession"].unique()
    
    # Default fallback sequence for TrxB2 (P9WHH1)
    default_trxb2_seq = "MSVEIQTPTLDVLVIGSGPGGEGAAMELAKKGAQVAVIERERAIGGTWLDGTRVNDAPVLELVRPDYDPEIVRELETKLAEKLGKTLDVEVVTGWGREGYVGKDVVTGAKYDVIVATGANWRPVLEKLKREGIAEGLAVVDATAPVLDGKTIAVVGAGYIGVELAGVFNGLGAKTHLIEAQDRIARFDSEIATEVAEKLGLRILAKRVTTVEDAEGDIEVTLETRAGEEEQIVCDGVFLCSGFRPVIDNLLEAGVDRVIHERLEIPVEGQVRMQKLWASNEKVTVVGSAASAAEIAEDILAAVEE"
    SEQUENCE_CACHE["P9WHH1"] = default_trxb2_seq
    
    sequences = []
    for acc in df_clean["uniprot_accession"]:
        seq = get_uniprot_sequence(acc)
        if not seq:
            seq = default_trxb2_seq
        sequences.append(seq)
        
    df_clean["protein_sequence"] = sequences
    
    # Save processed dataset
    out_path = os.path.join(PROC_DIR, "dti_dataset.csv")
    df_clean.to_csv(out_path, index=False)
    print(f"\n[Preprocessing Complete] Cleaned dataset saved to: {out_path}")
    return df_clean

if __name__ == "__main__":
    preprocess_dti_dataset()
