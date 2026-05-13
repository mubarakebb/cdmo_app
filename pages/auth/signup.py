"""
CDMO Studio — Sign Up page  (Folio premium design)
"""

import streamlit as st
from utils.auth import register_user, login_user, is_authenticated, AuthError
from utils.ui import inject_base_styles

# Already logged in → go straight to home
if is_authenticated():
  st.switch_page("app.py")

# ─── Page-specific overrides ──────────────────────────────────────────────────
st.markdown(
    """
    <style>
      [data-testid="stSidebar"]        { display: none !important; }
      [data-testid="collapsedControl"]  { display: none !important; }

      .stApp { background: var(--bg-secondary) !important; }
      .block-container {
        max-width: 100% !important;
        padding: 2rem 1rem !important;
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

      /* ── Card — fills the column (no fixed max-width) ── */
      .auth-card {
        position: relative;
        z-index: 1;
        width: 100%;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        box-shadow: var(--card-shadow-lg);
        padding: 2.6rem 2.5rem 0.5rem;
        margin-bottom: 0;
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
      /* st.page_link styled as footer link */
      .auth-footer-nav [data-testid="stPageLink"] a {
        color: var(--accent-teal) !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        text-decoration: none !important;
      }
      .auth-footer-nav [data-testid="stPageLink"] a:hover { text-decoration: underline !important; }
      .auth-footer-nav { text-align: center; margin-top: 0.5rem; }

      /* Remove "Press Enter to submit form" hint */
      [data-testid="InputInstructions"] { display: none !important; }

      /* Hide ONLY the browser-native password reveal (keeps Streamlit's single toggle) */
      input[type="password"]::-ms-reveal            { display: none !important; }
      input[type="password"]::-ms-clear             { display: none !important; }
      input[type="password"]::-webkit-contacts-auto-fill-button { display: none !important; }
      input[type="password"]::-webkit-credentials-auto-fill-button { display: none !important; }

      /* Strip the form's own box so it blends into .auth-card */
      [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
      }

      /* Primary submit button */
      [data-testid="stFormSubmitButton"] > button,
      [data-testid="stFormSubmitButton"] > button[kind="primary"] {
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
        width: 100% !important;
      }
      [data-testid="stFormSubmitButton"] > button:hover {
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

# ─── Centred column — card header + form share the same width ─────────────────
_, col, _ = st.columns([1, 6, 1])

with col:
    # Brand header (same column = same width as form)
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
            '<p class="pw-hint">🔒 Minimum 8 characters.</p>',
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
                st.rerun()
            except AuthError as e:
                st.error(str(e))

    st.markdown(
        '<div class="auth-footer">Already have an account?</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="auth-footer-nav">', unsafe_allow_html=True)
    st.page_link("pages/auth/login.py", label="Sign in instead →")
    st.markdown('</div>', unsafe_allow_html=True)
