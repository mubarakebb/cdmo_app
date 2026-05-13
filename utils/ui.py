"""
Shared UI helpers for the CDMO Streamlit app.
Folio-theme design system — premium, agency-quality aesthetic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import streamlit as st


@dataclass(frozen=True)
class HeaderSpec:
    icon: str
    title: str
    subtitle: str
    accent: str = "#2E86AB"
    accent_2: str = "#1A5276"


# ─── Core CSS (Folio design system) ──────────────────────────────────────────

_CSS_FOLIO = """
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,400&display=swap" rel="stylesheet">

<style>
/* ── Design tokens ─────────────────────────────────────── */
:root {{
  --bg-primary:      #ffffff;
  --bg-secondary:    #f8f9fb;
  --bg-card:         #ffffff;
  --bg-card-hover:   #f3f6fa;
  --text-primary:    #0d0f1a;
  --text-secondary:  #4b5168;
  --text-muted:      #8b90a7;

  --accent:          {accent};
  --accent-2:        {accent_2};
  --accent-orange:   #f97316;
  --accent-indigo:   #6366f1;
  --accent-teal:     #14b8a6;

  --border:          #e8eaf0;
  --card-shadow:     0 4px 24px rgba(0,0,0,0.07);
  --card-shadow-lg:  0 12px 40px rgba(0,0,0,0.11);

  --orb-purple: rgba(139,92,246,0.14);
  --orb-blue:   rgba(46,134,171,0.12);
  --orb-teal:   rgba(20,184,166,0.10);
  --orb-orange: rgba(249,115,22,0.08);

  --font-heading: 'Sora', 'Plus Jakarta Sans', system-ui, sans-serif;
  --font-body:    'DM Sans', 'Nunito', system-ui, sans-serif;

  --radius-sm:   8px;
  --radius-md:   14px;
  --radius-lg:   20px;
  --radius-xl:   28px;
  --radius-pill: 999px;
}}

/* Dark mode token overrides */
[data-theme="dark"] {{
  --bg-primary:    #0a0b14;
  --bg-secondary:  #10121f;
  --bg-card:       #141626;
  --bg-card-hover: #1a1d30;
  --text-primary:  #f0f1fa;
  --text-secondary:#9499b8;
  --text-muted:    #565b78;
  --border:        #1e2035;
  --card-shadow:   0 4px 24px rgba(0,0,0,0.35);
}}

/* ── Typography ───────────────────────────────────────── */
html, body, .stApp, .stApp *,
[data-testid="stSidebar"], [data-testid="stSidebar"] * {{
  font-family: var(--font-body) !important;
  -webkit-font-smoothing: antialiased;
}}

/* Restore Material Symbols font — the broad rule above strips it,
   which causes icon ligatures to render as raw text (e.g. "keyboard_double_arrow_left") */
[class*="material-symbols"],
[data-testid="stSidebarCollapseButton"] button span,
[data-testid="collapsedControl"] span,
[data-baseweb="icon"] span,
span[data-testid="stIconMaterial"] {{
  font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
  font-feature-settings: 'liga' 1 !important;
  -webkit-font-feature-settings: 'liga' 1 !important;
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24 !important;
}}

h1, h2, h3, h4,
.cdmo-h1, .cdmo-h2, .cdmo-h3 {{
  font-family: var(--font-heading) !important;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  line-height: 1.2;
}}

/* ── App shell ────────────────────────────────────────── */
.stApp {{
  background: var(--bg-primary) !important;
}}

.block-container {{
  padding-top: 1.75rem !important;
  padding-bottom: 3.5rem !important;
  max-width: 1240px !important;
}}

/* Top deploy/header bar — minimal */
[data-testid="stHeader"] {{
  background: transparent !important;
  border-bottom: none !important;
}}

/* ── Sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"] {{
  background: var(--bg-secondary) !important;
  border-right: 1px solid var(--border) !important;
}}

[data-testid="stSidebarContent"] {{
  padding-top: 0.5rem !important;
}}

/* Sidebar navigation links */
[data-testid="stSidebarNav"] ul {{
  padding: 0 !important;
  margin: 0 !important;
}}

[data-testid="stSidebarNav"] li {{
  list-style: none !important;
  margin: 0.2rem 0.5rem !important;
}}

[data-testid="stSidebarNav"] a {{
  display: flex !important;
  align-items: center !important;
  gap: 0.6rem !important;
  padding: 0.6rem 0.85rem !important;
  border-radius: var(--radius-md) !important;
  border: 1px solid transparent !important;
  color: var(--text-secondary) !important;
  text-decoration: none !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  transition: all 0.18s ease !important;
  background: transparent !important;
}}

[data-testid="stSidebarNav"] a:hover {{
  background: var(--bg-card) !important;
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
  transform: translateX(2px) !important;
  box-shadow: var(--card-shadow) !important;
}}

[data-testid="stSidebarNav"] a[aria-current="page"] {{
  background: linear-gradient(135deg,
    rgba(46,134,171,0.12),
    rgba(26,82,118,0.08)) !important;
  border-color: rgba(46,134,171,0.30) !important;
  color: var(--accent) !important;
  font-weight: 600 !important;
}}

/* Sidebar section headers */
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {{
  font-size: 0.72rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.10em !important;
  text-transform: uppercase !important;
  color: var(--text-muted) !important;
  margin: 1.1rem 0 0.4rem !important;
  padding: 0 0.5rem !important;
}}

/* ── Buttons ──────────────────────────────────────────── */
.stButton > button {{
  font-family: var(--font-body) !important;
  font-weight: 600 !important;
  border-radius: var(--radius-pill) !important;
  border: 1.5px solid var(--border) !important;
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
  transition: all 0.2s ease !important;
  padding: 0.55rem 1.4rem !important;
  font-size: 0.875rem !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}}

.stButton > button:hover {{
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  box-shadow: 0 4px 14px rgba(46,134,171,0.18) !important;
  transform: translateY(-1px) !important;
}}

.stButton > button[kind="primary"] {{
  background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
  color: #fff !important;
  border-color: transparent !important;
  box-shadow: 0 4px 16px rgba(46,134,171,0.30) !important;
}}

.stButton > button[kind="primary"]:hover {{
  background: linear-gradient(135deg, var(--accent-2), var(--accent)) !important;
  color: #fff !important;
  box-shadow: 0 8px 24px rgba(46,134,171,0.40) !important;
  transform: translateY(-2px) !important;
}}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {{
  width: 100% !important;
  border: 1px solid var(--border) !important;
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
  padding: 0.6rem 1rem !important;
  font-size: 0.875rem !important;
  border-radius: var(--radius-md) !important;
}}

[data-testid="stSidebar"] .stButton > button:hover {{
  background: var(--bg-card-hover) !important;
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}}

/* ── Sidebar collapse / expand buttons ─── */

/* Collapse arrow inside the open sidebar */
[data-testid="stSidebarCollapseButton"] {{
  display: flex !important;
  opacity: 1 !important;
  visibility: visible !important;
}}

[data-testid="stSidebarCollapseButton"] button {{
  background: transparent !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-secondary) !important;
  width: 32px !important;
  height: 32px !important;
  padding: 0 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}}

[data-testid="stSidebarCollapseButton"] button:hover {{
  background: var(--bg-card-hover) !important;
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}}

/* Floating expand pill shown when sidebar is collapsed */
[data-testid="collapsedControl"] {{
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 36px !important;
  height: 36px !important;
  border-radius: var(--radius-md) !important;
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  opacity: 1 !important;
  visibility: visible !important;
}}

[data-testid="collapsedControl"]:hover {{
  background: var(--bg-card-hover) !important;
  border-color: var(--accent) !important;
}}

[data-testid="collapsedControl"] svg {{
  width: 18px !important;
  height: 18px !important;
  color: var(--text-primary) !important;
  stroke: currentColor !important;
  fill: none !important;
}}

/* ── Form inputs ─────────────────────────────────────── */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea {{
  font-family: var(--font-body) !important;
  border-radius: var(--radius-md) !important;
  border: 1.5px solid var(--border) !important;
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
  font-size: 0.9rem !important;
  padding: 0.6rem 1rem !important;
}}

.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {{
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(46,134,171,0.15) !important;
  outline: none !important;
}}

.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stMultiSelect label,
.stSlider label,
.stTextArea label {{
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  color: var(--text-secondary) !important;
  letter-spacing: 0.02em !important;
  margin-bottom: 0.25rem !important;
}}

/* ── Select boxes ────────────────────────────────────── */
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {{
  border-radius: var(--radius-md) !important;
  border: 1.5px solid var(--border) !important;
  background: var(--bg-card) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}}

.stSelectbox [data-baseweb="select"] > div:focus-within,
.stMultiSelect [data-baseweb="select"] > div:focus-within {{
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(46,134,171,0.15) !important;
}}

/* ── Tabs ────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  background: var(--bg-secondary) !important;
  border-radius: var(--radius-pill) !important;
  padding: 4px !important;
  gap: 2px !important;
  border: 1px solid var(--border) !important;
}}

.stTabs [data-baseweb="tab"] {{
  border-radius: var(--radius-pill) !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  color: var(--text-secondary) !important;
  padding: 0.45rem 1.1rem !important;
  transition: all 0.18s ease !important;
  background: transparent !important;
  border: none !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
  color: var(--text-primary) !important;
  background: var(--bg-card) !important;
}}

.stTabs [aria-selected="true"] {{
  background: var(--bg-card) !important;
  color: var(--accent) !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}}

.stTabs [data-baseweb="tab-highlight"] {{
  display: none !important;
}}

.stTabs [data-baseweb="tab-border"] {{
  display: none !important;
}}

/* ── Metrics ──────────────────────────────────────────── */
[data-testid="stMetric"] {{
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 1.1rem 1.3rem !important;
  box-shadow: var(--card-shadow) !important;
  transition: transform 0.2s, box-shadow 0.2s !important;
}}

[data-testid="stMetric"]:hover {{
  transform: translateY(-2px) !important;
  box-shadow: var(--card-shadow-lg) !important;
}}

[data-testid="stMetricLabel"] {{
  font-size: 0.75rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  color: var(--text-muted) !important;
}}

[data-testid="stMetricValue"] {{
  font-family: var(--font-heading) !important;
  font-size: 1.9rem !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  letter-spacing: -0.03em !important;
}}

[data-testid="stMetricDelta"] {{
  font-size: 0.78rem !important;
  font-weight: 600 !important;
}}

/* ── DataFrames ───────────────────────────────────────── */
[data-testid="stDataFrame"] {{
  border-radius: var(--radius-lg) !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
  box-shadow: var(--card-shadow) !important;
}}

/* ── Alert boxes ──────────────────────────────────────── */
[data-testid="stInfo"] {{
  background: linear-gradient(135deg,
    rgba(46,134,171,0.06),
    rgba(99,102,241,0.04)) !important;
  border: 1px solid rgba(46,134,171,0.22) !important;
  border-left: 4px solid var(--accent) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-secondary) !important;
}}

[data-testid="stSuccess"] {{
  background: rgba(20,184,166,0.06) !important;
  border: 1px solid rgba(20,184,166,0.22) !important;
  border-left: 4px solid var(--accent-teal) !important;
  border-radius: var(--radius-md) !important;
}}

[data-testid="stWarning"] {{
  background: rgba(249,115,22,0.06) !important;
  border: 1px solid rgba(249,115,22,0.22) !important;
  border-left: 4px solid var(--accent-orange) !important;
  border-radius: var(--radius-md) !important;
}}

[data-testid="stError"] {{
  background: rgba(239,68,68,0.06) !important;
  border: 1px solid rgba(239,68,68,0.22) !important;
  border-left: 4px solid #ef4444 !important;
  border-radius: var(--radius-md) !important;
}}

/* ── Progress bars ────────────────────────────────────── */
[data-testid="stProgressBar"] > div {{
  height: 6px !important;
  border-radius: var(--radius-pill) !important;
  background: var(--bg-secondary) !important;
}}

[data-testid="stProgressBar"] > div > div {{
  background: linear-gradient(90deg, var(--accent), var(--accent-2)) !important;
  border-radius: var(--radius-pill) !important;
  transition: width 0.4s ease !important;
}}

/* ── Sliders ──────────────────────────────────────────── */
[data-testid="stSlider"] [role="slider"] {{
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(46,134,171,0.20) !important;
}}

[data-testid="stSlider"] [data-testid="stTickBar"] > div {{
  background: linear-gradient(90deg, var(--accent), var(--accent-2)) !important;
}}

/* ── Expanders ────────────────────────────────────────── */
[data-testid="stExpander"] {{
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  background: var(--bg-card) !important;
  box-shadow: var(--card-shadow) !important;
}}

[data-testid="stExpander"] summary {{
  font-weight: 600 !important;
  color: var(--text-primary) !important;
  font-size: 0.9rem !important;
}}

/* ── Dividers ─────────────────────────────────────────── */
hr {{
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.5rem 0 !important;
}}

/* ── File uploader ────────────────────────────────────── */
/* Target the inner dropzone only — styling the outer container
   bleeds into the internal layout and causes text to overlap. */
[data-testid="stFileUploader"] {{
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
}}

[data-testid="stFileUploaderDropzone"] {{
  border: 2px dashed var(--border) !important;
  border-radius: var(--radius-lg) !important;
  background: var(--bg-secondary) !important;
  transition: border-color 0.2s, background 0.2s !important;
  padding: 1.25rem 1rem !important;
}}

[data-testid="stFileUploaderDropzone"]:hover {{
  border-color: var(--accent) !important;
  background: rgba(46,134,171,0.04) !important;
}}

/* Ensure text inside the dropzone is properly stacked */
[data-testid="stFileUploaderDropzone"] > div {{
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  gap: 0.4rem !important;
}}

[data-testid="stFileUploaderDropzone"] small {{
  display: block !important;
  text-align: center !important;
  color: var(--text-muted) !important;
  font-size: 0.82rem !important;
  line-height: 1.4 !important;
}}

/* Scope span styling to non-button spans only — applying display:block to
   ALL spans inside the dropzone forces hidden button label spans to appear,
   which causes the "Browse files / Upload" text to show twice */
[data-testid="stFileUploaderDropzone"] > div > span {{
  display: block !important;
  text-align: center !important;
  color: var(--text-muted) !important;
  font-size: 0.82rem !important;
  line-height: 1.4 !important;
}}
[data-testid="stFileUploaderDropzone"] button span {{
  display: inline !important;
}}

/* ── Checkboxes / Radio ───────────────────────────────── */
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label {{
  font-size: 0.88rem !important;
  color: var(--text-secondary) !important;
}}

/* ── Spinner ──────────────────────────────────────────── */
[data-testid="stSpinner"] {{
  color: var(--accent) !important;
}}

/* ── Download button ──────────────────────────────────── */
[data-testid="stDownloadButton"] > button {{
  background: linear-gradient(135deg,
    rgba(46,134,171,0.10),
    rgba(26,82,118,0.06)) !important;
  border-color: rgba(46,134,171,0.30) !important;
  color: var(--accent) !important;
  font-weight: 600 !important;
}}

[data-testid="stDownloadButton"] > button:hover {{
  background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
  color: #fff !important;
  box-shadow: 0 4px 16px rgba(46,134,171,0.30) !important;
}}

/* ── Custom card components ───────────────────────────── */
.cdmo-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.4rem;
  box-shadow: var(--card-shadow);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}}

.cdmo-card:hover {{
  transform: translateY(-4px);
  box-shadow: var(--card-shadow-lg);
}}

.cdmo-card--accent {{
  border-left: 4px solid var(--accent);
}}

.cdmo-card--orange {{
  border-left: 4px solid var(--accent-orange);
}}

.cdmo-card--teal {{
  border-left: 4px solid var(--accent-teal);
}}

/* Eyebrow label */
.cdmo-eyebrow {{
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent-indigo);
  margin-bottom: 0.5rem;
}}

/* Badge / pill */
.cdmo-badge {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-pill);
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}}

.cdmo-badge--blue {{
  background: rgba(46,134,171,0.10);
  border-color: rgba(46,134,171,0.25);
  color: var(--accent);
}}

.cdmo-badge--orange {{
  background: rgba(249,115,22,0.10);
  border-color: rgba(249,115,22,0.25);
  color: var(--accent-orange);
}}

.cdmo-badge--green {{
  background: rgba(20,184,166,0.10);
  border-color: rgba(20,184,166,0.25);
  color: var(--accent-teal);
}}

/* Metric card (custom, not Streamlit's) */
.cdmo-metric {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.2rem 1.4rem;
  box-shadow: var(--card-shadow);
}}

.cdmo-metric-value {{
  font-family: var(--font-heading);
  font-size: 2rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.04em;
  line-height: 1;
}}

.cdmo-metric-label {{
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-top: 0.4rem;
}}

.cdmo-metric-delta {{
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent-teal);
  margin-top: 0.2rem;
}}

/* Feature icon box */
.cdmo-icon-box {{
  width: 46px;
  height: 46px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg,
    rgba(46,134,171,0.12),
    rgba(99,102,241,0.08));
  border: 1px solid rgba(46,134,171,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  margin-bottom: 1rem;
  flex-shrink: 0;
}}

/* Orb decorations */
.cdmo-orb-wrap {{
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
  border-radius: inherit;
}}

.cdmo-orb {{
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  pointer-events: none;
}}

.cdmo-orb-purple {{
  width: 520px; height: 520px;
  background: var(--orb-purple);
  top: -180px; right: -60px;
  animation: cdmo-drift 12s ease-in-out infinite alternate;
}}

.cdmo-orb-blue {{
  width: 380px; height: 380px;
  background: var(--orb-blue);
  bottom: -120px; left: -60px;
  animation: cdmo-drift 9s ease-in-out infinite alternate-reverse;
}}

.cdmo-orb-teal {{
  width: 260px; height: 260px;
  background: var(--orb-teal);
  top: 40%; right: 20%;
  animation: cdmo-drift 7s ease-in-out infinite alternate;
  animation-delay: -4s;
}}

@keyframes cdmo-drift {{
  from {{ transform: translate(0, 0) scale(1);    }}
  to   {{ transform: translate(28px, -18px) scale(1.06); }}
}}

/* Scroll reveal */
.cdmo-reveal {{
  opacity: 0;
  transform: translateY(22px);
  animation: cdmo-fadeUp 0.65s ease forwards;
}}
.cdmo-reveal-1 {{ animation-delay: 0.05s; }}
.cdmo-reveal-2 {{ animation-delay: 0.15s; }}
.cdmo-reveal-3 {{ animation-delay: 0.25s; }}
.cdmo-reveal-4 {{ animation-delay: 0.35s; }}
.cdmo-reveal-5 {{ animation-delay: 0.45s; }}

@keyframes cdmo-fadeUp {{
  to {{ opacity: 1; transform: none; }}
}}

/* Gradient text */
.cdmo-text-gradient {{
  background: linear-gradient(135deg, var(--accent), var(--accent-indigo));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}

/* Page header */
.cdmo-header {{
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, {accent_2} 0%, {accent} 65%, rgba(99,102,241,0.85) 120%);
  padding: 1.8rem 2rem;
  border-radius: var(--radius-xl);
  margin-bottom: 1.5rem;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}}

.cdmo-header-row {{
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
  z-index: 1;
}}

.cdmo-header-icon {{
  width: 52px; height: 52px;
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.7rem;
  flex-shrink: 0;
  backdrop-filter: blur(8px);
}}

.cdmo-header-title {{
  font-family: var(--font-heading);
  font-size: clamp(1.35rem, 3vw, 1.9rem);
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin: 0;
}}

.cdmo-header-subtitle {{
  font-size: 0.88rem;
  color: rgba(255,255,255,0.82);
  margin: 0.3rem 0 0;
  line-height: 1.4;
}}

.cdmo-header-badge {{
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.7rem;
  border-radius: var(--radius-pill);
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.25);
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 0.55rem;
  width: fit-content;
  backdrop-filter: blur(4px);
}}

/* Stats grid */
.cdmo-stats-grid {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}}

.cdmo-stat {{
  background: var(--bg-card);
  padding: 1.4rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}}

.cdmo-stat-value {{
  font-family: var(--font-heading);
  font-size: 2rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.04em;
  line-height: 1;
}}

.cdmo-stat-label {{
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}}

/* Feature card */
.cdmo-feature-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem 1.6rem;
  box-shadow: var(--card-shadow);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}}

.cdmo-feature-card:hover {{
  transform: translateY(-5px);
  box-shadow: var(--card-shadow-lg);
  border-color: rgba(46,134,171,0.30);
}}

.cdmo-feature-card-title {{
  font-family: var(--font-heading);
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  margin: 0;
}}

.cdmo-feature-card-body {{
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.6;
  flex: 1;
}}

.cdmo-feature-card-link {{
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--accent);
  margin-top: 0.5rem;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}}

/* Explicit text color for feature cards - ensure contrast on all backgrounds */
.cdmo-feature-card {{
  background: #ffffff !important;
  color: #0d0f1a !important;
}}

.cdmo-feature-card-title {{
  color: #0d0f1a !important;
}}

.cdmo-feature-card-body {{
  color: #666d7d !important;
}}

/* Process step */
.cdmo-step {{
  display: flex;
  gap: 1.2rem;
  align-items: flex-start;
  padding: 1rem 0;
}}

.cdmo-step-num {{
  font-family: var(--font-heading);
  font-size: 2rem;
  font-weight: 800;
  color: var(--accent);
  opacity: 0.25;
  letter-spacing: -0.06em;
  line-height: 1;
  flex-shrink: 0;
  min-width: 3rem;
  transition: opacity 0.2s;
}}

.cdmo-step:hover .cdmo-step-num {{
  opacity: 1;
}}

.cdmo-step-title {{
  font-family: var(--font-heading);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.2rem;
}}

.cdmo-step-body {{
  font-size: 0.83rem;
  color: var(--text-secondary);
  line-height: 1.55;
}}

/* Info strip */
.cdmo-strip {{
  background: linear-gradient(135deg,
    rgba(46,134,171,0.07),
    rgba(99,102,241,0.04));
  border: 1px solid rgba(46,134,171,0.18);
  border-radius: var(--radius-lg);
  padding: 1.1rem 1.4rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
}}

/* Sidebar brand card */
.cdmo-brand-card {{
  margin: 0.6rem 0.5rem 0.3rem;
  padding: 0.9rem 1rem;
  background: linear-gradient(135deg, var(--accent-2), var(--accent));
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 16px rgba(46,134,171,0.25);
}}

.cdmo-brand-name {{
  font-family: var(--font-heading);
  font-weight: 800;
  color: #fff;
  font-size: 0.95rem;
  letter-spacing: -0.01em;
}}

.cdmo-brand-sub {{
  font-size: 0.7rem;
  color: rgba(255,255,255,0.72);
  margin-top: 0.15rem;
  line-height: 1.4;
}}

/* User badge in sidebar */
.cdmo-user-badge {{
  margin: 0.5rem;
  padding: 0.6rem 0.85rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: 0.7rem;
  box-shadow: var(--card-shadow);
}}

.cdmo-user-avatar {{
  width: 34px; height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent-indigo));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-family: var(--font-heading);
  font-weight: 800;
  font-size: 0.88rem;
  flex-shrink: 0;
}}

.cdmo-user-name {{
  font-size: 0.83rem;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}

.cdmo-user-handle {{
  font-size: 0.72rem;
  color: var(--text-muted);
}}

/* Empty state */
.cdmo-empty {{
  text-align: center;
  padding: 3.5rem 2rem;
  background: var(--bg-secondary);
  border: 2px dashed var(--border);
  border-radius: var(--radius-xl);
  color: var(--text-muted);
}}

.cdmo-empty-icon {{
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  display: block;
}}

.cdmo-empty-title {{
  font-family: var(--font-heading);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 0.4rem;
}}

.cdmo-empty-body {{
  font-size: 0.87rem;
  color: var(--text-muted);
  max-width: 360px;
  margin: 0 auto;
  line-height: 1.6;
}}
</style>
"""


# ─── Public helpers ───────────────────────────────────────────────────────────

def inject_base_styles(*, accent: str = "#2E86AB", accent_2: str = "#1A5276") -> None:
    """Inject the full Folio-theme CSS into the current page."""
    st.markdown(
        _CSS_FOLIO.format(accent=accent, accent_2=accent_2),
        unsafe_allow_html=True,
    )


def page_header(spec: HeaderSpec) -> None:
    """Render a premium Folio-style page header with orb decoration."""
    inject_base_styles(accent=spec.accent, accent_2=spec.accent_2)
    st.markdown(
        f"""
        <div class="cdmo-header">
          <div class="cdmo-orb-wrap">
            <div class="cdmo-orb cdmo-orb-purple"></div>
            <div class="cdmo-orb cdmo-orb-teal" style="width:220px;height:220px;bottom:-60px;left:30%;"></div>
          </div>
          <div class="cdmo-header-row">
            <div class="cdmo-header-icon">{spec.icon}</div>
            <div>
              <h1 class="cdmo-header-title">{spec.title}</h1>
              <p class="cdmo-header-subtitle">{spec.subtitle}</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand(
    *,
    title: str = "CDMO Studio",
    subtitle: str = "Computational Design & Multi‑Objective Optimization",
) -> None:
    """Sidebar brand block + authenticated user badge + logout."""
    # Brand gradient card
    st.sidebar.markdown(
        f"""
        <div class="cdmo-brand-card">
          <div class="cdmo-brand-name">🔬 {title}</div>
          <div class="cdmo-brand-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # User badge + logout
    try:
        from utils.auth import get_current_user, logout_user, is_authenticated
        if is_authenticated():
            user = get_current_user()
            display  = (user.get("full_name") or user.get("username", "User")) if user else "User"
            username = st.session_state.get("_cdmo_user", "")
            initial  = display[0].upper() if display else "U"

            st.sidebar.markdown(
                f"""
                <div class="cdmo-user-badge">
                  <div class="cdmo-user-avatar">{initial}</div>
                  <div style="min-width:0;">
                    <div class="cdmo-user-name">{display}</div>
                    <div class="cdmo-user-handle">@{username}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.sidebar.button(
                "⏻  Sign Out",
                use_container_width=True,
                key="_cdmo_logout_btn",
            ):
                logout_user(username)
                for key in ("_cdmo_user", "_cdmo_token"):
                    st.session_state.pop(key, None)
                st.switch_page("pages/auth/login.py")
    except Exception:
        pass


def cards_grid(cards: Iterable[tuple[str, str, str]], *, columns: int = 3) -> None:
    """Render a responsive grid of Folio-style feature cards.

    cards: iterable of (icon, title, body)
    """
    cols = st.columns(columns, gap="medium")
    for i, (icon, title, body) in enumerate(cards):
        with cols[i % columns]:
            st.markdown(
                f"""
                <div class="cdmo-feature-card cdmo-reveal cdmo-reveal-{min(i+1, 5)}">
                  <div class="cdmo-icon-box">{icon}</div>
                  <p class="cdmo-feature-card-title">{title}</p>
                  <p class="cdmo-feature-card-body">{body}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def empty_state(
    icon: str = "📂",
    title: str = "Nothing here yet",
    body: str = "Complete the previous step to see results here.",
) -> None:
    """Render a centred empty-state placeholder."""
    st.markdown(
        f"""
        <div class="cdmo-empty">
          <span class="cdmo-empty-icon">{icon}</span>
          <div class="cdmo-empty-title">{title}</div>
          <div class="cdmo-empty-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def eyebrow(text: str) -> None:
    """Render a small Folio-style eyebrow label."""
    st.markdown(
        f'<span class="cdmo-eyebrow">{text}</span>',
        unsafe_allow_html=True,
    )


def badge(text: str, variant: str = "") -> str:
    """Return HTML for an inline badge/pill. variant: '' | 'blue' | 'orange' | 'green'."""
    cls = f"cdmo-badge cdmo-badge--{variant}" if variant else "cdmo-badge"
    return f'<span class="{cls}">{text}</span>'
