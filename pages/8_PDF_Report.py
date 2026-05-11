"""
PDF Report Generator Page - CDMO Phase 3
Generate automated thesis-quality PDF reports from analysis results.
"""

import streamlit as st
import os
import tempfile

from utils.ui import HeaderSpec, page_header, sidebar_brand

from utils.report_generator import generate_pdf_report
from core.statistics import run_full_statistical_analysis

st.set_page_config(page_title="PDF Report", page_icon="📄", layout="wide")

page_header(
    HeaderSpec(
        icon="📄",
        title="Automated PDF Report",
        subtitle="Generate a thesis-quality analysis report with charts and statistics.",
        accent="#4A235A",
        accent_2="#1A5276",
    )
)
sidebar_brand()

st.markdown("""
The report includes: executive summary, performance rankings, Pareto frontier,
radar charts, bar charts, statistical tests, correlation analysis, regression models,
and full geometry metrics — all in a single professionally formatted PDF.
""")

if not st.session_state.get("all_carriers"):
    st.info("📤 Upload and analyse STL files on the main page first.")
    st.stop()

carriers = st.session_state.all_carriers
results  = st.session_state.get("results", [])

# ─── Report Configuration ────────────────────────────────────────────────────
st.markdown("### Report Configuration")
col1, col2 = st.columns(2)
with col1:
    include_stats = st.checkbox("Include statistical analysis", value=True)
    include_charts = st.checkbox("Include charts and visualisations", value=True)
with col2:
    n_geo = len(set(c.filename for c in carriers))
    n_pareto = len([c for c in carriers if c.is_pareto_optimal])
    st.metric("Designs in report", n_geo)
    st.metric("Pareto-optimal designs", n_pareto)

# Analysis params snapshot
analysis_params = {
    "fluid_type": "Faecal Sludge Medium",
    "fluid_density": 1015.0,
    "fluid_viscosity": 0.003,
    "flow_velocity": 0.01,
    "weights": {
        "SA/V Ratio": 0.30, "Porosity": 0.20,
        "Flow Efficiency": 0.20, "Buoyancy": 0.15,
        "Biofilm Affinity": 0.10, "Mechanical": 0.05,
    }
}

st.markdown("---")

generate_btn = st.button("📄 Generate PDF Report", type="primary", use_container_width=False)

if generate_btn:
    with st.spinner("Generating PDF report (this may take 30-60 seconds)..."):
        try:
            # Run stats if requested
            stat_report = None
            if include_stats:
                stat_report = run_full_statistical_analysis(carriers)
                st.session_state.stat_report = stat_report

            pdf_path = generate_pdf_report(
                carriers=carriers,
                results=results,
                stat_report=stat_report,
                analysis_params=analysis_params,
            )

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            os.unlink(pdf_path)

            st.session_state.pdf_bytes = pdf_bytes
            st.success(f"✅ Report generated ({len(pdf_bytes)/1024:.0f} KB)")

        except Exception as e:
            st.error(f"Report generation failed: {e}")
            st.exception(e)

if "pdf_bytes" in st.session_state:
    st.download_button(
        label="⬇️ Download PDF Report",
        data=st.session_state.pdf_bytes,
        file_name="CDMO_Analysis_Report.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )

    st.markdown("---")
    st.markdown("### Report Contents")
    sections = [
        ("Cover Page", "Title, metadata, KPI summary boxes"),
        ("1. Executive Summary", "Key findings narrative, analysis parameters, objective weights"),
        ("2. Performance Rankings", "Top 20 table, Pareto-optimal designs table"),
        ("3. Performance Visualisations", "Composite score bar chart, radar profile of top 5"),
        ("4. Pareto Frontier Analysis", "SA/V vs Flow Efficiency scatter, material box plot"),
        ("5. Statistical Analysis", "ANOVA/Kruskal-Wallis, pairwise comparisons, correlation matrix, regression models"),
        ("6. Geometric Performance Summary", "Full geometry metrics for all evaluated designs"),
    ]

    for title, desc in sections:
        st.markdown(f"""
        <div style="display:flex;gap:1rem;padding:0.5rem 0;border-bottom:1px solid #eee;">
            <div style="font-weight:bold;min-width:220px;color:#1a5276;">{title}</div>
            <div style="color:#555;font-size:0.9rem;">{desc}</div>
        </div>""", unsafe_allow_html=True)
