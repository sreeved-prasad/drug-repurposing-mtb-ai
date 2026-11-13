import os
import json
import csv
import urllib.request
import urllib.parse
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def get_uniprot_target_info(accession="P9WHH1"):
    """
    Fetch verified target metadata from UniProt REST API.
    """
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.json"
    print(f"[UniProt] Fetching target details for accession {accession}...")
    try:
        data = fetch_json(url)
        gene = data.get("genes", [{}])[0].get("geneName", {}).get("value", "trxB2")
        protein_name = data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "Thioredoxin reductase")
        organism = data.get("organism", {}).get("scientificName", "Mycobacterium tuberculosis")
        sequence = data.get("sequence", {}).get("value", "")
        
        # PDB xrefs
        pdbs = [ref["id"] for ref in data.get("dbReferences", []) if ref.get("type") == "PDB"]
        
        info = {
            "uniprot_id": accession,
            "gene": gene,
            "protein_name": protein_name,
            "organism": organism,
            "sequence_length": len(sequence),
            "sequence": sequence,
            "pdb_structures": pdbs
        }
        print(f"[UniProt] Retained {protein_name} ({gene}) | Seq Len: {len(sequence)} | PDBs: {pdbs[:5]}")
        return info
    except Exception as e:
        print(f"[UniProt] Error fetching {accession}: {e}")
        return None

def fetch_chembl_tb_targets(organism="Mycobacterium tuberculosis"):
    """
    Retrieve single-protein targets for specified organism from ChEMBL REST API.
    """
    print(f"[ChEMBL] Searching targets for organism: '{organism}'...")
    encoded_org = urllib.parse.quote(organism)
    url = f"https://www.ebi.ac.uk/chembl/api/data/target.json?organism={encoded_org}&target_type=SINGLE%20PROTEIN&limit=100"
    
    targets = []
    try:
        res = fetch_json(url)
        raw_targets = res.get("targets", [])
        print(f"[ChEMBL] Retrieved {len(raw_targets)} single-protein targets for {organism}.")
        for t in raw_targets:
            target_chembl_id = t.get("target_chembl_id")
            pref_name = t.get("pref_name")
            target_components = t.get("target_components", [])
            accession = "N/A"
            if target_components and len(target_components) > 0:
                accession = target_components[0].get("accession", "N/A")
            targets.append({
                "target_chembl_id": target_chembl_id,
                "target_name": pref_name,
                "uniprot_accession": accession,
                "organism": organism
            })
    except Exception as e:
        print(f"[ChEMBL] Error retrieving targets: {e}")
    return pd.DataFrame(targets)

def fetch_chembl_bioactivities_for_target(target_chembl_id, limit=300):
    """
    Fetch bioactivity measurements (IC50, Ki, Kd, EC50) for a given target ChEMBL ID.
    """
    url = f"https://www.ebi.ac.uk/chembl/api/data/activity.json?target_chembl_id={target_chembl_id}&limit={limit}"
    activities = []
    try:
        res = fetch_json(url)
        acts = res.get("activities", [])
        for a in acts:
            activities.append({
                "molecule_chembl_id": a.get("molecule_chembl_id"),
                "canonical_smiles": a.get("canonical_smiles"),
                "target_chembl_id": target_chembl_id,
                "standard_type": a.get("standard_type"),
                "standard_relation": a.get("standard_relation"),
                "standard_value": a.get("standard_value"),
                "standard_units": a.get("standard_units"),
                "assay_description": a.get("assay_description"),
                "assay_type": a.get("assay_type")
            })
    except Exception as e:
        print(f"[ChEMBL] Error fetching bioactivities for {target_chembl_id}: {e}")
    return activities

def fetch_auranofin_chembl_info():
    """
    Fetch Auranofin compound metadata & structure from ChEMBL.
    """
    url = "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL1366.json"
    print("[ChEMBL] Fetching Auranofin metadata (CHEMBL1366)...")
    try:
        data = fetch_json(url)
        smiles = data.get("molecule_structures", {}).get("canonical_smiles", "CC(=O)OCC1C(C(C(C(O1)S[Au]P(CC)(CC)CC)OC(=O)C)OC(=O)C)OC(=O)C")
        pref_name = data.get("pref_name", "AURANOFIN")
        chembl_id = data.get("molecule_chembl_id", "CHEMBL1366")
        info = {
            "chembl_id": chembl_id,
            "drug_name": pref_name,
            "smiles": smiles,
            "indication": "Rheumatoid Arthritis (FDA Approved 1985)"
        }
        print(f"[ChEMBL] Auranofin SMILES: {smiles}")
        return info
    except Exception as e:
        print(f"[ChEMBL] Error fetching Auranofin info: {e}")
        # Default canonical SMILES fallback
        return {
            "chembl_id": "CHEMBL1366",
            "drug_name": "AURANOFIN",
            "smiles": "CC(=O)OCC1C(C(C(C(O1)S[Au]P(CC)(CC)CC)OC(=O)C)OC(=O)C)OC(=O)C",
            "indication": "Rheumatoid Arthritis (FDA Approved 1985)"
        }

def collect_all_data(disease_name="Tuberculosis"):
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"\n=======================================================")
    print(f"       DATA COLLECTION STAGE: {disease_name.upper()}")
    print(f"=======================================================\n")
    
    # 1. Fetch Target details for TrxB2 (P9WHH1)
    trxb2_info = get_uniprot_target_info("P9WHH1")
    with open(os.path.join(DATA_DIR, "trxb2_uniprot_info.json"), "w") as f:
        json.dump(trxb2_info, f, indent=2)
        
    # 2. Fetch Auranofin details
    auranofin_info = fetch_auranofin_chembl_info()
    with open(os.path.join(DATA_DIR, "auranofin_chembl_info.json"), "w") as f:
        json.dump(auranofin_info, f, indent=2)
        
    # 3. Retrieve M. tuberculosis Targets from ChEMBL
    targets_df = fetch_chembl_tb_targets("Mycobacterium tuberculosis")
    targets_df.to_csv(os.path.join(DATA_DIR, "chembl_tb_targets.csv"), index=False)
    
    # 4. Collect bioactivities for top targets (including TrxB2 CHEMBL2390811, InhA CHEMBL1828, DprE1 CHEMBL2094254, etc.)
    all_activities = []
    target_ids = list(targets_df["target_chembl_id"].dropna().unique()[:15])
    if "CHEMBL2390811" not in target_ids:
        target_ids.append("CHEMBL2390811")
        
    print(f"\n[ChEMBL] Collecting bioactivities for {len(target_ids)} key Mycobacterium tuberculosis targets...")
    for tid in target_ids:
        acts = fetch_chembl_bioactivities_for_target(tid, limit=200)
        print(f"  Target {tid}: fetched {len(acts)} bioactivity records.")
        all_activities.extend(acts)
        
    act_df = pd.DataFrame(all_activities)
    act_df.to_csv(os.path.join(DATA_DIR, "chembl_tb_bioactivities.csv"), index=False)
    print(f"\n[Data Collection Complete] Total raw bioactivities collected: {len(act_df)}")
    return act_df

if __name__ == "__main__":
    collect_all_data("Tuberculosis")
