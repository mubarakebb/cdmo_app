"""
CDMO Studio — Sign In page  (Folio premium design)
"""

import streamlit as st
from utils.auth import login_user, is_authenticated, AuthError
from utils.ui import inject_base_styles

# Already logged in → go straight to home
if is_authenticated():
  st.switch_page("app.py")

# ─── Page-specific overrides ──────────────────────────────────────────────────
st.markdown(
    """
    <style>
      /* Hide sidebar on auth pages */
      [data-testid="stSidebar"]        { display: none !important; }
      [data-testid="collapsedControl"]  { display: none !important; }

      /* Full-screen auth background */
      .stApp { background: var(--bg-secondary) !important; }
      .block-container {
        max-width: 100% !important;
        padding: 2rem 1rem !important;
      }

      /* ── Orb decorations ── */
      .auth-orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(90px);
        pointer-events: none;
        z-index: 0;
      }
      .auth-orb-1 {
        width: 520px; height: 520px;
        background: var(--orb-purple);
        top: -160px; right: -120px;
        animation: cdmo-drift 11s ease-in-out infinite alternate;
      }
      .auth-orb-2 {
        width: 380px; height: 380px;
        background: var(--orb-blue);
        bottom: -100px; left: -100px;
        animation: cdmo-drift 8s ease-in-out infinite alternate-reverse;
      }
      .auth-orb-3 {
        width: 260px; height: 260px;
        background: var(--orb-teal);
        top: 55%; left: 60%;
        animation: cdmo-drift 13s ease-in-out infinite alternate;
      }

      /* ── Unified auth card (wraps brand header + form) ── */
      .auth-card {
        position: relative;
        z-index: 1;
        width: 100%;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        box-shadow: var(--card-shadow-lg);
        padding: 2.6rem 2.4rem 0.5rem;
        margin-bottom: 0;
      }

      /* ── Brand block ── */
      .auth-brand {
        text-align: center;
        margin-bottom: 1.8rem;
      }
      .auth-brand-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 62px; height: 62px;
        border-radius: var(--radius-md);
        background: linear-gradient(135deg, var(--accent), var(--accent-indigo));
        font-size: 1.8rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(46,134,171,0.28);
      }
      .auth-brand-title {
        font-family: var(--font-heading);
        font-size: 1.55rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.025em;
        margin: 0 0 0.25rem;
      }
      .auth-brand-sub {
        font-size: 0.8rem;
        color: var(--text-muted);
        letter-spacing: 0.01em;
      }

      /* ── Section label ── */
      .auth-eyebrow {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 0.35rem;
      }
      .auth-heading {
        font-family: var(--font-heading);
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 1.4rem;
        letter-spacing: -0.015em;
      }

      /* ── Divider ── */
      .auth-divider {
        border: none;
        border-top: 1px solid var(--border);
        margin: 0 0 1.6rem;
      }

      /* ── Footer link ── */
      .auth-footer {
        text-align: center;
        font-size: 0.84rem;
        color: var(--text-muted);
        margin-top: 0.8rem;
        padding: 1rem 0 0.5rem;
        border-top: 1px solid var(--border);
      }
      .auth-footer-inline {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.35rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
        font-size: 0.84rem;
        color: var(--text-muted);
      }
      .auth-footer-inline a {
        color: var(--accent) !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        text-decoration: none !important;
      }
      .auth-footer-inline a:hover { text-decoration: underline !important; }

      /* ── Trust badge strip ── */
      .auth-trust {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 0.25rem;
        font-size: 0.75rem;
        color: var(--text-muted);
      }
      .auth-trust-item { display: flex; align-items: center; gap: 0.35rem; }

      /* ── Streamlit form cleanup inside the card ── */

      /* Remove the "Press Enter to submit form" hint */
      [data-testid="InputInstructions"] { display: none !important; }

      /* Hide ONLY the browser-native password reveal (keeps Streamlit's single toggle) */
      input[type="password"]::-ms-reveal            { display: none !important; }
      input[type="password"]::-ms-clear             { display: none !important; }
      input[type="password"]::-webkit-contacts-auto-fill-button { display: none !important; }
      input[type="password"]::-webkit-credentials-auto-fill-button { display: none !important; }

      /* Strip the form's own card styling so it blends into .auth-card */
      [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
      }

      /* Primary button */
      [data-testid="stFormSubmitButton"] > button,
      [data-testid="stFormSubmitButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-indigo) 100%) !important;
        border: none !important;
        border-radius: var(--radius-pill) !important;
        padding: 0.75rem 1.75rem !important;
        font-family: var(--font-heading) !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        box-shadow: 0 4px 18px rgba(46,134,171,0.32) !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
        width: 100% !important;
      }
      [data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(46,134,171,0.42) !important;
      }
    </style>

    <!-- Background orb decorations -->
    <div class="auth-orb auth-orb-1"></div>
    <div class="auth-orb auth-orb-2"></div>
    <div class="auth-orb auth-orb-3"></div>
    """,
    unsafe_allow_html=True,
)

# ─── Centred column — card header + form share the same width ─────────────────
_, col, _ = st.columns([1, 6, 1])

with col:
    # Brand header (inside same column as form → same width)
    st.markdown(
        """
        <div class="auth-card">
          <div class="auth-brand">
            <div class="auth-brand-icon">🔬</div>
            <div class="auth-brand-title">CDMO Studio</div>
            <div class="auth-brand-sub">Computational Design &amp; Multi-Objective Optimization</div>
          </div>
          <hr class="auth-divider">
          <div class="auth-eyebrow">Welcome back</div>
          <div class="auth-heading">Sign in to your account</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Username",
            placeholder="your-username",
            autocomplete="username",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="••••••••",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button(
            "Sign In →",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            try:
                token = login_user(username, password)
                st.session_state["_cdmo_user"]  = username.strip().lower()
                st.session_state["_cdmo_token"] = token
                st.success("Signed in! Redirecting…")
                st.rerun()
            except AuthError as e:
                st.error(str(e))

    st.markdown(
        """
        <div class="auth-footer-inline">
          <span>Don't have an account?</span>
          <a href="/auth/signup" target="_self">Create one free →</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="auth-trust">
          <div class="auth-trust-item">🔒 Secure login</div>
          <div class="auth-trust-item">🎓 Research-grade</div>
          <div class="auth-trust-item">⚡ Instant access</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
