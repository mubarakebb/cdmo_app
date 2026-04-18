"""
CDMO Landing Page
Computational Design and Multi-Objective Optimization Framework
University of Ibadan, Nigeria
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.ui import inject_base_styles, sidebar_brand, cards_grid

st.set_page_config(
    page_title="CDMO Framework",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_base_styles()
sidebar_brand()

st.markdown(
    """
    <div class="cdmo-header" style="text-align:center;padding:2.4rem 2rem;">
      <div style="font-size:3rem;line-height:1;margin-bottom:0.65rem;">🔬</div>
      <div class="cdmo-badge" style="margin-bottom:0.6rem;">University of Ibadan · PhD Research</div>
      <h1 class="cdmo-header__title" style="font-size:2.05rem;margin:0;">CDMO Framework</h1>
      <p class="cdmo-header__subtitle" style="max-width:70ch;margin:0.55rem auto 0;">
        Computational Design &amp; Multi-Objective Optimization of 3D Printed Biofilm Carriers
        for Faecal Sludge Treatment
      </p>
      <p style="margin:0.65rem 0 0;opacity:0.78;font-size:0.86rem;">
        Mechanical Engineering · 2025
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Live session stats if data exists
if st.session_state.get("all_carriers"):
    carriers = st.session_state.all_carriers
    n_geo = len(set(c.filename for c in carriers))
    n_pareto = len([c for c in carriers if c.is_pareto_optimal])
    best = min(carriers, key=lambda c: c.rank)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Geometries Analysed", n_geo)
    col2.metric("Total Combinations", len(carriers))
    col3.metric("Pareto Optimal", n_pareto)
    col4.metric(
        "Top Design",
        f"{best.filename.replace('.stl','')} × {best.material}",
        f"Score: {best.composite_score:.3f}",
    )
    st.markdown("---")

# Module cards
st.markdown("### 📦 Framework Modules")
st.caption("Navigate using the sidebar, or use this overview to plan your workflow.")

cards_grid(
    [
        (
            "📤",
            "Upload & Analyse",
            "Upload STL files and run the full CDMO pipeline: geometry analysis, flow simulation, buoyancy, scoring, Pareto frontier.",
        ),
        (
            "📈",
            "Sensitivity Analysis",
            "Quantify how geometric parameters influence each objective. Produces publishable rankings and sensitivity curves.",
        ),
        (
            "🖨️",
            "STL Generator",
            "Generate improved carrier geometries parametrically. Cross-flow, honeycomb, lattice, and hybrid topologies.",
        ),
    ],
    columns=3,
)

cards_grid(
    [
        (
            "🗺️",
            "Design Comparison Matrix",
            "Compare all designs via heatmaps and matrices. Identify patterns across geometry families and materials.",
        ),
        (
            "💾",
            "Session Manager",
            "Save complete sessions to disk and reload without re-uploading STL files. Export results and Pareto subsets.",
        ),
        (
            "🧬",
            "GA Optimiser",
            "NSGA‑II genetic algorithm searches the parametric design space to find Pareto‑optimal geometries.",
        ),
    ],
    columns=3,
)

cards_grid(
    [
        (
            "📊",
            "Statistical Analysis",
            "Hypothesis tests, effect sizes, correlations, and regression models for thesis‑citable results.",
        ),
        (
            "📄",
            "PDF Report",
            "One‑click automated thesis‑quality PDF with charts, rankings, stats, Pareto analysis, and geometry metrics.",
        ),
        (
            "📋",
            "Flow & Export",
            "Flow dashboard with Ergun pressure drop curves, porosity‑efficiency plots, and full CSV export.",
        ),
    ],
    columns=3,
)

st.markdown("---")
st.markdown("### 🚀 Recommended Workflow")

steps = [
    ("1", "Upload & Analyse", "Upload all 16 STL files. Select all 4 materials. Run analysis.", "📤"),
    ("2", "Save Session", "Save your session in Session Manager — no re-uploading needed.", "💾"),
    ("3", "Compare Designs", "Open Design Comparison Matrix for the full 16-carrier overview.", "🗺️"),
    ("4", "Sensitivity Analysis", "Run Sensitivity Analysis to identify which parameters matter most.", "📈"),
    ("5", "Run GA Optimiser", "Use the GA to search for better designs beyond your original 16.", "🧬"),
    ("6", "Statistical Analysis", "Run hypothesis tests and correlations for thesis-citable results.", "📊"),
    ("7", "Generate Improvements", "Use STL Generator to create improved designs from GA findings.", "🖨️"),
    ("8", "Export PDF Report", "One-click PDF with all results, charts, and statistics.", "📄"),
]

step_cols = st.columns(4)
for i, (num, title, desc, icon) in enumerate(steps):
    with step_cols[i % 4]:
        st.markdown(
            f"""
            <div class="cdmo-card cdmo-card--soft" style="margin:0.45rem 0;border-left:4px solid var(--cdmo-accent);">
              <b>{icon} Step {num}: {title}</b>
              <p style="color:#555;font-size:0.85rem;margin:0.4rem 0 0;">{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown(
    """
    <div style="text-align:center;color:#64748b;font-size:0.82rem;">
      CDMO Framework · University of Ibadan, Nigeria · Mechanical Engineering Department<br>
      PhD Research: Computational Design and Multi-Objective Optimization of
      3D Printed Biofilm Carriers for Faecal Sludge Treatment
    </div>
    """,
    unsafe_allow_html=True,
)

