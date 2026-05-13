"""
CDMO - Computational Design and Multi-Objective Optimization
Web Application for 3D Printed Biofilm Carrier Evaluation

University of Ibadan, Nigeria
PhD Research - Mechanical Engineering Department
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import tempfile
import os

from utils.ui import HeaderSpec, page_header, sidebar_brand

from core.geometry import analyze_stl, GeometryMetrics, get_metrics_summary
from core.flow_analysis import compute_flow_metrics, FlowMetrics, get_flow_summary
from core.buoyancy import compute_buoyancy, compare_materials_buoyancy, get_buoyancy_summary
from core.scoring import (
    ObjectiveWeights, CarrierScore, score_carrier,
    compute_composite_scores, find_pareto_frontier,
    generate_improvement_suggestions, get_ranking_summary
)
from core.materials import MATERIALS, FLUID_PROPERTIES


# ─── Cached analysis helpers ──────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def cached_analyze_stl(file_bytes: bytes, filename: str) -> GeometryMetrics:
    """Cache geometry analysis keyed on file content so re-renders don't re-parse STL."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        geo = analyze_stl(tmp_path)
        geo.filename = filename
        return geo
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@st.cache_data(show_spinner=False)
def cached_flow_metrics(
    porosity: float, hydraulic_diameter: float,
    specific_surface_area: float, sav_ratio: float,
    surface_area: float, volume: float, bounding_box_volume: float,
    superficial_velocity: float, fluid_density: float,
    fluid_viscosity: float, temperature: float,
) -> FlowMetrics:
    """Cache flow metrics keyed on geometry + operating conditions."""
    geo = GeometryMetrics(
        porosity=porosity,
        hydraulic_diameter=hydraulic_diameter,
        specific_surface_area=specific_surface_area,
        sav_ratio=sav_ratio,
        surface_area=surface_area,
        volume=volume,
        bounding_box_volume=bounding_box_volume,
    )
    return compute_flow_metrics(
        geo, superficial_velocity, fluid_density, fluid_viscosity, temperature
    )


@st.cache_data(show_spinner=False)
def _porosity_flow_curve(
    base_sav: float, base_surface_area: float, base_volume: float,
    base_bb_volume: float, base_porosity: float, base_hd: float,
    base_ssa: float,
    flow_velocity: float, fluid_density: float, fluid_viscosity: float,
) -> tuple:
    """Pre-compute the 50-point porosity-vs-flow-efficiency curve once per design."""
    porosities = np.linspace(0.3, 0.95, 50)
    flow_eff_values = []
    for por in porosities:
        geo_temp = GeometryMetrics(
            porosity=por,
            sav_ratio=base_sav,
            surface_area=base_surface_area,
            volume=base_volume * (1 - por) / max(1 - base_porosity, 1e-6),
            bounding_box_volume=base_bb_volume,
            specific_surface_area=base_ssa,
            hydraulic_diameter=base_hd * por / max(base_porosity, 1e-6),
        )
        f_temp = compute_flow_metrics(geo_temp, flow_velocity, fluid_density, fluid_viscosity)
        flow_eff_values.append(f_temp.flow_efficiency_score)
    return porosities, np.array(flow_eff_values)


# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="CDMO - Biofilm Carrier Optimizer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

page_header(
    HeaderSpec(
        icon="🔬",
        title="Upload & Analyse",
        subtitle="Run the full CDMO pipeline: geometry → flow → buoyancy → scoring → Pareto frontier.",
        accent="#2E86AB",
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
        padding: 0.95rem 1rem;
        margin: 0.45rem 0;
      }
      .pareto-badge{
        background: #16a34a;
        color: white;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 800;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Session State ────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = []
if "all_carriers" not in st.session_state:
    st.session_state.all_carriers = []


# ─── Sidebar: Configuration ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    st.markdown("### 🧪 Material Selection")
    selected_materials = st.multiselect(
        "Select materials to evaluate",
        options=list(MATERIALS.keys()),
        default=["PLA", "ABS", "PETG", "PP"],
        help="Choose which polymer materials to include in the analysis"
    )
    
    st.markdown("### 💧 Reactor Conditions")
    fluid_type = st.selectbox(
        "Fluid Type",
        options=list(FLUID_PROPERTIES.keys()),
        index=2,
        format_func=lambda x: FLUID_PROPERTIES[x]["name"]
    )
    fluid = FLUID_PROPERTIES[fluid_type]
    
    col1, col2 = st.columns(2)
    with col1:
        fluid_density = st.number_input(
            "Density (kg/m³)", 
            min_value=990.0, max_value=1100.0,
            value=float(fluid["density"]), step=1.0)
    with col2:
        fluid_viscosity = st.number_input(
            "Viscosity (Pa·s)", 
            min_value=0.0005, max_value=0.02,
            value=float(fluid["viscosity"]), step=0.0005,
            format="%.4f")
    
    flow_velocity = st.slider(
        "Superficial Velocity (m/s)",
        min_value=0.001, max_value=0.1,
        value=0.01, step=0.001,
        format="%.3f"
    )
    temperature = st.number_input(
        "Temperature (°C)", 
        min_value=5.0, max_value=50.0,
        value=25.0, step=0.5)
    
    st.markdown("### 🎯 Objective Weights")
    st.caption("Adjust importance of each performance metric")
    
    w_sav = st.slider("SA/V Ratio", 0.0, 1.0, 0.30, 0.05,
                       help="Surface area to volume ratio - biofilm attachment potential")
    w_por = st.slider("Porosity", 0.0, 1.0, 0.20, 0.05,
                       help="Void fraction - hydraulic conductivity and accessibility")
    w_flow = st.slider("Flow Efficiency", 0.0, 1.0, 0.20, 0.05,
                        help="Hydraulic performance -  pressure drop and mass transfer")
    w_buoy = st.slider("Buoyancy Suitability", 0.0, 1.0, 0.15, 0.05,
                        help="Reactor mixing behaviour - carrier distribution")
    w_bio = st.slider("Biofilm Affinity", 0.0, 1.0, 0.10, 0.05,
                       help="Material surface chemistry - microbial attachment")
    w_mech = st.slider("Mechanical Strength", 0.0, 1.0, 0.05, 0.05,
                        help="Structural durability under hydraulic loading")
    
    total_weight = w_sav + w_por + w_flow + w_buoy + w_bio + w_mech
    if abs(total_weight - 1.0) > 0.01:
        st.warning(f"⚠️ Weights sum to {total_weight:.2f}. Will be auto-normalized.")
    else:
        st.success(f"✓ Weights sum to {total_weight:.2f}")
    
    if st.button("🗑️ Clear All Results", use_container_width=True):
        st.session_state.results = []
        st.session_state.all_carriers = []
        st.rerun()


# ─── Main Content: Tabs ───────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📤 Upload & Analyze",
    "📊 Results & Comparison",
    "🎯 Pareto Analysis",
    "💧 Flow Visualization",
    "📋 Export Report"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Upload & Analyze
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Upload STL Files for Analysis")
    st.caption("Upload one or more STL files from Blender. "
               "Each file will be analyzed against all selected materials.")
    
    uploaded_files = st.file_uploader(
        "Drop STL files here",
        type=["stl"],
        accept_multiple_files=True,
        help="Binary or ASCII STL files exported from Blender or any CAD software"
    )
    
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) ready for analysis**")
        
        # Show file list
        file_info_cols = st.columns(min(len(uploaded_files), 4))
        for i, f in enumerate(uploaded_files):
            with file_info_cols[i % 4]:
                st.markdown(f"""
                <div class="metric-card">
                    <b>📄 {f.name}</b><br>
                    <small>{f.size/1024:.1f} KB</small>
                </div>
                """, unsafe_allow_html=True)
        
        col_run, col_info = st.columns([1, 2])
        with col_run:
            run_analysis = st.button(
                "🚀 Run Full Analysis",
                use_container_width=True,
                type="primary"
            )
        with col_info:
            st.info(f"Will evaluate {len(uploaded_files)} design(s) × "
                    f"{len(selected_materials)} material(s) = "
                    f"{len(uploaded_files) * len(selected_materials)} combinations")
        
        if run_analysis and selected_materials:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            new_results = []
            new_carriers = []
            total = len(uploaded_files) * len(selected_materials)
            step = 0
            
            for uploaded_file in uploaded_files:
                try:
                    # Geometry analysis (cached by file content)
                    status_text.text(f"⚙️ Analyzing geometry: {uploaded_file.name}")
                    geo = cached_analyze_stl(uploaded_file.getvalue(), uploaded_file.name)

                    # Flow analysis (cached by geometry + conditions)
                    flow = cached_flow_metrics(
                        geo.porosity, geo.hydraulic_diameter,
                        geo.specific_surface_area, geo.sav_ratio,
                        geo.surface_area, geo.volume, geo.bounding_box_volume,
                        flow_velocity, fluid_density, fluid_viscosity, temperature,
                    )
                    
                    # Per-material analysis
                    for material in selected_materials:
                        step += 1
                        status_text.text(
                            f"🧪 Evaluating {uploaded_file.name} × {material} "
                            f"({step}/{total})")
                        progress_bar.progress(step / total)
                        
                        buoy = compute_buoyancy(geo, material, fluid_density)
                        
                        design_id = f"{uploaded_file.name.replace('.stl','')}_{material}"
                        cs = score_carrier(geo, flow, buoy, material, design_id)
                        
                        new_results.append({
                            "design_id": design_id,
                            "filename": uploaded_file.name,
                            "material": material,
                            "geo": geo,
                            "flow": flow,
                            "buoy": buoy,
                            "carrier_score": cs
                        })
                        new_carriers.append(cs)
                
                except Exception as e:
                    st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
            
            # Population-level scoring and Pareto analysis
            if new_carriers:
                weights = ObjectiveWeights(
                    sav_ratio=w_sav, porosity=w_por,
                    flow_efficiency=w_flow, buoyancy=w_buoy,
                    biofilm_affinity=w_bio, mechanical=w_mech
                )
                
                # Combine with existing if any
                all_carriers = st.session_state.all_carriers + new_carriers
                all_carriers = compute_composite_scores(all_carriers, weights)
                all_carriers = find_pareto_frontier(all_carriers)
                
                # Update carrier scores in results
                score_map = {c.design_id: c for c in all_carriers}
                for r in new_results:
                    r["carrier_score"] = score_map.get(r["design_id"], r["carrier_score"])
                
                st.session_state.results.extend(new_results)
                st.session_state.all_carriers = all_carriers
            
            progress_bar.progress(1.0)
            status_text.text("✅ Analysis complete!")
            st.success(
                f"Successfully analyzed {len(uploaded_files)} design(s) across "
                f"{len(selected_materials)} material(s). "
                f"View results in the other tabs.")
        
        elif run_analysis and not selected_materials:
            st.warning("Please select at least one material in the sidebar.")
    
    else:
        # Empty state
        st.markdown("""
        <div style="text-align:center; padding: 3rem; color: #6c757d; 
                    border: 2px dashed #dee2e6; border-radius: 12px;">
            <h3>📂 No files uploaded yet</h3>
            <p>Upload your STL files above to begin the CDMO analysis pipeline.</p>
            <p><small>Supports Blender-exported binary and ASCII STL files</small></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show single-file detail if results exist
    if st.session_state.results:
        st.markdown("---")
        st.markdown("### 🔍 Single Design Inspector")
        
        design_options = list({r["filename"] for r in st.session_state.results})
        selected_design = st.selectbox("Select design to inspect", design_options)
        
        design_results = [r for r in st.session_state.results 
                          if r["filename"] == selected_design]
        
        if design_results:
            geo = design_results[0]["geo"]
            flow = design_results[0]["flow"]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📐 Geometry**")
                st.metric("SA/V Ratio (mm⁻¹)", f"{geo.sav_ratio:.4f}")
                st.metric("Porosity", f"{geo.porosity:.4f}")
                st.metric("Surface Area (mm²)", f"{geo.surface_area:,.1f}")
                st.metric("Volume (mm³)", f"{geo.volume:,.1f}")
                st.metric("Spec. Surface Area (m²/m³)", f"{geo.specific_surface_area:.1f}")
            
            with col2:
                st.markdown("**💧 Flow Analysis**")
                st.metric("Reynolds Number", f"{flow.reynolds_number:.1f}")
                st.metric("Flow Regime", flow.flow_regime)
                st.metric("Pressure Drop (Pa/m)", f"{flow.pressure_drop_per_m:.2f}")
                st.metric("Mass Transfer (m/s)", f"{flow.mass_transfer_coefficient:.2e}")
                st.metric("Clogging Risk", flow.clogging_risk)
            
            with col3:
                st.markdown("**🧪 Material Buoyancy**")
                for r in design_results:
                    bm = r["buoy"]
                    color = "🟢" if bm.behavior == "Neutrally Buoyant" else \
                            "🟡" if bm.behavior == "Floats" else "🔴"
                    st.metric(
                        f"{color} {r['material']}",
                        bm.behavior,
                        f"eff. density: {bm.effective_density:.3f} g/cm³"
                    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: Results & Comparison
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.all_carriers:
        st.info("📤 Upload and analyze STL files in the first tab to see results here.")
    else:
        carriers = st.session_state.all_carriers
        
        st.markdown("### 📊 Composite Performance Rankings")
        
        # Rankings table
        ranking_data = get_ranking_summary(carriers)
        df_rank = pd.DataFrame(ranking_data)
        
        # Color-code by composite score
        st.dataframe(
            df_rank,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Composite Score": st.column_config.ProgressColumn(
                    "Composite Score", min_value=0, max_value=1),
                "SA/V Score": st.column_config.ProgressColumn(
                    "SA/V Score", min_value=0, max_value=1),
                "Porosity Score": st.column_config.ProgressColumn(
                    "Porosity Score", min_value=0, max_value=1),
                "Flow Score": st.column_config.ProgressColumn(
                    "Flow Score", min_value=0, max_value=1),
                "Buoyancy Score": st.column_config.ProgressColumn(
                    "Buoyancy Score", min_value=0, max_value=1),
            }
        )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏆 Top Performers by Objective")
            
            objectives = ["score_sav", "score_porosity", "score_flow", "score_buoyancy"]
            obj_labels = ["SA/V Ratio", "Porosity", "Flow Efficiency", "Buoyancy"]
            
            for obj, label in zip(objectives, obj_labels):
                best = max(carriers, key=lambda c: getattr(c, obj))
                st.markdown(f"""
                <div class="metric-card">
                    <b>{label}</b><br>
                    🥇 {best.filename.replace('.stl','')} × {best.material}<br>
                    <small>Score: {getattr(best, obj):.4f}</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📈 Score Distribution by Material")
            
            mat_data = []
            for c in carriers:
                mat_data.append({
                    "Material": c.material,
                    "Composite Score": c.composite_score
                })
            df_mat = pd.DataFrame(mat_data)
            
            fig_box = px.box(
                df_mat, x="Material", y="Composite Score",
                color="Material",
                color_discrete_map={
                    "PLA": "#4CAF50", "ABS": "#2196F3",
                    "PETG": "#FF9800", "PP": "#9C27B0"
                },
                title="Composite Score Distribution by Material"
            )
            fig_box.update_layout(
                height=350, showlegend=False,
                plot_bgcolor="white",
                yaxis=dict(range=[0, 1])
            )
            st.plotly_chart(fig_box, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🕸️ Radar Chart: Objective Profile")
        
        # Show radar for top 5 or selected carriers
        top_n = min(5, len(carriers))
        top_carriers = carriers[:top_n]
        
        categories = ["SA/V", "Porosity", "Flow", "Buoyancy", "Biofilm", "Mechanical"]
        
        fig_radar = go.Figure()
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
        
        for i, c in enumerate(top_carriers):
            values = [
                c.score_sav, c.score_porosity, c.score_flow,
                c.score_buoyancy, c.score_biofilm_affinity, c.score_mechanical
            ]
            values += [values[0]]  # close the polygon
            
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill='toself',
                opacity=0.3,
                name=f"{c.filename.replace('.stl','')} × {c.material}",
                line_color=colors[i % len(colors)]
            ))
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            height=450,
            title="Multi-Objective Profile: Top 5 Designs"
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Improvement suggestions
        st.markdown("---")
        st.markdown("### 💡 Design Improvement Suggestions")
        
        selected_for_suggest = st.selectbox(
            "Select design for suggestions",
            options=[f"{c.filename.replace('.stl','')} × {c.material}" for c in carriers],
            key="suggest_select"
        )
        
        if selected_for_suggest:
            idx = [f"{c.filename.replace('.stl','')} × {c.material}" 
                   for c in carriers].index(selected_for_suggest)
            target_carrier = carriers[idx]
            weights_obj = ObjectiveWeights(
                sav_ratio=w_sav, porosity=w_por,
                flow_efficiency=w_flow, buoyancy=w_buoy,
                biofilm_affinity=w_bio, mechanical=w_mech
            )
            weights_obj.normalize()
            suggestions = generate_improvement_suggestions(target_carrier, weights_obj)
            
            for s in suggestions:
                st.markdown(f"""
                <div class="warning-box">
                    💡 {s}
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: Pareto Analysis
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.all_carriers:
        st.info("📤 Upload and analyze STL files to see Pareto analysis here.")
    else:
        carriers = st.session_state.all_carriers
        pareto_carriers = [c for c in carriers if c.is_pareto_optimal]
        dominated_carriers = [c for c in carriers if not c.is_pareto_optimal]
        
        st.markdown("### 🎯 Pareto Frontier Analysis")
        st.caption(
            "Pareto-optimal designs cannot be improved on any objective "
            "without worsening another. These represent the best achievable trade-offs.")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Designs", len(carriers))
        col2.metric("Pareto Optimal", len(pareto_carriers))
        col3.metric("Dominated", len(dominated_carriers))
        
        st.markdown("---")
        
        # Axis selection for Pareto scatter
        col_x, col_y = st.columns(2)
        with col_x:
            x_axis = st.selectbox("X Axis", [
                "SA/V Ratio (mm⁻¹)", "Porosity", "Flow Efficiency",
                "Buoyancy Score", "Specific Surface Area (m²/m³)"
            ], index=0)
        with col_y:
            y_axis = st.selectbox("Y Axis", [
                "SA/V Ratio (mm⁻¹)", "Porosity", "Flow Efficiency",
                "Buoyancy Score", "Specific Surface Area (m²/m³)"
            ], index=2)
        
        axis_map = {
            "SA/V Ratio (mm⁻¹)": "sav_ratio",
            "Porosity": "porosity",
            "Flow Efficiency": "flow_efficiency",
            "Buoyancy Score": "buoyancy_score",
            "Specific Surface Area (m²/m³)": "specific_surface_area"
        }
        
        x_attr = axis_map[x_axis]
        y_attr = axis_map[y_axis]
        
        # Build Pareto scatter plot
        fig_pareto = go.Figure()
        
        mat_colors = {"PLA": "#4CAF50", "ABS": "#2196F3", 
                      "PETG": "#FF9800", "PP": "#9C27B0"}
        
        for mat in selected_materials:
            pareto_pts = [c for c in pareto_carriers if c.material == mat]
            dom_pts = [c for c in dominated_carriers if c.material == mat]
            
            if pareto_pts:
                fig_pareto.add_trace(go.Scatter(
                    x=[getattr(c, x_attr) for c in pareto_pts],
                    y=[getattr(c, y_attr) for c in pareto_pts],
                    mode='markers',
                    marker=dict(
                        size=16, color=mat_colors.get(mat, "#333"),
                        symbol='star', line=dict(width=2, color='white')
                    ),
                    name=f"{mat} (Pareto ★)",
                    text=[f"{c.filename}<br>Rank: {c.rank}<br>Score: {c.composite_score:.3f}"
                          for c in pareto_pts],
                    hovertemplate="<b>%{text}</b><br>" +
                                  f"{x_axis}: %{{x:.4f}}<br>" +
                                  f"{y_axis}: %{{y:.4f}}<extra></extra>"
                ))
            
            if dom_pts:
                fig_pareto.add_trace(go.Scatter(
                    x=[getattr(c, x_attr) for c in dom_pts],
                    y=[getattr(c, y_attr) for c in dom_pts],
                    mode='markers',
                    marker=dict(
                        size=10, color=mat_colors.get(mat, "#333"),
                        opacity=0.4, symbol='circle'
                    ),
                    name=f"{mat} (dominated)",
                    text=[f"{c.filename}<br>Rank: {c.rank}" for c in dom_pts],
                    hovertemplate="<b>%{text}</b><br>" +
                                  f"{x_axis}: %{{x:.4f}}<br>" +
                                  f"{y_axis}: %{{y:.4f}}<extra></extra>"
                ))
        
        fig_pareto.update_layout(
            title=f"Pareto Frontier: {x_axis} vs {y_axis}",
            xaxis_title=x_axis,
            yaxis_title=y_axis,
            height=500,
            plot_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3)
        )
        fig_pareto.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
        fig_pareto.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
        
        st.plotly_chart(fig_pareto, use_container_width=True)
        
        # Pareto optimal table
        st.markdown("### ⭐ Pareto-Optimal Designs")
        if pareto_carriers:
            pareto_data = [{
                "Design": c.filename.replace(".stl", ""),
                "Material": c.material,
                "Overall Rank": c.rank,
                "Composite Score": c.composite_score,
                "SA/V (mm⁻¹)": c.sav_ratio,
                "Porosity": c.porosity,
                "Flow Efficiency": c.flow_efficiency,
                "Buoyancy Score": c.buoyancy_score,
            } for c in sorted(pareto_carriers, key=lambda c: c.rank)]
            
            st.dataframe(pd.DataFrame(pareto_data), use_container_width=True,
                         hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: Flow Visualization
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    if not st.session_state.results:
        st.info("📤 Upload and analyze STL files to see flow analysis here.")
    else:
        st.markdown("### 💧 Flow Analysis Dashboard")

        # Population view: effective density vs porosity (all geometry × material runs)
        st.markdown("#### Effective Density vs Porosity")
        st.caption(
            "Each point is one geometry × material combination. "
            "Effective density is solid polymer mass divided by bounding-box volume (see buoyancy module). "
            "Points below the fluid reference line tend to float; above tend to sink."
        )
        _res = st.session_state.results
        _ed_rows = []
        for r in _res:
            _g, _b = r["geo"], r["buoy"]
            _ed_rows.append({
                "Porosity": _g.porosity,
                "Effective Density (g/cm³)": _b.effective_density,
                "Material": r["material"],
                "Design": r["filename"].replace(".stl", ""),
                "Behavior": _b.behavior,
            })
        df_ed = pd.DataFrame(_ed_rows)
        _mat_colors = {
            "PLA": "#4CAF50", "ABS": "#2196F3",
            "PETG": "#FF9800", "PP": "#9C27B0",
        }
        fig_ed = px.scatter(
            df_ed,
            x="Porosity",
            y="Effective Density (g/cm³)",
            color="Material",
            hover_data=["Design", "Behavior"],
            color_discrete_map=_mat_colors,
        )
        _fluid_rho = _res[0]["buoy"].fluid_density
        fig_ed.add_hline(
            y=_fluid_rho,
            line_dash="dash",
            line_color="#2563eb",
            annotation_text=f"Fluid density ≈ {_fluid_rho:.3f} g/cm³",
            annotation_position="right",
        )
        fig_ed.update_layout(
            title="Effective Density vs Porosity",
            height=420,
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_title="Porosity (void fraction)",
            yaxis_title="Effective density (g/cm³)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=50),
        )
        fig_ed.update_xaxes(range=[0, 1], showgrid=True, gridcolor="#f0f0f0")
        fig_ed.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
        st.plotly_chart(fig_ed, use_container_width=True)

        st.markdown("---")
        
        unique_designs = list({r["filename"]: r for r in st.session_state.results}.values())
        selected_flow_design = st.selectbox(
            "Select design", 
            [r["filename"] for r in unique_designs],
            key="flow_design_select"
        )
        
        design_result = next(r for r in unique_designs 
                              if r["filename"] == selected_flow_design)
        geo = design_result["geo"]
        flow = design_result["flow"]
        
        # Flow metric cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Reynolds Number", f"{flow.reynolds_number:.1f}",
                    delta=flow.flow_regime)
        col2.metric("Pressure Drop (Pa/m)", f"{flow.pressure_drop_per_m:.2f}")
        col3.metric("Mass Transfer (m/s)", f"{flow.mass_transfer_coefficient:.2e}")
        col4.metric("Clogging Risk", flow.clogging_risk)
        
        st.markdown("---")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("#### Velocity vs Pressure Drop (Ergun Curve)")
            velocities = np.linspace(0.001, 0.1, 50)
            pressure_drops = []
            for v in velocities:
                f_temp = compute_flow_metrics(geo, v, fluid_density, fluid_viscosity)
                pressure_drops.append(f_temp.pressure_drop_per_m)
            
            fig_pd = go.Figure()
            fig_pd.add_trace(go.Scatter(
                x=velocities * 1000,  # convert to mm/s for display
                y=pressure_drops,
                mode='lines',
                line=dict(color='#2e86ab', width=2.5),
                fill='tozeroy',
                fillcolor='rgba(46,134,171,0.1)'
            ))
            fig_pd.add_vline(
                x=flow_velocity * 1000,
                line_dash="dash", line_color="red",
                annotation_text="Current operating point"
            )
            fig_pd.update_layout(
                xaxis_title="Superficial Velocity (mm/s)",
                yaxis_title="Pressure Drop (Pa/m)",
                height=320, plot_bgcolor="white"
            )
            fig_pd.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
            fig_pd.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
            st.plotly_chart(fig_pd, use_container_width=True)
        
        with col_right:
            st.markdown("#### Porosity vs Flow Efficiency")
            porosities, flow_eff_values = _porosity_flow_curve(
                geo.sav_ratio, geo.surface_area, geo.volume,
                geo.bounding_box_volume, geo.porosity,
                geo.hydraulic_diameter, geo.specific_surface_area,
                flow_velocity, fluid_density, fluid_viscosity,
            )
            
            fig_fe = go.Figure()
            fig_fe.add_trace(go.Scatter(
                x=porosities,
                y=flow_eff_values,
                mode='lines',
                line=dict(color='#27ae60', width=2.5),
                fill='tozeroy',
                fillcolor='rgba(39,174,96,0.1)'
            ))
            fig_fe.add_vline(
                x=geo.porosity,
                line_dash="dash", line_color="red",
                annotation_text=f"Current: {geo.porosity:.2f}"
            )
            fig_fe.update_layout(
                xaxis_title="Porosity (void fraction)",
                yaxis_title="Flow Efficiency Score",
                height=320, plot_bgcolor="white",
                yaxis=dict(range=[0, 1])
            )
            fig_fe.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
            fig_fe.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
            st.plotly_chart(fig_fe, use_container_width=True)
        
        # Buoyancy comparison
        st.markdown("#### Material Buoyancy Comparison")
        bm_results = compare_materials_buoyancy(geo, fluid_density)
        
        buoy_data = []
        for mat, bm in bm_results.items():
            buoy_data.append({
                "Material": mat,
                "Effective Density (g/cm³)": bm.effective_density,
                "Fluid Density (g/cm³)": bm.fluid_density,
                "Behavior": bm.behavior,
                "Score": bm.buoyancy_score,
                "Net Force (N)": bm.net_force
            })
        
        df_buoy = pd.DataFrame(buoy_data)
        
        fig_buoy = go.Figure()
        colors_mat = {"PLA": "#4CAF50", "ABS": "#2196F3", 
                      "PETG": "#FF9800", "PP": "#9C27B0"}
        
        for _, row in df_buoy.iterrows():
            fig_buoy.add_trace(go.Bar(
                name=row["Material"],
                x=[row["Material"]],
                y=[row["Effective Density (g/cm³)"]],
                marker_color=colors_mat.get(row["Material"], "#333"),
                text=[row["Behavior"]],
                textposition="outside"
            ))
        
        fig_buoy.add_hline(
            y=bm_results["PLA"].fluid_density,
            line_dash="dash", line_color="blue",
            annotation_text=f"Fluid density: {bm_results['PLA'].fluid_density:.3f} g/cm³"
        )
        fig_buoy.update_layout(
            title="Effective Carrier Density vs Fluid Density",
            yaxis_title="Density (g/cm³)",
            height=350, showlegend=False,
            plot_bgcolor="white"
        )
        st.plotly_chart(fig_buoy, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: Export Report
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    if not st.session_state.all_carriers:
        st.info("📤 Run an analysis first to generate an exportable report.")
    else:
        st.markdown("### 📋 Export Analysis Report")
        
        carriers = st.session_state.all_carriers
        
        # Build comprehensive dataframe
        export_data = []
        for c in carriers:
            # Find matching result for raw geo/flow data
            matching = [r for r in st.session_state.results 
                       if r["design_id"] == c.design_id]
            
            row = {
                "Design ID": c.design_id,
                "Filename": c.filename,
                "Material": c.material,
                "Rank": c.rank,
                "Composite Score": c.composite_score,
                "Pareto Optimal": c.is_pareto_optimal,
                "SA/V Ratio (mm⁻¹)": c.sav_ratio,
                "Porosity": c.porosity,
                "Flow Efficiency Score": c.flow_efficiency,
                "Buoyancy Score": c.buoyancy_score,
                "Mass Transfer Coeff (m/s)": c.mass_transfer_coeff,
                "Pressure Drop (Pa/m)": c.pressure_drop,
            }
            
            if matching:
                geo = matching[0]["geo"]
                buoy = matching[0]["buoy"]
                row.update({
                    "Effective Density (g/cm³)": buoy.effective_density,
                    "Surface Area (mm²)": geo.surface_area,
                    "Volume (mm³)": geo.volume,
                    "Specific SA (m²/m³)": geo.specific_surface_area,
                    "Hydraulic Diameter (mm)": geo.hydraulic_diameter,
                    "Dim X (mm)": geo.dim_x,
                    "Dim Y (mm)": geo.dim_y,
                    "Dim Z (mm)": geo.dim_z,
                    "Triangles": geo.num_triangles,
                    "Watertight": geo.is_watertight,
                })
            
            export_data.append(row)
        
        df_export = pd.DataFrame(export_data)
        st.dataframe(df_export, use_container_width=True, hide_index=True)
        
        # CSV download
        csv = df_export.to_csv(index=False)
        st.download_button(
            label="⬇️ Download Full Results (CSV)",
            data=csv,
            file_name="cdmo_analysis_results.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
        
        # Summary statistics
        st.markdown("---")
        st.markdown("### 📊 Summary Statistics")
        
        summary_stats = df_export[[
            "SA/V Ratio (mm⁻¹)", "Porosity", 
            "Flow Efficiency Score", "Composite Score"
        ]].describe().round(4)
        
        st.dataframe(summary_stats, use_container_width=True)
        
        # Analysis parameters used
        st.markdown("---")
        st.markdown("### ⚙️ Analysis Parameters Used")
        params = {
            "Fluid Type": FLUID_PROPERTIES[fluid_type]["name"],
            "Fluid Density (kg/m³)": fluid_density,
            "Fluid Viscosity (Pa·s)": fluid_viscosity,
            "Superficial Velocity (m/s)": flow_velocity,
            "Temperature (°C)": temperature,
            "Weight SA/V Ratio": w_sav,
            "Weight Porosity": w_por,
            "Weight Flow Efficiency": w_flow,
            "Weight Buoyancy": w_buoy,
            "Weight Biofilm Affinity": w_bio,
            "Weight Mechanical": w_mech,
        }
        st.json(params)
