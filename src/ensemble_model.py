import os
import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
try:
    from xgboost import XGBClassifier
except ImportError:
    print("[Ensemble] Warning: xgboost not installed. Please install xgboost.")
    XGBClassifier = None

from model import BaselineRFModel, DualEncoderDTI
from evaluate import compute_dti_metrics
from train import build_feature_tensors, train_pytorch_model

class EnsembleTrainer:
    def __init__(self, n_splits=3, random_state=42):
        self.n_splits = n_splits
        self.random_state = random_state
        self.meta_learner = LogisticRegression(class_weight='balanced')
        
    def _get_base_models(self):
        # We need a new instance of each model for each fold
        rf = RandomForestClassifier(n_estimators=100, random_state=self.random_state, n_jobs=-1)
        xgb = None
        if XGBClassifier is not None:
            xgb = XGBClassifier(
                n_estimators=200, 
                max_depth=6, 
                learning_rate=0.1, 
                subsample=0.8,
                random_state=self.random_state,
                n_jobs=-1,
                eval_metric="logloss"
            )
        return rf, xgb
        
    def train_and_evaluate(self, X_drug, X_prot, y, test_idx=None, X_drug_test=None, X_prot_test=None, y_test=None):
        """
        Train stacked ensemble using cross-validation.
        X_drug: (N, 2182)
        X_prot: (N, 684)
        """
        print(f"\n[Ensemble] Starting {self.n_splits}-fold Stacking Ensemble Training...")
        X_comb = np.hstack([X_drug, X_prot])
        
        kf = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
        
        # OOF arrays
        oof_rf = np.zeros(len(y))
        oof_xgb = np.zeros(len(y))
        oof_dti = np.zeros(len(y))
        
        for fold, (train_index, val_index) in enumerate(kf.split(X_comb, y)):
            print(f"  --- Fold {fold+1}/{self.n_splits} ---")
            
            X_c_tr, X_c_va = X_comb[train_index], X_comb[val_index]
            y_tr, y_va = y[train_index], y[val_index]
            
            X_d_tr, X_d_va = X_drug[train_index], X_drug[val_index]
            X_p_tr, X_p_va = X_prot[train_index], X_prot[val_index]
            
            rf, xgb = self._get_base_models()
            
            # Train RF
            print("    Training RF...")
            rf.fit(X_c_tr, y_tr)
            oof_rf[val_index] = rf.predict_proba(X_c_va)[:, 1]
            
            # Train XGB
            if xgb is not None:
                print("    Training XGBoost...")
                xgb.fit(X_c_tr, y_tr)
                oof_xgb[val_index] = xgb.predict_proba(X_c_va)[:, 1]
                
            # Train DTI
            print("    Training DualEncoderDTI...")
            # Use fewer epochs for fold training to speed up, or same epochs
            dl_model, preds = train_pytorch_model(X_d_tr, X_p_tr, y_tr, X_d_va, X_p_va, y_va, epochs=15)
            oof_dti[val_index] = preds
            
        print("\n[Ensemble] OOF Predictions Collected. Training Meta-Learner...")
        
        # Meta features
        if xgb is not None:
            OOF_meta = np.column_stack([oof_rf, oof_xgb, oof_dti])
            feature_names = ["RandomForest", "XGBoost", "DualEncoderDTI"]
        else:
            OOF_meta = np.column_stack([oof_rf, oof_dti])
            feature_names = ["RandomForest", "DualEncoderDTI"]
            
        self.meta_learner.fit(OOF_meta, y)
        
        print("\n[Ensemble] Meta-Learner Learned Weights:")
        for name, weight in zip(feature_names, self.meta_learner.coef_[0]):
            print(f"  {name}: {weight:.4f}")
        print(f"  Intercept: {self.meta_learner.intercept_[0]:.4f}")
        
        if test_idx is not None and X_drug_test is not None and X_prot_test is not None and y_test is not None:
            print("\n[Ensemble] Retraining Base Models on Full Training Data...")
            X_comb_test = np.hstack([X_drug_test, X_prot_test])
            
            rf, xgb = self._get_base_models()
            print("  Retraining RF...")
            rf.fit(X_comb, y)
            rf_test_preds = rf.predict_proba(X_comb_test)[:, 1]
            
            if xgb is not None:
                print("  Retraining XGBoost...")
                xgb.fit(X_comb, y)
                xgb_test_preds = xgb.predict_proba(X_comb_test)[:, 1]
            
            print("  Retraining DualEncoderDTI...")
            final_dti, dti_test_preds = train_pytorch_model(X_drug, X_prot, y, X_drug_test, X_prot_test, y_test, epochs=30)
            
            if xgb is not None:
                test_meta = np.column_stack([rf_test_preds, xgb_test_preds, dti_test_preds])
            else:
                test_meta = np.column_stack([rf_test_preds, dti_test_preds])
                
            ensemble_test_preds = self.meta_learner.predict_proba(test_meta)[:, 1]
            
            ens_metrics = compute_dti_metrics(y_test, ensemble_test_preds)
            print("\n================ ENSEMBLE TEST PERFORMANCE ================\n")
            print(f"ROC-AUC: {ens_metrics['ROC-AUC']:.4f}")
            print(f"PR-AUC:  {ens_metrics['PR-AUC']:.4f}")
            print(f"F1-Score:{ens_metrics['F1-Score']:.4f}")
            
            return ens_metrics, ensemble_test_preds, final_dti
        
        return None, None, None

if __name__ == "__main__":
    print("Testing Ensemble Module (Dummy Data)...")
    np.random.seed(42)
    N = 100
    X_d = np.random.randn(N, 2182).astype(np.float32)
    X_p = np.random.randn(N, 684).astype(np.float32)
    y = np.random.randint(0, 2, N).astype(np.float32)
    
    trainer = EnsembleTrainer(n_splits=2)
    # mock train_pytorch_model to bypass actual training in test
    import train
    original_train = train.train_pytorch_model
    def mock_train(Xdtr, Xptr, ytr, Xdte, Xpte, yte, epochs=30, batch_size=32, lr=1e-3):
        return DualEncoderDTI(2182, 684), np.random.rand(len(yte))
    train.train_pytorch_model = mock_train
    
    try:
        trainer.train_and_evaluate(X_d, X_p, y)
    finally:
        train.train_pytorch_model = original_train
