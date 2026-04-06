import streamlit as st
import json
import os
import pandas as pd
import importlib.util
from datetime import datetime

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CriticalArc Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600;700&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Barlow', sans-serif;
        color: #F0F0F0;
    }
    .main { background-color: #23262B; }

    section[data-testid="stSidebar"] {
        background-color: #2D3035;
        border-right: 1px solid #3E4248;
    }
   section[data-testid="stSidebar"] * { color: #C8CDD4 !important; }

    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .element-container p,
    section[data-testid="stSidebar"] .stMarkdown p {
        font-size: 11px !important;
        letter-spacing: 1px !important;
    }

    section[data-testid="stSidebar"] .stSelectbox div {
        font-size: 13px !important;
    }

    .kpi-card {
        background: #2D3035;
        border: 1px solid #3E4248;
        border-radius: 10px;
        padding: 20px 24px;
        text-align: center;
        transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: #8A8F98; }
    .kpi-label {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #8A8F98;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-family: 'DM Mono', monospace;
        font-size: 32px;
        font-weight: 500;
        line-height: 1;
        margin-bottom: 4px;
    }
    .kpi-sub { font-size: 12px; color: #8A8F98; }
    .kpi-red    { color: #E04040; }
    .kpi-yellow { color: #F4B942; }
    .kpi-green  { color: #39B54A; }
    .kpi-blue   { color: #4A90D9; }
    .kpi-white  { color: #F0F0F0; }

    .section-header {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #39B54A;
        margin: 24px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #3E4248;
    }

    .dash-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 36px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #F0F0F0;
    margin: 0;
    text-transform: uppercase;
    }
            
    .dash-sub {
        font-size: 14px;
        color: #8A8F98;
        margin: 4px 0 0 0;
        letter-spacing: 0.5px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #2D3035;
        padding: 4px;
        border-radius: 10px;
        border: 1px solid #3E4248;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: #8A8F98;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.5px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: #34383E !important;
        color: #39B54A !important;
    }

    .stDataFrame {
        border: 1px solid #3E4248;
        border-radius: 8px;
        overflow: hidden;
    }

    .stButton > button {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        background: transparent;
        color: #F0F0F0;
        border: 1px solid #3E4248;
        border-radius: 6px;
        transition: background 0.15s, border-color 0.15s;
    }
    .stButton > button:hover {
        background: #34383E;
        border-color: #8A8F98;
        color: #F0F0F0;
    }

    .ca-brand {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #F0F0F0;
        border-bottom: 2px solid #39B54A;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }
    .ca-brand-sub {
        font-size: 11px;
        color: #8A8F98;
        letter-spacing: 1px;
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Load Projects ─────────────────────────────────────────────────────────────
def get_all_projects():
    projects = {}
    projects_dir = os.path.join(os.path.dirname(__file__), "projects")
    for folder in os.listdir(projects_dir):
        config_path = os.path.join(projects_dir, folder, "config.json")
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    projects[folder] = json.loads(content)
    return projects

all_projects = get_all_projects()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="ca-brand">
        CriticalArc
        <div class="ca-brand-sub">Project Dashboard Platform</div>
    </div>
    """, unsafe_allow_html=True)

    project_labels = {k: v["project_name"] for k, v in all_projects.items()}
    selected_key = st.selectbox(
        "Select Project",
        options=list(project_labels.keys()),
        format_func=lambda k: project_labels[k]
    )
    config = all_projects[selected_key]

    st.markdown("---")
    st.markdown("**Filters**")

    from utils.gsheets import load_project_data
    try:
        with st.spinner("Loading filters..."):
            raw = load_project_data(config["sheet_name"])
            issues_raw = raw.get("Issues", pd.DataFrame())
    except Exception as e:
        st.warning(f"Could not load filters: {e}")
        issues_raw = pd.DataFrame()

    disciplines = ["All"]
    if not issues_raw.empty and "discipline" in issues_raw.columns:
        disciplines += sorted([d for d in issues_raw["discipline"].dropna().unique() if d])

    contractors = ["All"]
    if not issues_raw.empty and "assigned_company" in issues_raw.columns:
        contractors += sorted([c for c in issues_raw["assigned_company"].dropna().unique() if c])
    
    filters = {
        "discipline": st.selectbox("Division / Discipline", disciplines),
        "contractor": st.selectbox("Contractor / Assigned To", contractors),
        "status": st.selectbox("Status", ["All", "Open", "In Progress", "Pending Review", "Closed"]),
    }

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:11px; color:#8A8F98;'>Refreshed: {datetime.now().strftime('%b %d %H:%M')}</div>",
        unsafe_allow_html=True
    )
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# ─── Header ───────────────────────────────────────────────────────────────────
st.html(f"""
<div style="padding: 8px 0 16px 0;">
    <div style="
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 42px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #374151;
        text-transform: uppercase;
        line-height: 1.1;
    ">{config['project_name']}</div>
    <div style="
        font-family: 'Barlow', sans-serif;
        font-size: 14px;
        color: #8A8F98;
        margin-top: 4px;
        letter-spacing: 0.5px;
    ">{config.get('subtitle', '')}</div>
</div>
""")

# ─── Render Project Layout ─────────────────────────────────────────────────────
layout_path = os.path.join(os.path.dirname(__file__), "projects", selected_key, "layout.py")
spec = importlib.util.spec_from_file_location("layout", layout_path)
layout_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout_mod)
layout_mod.render(config, filters)