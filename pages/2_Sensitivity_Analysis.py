"""
Sensitivity Analysis Page - CDMO Phase 2
Quantifies how each geometric parameter influences performance objectives.
Supports two input modes: STL file upload or manual parameter entry.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os

from utils.ui import HeaderSpec, page_header, sidebar_brand

from core.sensitivity import run_sensitivity_analysis, get_sensitivity_matrix
from core.geometry import GeometryMetrics, analyze_stl
from core.materials import MATERIALS, FLUID_PROPERTIES
import tempfile

st.set_page_config(page_title="Sensitivity Analysis", page_icon="📈", layout="wide")

page_header(
    HeaderSpec(
        icon="📈",
        title="Sensitivity Analysis",
        subtitle="Quantify how geometric parameters influence each performance objective.",
        accent="#117A65",
        accent_2="#1A5276",
    )
)
sidebar_brand()

st.markdown("""
Sensitivity analysis answers the question: **which geometric parameters matter most?**
This is a core research contribution, it shows which design variables have the greatest
influence on biofilm carrier performance and in which direction.
""")


# ─── Helper: build GeometryMetrics from manual inputs ────────────────────────

def _build_manual_geo(
    sav_ratio: float,
    porosity: float,
    hydraulic_diameter: float,
    specific_surface_area: float,
) -> GeometryMetrics:
    """
    Construct a synthetic GeometryMetrics from four user-supplied values.
    Uses a normalised unit bounding box (1 000 mm³) to derive internally
    consistent volume and surface_area values.  The absolute scale does not
    affect sensitivity indices because all sweep ranges are expressed as
    multiples of these baseline values.
    """
    bb_vol     = 1000.0                        # mm³ — normalised unit carrier
    volume     = bb_vol * (1.0 - porosity)
    surf_area  = sav_ratio * volume

    return GeometryMetrics(
        filename              = "manual_input",
        sav_ratio             = sav_ratio,
        porosity              = porosity,
        hydraulic_diameter    = hydraulic_diameter,
        specific_surface_area = specific_surface_area,
        surface_area          = surf_area,
        volume                = volume,
        bounding_box_volume   = bb_vol,
        is_watertight         = True,
        is_winding_consistent = True,
    )


# ─── Sidebar controls ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Sensitivity Settings")

    # ── Input mode toggle ────────────────────────────────────────────────────
    input_mode = st.radio(
        "Input Mode",
        ["📁 Upload STL File", "✏️ Enter Values Manually"],
        horizontal=True,
        help="Choose whether to derive baseline geometry from an STL file "
             "or enter the four key parameters directly.",
    )

    stl_mode    = input_mode.startswith("📁")
    manual_mode = not stl_mode

    st.markdown("---")

    # ── Mode-specific geometry inputs ────────────────────────────────────────
    uploaded = None
    manual_sav = manual_porosity = manual_hd = manual_ssa = None

    if stl_mode:
        uploaded = st.file_uploader(
            "Reference STL file",
            type=["stl"],
            help="Upload a carrier to use as the baseline for sensitivity analysis.",
        )
    else:
        st.markdown("#### Baseline Geometry")
        manual_sav = st.number_input(
            "SA/V Ratio (mm⁻¹)",
            min_value=0.05, max_value=20.0,
            value=1.5, step=0.05, format="%.2f",
            help="Surface area to volume ratio of the carrier.",
        )
        manual_porosity = st.number_input(
            "Porosity (0 – 1)",
            min_value=0.10, max_value=0.95,
            value=0.60, step=0.01, format="%.2f",
            help="Void fraction is theratio of open space to total bounding volume.",
        )
        manual_hd = st.number_input(
            "Hydraulic Diameter (mm)",
            min_value=0.1, max_value=100.0,
            value=5.0, step=0.1, format="%.1f",
            help="Characteristic flow length (4ε / specific surface area).",
        )
        manual_ssa = st.number_input(
            "Specific Surface Area (m²/m³)",
            min_value=10.0, max_value=10000.0,
            value=500.0, step=10.0, format="%.0f",
            help="Surface area per unit bulk volume, used in reactor design.",
        )

    st.markdown("---")

    # ── Shared operating conditions ──────────────────────────────────────────
    st.markdown("#### Operating Conditions")
    material = st.selectbox("Material", list(MATERIALS.keys()))

    fluid_type = st.selectbox(
        "Fluid", list(FLUID_PROPERTIES.keys()),
        format_func=lambda x: FLUID_PROPERTIES[x]["name"], index=2,
    )
    fluid = FLUID_PROPERTIES[fluid_type]

    fluid_density   = st.number_input("Density (kg/m³)",  990.0, 1100.0,
                                       float(fluid["density"]),   1.0)
    fluid_viscosity = st.number_input("Viscosity (Pa·s)", 0.0005, 0.02,
                                       float(fluid["viscosity"]), 0.0005,
                                       format="%.4f")
    flow_velocity = st.slider("Flow Velocity (m/s)", 0.001, 0.1, 0.01, 0.001,
                               format="%.3f")
    n_points = st.slider("Resolution (sample points)", 10, 40, 20,
                          help="More points = smoother curves but slower analysis.")

    run_btn = st.button("▶ Run Sensitivity Analysis", type="primary",
                         use_container_width=True)


# ─── Readiness gate ───────────────────────────────────────────────────────────
ready = (stl_mode and uploaded is not None) or manual_mode

if not ready:
    st.info("📤 Upload an STL file in the sidebar to begin sensitivity analysis.")
    st.stop()


# ─── Run analysis ─────────────────────────────────────────────────────────────
# Re-run when button pressed OR when no cached report exists yet
if run_btn or ("sensitivity_report" not in st.session_state):
    with st.spinner("Running sensitivity analysis…"):
        try:
            if stl_mode and uploaded:
                # STL path: write temp file → analyze_stl
                with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
                    tmp.write(uploaded.getvalue())
                    tmp_path = tmp.name
                try:
                    geo = analyze_stl(tmp_path)
                    geo.filename = uploaded.name
                finally:
                    os.unlink(tmp_path)

            else:
                # Manual path: construct synthetic GeometryMetrics
                geo = _build_manual_geo(
                    sav_ratio             = manual_sav,
                    porosity              = manual_porosity,
                    hydraulic_diameter    = manual_hd,
                    specific_surface_area = manual_ssa,
                )

            report = run_sensitivity_analysis(
                geo, material, fluid_density, fluid_viscosity,
                flow_velocity, n_points,
            )
            st.session_state.sensitivity_report = report
            st.session_state.sensitivity_geo    = geo
            st.session_state.sensitivity_mode   = "manual" if manual_mode else "stl"

        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

if "sensitivity_report" not in st.session_state:
    st.stop()

report = st.session_state.sensitivity_report
geo    = st.session_state.sensitivity_geo
is_manual = st.session_state.get("sensitivity_mode") == "manual"

# ─── Baseline info banner (manual mode) ──────────────────────────────────────
if is_manual:
    st.info(
        f"**Manual baseline** - "
        f"SA/V: {geo.sav_ratio:.2f} mm⁻¹ · "
        f"Porosity: {geo.porosity:.2f} · "
        f"Dₕ: {geo.hydraulic_diameter:.1f} mm · "
        f"SSA: {geo.specific_surface_area:.0f} m²/m³"
    )

# ─── Summary KPIs ─────────────────────────────────────────────────────────────
st.markdown("### Key Findings")
col1, col2, col3 = st.columns(3)
col1.metric("Most Influential Parameter",  report.most_influential_parameter)
col2.metric("Most Sensitive Objective",    report.most_sensitive_objective)
col3.metric("Parameters Analysed",         len(report.parameter_importance))

st.markdown("---")

# ─── Parameter Importance Bar Chart ──────────────────────────────────────────
st.markdown("### Parameter Importance Rankings")
st.caption("Global sensitivity index: normalised range of objective response. "
           "Higher = more influential on overall performance.")

importance_df = pd.DataFrame([
    {"Parameter": k, "Global Sensitivity Index": v}
    for k, v in report.parameter_importance.items()
])

fig_importance = px.bar(
    importance_df.sort_values("Global Sensitivity Index"),
    x="Global Sensitivity Index", y="Parameter",
    orientation="h",
    color="Global Sensitivity Index",
    color_continuous_scale="Blues",
    title="Parameter Global Sensitivity (averaged across all objectives)"
)
fig_importance.update_layout(height=300, plot_bgcolor="white",
                               coloraxis_showscale=False)
fig_importance.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
st.plotly_chart(fig_importance, use_container_width=True)

st.markdown("---")

# ─── Sensitivity Heatmap ──────────────────────────────────────────────────────
st.markdown("### Sensitivity Heatmap: Parameter × Objective")
st.caption("Each cell shows how strongly varying that parameter affects that objective. "
           "Darker = stronger sensitivity.")

matrix_data = get_sensitivity_matrix(report)
params      = matrix_data["parameters"]
objectives  = matrix_data["objectives"]
matrix      = np.array(matrix_data["matrix"])

fig_heat = go.Figure(data=go.Heatmap(
    z=matrix,
    x=objectives,
    y=params,
    colorscale="YlOrRd",
    text=np.round(matrix, 3),
    texttemplate="%{text}",
    textfont={"size": 11},
    colorbar=dict(title="Sensitivity Index"),
))
fig_heat.update_layout(
    title="Sensitivity Index Matrix",
    xaxis_title="Performance Objective",
    yaxis_title="Geometric Parameter",
    height=320,
    xaxis=dict(side="bottom"),
)
st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# ─── Interactive Sensitivity Curves ──────────────────────────────────────────
st.markdown("### Sensitivity Curves")
st.caption("Select a parameter and objective to explore their relationship in detail.")

col_p, col_o = st.columns(2)
all_params = list(dict.fromkeys(r.parameter_name for r in report.results))
all_objs   = list(dict.fromkeys(r.objective_name  for r in report.results))

with col_p:
    sel_param = st.selectbox("Parameter", all_params)
with col_o:
    sel_obj = st.selectbox("Objective", all_objs)

matching = [r for r in report.results
            if r.parameter_name == sel_param and r.objective_name == sel_obj]

if matching:
    r = matching[0]
    fig_curve = go.Figure()
    fig_curve.add_trace(go.Scatter(
        x=r.parameter_values,
        y=r.objective_values,
        mode="lines+markers",
        line=dict(color="#2e86ab", width=2.5),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(46,134,171,0.08)",
    ))

    # Baseline vertical marker
    baseline_x = getattr(geo, {
        "SA/V Ratio (mm⁻¹)":       "sav_ratio",
        "Porosity":                 "porosity",
        "Hydraulic Diameter (mm)":  "hydraulic_diameter",
        "Specific SA (m²/m³)":      "specific_surface_area",
    }.get(sel_param, "sav_ratio"), None)

    if baseline_x:
        baseline_label = "Baseline (manual)" if is_manual else "Baseline (STL)"
        fig_curve.add_vline(
            x=baseline_x,
            line_dash="dash",
            line_color="red",
            annotation_text=baseline_label,
        )

    fig_curve.update_layout(
        title=f"{sel_obj} vs {sel_param}",
        xaxis_title=sel_param,
        yaxis_title=sel_obj,
        height=380,
        plot_bgcolor="white",
    )
    fig_curve.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig_curve.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    st.plotly_chart(fig_curve, use_container_width=True)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Sensitivity Index", f"{r.sensitivity_index:.4f}")
    col_b.metric("Direction",          r.direction.title())
    col_c.metric("Linearity (R²)",     f"{r.r_squared:.4f}")

st.markdown("---")

# ─── Full Sensitivity Grid ────────────────────────────────────────────────────
st.markdown("### Full Sensitivity Grid")
st.caption("All parameter-objective curves. Useful for thesis figures.")

show_all = st.checkbox("Show all curves", value=False)
if show_all:
    for param in all_params:
        st.markdown(f"**{param}**")
        cols = st.columns(min(3, len(all_objs)))
        for j, obj in enumerate(all_objs):
            matching_r = [r for r in report.results
                          if r.parameter_name == param and r.objective_name == obj]
            if matching_r:
                r = matching_r[0]
                with cols[j % 3]:
                    fig_mini = go.Figure(go.Scatter(
                        x=r.parameter_values, y=r.objective_values,
                        mode="lines", line=dict(color="#2e86ab", width=1.5),
                    ))
                    fig_mini.update_layout(
                        title=dict(text=obj, font=dict(size=11)),
                        height=180,
                        margin=dict(l=30, r=10, t=30, b=30),
                        plot_bgcolor="white",
                        xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                    )
                    st.plotly_chart(fig_mini, use_container_width=True)
