import os
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
try:
    import shap
except ImportError:
    print("[Explainability] Warning: shap not installed. Please install shap for RF interpretability.")

from drug_features import get_drug_encoding
from protein_features import get_protein_encoding
from model import DualEncoderDTI, BaselineRFModel

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

class ExplainabilityModule:
    def __init__(self, dti_model, rf_model=None):
        self.dti_model = dti_model
        self.rf_model = rf_model
        self.device = next(dti_model.parameters()).device

    def integrated_gradients(self, drug_x, protein_x, baseline_d=None, baseline_p=None, steps=50):
        """
        Compute Integrated Gradients for the DualEncoderDTI model.
        drug_x: (1, 2182)
        protein_x: (1, 684)
        """
        self.dti_model.eval()
        if baseline_d is None:
            baseline_d = torch.zeros_like(drug_x)
        if baseline_p is None:
            baseline_p = torch.zeros_like(protein_x)
            
        drug_x = drug_x.to(self.device)
        protein_x = protein_x.to(self.device)
        baseline_d = baseline_d.to(self.device)
        baseline_p = baseline_p.to(self.device)
        
        scaled_d = [baseline_d + (float(i) / steps) * (drug_x - baseline_d) for i in range(0, steps + 1)]
        scaled_p = [baseline_p + (float(i) / steps) * (protein_x - baseline_p) for i in range(0, steps + 1)]
        
        scaled_d = torch.cat(scaled_d, dim=0).requires_grad_()
        scaled_p = torch.cat(scaled_p, dim=0).requires_grad_()
        
        preds = self.dti_model(scaled_d, scaled_p)
        
        self.dti_model.zero_grad()
        preds.sum().backward()
        
        grads_d = scaled_d.grad
        grads_p = scaled_p.grad
        
        avg_grads_d = grads_d[:-1].mean(dim=0, keepdim=True)
        avg_grads_p = grads_p[:-1].mean(dim=0, keepdim=True)
        
        ig_d = (drug_x - baseline_d) * avg_grads_d
        ig_p = (protein_x - baseline_p) * avg_grads_p
        
        return ig_d.detach().cpu().numpy().flatten(), ig_p.detach().cpu().numpy().flatten()
        
    def render_atom_heatmap(self, smiles, feature_importances, filename="atom_heatmap.png"):
        """
        Map ECFP4 attributions back to atoms and render a heatmap.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
            
        # extract ECFP4 importances (first 2048 dims)
        ecfp4_imp = feature_importances[:2048]
        
        bit_info = {}
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048, bitInfo=bit_info)
        
        atom_scores = np.zeros(mol.GetNumAtoms())
        
        for bit, atoms_radii in bit_info.items():
            score = ecfp4_imp[bit]
            for atom_idx, radius in atoms_radii:
                # Distribute score
                if radius == 0:
                    atom_scores[atom_idx] += score
                else:
                    # RDKit environment finding
                    env = Chem.FindAtomEnvironmentOfRadiusN(mol, radius, atom_idx)
                    amap = {}
                    submol = Chem.PathToSubmol(mol, env, atomMap=amap)
                    for a_idx in amap.keys():
                        atom_scores[a_idx] += score / max(1, len(amap))
                        
        # Normalize scores for colors
        max_score = np.max(np.abs(atom_scores))
        if max_score == 0: max_score = 1
        
        atom_colors = {}
        for i in range(mol.GetNumAtoms()):
            val = atom_scores[i] / max_score
            # Red for positive, blue for negative
            if val > 0:
                atom_colors[i] = (1.0, 1.0 - val, 1.0 - val)
            else:
                val = abs(val)
                atom_colors[i] = (1.0 - val, 1.0 - val, 1.0)
                
        d2d = rdMolDraw2D.MolDraw2DCairo(400, 400)
        rdMolDraw2D.PrepareAndDrawMolecule(d2d, mol, highlightAtoms=list(atom_colors.keys()), highlightAtomColors=atom_colors)
        d2d.FinishDrawing()
        
        out_path = os.path.join(FIGURES_DIR, filename)
        with open(out_path, "wb") as f:
            f.write(d2d.GetDrawingText())
            
        return out_path

    def plot_protein_attribution(self, ig_p, filename="protein_attribution.png"):
        """
        Plot bar chart for protein feature attributions.
        """
        # Protein features: 684 dims ( ESM-2 (320) + AAC (20) + Conjoint Triads (343) + Length (1) )
        if len(ig_p) != 684:
            print("[Explainability] Expected 684 protein features.")
            return None
            
        esm_imp = np.sum(np.abs(ig_p[:320]))
        aac_imp = np.sum(np.abs(ig_p[320:340]))
        ct_imp = np.sum(np.abs(ig_p[340:683]))
        len_imp = np.abs(ig_p[683])
        
        labels = ['ESM-2', 'AAC', 'Conjoint Triads', 'Length']
        vals = [esm_imp, aac_imp, ct_imp, len_imp]
        
        plt.figure(figsize=(8, 5))
        plt.bar(labels, vals, color=['#4C72B0', '#DD8452', '#55A868', '#C44E52'])
        plt.title("Protein Feature Category Attributions (Integrated Gradients)")
        plt.ylabel("Absolute Attribution Sum")
        plt.tight_layout()
        out_path = os.path.join(FIGURES_DIR, filename)
        plt.savefig(out_path, dpi=300)
        plt.close()
        return out_path

    def get_rf_shap_values(self, X_sample):
        """
        Compute SHAP values for the Random Forest model.
        """
        if self.rf_model is None or not hasattr(self.rf_model, 'model'):
            return None
            
        try:
            explainer = shap.TreeExplainer(self.rf_model.model)
            shap_values = explainer.shap_values(X_sample)
            return shap_values
        except Exception as e:
            print(f"[Explainability] Error computing SHAP: {e}")
            return None


if __name__ == "__main__":
    print("Testing Explainability Module...")
    # Mock data
    d_x = torch.randn(1, 2182)
    p_x = torch.randn(1, 684)
    model = DualEncoderDTI(drug_dim=2182, protein_dim=684)
    model.eval()
    
    explainer = ExplainabilityModule(model)
    ig_d, ig_p = explainer.integrated_gradients(d_x, p_x)
    
    print(f"IG Drug Attributions Shape: {ig_d.shape}")
    print(f"IG Protein Attributions Shape: {ig_p.shape}")
    
    test_smiles = "CC(=O)OCC1C(C(C(C(O1)S[Au]P(CC)(CC)CC)OC(=O)C)OC(=O)C)OC(=O)C" # Auranofin
    heatmap_path = explainer.render_atom_heatmap(test_smiles, ig_d)
    print(f"Rendered Atom Heatmap: {heatmap_path}")
    
    p_attr_path = explainer.plot_protein_attribution(ig_p)
    print(f"Rendered Protein Attribution: {p_attr_path}")
