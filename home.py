"""
CDMO Landing Page — Premium Folio-theme design
Computational Design and Multi-Objective Optimization Framework
University of Ibadan, Nigeria
"""

import streamlit as st
from utils.ui import inject_base_styles, sidebar_brand, cards_grid, eyebrow

inject_base_styles()
sidebar_brand()

# ─── Hero ─────────────────────────────────────────────────────────────────────
hero_html = """<div style="position:relative;overflow:hidden;padding:3rem 2.5rem 2.8rem;background:linear-gradient(135deg,#0a0b14 0%,#10121f 50%,#0d1320 100%);border-radius:var(--radius-xl);margin-bottom:1.8rem;box-shadow:0 20px 60px rgba(0,0,0,0.22);">
  <div class="cdmo-orb cdmo-orb-purple" style="width:560px;height:560px;top:-200px;right:-80px;opacity:0.55;"></div>
  <div class="cdmo-orb cdmo-orb-blue" style="width:320px;height:320px;bottom:-100px;left:-60px;opacity:0.50;"></div>
  <div class="cdmo-orb" style="width:200px;height:200px;background:var(--orb-teal);top:60%;right:30%;filter:blur(60px);animation:cdmo-drift 9s ease-in-out infinite alternate;"></div>
  <div style="position:relative;z-index:1;">
    <div class="cdmo-reveal cdmo-reveal-1">
      <span style="display:inline-flex;align-items:center;gap:0.5rem;padding:0.3rem 0.85rem;border-radius:var(--radius-pill);background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);font-size:0.75rem;font-weight:600;color:rgba(255,255,255,0.7);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:1.1rem;">
        🎓 University of Ibadan · PhD Research
      </span>
    </div>
    <h1 class="cdmo-reveal cdmo-reveal-2" style="font-family:var(--font-heading);font-size:clamp(2rem,5vw,3.2rem);font-weight:800;line-height:1.1;letter-spacing:-0.04em;color:#fff;margin:0 0 0.75rem;">
      Computational Design &<br><span style="background:linear-gradient(135deg,#2E86AB,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Multi-Objective Optimization</span>
    </h1>
    <p class="cdmo-reveal cdmo-reveal-3" style="font-size:1.05rem;color:rgba(255,255,255,0.62);max-width:560px;line-height:1.65;margin:0 0 2rem;">
      Evaluate, compare and evolve 3D-printed biofilm carriers for faecal sludge treatment — geometry analysis, flow simulation, NSGA-II optimisation and automated thesis reporting in one platform.
    </p>
    <div class="cdmo-reveal cdmo-reveal-4" style="display:flex;flex-wrap:wrap;gap:0.6rem;">
      <span style="display:inline-flex;align-items:center;gap:0.4rem;padding:0.35rem 0.85rem;border-radius:var(--radius-pill);background:rgba(46,134,171,0.18);border:1px solid rgba(46,134,171,0.35);font-size:0.8rem;font-weight:600;color:#7ec8e3;">✓ STL Geometry Analysis</span>
      <span style="display:inline-flex;align-items:center;gap:0.4rem;padding:0.35rem 0.85rem;border-radius:var(--radius-pill);background:rgba(99,102,241,0.18);border:1px solid rgba(99,102,241,0.35);font-size:0.8rem;font-weight:600;color:#a5b4fc;">✓ NSGA-II Genetic Algorithm</span>
      <span style="display:inline-flex;align-items:center;gap:0.4rem;padding:0.35rem 0.85rem;border-radius:var(--radius-pill);background:rgba(20,184,166,0.15);border:1px solid rgba(20,184,166,0.30);font-size:0.8rem;font-weight:600;color:#5eead4;">✓ Pareto Frontier Analysis</span>
      <span style="display:inline-flex;align-items:center;gap:0.4rem;padding:0.35rem 0.85rem;border-radius:var(--radius-pill);background:rgba(249,115,22,0.15);border:1px solid rgba(249,115,22,0.30);font-size:0.8rem;font-weight:600;color:#fdba74;">✓ Automated PDF Reports</span>
    </div>
  </div>
</div>"""
st.markdown(hero_html, unsafe_allow_html=True)

# ─── Live session stats (if data is loaded) ──────────────────────────────────
if st.session_state.get("all_carriers"):
    carriers = st.session_state.all_carriers
    n_geo    = len({c.filename for c in carriers})
    n_pareto = len([c for c in carriers if c.is_pareto_optimal])
    best     = min(carriers, key=lambda c: c.rank)

    eyebrow("Current session")
    st.markdown(
        f"""
        <div class="cdmo-stats-grid cdmo-reveal cdmo-reveal-1"
             style="margin-bottom:1.8rem;">
          <div class="cdmo-stat">
            <div class="cdmo-stat-value">{n_geo}</div>
            <div class="cdmo-stat-label">Geometries analysed</div>
          </div>
          <div class="cdmo-stat">
            <div class="cdmo-stat-value">{len(carriers)}</div>
            <div class="cdmo-stat-label">Design–material combos</div>
          </div>
          <div class="cdmo-stat">
            <div class="cdmo-stat-value">{n_pareto}</div>
            <div class="cdmo-stat-label">Pareto-optimal designs</div>
          </div>
          <div class="cdmo-stat">
            <div class="cdmo-stat-value"
                 style="font-size:1.1rem;padding-top:0.3rem;">
              {best.filename.replace('.stl','')[:14]}
            </div>
            <div class="cdmo-stat-label">Top design (score {best.composite_score:.3f})</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<hr style="margin:0.5rem 0 1.5rem;">', unsafe_allow_html=True)

# ─── Research stats row ───────────────────────────────────────────────────────
else:
    st.markdown(
        """
        <div class="cdmo-stats-grid cdmo-reveal cdmo-reveal-1"
             style="margin-bottom:1.8rem;">
          <div class="cdmo-stat">
            <div class="cdmo-stat-value"
                 style="background:linear-gradient(135deg,#2E86AB,#6366f1);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;">16</div>
            <div class="cdmo-stat-label">Carrier designs in study</div>
          </div>
          <div class="cdmo-stat">
            <div class="cdmo-stat-value"
                 style="background:linear-gradient(135deg,#2E86AB,#6366f1);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;">4</div>
            <div class="cdmo-stat-label">Polymer materials evaluated</div>
          </div>
          <div class="cdmo-stat">
            <div class="cdmo-stat-value"
                 style="background:linear-gradient(135deg,#2E86AB,#6366f1);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;">6</div>
            <div class="cdmo-stat-label">Performance objectives</div>
          </div>
          <div class="cdmo-stat">
            <div class="cdmo-stat-value"
                 style="background:linear-gradient(135deg,#2E86AB,#6366f1);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;">3</div>
            <div class="cdmo-stat-label">Research phases (CDMO)</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─── Module feature grid ──────────────────────────────────────────────────────
eyebrow("Core modules")
st.markdown(
    """
    <h2 style="font-family:var(--font-heading);
               font-size:clamp(1.4rem,3vw,1.85rem);
               font-weight:800;letter-spacing:-0.03em;
               color:var(--text-primary);
               margin:0.2rem 0 1.2rem;">
      Eight integrated tools, one platform
    </h2>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4, gap="medium")

_MODULES = [
    ("📤", "Upload & Analyse",
     "Full CDMO pipeline — geometry, Ergun flow, Archimedes buoyancy, weighted scoring and Pareto frontier.",
     "blue"),
    ("📈", "Sensitivity Analysis",
     "One-at-a-time sensitivity quantification. Identifies which geometric parameters drive each objective.",
     "blue"),
    ("🖨️", "STL Generator",
     "Parametric carrier generation — cross-flow, honeycomb, lattice and hybrid topologies with live 3D preview.",
     ""),
    ("🗺️", "Design Comparison",
     "Heatmaps and matrix views for all 16 designs × 4 materials = 64 combinations simultaneously.",
     ""),
    ("💾", "Session Manager",
     "Save and reload complete sessions as portable JSON. No STL re-uploading across research sessions.",
     ""),
    ("🧬", "GA Optimiser",
     "NSGA-II genetic algorithm with SBX crossover and polynomial mutation — finds Pareto-optimal geometries.",
     "orange"),
    ("📊", "Statistical Analysis",
     "ANOVA, Kruskal-Wallis, Bonferroni correction, Cohen's d, Pearson / Spearman correlations and linear regression.",
     "orange"),
    ("📄", "PDF Report",
     "One-click automated thesis-quality PDF with charts, rankings, Pareto analysis and full statistics.",
     "orange"),
]

pairs = [_MODULES[i:i+4] for i in range(0, len(_MODULES), 4)]
for row_modules in pairs:
    cols = st.columns(4, gap="medium")
    for col, (icon, title, body, variant) in zip(cols, row_modules):
        border_accent = {
            "blue":   "border-top:3px solid var(--accent);",
            "orange": "border-top:3px solid var(--accent-orange);",
        }.get(variant, "border-top:3px solid var(--accent-indigo);")
        with col:
            st.markdown(
                f"""
                <div class="cdmo-feature-card" style="{border_accent}">
                  <div class="cdmo-icon-box" style="width:40px;height:40px;font-size:1.15rem;">
                    {icon}
                  </div>
                  <p class="cdmo-feature-card-title">{title}</p>
                  <p class="cdmo-feature-card-body">{body}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─── Recommended workflow ──────────────────────────────────────────────────────
col_steps, col_context = st.columns([3, 2], gap="large")

with col_steps:
    eyebrow("Recommended workflow")
    st.markdown(
        """
        <h2 style="font-family:var(--font-heading);font-size:1.55rem;
                   font-weight:800;letter-spacing:-0.03em;
                   color:var(--text-primary);margin:0.2rem 0 1rem;">
          From STL files to thesis-ready results
        </h2>
        """,
        unsafe_allow_html=True,
    )

    steps = [
        ("01", "Upload & Analyse",
         "Upload all STL files, select all 4 materials, run the full CDMO pipeline."),
        ("02", "Save Session",
         "Save to the Session Manager — no re-uploading needed in future sessions."),
        ("03", "Compare & Identify",
         "Open Design Comparison to find patterns across the 16 × 4 matrix."),
        ("04", "Sensitivity Analysis",
         "Discover which geometric parameters drive each objective."),
        ("05", "Run GA Optimiser",
         "Evolve Pareto-optimal geometries beyond your original 16 designs."),
        ("06", "Statistical Validation",
         "ANOVA, effect sizes and correlations for peer-reviewed reporting."),
        ("07", "Generate Improved STLs",
         "Produce improved carriers from GA findings via the STL Generator."),
        ("08", "Export PDF Report",
         "One-click thesis-quality PDF with all results, charts and statistics."),
    ]

    for num, title, desc in steps:
        st.markdown(
            f"""
            <div class="cdmo-step">
              <div class="cdmo-step-num">{num}</div>
              <div>
                <div class="cdmo-step-title">{title}</div>
                <div class="cdmo-step-body">{desc}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_context:
    eyebrow("Research context")
    st.markdown(
        """
        <h2 style="font-family:var(--font-heading);font-size:1.55rem;
                   font-weight:800;letter-spacing:-0.03em;
                   color:var(--text-primary);margin:0.2rem 0 1rem;">
          About this framework
        </h2>
        """,
        unsafe_allow_html=True,
    )

    context_items = [
        ("🔬", "Research scope",
         "Evaluates 3D-printed Moving Bed Biofilm Reactor (MBBR) carriers for decentralised faecal sludge treatment in Sub-Saharan Africa."),
        ("⚙️", "Physics models",
         "Ergun equation, Kozeny-Carman permeability, Wilson-Geankoplis mass transfer and Archimedes buoyancy — all computed from STL geometry."),
        ("🧬", "Optimisation",
         "NSGA-II with non-dominated sorting, crowding distance, simulated binary crossover and polynomial mutation over a 10-parameter design space."),
        ("📊", "Statistics",
         "ANOVA / Kruskal-Wallis, Bonferroni-corrected pairwise tests, Cohen's d effect sizes, Pearson / Spearman correlations, linear regression."),
    ]

    for icon, title, body in context_items:
        st.markdown(
            f"""
            <div class="cdmo-card cdmo-card--accent"
                 style="margin-bottom:0.75rem;padding:1rem 1.15rem;">
              <div style="display:flex;align-items:flex-start;gap:0.8rem;">
                <div class="cdmo-icon-box"
                     style="width:36px;height:36px;font-size:1rem;
                            flex-shrink:0;margin-bottom:0;">
                  {icon}
                </div>
                <div>
                  <div style="font-family:var(--font-heading);font-size:0.88rem;
                               font-weight:700;color:var(--text-primary);
                               margin-bottom:0.2rem;">{title}</div>
                  <div style="font-size:0.8rem;color:var(--text-secondary);
                               line-height:1.55;">{body}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Material reference
    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
    eyebrow("Materials database")
    st.markdown(
        """
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin-top:0.3rem;">
          <div class="cdmo-card" style="padding:0.75rem 0.9rem;">
            <div style="font-weight:800;font-size:0.85rem;color:#4CAF50;">PLA</div>
            <div style="font-size:0.75rem;color:var(--text-muted);">1.24 g/cm³ · Biofilm ★★★★★</div>
          </div>
          <div class="cdmo-card" style="padding:0.75rem 0.9rem;">
            <div style="font-weight:800;font-size:0.85rem;color:#2196F3;">ABS</div>
            <div style="font-size:0.75rem;color:var(--text-muted);">1.05 g/cm³ · Biofilm ★★★★☆</div>
          </div>
          <div class="cdmo-card" style="padding:0.75rem 0.9rem;">
            <div style="font-weight:800;font-size:0.85rem;color:#FF9800;">PETG</div>
            <div style="font-size:0.75rem;color:var(--text-muted);">1.28 g/cm³ · Biofilm ★★★☆☆</div>
          </div>
          <div class="cdmo-card" style="padding:0.75rem 0.9rem;">
            <div style="font-weight:800;font-size:0.85rem;color:#9C27B0;">PP</div>
            <div style="font-size:0.75rem;color:var(--text-muted);">0.91 g/cm³ · Biofilm ★★★☆☆</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="text-align:center;padding:0.5rem 0 0.25rem;">
      <div style="font-family:var(--font-heading);font-weight:800;
                  font-size:0.95rem;color:var(--text-primary);
                  letter-spacing:-0.01em;margin-bottom:0.3rem;">
        CDMO Studio
      </div>
      <div style="font-size:0.78rem;color:var(--text-muted);line-height:1.6;">
        University of Ibadan · Department of Mechanical Engineering<br>
        PhD Research — Computational Design &amp; Multi-Objective Optimization
        of 3D Printed Biofilm Carriers for Faecal Sludge Treatment
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
