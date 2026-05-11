"""
CDMO Studio — Sign Up page  (Folio premium design)
"""

import streamlit as st
from utils.auth import register_user, login_user, is_authenticated, AuthError
from utils.ui import inject_base_styles

st.set_page_config(
    page_title="Sign Up — CDMO Studio",
    page_icon="🔬",
    layout="centered",
)

inject_base_styles()

# Already logged in → go straight to home
if is_authenticated():
    st.switch_page("home.py")

# ─── Page-specific overrides ──────────────────────────────────────────────────
st.markdown(
    """
    <style>
      [data-testid="stSidebar"]        { display: none !important; }
      [data-testid="collapsedControl"]  { display: none !important; }

      .stApp { background: var(--bg-secondary) !important; }
      .block-container {
        max-width: 100% !important;
        padding: 0 !important;
      }

      /* ── Orbs ── */
      .auth-orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(90px);
        pointer-events: none;
        z-index: 0;
      }
      .auth-orb-1 {
        width: 500px; height: 500px;
        background: var(--orb-teal);
        top: -140px; left: -120px;
        animation: cdmo-drift 10s ease-in-out infinite alternate;
      }
      .auth-orb-2 {
        width: 420px; height: 420px;
        background: var(--orb-purple);
        bottom: -120px; right: -100px;
        animation: cdmo-drift 9s ease-in-out infinite alternate-reverse;
      }
      .auth-orb-3 {
        width: 240px; height: 240px;
        background: var(--orb-orange);
        top: 40%; right: 15%;
        animation: cdmo-drift 14s ease-in-out infinite alternate;
      }

      /* ── Card ── */
      .auth-card {
        position: relative;
        z-index: 1;
        width: 100%;
        max-width: 480px;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        box-shadow: var(--card-shadow-lg);
        padding: 2.6rem 2.5rem 2.2rem;
        margin: 0 auto;
      }

      /* ── Brand ── */
      .auth-brand {
        text-align: center;
        margin-bottom: 1.8rem;
      }
      .auth-brand-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 58px; height: 58px;
        border-radius: var(--radius-md);
        background: linear-gradient(135deg, var(--accent-teal), var(--accent-indigo));
        font-size: 1.7rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 8px 24px rgba(20,184,166,0.28);
      }
      .auth-brand-title {
        font-family: var(--font-heading);
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.025em;
        margin: 0 0 0.25rem;
      }
      .auth-brand-sub {
        font-size: 0.79rem;
        color: var(--text-muted);
      }

      .auth-eyebrow {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--accent-teal);
        margin-bottom: 0.35rem;
      }
      .auth-heading {
        font-family: var(--font-heading);
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 1.5rem;
        letter-spacing: -0.015em;
      }

      .auth-divider {
        border: none;
        border-top: 1px solid var(--border);
        margin: 0 0 1.6rem;
      }

      /* ── Password hint ── */
      .pw-hint {
        font-size: 0.76rem;
        color: var(--text-muted);
        margin-top: -0.5rem;
        margin-bottom: 0.5rem;
        line-height: 1.5;
        padding-left: 0.2rem;
      }

      /* ── Benefit pills ── */
      .auth-benefits {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1.4rem;
      }
      .auth-benefit-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.3rem 0.75rem;
        border-radius: var(--radius-pill);
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        font-size: 0.76rem;
        color: var(--text-secondary);
        font-weight: 500;
      }

      .auth-footer {
        text-align: center;
        font-size: 0.84rem;
        color: var(--text-muted);
        margin-top: 1.3rem;
        padding-top: 1.2rem;
        border-top: 1px solid var(--border);
      }
      .auth-footer a {
        color: var(--accent-teal);
        text-decoration: none;
        font-weight: 600;
      }
      .auth-footer a:hover { text-decoration: underline; }

      /* Primary button */
      .auth-card .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-teal) 0%, var(--accent-indigo) 100%) !important;
        border: none !important;
        border-radius: var(--radius-pill) !important;
        padding: 0.75rem 1.75rem !important;
        font-family: var(--font-heading) !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        box-shadow: 0 4px 18px rgba(20,184,166,0.32) !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
      }
      .auth-card .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(20,184,166,0.42) !important;
      }
    </style>

    <div class="auth-orb auth-orb-1"></div>
    <div class="auth-orb auth-orb-2"></div>
    <div class="auth-orb auth-orb-3"></div>
    """,
    unsafe_allow_html=True,
)

# ─── Card header ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-brand-icon">🔬</div>
        <div class="auth-brand-title">CDMO Studio</div>
        <div class="auth-brand-sub">Computational Design &amp; Multi-Objective Optimization</div>
      </div>
      <hr class="auth-divider">
      <div class="auth-eyebrow">Get started for free</div>
      <div class="auth-heading">Create your account</div>
      <div class="auth-benefits">
        <span class="auth-benefit-pill">🧬 NSGA-II Optimiser</span>
        <span class="auth-benefit-pill">📊 Statistical Analysis</span>
        <span class="auth-benefit-pill">🖨️ STL Generator</span>
        <span class="auth-benefit-pill">📄 PDF Reports</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Form ─────────────────────────────────────────────────────────────────────
_, col, _ = st.columns([1, 8, 1])

with col:
    with st.form("signup_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input(
                "Full Name",
                placeholder="e.g. Yusuf Majolagbe",
                autocomplete="name",
            )
        with c2:
            email = st.text_input(
                "Email Address",
                placeholder="you@example.com",
                autocomplete="email",
            )
        username = st.text_input(
            "Username",
            placeholder="letters, numbers, _ or - (min 3 chars)",
            autocomplete="username",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="At least 8 characters",
            autocomplete="new-password",
        )
        st.markdown(
            '<p class="pw-hint">🔒 Minimum 8 characters — stored with PBKDF2-SHA256 hashing.</p>',
            unsafe_allow_html=True,
        )
        confirm = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Repeat your password",
            autocomplete="new-password",
        )

        submitted = st.form_submit_button(
            "Create Account →",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        errors = []
        if not username:
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        elif password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                register_user(
                    username=username,
                    password=password,
                    email=email,
                    full_name=full_name,
                )
                token = login_user(username, password)
                st.session_state["_cdmo_user"]  = username.strip().lower()
                st.session_state["_cdmo_token"] = token
                st.success(f"Account created! Welcome, {full_name or username}. Redirecting…")
                st.switch_page("home.py")
            except AuthError as e:
                st.error(str(e))

    st.markdown(
        """
        <div class="auth-footer">
          Already have an account?&nbsp;
          <a href="/auth/login" target="_self">Sign in instead →</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
