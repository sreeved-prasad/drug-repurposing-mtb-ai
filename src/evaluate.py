import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_curve,
    precision_recall_curve
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")

def compute_dti_metrics(y_true, y_pred_prob, threshold=0.5):
    """
    Calculate ROC-AUC, PR-AUC, Accuracy, Precision, Recall, F1 score.
    """
    y_true = np.array(y_true)
    y_pred_prob = np.array(y_pred_prob)
    y_pred_bin = (y_pred_prob >= threshold).astype(int)
    
    roc_auc = roc_auc_score(y_true, y_pred_prob) if len(np.unique(y_true)) > 1 else 0.5
    pr_auc = average_precision_score(y_true, y_pred_prob) if len(np.unique(y_true)) > 1 else 0.5
    
    acc = accuracy_score(y_true, y_pred_bin)
    prec = precision_score(y_true, y_pred_bin, zero_division=0)
    rec = recall_score(y_true, y_pred_bin, zero_division=0)
    f1 = f1_score(y_true, y_pred_bin, zero_division=0)
    cm = confusion_matrix(y_true, y_pred_bin)
    
    return {
        "ROC-AUC": round(roc_auc, 4),
        "PR-AUC": round(pr_auc, 4),
        "Accuracy": round(acc, 4),
        "Precision": round(prec, 4),
        "Recall": round(rec, 4),
        "F1-Score": round(f1, 4),
        "Confusion_Matrix": cm.tolist()
    }

def plot_evaluation_curves(results_dict, fig_prefix="dti_evaluation"):
    """
    Generate ROC Curve, Precision-Recall Curve, and Confusion Matrix figures.
    """
    fig_dir = os.path.join(RESULTS_DIR, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # 1. ROC Curve
    ax_roc = axes[0]
    for model_name, res in results_dict.items():
        y_true = res["y_true"]
        y_prob = res["y_prob"]
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        auc = res["metrics"]["ROC-AUC"]
        ax_roc.plot(fpr, tpr, label=f"{model_name} (AUC = {auc:.3f})", lw=2)
        
    ax_roc.plot([0, 1], [0, 1], 'k--', label="Random Chance (0.50)")
    ax_roc.set_xlabel("False Positive Rate", fontsize=12)
    ax_roc.set_ylabel("True Positive Rate", fontsize=12)
    ax_roc.set_title("ROC Curves Comparison", fontsize=14, fontweight='bold')
    ax_roc.legend(loc="lower right")
    ax_roc.grid(True, alpha=0.3)
    
    # 2. Precision-Recall Curve
    ax_pr = axes[1]
    for model_name, res in results_dict.items():
        y_true = res["y_true"]
        y_prob = res["y_prob"]
        prec, rec, _ = precision_recall_curve(y_true, y_prob)
        pr_auc = res["metrics"]["PR-AUC"]
        ax_pr.plot(rec, prec, label=f"{model_name} (PR-AUC = {pr_auc:.3f})", lw=2)
        
    ax_pr.set_xlabel("Recall", fontsize=12)
    ax_pr.set_ylabel("Precision", fontsize=12)
    ax_pr.set_title("Precision-Recall Curves", fontsize=14, fontweight='bold')
    ax_pr.legend(loc="lower left")
    ax_pr.grid(True, alpha=0.3)
    
    plt.tight_layout()
    out_fig = os.path.join(fig_dir, f"{fig_prefix}_curves.png")
    plt.savefig(out_fig, dpi=300)
    plt.close()
    print(f"[Evaluation] Figures saved to: {out_fig}")
