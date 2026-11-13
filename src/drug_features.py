import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors

try:
    from torch_geometric.data import Data, Batch
    from torch_geometric.nn import GCNConv, global_mean_pool, global_max_pool
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "models")
GNN_WEIGHTS_PATH = os.path.join(MODELS_DIR, "molecular_gnn_encoder.pt")

# Standard atomic mapping for drug-like and organometallic compounds
ATOM_LIST = ['C', 'N', 'O', 'S', 'P', 'F', 'Cl', 'Br', 'I', 'Au', 'Other']

def get_atom_features(atom, pos_3d=None, centroid_3d=None):
    """
    18-dimensional atom feature vector encoding topological and 3D spatial properties.
    """
    symbol = atom.GetSymbol()
    one_hot_symbol = [1.0 if symbol == a else 0.0 for a in ATOM_LIST[:-1]]
    if sum(one_hot_symbol) == 0:
        one_hot_symbol.append(1.0) # 'Other'
    else:
        one_hot_symbol.append(0.0)
        
    degree = float(atom.GetTotalDegree())
    formal_charge = float(atom.GetFormalCharge())
    is_aromatic = 1.0 if atom.GetIsAromatic() else 0.0
    num_hs = float(atom.GetTotalNumHs())
    is_in_ring = 1.0 if atom.IsInRing() else 0.0
    mass = atom.GetMass() / 100.0
    
    # 3D radial distance from molecular centroid
    radial_dist = 0.0
    if pos_3d is not None and centroid_3d is not None:
        radial_dist = float(np.linalg.norm(pos_3d - centroid_3d))
        
    features = one_hot_symbol + [degree, formal_charge, is_aromatic, num_hs, is_in_ring, mass, radial_dist]
    return np.array(features, dtype=np.float32)

def smiles_to_pyg_graph(smiles, add_3d_conformer=True):
    """
    Convert SMILES string into a PyTorch Geometric Data object with 3D conformation.
    """
    if not isinstance(smiles, str) or len(smiles.strip()) == 0:
        return None
        
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            mol = Chem.MolFromSmiles(smiles, sanitize=False)
            if mol is not None:
                mol.UpdatePropertyCache(strict=False)
                
        if mol is None:
            return None
            
        num_atoms = mol.GetNumAtoms()
        if num_atoms == 0:
            return None
            
        # Attempt 3D Conformation Embedding via ETKDG
        pos_coords = None
        centroid = None
        if add_3d_conformer:
            mol_h = Chem.AddHs(mol)
            res = AllChem.EmbedMolecule(mol_h, AllChem.ETKDG())
            if res == 0:
                try:
                    AllChem.MMFFOptimizeMolecule(mol_h)
                except Exception:
                    pass
                mol_no_h = Chem.RemoveHs(mol_h)
                if mol_no_h.GetNumConformers() > 0:
                    conf = mol_no_h.GetConformer()
                    pos_coords = np.array([list(conf.GetAtomPosition(i)) for i in range(num_atoms)], dtype=np.float32)
                    centroid = pos_coords.mean(axis=0)
                    
        # Extract Node Features
        node_features = []
        for i, atom in enumerate(mol.GetAtoms()):
            atom_pos = pos_coords[i] if pos_coords is not None else None
            feat = get_atom_features(atom, pos_3d=atom_pos, centroid_3d=centroid)
            node_features.append(feat)
            
        x = torch.tensor(np.array(node_features), dtype=torch.float32)
        
        # Extract Edges
        edge_indices = []
        for bond in mol.GetBonds():
            u = bond.GetBeginAtomIdx()
            v = bond.GetEndAtomIdx()
            edge_indices.append([u, v])
            edge_indices.append([v, u]) # undirected
            
        if len(edge_indices) > 0:
            edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        else:
            # Self loops if single atom
            edge_index = torch.zeros((2, 1), dtype=torch.long)
            
        pos = torch.tensor(pos_coords, dtype=torch.float32) if pos_coords is not None else torch.zeros((num_atoms, 3))
        
        if HAS_PYG:
            return Data(x=x, edge_index=edge_index, pos=pos)
        else:
            return {"x": x, "edge_index": edge_index, "pos": pos}
            
    except Exception as e:
        print(f"[Drug Features] Warning: PyG graph generation failed for SMILES '{smiles[:30]}...': {e}")
        return None

class MolecularGNNEncoder(nn.Module):
    """
    Graph Neural Network Encoder (GCN + Dual Pooling) for molecular SMILES graphs.
    Projects arbitrary molecular topologies + 3D coordinates into a 128-dimensional dense vector.
    """
    def __init__(self, in_dim=18, hidden_dim=64, out_dim=128):
        super(MolecularGNNEncoder, self).__init__()
        self.out_dim = out_dim
        
        if HAS_PYG:
            self.conv1 = GCNConv(in_dim, hidden_dim)
            self.bn1 = nn.BatchNorm1d(hidden_dim)
            self.conv2 = GCNConv(hidden_dim, hidden_dim)
            self.bn2 = nn.BatchNorm1d(hidden_dim)
            self.fc = nn.Linear(hidden_dim * 2, out_dim)
        else:
            # Linear surrogate fallback if PyG is absent
            self.fc = nn.Linear(in_dim, out_dim)

    def forward(self, x, edge_index, batch=None):
        if not HAS_PYG:
            return self.fc(x.mean(dim=0, keepdim=True))
            
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
            
        # GCN Layer 1
        h = self.conv1(x, edge_index)
        if h.size(0) > 1:
            h = self.bn1(h)
        h = F.leaky_relu(h, 0.1)
        
        # GCN Layer 2
        h = self.conv2(h, edge_index)
        if h.size(0) > 1:
            h = self.bn2(h)
        h = F.leaky_relu(h, 0.1)
        
        # Multi-Pool Aggregation (Mean + Max)
        mean_pool = global_mean_pool(h, batch)
        max_pool = global_max_pool(h, batch)
        graph_repr = torch.cat([mean_pool, max_pool], dim=1)
        
        out = self.fc(graph_repr)
        return out

# Global Singleton GNN Instance
_GNN_INSTANCE = None

def get_gnn_encoder():
    global _GNN_INSTANCE
    if _GNN_INSTANCE is None:
        _GNN_INSTANCE = MolecularGNNEncoder()
        os.makedirs(MODELS_DIR, exist_ok=True)
        if os.path.exists(GNN_WEIGHTS_PATH):
            try:
                _GNN_INSTANCE.load_state_dict(torch.load(GNN_WEIGHTS_PATH, map_location="cpu"))
            except Exception:
                pass
        else:
            try:
                torch.save(_GNN_INSTANCE.state_dict(), GNN_WEIGHTS_PATH)
            except Exception:
                pass
        _GNN_INSTANCE.eval()
    return _GNN_INSTANCE

def get_morgan_fingerprint(smiles, radius=2, n_bits=2048):
    """
    Generate 2048-bit ECFP4 (Morgan) fingerprint array for a given SMILES string.
    """
    if not isinstance(smiles, str) or len(smiles.strip()) == 0:
        return np.zeros(n_bits, dtype=np.float32)
        
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            mol = Chem.MolFromSmiles(smiles, sanitize=False)
            if mol is not None:
                mol.UpdatePropertyCache(strict=False)
                
        if mol is not None:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=radius, nBits=n_bits)
            arr = np.zeros((n_bits,), dtype=np.float32)
            Chem.DataStructs.ConvertToNumpyArray(fp, arr)
            return arr
    except Exception as e:
        print(f"[Drug Features] Warning: fingerprint generation failed for SMILES '{smiles[:30]}...': {e}")
        
    return np.zeros(n_bits, dtype=np.float32)

def get_physicochemical_descriptors(smiles):
    """
    Calculate MW, LogP, TPSA, HBD, HBA, NumRotatableBonds for a SMILES string.
    """
    defaults = np.zeros(6, dtype=np.float32)
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            tpsa = Descriptors.TPSA(mol)
            hbd = Descriptors.NumHDonors(mol)
            hba = Descriptors.NumHAcceptors(mol)
            rot = Descriptors.NumRotatableBonds(mol)
            return np.array([mw, logp, tpsa, hbd, hba, rot], dtype=np.float32)
    except Exception:
        pass
    return defaults

def get_graph_embedding(smiles):
    """
    Compute 128-dimensional GNN molecular graph embedding for a SMILES string.
    """
    encoder = get_gnn_encoder()
    pyg_data = smiles_to_pyg_graph(smiles, add_3d_conformer=True)
    if pyg_data is None or not HAS_PYG:
        return np.zeros(128, dtype=np.float32)
        
    with torch.no_grad():
        emb = encoder(pyg_data.x, pyg_data.edge_index)
        return emb.cpu().squeeze(0).numpy().astype(np.float32)

def get_drug_encoding(smiles, mode="combined", use_descriptors=True, use_graph=True):
    """
    Drug representation options:
    - combined (default, 2182 dims): Morgan ECFP4 (2048) + Descriptors (6) + GNN 3D Graph (128)
    - graph (128 dims): GNN molecular graph embedding only
    - baseline (2054 dims): Morgan ECFP4 (2048) + Descriptors (6)
    """
    if mode == "graph":
        return get_graph_embedding(smiles)
        
    fp = get_morgan_fingerprint(smiles)
    desc = get_physicochemical_descriptors(smiles) if use_descriptors else np.array([], dtype=np.float32)
    
    if mode == "baseline" or not use_graph:
        return np.concatenate([fp, desc]) if len(desc) > 0 else fp
        
    graph_emb = get_graph_embedding(smiles)
    return np.concatenate([fp, desc, graph_emb])

if __name__ == "__main__":
    test_smiles = "CC(=O)OCC1C(C(C(C(O1)S[Au]P(CC)(CC)CC)OC(=O)C)OC(=O)C)OC(=O)C"  # Auranofin
    graph_data = smiles_to_pyg_graph(test_smiles)
    print(f"Auranofin PyG Graph Nodes: {graph_data.x.shape}, Edges: {graph_data.edge_index.shape}, 3D Pos: {graph_data.pos.shape}")
    
    enc_comb = get_drug_encoding(test_smiles, mode="combined")
    print(f"Auranofin Combined Drug Vector Shape: {enc_comb.shape}")
    print(f"  - Morgan ECFP4: 2048 dims")
    print(f"  - Physicochemical Descriptors: 6 dims")
    print(f"  - Molecular GNN (3D Graph): 128 dims")
    print(f"  - Total Dimension: {len(enc_comb)} dims | L2 Norm: {np.linalg.norm(enc_comb):.4f}")
