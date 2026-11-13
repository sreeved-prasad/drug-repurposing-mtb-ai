import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.ensemble import RandomForestClassifier

from drug_features import MolecularGNNEncoder, HAS_PYG

class BaselineRFModel:
    """
    Random Forest Baseline Classifier for Drug-Target Interaction prediction.
    """
    def __init__(self, n_estimators=100, random_state=42):
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state, n_jobs=-1)
        
    def fit(self, X_train, y_train):
        self.model.fit(X_train, y_train)
        
    def predict_proba(self, X):
        return self.model.predict_proba(X)[:, 1]
        
    def predict(self, X):
        return self.model.predict(X)

class CrossAttentionFusion(nn.Module):
    """
    Bi-directional cross-attention between latent Drug and Protein representations.
    Allows drug features to attend to relevant protein active sites and vice versa.
    """
    def __init__(self, embed_dim=128):
        super(CrossAttentionFusion, self).__init__()
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        self.scale = 1.0 / (embed_dim ** 0.5)

    def forward(self, d_emb, p_emb):
        # Shapes: (B, embed_dim) -> (B, 1, embed_dim)
        d_q = self.q_proj(d_emb).unsqueeze(1)
        p_k = self.k_proj(p_emb).unsqueeze(1)
        p_v = self.v_proj(p_emb).unsqueeze(1)
        
        # Attention score
        attn = torch.softmax((d_q * p_k).sum(dim=-1, keepdim=True) * self.scale, dim=-1)
        attended = (attn * p_v).squeeze(1)
        return attended

class DualEncoderDTI(nn.Module):
    """
    Stage 2 Deep Neural Network Dual-Encoder Architecture for DTI prediction.
    
    Drug Representation (2182 dims: ECFP4 + Descriptors + 3D GNN) ---> [Drug MLP Encoder] ----> 128-dim Drug Latent
                                                                                               \
                                                                                                ==> [Cross-Attention & Fusion MLP] --> Sigmoid Probability
                                                                                               /
    Protein Sequence (684 dims: ESM-2 + AAC + Conjoint Triads) ------> [Protein MLP Encoder] --> 128-dim Protein Latent
    """
    def __init__(self, drug_dim=2182, protein_dim=684, embed_dim=128):
        super(DualEncoderDTI, self).__init__()
        self.drug_dim = drug_dim
        self.protein_dim = protein_dim
        self.embed_dim = embed_dim
        
        # Drug Encoder Branch
        self.drug_fc1 = nn.Linear(drug_dim, 512)
        self.drug_bn1 = nn.BatchNorm1d(512)
        self.drug_fc2 = nn.Linear(512, embed_dim)
        self.drug_bn2 = nn.BatchNorm1d(embed_dim)
        self.drug_dropout = nn.Dropout(0.3)
        
        # Protein Encoder Branch
        self.protein_fc1 = nn.Linear(protein_dim, 384)
        self.protein_bn1 = nn.BatchNorm1d(384)
        self.protein_fc2 = nn.Linear(384, embed_dim)
        self.protein_bn2 = nn.BatchNorm1d(embed_dim)
        self.protein_dropout = nn.Dropout(0.3)
        
        # Interaction & Fusion Classifier
        self.cross_attn = CrossAttentionFusion(embed_dim=embed_dim)
        # Concatenate: drug (128) + protein (128) + attended interaction (128) + elementwise product (128) = 512
        self.fusion_fc1 = nn.Linear(embed_dim * 4, 128)
        self.fusion_bn1 = nn.BatchNorm1d(128)
        self.fusion_fc2 = nn.Linear(128, 64)
        self.fusion_bn2 = nn.BatchNorm1d(64)
        self.fusion_out = nn.Linear(64, 1)
        self.fusion_dropout = nn.Dropout(0.2)

    def forward(self, drug_x, protein_x):
        # 1. Encode Drug
        d = F.relu(self.drug_bn1(self.drug_fc1(drug_x)))
        d = self.drug_dropout(d)
        d = F.relu(self.drug_bn2(self.drug_fc2(d)))
        
        # 2. Encode Protein
        p = F.relu(self.protein_bn1(self.protein_fc1(protein_x)))
        p = self.protein_dropout(p)
        p = F.relu(self.protein_bn2(self.protein_fc2(p)))
        
        # 3. Cross-Attention Interaction
        interact = self.cross_attn(d, p)
        elem_prod = d * p
        
        # 4. Multimodal Fusion
        fusion = torch.cat([d, p, interact, elem_prod], dim=1)
        
        # 5. Predict Binding Likelihood
        x = F.relu(self.fusion_bn1(self.fusion_fc1(fusion)))
        x = self.fusion_dropout(x)
        x = F.relu(self.fusion_bn2(self.fusion_fc2(x)))
        logits = self.fusion_out(x)
        prob = torch.sigmoid(logits)
        return prob.squeeze(1)

class GraphDualEncoderDTI(nn.Module):
    """
    End-to-End Molecular Graph Dual-Encoder DTI Network.
    Accepts raw PyG graph data for molecules and ESM-2 sequence vectors for targets.
    """
    def __init__(self, protein_dim=684, embed_dim=128):
        super(GraphDualEncoderDTI, self).__init__()
        self.gnn_encoder = MolecularGNNEncoder(in_dim=18, hidden_dim=64, out_dim=embed_dim)
        
        self.protein_fc1 = nn.Linear(protein_dim, 384)
        self.protein_bn1 = nn.BatchNorm1d(384)
        self.protein_fc2 = nn.Linear(384, embed_dim)
        self.protein_bn2 = nn.BatchNorm1d(embed_dim)
        self.protein_dropout = nn.Dropout(0.3)
        
        self.fusion_fc1 = nn.Linear(embed_dim * 3, 128)
        self.fusion_bn1 = nn.BatchNorm1d(128)
        self.fusion_fc2 = nn.Linear(128, 64)
        self.fusion_bn2 = nn.BatchNorm1d(64)
        self.fusion_out = nn.Linear(64, 1)
        self.dropout = nn.Dropout(0.2)

    def forward(self, graph_batch, protein_x):
        # 1. GNN Drug Encoding
        d = self.gnn_encoder(graph_batch.x, graph_batch.edge_index, getattr(graph_batch, 'batch', None))
        
        # 2. Protein Sequence Encoding
        p = F.relu(self.protein_bn1(self.protein_fc1(protein_x)))
        p = self.protein_dropout(p)
        p = F.relu(self.protein_bn2(self.protein_fc2(p)))
        
        # 3. Fuse
        fusion = torch.cat([d, p, d * p], dim=1)
        x = F.relu(self.fusion_bn1(self.fusion_fc1(fusion)))
        x = self.dropout(x)
        x = F.relu(self.fusion_bn2(self.fusion_fc2(x)))
        logits = self.fusion_out(x)
        return torch.sigmoid(logits).squeeze(1)

if __name__ == "__main__":
    d_x = torch.randn(8, 2182)
    p_x = torch.randn(8, 684)
    model = DualEncoderDTI(drug_dim=2182, protein_dim=684)
    out = model(d_x, p_x)
    print("DualEncoderDTI Forward Pass Shape:", out.shape, "Sample outputs:", out[:4].detach().numpy())
