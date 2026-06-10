"""
Sensitivity Analysis Page - CDMO Phase 2
Quantifies how each geometric parameter influences performance objectives.
Supports multiple designs simultaneously; results accumulate across runs.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os
import tempfile

from utils.ui import HeaderSpec, page_header, sidebar_brand
from core.sensitivity import run_sensitivity_analysis, get_sensitivity_matrix
from core.geometry import GeometryMetrics, analyze_stl
from core.materials import MATERIALS, FLUID_PROPERTIES

st.set_page_config(page_title="Sensitivity Analysis", page_icon="📈", layout="wide")

page_header(
    HeaderSpec(
        icon="📈",
        title="Sensitivity Analysis",
        subtitle="Quantify how geometric parameters influence each performance objective — across multiple designs.",
        accent="#117A65",
        accent_2="#1A5276",
    )
)
sidebar_brand()

st.markdown("""
Sensitivity analysis answers: **which geometric parameters matter most?**
Upload multiple STL files (or add manual entries one at a time) — each design is analysed
independently and kept in the session so you can compare and download all results together.
""")


# ─── Session state ────────────────────────────────────────────────────────────
# Each entry: {"filename": str, "geo": GeometryMetrics,
#              "report": SensitivityReport, "material": str, "mode": str}
if "sa_analyses" not in st.session_state:
    st.session_state.sa_analyses = []


# ─── Helper: build GeometryMetrics from manual inputs ────────────────────────
def _build_manual_geo(sav_ratio, porosity, hydraulic_diameter, specific_surface_area):
    bb_vol    = 1000.0
    volume    = bb_vol * (1.0 - porosity)
    surf_area = sav_ratio * volume
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


def _analyze_stl_file(uploaded_file):
    """Write temp file, run analyze_stl, clean up."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    try:
        geo = analyze_stl(tmp_path)
        geo.filename = uploaded_file.name
        return geo
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ─── Sidebar controls ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Sensitivity Settings")

    n_loaded = len(st.session_state.sa_analyses)
    if n_loaded:
        st.success(f"✓ {n_loaded} design{'s' if n_loaded > 1 else ''} loaded")

    input_mode = st.radio(
        "Input Mode",
        ["📁 Upload STL Files", "✏️ Enter Values Manually"],
        horizontal=True,
    )
    stl_mode   = input_mode.startswith("📁")
    manual_mode = not stl_mode

    st.markdown("---")

    uploaded_files = []
    manual_sav = manual_porosity = manual_hd = manual_ssa = None

    if stl_mode:
        uploaded_files = st.file_uploader(
            "STL files (select multiple)",
            type=["stl"],
            accept_multiple_files=True,
            help="Upload one or more carrier STL files. "
                 "New files are added to the session without replacing existing results.",
        )
    else:
        st.markdown("#### Baseline Geometry")
        manual_sav = st.number_input(
            "SA/V Ratio (mm⁻¹)", min_value=0.05, max_value=20.0,
            value=1.5, step=0.05, format="%.2f",
        )
        manual_porosity = st.number_input(
            "Porosity (0 – 1)", min_value=0.10, max_value=0.95,
            value=0.60, step=0.01, format="%.2f",
        )
        manual_hd = st.number_input(
            "Hydraulic Diameter (mm)", min_value=0.1, max_value=100.0,
            value=5.0, step=0.1, format="%.1f",
        )
        manual_ssa = st.number_input(
            "Specific Surface Area (m²/m³)", min_value=10.0, max_value=10000.0,
            value=500.0, step=10.0, format="%.0f",
        )

    st.markdown("---")
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

    run_btn   = st.button("▶ Run / Add Designs", type="primary",
                           use_container_width=True)
    clear_btn = st.button("🗑 Clear All Designs",
                           use_container_width=True)

    if clear_btn:
        st.session_state.sa_analyses = []
        st.rerun()


# ─── Run analysis ─────────────────────────────────────────────────────────────
if run_btn:
    existing_names = {a["filename"] for a in st.session_state.sa_analyses}

    if stl_mode:
        new_files = [f for f in uploaded_files if f.name not in existing_names]
        if not new_files:
            if uploaded_files:
                st.sidebar.info("All uploaded files are already in the session.")
            else:
                st.sidebar.warning("No files selected.")
        else:
            progress = st.progress(0, text="Analysing…")
            for i, f in enumerate(new_files):
                progress.progress((i) / len(new_files), text=f"Analysing {f.name}…")
                try:
                    geo    = _analyze_stl_file(f)
                    report = run_sensitivity_analysis(
                        geo, material, fluid_density, fluid_viscosity,
                        flow_velocity, n_points,
                    )
                    st.session_state.sa_analyses.append({
                        "filename": f.name,
                        "geo":      geo,
                        "report":   report,
                        "material": material,
                        "mode":     "stl",
                    })
                except Exception as e:
                    st.error(f"Failed to analyse {f.name}: {e}")
            progress.progress(1.0, text="Done.")

    else:  # manual mode
        # Derive a unique display name for manual entries
        manual_count = sum(
            1 for a in st.session_state.sa_analyses if a["mode"] == "manual"
        )
        display_name = f"Manual Entry {manual_count + 1}"
        try:
            geo    = _build_manual_geo(manual_sav, manual_porosity,
                                       manual_hd, manual_ssa)
            geo.filename = display_name
            report = run_sensitivity_analysis(
                geo, material, fluid_density, fluid_viscosity,
                flow_velocity, n_points,
            )
            st.session_state.sa_analyses.append({
                "filename": display_name,
                "geo":      geo,
                "report":   report,
                "material": material,
                "mode":     "manual",
            })
        except Exception as e:
            st.error(f"Analysis failed: {e}")


# ─── Empty state ──────────────────────────────────────────────────────────────
analyses = st.session_state.sa_analyses
if not analyses:
    st.info("📤 Upload STL files (or enter values manually) in the sidebar, "
            "then click **▶ Run / Add Designs** to begin.")
    st.stop()


# ─── Cross-design helpers ─────────────────────────────────────────────────────
def _summary_df_for(analysis):
    """Return a summary DataFrame for one analysis entry."""
    return pd.DataFrame([
        {
            "Design":            analysis["filename"],
            "Parameter":         r.parameter_name,
            "Objective":         r.objective_name,
            "Sensitivity Index": round(r.sensitivity_index, 6),
            "Direction":         r.direction,
            "R² (Linearity)":    round(r.r_squared, 6),
        }
        for r in analysis["report"].results
    ])


def _raw_df_for(analysis):
    """Return a raw-curves DataFrame for one analysis entry."""
    return pd.DataFrame([
        {
            "Design":          analysis["filename"],
            "Parameter":       r.parameter_name,
            "Objective":       r.objective_name,
            "Parameter Value": pv,
            "Objective Value": ov,
        }
        for r in analysis["report"].results
        for pv, ov in zip(r.parameter_values, r.objective_values)
    ])


# ─── Top-level KPI bar ────────────────────────────────────────────────────────
n = len(analyses)
kc1, kc2, kc3 = st.columns(3)
kc1.metric("Designs Loaded", n)
kc2.metric("Parameters Analysed", len(analyses[0]["report"].parameter_importance))
# Most commonly top-ranked parameter across all designs
top_params = [max(a["report"].parameter_importance,
                  key=a["report"].parameter_importance.get)
              for a in analyses]
from collections import Counter
most_common_top = Counter(top_params).most_common(1)[0][0]
kc3.metric("Most Influential (overall)", most_common_top)

st.markdown("---")


# ─── Per-design results in tabs ───────────────────────────────────────────────
tab_labels = [a["filename"].replace(".stl", "") for a in analyses]
if n > 1:
    tab_labels.append("All Designs")

tabs = st.tabs(tab_labels)

# ── Individual design tabs ────────────────────────────────────────────────────
for tab, analysis in zip(tabs[:n], analyses):
    report = analysis["report"]
    geo    = analysis["geo"]
    is_manual = analysis["mode"] == "manual"

    with tab:
        # Baseline banner
        if is_manual:
            st.info(
                f"**Manual baseline** — "
                f"SA/V: {geo.sav_ratio:.2f} mm⁻¹ · "
                f"Porosity: {geo.porosity:.2f} · "
                f"Dₕ: {geo.hydraulic_diameter:.1f} mm · "
                f"SSA: {geo.specific_surface_area:.0f} m²/m³  |  "
                f"Material: **{analysis['material']}**"
            )
        else:
            st.caption(
                f"Material: **{analysis['material']}** · "
                f"SA/V: {geo.sav_ratio:.3f} mm⁻¹ · "
                f"Porosity: {geo.porosity:.3f} · "
                f"Dₕ: {geo.hydraulic_diameter:.2f} mm"
            )

        # KPIs
        m1, m2, m3 = st.columns(3)
        m1.metric("Most Influential Parameter", report.most_influential_parameter)
        m2.metric("Most Sensitive Objective",   report.most_sensitive_objective)
        m3.metric("Parameters Analysed",        len(report.parameter_importance))

        st.markdown("---")

        # Parameter importance bar chart
        st.markdown("#### Parameter Importance Rankings")
        imp_df = pd.DataFrame([
            {"Parameter": k, "Global Sensitivity Index": v}
            for k, v in report.parameter_importance.items()
        ])
        fig_imp = px.bar(
            imp_df.sort_values("Global Sensitivity Index"),
            x="Global Sensitivity Index", y="Parameter",
            orientation="h",
            color="Global Sensitivity Index",
            color_continuous_scale="Blues",
            title="Global Sensitivity (averaged across all objectives)",
        )
        fig_imp.update_layout(height=280, plot_bgcolor="white",
                               coloraxis_showscale=False)
        fig_imp.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
        st.plotly_chart(fig_imp, use_container_width=True)

        st.markdown("---")

        # Heatmap
        st.markdown("#### Sensitivity Heatmap")
        mdata  = get_sensitivity_matrix(report)
        params = mdata["parameters"]
        objs   = mdata["objectives"]
        mat    = np.array(mdata["matrix"])

        fig_heat = go.Figure(data=go.Heatmap(
            z=mat, x=objs, y=params,
            colorscale="YlOrRd",
            text=np.round(mat, 3),
            texttemplate="%{text}",
            textfont={"size": 11},
            colorbar=dict(title="SI"),
        ))
        fig_heat.update_layout(
            title="Sensitivity Index Matrix",
            xaxis_title="Performance Objective",
            yaxis_title="Geometric Parameter",
            height=300, xaxis=dict(side="bottom"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("---")

        # Interactive sensitivity curve
        st.markdown("#### Sensitivity Curves")
        all_params = list(dict.fromkeys(r.parameter_name for r in report.results))
        all_objs   = list(dict.fromkeys(r.objective_name  for r in report.results))

        # unique widget keys to avoid conflicts across tabs
        safe_name = analysis["filename"].replace(".", "_").replace(" ", "_")
        col_p, col_o = st.columns(2)
        with col_p:
            sel_param = st.selectbox("Parameter", all_params,
                                      key=f"param_{safe_name}")
        with col_o:
            sel_obj = st.selectbox("Objective", all_objs,
                                    key=f"obj_{safe_name}")

        matching = [r for r in report.results
                    if r.parameter_name == sel_param
                    and r.objective_name == sel_obj]

        if matching:
            r = matching[0]
            fig_c = go.Figure()
            fig_c.add_trace(go.Scatter(
                x=r.parameter_values, y=r.objective_values,
                mode="lines+markers",
                line=dict(color="#117A65", width=2.5),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor="rgba(17,122,101,0.08)",
            ))
            baseline_attr = {
                "SA/V Ratio (mm⁻\xb9)": "sav_ratio",
                "Porosity":                  "porosity",
                "Hydraulic Diameter (mm)":   "hydraulic_diameter",
                "Specific SA (m\xb2/m\xb3)": "specific_surface_area",
            }.get(sel_param)
            if baseline_attr:
                bx = getattr(geo, baseline_attr, None)
                if bx:
                    fig_c.add_vline(x=bx, line_dash="dash", line_color="red",
                                    annotation_text="Baseline")
            fig_c.update_layout(
                title=f"{sel_obj} vs {sel_param}",
                xaxis_title=sel_param, yaxis_title=sel_obj,
                height=360, plot_bgcolor="white",
            )
            fig_c.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
            fig_c.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
            st.plotly_chart(fig_c, use_container_width=True)

            ca, cb, cc = st.columns(3)
            ca.metric("Sensitivity Index", f"{r.sensitivity_index:.4f}")
            cb.metric("Direction",          r.direction.title())
            cc.metric("Linearity (R²)",     f"{r.r_squared:.4f}")

        st.markdown("---")

        # Full grid (collapsible)
        with st.expander("Show full curve grid"):
            for param in all_params:
                st.markdown(f"**{param}**")
                cols = st.columns(min(3, len(all_objs)))
                for j, obj in enumerate(all_objs):
                    mr = [r for r in report.results
                          if r.parameter_name == param and r.objective_name == obj]
                    if mr:
                        with cols[j % 3]:
                            fig_mini = go.Figure(go.Scatter(
                                x=mr[0].parameter_values,
                                y=mr[0].objective_values,
                                mode="lines",
                                line=dict(color="#117A65", width=1.5),
                            ))
                            fig_mini.update_layout(
                                title=dict(text=obj, font=dict(size=10)),
                                height=160,
                                margin=dict(l=25, r=8, t=28, b=28),
                                plot_bgcolor="white",
                                xaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                                yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                            )
                            st.plotly_chart(fig_mini, use_container_width=True,
                                            key=f"mini_{safe_name}_{param}_{obj}")

        st.markdown("---")

        # Per-design downloads
        st.markdown("#### Download — This Design")
        sdf = _summary_df_for(analysis)
        rdf = _raw_df_for(analysis)
        mp  = pd.DataFrame(mat, index=params, columns=objs).round(6)
        mp.index.name = "Parameter"

        dl1, dl2, dl3 = st.columns(3)
        fname_stem = analysis["filename"].replace(".stl", "").replace(" ", "_")
        with dl1:
            st.download_button(
                "⬇ Summary (CSV)",
                data=sdf.to_csv(index=False).encode("utf-8"),
                file_name=f"{fname_stem}_sensitivity_summary.csv",
                mime="text/csv", use_container_width=True,
            )
        with dl2:
            st.download_button(
                "⬇ Matrix (CSV)",
                data=mp.to_csv().encode("utf-8"),
                file_name=f"{fname_stem}_sensitivity_matrix.csv",
                mime="text/csv", use_container_width=True,
            )
        with dl3:
            st.download_button(
                "⬇ Raw Curves (CSV)",
                data=rdf.to_csv(index=False).encode("utf-8"),
                file_name=f"{fname_stem}_sensitivity_curves.csv",
                mime="text/csv", use_container_width=True,
            )


# ── "All Designs" comparison tab (only shown when n > 1) ─────────────────────
if n > 1:
    with tabs[-1]:
        st.markdown("### Cross-Design Comparison")
        st.caption("All designs side-by-side — compare parameter importance rankings and sensitivity indices.")

        # ── Grouped bar: importance per design ───────────────────────────────
        st.markdown("#### Parameter Importance Rankings — All Designs")

        imp_rows = []
        for a in analyses:
            for param, val in a["report"].parameter_importance.items():
                imp_rows.append({
                    "Design":    a["filename"].replace(".stl", ""),
                    "Parameter": param,
                    "Global Sensitivity Index": val,
                })
        imp_all = pd.DataFrame(imp_rows)

        fig_cmp = px.bar(
            imp_all,
            x="Parameter", y="Global Sensitivity Index",
            color="Design", barmode="group",
            title="Parameter Global Sensitivity — All Designs",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_cmp.update_layout(
            height=380, plot_bgcolor="white",
            xaxis_tickangle=-25,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        fig_cmp.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
        st.plotly_chart(fig_cmp, use_container_width=True)

        st.markdown("---")

        # ── Heatmap: sensitivity per (design, parameter) for a chosen objective
        st.markdown("#### Sensitivity Index by Design × Parameter")
        all_obj_names = list(dict.fromkeys(
            r.objective_name
            for a in analyses
            for r in a["report"].results
        ))
        chosen_obj = st.selectbox(
            "Select objective to compare across designs",
            all_obj_names, key="cmp_obj",
        )

        all_param_names = list(dict.fromkeys(
            r.parameter_name
            for a in analyses
            for r in a["report"].results
        ))
        design_labels = [a["filename"].replace(".stl", "") for a in analyses]
        heat_z = np.zeros((len(analyses), len(all_param_names)))

        for i, a in enumerate(analyses):
            for r in a["report"].results:
                if r.objective_name == chosen_obj:
                    j = all_param_names.index(r.parameter_name)
                    heat_z[i][j] = r.sensitivity_index

        fig_ch = go.Figure(data=go.Heatmap(
            z=heat_z,
            x=all_param_names,
            y=design_labels,
            colorscale="YlOrRd",
            text=np.round(heat_z, 3),
            texttemplate="%{text}",
            textfont={"size": 11},
            colorbar=dict(title="SI"),
        ))
        fig_ch.update_layout(
            title=f"Sensitivity Index for: {chosen_obj}",
            xaxis_title="Geometric Parameter",
            yaxis_title="Design",
            height=max(240, n * 55 + 100),
        )
        st.plotly_chart(fig_ch, use_container_width=True)

        st.markdown("---")

        # ── Combined downloads ────────────────────────────────────────────────
        st.markdown("#### Download — All Designs Combined")

        combined_summary = pd.concat(
            [_summary_df_for(a) for a in analyses], ignore_index=True
        )
        combined_raw = pd.concat(
            [_raw_df_for(a) for a in analyses], ignore_index=True
        )

        # Wide matrix: one sheet per design stacked with a Design header column
        matrix_frames = []
        for a in analyses:
            mdata = get_sensitivity_matrix(a["report"])
            df_m  = pd.DataFrame(
                mdata["matrix"],
                index=mdata["parameters"],
                columns=mdata["objectives"],
            ).round(6)
            df_m.index.name = "Parameter"
            df_m.insert(0, "Design", a["filename"])
            matrix_frames.append(df_m)
        combined_matrix = pd.concat(matrix_frames)

        dl_a, dl_b, dl_c = st.columns(3)
        with dl_a:
            st.download_button(
                "⬇ All Summaries (CSV)",
                data=combined_summary.to_csv(index=False).encode("utf-8"),
                file_name="all_designs_sensitivity_summary.csv",
                mime="text/csv", use_container_width=True,
                help="Sensitivity index, direction, R² for every design × parameter × objective.",
            )
        with dl_b:
            st.download_button(
                "⬇ All Matrices (CSV)",
                data=combined_matrix.to_csv().encode("utf-8"),
                file_name="all_designs_sensitivity_matrix.csv",
                mime="text/csv", use_container_width=True,
                help="Sensitivity index matrix for every design, stacked.",
            )
        with dl_c:
            st.download_button(
                "⬇ All Raw Curves (CSV)",
                data=combined_raw.to_csv(index=False).encode("utf-8"),
                file_name="all_designs_sensitivity_curves.csv",
                mime="text/csv", use_container_width=True,
                help="All sampled (parameter value, objective value) points for every design.",
            )
