"""
Shared UI helpers for the CDMO Streamlit app.

Goal: keep styling consistent across `app.py` and all `pages/*.py`.
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


_CSS_BASE = """
<style>
  :root {{
    --cdmo-accent: {accent};
    --cdmo-accent-2: {accent_2};
    --cdmo-border: rgba(15, 23, 42, 0.12);
    --cdmo-text-muted: rgba(15, 23, 42, 0.72);
    --cdmo-surface: rgba(255, 255, 255, 0.92);
    --cdmo-surface-2: rgba(246, 248, 251, 1);
    --cdmo-shadow: 0 10px 28px rgba(2, 6, 23, 0.10);
    --cdmo-shadow-soft: 0 2px 10px rgba(2, 6, 23, 0.06);
    --cdmo-radius-lg: 16px;
    --cdmo-radius-md: 12px;
    --cdmo-radius-sm: 10px;
  }}

  /* Slightly tighter overall layout */
  .block-container {{
    padding-top: 1.25rem;
    padding-bottom: 2.5rem;
  }}

  /* Make sidebar sections feel more "app-like" */
  section[data-testid="stSidebar"] {{
    border-right: 1px solid rgba(15, 23, 42, 0.08);
  }}

  /* Sidebar navigation: make links feel like buttons */
  nav[data-testid="stSidebarNav"] {{
    margin-top: 0.25rem;
  }}

  nav[data-testid="stSidebarNav"] ul {{
    padding-left: 0;
  }}

  nav[data-testid="stSidebarNav"] li {{
    list-style: none;
    margin: 0.25rem 0;
  }}

  nav[data-testid="stSidebarNav"] a {{
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.55rem 0.65rem;
    border-radius: 12px;
    border: 1px solid rgba(15, 23, 42, 0.10);
    background: rgba(255, 255, 255, 0.75);
    box-shadow: 0 1px 8px rgba(2, 6, 23, 0.05);
    color: rgba(15, 23, 42, 0.86);
    text-decoration: none;
    transition: transform 120ms ease, background 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
  }}

  nav[data-testid="stSidebarNav"] a:hover {{
    transform: translateY(-1px);
    background: rgba(246, 248, 251, 1);
    border-color: rgba(46, 134, 171, 0.45);
    box-shadow: 0 8px 18px rgba(2, 6, 23, 0.10);
  }}

  /* Current page */
  nav[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: rgba(46, 134, 171, 0.12);
    border-color: rgba(46, 134, 171, 0.55);
    color: rgba(15, 23, 42, 0.95);
  }}

  /* Tidy up the default "Pages" heading spacing if present */
  nav[data-testid="stSidebarNav"] > div:first-child {{
    margin-bottom: 0.35rem;
  }}

  /* Header component */
  .cdmo-header {{
    background: linear-gradient(135deg, var(--cdmo-accent-2) 0%, var(--cdmo-accent) 70%, rgba(17, 122, 101, 0.96) 120%);
    padding: 1.3rem 1.6rem;
    border-radius: var(--cdmo-radius-lg);
    color: white;
    box-shadow: var(--cdmo-shadow);
    margin: 0 0 1.2rem 0;
    overflow: hidden;
  }}

  .cdmo-header__row {{
    display: flex;
    align-items: center;
    gap: 0.9rem;
  }}

  .cdmo-header__icon {{
    width: 44px;
    height: 44px;
    display: grid;
    place-items: center;
    border-radius: 14px;
    background: rgba(255,255,255,0.14);
    font-size: 1.6rem;
    flex: 0 0 auto;
  }}

  .cdmo-header__title {{
    margin: 0;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.15;
  }}

  .cdmo-header__subtitle {{
    margin: 0.25rem 0 0 0;
    opacity: 0.92;
    font-size: 0.95rem;
    line-height: 1.35;
  }}

  /* Cards / callouts */
  .cdmo-card {{
    background: var(--cdmo-surface);
    border: 1px solid var(--cdmo-border);
    border-radius: var(--cdmo-radius-md);
    padding: 1rem 1.1rem;
    box-shadow: var(--cdmo-shadow-soft);
  }}

  .cdmo-card--soft {{
    background: var(--cdmo-surface-2);
    box-shadow: none;
  }}

  .cdmo-kicker {{
    color: var(--cdmo-text-muted);
    font-size: 0.85rem;
    margin-top: 0.25rem;
  }}

  .cdmo-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    border: 1px solid rgba(255,255,255,0.25);
    background: rgba(255,255,255,0.12);
    color: white;
  }}

  /* Streamlit widgets polish */
  div[data-testid="stMetric"] {{
    background: var(--cdmo-surface);
    border: 1px solid rgba(15, 23, 42, 0.10);
    border-radius: var(--cdmo-radius-sm);
    padding: 0.75rem 0.85rem;
    box-shadow: var(--cdmo-shadow-soft);
  }}

  /* Buttons */
  .stButton > button {{
    border-radius: 10px;
    font-weight: 700;
  }}

  /* Dataframes */
  div[data-testid="stDataFrame"] {{
    border-radius: var(--cdmo-radius-md);
    overflow: hidden;
    border: 1px solid rgba(15, 23, 42, 0.10);
  }}

  /* Small helper classes used in pages */
  .cdmo-muted {{ color: var(--cdmo-text-muted); }}
</style>
"""


def inject_base_styles(*, accent: str = "#2E86AB", accent_2: str = "#1A5276") -> None:
    """Inject global CSS for consistent styling on the current page."""
    st.markdown(_CSS_BASE.format(accent=accent, accent_2=accent_2), unsafe_allow_html=True)


def page_header(spec: HeaderSpec) -> None:
    """Render a consistent page header."""
    inject_base_styles(accent=spec.accent, accent_2=spec.accent_2)
    st.markdown(
        f"""
        <div class="cdmo-header">
          <div class="cdmo-header__row">
            <div class="cdmo-header__icon">{spec.icon}</div>
            <div>
              <h1 class="cdmo-header__title">{spec.title}</h1>
              <p class="cdmo-header__subtitle">{spec.subtitle}</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand(*, title: str = "CDMO Framework", subtitle: str = "Computational Design & Multi‑Objective Optimization") -> None:
    """Optional sidebar top branding block."""
    st.sidebar.markdown(
        f"""
        <div class="cdmo-card cdmo-card--soft" style="padding:0.85rem 0.95rem;margin-bottom:0.8rem;">
          <div style="font-weight:900;color:var(--cdmo-accent-2);letter-spacing:-0.01em;">{title}</div>
          <div class="cdmo-kicker">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def cards_grid(cards: Iterable[tuple[str, str, str]], *, columns: int = 3) -> None:
    """Render a simple grid of icon/title/body cards.

    cards: iterable of (icon, title, body)
    """
    cols = st.columns(columns)
    for i, (icon, title, body) in enumerate(cards):
        with cols[i % columns]:
            st.markdown(
                f"""
                <div class="cdmo-card" style="height:100%;">
                  <div style="font-size:1.7rem;margin-bottom:0.25rem;">{icon}</div>
                  <div style="font-weight:800;margin-bottom:0.35rem;">{title}</div>
                  <div class="cdmo-muted" style="font-size:0.9rem;line-height:1.45;">{body}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

