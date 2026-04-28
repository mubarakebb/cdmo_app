"""
CDMO App Entrypoint

Uses Streamlit's `st.navigation` + `st.Page` to define sidebar labels/icons.
"""

import streamlit as st
from utils.ui import inject_base_styles

st.set_page_config(page_title="CDMO Studio", page_icon="🔬", layout="wide")
inject_base_styles()

pages = [
    st.Page("home.py", title="Home", icon="🏠"),
    st.Page("pages/1_Upload_Analyse.py", title="Upload & Analyse", icon="📤"),
    st.Page("pages/2_Sensitivity_Analysis.py", title="Sensitivity Analysis", icon="📈"),
    st.Page("pages/3_STL_Generator.py", title="STL Generator", icon="🖨️"),
    st.Page("pages/4_Design_Comparison.py", title="Design Comparison", icon="🗺️"),
    st.Page("pages/5_Session_Manager.py", title="Session Manager", icon="💾"),
    st.Page("pages/6_GA_Optimiser.py", title="GA Optimiser", icon="🧬"),
    st.Page("pages/7_Statistical_Analysis.py", title="Statistical Analysis", icon="📊"),
    st.Page("pages/8_PDF_Report.py", title="PDF Report", icon="📄"),
]

nav = st.navigation(pages, position="sidebar")
nav.run()
