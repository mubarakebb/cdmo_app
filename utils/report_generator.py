"""
PDF Report Generator
Produces automated thesis-quality PDF reports from CDMO analysis results.
Includes summary statistics, rankings, Pareto findings, and all charts.
"""

import io
import os
import sys
import tempfile
from datetime import datetime
from typing import List, Dict

import numpy as np
from fpdf import FPDF
import plotly.graph_objects as go
import plotly.express as px

def _safe(text: str) -> str:
    """Strip non-latin-1 chars so fpdf2 core fonts never error."""
    return text.encode('latin-1', errors='replace').decode('latin-1')


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class CDMOReport(FPDF):
    """Custom FPDF subclass with CDMO styling."""

    def normalize_text(self, text):
        if isinstance(text, str):
            text = text.encode('latin-1', errors='replace').decode('latin-1')
        return super().normalize_text(text)

    
    TITLE_COLOR = (26, 82, 118)    # #1a5276
    ACCENT_COLOR = (46, 134, 171)  # #2e86ab
    TEXT_COLOR = (33, 33, 33)
    LIGHT_GRAY = (245, 245, 245)
    MID_GRAY = (180, 180, 180)
    
    def header(self):
        self.set_fill_color(*self.TITLE_COLOR)
        self.rect(0, 0, 210, 14, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 9)
        self.set_xy(10, 4)
        self.cell(0, 6, "CDMO Framework - Biofilm Carrier Analysis Report", ln=False)
        self.set_xy(-40, 4)
        self.cell(30, 6, f"Page {self.page_no()}", align="R")
        self.set_text_color(*self.TEXT_COLOR)
        self.ln(16)
    
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*self.MID_GRAY)
        self.cell(0, 5,
            "University of Ibadan · Mechanical Engineering · PhD Research · "
            "Computational Design and Multi-Objective Optimization of "
            "3D Printed Biofilm Carriers", align="C")
    
    def chapter_title(self, title: str):
        self.set_fill_color(*self.ACCENT_COLOR)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 9, f"  {title}", ln=True, fill=True)
        self.set_text_color(*self.TEXT_COLOR)
        self.ln(3)
    
    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.TITLE_COLOR)
        self.cell(0, 7, title, ln=True)
        self.set_draw_color(*self.ACCENT_COLOR)
        self.set_line_width(0.4)
        x = self.get_x()
        y = self.get_y()
        self.line(x, y, x + 190, y)
        self.set_text_color(*self.TEXT_COLOR)
        self.ln(3)
    
    def body_text(self, text: str, indent: float = 0):
        self.set_font("Helvetica", "", 9)
        self.set_x(10 + indent)
        self.multi_cell(190 - indent, 5, text)
        self.ln(1)
    
    def metric_box(self, label: str, value: str, x: float, y: float, w: float = 44):
        self.set_fill_color(*self.LIGHT_GRAY)
        self.set_draw_color(*self.MID_GRAY)
        self.rect(x, y, w, 14, 'FD')
        self.set_xy(x + 2, y + 1)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(100, 100, 100)
        self.cell(w - 4, 5, label)
        self.set_xy(x + 2, y + 6)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.TITLE_COLOR)
        self.cell(w - 4, 7, str(value))
        self.set_text_color(*self.TEXT_COLOR)
    
    def data_table(self, headers: List[str], rows: List[List[str]],
                   col_widths: List[float] = None):
        if col_widths is None:
            w = 190 / len(headers)
            col_widths = [w] * len(headers)
        
        # Header row
        self.set_fill_color(*self.TITLE_COLOR)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 8)
        for h, w in zip(headers, col_widths):
            self.cell(w, 7, str(h)[:18], border=0, fill=True, align="C")
        self.ln()
        
        # Data rows
        self.set_text_color(*self.TEXT_COLOR)
        for i, row in enumerate(rows):
            fill = i % 2 == 0
            self.set_fill_color(248, 248, 252) if fill else self.set_fill_color(255, 255, 255)
            self.set_font("Helvetica", "", 7.5)
            for val, w in zip(row, col_widths):
                self.cell(w, 6, str(val)[:20], border=0, fill=fill, align="C")
            self.ln()
        self.ln(2)


def _save_plotly_as_image(fig, width: int = 750, height: int = 380) -> str:
    """Save a Plotly figure as a temporary PNG file. Returns file path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    fig.write_image(tmp.name, width=width, height=height, scale=1.5)
    return tmp.name


def generate_summary_charts(carriers) -> Dict[str, str]:
    """Generate chart images for the PDF. Returns dict of {name: filepath}."""
    charts = {}
    
    if not carriers:
        return charts
    
    # 1. Radar chart   top 5 designs
    top5 = carriers[:min(5, len(carriers))]
    categories = ["SA/V", "Porosity", "Flow", "Buoyancy", "Biofilm", "Mech"]
    colors = ["#1a5276", "#2e86ab", "#27ae60", "#e67e22", "#8e44ad"]
    
    fig_radar = go.Figure()
    for i, c in enumerate(top5):
        vals = [c.score_sav, c.score_porosity, c.score_flow,
                c.score_buoyancy, c.score_biofilm_affinity, c.score_mechanical]
        vals += [vals[0]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=categories + [categories[0]],
            fill='toself', opacity=0.35, name=f"{c.filename.replace('.stl','')}×{c.material}",
            line_color=colors[i % len(colors)]))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(range=[0, 1])),
        showlegend=True, height=380,
        title="Multi-Objective Profile - Top 5 Designs",
        paper_bgcolor="white")
    charts["radar"] = _save_plotly_as_image(fig_radar)
    
    # 2. Bar chart   composite scores
    df_bar = sorted(carriers, key=lambda c: c.composite_score, reverse=True)[:16]
    mat_colors = {"PLA": "#4CAF50", "ABS": "#2196F3", "PETG": "#FF9800", "PP": "#9C27B0"}
    
    fig_bar = go.Figure()
    for mat in ["PLA", "ABS", "PETG", "PP"]:
        mat_carriers = [c for c in df_bar if c.material == mat]
        if mat_carriers:
            fig_bar.add_trace(go.Bar(
                x=[f"{c.filename.replace('.stl','')}".replace("Body","B") for c in mat_carriers],
                y=[c.composite_score for c in mat_carriers],
                name=mat, marker_color=mat_colors[mat]))
    fig_bar.update_layout(
        barmode="group", height=360,
        title="Composite Performance Scores by Design and Material",
        xaxis_title="Carrier Design", yaxis_title="Composite Score",
        yaxis=dict(range=[0, 1]),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.3))
    fig_bar.update_xaxes(tickangle=-40, tickfont=dict(size=8))
    charts["bar"] = _save_plotly_as_image(fig_bar, height=400)
    
    # 3. Pareto scatter   SA/V vs Flow Efficiency
    pareto = [c for c in carriers if c.is_pareto_optimal]
    dominated = [c for c in carriers if not c.is_pareto_optimal]
    
    fig_pareto = go.Figure()
    for mat in ["PLA", "ABS", "PETG", "PP"]:
        d_pts = [c for c in dominated if c.material == mat]
        p_pts = [c for c in pareto if c.material == mat]
        if d_pts:
            fig_pareto.add_trace(go.Scatter(
                x=[c.sav_ratio for c in d_pts],
                y=[c.flow_efficiency for c in d_pts],
                mode='markers', marker=dict(size=7, color=mat_colors[mat], opacity=0.35),
                name=f"{mat} (dominated)", showlegend=True))
        if p_pts:
            fig_pareto.add_trace(go.Scatter(
                x=[c.sav_ratio for c in p_pts],
                y=[c.flow_efficiency for c in p_pts],
                mode='markers', marker=dict(size=13, color=mat_colors[mat],
                symbol='star', line=dict(width=1.5, color='white')),
                name=f"{mat} (Pareto * )", showlegend=True))
    fig_pareto.update_layout(
        title="Pareto Frontier: SA/V Ratio vs Flow Efficiency",
        xaxis_title="SA/V Ratio (mm-1)", yaxis_title="Flow Efficiency Score",
        height=360, plot_bgcolor="white", paper_bgcolor="white")
    charts["pareto"] = _save_plotly_as_image(fig_pareto)
    
    # 4. Material box plot
    import pandas as pd
    df_box = pd.DataFrame({
        "Material": [c.material for c in carriers],
        "Composite Score": [c.composite_score for c in carriers]
    })
    fig_box = px.box(df_box, x="Material", y="Composite Score",
                     color="Material", color_discrete_map=mat_colors,
                     title="Composite Score Distribution by Material")
    fig_box.update_layout(
        height=340, showlegend=False, plot_bgcolor="white",
        paper_bgcolor="white", yaxis=dict(range=[0, 1]))
    charts["boxplot"] = _save_plotly_as_image(fig_box, height=340)
    
    return charts


def generate_pdf_report(
    carriers,
    results: List[Dict],
    stat_report,
    analysis_params: Dict,
    output_path: str = None
) -> str:
    """
    Generate a full PDF analysis report.
    Returns path to generated PDF file.
    """
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf",
                                          prefix="cdmo_report_")
        output_path = tmp.name
        tmp.close()
    
    pdf = CDMOReport(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(10, 18, 10)
    
    # ── Cover Page ──────────────────────────────────────────────────────────
    pdf.add_page()
    
    pdf.set_fill_color(*pdf.TITLE_COLOR)
    pdf.rect(0, 14, 210, 80, 'F')
    
    pdf.set_xy(15, 28)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(180, 10, "CDMO Framework\nAnalysis Report", align="C")
    
    pdf.set_xy(15, 68)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(180, 6,
        "Computational Design and Multi-Objective Optimization\n"
        "of 3D Printed Biofilm Carriers for Faecal Sludge Treatment", align="C")
    
    pdf.set_xy(15, 100)
    pdf.set_text_color(*pdf.TEXT_COLOR)
    pdf.set_font("Helvetica", "", 10)
    
    n_geo = len(set(c.filename for c in carriers))
    n_mats = len(set(c.material for c in carriers))
    n_pareto = len([c for c in carriers if c.is_pareto_optimal])
    
    meta_lines = [
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        f"Geometries Evaluated: {n_geo}",
        f"Materials Evaluated: {n_mats} (PLA, ABS, PETG, PP)",
        f"Total Design-Material Combinations: {len(carriers)}",
        f"Pareto-Optimal Designs Identified: {n_pareto}",
        "",
        "University of Ibadan · Mechanical Engineering Department",
        "PhD Research · Majolagbe Yusuf Oladimeji",
    ]
    for line in meta_lines:
        pdf.cell(0, 6, line, ln=True)
    
    # Summary KPI boxes
    pdf.set_xy(10, 168)
    kpis = [
        ("Designs", str(n_geo)),
        ("Materials", str(n_mats)),
        ("Combinations", str(len(carriers))),
        ("Pareto Optimal", str(n_pareto)),
    ]
    if carriers:
        best = min(carriers, key=lambda c: c.rank)
        kpis.append(("Best Score", f"{best.composite_score:.3f}"))
    
    for i, (label, val) in enumerate(kpis[:4]):
        pdf.metric_box(label, val, 10 + i * 48, 168)
    
    # ── Page 2: Executive Summary ────────────────────────────────────────────
    pdf.add_page()
    pdf.chapter_title("1. Executive Summary")
    
    if stat_report and stat_report.key_findings:
        pdf.section_title("Key Findings")
        for finding in stat_report.key_findings:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_x(14)
            pdf.cell(5, 5, "-")
            pdf.set_x(18)
            pdf.multi_cell(182, 5, finding)
            pdf.ln(1)
    
    pdf.ln(3)
    pdf.section_title("Analysis Parameters")
    params_text = (
        f"Fluid: {analysis_params.get('fluid_type', 'Faecal Sludge Medium')} | "
        f"Density: {analysis_params.get('fluid_density', 1015):.0f} kg/m³ | "
        f"Viscosity: {analysis_params.get('fluid_viscosity', 0.003):.4f} Pa·s | "
        f"Flow Velocity: {analysis_params.get('flow_velocity', 0.01):.3f} m/s"
    )
    pdf.body_text(params_text)
    
    weights = analysis_params.get("weights", {})
    if weights:
        w_text = " | ".join([f"{k}: {v:.0%}" for k, v in weights.items()])
        pdf.body_text(f"Objective Weights   {w_text}")
    
    # ── Page 3: Performance Rankings ────────────────────────────────────────
    pdf.add_page()
    pdf.chapter_title("2. Performance Rankings")
    pdf.section_title("Top 20 Design-Material Combinations (by Composite Score)")
    
    top20 = sorted(carriers, key=lambda c: c.rank)[:20]
    headers = ["Rank", "Design", "Material", "Composite", "SA/V", "Porosity", "Flow", "Pareto"]
    rows = []
    for c in top20:
        rows.append([
            str(c.rank),
            c.filename.replace(".stl", "")[:14],
            c.material,
            f"{c.composite_score:.3f}",
            f"{c.sav_ratio:.3f}",
            f"{c.porosity:.3f}",
            f"{c.flow_efficiency:.3f}",
            "*" if c.is_pareto_optimal else "",
        ])
    pdf.data_table(headers, rows, col_widths=[12, 38, 18, 22, 18, 18, 18, 16])
    
    # Pareto optimal table
    pareto_carriers = [c for c in carriers if c.is_pareto_optimal]
    if pareto_carriers:
        pdf.ln(3)
        pdf.section_title(f"Pareto-Optimal Designs ({len(pareto_carriers)} identified)")
        p_headers = ["Design", "Material", "Composite", "SA/V (mm-1)", "Porosity", "Flow Eff."]
        p_rows = [[
            c.filename.replace(".stl", "")[:16],
            c.material,
            f"{c.composite_score:.4f}",
            f"{c.sav_ratio:.4f}",
            f"{c.porosity:.4f}",
            f"{c.flow_efficiency:.4f}",
        ] for c in sorted(pareto_carriers, key=lambda c: c.composite_score, reverse=True)]
        pdf.data_table(p_headers, p_rows, col_widths=[42, 20, 28, 30, 28, 28])
    
    # ── Page 4: Charts ───────────────────────────────────────────────────────
    pdf.add_page()
    pdf.chapter_title("3. Performance Visualisations")
    
    chart_paths = {}
    try:
        chart_paths = generate_summary_charts(carriers)
    except Exception as e:
        pdf.body_text(f"Chart generation note: {str(e)[:100]}")
    
    if "bar" in chart_paths:
        pdf.section_title("Composite Score Rankings")
        pdf.image(chart_paths["bar"], x=10, w=190)
        pdf.ln(3)
    
    if "radar" in chart_paths:
        pdf.section_title("Multi-Objective Radar Profile - Top 5 Designs")
        pdf.image(chart_paths["radar"], x=10, w=190)
    
    # ── Page 5: Pareto & Statistical ────────────────────────────────────────
    pdf.add_page()
    pdf.chapter_title("4. Pareto Frontier Analysis")
    
    if "pareto" in chart_paths:
        pdf.image(chart_paths["pareto"], x=10, w=130)
    
    if "boxplot" in chart_paths:
        pdf.set_xy(148, pdf.get_y() - (340 * 130 / 750 * 0.7) if "pareto" in chart_paths else pdf.get_y())
        # Place boxplot beside pareto if possible
        pdf.image(chart_paths["boxplot"], x=145, w=60)
    
    # ── Page 6: Statistical Analysis ────────────────────────────────────────
    if stat_report:
        pdf.add_page()
        pdf.chapter_title("5. Statistical Analysis")
        
        if stat_report.anova_results:
            pdf.section_title("Group Comparison Tests (Material Effect)")
            a_headers = ["Metric", "Test", "Statistic", "p-value", "Significant", "Effect"]
            a_rows = []
            for metric, result in stat_report.anova_results.items():
                a_rows.append([
                    metric[:20],
                    result.test_name[:18],
                    f"{result.statistic:.3f}",
                    f"{result.p_value:.4f}",
                    "Yes ***" if result.significant else "No",
                    result.effect_magnitude,
                ])
            pdf.data_table(a_headers, a_rows, col_widths=[38, 42, 22, 22, 24, 22])
        
        if stat_report.correlations:
            pdf.ln(3)
            pdf.section_title("Correlation Analysis (Top 8)")
            c_headers = ["Variable 1", "Variable 2", "Pearson r", "p-value", "Strength"]
            c_rows = [[
                r.var1[:18], r.var2[:18],
                f"{r.pearson_r:.3f}", f"{r.pearson_p:.4f}",
                f"{r.strength} {r.direction}"
            ] for r in stat_report.correlations[:8]]
            pdf.data_table(c_headers, c_rows, col_widths=[44, 44, 26, 26, 36])
        
        if stat_report.regression_models:
            pdf.ln(3)
            pdf.section_title("Regression Models")
            for name, model in stat_report.regression_models.items():
                if model:
                    pdf.set_font("Helvetica", "B", 9)
                    pdf.cell(0, 5, model.get("equation", ""), ln=True)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_x(14)
                    pdf.multi_cell(186, 4.5, model.get("interpretation", ""))
                    pdf.ln(2)
    
    # ── Page 7: Geometry Details ─────────────────────────────────────────────
    pdf.add_page()
    pdf.chapter_title("6. Geometric Performance Summary")
    
    geo_seen = set()
    geo_rows = []
    for r in results:
        geo = r.get("geo")
        fname = r.get("filename", "")
        if fname not in geo_seen and geo:
            geo_seen.add(fname)
            geo_rows.append([
                fname.replace(".stl", "")[:16],
                f"{geo.surface_area:,.0f}",
                f"{geo.volume:,.0f}",
                f"{geo.sav_ratio:.4f}",
                f"{geo.porosity:.4f}",
                f"{geo.specific_surface_area:.1f}",
                f"{geo.hydraulic_diameter:.2f}",
                "Yes" if geo.is_watertight else "No",
            ])
    
    if geo_rows:
        g_headers = ["Design", "SA (mm²)", "Vol (mm³)", "SA/V", "Porosity", "Spec SA", "Dh (mm)", "Water."]
        pdf.data_table(g_headers, geo_rows,
                       col_widths=[34, 24, 24, 20, 20, 24, 22, 18])
    
    # ── Cleanup chart temp files ──────────────────────────────────────────────
    for path in chart_paths.values():
        try:
            os.unlink(path)
        except Exception:
            pass
    
    pdf.output(output_path)
    return output_path
