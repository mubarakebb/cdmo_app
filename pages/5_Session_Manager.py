"""
Session Manager Page - CDMO Phase 2
Save, reload and manage complete analysis sessions.
Avoids re-uploading all 16 STL files every session.
"""

import streamlit as st
import pandas as pd
import os

from utils.ui import HeaderSpec, page_header, sidebar_brand

from utils.persistence import (
    save_session, load_session, list_sessions,
    delete_session, export_session_csv
)

st.set_page_config(page_title="Session Manager", page_icon="💾", layout="wide")

page_header(
    HeaderSpec(
        icon="💾",
        title="Session Manager",
        subtitle="Save and reload complete analysis sessions — no need to re-upload STL files.",
        accent="#1E8449",
        accent_2="#1A5276",
    )
)
sidebar_brand()

st.markdown(
    """
    <style>
      .session-card{
        background: var(--cdmo-surface-2);
        border: 1px solid rgba(15, 23, 42, 0.10);
        border-left: 4px solid var(--cdmo-accent);
        border-radius: 12px;
        padding: 1rem 1.05rem;
        margin: 0.45rem 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

tab_save, tab_load, tab_export = st.tabs(["💾 Save Session", "📂 Load Session", "⬇️ Export Data"])

# ══════════════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════════════
with tab_save:
    st.markdown("### Save Current Session")

    if not st.session_state.get("all_carriers"):
        st.info("No analysis data in current session. "
                "Upload and analyse STL files on the main page first.")
    else:
        carriers = st.session_state.all_carriers
        results = st.session_state.get("results", [])

        n_designs = len(set(c.filename for c in carriers))
        n_materials = len(set(c.material for c in carriers))
        n_pareto = len([c for c in carriers if c.is_pareto_optimal])

        col1, col2, col3 = st.columns(3)
        col1.metric("Geometries", n_designs)
        col2.metric("Combinations", len(carriers))
        col3.metric("Pareto Optimal", n_pareto)

        session_name = st.text_input(
            "Session name",
            value=f"16_carriers_analysis",
            placeholder="e.g., phase1_baseline_all_materials"
        )

        # Capture current sidebar parameters
        params_snapshot = {
            "fluid_density": st.session_state.get("fluid_density", 1015.0),
            "fluid_viscosity": st.session_state.get("fluid_viscosity", 0.003),
            "flow_velocity": st.session_state.get("flow_velocity", 0.01),
            "weights": {
                "sav_ratio": st.session_state.get("w_sav", 0.30),
                "porosity": st.session_state.get("w_por", 0.20),
                "flow_efficiency": st.session_state.get("w_flow", 0.20),
                "buoyancy": st.session_state.get("w_buoy", 0.15),
                "biofilm_affinity": st.session_state.get("w_bio", 0.10),
                "mechanical": st.session_state.get("w_mech", 0.05),
            }
        }

        if st.button("💾 Save Session", type="primary", use_container_width=True):
            if not session_name.strip():
                st.warning("Please enter a session name.")
            else:
                try:
                    saved_path = save_session(
                        session_name, results, carriers, params_snapshot)
                    st.success(f"✅ Session saved: `{os.path.basename(saved_path)}`")
                except Exception as e:
                    st.error(f"Save failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# LOAD
# ══════════════════════════════════════════════════════════════════════════════
with tab_load:
    st.markdown("### Load a Saved Session")

    sessions = list_sessions()

    if not sessions:
        st.info("No saved sessions found. Save a session first using the Save tab.")
    else:
        st.markdown(f"**{len(sessions)} saved session(s) found**")

        for s in sessions:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div class="session-card">
                        <b>📋 {s['session_name']}</b><br>
                        <small>Saved: {s['timestamp']} | 
                        {s['carriers_count']} combinations | 
                        {s['results_count']} results</small>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("📂 Load", key=f"load_{s['filepath']}",
                                 use_container_width=True):
                        try:
                            data = load_session(s["filepath"])
                            st.session_state.all_carriers = data["all_carriers"]
                            st.session_state.results = data["results"]
                            st.success(
                                f"✅ Loaded '{s['session_name']}' — "
                                f"{len(data['all_carriers'])} designs ready.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Load failed: {e}")
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{s['filepath']}",
                                 use_container_width=True):
                        if delete_session(s["filepath"]):
                            st.success("Deleted.")
                            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ══════════════════════════════════════════════════════════════════════════════
with tab_export:
    st.markdown("### Export Analysis Data")

    if not st.session_state.get("all_carriers"):
        st.info("No analysis data to export. Load a session or run an analysis first.")
    else:
        carriers = st.session_state.all_carriers
        results = st.session_state.get("results", [])

        st.markdown(f"Ready to export **{len(carriers)} design-material combinations**.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Full Results CSV")
            st.caption("All metrics, scores, Pareto flags, geometry data.")
            csv_data = export_session_csv(carriers, results)
            st.download_button(
                "⬇️ Download Full CSV",
                data=csv_data,
                file_name="cdmo_full_results.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )

        with col2:
            st.markdown("#### Pareto-Optimal Only CSV")
            st.caption("Filtered to Pareto-optimal designs only.")
            pareto_carriers = [c for c in carriers if c.is_pareto_optimal]
            pareto_results = [r for r in results
                              if any(c.design_id == r["design_id"]
                                     for c in pareto_carriers)]
            if pareto_carriers:
                pareto_csv = export_session_csv(pareto_carriers, pareto_results)
                st.download_button(
                    "⬇️ Download Pareto CSV",
                    data=pareto_csv,
                    file_name="cdmo_pareto_optimal.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No Pareto-optimal designs identified yet.")

        st.markdown("---")
        st.markdown("#### Data Preview")

        preview_data = [{
            "Design": c.filename.replace(".stl", ""),
            "Material": c.material,
            "Rank": c.rank,
            "Composite Score": c.composite_score,
            "SA/V (mm⁻¹)": c.sav_ratio,
            "Porosity": c.porosity,
            "Pareto": "★" if c.is_pareto_optimal else "",
        } for c in sorted(carriers, key=lambda c: c.rank)[:20]]

        st.dataframe(pd.DataFrame(preview_data), use_container_width=True,
                     hide_index=True)
        if len(carriers) > 20:
            st.caption(f"Showing first 20 of {len(carriers)} rows.")
