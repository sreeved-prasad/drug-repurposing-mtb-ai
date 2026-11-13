# PyMOL Visualization Script for Auranofin - TrxB2 (PDB 2A87) Complex
# Execute in PyMOL: @visualize_auranofin_2A87.pml

reinitialize
load C:\Users\HP\Pictures\Drug in AI\results\docking\2A87_auranofin_complex.pdb, trxb2_auranofin_complex

# Setup background and display
bg_color white
set ray_shadows, 0
set antialias, 2
set depth_cue, 1

# Receptor presentation
hide everything, all
show cartoon, chain A
color slate, chain A

# Active site residues
select active_site, chain A and resi 145+146+147+148+198+302+305
show sticks, active_site
color firebrick, chain A and resi 145+148
color marine, chain A and resi 146+147+198+302+305

# Ligand presentation
select auranofin, resn LIG
show sticks, auranofin
color forest, auranofin and elem C
color red, auranofin and elem O
color yellow, auranofin and elem S
color orange, auranofin and elem P
color gold, auranofin and elem Au
set stick_radius, 0.32, auranofin

# Catalytic coordination & Hydrogen bond distances
distance au_coord1, (chain A and resi 145 and name SG), (resn LIG and elem Au)
distance au_coord2, (chain A and resi 148 and name SG), (resn LIG and elem Au)
color yellow, au_coord1 au_coord2
set dash_width, 3
set dash_gap, 0.2

# Zoom to pocket
zoom active_site or auranofin, 5
orient active_site or auranofin

# Surface overview
create active_surf, chain A and (active_site expand 4.0)
show surface, active_surf
set transparency, 0.65, active_surf
color gray90, active_surf

print("PyMOL script initialized: Auranofin positioned in TrxB2 Cys145-Cys148 redox cleft.")
