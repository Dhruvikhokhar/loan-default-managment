import streamlit as st
import pandas as pd
import numpy as np
import time
import random
import shutil
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from api_service import APIService
from charts_builder import ChartsBuilder
from mock_database import MockDatabase

# 1. Dataset Resolution & Safe Copy
csv_target = Path(__file__).with_name("Loan_default.csv")
if not csv_target.exists():
    for name in ["Loan_default (1).csv", "Loan_default.csv"]:
        src = Path(__file__).with_name(name)
        if src.exists():
            try:
                shutil.copy(src, csv_target)
                break
            except Exception:
                pass
    if not csv_target.exists():
        matches = list(Path(__file__).parent.glob("*Loan_default*.csv"))
        if matches:
            try:
                shutil.copy(matches[0], csv_target)
            except Exception:
                pass

@st.cache_data(show_spinner=False)
def get_dataset():
    if csv_target.exists():
        try:
            df = pd.read_csv(csv_target)
            if 'Default' in df.columns:
                return df
        except Exception:
            pass
    return pd.DataFrame({
        'Default': [0]*750 + [1]*250,
        'Income': np.random.randint(30000, 150000, 1000),
        'LoanAmount': np.random.randint(10000, 80000, 1000),
        'CreditScore': np.random.randint(580, 820, 1000),
        'Education': np.random.choice(["High School", "Bachelor's", "Master's", "PhD"], 1000),
        'LoanPurpose': np.random.choice(["Home", "Auto", "Education", "Business", "Other"], 1000)
    })

# 2. Page Configuration
st.set_page_config(
    page_title="LoanIQ - Smarter Loan Decisions",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 3. Session State
if 'db' not in st.session_state:
    st.session_state.db = MockDatabase()
if 'api' not in st.session_state:
    st.session_state.api = APIService()
if 'charts' not in st.session_state:
    st.session_state.charts = ChartsBuilder()
if 'page' not in st.session_state:
    st.session_state.page = "Overview"
if 'theme' not in st.session_state:
    st.session_state.theme = "light"
if 'prediction_status' not in st.session_state:
    st.session_state.prediction_status = "idle"
if 'last_prediction' not in st.session_state:
    st.session_state.last_prediction = None
if 'last_inputs' not in st.session_state:
    st.session_state.last_inputs = None
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = None

# Theme Variables
is_dark = st.session_state.theme == 'dark'

if is_dark:
    bg_color = "#090d16"
    card_bg = "#111827"
    border_color = "#1f293d"
    text_color = "#f8fafc"
    subtitle_color = "#94a3b8"
    input_bg = "#161f30"
    hover_bg = "#1e293b"
    card_shadow = "0 8px 25px rgba(0, 0, 0, 0.4), 0 2px 8px rgba(37, 99, 235, 0.1)"
    hero_bg = "linear-gradient(135deg, #161f30 0%, #0d1322 100%)"
    badge_green_bg = "rgba(16, 185, 129, 0.15)"
    badge_green_txt = "#34d399"
    badge_green_brd = "rgba(16, 185, 129, 0.3)"
    badge_red_bg = "rgba(239, 68, 68, 0.15)"
    badge_red_txt = "#f87171"
    badge_red_brd = "rgba(239, 68, 68, 0.3)"
    badge_warn_bg = "rgba(245, 158, 11, 0.15)"
    badge_warn_txt = "#fbbf24"
    badge_warn_brd = "rgba(245, 158, 11, 0.3)"
    float_card_bg = "#1e293b"
else:
    bg_color = "#f4f8fc"
    card_bg = "#ffffff"
    border_color = "#e2e8f0"
    text_color = "#0f172a"
    subtitle_color = "#64748b"
    input_bg = "#ffffff"
    hover_bg = "#f1f5f9"
    card_shadow = "0 4px 20px -2px rgba(37, 99, 235, 0.05), 0 2px 6px -1px rgba(0, 0, 0, 0.02)"
    hero_bg = "linear-gradient(135deg, #eaf3ff 0%, #f4f8ff 60%, #e6f0fa 100%)"
    badge_green_bg = "#ecfdf5"
    badge_green_txt = "#047857"
    badge_green_brd = "#a7f3d0"
    badge_red_bg = "#fef2f2"
    badge_red_txt = "#b91c1c"
    badge_red_brd = "#fecaca"
    badge_warn_bg = "#fffbeb"
    badge_warn_txt = "#b45309"
    badge_warn_brd = "#fde68a"
    float_card_bg = "#ffffff"

# 4. Custom CSS Stylesheet
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    
    /* Hide Default Chrome */
    [data-testid="stSidebar"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    .block-container {{ padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 96% !important; }}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, p, label {{
        color: {text_color} !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }}
    .stMarkdown p {{
        color: {text_color} !important;
        font-size: 14px;
    }}
    .subtext {{
        color: {subtitle_color} !important;
        font-size: 13px;
        line-height: 1.5;
    }}

    /* Card Containers */
    div[data-testid="stVerticalBlockBorder"] {{
        background: {card_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 16px !important;
        padding: 20px 24px !important;
        box-shadow: {card_shadow} !important;
        margin-bottom: 16px !important;
    }}

    /* Global Input Overrides */
    div[data-baseweb="input"], 
    div[data-baseweb="select"] > div,
    input, select {{
        background-color: {input_bg} !important;
        border: 1px solid {border_color} !important;
        color: {text_color} !important;
        border-radius: 10px !important;
    }}

    /* Stat Cards */
    .stat-box {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: {card_shadow};
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }}
    .stat-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }}
    .stat-icon-wrap {{
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }}
    .icon-blue {{ background: rgba(37, 99, 235, 0.15); color: #3b82f6; }}
    .icon-green {{ background: rgba(16, 185, 129, 0.15); color: #10b981; }}
    .icon-red {{ background: rgba(239, 68, 68, 0.15); color: #ef4444; }}
    .icon-purple {{ background: rgba(139, 92, 246, 0.15); color: #8b5cf6; }}
    
    .stat-delta {{
        font-size: 11px;
        font-weight: 700;
        padding: 4px 8px;
        border-radius: 12px;
    }}
    .delta-up {{ background: rgba(16, 185, 129, 0.15); color: #10b981; }}
    .delta-down {{ background: rgba(239, 68, 68, 0.15); color: #ef4444; }}
    
    .stat-val {{
        font-size: 26px;
        font-weight: 800;
        color: {text_color};
        letter-spacing: -0.5px;
        margin-bottom: 2px;
    }}
    .stat-lbl {{
        font-size: 12px;
        color: {subtitle_color};
        font-weight: 600;
    }}

    /* Section Cards */
    .sec-hdr {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 15px;
        font-weight: 700;
        color: {text_color};
        margin-bottom: 16px;
        border-bottom: 1px solid {border_color};
        padding-bottom: 10px;
    }}
    .sec-num {{
        width: 24px;
        height: 24px;
        border-radius: 6px;
        background: #2563eb;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
    }}

    /* Status Badges */
    .badge-approved {{
        background: {badge_green_bg};
        color: {badge_green_txt};
        border: 1px solid {badge_green_brd};
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 12px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }}
    .badge-rejected {{
        background: {badge_red_bg};
        color: {badge_red_txt};
        border: 1px solid {badge_red_brd};
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 12px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }}
    .badge-warning {{
        background: {badge_warn_bg};
        color: {badge_warn_txt};
        border: 1px solid {badge_warn_brd};
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 12px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }}

    /* Button Styling Overrides for Top Navbar & CTAs */
    .top-nav-box button[data-testid="stBaseButton-secondary"] {{
        background: transparent !important;
        border: none !important;
        color: {subtitle_color} !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }}
    .top-nav-box button[data-testid="stBaseButton-secondary"]:hover {{
        color: #2563eb !important;
        background-color: {hover_bg} !important;
    }}
    
    div[data-testid="stButton"] button {{
        height: 38px !important;
        min-height: 38px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        border-radius: 20px !important;
        padding: 0 12px !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}
    button[data-testid="stBaseButton-primary"] {{
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
    }}

    /* Top Horizontal Navigation Container */
    .top-nav-box {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 16px;
        padding: 8px 16px;
        margin-bottom: 20px;
        box-shadow: {card_shadow};
    }}

    /* Exact Hero Banner Styling */
    .hero-card-container {{
        background: {hero_bg};
        border: 1px solid {border_color};
        border-radius: 24px;
        padding: 32px 36px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        box-shadow: {card_shadow};
    }}
    .hero-badge {{
        background: rgba(37, 99, 235, 0.12);
        color: #2563eb;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}
    .hero-headline {{
        font-size: 34px;
        font-weight: 800;
        color: {text_color};
        line-height: 1.2;
        margin: 14px 0 10px 0;
        letter-spacing: -0.5px;
    }}
    .hero-subtext {{
        font-size: 13px;
        color: {subtitle_color};
        line-height: 1.6;
        max-width: 480px;
        margin-bottom: 20px;
    }}
    .hero-image-wrapper {{
        position: relative;
        width: 440px;
        height: 240px;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.12);
    }}
    .hero-image-wrapper img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 20px;
    }}
    .hero-float-card {{
        position: absolute;
        top: 14px;
        right: 14px;
        background: {float_card_bg};
        border-radius: 14px;
        padding: 8px 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        border: 1px solid {border_color};
    }}
    .donut-circle {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 4px solid #10b981;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 800;
        color: {text_color};
    }}
    .float-title {{
        font-size: 12px;
        font-weight: 800;
        color: {text_color};
    }}
    .float-sub {{
        font-size: 10px;
        color: {subtitle_color};
    }}
</style>
""", unsafe_allow_html=True)

# 5. Top Navigation Header Layout
pages = ["Overview", "Predict Loan", "Analytics", "Model Insights", "Applications", "Settings"]
nav_labels = {
    "Overview": "🏠 Overview",
    "Predict Loan": "💰 Predict Loan",
    "Analytics": "📊 Analytics",
    "Model Insights": "🎛️ Dashboard",
    "Applications": "📋 Applications",
    "Settings": "ℹ️ About"
}

with st.container():
    st.markdown("<div class='top-nav-box'>", unsafe_allow_html=True)
    nav_c1, nav_c2, nav_c3 = st.columns([1.8, 8.2, 2.0])

    with nav_c1:
        st.markdown(f"""
            <div style='display:flex; align-items:center; gap:8px;'>
                <div style='background:linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color:white; border-radius:8px; width:34px; height:34px; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:bold; box-shadow: 0 3px 10px rgba(37,99,235,0.3);'>📊</div>
                <div>
                    <div style='font-size:17px; font-weight:800; color:{text_color}; letter-spacing:-0.5px; line-height:1;'>Loan<span style='color:#2563eb;'>IQ</span></div>
                    <div style='font-size:10px; color:{subtitle_color}; font-weight:500; margin-top:2px;'>Smarter Loan Decisions</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with nav_c2:
        btn_cols = st.columns(len(pages))
        for idx, page_item in enumerate(pages):
            is_active = st.session_state.page == page_item
            dis_name = nav_labels[page_item]
            if btn_cols[idx].button(dis_name, key=f"nav_top_btn_{page_item}", type="primary" if is_active else "secondary", use_container_width=True):
                st.session_state.page = page_item
                if page_item != "Predict Loan":
                    st.session_state.prediction_status = "idle"
                st.rerun()

    with nav_c3:
        c_th, c_usr = st.columns([1.2, 1])
        with c_th:
            theme_btn_lbl = "🌙 Dark" if st.session_state.theme == "light" else "☀️ Light"
            if st.button(theme_btn_lbl, key="top_theme_toggle", use_container_width=True):
                st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
                st.rerun()
        with c_usr:
            st.markdown(f"<div style='text-align:right; font-weight:600; font-size:12px; margin-top:8px; color:{text_color}; white-space:nowrap;'>👤 User ▾</div>", unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)


# Helper function to generate clean Plotly charts
def format_plotly(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans", color=text_color, size=12),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(showgrid=True, gridcolor=border_color, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=border_color, zeroline=False)
    return fig


# ================= PAGE 1: OVERVIEW =================
if st.session_state.page == "Overview":
    records = st.session_state.db.get_all_records()
    approved_cnt = sum(r["prediction"] == "Approved" for r in records)
    rejected_cnt = sum(r["prediction"] == "Rejected" for r in records)
    total_cnt = len(records) if records else 2548
    approved_num = approved_cnt if records else 1892
    rejected_num = rejected_cnt if records else 312

    # Hero Banner Matching Image
    hero_col1, hero_col2 = st.columns([1.6, 1])
    with hero_col1:
        st.markdown(f"""
            <div class='hero-card-container' style='box-shadow:none; padding: 24px 28px;'>
                <div>
                    <div class='hero-badge'>
                        ⚡ AI Powered Loan Default Prediction
                    </div>
                    <div class='hero-headline'>
                        Smarter <span style='color: #2563eb;'>Loan Decisions</span><br>with Machine Learning
                    </div>
                    <div class='hero-subtext'>
                        Predict loan default risk, analyze customer profiles and make data-driven lending decisions using powerful machine learning models.
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        hbtn1, hbtn2, _ = st.columns([1.3, 1.3, 1.4])
        with hbtn1:
            if st.button("🚀 Predict Loan Risk →", type="primary", use_container_width=True):
                st.session_state.page = "Predict Loan"
                st.rerun()
        with hbtn2:
            if st.button("🎛️ View Dashboard", use_container_width=True):
                st.session_state.page = "Analytics"
                st.rerun()

    with hero_col2:
        st.markdown(f"""
            <div class='hero-image-wrapper' style='width:100%; height:250px;'>
                <img src='https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=800&q=80' alt='House Model' />
                <div class='hero-float-card'>
                    <div class='donut-circle'>75%</div>
                    <div>
                        <div class='float-title'>Model Accuracy</div>
                        <div class='float-sub'>High prediction performance</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4 Metric Cards Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
            <div class='stat-box'>
                <div class='stat-top'>
                    <div class='stat-icon-wrap icon-blue'>📋</div>
                    <div class='stat-delta delta-up'>↑ 12% from last month</div>
                </div>
                <div>
                    <div class='stat-val'>{total_cnt:,}</div>
                    <div class='stat-lbl'>Total Applications</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
            <div class='stat-box'>
                <div class='stat-top'>
                    <div class='stat-icon-wrap icon-green'>✅</div>
                    <div class='stat-delta delta-up'>↑ 18% from last month</div>
                </div>
                <div>
                    <div class='stat-val'>{approved_num:,}</div>
                    <div class='stat-lbl'>Approved Loans</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
            <div class='stat-box'>
                <div class='stat-top'>
                    <div class='stat-icon-wrap icon-red'>⚠️</div>
                    <div class='stat-delta delta-down'>↓ 4% from last month</div>
                </div>
                <div>
                    <div class='stat-val'>{rejected_num:,}</div>
                    <div class='stat-lbl'>Defaulted Loans</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
            <div class='stat-box'>
                <div class='stat-top'>
                    <div class='stat-icon-wrap icon-purple'>💳</div>
                    <div class='stat-delta delta-up'>↑ 8% from last month</div>
                </div>
                <div>
                    <div class='stat-val'>₹ 45.2 Cr</div>
                    <div class='stat-lbl'>Total Loan Amount</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2 Charts Row
    ch_col1, ch_col2 = st.columns(2)
    with ch_col1:
        with st.container(border=True):
            st.markdown("#### 📊 Loan Status Distribution")
            st.caption("Overall loan application status")
            pie_df = pd.DataFrame({
                'Status': ['Approved Loans', 'Defaulted Loans', 'Rejected Loans'],
                'Count': [1892, 312, 344]
            })
            fig_pie = px.pie(
                pie_df, names='Status', values='Count', hole=0.6,
                color_discrete_sequence=['#2563eb', '#ef4444', '#f59e0b']
            )
            format_plotly(fig_pie)
            st.plotly_chart(fig_pie, use_container_width=True)

    with ch_col2:
        with st.container(border=True):
            st.markdown("#### 📊 Default Risk by Income Category")
            st.caption("Analysis of default rates across different income ranges")
            inc_df = pd.DataFrame({
                'Income Category': ['< 3L', '3L - 5L', '5L - 10L', '10L - 20L', '> 20L'],
                'Default Rate (%)': [28, 20, 12, 8, 5]
            })
            fig_bar = px.bar(
                inc_df, x='Income Category', y='Default Rate (%)',
                color_discrete_sequence=['#2563eb']
            )
            format_plotly(fig_bar)
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature Highlights Row
    f1, f2, f3 = st.columns(3)
    with f1:
        with st.container(border=True):
            st.markdown("<div style='display:flex; align-items:center; gap:10px;'><div style='background:rgba(37,99,235,0.15); color:#3b82f6; padding:10px; border-radius:10px; font-size:20px;'>🎯</div><div><b>Accurate Predictions</b><div class='subtext'>Use machine learning to predict loan default risk with high accuracy.</div></div></div>", unsafe_allow_html=True)
    with f2:
        with st.container(border=True):
            st.markdown("<div style='display:flex; align-items:center; gap:10px;'><div style='background:rgba(139,92,246,0.15); color:#8b5cf6; padding:10px; border-radius:10px; font-size:20px;'>📊</div><div><b>Risk Analysis & Insights</b><div class='subtext'>Analyze customer profiles and key risk factors.</div></div></div>", unsafe_allow_html=True)
    with f3:
        with st.container(border=True):
            st.markdown("<div style='display:flex; align-items:center; gap:10px;'><div style='background:rgba(16,185,129,0.15); color:#10b981; padding:10px; border-radius:10px; font-size:20px;'>💡</div><div><b>Better Lending Decisions</b><div class='subtext'>Make data-driven financial decisions with AI.</div></div></div>", unsafe_allow_html=True)


# ================= PAGE 2: PREDICT LOAN =================
elif st.session_state.page == "Predict Loan":
    
    if st.session_state.prediction_status == "success" and st.session_state.last_prediction is not None:
        res = st.session_state.last_prediction
        inp = st.session_state.last_inputs or {}
        prob_pct = res['probability'] * 100
        is_approved = res['prediction'] == "Approved"

        st.markdown("### Prediction Result")
        st.caption("Here is the loan default risk prediction based on the provided applicant information.")
        st.markdown("<br>", unsafe_allow_html=True)

        res_c1, res_c2, res_c3 = st.columns([1.2, 1.2, 1])

        with res_c1:
            with st.container(border=True):
                if is_approved:
                    st.markdown("""
                        <div style='text-align:center; padding:10px;'>
                            <div style='width:64px; height:64px; background:rgba(16,185,129,0.15); color:#10b981; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:36px; margin:0 auto 12px;'>✓</div>
                            <div style='font-size:20px; font-weight:800; color:#10b981;'>Not Likely to Default</div>
                            <div class='badge-approved' style='margin: 8px 0;'>Low Risk Applicant</div>
                            <div class='subtext' style='margin-top:8px;'>Based on the provided information, this applicant is predicted to be a low risk for loan default.</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div style='text-align:center; padding:10px;'>
                            <div style='width:64px; height:64px; background:rgba(239,68,68,0.15); color:#ef4444; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:36px; margin:0 auto 12px;'>✕</div>
                            <div style='font-size:20px; font-weight:800; color:#ef4444;'>Likely to Default</div>
                            <div class='badge-rejected' style='margin: 8px 0;'>High Risk Applicant</div>
                            <div class='subtext' style='margin-top:8px;'>Based on the provided information, this applicant has a higher likelihood of default risk.</div>
                        </div>
                    """, unsafe_allow_html=True)

        pred_color = "#10b981" if is_approved else "#ef4444"
        pred_label = "Not Likely to Default" if is_approved else "Likely to Default"
        risk_badge_class = "badge-approved" if is_approved else "badge-rejected"
        risk_text = res.get('risk', 'Low')

        with res_c2:
            with st.container(border=True):
                st.markdown("<b>Prediction Details</b>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style='line-height:2.2; font-size:13px; margin-top:8px;'>
                        <div style='display:flex; justify-content:space-between;'><span>Prediction</span><span style='font-weight:700; color:{pred_color};'>{pred_label}</span></div>
                        <div style='display:flex; justify-content:space-between;'><span>Risk Level</span><span class='{risk_badge_class}'>{risk_text}</span></div>
                        <div style='display:flex; justify-content:space-between;'><span>Probability of Default</span><span style='font-weight:700;'>{100 - prob_pct if is_approved else prob_pct:.1f}%</span></div>
                        <div style='display:flex; justify-content:space-between;'><span>Model Confidence</span><span style='font-weight:700;'>92%</span></div>
                    </div>
                """, unsafe_allow_html=True)

        with res_c3:
            with st.container(border=True):
                st.markdown("<b>👤 Applicant Summary</b>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style='line-height:1.9; font-size:12px; margin-top:6px; color:{subtitle_color};'>
                        <div><b>Age:</b> {inp.get('Age', 35)}</div>
                        <div><b>Gender:</b> {inp.get('Gender', 'Male')}</div>
                        <div><b>Dependents:</b> {inp.get('HasDependents', '2')}</div>
                        <div><b>Education:</b> {inp.get('Education', 'Graduate')}</div>
                        <div><b>Income:</b> ₹ {inp.get('Income', 750000):,}</div>
                        <div><b>Loan Amount:</b> ₹ {inp.get('LoanAmount', 200000):,}</div>
                        <div><b>Loan Term:</b> {inp.get('LoanTerm', 360)} Months</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        p1, p2, p3, p4 = st.columns(4)
        p1.markdown(f"<div class='stat-box' style='text-align:center;'><div>📊 <b>{100 - prob_pct if is_approved else prob_pct:.1f}%</b></div><div class='stat-lbl'>Default Probability</div></div>", unsafe_allow_html=True)
        p2.markdown(f"<div class='stat-box' style='text-align:center;'><div>🛡️ <b style='color:{pred_color};'>{risk_text}</b></div><div class='stat-lbl'>Risk Level</div></div>", unsafe_allow_html=True)
        p3.markdown("<div class='stat-box' style='text-align:center;'><div>🎯 <b>92%</b></div><div class='stat-lbl'>Model Confidence</div></div>", unsafe_allow_html=True)
        p4.markdown("<div class='stat-box' style='text-align:center;'><div>⏱️ <b>~ 2s</b></div><div class='stat-lbl'>Prediction Time</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        btn_act1, btn_act2 = st.columns([1, 1])
        with btn_act1:
            if st.button("🔄 Make Another Prediction", type="primary", use_container_width=True):
                st.session_state.prediction_status = "idle"
                st.rerun()
        with btn_act2:
            if st.button("📊 View Dashboard", use_container_width=True):
                st.session_state.page = "Analytics"
                st.rerun()

    else:
        st.markdown("### Predict Loan **Default Risk**")
        st.caption("Enter applicant details below to get the loan default prediction using our machine learning model.")
        st.markdown("<br>", unsafe_allow_html=True)

        col_input, col_side = st.columns([2.2, 1])

        with col_input:
            with st.container(border=True):
                st.markdown("<div class='sec-hdr'><div class='sec-num'>1</div> Profile Characteristics</div>", unsafe_allow_html=True)
                st.caption("Basic information about the loan applicant")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    age = st.number_input("👤 Age", 18, 100, 35)
                with c2:
                    gender = st.selectbox("👤 Gender", ["Male", "Female"])
                with c3:
                    marital = st.selectbox("💍 Married", ["Yes", "No"])
                with c4:
                    dependents = st.selectbox("👨‍👩‍👧 Dependents", ["0", "1", "2", "3+"])
                
                c5, c6 = st.columns(2)
                with c5:
                    education = st.selectbox("🎓 Education", ["Graduate", "High School", "Post Graduate", "Professional"])
                with c6:
                    self_emp = st.selectbox("💼 Self Employed", ["No", "Yes"])

            with st.container(border=True):
                st.markdown("<div class='sec-hdr'><div class='sec-num'>2</div> Financial Portfolio</div>", unsafe_allow_html=True)
                st.caption("Financial background and credit information")
                f1, f2, f3 = st.columns(3)
                with f1:
                    income = st.number_input("💵 Income (Annual)", 0, 10000000, 750000, step=50000)
                with f2:
                    credit_history = st.selectbox("📜 Credit History", ["1 (Good)", "0 (Bad)"])
                with f3:
                    property_area = st.selectbox("🏡 Property Area", ["Urban", "Semiurban", "Rural"])

            with st.container(border=True):
                st.markdown("<div class='sec-hdr'><div class='sec-num'>3</div> Loan Parameters</div>", unsafe_allow_html=True)
                st.caption("Loan specific details")
                l1, l2 = st.columns(2)
                with l1:
                    loan_amount = st.number_input("💰 Loan Amount", 0, 10000000, 200000, step=10000)
                with l2:
                    loan_term = st.number_input("📅 Loan Term (Months)", 12, 600, 360, step=12)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔮 Predict Loan Default", type="primary", use_container_width=True):
                credit_score = 720 if "1" in credit_history else 580
                payload = {
                    "Age": age, "Income": income, "LoanAmount": loan_amount,
                    "CreditScore": credit_score, "MonthsEmployed": 60,
                    "NumCreditLines": 3, "InterestRate": 8.5,
                    "LoanTerm": loan_term, "DTIRatio": 0.35, "Education": education,
                    "EmploymentType": "Full-time" if self_emp == "No" else "Self-employed",
                    "MaritalStatus": "Married" if marital == "Yes" else "Single",
                    "HasMortgage": "No", "HasDependents": "Yes" if dependents != "0" else "No",
                    "LoanPurpose": "Home", "HasCoSigner": "No"
                }
                st.session_state.last_inputs = payload
                st.session_state.last_inputs['Gender'] = gender
                try:
                    res = st.session_state.api.call_predict(payload, demo_mode=st.session_state.demo_mode)
                    st.session_state.db.add_record(payload, res)
                    st.session_state.last_prediction = res
                    st.session_state.prediction_status = "success"
                except Exception as e:
                    st.session_state.prediction_status = "error"
                    st.session_state.last_error = str(e)
                st.rerun()

        with col_side:
            st.markdown("""
                <div class='side-info-card'>
                    <div class='side-info-title'>ℹ️ How It Works?</div>
                    <div class='side-info-body'>Fill in all required applicant details cleanly.</div>
                    <div style='margin-top:10px; font-size:12px; line-height:1.8;'>
                        <div><b>1. Enter Applicant Details</b></div>
                        <div><b>2. ML Model Analysis</b></div>
                        <div><b>3. Get Prediction Result</b></div>
                    </div>
                </div>
                
                <div class='side-info-card'>
                    <div class='side-info-title'>🔒 Data Security</div>
                    <div class='side-info-body'>Your data is processed securely and used only for prediction purposes.</div>
                </div>
                
                <div class='side-info-card'>
                    <div class='side-info-title'>❓ Need Help?</div>
                    <div class='side-info-body'>Check the field descriptions and model information to understand each input.</div>
                </div>

                <div class='side-info-card'>
                    <div class='side-info-title'>📌 Important Note</div>
                    <div class='side-info-body'>This prediction is based on machine learning analysis and should be used for reference only.</div>
                </div>
            """, unsafe_allow_html=True)


# ================= PAGE 3: ANALYTICS =================
elif st.session_state.page == "Analytics":
    st.markdown("### Loan **Analytics & Insights**")
    st.caption("Explore key trends, patterns and insights from loan applications using data visualization.")
    st.markdown("<br>", unsafe_allow_html=True)

    a1, a2, a3, a4 = st.columns(4)
    a1.markdown("<div class='stat-box'><div class='stat-lbl'>Total Applications</div><div class='stat-val'>2,548</div><div class='stat-delta delta-up'>↑ 12% from last month</div></div>", unsafe_allow_html=True)
    a2.markdown("<div class='stat-box'><div class='stat-lbl'>Approved Loans</div><div class='stat-val'>1,892</div><div class='stat-delta delta-up'>↑ 18% from last month</div></div>", unsafe_allow_html=True)
    a3.markdown("<div class='stat-box'><div class='stat-lbl'>Defaulted Loans</div><div class='stat-val'>312</div><div class='stat-delta delta-down'>↓ 4% from last month</div></div>", unsafe_allow_html=True)
    a4.markdown("<div class='stat-box'><div class='stat-lbl'>Total Loan Amount</div><div class='stat-val'>₹ 45.2 Cr</div><div class='stat-delta delta-up'>↑ 8% from last month</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    csv_df = get_dataset()

    c_r1_1, c_r1_2 = st.columns(2)
    with c_r1_1:
        with st.container(border=True):
            st.markdown("#### 📊 Loan Status Distribution")
            st.plotly_chart(st.session_state.charts.build_approval_donut(csv_df, st.session_state.theme), use_container_width=True)
    with c_r1_2:
        with st.container(border=True):
            st.markdown("#### 📊 Default Risk by Income Category")
            st.plotly_chart(st.session_state.charts.build_income_dist(csv_df, st.session_state.theme), use_container_width=True)

    c_r2_1, c_r2_2 = st.columns(2)
    with c_r2_1:
        with st.container(border=True):
            st.markdown("#### 📊 Loan Amount Distribution")
            st.plotly_chart(st.session_state.charts.build_loan_amt_dist(csv_df, st.session_state.theme), use_container_width=True)
    with c_r2_2:
        with st.container(border=True):
            st.markdown("#### 📊 Approval Rate by Education")
            st.plotly_chart(st.session_state.charts.build_education_vs_approval(csv_df, st.session_state.theme), use_container_width=True)


# ================= PAGE 4: MODEL INSIGHTS =================
elif st.session_state.page == "Model Insights":
    st.markdown("### Model Insights & **Explainability**")
    st.caption("Understand how the machine learning model works and which factors influence loan default risk.")
    st.markdown("<br>", unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown("<div class='stat-box'><div class='stat-lbl'>Model Accuracy</div><div class='stat-val'>92%</div><div class='stat-delta delta-up'>↑ 4% from last version</div></div>", unsafe_allow_html=True)
    m2.markdown("<div class='stat-box'><div class='stat-lbl'>Model Error (MAE)</div><div class='stat-val'>0.08</div><div class='stat-delta delta-down'>↓ 12% from last version</div></div>", unsafe_allow_html=True)
    m3.markdown("<div class='stat-box'><div class='stat-lbl'>AUC Score</div><div class='stat-val'>0.89</div><div class='stat-delta delta-up'>↑ 5% from last version</div></div>", unsafe_allow_html=True)
    m4.markdown("<div class='stat-box'><div class='stat-lbl'>Selected Model</div><div class='stat-val' style='font-size:18px;'>Random Forest</div><div class='subtext'>Best performing model</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_fi, col_comp = st.columns(2)
    with col_fi:
        with st.container(border=True):
            st.markdown("#### 📊 Feature Importance")
            st.caption("Key factors that influence loan default prediction")
            feat_df = pd.DataFrame({
                'Feature': ['Credit_History', 'Income', 'LoanAmount', 'Loan_Term', 'Property_Area', 'Dependents', 'Gender', 'Age'],
                'Importance (%)': [25.4, 18.7, 15.2, 10.8, 8.3, 5.1, 3.2, 2.8]
            }).sort_values('Importance (%)')
            fig_fi = px.bar(feat_df, x='Importance (%)', y='Feature', orientation='h', color_discrete_sequence=['#2563eb'])
            format_plotly(fig_fi)
            st.plotly_chart(fig_fi, use_container_width=True)

    with col_comp:
        with st.container(border=True):
            st.markdown("#### 📊 Model Performance Comparison")
            st.caption("Comparison of different machine learning models")
            comp_df = pd.DataFrame({
                'Model': ['Logistic Regression', 'Decision Tree', 'Random Forest', 'SVM', 'XGBoost'],
                'Accuracy': [78, 82, 92, 85, 90],
                'Precision': [75, 80, 91, 83, 89],
                'Recall': [72, 79, 89, 81, 88]
            })
            fig_comp = px.bar(comp_df, x='Model', y=['Accuracy', 'Precision', 'Recall'], barmode='group', color_discrete_sequence=['#2563eb', '#10b981', '#8b5cf6'])
            format_plotly(fig_comp)
            st.plotly_chart(fig_comp, use_container_width=True)


# ================= PAGE 5: APPLICATIONS =================
elif st.session_state.page == "Applications":
    st.markdown("### Loan **Applications History**")
    st.caption("View and manage all loan applications with their prediction results.")
    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        sc1, sc2, sc3, sc4 = st.columns([3, 1.5, 1.5, 1])
        with sc1:
            search = st.text_input("Search", placeholder="🔍 Search by applicant ID or name...", label_visibility="collapsed")
        with sc2:
            status_flt = st.selectbox("Status", ["All Status", "Approved", "Rejected"], label_visibility="collapsed")
        with sc3:
            risk_flt = st.selectbox("Risk Level", ["All Risk Levels", "Low", "Medium", "High"], label_visibility="collapsed")
        with sc4:
            st.button("🔍 Search", type="primary", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    p1, p2, p3, p4 = st.columns(4)
    p1.markdown("<div class='stat-box'><div class='stat-lbl'>Total Applications</div><div class='stat-val'>2,548</div></div>", unsafe_allow_html=True)
    p2.markdown("<div class='stat-box'><div class='stat-lbl'>Approved</div><div class='stat-val' style='color:#10b981;'>1,892 <span style='font-size:12px;'>74.2%</span></div></div>", unsafe_allow_html=True)
    p3.markdown("<div class='stat-box'><div class='stat-lbl'>Defaulted</div><div class='stat-val' style='color:#ef4444;'>312 <span style='font-size:12px;'>12.2%</span></div></div>", unsafe_allow_html=True)
    p4.markdown("<div class='stat-box'><div class='stat-lbl'>Rejected</div><div class='stat-val' style='color:#f59e0b;'>344 <span style='font-size:12px;'>13.6%</span></div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    recs = st.session_state.db.get_all_records()
    if not recs:
        mock_apps = [
            {"id": "APP001", "age": 35, "gender": "Male", "income": 750000, "loan": 200000, "pred": "Not Likely", "risk": "Low", "date": "24 Sep 2026"},
            {"id": "APP002", "age": 42, "gender": "Female", "income": 500000, "loan": 150000, "pred": "Not Likely", "risk": "Low", "date": "24 Sep 2026"},
            {"id": "APP003", "age": 28, "gender": "Male", "income": 800000, "loan": 300000, "pred": "Not Likely", "risk": "Low", "date": "23 Sep 2026"},
            {"id": "APP004", "age": 50, "gender": "Male", "income": 650000, "loan": 250000, "pred": "Likely", "risk": "High", "date": "23 Sep 2026"},
            {"id": "APP005", "age": 38, "gender": "Female", "income": 400000, "loan": 180000, "pred": "Not Likely", "risk": "Medium", "date": "22 Sep 2026"},
            {"id": "APP006", "age": 45, "gender": "Male", "income": 900000, "loan": 400000, "pred": "Not Likely", "risk": "Low", "date": "22 Sep 2026"},
            {"id": "APP007", "age": 32, "gender": "Female", "income": 350000, "loan": 120000, "pred": "Likely", "risk": "High", "date": "21 Sep 2026"},
            {"id": "APP008", "age": 40, "gender": "Male", "income": 720000, "loan": 230000, "pred": "Not Likely", "risk": "Low", "date": "21 Sep 2026"},
            {"id": "APP009", "age": 29, "gender": "Male", "income": 580000, "loan": 190000, "pred": "Not Likely", "risk": "Low", "date": "20 Sep 2026"},
            {"id": "APP010", "age": 37, "gender": "Female", "income": 620000, "loan": 210000, "pred": "Not Likely", "risk": "Low", "date": "20 Sep 2026"},
        ]
        apps_list = mock_apps
    else:
        apps_list = recs

    # Dynamic Filtering
    filtered_list = []
    q = search.strip().lower()
    for item in apps_list:
        app_id = str(item.get('id', item.get('Application ID', ''))).lower()
        pred_lbl = str(item.get('pred', item.get('prediction', ''))).lower()
        risk_lbl = str(item.get('risk', '')).lower()
        gender_lbl = str(item.get('gender', '')).lower()
        date_lbl = str(item.get('date', '')).lower()

        if q and (q not in app_id and q not in pred_lbl and q not in risk_lbl and q not in gender_lbl and q not in date_lbl):
            continue

        if status_flt == "Approved" and ("approved" not in pred_lbl and "not likely" not in pred_lbl):
            continue
        if status_flt == "Rejected" and ("rejected" not in pred_lbl and "likely" not in pred_lbl or "not likely" in pred_lbl):
            continue

        if risk_flt != "All Risk Levels" and risk_flt.lower() != risk_lbl:
            continue

        filtered_list.append(item)

    if not filtered_list:
        st.info("🔍 No loan applications match your search filters.")
    else:
        # Clean HTML table string (NO leading markdown indentation!)
        table_html = f"""<div style="background:{card_bg}; border:1px solid {border_color}; border-radius:14px; overflow:hidden; box-shadow:{card_shadow}; margin-top:16px;">
<table style="width:100%; border-collapse:collapse; font-family:'Plus Jakarta Sans', sans-serif;">
<thead>
<tr style="background:{input_bg}; border-bottom:1px solid {border_color};">
<th style="padding:14px 16px; text-align:left; font-size:12px; font-weight:700; color:{subtitle_color}; text-transform:uppercase;">Applicant ID</th>
<th style="padding:14px 16px; text-align:left; font-size:12px; font-weight:700; color:{subtitle_color}; text-transform:uppercase;">Age</th>
<th style="padding:14px 16px; text-align:left; font-size:12px; font-weight:700; color:{subtitle_color}; text-transform:uppercase;">Gender</th>
<th style="padding:14px 16px; text-align:left; font-size:12px; font-weight:700; color:{subtitle_color}; text-transform:uppercase;">Income</th>
<th style="padding:14px 16px; text-align:left; font-size:12px; font-weight:700; color:{subtitle_color}; text-transform:uppercase;">Loan Amount</th>
<th style="padding:14px 16px; text-align:left; font-size:12px; font-weight:700; color:{subtitle_color}; text-transform:uppercase;">Prediction</th>
<th style="padding:14px 16px; text-align:left; font-size:12px; font-weight:700; color:{subtitle_color}; text-transform:uppercase;">Risk Level</th>
<th style="padding:14px 16px; text-align:left; font-size:12px; font-weight:700; color:{subtitle_color}; text-transform:uppercase;">Date</th>
</tr>
</thead>
<tbody>
"""

        for item in filtered_list:
            pred_lbl = item.get('pred', item.get('prediction', 'Not Likely'))
            is_approved_row = pred_lbl in ["Not Likely", "Approved"]
            
            if is_approved_row:
                p_badge = f'<span style="background:{badge_green_bg}; color:{badge_green_txt}; border:1px solid {badge_green_brd}; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:700;">Not Likely</span>'
            else:
                p_badge = f'<span style="background:{badge_red_bg}; color:{badge_red_txt}; border:1px solid {badge_red_brd}; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:700;">Likely</span>'
                
            r_lvl = item.get('risk', 'Low')
            if r_lvl == "Low":
                r_badge = f'<span style="background:{badge_green_bg}; color:{badge_green_txt}; border:1px solid {badge_green_brd}; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:700;">Low Risk</span>'
            elif r_lvl == "High":
                r_badge = f'<span style="background:{badge_red_bg}; color:{badge_red_txt}; border:1px solid {badge_red_brd}; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:700;">High Risk</span>'
            else:
                r_badge = f'<span style="background:{badge_warn_bg}; color:{badge_warn_txt}; border:1px solid {badge_warn_brd}; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:700;">Medium Risk</span>'
                
            inc_str = f"₹ {item.get('income', 0):,}"
            loan_str = f"₹ {item.get('loan', item.get('loan_amount', 0)):,}"
            app_id = item.get('id', item.get('Application ID', 'APP001'))
            age_str = item.get('age', 35)
            gen_str = item.get('gender', 'Male')
            dt_str = item.get('date', '24 Sep 2026')
            
            table_html += f"""<tr style="border-bottom:1px solid {border_color};">
<td style="padding:12px 16px; font-size:13px; font-weight:700; color:{text_color};">{app_id}</td>
<td style="padding:12px 16px; font-size:13px; color:{text_color};">{age_str}</td>
<td style="padding:12px 16px; font-size:13px; color:{text_color};">{gen_str}</td>
<td style="padding:12px 16px; font-size:13px; color:{text_color};">{inc_str}</td>
<td style="padding:12px 16px; font-size:13px; color:{text_color};">{loan_str}</td>
<td style="padding:12px 16px;">{p_badge}</td>
<td style="padding:12px 16px;">{r_badge}</td>
<td style="padding:12px 16px; font-size:13px; color:{subtitle_color};">{dt_str}</td>
</tr>
"""

        table_html += "</tbody></table></div>"

        st.markdown(table_html, unsafe_allow_html=True)


# ================= PAGE 6: SETTINGS =================
elif st.session_state.page == "Settings":
    st.markdown("### Settings & **Preferences**")
    st.caption("Customize appearance and model execution modes.")
    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### Appearance Theme")
        st.caption("Select your preferred visual layout mode.")
        th1, th2 = st.columns(2)
        with th1:
            if st.button("☀️ Light Mode", type="primary" if st.session_state.theme == "light" else "secondary", use_container_width=True):
                st.session_state.theme = "light"
                st.rerun()
        with th2:
            if st.button("🌙 Dark Mode", type="primary" if st.session_state.theme == "dark" else "secondary", use_container_width=True):
                st.session_state.theme = "dark"
                st.rerun()

    with st.container(border=True):
        st.markdown("#### Model Simulation Options")
        st.caption("Test specific prediction outcomes for demonstration.")
        modes = {
            "Normal AI Model": None,
            "Force Approved": "approved",
            "Force Rejected": "rejected",
            "Simulate API Error": "error"
        }
        curr_mode = next((k for k, v in modes.items() if v == st.session_state.demo_mode), "Normal AI Model")
        sel_mode = st.selectbox("Simulation Mode", list(modes.keys()), index=list(modes.keys()).index(curr_mode))
        st.session_state.demo_mode = modes[sel_mode]
