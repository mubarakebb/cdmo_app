"""
Parametric STL Generator Page - CDMO Phase 2
Design and generate optimised carrier geometries from scratch.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import io
import trimesh
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
from core.commercial_carriers import (
    COMMERCIAL_CARRIERS,
    compare_to_commercial,
    PUBLISHED_MBBR_TABLE_MD,
    PUBLISHED_MBBR_REFERENCES,
)

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


def stl_mesh_figure(stl_bytes: bytes, title: str = "3D STL View") -> go.Figure:
    """Create an interactive Plotly 3D mesh figure from STL bytes."""
    mesh = trimesh.load(io.BytesIO(stl_bytes), file_type="stl", force="mesh")
    vertices = np.asarray(mesh.vertices)  # type: ignore
    faces = np.asarray(mesh.faces)  # type: ignore

    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                intensity=vertices[:, 2],
                colorscale="Viridis",
                flatshading=True,
                opacity=1.0,
                showscale=False,
                lighting=dict(ambient=0.45, diffuse=0.7, roughness=0.6, specular=0.2),
                lightposition=dict(x=200, y=100, z=150),
            )
        ]
    )
    fig.update_layout(
        title=title,
        height=520,
        margin=dict(l=0, r=0, t=36, b=0),
        scene=dict(
            xaxis_title="X (mm)",
            yaxis_title="Y (mm)",
            zaxis_title="Z (mm)",
            aspectmode="data",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
        ),
    )
    return fig

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
    with open(out_path, "rb") as f:
        stl_bytes = f.read()

    st.markdown("### Generated Design — Verified Metrics")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Surface Area (mm²)", f"{geo.surface_area:,.1f}")
    col2.metric("Volume (mm³)", f"{geo.volume:,.1f}")
    col3.metric("SA/V Ratio (mm⁻¹)", f"{geo.sav_ratio:.4f}")
    col4.metric("Porosity", f"{geo.porosity:.4f}")
    col5.metric("Specific SA (m²/m³)", f"{geo.specific_surface_area:.1f}")

    st.markdown("---")

    st.markdown("### 3D STL Preview")
    st.plotly_chart(
        stl_mesh_figure(stl_bytes, title=f"Generated {params.design_type.replace('_', ' ').title()} Carrier"),
        use_container_width=True,
    )

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

    st.markdown("---")
    st.markdown("### Commercial Carrier Comparison")
    st.caption("How your generated design compares to published MBBR media specifications.")

    # Compare generated design to commercial carriers
    comp_data = compare_to_commercial(
        user_sav=geo.sav_ratio,
        user_porosity=geo.porosity,
        user_specific_sa=geo.specific_surface_area
    )

    col_comp1, col_comp2, col_comp3 = st.columns(3)
    with col_comp1:
        st.markdown("**SA/V Ratio**")
        st.metric(
            "Your Design",
            f"{comp_data['user_sav']:.4f} mm⁻¹",
            f"Percentile: {comp_data['sav_percentile']:.0f}%"
        )
        st.caption(f"vs. {comp_data['mean_commercial_sav']:.4f} (avg)")
    with col_comp2:
        st.markdown("**Porosity**")
        st.metric(
            "Your Design",
            f"{comp_data['user_porosity']:.4f}",
            f"Percentile: {comp_data['porosity_percentile']:.0f}%"
        )
        st.caption(f"vs. {comp_data['mean_commercial_porosity']:.4f} (avg)")
    with col_comp3:
        st.markdown("**Specific SA (m²/m³)**")
        st.metric(
            "Your Design",
            f"{comp_data['user_specific_sa']:.1f}",
            f"Percentile: {comp_data['ssa_percentile']:.0f}%"
        )
        st.caption(f"vs. {comp_data['mean_commercial_ssa']:.1f} (avg)")

    st.markdown("#### Published Commercial Media Specifications")

    # Build comparison table
    comp_rows = []
    comp_rows.append({
        "Product": "🔵 YOUR DESIGN (Generated)",
        "Manufacturer": design_type.replace('_', ' ').title(),
        "Material": "CDMO",
        "SA/V (mm⁻¹)": f"{comp_data['user_sav']:.4f}",
        "Porosity": f"{comp_data['user_porosity']:.4f}",
        "Specific SA (m²/m³)": f"{comp_data['user_specific_sa']:.1f}",
        "Dimensions": f"{outer_diameter:.0f} x {height:.0f} mm",
    })
    for carrier in COMMERCIAL_CARRIERS:
        comp_rows.append({
            "Product": carrier.name,
            "Manufacturer": carrier.manufacturer,
            "Material": carrier.material,
            "SA/V (mm⁻¹)": f"{carrier.sa_v_ratio:.4f}",
            "Porosity": f"{carrier.porosity:.4f}",
            "Specific SA (m²/m³)": f"{carrier.specific_surface_area:.1f}",
            "Dimensions": carrier.dimensions_label,
        })

    import pandas as pd
    comp_df = pd.DataFrame(comp_rows)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    st.markdown("#### Detailed Specifications")
    with st.expander("View commercial carrier details"):
        col_detail = st.columns(1)[0]
        with col_detail:
            selected_product = st.selectbox(
                "View detailed specs for:",
                ["YOUR DESIGN"] + [c.name for c in COMMERCIAL_CARRIERS],
                key="detail_select_gen"
            )

            if selected_product == "YOUR DESIGN":
                st.markdown(f"**🔵 Your CDMO {design_type.title()} Design**")
                det_cols = st.columns(4)
                det_cols[0].metric("SA/V", f"{comp_data['user_sav']:.4f} mm⁻¹")
                det_cols[1].metric("Porosity", f"{comp_data['user_porosity']:.4f}")
                det_cols[2].metric("Specific SA", f"{comp_data['user_specific_sa']:.1f} m²/m³")
                det_cols[3].metric("Material", "CDMO (custom)")
                st.info(
                    f"**Dimensions:** {outer_diameter}mm ⌀ × {height}mm H  \n"
                    f"**Fins:** {num_fins} | **Rings:** {num_rings} | **Spikes:** {num_spikes}"
                )
            else:
                carrier = next((c for c in COMMERCIAL_CARRIERS if c.name == selected_product), None)
                if carrier:
                    st.markdown(f"**{carrier.name}** — {carrier.manufacturer}")
                    det_cols = st.columns(4)
                    det_cols[0].metric("SA/V", f"{carrier.sa_v_ratio:.4f} mm⁻¹")
                    det_cols[1].metric("Porosity", f"{carrier.porosity:.4f}")
                    det_cols[2].metric("Specific SA", f"{carrier.specific_surface_area:.1f} m²/m³")
                    det_cols[3].metric("Material", carrier.material)
                    st.markdown(
                        f"**Biofilm Affinity:** {carrier.biofilm_affinity:.2f}  \n"
                        f"**Clogging Risk:** {carrier.clogging_risk}  \n"
                        f"**Source Type:** {carrier.source_label}  \n"
                        f"**Notes:** {carrier.notes}"
                    )

    st.markdown("#### Published MBBR Table (For Thesis/Publication)")
    st.markdown(PUBLISHED_MBBR_TABLE_MD)
    st.markdown("**References:**")
    for ref in PUBLISHED_MBBR_REFERENCES:
        st.markdown(f"- [{ref}]({ref})")
