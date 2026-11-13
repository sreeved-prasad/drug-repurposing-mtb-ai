import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from drug_features import get_drug_encoding
from protein_features import get_protein_encoding
from model import BaselineRFModel, DualEncoderDTI
from evaluate import compute_dti_metrics, plot_evaluation_curves

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
FEAT_CACHE = os.path.join(DATA_DIR, "features_cache_stage2.npz")

def build_feature_tensors(df):
    """
    Extract Stage 2 molecular (2182-dim: Morgan ECFP4 + Descriptors + PyG GNN 3D)
    and protein (684-dim: ESM-2 + AAC + Conjoint Triad + Length) feature matrices.
    """
    if os.path.exists(FEAT_CACHE):
        try:
            cached = np.load(FEAT_CACHE)
            print(f"[Train] Loaded cached Stage 2 feature tensors from {FEAT_CACHE}")
            return cached["X_drug"], cached["X_prot"], cached["y"]
        except Exception:
            pass
            
    print(f"[Train] Extracting Stage 2 molecular and ESM-2 protein features for {len(df)} samples...")
    drug_vecs = []
    protein_vecs = []
    
    for idx, (_, r) in enumerate(df.iterrows()):
        d_enc = get_drug_encoding(r["smiles"], mode="combined")
        p_enc = get_protein_encoding(r["protein_sequence"], mode="combined")
        drug_vecs.append(d_enc)
        protein_vecs.append(p_enc)
        if (idx + 1) % 150 == 0 or (idx + 1) == len(df):
            print(f"  Featurized {idx + 1}/{len(df)} samples...")
            
    X_drug = np.array(drug_vecs, dtype=np.float32)
    X_prot = np.array(protein_vecs, dtype=np.float32)
    y = np.array(df["label"].values, dtype=np.float32)
    
    try:
        np.savez_compressed(FEAT_CACHE, X_drug=X_drug, X_prot=X_prot, y=y)
        print(f"[Train] Persisted Stage 2 feature tensors to {FEAT_CACHE}")
    except Exception as e:
        print(f"[Train] Warning: Could not cache features: {e}")
        
    return X_drug, X_prot, y

def split_dataset(df, split_type="random", test_size=0.2, seed=42):
    """
    Perform Random, Drug-Cold, or Target-Cold dataset splitting.
    """
    np.random.seed(seed)
    indices = np.arange(len(df))
    
    if split_type == "random":
        train_idx, test_idx = train_test_split(indices, test_size=test_size, random_state=seed, stratify=df["label"])
        
    elif split_type == "drug_cold":
        unique_drugs = df["smiles"].unique()
        train_drugs, test_drugs = train_test_split(unique_drugs, test_size=test_size, random_state=seed)
        train_idx = df[df["smiles"].isin(train_drugs)].index.values
        test_idx = df[df["smiles"].isin(test_drugs)].index.values
        
    elif split_type == "target_cold":
        unique_targets = df["uniprot_accession"].unique()
        if len(unique_targets) <= 2:
            print("[Warning] Target-Cold split falling back to Random split due to limited target diversity.")
            train_idx, test_idx = train_test_split(indices, test_size=test_size, random_state=seed)
        else:
            train_targets, test_targets = train_test_split(unique_targets, test_size=test_size, random_state=seed)
            train_idx = df[df["uniprot_accession"].isin(train_targets)].index.values
            test_idx = df[df["uniprot_accession"].isin(test_targets)].index.values
            
    return train_idx, test_idx

def train_pytorch_model(X_d_tr, X_p_tr, y_tr, X_d_te, X_p_te, y_te, epochs=30, batch_size=32, lr=1e-3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[PyTorch DTI] Training Stage 2 DualEncoderDTI on device: {device}")
    print(f"  Drug Feature Dim: {X_d_tr.shape[1]} | Protein Feature Dim: {X_p_tr.shape[1]}")
    
    train_ds = TensorDataset(torch.tensor(X_d_tr), torch.tensor(X_p_tr), torch.tensor(y_tr))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    
    model = DualEncoderDTI(drug_dim=X_d_tr.shape[1], protein_dim=X_p_tr.shape[1]).to(device)
    criterion = nn.BCELoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for d_b, p_b, y_b in train_loader:
            d_b, p_b, y_b = d_b.to(device), p_b.to(device), y_b.to(device)
            optimizer.zero_grad()
            pred = model(d_b, p_b)
            loss = criterion(pred, y_b)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(y_b)
            
        scheduler.step()
        avg_loss = total_loss / len(train_ds)
        if epoch % 5 == 0 or epoch == epochs:
            print(f"  Epoch {epoch:02d}/{epochs:02d} | Train Loss: {avg_loss:.4f}")
            
    model.eval()
    with torch.no_grad():
        d_te_t = torch.tensor(X_d_te).to(device)
        p_te_t = torch.tensor(X_p_te).to(device)
        preds = model(d_te_t, p_te_t).cpu().numpy()
        
    return model, preds

def run_training_pipeline(split_type="random", use_ensemble=False):
    print(f"\n=======================================================")
    print(f"      STAGE 2 MODEL TRAINING & EVALUATION ({split_type.upper()} SPLIT)")
    print(f"      Features: ESM-2 (684d) + PyG GNN 3D (2182d)")
    print(f"=======================================================\n")
    
    data_path = os.path.join(DATA_DIR, "dti_dataset.csv")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed dataset missing at {data_path}")
        
    df = pd.read_csv(data_path)
    X_drug, X_prot, y = build_feature_tensors(df)
    
    train_idx, test_idx = split_dataset(df, split_type=split_type, test_size=0.2, seed=42)
    print(f"[Data Split] Train set size: {len(train_idx)} | Test set size: {len(test_idx)}")
    
    X_d_tr, X_p_tr, y_tr = X_drug[train_idx], X_prot[train_idx], y[train_idx]
    X_d_te, X_p_te, y_te = X_drug[test_idx], X_prot[test_idx], y[test_idx]
    
    # Combined feature matrix for Baseline RF Model
    X_comb_tr = np.hstack([X_d_tr, X_p_tr])
    X_comb_te = np.hstack([X_d_te, X_p_te])
    
    # 1. Baseline Model: Random Forest
    print("\n--- Training Baseline Model: Random Forest ---")
    rf = BaselineRFModel(n_estimators=100, random_state=42)
    rf.fit(X_comb_tr, y_tr)
    rf_probs = rf.predict_proba(X_comb_te)
    rf_metrics = compute_dti_metrics(y_te, rf_probs)
    
    # 2. Deep Learning Model: Stage 2 DualEncoderDTI
    print("\n--- Training Deep Learning Model: DualEncoderDTI (Cross-Attention + pLM + GNN) ---")
    dl_model, dl_probs = train_pytorch_model(X_d_tr, X_p_tr, y_tr, X_d_te, X_p_te, y_te, epochs=30)
    dl_metrics = compute_dti_metrics(y_te, dl_probs)
    
    # Summary Table
    summary = pd.DataFrame([
        {"Model": "Random Forest Baseline (Stage 2 Features)", **rf_metrics},
        {"Model": "DualEncoderDTI (Cross-Attention + pLM + GNN)", **dl_metrics}
    ])
    
    print(f"\n================ MODEL PERFORMANCE ({split_type.upper()} SPLIT) ================\n")
    print(summary[["Model", "ROC-AUC", "PR-AUC", "Accuracy", "Precision", "Recall", "F1-Score"]].to_string(index=False))
    
    # Save results
    metrics_dir = os.path.join(RESULTS_DIR, "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    summary.to_csv(os.path.join(metrics_dir, f"model_comparison_{split_type}.csv"), index=False)
    
    # Plot evaluation curves
    eval_dict = {
        "Random Forest": {"y_true": y_te, "y_prob": rf_probs, "metrics": rf_metrics},
        "DualEncoderDTI (Stage 2)": {"y_true": y_te, "y_prob": dl_probs, "metrics": dl_metrics}
    }
    plot_evaluation_curves(eval_dict, fig_prefix=f"dti_{split_type}")
    
    # Save trained PyTorch model checkpoint
    models_dir = os.path.join(RESULTS_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)
    model_checkpoint_path = os.path.join(models_dir, "dual_encoder_dti.pt")
    torch.save(dl_model.state_dict(), model_checkpoint_path)
    print(f"\n[Model Saved] Upgraded Stage 2 PyTorch checkpoint saved to: {model_checkpoint_path}")
    
    if use_ensemble:
        from ensemble_model import EnsembleTrainer
        import pickle
        trainer = EnsembleTrainer(n_splits=3)
        ens_metrics, ens_preds, final_dti = trainer.train_and_evaluate(
            X_d_tr, X_p_tr, y_tr, test_idx=test_idx, X_drug_test=X_d_te, X_prot_test=X_p_te, y_test=y_te
        )
        if ens_metrics:
            summary = pd.DataFrame([
                {"Model": "Random Forest Baseline (Stage 2 Features)", **rf_metrics},
                {"Model": "DualEncoderDTI (Cross-Attention + pLM + GNN)", **dl_metrics},
                {"Model": "Stage 3 Stacking Ensemble (RF + XGB + DTI)", **ens_metrics}
            ])
            print(f"\n================ MODEL PERFORMANCE ({split_type.upper()} SPLIT) ================\n")
            print(summary[["Model", "ROC-AUC", "PR-AUC", "Accuracy", "Precision", "Recall", "F1-Score"]].to_string(index=False))
            
            with open(os.path.join(models_dir, "ensemble_stage3.pkl"), "wb") as f:
                pickle.dump(trainer.meta_learner, f)
            print(f"\n[Model Saved] Stage 3 Ensemble meta-learner saved.")
            
            # Update eval_dict with ensemble
            eval_dict["Stage 3 Ensemble"] = {"y_true": y_te, "y_prob": ens_preds, "metrics": ens_metrics}
            plot_evaluation_curves(eval_dict, fig_prefix=f"dti_{split_type}_ensemble")
            
    return dl_model, summary

if __name__ == "__main__":
    import sys
    split = "drug_cold" if "drug_cold" in sys.argv else "random"
    use_ensemble = "--ensemble" in sys.argv
    run_training_pipeline(split, use_ensemble=use_ensemble)
