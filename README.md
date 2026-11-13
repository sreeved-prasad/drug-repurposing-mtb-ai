# AI-Driven Drug Repurposing Pipeline

An end-to-end, reproducible computational drug repurposing framework leveraging public database retrieval (ChEMBL, BindingDB, UniProt, RCSB PDB), Machine Learning / Deep Learning Drug–Target Interaction (DTI) models, candidate ranking, target verification, and molecular docking (AutoDock Vina).

## Primary Test Case
- **Disease:** Tuberculosis (*Mycobacterium tuberculosis*)
- **Primary Target:** Thioredoxin Reductase TrxB2 (`trxB2` / `Rv3913`, UniProt **P9WHH1**, PDB **2A87**)
- **Validation Drug Candidate:** Auranofin (FDA Approved for Rheumatoid Arthritis)

## Workflow
1. **Target Identification:** Disease input → disease-associated biological target retrieval.
2. **Database Scraping & Data Curation:** Query ChEMBL/BindingDB bioactivities, normalize affinity metrics ($pIC_{50}$), perform negative sampling.
3. **Molecular Representation:**
   - **Drugs:** 2048-bit Morgan Fingerprints (ECFP4) + Physicochemical descriptors (RDKit).
   - **Proteins:** Amino Acid Composition (AAC), Conjoint Triad features.
4. **Model Architecture:** Baseline ML (Random Forest) vs Deep Neural Network (Dual Encoder MLP / CNN).
5. **Data Splitting & Evaluation:** Random, Cold-Drug, Target-Cold splits evaluated on ROC-AUC, PR-AUC, Precision, Recall, F1.
6. **Candidate Prioritization:** FDA-approved drug collection screening against *M. tuberculosis* targets.
7. **Docking Validation:** PDB 2A87 preparation, ligand grid definition, AutoDock Vina binding energy scoring ($\text{kcal/mol}$).

## Quick Start
```bash
pip install -r requirements.txt
python src/data_collection.py
python src/preprocessing.py
python src/train.py
python src/prediction.py
python src/docking.py
```
