"""
Genetic Algorithm Optimiser Page - CDMO Phase 3
NSGA-II multi-objective optimisation to find Pareto-optimal carrier geometries.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import io
import os
import tempfile
import trimesh

from utils.ui import HeaderSpec, page_header, sidebar_brand
from utils.persistence import save_ga_result, load_ga_result, list_ga_results

from core.genetic_algorithm import (
    run_genetic_algorithm, ga_result_to_dataframe,
    CarrierParams, generate_carrier_stl
)
from core.geometry import analyze_stl
from core.materials import MATERIALS, FLUID_PROPERTIES
from core.commercial_carriers import (
    COMMERCIAL_CARRIERS,
    compare_to_commercial,
    build_published_mbbr_table_md,
    PUBLISHED_MBBR_REFERENCES,
)

st.set_page_config(page_title="GA Optimiser", page_icon="🧬", layout="wide")

page_header(
    HeaderSpec(
        icon="🧬",
        title="Genetic Algorithm Optimiser",
        subtitle="NSGA‑II multi‑objective search for Pareto‑optimal carrier geometries.",
        accent="#922B21",
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
The GA evolves a population of parametric carrier designs over multiple generations,
using tournament selection, simulated binary crossover, and polynomial mutation.
Pareto-optimal designs on the final front represent the best achievable trade-offs
between competing objectives.
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
                colorscale="Turbo",
                flatshading=True,
                opacity=1.0,
                showscale=False,
                lighting=dict(ambient=0.45, diffuse=0.75, roughness=0.55, specular=0.25),
                lightposition=dict(x=220, y=120, z=160),
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

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## GA Configuration")

    design_type = st.selectbox("Carrier Topology", [
        "cross_flow", "honeycomb", "lattice", "hybrid"],
        format_func=lambda x: x.replace("_", " ").title())

    material = st.selectbox("Optimise for Material", list(MATERIALS.keys()))

    fluid_type = st.selectbox("Fluid", list(FLUID_PROPERTIES.keys()),
        index=2, format_func=lambda x: FLUID_PROPERTIES[x]["name"])
    fluid = FLUID_PROPERTIES[fluid_type]
    fluid_density = st.number_input("Density (kg/m³)", 990.0, 1100.0,
                                     float(fluid["density"]), 1.0)
    fluid_viscosity = st.number_input("Viscosity (Pa·s)", 0.0005, 0.02,
                                       float(fluid["viscosity"]), 0.0005, format="%.4f")
    flow_velocity = st.slider("Flow Velocity (m/s)", 0.001, 0.1, 0.01, 0.001)

    st.markdown("### Objective Weights")
    w_sav  = st.slider("SA/V Ratio",       0.0, 1.0, 0.30, 0.05)
    w_por  = st.slider("Porosity",          0.0, 1.0, 0.20, 0.05)
    w_flow = st.slider("Flow Efficiency",   0.0, 1.0, 0.20, 0.05)
    w_buoy = st.slider("Buoyancy",          0.0, 1.0, 0.15, 0.05)

    st.markdown("### Algorithm Parameters")
    n_gen  = st.slider("Generations", 5, 50, 15,
                        help="More generations = better results, slower run")
    pop_sz = st.select_slider("Population Size", [8, 12, 16, 20, 24, 30], value=16,
                               help="Must be even")
    use_seed = st.checkbox("Fix random seed (reproducible)", value=False,
                            help="Enable to get identical results across runs (useful for thesis reproducibility)")
    random_seed = st.number_input("Seed value", min_value=0, max_value=99999,
                                   value=42, step=1) if use_seed else None

    st.info(f"~{n_gen * pop_sz * 2} STL evaluations total")
    run_btn = st.button("🧬 Run Optimisation", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("### 💾 Session")
    save_name = st.text_input("Save name", value="ga_run", key="ga_save_name")
    save_btn = st.button("💾 Save GA Result", use_container_width=True,
                          disabled="ga_result" not in st.session_state)

    st.markdown("**Load previous run:**")
    saved_ga = list_ga_results()
    if saved_ga:
        load_sel = st.selectbox(
            "Saved GA results",
            ["— select —"] + [f"{s['session_name']} ({s['design_type']}, {s['material']}, "
                               f"gen={s['n_generations']}, pareto={s['pareto_size']})"
                               for s in saved_ga],
            key="ga_load_sel",
        )
        load_btn = st.button("📂 Load", use_container_width=True,
                              disabled=(load_sel == "— select —"))
    else:
        load_btn = False
        load_sel = None

# ─── Save / Load handlers ─────────────────────────────────────────────────────
if save_btn and "ga_result" in st.session_state:
    try:
        path = save_ga_result(st.session_state.ga_result, save_name)
        st.sidebar.success(f"Saved: {os.path.basename(path)}")
    except Exception as e:
        st.sidebar.error(f"Save failed: {e}")

if load_btn and saved_ga and load_sel != "— select —":
    idx = [f"{s['session_name']} ({s['design_type']}, {s['material']}, "
           f"gen={s['n_generations']}, pareto={s['pareto_size']})"
           for s in saved_ga].index(load_sel)
    try:
        st.session_state.ga_result = load_ga_result(saved_ga[idx]["filepath"])
        st.sidebar.success("GA result loaded.")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Load failed: {e}")

# ─── Main ─────────────────────────────────────────────────────────────────────
if run_btn:
    weights = {"sav_ratio": w_sav, "porosity": w_por,
               "flow_efficiency": w_flow, "buoyancy": w_buoy}

    progress_bar = st.progress(0)
    status = st.empty()

    def update_progress(gen, total, frac):
        progress_bar.progress(min(frac, 1.0))
        status.text(f"Generation {gen}/{total} — evolving population...")

    try:
        with st.spinner("Running NSGA-II..."):
            result = run_genetic_algorithm(
                n_generations=n_gen,
                population_size=pop_sz,
                design_type=design_type,
                material=material,
                fluid_density=fluid_density,
                fluid_viscosity=fluid_viscosity,
                flow_velocity=flow_velocity,
                weights=weights,
                progress_callback=update_progress,
                random_seed=random_seed,
            )
        progress_bar.progress(1.0)
        status.text("✅ Optimisation complete!")
        st.session_state.ga_result = result
    except Exception as e:
        st.error(f"Optimisation failed: {e}")

if "ga_result" not in st.session_state:
    st.info("Configure the GA in the sidebar and click **Run Optimisation**.")
    st.stop()

result = st.session_state.ga_result

# ─── KPI Summary ─────────────────────────────────────────────────────────────
st.markdown("### Optimisation Results")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Pareto Front Size", len(result.pareto_front))
col2.metric("Final Population", len(result.population))
col3.metric("Generations Run", result.n_generations)
if result.best_composite:
    b = result.best_composite
    col4.metric("Best Composite Score", f"{b.composite_score:.4f}")

st.markdown("---")

# ─── Convergence Chart ────────────────────────────────────────────────────────
if result.generation_history:
    st.markdown("#### Genetic Algorithm Convergence")
    hist_df = pd.DataFrame(result.generation_history)
    fig_conv = go.Figure()
    fig_conv.add_trace(go.Scatter(
        x=hist_df["generation"],
        y=hist_df["best_composite"],
        mode="lines+markers",
        name="Best fitness",
        line=dict(color="#922b21", width=2.5),
        marker=dict(size=6),
    ))
    if "mean_composite" in hist_df.columns:
        fig_conv.add_trace(go.Scatter(
            x=hist_df["generation"],
            y=hist_df["mean_composite"],
            mode="lines+markers",
            name="Mean fitness",
            line=dict(color="#1f77b4", width=2.5, dash="dash"),
            marker=dict(size=6),
        ))
    fig_conv.update_layout(
        xaxis_title="Generation",
        yaxis_title="Fitness",
        height=340,
        plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.25),
    )
    fig_conv.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig_conv.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    st.plotly_chart(fig_conv, use_container_width=True)

    st.markdown("#### Generation History")
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=hist_df["generation"], y=hist_df["best_sav"],
        mode="lines", name="Best SA/V", line=dict(color="#2196F3")))
    fig_hist.add_trace(go.Scatter(
        x=hist_df["generation"], y=hist_df["best_porosity"],
        mode="lines", name="Best Porosity", line=dict(color="#4CAF50")))
    fig_hist.add_trace(go.Scatter(
        x=hist_df["generation"], y=hist_df["best_flow"],
        mode="lines", name="Best Flow", line=dict(color="#FF9800")))
    fig_hist.update_layout(
        xaxis_title="Generation", yaxis_title="Objective Value",
        height=300, plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.35))
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")

# ─── Pareto Front Scatter ─────────────────────────────────────────────────────
st.markdown("### Pareto Frontier")

if result.pareto_front:
    col_px, col_py = st.columns(2)
    objs = ["SA/V Ratio (mm⁻¹)", "Porosity", "Flow Efficiency", "Buoyancy Score"]
    with col_px:
        x_obj = st.selectbox("X Axis", objs, index=0, key="ga_x")
    with col_py:
        y_obj = st.selectbox("Y Axis", objs, index=2, key="ga_y")

    obj_map = {
        "SA/V Ratio (mm⁻¹)": "obj_sav",
        "Porosity": "obj_porosity",
        "Flow Efficiency": "obj_flow",
        "Buoyancy Score": "obj_buoyancy",
    }

    fig_pf = go.Figure()
    all_pop = result.population
    pareto_ids = {id(ind) for ind in result.pareto_front}
    dominated = [ind for ind in all_pop if id(ind) not in pareto_ids and ind.feasible]

    if dominated:
        fig_pf.add_trace(go.Scatter(
            x=[getattr(ind, obj_map[x_obj]) for ind in dominated],
            y=[getattr(ind, obj_map[y_obj]) for ind in dominated],
            mode='markers',
            marker=dict(size=7, color="#aaa", opacity=0.4),
            name="Dominated"))

    fig_pf.add_trace(go.Scatter(
        x=[getattr(ind, obj_map[x_obj]) for ind in result.pareto_front],
        y=[getattr(ind, obj_map[y_obj]) for ind in result.pareto_front],
        mode='markers',
        marker=dict(size=14, color="#922b21", symbol='star',
                    line=dict(width=1.5, color='white')),
        text=[f"D={ind.params.outer_diameter:.0f}mm H={ind.params.height:.0f}mm "
              f"Fins={ind.params.num_fins} Score={ind.composite_score:.3f}"
              for ind in result.pareto_front],
        hovertemplate="<b>%{text}</b><br>" +
                      f"{x_obj}: %{{x:.4f}}<br>{y_obj}: %{{y:.4f}}<extra></extra>",
        name="Pareto Optimal ★"))

    fig_pf.update_layout(
        title=f"Pareto Front: {x_obj} vs {y_obj}",
        xaxis_title=x_obj, yaxis_title=y_obj,
        height=420, plot_bgcolor="white")
    fig_pf.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig_pf.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    st.plotly_chart(fig_pf, use_container_width=True)

st.markdown("---")

# ─── Pareto Front Table ───────────────────────────────────────────────────────
st.markdown("### Pareto-Optimal Design Parameters")
if result.pareto_front:
    df_pareto = ga_result_to_dataframe(result)
    st.dataframe(df_pareto, use_container_width=True, hide_index=True,
                 column_config={
                     "Composite Score": st.column_config.ProgressColumn(min_value=0, max_value=1),
                     "SA/V Ratio (mm⁻¹)": st.column_config.NumberColumn(format="%.4f"),
                 })

    st.markdown("---")
    st.markdown("### Download Best Design as STL")
    
    # Sort by composite score and let user pick
    sorted_pf = sorted(result.pareto_front, key=lambda x: x.composite_score, reverse=True)
    selected_idx = st.selectbox(
        "Select design to download",
        range(len(sorted_pf)),
        format_func=lambda i: (
            f"Rank {i+1} | Score: {sorted_pf[i].composite_score:.4f} | "
            f"D={sorted_pf[i].params.outer_diameter:.0f}mm "
            f"H={sorted_pf[i].params.height:.0f}mm "
            f"Fins={sorted_pf[i].params.num_fins}"))

    selected_ind = sorted_pf[selected_idx]

    col_dl, col_info = st.columns([1, 2])
    stl_bytes = b""
    with col_dl:
        try:
            stl_path, _ = generate_carrier_stl(selected_ind.params)
            try:
                with open(stl_path, "rb") as f:
                    stl_bytes = f.read()
            finally:
                if os.path.exists(stl_path):
                    os.unlink(stl_path)

            fname = (f"ga_optimised_{design_type}_"
                     f"D{int(selected_ind.params.outer_diameter)}"
                     f"H{int(selected_ind.params.height)}"
                     f"F{selected_ind.params.num_fins}.stl")
            st.download_button(
                "⬇️ Download Optimised STL",
                data=stl_bytes, file_name=fname,
                mime="application/octet-stream",
                use_container_width=True, type="primary")
        except Exception as e:
            st.error(f"STL generation failed: {e}")

    with col_info:
        g = selected_ind.geo_metrics
        st.markdown("**Predicted Performance:**")
        m1, m2, m3 = st.columns(3)
        m1.metric("SA/V (mm⁻¹)", f"{g.get('sav_ratio', 0):.4f}")
        m2.metric("Porosity", f"{g.get('porosity', 0):.4f}")
        m3.metric("Flow Efficiency", f"{g.get('flow_efficiency', 0):.4f}")

    if stl_bytes:
        st.markdown("### 3D View of Selected Optimised STL")
        st.plotly_chart(
            stl_mesh_figure(
                stl_bytes,
                title=(
                    f"Optimised Rank {selected_idx + 1} "
                    f"({selected_ind.params.design_type.replace('_', ' ').title()})"
                ),
            ),
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("### Commercial Carrier Comparison")
    st.caption("How your optimised design compares to published MBBR media specifications.")

    # Compare selected design to commercial carriers
    comp_data = compare_to_commercial(
        user_sav=selected_ind.geo_metrics.get('sav_ratio', 0),
        user_porosity=selected_ind.geo_metrics.get('porosity', 0),
        user_specific_sa=selected_ind.geo_metrics.get('specific_surface_area', 0)
    )

    col_comp1, col_comp2, col_comp3 = st.columns(3)
    with col_comp1:
        st.markdown("**SA/V Ratio**")
        st.metric(
            "Your Design",
            f"{comp_data['user_sav']:.4f} mm⁻¹",
            f"Percentile: {comp_data['sav_percentile']:.0f}%"
        )
        st.caption(f"vs. {comp_data['mean_commercial_sav']:.4f} (commercial avg)")
    with col_comp2:
        st.markdown("**Porosity**")
        st.metric(
            "Your Design",
            f"{comp_data['user_porosity']:.4f}",
            f"Percentile: {comp_data['porosity_percentile']:.0f}%"
        )
        st.caption(f"vs. {comp_data['mean_commercial_porosity']:.4f} (commercial avg)")
    with col_comp3:
        st.markdown("**Specific SA (m²/m³)**")
        st.metric(
            "Your Design",
            f"{comp_data['user_specific_sa']:.1f}",
            f"Percentile: {comp_data['ssa_percentile']:.0f}%"
        )
        st.caption(f"vs. {comp_data['mean_commercial_ssa']:.1f} (commercial avg)")

    st.markdown("#### Commercial Media Specifications")

    # Build comparison table
    comp_rows = []
    comp_rows.append({
        "Product": "🔵 YOUR DESIGN (Optimised)",
        "Manufacturer": result.design_type.replace('_', ' ').title(),
        "Material": "CDMO",
        "SA/V (mm⁻¹)": f"{comp_data['user_sav']:.4f}",
        "Porosity": f"{comp_data['user_porosity']:.4f}",
        "Specific SA (m²/m³)": f"{comp_data['user_specific_sa']:.1f}",
        "Dimensions": (
            f"{selected_ind.params.outer_diameter:.0f} x "
            f"{selected_ind.params.height:.0f} mm"
        ),
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

    comp_df = pd.DataFrame(comp_rows)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    st.markdown("#### Detailed Specifications")
    col_detail = st.columns(1)[0]
    with col_detail:
        selected_product = st.selectbox(
            "View detailed specs for:",
            ["YOUR DESIGN"] + [c.name for c in COMMERCIAL_CARRIERS]
        )

        if selected_product == "YOUR DESIGN":
            st.markdown(f"**🔵 Your CDMO {result.design_type.title()} Design**")
            det_cols = st.columns(4)
            det_cols[0].metric("SA/V", f"{comp_data['user_sav']:.4f} mm⁻¹")
            det_cols[1].metric("Porosity", f"{comp_data['user_porosity']:.4f}")
            det_cols[2].metric("Specific SA", f"{comp_data['user_specific_sa']:.1f} m²/m³")
            det_cols[3].metric("Material", "CDMO (design)")
            st.info(f"**Notes:** Rank {selected_idx + 1} on Pareto front. "
                   f"Composite score: {selected_ind.composite_score:.4f}")
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
    st.markdown(build_published_mbbr_table_md())
    st.markdown("**References:**")
    for ref in PUBLISHED_MBBR_REFERENCES:
        st.markdown(f"- [{ref}]({ref})")
