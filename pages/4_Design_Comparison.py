"""
Design Comparison Heatmap Page - CDMO Phase 2
Visual comparison of all 16 carriers across all objectives simultaneously.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os

from utils.ui import HeaderSpec, page_header, sidebar_brand

from core.materials import MATERIALS

st.set_page_config(page_title="Design Comparison", page_icon="🗺️", layout="wide")

page_header(
    HeaderSpec(
        icon="🗺️",
        title="Design Comparison Matrix",
        subtitle="Visual comparison of all carrier designs across objectives and materials.",
        accent="#C0392B",
        accent_2="#1A5276",
    )
)
sidebar_brand()

# ─── Check for session data ───────────────────────────────────────────────────
# Try to load from main app session
if "all_carriers" not in st.session_state or not st.session_state.all_carriers:
    st.info("""
    📤 **No analysis data found.**
    
    Please upload and analyse your STL files on the main **Upload & Analyse** page first,
    then return here to compare all designs.
    """)
    st.stop()

carriers = st.session_state.all_carriers
results = st.session_state.get("results", [])

st.markdown(f"**{len(carriers)} design-material combinations loaded** "
            f"({len(set(c.filename for c in carriers))} geometries × "
            f"{len(set(c.material for c in carriers))} materials)")

# ─── Sidebar filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Display Options")

    selected_mats = st.multiselect(
        "Filter by material",
        options=list(MATERIALS.keys()),
        default=list(MATERIALS.keys())
    )

    show_raw = st.radio(
        "Value display",
        ["Normalised scores (0-1)", "Raw metric values"],
        index=0
    )

    sort_by = st.selectbox(
        "Sort designs by",
        ["Composite Score", "SA/V Ratio", "Porosity",
         "Flow Efficiency", "Buoyancy Score", "Filename"]
    )

    show_pareto_only = st.checkbox("Show Pareto-optimal only", False)

# ─── Filter ───────────────────────────────────────────────────────────────────
filtered = [c for c in carriers if c.material in selected_mats]
if show_pareto_only:
    filtered = [c for c in filtered if c.is_pareto_optimal]

if not filtered:
    st.warning("No designs match current filter criteria.")
    st.stop()

# ─── Sort ─────────────────────────────────────────────────────────────────────
sort_map = {
    "Composite Score": lambda c: -c.composite_score,
    "SA/V Ratio": lambda c: -c.sav_ratio,
    "Porosity": lambda c: -c.porosity,
    "Flow Efficiency": lambda c: -c.flow_efficiency,
    "Buoyancy Score": lambda c: -c.buoyancy_score,
    "Filename": lambda c: c.filename,
}
filtered.sort(key=sort_map[sort_by])

# ─── Build comparison data ────────────────────────────────────────────────────
labels = [f"{c.filename.replace('.stl','')}\n({c.material})" for c in filtered]

if show_raw == "Normalised scores (0-1)":
    metrics = {
        "SA/V\nScore":    [c.score_sav for c in filtered],
        "Porosity\nScore": [c.score_porosity for c in filtered],
        "Flow\nScore":    [c.score_flow for c in filtered],
        "Buoyancy\nScore": [c.score_buoyancy for c in filtered],
        "Biofilm\nAffinity": [c.score_biofilm_affinity for c in filtered],
        "Mechanical\nScore": [c.score_mechanical for c in filtered],
        "Composite\nScore": [c.composite_score for c in filtered],
    }
    colorscale = "RdYlGn"
    zmin, zmax = 0, 1
else:
    metrics = {
        "SA/V Ratio\n(mm⁻¹)":       [c.sav_ratio for c in filtered],
        "Porosity":                  [c.porosity for c in filtered],
        "Flow\nEfficiency":          [c.flow_efficiency for c in filtered],
        "Buoyancy\nScore":           [c.buoyancy_score for c in filtered],
        "Specific SA\n(m²/m³)":      [c.specific_surface_area for c in filtered],
        "Pressure Drop\n(Pa/m)":     [c.pressure_drop for c in filtered],
        "Mass Transfer\n(µm/s)":     [c.mass_transfer_coeff * 1e6 for c in filtered],
    }
    colorscale = "Viridis"
    zmin, zmax = None, None

metric_names = list(metrics.keys())
z_matrix = np.array([metrics[m] for m in metric_names])  # shape: (metrics, designs)

# ─── Heatmap ──────────────────────────────────────────────────────────────────
st.markdown("### Performance Heatmap")
st.caption("Each row is a performance metric. Each column is a design-material combination. "
           "Greener = better (for normalised view).")

# Normalise each row independently for colour consistency in raw mode
if show_raw == "Raw metric values":
    # Invert pressure drop (lower is better)
    z_display = z_matrix.copy().astype(float)
    if "Pressure Drop\n(Pa/m)" in metric_names:
        pdrop_idx = metric_names.index("Pressure Drop\n(Pa/m)")
        row = z_display[pdrop_idx]
        row_min, row_max = row.min(), row.max()
        if row_max > row_min:
            z_display[pdrop_idx] = 1 - (row - row_min) / (row_max - row_min)
else:
    z_display = z_matrix.copy()

# Hover text
hover = []
for i, metric in enumerate(metric_names):
    row_hover = []
    for j, c in enumerate(filtered):
        row_hover.append(
            f"<b>{c.filename.replace('.stl','')}</b> × {c.material}<br>"
            f"{metric.replace(chr(10), ' ')}: {z_matrix[i][j]:.4f}<br>"
            f"Rank: {c.rank} | Pareto: {'Yes' if c.is_pareto_optimal else 'No'}"
        )
    hover.append(row_hover)

fig_heat = go.Figure(data=go.Heatmap(
    z=z_display,
    x=labels,
    y=metric_names,
    colorscale=colorscale,
    zmin=zmin if zmin is not None else z_display.min(),
    zmax=zmax if zmax is not None else z_display.max(),
    text=np.round(z_matrix, 3),
    texttemplate="%{text}",
    textfont={"size": 9},
    hovertext=hover,
    hovertemplate="%{hovertext}<extra></extra>",
    colorbar=dict(title="Score" if show_raw == "Normalised scores (0-1)" else "Value")
))

# Mark Pareto-optimal with annotation
pareto_indices = [j for j, c in enumerate(filtered) if c.is_pareto_optimal]
for j in pareto_indices:
    fig_heat.add_annotation(
        x=labels[j], y=metric_names[-1],
        text="★", showarrow=False,
        font=dict(size=14, color="gold"),
        yshift=20
    )

fig_heat.update_layout(
    height=max(400, len(metric_names) * 55 + 100),
    xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
    yaxis=dict(tickfont=dict(size=10)),
    margin=dict(l=140, r=40, t=60, b=120),
)
st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# ─── Material comparison matrix ───────────────────────────────────────────────
st.markdown("### Material × Design Average Performance")
st.caption("Average composite score for each geometry-material combination.")

# Pivot: rows = designs, cols = materials
all_filenames = sorted(set(c.filename for c in carriers))
all_materials = sorted(set(c.material for c in carriers))

pivot_data = np.full((len(all_filenames), len(all_materials)), np.nan)
for c in carriers:
    i = all_filenames.index(c.filename)
    j = all_materials.index(c.material)
    pivot_data[i][j] = c.composite_score

clean_filenames = [f.replace(".stl", "") for f in all_filenames]

fig_pivot = go.Figure(data=go.Heatmap(
    z=pivot_data,
    x=all_materials,
    y=clean_filenames,
    colorscale="Blues",
    text=np.where(np.isnan(pivot_data), "", np.round(pivot_data, 3)),
    texttemplate="%{text}",
    textfont={"size": 10},
    colorbar=dict(title="Composite Score"),
    zmin=0, zmax=1
))
fig_pivot.update_layout(
    title="Composite Score: Geometry × Material",
    xaxis_title="Material",
    yaxis_title="Carrier Geometry",
    height=max(350, len(all_filenames) * 28 + 100),
    margin=dict(l=120, r=40, t=60, b=60)
)
st.plotly_chart(fig_pivot, use_container_width=True)

st.markdown("---")

# ─── Parallel coordinates ─────────────────────────────────────────────────────
st.markdown("### Parallel Coordinates — Design Space Explorer")
st.caption("Drag axes to reorder. Brush on any axis to filter designs. "
           "Useful for finding designs that satisfy multiple criteria simultaneously.")

mat_color_map = {"PLA": 0, "ABS": 1, "PETG": 2, "PP": 3}

pc_data = {
    "SA/V Ratio": [c.score_sav for c in filtered],
    "Porosity": [c.score_porosity for c in filtered],
    "Flow Efficiency": [c.score_flow for c in filtered],
    "Buoyancy": [c.score_buoyancy for c in filtered],
    "Biofilm Affinity": [c.score_biofilm_affinity for c in filtered],
    "Composite Score": [c.composite_score for c in filtered],
    "Material (colour)": [mat_color_map.get(c.material, 0) for c in filtered],
}

fig_pc = go.Figure(data=go.Parcoords(
    line=dict(
        color=pc_data["Material (colour)"],
        colorscale=[[0, "#4CAF50"], [0.33, "#2196F3"],
                    [0.66, "#FF9800"], [1.0, "#9C27B0"]],
        showscale=True,
        colorbar=dict(
            tickvals=[0, 1, 2, 3],
            ticktext=["PLA", "ABS", "PETG", "PP"],
            title="Material"
        )
    ),
    dimensions=[
        dict(label=k, values=pc_data[k],
             range=[0, 1] if k != "Material (colour)" else [0, 3])
        for k in pc_data
    ]
))
fig_pc.update_layout(height=400, margin=dict(l=80, r=80, t=40, b=40))
st.plotly_chart(fig_pc, use_container_width=True)

st.markdown("---")

# ─── Rankings Table ───────────────────────────────────────────────────────────
st.markdown("### Full Rankings Table")

table_data = []
for c in filtered:
    table_data.append({
        "Rank": c.rank,
        "Design": c.filename.replace(".stl", ""),
        "Material": c.material,
        "Composite": c.composite_score,
        "SA/V Score": c.score_sav,
        "Porosity Score": c.score_porosity,
        "Flow Score": c.score_flow,
        "Buoyancy Score": c.score_buoyancy,
        "SA/V Raw (mm⁻¹)": round(c.sav_ratio, 4),
        "Porosity Raw": round(c.porosity, 4),
        "Pareto": "★" if c.is_pareto_optimal else "",
    })

st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True,
             column_config={
                 "Composite": st.column_config.ProgressColumn(min_value=0, max_value=1),
                 "SA/V Score": st.column_config.ProgressColumn(min_value=0, max_value=1),
                 "Porosity Score": st.column_config.ProgressColumn(min_value=0, max_value=1),
                 "Flow Score": st.column_config.ProgressColumn(min_value=0, max_value=1),
                 "Buoyancy Score": st.column_config.ProgressColumn(min_value=0, max_value=1),
             })
