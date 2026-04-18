"""
Parametric STL Generator Page - CDMO Phase 2
Design and generate optimised carrier geometries from scratch.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.ui import HeaderSpec, page_header, sidebar_brand

from core.stl_generator import CarrierParams, generate_carrier_stl
from core.geometry import analyze_stl
from core.flow_analysis import compute_flow_metrics
from core.buoyancy import compare_materials_buoyancy
from core.materials import FLUID_PROPERTIES

st.set_page_config(page_title="STL Generator", page_icon="🖨️", layout="wide")

page_header(
    HeaderSpec(
        icon="🖨️",
        title="Parametric STL Generator",
        subtitle="Design and generate optimised carrier geometries based on target parameters.",
        accent="#6C3483",
        accent_2="#1A5276",
    )
)
sidebar_brand()

st.markdown(
    """
    <style>
      .metric-card{
        background: var(--cdmo-surface-2);
        border: 1px solid rgba(15, 23, 42, 0.10);
        border-left: 4px solid var(--cdmo-accent);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin: 0.4rem 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
Generate new STL files directly from the CDMO framework.
Adjust geometric parameters, preview the predicted performance metrics,
and download the STL for 3D printing validation.
""")

# ─── Sidebar: Design Parameters ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Design Parameters")

    design_type = st.selectbox(
        "Design Topology",
        ["cross_flow", "honeycomb", "lattice", "hybrid"],
        format_func=lambda x: {
            "cross_flow": "Cross-Flow (radial fins + rings)",
            "honeycomb": "Honeycomb (hexagonal cells)",
            "lattice": "Lattice (diagonal struts)",
            "hybrid": "Hybrid (fins + offset layers)"
        }[x]
    )

    st.markdown("### Envelope")
    outer_diameter = st.slider("Outer Diameter (mm)", 15.0, 80.0, 25.0, 0.5)
    height = st.slider("Height (mm)", 5.0, 40.0, 12.0, 0.5)
    wall_thickness = st.slider("Wall Thickness (mm)", 0.5, 3.0, 1.2, 0.1)

    st.markdown("### Internal Structure")
    num_fins = st.slider("Number of Fins", 3, 20, 8)
    fin_thickness = st.slider("Fin Thickness (mm)", 0.4, 2.5, 0.8, 0.1)
    num_rings = st.slider("Concentric Rings", 0, 5, 2)
    ring_gap = st.slider("Ring Gap (mm)", 1.0, 10.0, 3.0, 0.5)

    st.markdown("### Surface Features")
    num_spikes = st.slider("Outer Spikes", 0, 24, 12)
    spike_height = st.slider("Spike Height (mm)", 0.5, 6.0, 2.0, 0.25)
    spike_base = st.slider("Spike Base Width (mm)", 0.5, 4.0, 1.5, 0.25)

    st.markdown("### Mesh Quality")
    angular_segments = st.select_slider(
        "Curve Segments", [16, 32, 48, 64, 96], value=48,
        help="Higher = smoother curves, larger file")

    generate_btn = st.button("🖨️ Generate STL", type="primary",
                              use_container_width=True)

# ─── Build params object ──────────────────────────────────────────────────────
params = CarrierParams(
    outer_diameter=outer_diameter,
    height=height,
    wall_thickness=wall_thickness,
    num_fins=num_fins,
    fin_thickness=fin_thickness,
    num_rings=num_rings,
    ring_gap=ring_gap,
    num_spikes=num_spikes,
    spike_height=spike_height,
    spike_base=spike_base,
    design_type=design_type,
    angular_segments=angular_segments,
)

# ─── Live parameter preview ───────────────────────────────────────────────────
st.markdown("### Design Parameter Summary")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Outer Diameter", f"{outer_diameter} mm")
col2.metric("Height", f"{height} mm")
col3.metric("Wall Thickness", f"{wall_thickness} mm")
col4.metric("Design Type", design_type.replace("_", " ").title())

col5, col6, col7, col8 = st.columns(4)
col5.metric("Fins", num_fins)
col6.metric("Rings", num_rings)
col7.metric("Spikes", num_spikes)
col8.metric("Segments", angular_segments)

st.markdown("---")

# ─── Estimated metrics (before generation) ───────────────────────────────────
st.markdown("### Estimated Performance Metrics")
st.caption("Geometric estimates based on parameters. Run generation for precise values.")

r = outer_diameter / 2
bb_vol = outer_diameter * outer_diameter * height  # bounding box mm³

# Rough surface area estimate
outer_sa = 2 * np.pi * r * height + 2 * np.pi * r**2
fin_sa = num_fins * 2 * (r - wall_thickness) * height
ring_sa = num_rings * 2 * np.pi * (r * 0.5) * height * 0.3
spike_sa = num_spikes * spike_height * spike_base * 2
est_sa = outer_sa + fin_sa + ring_sa + spike_sa

# Rough volume estimate (solid minus voids)
shell_vol = np.pi * ((r**2) - (r - wall_thickness)**2) * height
fin_vol = num_fins * (r - wall_thickness) * fin_thickness * height
ring_vol = num_rings * np.pi * ((r * 0.5 + wall_thickness/4)**2 -
                                  (r * 0.5 - wall_thickness/4)**2) * height * 0.3
est_vol = shell_vol + fin_vol + ring_vol
est_porosity = max(0.1, 1 - est_vol / bb_vol)
est_sav = est_sa / est_vol if est_vol > 0 else 0

col_e1, col_e2, col_e3, col_e4 = st.columns(4)
col_e1.metric("Est. Surface Area", f"{est_sa:,.0f} mm²")
col_e2.metric("Est. Volume", f"{est_vol:,.0f} mm³")
col_e3.metric("Est. SA/V Ratio", f"{est_sav:.3f} mm⁻¹")
col_e4.metric("Est. Porosity", f"{est_porosity:.3f}")

st.markdown("---")

# ─── Generation ───────────────────────────────────────────────────────────────
if generate_btn:
    with st.spinner(f"Generating {design_type} carrier..."):
        try:
            out_path, gen_mesh = generate_carrier_stl(params)
            st.session_state.generated_stl_path = out_path
            st.session_state.generated_params = params

            # Analyse the generated STL
            geo = analyze_stl(out_path)
            geo.filename = f"generated_{design_type}.stl"
            st.session_state.generated_geo = geo

            st.success(f"✅ STL generated successfully! "
                       f"{geo.num_triangles:,} triangles, "
                       f"watertight: {geo.is_watertight}")
        except Exception as e:
            st.error(f"Generation failed: {e}")

if "generated_geo" in st.session_state:
    geo = st.session_state.generated_geo
    out_path = st.session_state.generated_stl_path

    st.markdown("### Generated Design — Verified Metrics")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Surface Area (mm²)", f"{geo.surface_area:,.1f}")
    col2.metric("Volume (mm³)", f"{geo.volume:,.1f}")
    col3.metric("SA/V Ratio (mm⁻¹)", f"{geo.sav_ratio:.4f}")
    col4.metric("Porosity", f"{geo.porosity:.4f}")
    col5.metric("Specific SA (m²/m³)", f"{geo.specific_surface_area:.1f}")

    st.markdown("---")

    # Flow and buoyancy quick analysis
    st.markdown("### Performance Preview")
    fluid = FLUID_PROPERTIES["faecal_sludge_medium"]
    flow = compute_flow_metrics(geo, 0.01, fluid["density"], fluid["viscosity"])
    buoyancy_map = compare_materials_buoyancy(geo, fluid["density"])

    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric("Flow Regime", flow.flow_regime)
    col_f2.metric("Clogging Risk", flow.clogging_risk)
    col_f3.metric("Flow Efficiency Score", f"{flow.flow_efficiency_score:.4f}")

    st.markdown("**Buoyancy by Material**")
    bcols = st.columns(4)
    for i, (mat, bm) in enumerate(buoyancy_map.items()):
        icon = "🟢" if bm.behavior == "Neutrally Buoyant" else \
               "🟡" if bm.behavior == "Floats" else "🔴"
        bcols[i].metric(f"{icon} {mat}", bm.behavior,
                        f"{bm.effective_density:.3f} g/cm³")

    st.markdown("---")

    # Comparison: estimated vs actual
    st.markdown("### Estimate vs Actual Comparison")
    comparison_df = {
        "Metric": ["Surface Area (mm²)", "Volume (mm³)", "SA/V Ratio (mm⁻¹)", "Porosity"],
        "Estimated": [f"{est_sa:,.0f}", f"{est_vol:,.0f}",
                      f"{est_sav:.3f}", f"{est_porosity:.3f}"],
        "Actual (STL)": [f"{geo.surface_area:,.1f}", f"{geo.volume:,.1f}",
                         f"{geo.sav_ratio:.4f}", f"{geo.porosity:.4f}"],
    }
    import pandas as pd
    st.dataframe(pd.DataFrame(comparison_df), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Download
    st.markdown("### Download Generated STL")
    with open(out_path, "rb") as f:
        stl_bytes = f.read()

    design_name = f"cdmo_{design_type}_D{int(outer_diameter)}H{int(height)}_fins{num_fins}.stl"
    st.download_button(
        label="⬇️ Download STL File",
        data=stl_bytes,
        file_name=design_name,
        mime="application/octet-stream",
        use_container_width=True,
        type="primary"
    )
    st.caption(f"File: {design_name} | "
               f"Size: {len(stl_bytes)/1024:.1f} KB | "
               f"Triangles: {geo.num_triangles:,}")
