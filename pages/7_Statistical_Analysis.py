"""
Statistical Analysis Page - CDMO Phase 3
Rigorous statistical comparison of geometry families and materials.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.ui import HeaderSpec, page_header, sidebar_brand

from core.statistics import run_full_statistical_analysis

st.set_page_config(page_title="Statistical Analysis", page_icon="📊", layout="wide")

page_header(
    HeaderSpec(
        icon="📊",
        title="Statistical Analysis",
        subtitle="Rigorous hypothesis testing, effect sizes, and correlation analysis.",
        accent="#1E8449",
        accent_2="#1A5276",
    )
)
sidebar_brand()

st.markdown(
    """
    <style>
      .sig-yes { color: #16a34a; font-weight: 800; }
      .sig-no  { color: #dc2626; }
    </style>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.get("all_carriers"):
    st.info("📤 Upload and analyse STL files on the main page first.")
    st.stop()

carriers = st.session_state.all_carriers

if st.button("▶ Run Statistical Analysis", type="primary"):
    with st.spinner("Running statistical tests..."):
        report = run_full_statistical_analysis(carriers)
        st.session_state.stat_report = report
    st.success("Analysis complete.")

if "stat_report" not in st.session_state:
    st.info("Click **Run Statistical Analysis** above.")
    st.stop()

report = st.session_state.stat_report

# ─── Key Findings ─────────────────────────────────────────────────────────────
st.markdown("### 🔑 Key Statistical Findings")
for finding in report.key_findings:
    st.markdown(f"""
    <div style="background:#f0f9ff;border-left:4px solid #2e86ab;
                padding:0.7rem 1rem;border-radius:6px;margin:0.4rem 0;font-size:0.9rem;">
        {finding}
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─── Descriptive Stats ────────────────────────────────────────────────────────
st.markdown("### Descriptive Statistics by Material")

materials = sorted(set(c.material for c in carriers))
metric_attrs = {
    "SA/V Ratio (mm⁻¹)": "sav_ratio",
    "Porosity": "porosity",
    "Flow Efficiency": "flow_efficiency",
    "Buoyancy Score": "buoyancy_score",
    "Composite Score": "composite_score",
}

desc_rows = []
for metric_name, attr in metric_attrs.items():
    for mat in materials:
        vals = [getattr(c, attr) for c in carriers if c.material == mat]
        if vals:
            desc_rows.append({
                "Metric": metric_name,
                "Material": mat,
                "N": len(vals),
                "Mean": round(np.mean(vals), 4),
                "Std Dev": round(np.std(vals, ddof=1) if len(vals) > 1 else 0, 4),
                "Median": round(np.median(vals), 4),
                "Min": round(min(vals), 4),
                "Max": round(max(vals), 4),
                "CV (%)": round(np.std(vals, ddof=1) / abs(np.mean(vals)) * 100 
                                if np.mean(vals) != 0 and len(vals) > 1 else 0, 1),
            })

if desc_rows:
    df_desc = pd.DataFrame(desc_rows)
    st.dataframe(df_desc, use_container_width=True, hide_index=True)

st.markdown("---")

# ─── Box Plots ────────────────────────────────────────────────────────────────
st.markdown("### Distribution Plots by Material")
mat_colors = {"PLA": "#4CAF50", "ABS": "#2196F3", "PETG": "#FF9800", "PP": "#9C27B0"}

sel_metric = st.selectbox("Select metric", list(metric_attrs.keys()))
attr = metric_attrs[sel_metric]

plot_data = pd.DataFrame({
    "Material": [c.material for c in carriers],
    sel_metric: [getattr(c, attr) for c in carriers],
    "Design": [c.filename.replace(".stl", "") for c in carriers],
})

col_box, col_violin = st.columns(2)
with col_box:
    fig_box = px.box(plot_data, x="Material", y=sel_metric,
                     color="Material", color_discrete_map=mat_colors,
                     points="all", hover_data=["Design"],
                     title=f"Box Plot: {sel_metric}")
    fig_box.update_layout(height=380, showlegend=False, plot_bgcolor="white")
    st.plotly_chart(fig_box, use_container_width=True)

with col_violin:
    fig_vio = px.violin(plot_data, x="Material", y=sel_metric,
                        color="Material", color_discrete_map=mat_colors,
                        box=True, points="all", hover_data=["Design"],
                        title=f"Violin Plot: {sel_metric}")
    fig_vio.update_layout(height=380, showlegend=False, plot_bgcolor="white")
    st.plotly_chart(fig_vio, use_container_width=True)

st.markdown("---")

# ─── ANOVA / Kruskal-Wallis Results ──────────────────────────────────────────
st.markdown("### Hypothesis Tests — Material Effect on Performance")
st.caption("Tests whether material type has a statistically significant effect on each metric. "
           "ANOVA used when normality and equal variance hold; Kruskal-Wallis otherwise.")

if report.anova_results:
    anova_rows = []
    for metric, res in report.anova_results.items():
        anova_rows.append({
            "Metric": metric,
            "Test": res.test_name,
            "Statistic": res.statistic,
            "p-value": res.p_value,
            "Significant (α=0.05)": "✅ Yes" if res.significant else "❌ No",
            "Effect Size": res.effect_size,
            "Effect Magnitude": res.effect_magnitude.title(),
        })
    df_anova = pd.DataFrame(anova_rows)
    st.dataframe(df_anova, use_container_width=True, hide_index=True,
                 column_config={
                     "p-value": st.column_config.NumberColumn(format="%.5f"),
                     "Effect Size": st.column_config.NumberColumn(format="%.4f"),
                 })

st.markdown("---")

# ─── Pairwise Comparisons ─────────────────────────────────────────────────────
st.markdown("### Pairwise Material Comparisons")
st.caption("Mann-Whitney U test with Bonferroni correction for multiple comparisons.")

sel_pw_metric = st.selectbox("Select metric for pairwise comparison",
                              list(report.pairwise.keys()), key="pw_metric")

if sel_pw_metric in report.pairwise:
    pw_rows = []
    for res in report.pairwise[sel_pw_metric]:
        pw_rows.append({
            "Comparison": res.test_name.replace("Mann-Whitney U ", ""),
            "U Statistic": res.statistic,
            "p-value (corrected)": res.p_value,
            "Significant": "✅ Yes" if res.significant else "❌ No",
            "Cohen's d": res.effect_size,
            "Effect": res.effect_magnitude.title(),
            "Interpretation": res.interpretation[:80] + "..." if len(res.interpretation) > 80
                              else res.interpretation,
        })
    st.dataframe(pd.DataFrame(pw_rows), use_container_width=True, hide_index=True,
                 column_config={
                     "p-value (corrected)": st.column_config.NumberColumn(format="%.5f"),
                     "Cohen's d": st.column_config.NumberColumn(format="%.4f"),
                 })

st.markdown("---")

# ─── Correlation Heatmap ──────────────────────────────────────────────────────
st.markdown("### Correlation Analysis")
st.caption("Pearson and Spearman correlations between performance metrics.")

if report.correlations:
    all_vars = list(set(
        [r.var1 for r in report.correlations] + [r.var2 for r in report.correlations]))
    
    n = len(all_vars)
    corr_matrix = np.zeros((n, n))
    np.fill_diagonal(corr_matrix, 1.0)
    
    for r in report.correlations:
        i, j = all_vars.index(r.var1), all_vars.index(r.var2)
        corr_matrix[i][j] = r.pearson_r
        corr_matrix[j][i] = r.pearson_r
    
    fig_corr = go.Figure(data=go.Heatmap(
        z=corr_matrix, x=all_vars, y=all_vars,
        colorscale="RdBu", zmin=-1, zmax=1,
        text=np.round(corr_matrix, 3), texttemplate="%{text}",
        textfont={"size": 10},
        colorbar=dict(title="Pearson r")))
    fig_corr.update_layout(
        title="Pearson Correlation Matrix", height=420,
        xaxis=dict(tickangle=-30))
    st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown("#### Top Correlations Table")
    corr_rows = [{
        "Variables": f"{r.var1} ↔ {r.var2}",
        "Pearson r": r.pearson_r,
        "Pearson p": r.pearson_p,
        "Spearman r": r.spearman_r,
        "Spearman p": r.spearman_p,
        "Strength": r.strength.title(),
        "Direction": r.direction.title(),
    } for r in report.correlations[:10]]
    st.dataframe(pd.DataFrame(corr_rows), use_container_width=True, hide_index=True,
                 column_config={
                     "Pearson r": st.column_config.NumberColumn(format="%.4f"),
                     "Pearson p": st.column_config.NumberColumn(format="%.5f"),
                     "Spearman r": st.column_config.NumberColumn(format="%.4f"),
                     "Spearman p": st.column_config.NumberColumn(format="%.5f"),
                 })

st.markdown("---")

# ─── Regression Models ────────────────────────────────────────────────────────
st.markdown("### Regression Models")
st.caption("Linear regression relationships between geometric and performance metrics.")

if report.regression_models:
    sav_vals = [c.sav_ratio for c in carriers]
    por_vals = [c.porosity for c in carriers]
    comp_vals = [c.composite_score for c in carriers]
    flow_vals = [c.flow_efficiency for c in carriers]
    
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        fig_reg1 = go.Figure()
        fig_reg1.add_trace(go.Scatter(
            x=sav_vals, y=comp_vals, mode='markers',
            marker=dict(size=8, color="#2e86ab", opacity=0.7), name="Data"))
        
        model = report.regression_models.get("SAV→Composite", {})
        if model:
            x_line = np.linspace(min(sav_vals), max(sav_vals), 50)
            y_line = model["slope"] * x_line + model["intercept"]
            fig_reg1.add_trace(go.Scatter(
                x=x_line, y=y_line, mode='lines',
                line=dict(color="#e74c3c", dash="dash", width=2),
                name=f"Fit (R²={model['r_squared']:.3f})"))
            fig_reg1.update_layout(
                title=f"SA/V → Composite Score (R²={model['r_squared']:.3f})",
                xaxis_title="SA/V Ratio (mm⁻¹)", yaxis_title="Composite Score",
                height=320, plot_bgcolor="white")
        st.plotly_chart(fig_reg1, use_container_width=True)
    
    with col_r2:
        fig_reg2 = go.Figure()
        fig_reg2.add_trace(go.Scatter(
            x=por_vals, y=flow_vals, mode='markers',
            marker=dict(size=8, color="#27ae60", opacity=0.7), name="Data"))
        
        model2 = report.regression_models.get("Porosity→Flow", {})
        if model2:
            x_line2 = np.linspace(min(por_vals), max(por_vals), 50)
            y_line2 = model2["slope"] * x_line2 + model2["intercept"]
            fig_reg2.add_trace(go.Scatter(
                x=x_line2, y=y_line2, mode='lines',
                line=dict(color="#e74c3c", dash="dash", width=2),
                name=f"Fit (R²={model2['r_squared']:.3f})"))
            fig_reg2.update_layout(
                title=f"Porosity → Flow Efficiency (R²={model2['r_squared']:.3f})",
                xaxis_title="Porosity", yaxis_title="Flow Efficiency Score",
                height=320, plot_bgcolor="white")
        st.plotly_chart(fig_reg2, use_container_width=True)

    for name, model in report.regression_models.items():
        if model:
            st.markdown(f"""
            <div style="background:#f8f9fa;border-left:3px solid #2e86ab;
                        padding:0.6rem 1rem;border-radius:6px;margin:0.3rem 0;font-size:0.85rem;">
                <code>{model.get('equation','')}</code><br>
                <small>{model.get('interpretation','')}</small>
            </div>""", unsafe_allow_html=True)
