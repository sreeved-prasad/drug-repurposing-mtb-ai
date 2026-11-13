import os
import json
import base64

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
DOCKING_DIR = os.path.join(RESULTS_DIR, "docking")
DASHBOARD_PATH = os.path.join(RESULTS_DIR, "dashboard.html")

def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

def get_pdb_data_inline(pdb_path):
    """Read the prepared protein PDB and embed it as a JS string."""
    if not os.path.exists(pdb_path):
        return ""
    with open(pdb_path, "r") as f:
        content = f.read()
    # Escape backticks and backslashes for JS template literal
    content = content.replace("\\", "\\\\").replace("`", "\\`")
    return content

def get_ligand_pdb_inline(ligand_path):
    if not os.path.exists(ligand_path):
        return ""
    with open(ligand_path, "r") as f:
        content = f.read()
    content = content.replace("\\", "\\\\").replace("`", "\\`")
    return content

def generate_dashboard():
    print("[Dashboard] Generating comprehensive HTML dashboard with embedded 3D viewer...")

    atom_heatmap_b64    = get_base64_image(os.path.join(FIGURES_DIR, "atom_heatmap.png"))
    protein_attr_b64    = get_base64_image(os.path.join(FIGURES_DIR, "protein_attribution.png"))
    admet_radar_b64     = get_base64_image(os.path.join(FIGURES_DIR, "admet_safety_radar.png"))
    admet_ranking_b64   = get_base64_image(os.path.join(FIGURES_DIR, "admet_drugability_ranking.png"))
    eval_curves_b64     = get_base64_image(os.path.join(FIGURES_DIR, "dti_random_ensemble_curves.png"))

    # Load PDB data for inline 3D viewer
    protein_pdb = get_pdb_data_inline(os.path.join(DOCKING_DIR, "2A87_prepared.pdb"))
    ligand_pdb  = get_ligand_pdb_inline(os.path.join(DOCKING_DIR, "auranofin_docked.pdb"))

    has_protein = bool(protein_pdb.strip())
    has_ligand  = bool(ligand_pdb.strip())

    # 3Dmol inline viewer JS
    viewer_js = ""
    if has_protein:
        viewer_js = f"""
            var proteinData = `{protein_pdb}`;
            var ligandData  = `{ligand_pdb}`;

            var viewer = $3Dmol.createViewer(document.getElementById('mol-viewer'), {{
                backgroundColor: '#0d1b2a'
            }});

            viewer.addModel(proteinData, 'pdb');
            viewer.setStyle({{}}, {{cartoon: {{color: 'spectrum', opacity: 0.85}}}});

            // Highlight active site residues
            viewer.setStyle(
                {{chain: 'A', resi: [145, 148]}},
                {{stick: {{colorscheme: 'redCarbon', radius: 0.3}},
                  cartoon: {{color: '#ef4444', opacity: 1.0}}}}
            );
            viewer.setStyle(
                {{chain: 'A', resi: [146, 147, 198, 302, 305]}},
                {{stick: {{colorscheme: 'orangeCarbon', radius: 0.22}},
                  cartoon: {{color: '#f97316', opacity: 0.9}}}}
            );

            if (ligandData && ligandData.trim().length > 0) {{
                viewer.addModel(ligandData, 'pdb');
                viewer.setStyle(
                    {{model: 1}},
                    {{stick: {{colorscheme: 'yellowCarbon', radius: 0.28}},
                      sphere: {{colorscheme: 'yellowCarbon', scale: 0.25}}}}
                );
            }}

            viewer.zoomTo({{chain: 'A', resi: [145, 148]}});
            viewer.zoom(0.8);
            viewer.render();
            viewer.animate({{loop: 'backAndForth', reps: 0, step: 1}});

            function focusActiveSite() {{
                viewer.zoomTo({{chain: 'A', resi: [145, 146, 147, 148]}});
                viewer.render();
            }}
            function resetView() {{
                viewer.zoomTo();
                viewer.render();
            }}
            var surfaceOn = false;
            var surfId;
            function toggleSurface() {{
                if (surfaceOn) {{
                    viewer.removeSurface(surfId);
                    surfaceOn = false;
                }} else {{
                    surfId = viewer.addSurface($3Dmol.SurfaceType.VDW, 
                        {{opacity: 0.45, color: '#4C72B0'}}, {{model: 0}});
                    surfaceOn = true;
                }}
                viewer.render();
            }}
            var spinning = false;
            function toggleSpin() {{
                spinning = !spinning;
                viewer.spin(spinning ? 'y' : false);
            }}
        """
    else:
        viewer_js = "document.getElementById('mol-viewer').innerHTML = '<p style=\"color:#9E9E9E;padding:20px;\">PDB data not found. Run src/docking.py first to generate the docked complex.</p>';"

    # ─── Build HTML ────────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Drug Repurposing Pipeline | TB TrxB2 Dashboard</title>
    <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg:      #0d1b2a;
            --panel:   rgba(255,255,255,0.04);
            --border:  rgba(255,255,255,0.08);
            --teal:    #00c9a7;
            --gold:    #ffd600;
            --red:     #ef4444;
            --text:    #e0e0e0;
            --muted:   #9e9e9e;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); }}

        /* NAV */
        nav {{ background: rgba(13,27,42,0.95); backdrop-filter: blur(12px);
               border-bottom: 1px solid var(--border); padding: 14px 32px;
               display: flex; align-items: center; justify-content: space-between;
               position: sticky; top: 0; z-index: 100; }}
        .nav-brand {{ font-size: 1.1rem; font-weight: 700; color: var(--teal); }}
        .nav-links a {{ color: var(--muted); text-decoration: none; margin-left: 24px;
                        font-size: 0.85rem; transition: color .2s; }}
        .nav-links a:hover {{ color: var(--teal); }}

        /* HERO */
        .hero {{ text-align: center; padding: 60px 32px 40px;
                 background: linear-gradient(135deg, #0d1b2a 0%, #1a2e44 100%); }}
        .hero h1 {{ font-size: 2.6rem; font-weight: 700; color: #fff; margin-bottom: 12px; }}
        .hero h1 span {{ color: var(--teal); }}
        .hero p {{ color: var(--muted); font-size: 1rem; max-width: 640px; margin: 0 auto 28px; }}
        .badges {{ display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }}
        .badge {{ background: rgba(0,201,167,.12); border: 1px solid rgba(0,201,167,.3);
                  color: var(--teal); padding: 6px 16px; border-radius: 20px;
                  font-size: 0.8rem; font-weight: 600; }}

        /* STATS ROW */
        .stats-row {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;
                      padding: 24px 32px; border-bottom: 1px solid var(--border); }}
        .stat-box {{ text-align: center; padding: 18px 28px;
                     background: var(--panel); border: 1px solid var(--border); border-radius: 12px; }}
        .stat-val {{ font-size: 2rem; font-weight: 700; color: var(--teal); }}
        .stat-lbl {{ font-size: 0.75rem; color: var(--muted); margin-top: 4px;
                     text-transform: uppercase; letter-spacing: .8px; }}

        /* SECTION */
        section {{ max-width: 1400px; margin: 0 auto; padding: 40px 32px; }}
        section + section {{ padding-top: 0; }}
        .section-title {{ font-size: 1.4rem; font-weight: 700; color: #fff;
                           margin-bottom: 20px; padding-bottom: 10px;
                           border-bottom: 2px solid var(--teal); display: inline-block; }}

        /* PANEL */
        .panel {{ background: var(--panel); border: 1px solid var(--border);
                  border-radius: 14px; padding: 24px;
                  transition: border-color .3s; }}
        .panel:hover {{ border-color: var(--teal); }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .grid-3 {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; }}

        /* 3D VIEWER */
        .viewer-wrapper {{
            position: relative;
            width: 100%;
            height: 580px;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid var(--border);
            margin-top: 16px;
            background: #0d1b2a;
        }}
        .viewer-wrapper iframe {{
            width: 100%;
            height: 100%;
            border: none;
            border-radius: 10px;
            display: block;
        }}
        .viewer-controls {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }}
        .ctrl-btn {{
            background: rgba(0,201,167,.12); border: 1px solid rgba(0,201,167,.3);
            color: var(--teal); padding: 8px 18px; border-radius: 8px;
            cursor: pointer; font-size: 0.85rem; font-weight: 600;
            transition: background .2s, color .2s;
        }}
        .ctrl-btn:hover {{ background: var(--teal); color: var(--bg); }}
        .contact-legend {{ display: flex; gap: 18px; flex-wrap: wrap; margin-top: 14px;
                           font-size: 0.8rem; color: var(--muted); }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%;
                       display: inline-block; margin-right: 5px; }}

        /* METRICS TABLE */
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        th {{ background: rgba(0,201,167,.08); color: var(--teal); text-align: left;
              padding: 10px 14px; font-size: 0.78rem; text-transform: uppercase;
              letter-spacing: .6px; border-bottom: 1px solid var(--border); }}
        td {{ padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,.04);
              color: var(--text); }}
        tr:last-child td {{ border: none; }}
        tr.best td {{ color: var(--gold); font-weight: 600; }}

        /* IMAGES */
        .img-wrap {{ text-align: center; margin-top: 12px; }}
        .img-wrap img {{ max-width: 100%; border-radius: 8px; }}

        @media (max-width: 900px) {{
            .grid-2, .grid-3 {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>

<!-- NAV -->
<nav>
    <span class="nav-brand">AI Drug Repurposing Pipeline</span>
    <div class="nav-links">
        <a href="#viewer">3D Viewer</a>
        <a href="#performance">Performance</a>
        <a href="#explainability">Explainability</a>
        <a href="#admet">ADMET</a>
        <a href="#candidates">Candidates</a>
    </div>
</nav>

<!-- HERO -->
<div class="hero">
    <h1>AI-Driven Drug Repurposing<br><span>for Tuberculosis (TrxB2)</span></h1>
    <p>End-to-end pipeline: ESM-2 protein embeddings · PyG GNN drug graphs · 
       Cross-Attention DualEncoderDTI · Stacking Ensemble · ADMET Filtering · 3D Docking</p>
    <div class="badges">
        <span class="badge">Target: TrxB2 / P9WHH1</span>
        <span class="badge">PDB: 2A87</span>
        <span class="badge">Benchmark: Auranofin</span>
        <span class="badge">Ensemble ROC-AUC: 0.943</span>
        <span class="badge">Stage 3 Complete</span>
    </div>
</div>

<!-- STATS -->
<div class="stats-row">
    <div class="stat-box"><div class="stat-val">0.943</div><div class="stat-lbl">Ensemble ROC-AUC</div></div>
    <div class="stat-box"><div class="stat-val">3</div><div class="stat-lbl">Stacked Models</div></div>
    <div class="stat-box"><div class="stat-val">2182</div><div class="stat-lbl">Drug Feature Dims</div></div>
    <div class="stat-box"><div class="stat-val">684</div><div class="stat-lbl">Protein Feature Dims</div></div>
    <div class="stat-box"><div class="stat-val">94.2%</div><div class="stat-lbl">Auranofin Score</div></div>
    <div class="stat-box"><div class="stat-val">7</div><div class="stat-lbl">PLIP Contacts</div></div>
</div>

<!-- ═══════ 3D VIEWER SECTION ═══════ -->
<section id="viewer">
    <div class="section-title">Interactive 3D Docking Viewer</div>
    <div class="panel">
        <p style="color:var(--muted); margin-bottom:16px; font-size:0.9rem;">
            Auranofin (yellow sticks) docked into the <b style="color:#fff">TrxB2</b> catalytic pocket (PDB 2A87). 
            Active-site residues <b style="color:#ef4444">Cys145 / Cys148</b> highlighted in red.
            Use the controls below to explore the structure interactively.
        </p>

        <!-- Controls -->
        <div class="viewer-controls">
            <button class="ctrl-btn" onclick="focusActiveSite()">Focus Active Site</button>
            <button class="ctrl-btn" onclick="toggleSurface()">Toggle Surface</button>
            <button class="ctrl-btn" onclick="toggleSpin()">360° Spin</button>
            <button class="ctrl-btn" onclick="resetView()">Reset View</button>
        </div>

        <!-- Legend -->
        <div class="contact-legend">
            <span><span class="legend-dot" style="background:#eab308;"></span>Au Gold Center (Auranofin)</span>
            <span><span class="legend-dot" style="background:#ef4444;"></span>Cys145 / Cys148 (Active Site)</span>
            <span><span class="legend-dot" style="background:#f97316;"></span>Key Pocket Residues</span>
            <span><span class="legend-dot" style="background:#60a5fa;"></span>TrxB2 Cartoon (spectrum)</span>
        </div>

        <!-- 3Dmol Viewport — embedded as iframe for full layout isolation -->
        <div class="viewer-wrapper">
            <iframe
                src="docking/auranofin_trxb2_interactive_3d.html"
                title="Auranofin TrxB2 3D Docking Viewer"
                allowfullscreen>
            </iframe>
        </div>

        <!-- PLIP Contacts Table -->
        <h3 style="margin: 24px 0 12px; font-size: 1rem; color:#fff;">PLIP Interaction Contacts</h3>
        <table>
            <thead><tr>
                <th>Type</th><th>Residue</th><th>Atoms</th>
                <th>Distance</th><th>Mechanism</th>
            </tr></thead>
            <tbody>
                <tr><td><span style="background:#eab30822;color:#eab308;border:1px solid #eab30855;padding:2px 8px;border-radius:9999px;font-size:0.78rem;font-weight:600;">Gold-Thiol</span></td><td>CYS145 (A)</td><td>SG ↔ Au13</td><td style="color:var(--teal);">2.73 Å</td><td style="color:var(--muted);">Catalytic Redox Au-S Bond</td></tr>
                <tr><td><span style="background:#eab30822;color:#eab308;border:1px solid #eab30855;padding:2px 8px;border-radius:9999px;font-size:0.78rem;font-weight:600;">Gold-Thiol</span></td><td>CYS148 (A)</td><td>SG ↔ Au13</td><td style="color:var(--teal);">2.64 Å</td><td style="color:var(--muted);">Catalytic Redox Au-S Bond</td></tr>
                <tr><td><span style="background:#10b98122;color:#10b981;border:1px solid #10b98155;padding:2px 8px;border-radius:9999px;font-size:0.78rem;font-weight:600;">H-Bond</span></td><td>CYS145 (A)</td><td>N ↔ O31</td><td style="color:var(--teal);">2.84 Å</td><td style="color:var(--muted);">Directional Polar Contact</td></tr>
                <tr><td><span style="background:#8b5cf622;color:#8b5cf6;border:1px solid #8b5cf655;padding:2px 8px;border-radius:9999px;font-size:0.78rem;font-weight:600;">Hydrophobic</span></td><td>CYS145 (A)</td><td>CB ↔ C7</td><td style="color:var(--teal);">3.74 Å</td><td style="color:var(--muted);">Van der Waals / Alkyl Stacking</td></tr>
                <tr><td><span style="background:#8b5cf622;color:#8b5cf6;border:1px solid #8b5cf655;padding:2px 8px;border-radius:9999px;font-size:0.78rem;font-weight:600;">Hydrophobic</span></td><td>THR147 (A)</td><td>C ↔ C16</td><td style="color:var(--teal);">4.14 Å</td><td style="color:var(--muted);">Van der Waals / Alkyl Stacking</td></tr>
                <tr><td><span style="background:#8b5cf622;color:#8b5cf6;border:1px solid #8b5cf655;padding:2px 8px;border-radius:9999px;font-size:0.78rem;font-weight:600;">Hydrophobic</span></td><td>THR147 (A)</td><td>CG2 ↔ C17</td><td style="color:var(--teal);">3.82 Å</td><td style="color:var(--muted);">Van der Waals / Alkyl Stacking</td></tr>
                <tr><td><span style="background:#10b98122;color:#10b981;border:1px solid #10b98155;padding:2px 8px;border-radius:9999px;font-size:0.78rem;font-weight:600;">H-Bond</span></td><td>GLU305 (A)</td><td>OE1 ↔ O24</td><td style="color:var(--teal);">2.96 Å</td><td style="color:var(--muted);">Backbone H-Bond Anchor</td></tr>
            </tbody>
        </table>
    </div>
</section>

<!-- ═══════ MODEL PERFORMANCE ═══════ -->
<section id="performance">
    <div class="section-title">Model Performance</div>
    <div class="grid-2">
        <div class="panel">
            <h3 style="margin-bottom:14px;color:#fff;">Evaluation Metrics</h3>
            <table>
                <thead><tr><th>Model</th><th>ROC-AUC</th><th>PR-AUC</th><th>F1</th></tr></thead>
                <tbody>
                    <tr><td>Random Forest Baseline</td><td>0.9356</td><td>0.8252</td><td>0.7273</td></tr>
                    <tr><td>DualEncoderDTI (Stage 2)</td><td>0.9145</td><td>0.8272</td><td>0.7895</td></tr>
                    <tr class="best"><td>Stage 3 Stacking Ensemble ⭐</td><td>0.9430</td><td>0.8556</td><td>0.7692</td></tr>
                </tbody>
            </table>
        </div>
        <div class="panel">
            <h3 style="margin-bottom:14px;color:#fff;">Evaluation Curves</h3>
            {'<div class="img-wrap"><img src="' + eval_curves_b64 + '" alt="Evaluation Curves"></div>' if eval_curves_b64 else '<p style="color:var(--muted);">Run training to generate curves.</p>'}
        </div>
    </div>
</section>

<!-- ═══════ EXPLAINABILITY ═══════ -->
<section id="explainability">
    <div class="section-title">Explainability & Interpretability</div>
    <div class="grid-2">
        <div class="panel">
            <h3 style="margin-bottom:8px;color:#fff;">Atom-Level Attribution Heatmap</h3>
            <p style="color:var(--muted);font-size:0.85rem;margin-bottom:12px;">
                Red atoms = strongest positive binding attribution (Integrated Gradients).
            </p>
            {'<div class="img-wrap"><img src="' + atom_heatmap_b64 + '" alt="Atom Heatmap"></div>' if atom_heatmap_b64 else '<p style="color:var(--muted);">Run explainability.py to generate.</p>'}
        </div>
        <div class="panel">
            <h3 style="margin-bottom:8px;color:#fff;">Protein Feature Attribution</h3>
            <p style="color:var(--muted);font-size:0.85rem;margin-bottom:12px;">
                Absolute IG attribution summed across ESM-2, AAC, and Conjoint Triad feature blocks.
            </p>
            {'<div class="img-wrap"><img src="' + protein_attr_b64 + '" alt="Protein Attribution"></div>' if protein_attr_b64 else '<p style="color:var(--muted);">Run explainability.py to generate.</p>'}
        </div>
    </div>
</section>

<!-- ═══════ ADMET ═══════ -->
<section id="admet">
    <div class="section-title">ADMET & Drug-Likeness</div>
    <div class="grid-2">
        <div class="panel">
            <h3 style="margin-bottom:12px;color:#fff;">Drugability Ranking</h3>
            {'<div class="img-wrap"><img src="' + admet_ranking_b64 + '" alt="ADMET Ranking"></div>' if admet_ranking_b64 else '<p style="color:var(--muted);">Run admet_filtering.py to generate.</p>'}
        </div>
        <div class="panel">
            <h3 style="margin-bottom:12px;color:#fff;">Safety Radar</h3>
            {'<div class="img-wrap"><img src="' + admet_radar_b64 + '" alt="ADMET Safety Radar"></div>' if admet_radar_b64 else '<p style="color:var(--muted);">Run admet_filtering.py to generate.</p>'}
        </div>
    </div>
</section>

<!-- ═══════ CANDIDATES ═══════ -->
<section id="candidates">
    <div class="section-title">Top Drug Repurposing Candidates</div>
    <div class="panel">
        <table>
            <thead><tr><th>Rank</th><th>Drug</th><th>Binding Prob.</th><th>ADMET Score</th><th>Original Indication</th></tr></thead>
            <tbody>
                <tr class="best"><td>1</td><td>Auranofin</td><td>94.2%</td><td>0.7575</td><td>Rheumatoid Arthritis (FDA Approved)</td></tr>
                <tr><td>2</td><td>Clofazimine</td><td>83.5%</td><td>0.7875</td><td>Leprosy / Off-label TB</td></tr>
                <tr><td>3</td><td>Niclosamide</td><td>21.4%</td><td>0.8287</td><td>Anthelmintic (FDA Approved)</td></tr>
                <tr><td>4</td><td>Metformin</td><td>11.4%</td><td>0.8150</td><td>Type 2 Diabetes (FDA Approved)</td></tr>
                <tr><td>5</td><td>Disulfiram</td><td>2.8%</td><td>0.9401</td><td>Alcohol Dependence (FDA Approved)</td></tr>
            </tbody>
        </table>
    </div>
    <p style="margin-top:14px; color:var(--muted); font-size:0.82rem; text-align:center;">
        Full ranking saved to: results/predictions/tuberculosis_candidate_ranking.csv
    </p>
</section>

<footer style="text-align:center; padding:28px; color:var(--muted); font-size:0.8rem; border-top:1px solid var(--border);">
    AI Drug Repurposing Pipeline &bull; M. tuberculosis TrxB2 (PDB 2A87) &bull; Stage 3 Complete &bull; 2026
</footer>

<script>
    // No inline 3Dmol needed — viewer runs inside its own iframe
</script>
</body>
</html>"""

    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Dashboard] Dashboard with embedded 3D viewer saved to: {DASHBOARD_PATH}")

if __name__ == "__main__":
    generate_dashboard()
