# CDMO Framework - Complete (Phase 1, 2 & 3)

## Computational Design & Multi-Objective Optimization

### 3D Printed Biofilm Carriers for Faecal Sludge Treatment

**University of Ibadan - Mechanical Engineering - PhD Research**
**Majolagbe Yusuf Oladimeji (R.Eng, PMP)**

---

## Quick Start

```powershell
cd C:\Users\mubar\Projects\cdmo_app
pip install -r requirements.txt
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

App opens at <http://localhost:8501>

---

## Project Structure

```
cdmo_app/
 app.py                               # Landing page
 requirements.txt
 pages/
   1_Upload_Analyse.py                # PHASE 1: Full analysis pipeline
   2_Sensitivity_Analysis.py          # PHASE 2: Parameter sensitivity
   3_STL_Generator.py                 # PHASE 2: Parametric STL generation
   4_Design_Comparison.py             # PHASE 2: 16-carrier comparison matrix
   5_Session_Manager.py               # PHASE 2: Session persistence
   6_GA_Optimiser.py                  # PHASE 3: NSGA-II genetic algorithm
   7_Statistical_Analysis.py          # PHASE 3: Hypothesis testing & regression
   8_PDF_Report.py                    # PHASE 3: Automated report generation
 core/
   geometry.py                        # STL processing & geometric metrics
   flow_analysis.py                   # Ergun / Kozeny-Carman / Sherwood
   buoyancy.py                        # Archimedes buoyancy analysis
   scoring.py                         # Multi-objective scoring & Pareto
   materials.py                       # PLA / ABS / PETG / PP database
   sensitivity.py                     # One-at-a-time sensitivity analysis
   stl_generator.py                   # Parametric carrier generation
   genetic_algorithm.py               # NSGA-II optimisation
   statistics.py                      # ANOVA, correlations, regression
 utils/
   persistence.py                     # Session save/load/export
   report_generator.py                # Automated PDF report
 data/sessions/                       # Saved analysis sessions
```

---

## Recommended Workflow

1. Upload & Analyse     - Upload all 16 STL files, run full pipeline
2. Session Manager      - Save session, no re-uploading needed
3. Design Comparison    - See all 16 designs across all objectives
4. Sensitivity Analysis - Find which parameters drive performance
5. GA Optimiser         - Search for better geometries beyond your 16
6. Statistical Analysis - ANOVA, correlations, regressions for thesis
7. STL Generator        - Generate improved designs from findings
8. PDF Report           - One-click automated thesis-quality report

---

## Core Modules Summary

### geometry.py

Surface area (mesh summation), volume (divergence theorem), porosity
(bounding box void fraction), hydraulic diameter (packed bed model),
specific surface area (m2/m3). Auto mesh repair.

### flow_analysis.py

Ergun equation (pressure drop), Kozeny-Carman (permeability),
Wilson-Geankoplis Sherwood number (mass transfer), Reynolds number,
flow regime classification, clogging risk for faecal sludge.

### buoyancy.py

Archimedes principle with effective carrier density accounting for
void fraction. MBBR suitability scoring. All 4 materials compared.

### scoring.py

Configurable objective weights. Population-level min-max normalisation.
NSGA-II Pareto dominance check. Improvement suggestion engine.

### genetic_algorithm.py

NSGA-II with non-dominated sorting, simulated binary crossover (SBX),
polynomial mutation, binary tournament selection, elitism.

### statistics.py

One-way ANOVA / Kruskal-Wallis, Levene test, Bonferroni-corrected
pairwise Mann-Whitney U, Cohen's d, eta-squared, Pearson/Spearman
correlations, linear regression with R2.

---

## Materials Database

Material | Density g/cm3 | Biofilm Affinity | Chemical Resistance
PLA      | 1.24-1.25     | 0.85 (best)      | Low
ABS      | 1.04-1.06     | 0.75             | Moderate
PETG     | 1.27-1.29     | 0.70             | High
PP       | 0.90-0.91     | 0.60             | Very High (best)

---

## Requirements

streamlit>=1.32.0, trimesh>=4.3.0, numpy>=1.26.0, scipy>=1.12.0,
plotly>=5.19.0, pandas>=2.2.0, numpy-stl>=3.1.0, fpdf2>=2.7.0, kaleido>=0.2.1,
networkx>=3.2.1
