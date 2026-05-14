"""
CDMO App Entrypoint

Uses Streamlit's `st.navigation` + `st.Page` to define sidebar labels/icons.

NOTE: Auth gate is currently DISABLED — uncomment the block below to re-enable
sign-in / sign-up enforcement.
"""

import streamlit as st
from utils.ui import inject_base_styles
from utils.auth import is_authenticated, get_current_user

st.set_page_config(page_title="CDMO Studio", page_icon="🔬", layout="wide")
inject_base_styles()

# ─── Auth gate (disabled) ─────────────────────────────────────────────────────
# Uncomment this block to require login before accessing the app.
#
# auth_pages = [
#     st.Page("pages/auth/login.py",  title="Sign In",  icon="🔑"),
#     st.Page("pages/auth/signup.py", title="Sign Up",  icon="📝"),
# ]
# if not is_authenticated():
#     nav = st.navigation(auth_pages, position="hidden")
#     nav.run()
#     st.stop()

# ─── Main navigation ──────────────────────────────────────────────────────────
pages = [
    st.Page("home.py",                          title="Home",                 icon="🏠"),
    st.Page("pages/1_Upload_Analyse.py",         title="Upload & Analyse",     icon="📤"),
    st.Page("pages/2_Sensitivity_Analysis.py",   title="Sensitivity Analysis", icon="📈"),
    st.Page("pages/3_STL_Generator.py",          title="STL Generator",        icon="🖨️"),
    st.Page("pages/4_Design_Comparison.py",      title="Design Comparison",    icon="🗺️"),
    st.Page("pages/5_Session_Manager.py",        title="Session Manager",      icon="💾"),
    st.Page("pages/6_GA_Optimiser.py",           title="GA Optimiser",         icon="🧬"),
    st.Page("pages/7_Statistical_Analysis.py",   title="Statistical Analysis", icon="📊"),
    st.Page("pages/8_PDF_Report.py",             title="PDF Report",           icon="📄"),
]

nav = st.navigation(pages, position="sidebar")
nav.run()
