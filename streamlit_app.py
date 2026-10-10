import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

st.set_page_config(
    page_title="MailForge - Professional Email Sender",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Dashboard Theme
st.markdown("""
<style>
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0a14 0%, #1a1a2e 100%);
        color: #e0e0e0;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid #2a3f5f;
    }
    
    .main {
        background: linear-gradient(135deg, #0a0a14 0%, #1a1a2e 100%);
    }
    
    /* Sidebar branding */
    .sidebar-brand {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        width: 40px;
        height: 40px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        font-size: 18px;
        margin-bottom: 12px;
    }
    
    .sidebar-title {
        font-weight: 700;
        color: #e0e0e0;
        font-size: 14px;
        margin: 0;
    }
    
    .sidebar-version {
        font-size: 12px;
        color: #888;
        margin: 4px 0 0 0;
    }
    
    .sidebar-section-header {
        padding: 16px 12px 8px 12px;
        color: #a0a0a0;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-top: 20px;
        border-top: 1px solid #2a3f5f;
        padding-top: 12px;
    }
    
    .sidebar-section-header:first-of-type {
        border-top: none;
        margin-top: 0;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a2a4a 0%, #0f1628 100%);
        border: 1px solid #2a3f5f;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    .metric-icon {
        font-size: 28px;
        margin-bottom: 12px;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #00d9ff;
        margin: 8px 0;
    }
    
    .metric-label {
        font-size: 12px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    
    .metric-status {
        font-size: 11px;
        color: #666;
        margin-top: 4px;
    }
    
    /* Feature cards */
    .feature-card {
        background: linear-gradient(135deg, rgba(26, 42, 74, 0.8) 0%, rgba(15, 22, 40, 0.8) 100%);
        border: 1px solid #2a3f5f;
        border-radius: 10px;
        padding: 20px;
        cursor: pointer;
        transition: all 0.3s;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .feature-card:hover {
        border-color: #00d9ff;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.2);
        transform: translateY(-2px);
        background: linear-gradient(135deg, rgba(26, 42, 74, 1) 0%, rgba(15, 22, 40, 1) 100%);
    }
    
    .feature-icon {
        font-size: 28px;
        margin-bottom: 12px;
    }
    
    .feature-title {
        font-size: 14px;
        font-weight: 700;
        color: #e0e0e0;
        margin-bottom: 4px;
    }
    
    .feature-desc {
        font-size: 12px;
        color: #888;
        line-height: 1.4;
    }
    
    .section-title {
        font-size: 12px;
        font-weight: 700;
        color: #a0a0a0;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin: 30px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #2a3f5f;
    }
    
    h1 {
        color: #e0e0e0 !important;
        font-size: 36px !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
        margin: 0 !important;
    }
    
    .subtitle {
        color: #888 !important;
        font-size: 14px !important;
        margin: 8px 0 20px 0 !important;
        font-weight: 400 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 1px solid #2a3f5f;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 14px 20px;
        background-color: transparent;
        color: #666;
        font-weight: 600;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 12px;
    }
    
    .stTabs [aria-selected="true"] [data-testid="stTab"] {
        color: #00d9ff !important;
        border-bottom: 2px solid #00d9ff !important;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        background-color: #1a2a4a !important;
        border: 1px solid #2a3f5f !important;
        color: #e0e0e0 !important;
        border-radius: 6px !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
        color: #000;
        border: none;
        border-radius: 6px;
        font-weight: 700;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    
    .stButton > button:hover {
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
    }
    
    .status-success {
        background: rgba(0, 255, 136, 0.1);
        border-left: 3px solid #00ff88;
        color: #00ff88;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 13px;
    }
    
    .status-error {
        background: rgba(255, 107, 107, 0.1);
        border-left: 3px solid #ff6b6b;
        color: #ff6b6b;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 13px;
    }
    
    .label-small {
        font-size: 11px;
        color: #00d9ff;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
        display: block;
    }
    
    .stCheckbox > label {
        color: #e0e0e0 !important;
        font-size: 13px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

if "config" not in st.session_state:
    st.session_state.config = {
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_email": "",
        "smtp_password": "",
        "sender_name": "",
        "anonymous": False,
        "anon_name": "",
        "anon_email": "",
        "subject": "",
        "email_mode": "html",  # "html" or "text"
        "html_file": None,
        "text_content": "",
        "csv_file": None,
    }

# ============ SIDEBAR ============
with st.sidebar:
    # Branding
    st.markdown("""
    <div style="padding: 16px 0; margin-bottom: 24px; border-bottom: 1px solid #2a3f5f;">
        <div class="sidebar-brand">✉️</div>
        <div class="sidebar-title">MailForge</div>
        <div class="sidebar-version">v4.0</div>
    </div>
    """, unsafe_allow_html=True)
    
    # SEND Section
    st.markdown('<div class="sidebar-section-header">SEND</div>', unsafe_allow_html=True)
    if st.button("📧 Compose", use_container_width=True, key="btn_compose"):
        st.session_state.current_page = "compose"
    if st.button("🤖 AI Sending", use_container_width=True, key="btn_ai"):
        st.session_state.current_page = "ai_sending"
    if st.button("📊 Delivery", use_container_width=True, key="btn_delivery"):
        st.session_state.current_page = "delivery"
    
    # SERVERS Section
    st.markdown('<div class="sidebar-section-header">SERVERS</div>', unsafe_allow_html=True)
    if st.button("🔌 SMTP", use_container_width=True, key="btn_smtp"):
        st.session_state.current_page = "smtp"
    if st.button("📨 O365 Send", use_container_width=True, key="btn_o365"):
        st.session_state.current_page = "o365"
    if st.button("🔄 Proxies", use_container_width=True, key="btn_proxies"):
        st.session_state.current_page = "proxies"
    
    # VERIFY Section
    st.markdown('<div class="sidebar-section-header">VERIFY</div>', unsafe_allow_html=True)
    if st.button("✅ Email Validator", use_container_width=True, key="btn_validator"):
        st.session_state.current_page = "validator"
    if st.button("📧 Office 365", use_container_width=True, key="btn_o365_verify"):
        st.session_state.current_page = "o365_verify"
    if st.button("🛍️ Amazon", use_container_width=True, key="btn_amazon"):
        st.session_state.current_page = "amazon"
    
    # EXTRACT Section
    st.markdown('<div class="sidebar-section-header">EXTRACT</div>', unsafe_allow_html=True)
    if st.button("🔍 Lead Gen", use_container_width=True, key="btn_leadgen"):
        st.session_state.current_page = "leadgen"
    if st.button("📄 From Files", use_container_width=True, key="btn_files"):
        st.session_state.current_page = "from_files"
    if st.button("📬 IMAP Inbox", use_container_width=True, key="btn_imap"):
        st.session_state.current_page = "imap"
    if st.button("📦 O365 Box-to-Box", use_container_width=True, key="btn_box2box"):
        st.session_state.current_page = "box2box"
    if st.button("🔧 QR Tool", use_container_width=True, key="btn_qr"):
        st.session_state.current_page = "qr"
    
    # Bottom
    st.markdown('<div style="margin-top: 40px; border-top: 1px solid #2a3f5f; padding-top: 20px;">', unsafe_allow_html=True)
    if st.button("⏱️ History", use_container_width=True, key="btn_history"):
        st.session_state.current_page = "history"
    if st.button("❓ Show me around", use_container_width=True, key="btn_tour"):
        st.session_state.current_page = "tour"
    if st.button("🚪 Sign out", use_container_width=True, key="btn_signout"):
        st.session_state.current_page = "dashboard"
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Status
    st.markdown("""
    <div style="position: absolute; bottom: 20px; width: 90%; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #2a3f5f; padding-top: 12px;">
        <span style="display: inline-block; width: 8px; height: 8px; background: #00ff88; border-radius: 50%; margin-right: 6px; vertical-align: middle;"></span> Ready &nbsp; | &nbsp; 📊 Dashboard &nbsp; | &nbsp; 🔌 0 &nbsp; | &nbsp; 🌐 offline
    </div>
    """, unsafe_allow_html=True)

# ============ MAIN CONTENT ============

if st.session_state.current_page == "dashboard":
    st.markdown("# Welcome back")
    st.markdown('<div class="subtitle">Your infrastructure — at a glance</div>', unsafe_allow_html=True)
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">🔌</div>
            <div class="metric-value">0</div>
            <div class="metric-label">SMTP servers</div>
            <div class="metric-status">ready to send</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">🔗</div>
            <div class="metric-value">0</div>
            <div class="metric-label">Proxies</div>
            <div class="metric-status">in rotation</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">🌐</div>
            <div class="metric-value">unavailable</div>
            <div class="metric-label">Egress IP</div>
            <div class="metric-status">current outbound</div>
        </div>
        """, unsafe_allow_html=True)
    
    # SEND Section
    st.markdown('<div class="section-title">SEND</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("", key="card1"):
            st.session_state.current_page = "compose"
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">📧</div>
                <div class="feature-title">Compose & Send</div>
                <div class="feature-desc">Build and send campaigns</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI Sending</div>
                <div class="feature-desc">AI-powered campaigns</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">📊</div>
                <div class="feature-title">Delivery</div>
                <div class="feature-desc">Pacing and delays</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">🔌</div>
                <div class="feature-title">SMTP Servers</div>
                <div class="feature-desc">Manage sending servers</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">📨</div>
                <div class="feature-title">O365 Send</div>
                <div class="feature-desc">Graph API campaigns</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">🔄</div>
                <div class="feature-title">Proxies</div>
                <div class="feature-desc">HTTP/SOCKS rotation</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    # VERIFY Section
    st.markdown('<div class="section-title">VERIFY</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">✅</div>
                <div class="feature-title">Email Validator</div>
                <div class="feature-desc">MX, SMTP, spam trap</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">📧</div>
                <div class="feature-title">Office 365</div>
                <div class="feature-desc">O365 existence check</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">🛍️</div>
                <div class="feature-title">Amazon Verify</div>
                <div class="feature-desc">Seller account checker</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    # EXTRACT Section
    st.markdown('<div class="section-title">EXTRACT</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">🔍</div>
                <div class="feature-title">Lead Gen</div>
                <div class="feature-desc">Find business emails</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">📄</div>
                <div class="feature-title">From Files</div>
                <div class="feature-desc">PDF, DOCX, XLSX</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">📬</div>
                <div class="feature-title">IMAP Inbox</div>
                <div class="feature-desc">Harvest from mailbox</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">📦</div>
                <div class="feature-title">O365 Box-to-Box</div>
                <div class="feature-desc">Cookie-based import</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div>
                <div class="feature-icon">🔧</div>
                <div class="feature-title">QR Tool</div>
                <div class="feature-desc">Generate QR codes</div>
            </div>
            <div style="text-align: right; color: #666; font-size: 16px;">→</div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.current_page == "compose":
    st.markdown("# Compose & Send")
    st.markdown('<div class="subtitle">Build and send cold email campaigns</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ SMTP", "📝 TEMPLATE", "👁️ PREVIEW", "🚀 SEND"])
    
    with tab1:
        st.markdown('<div class="section-title">SMTP Server Connection</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<span class="label-small">SMTP Host</span>', unsafe_allow_html=True)
            st.session_state.config["smtp_host"] = st.text_input("Host", st.session_state.config["smtp_host"], placeholder="smtp.gmail.com", label_visibility="collapsed")
            
            st.markdown('<span class="label-small">SMTP Port</span>', unsafe_allow_html=True)
            st.session_state.config["smtp_port"] = st.number_input("Port", st.session_state.config["smtp_port"], label_visibility="collapsed")
        
        with col2:
            st.markdown('<span class="label-small">Email Address</span>', unsafe_allow_html=True)
            st.session_state.config["smtp_email"] = st.text_input("Email", st.session_state.config["smtp_email"], placeholder="your-email@gmail.com", label_visibility="collapsed")
            
            st.markdown('<span class="label-small">App Password</span>', unsafe_allow_html=True)
            st.session_state.config["smtp_password"] = st.text_input("Password", st.session_state.config["smtp_password"], type="password", placeholder="16-char app password", label_visibility="collapsed")
        
        st.markdown('<div class="section-title">Sender Identity</div>', unsafe_allow_html=True)
        
        st.session_state.config["anonymous"] = st.checkbox("🔒 Enable Anonymous Sending", st.session_state.config["anonymous"])
        
        if not st.session_state.config["anonymous"]:
            st.markdown('<span class="label-small">Display Name</span>', unsafe_allow_html=True)
            st.session_state.config["sender_name"] = st.text_input("Sender Name", st.session_state.config["sender_name"], placeholder="Your Name or Company", label_visibility="collapsed")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<span class="label-small">Anonymous Sender Name</span>', unsafe_allow_html=True)
                st.session_state.config["anon_name"] = st.text_input("Anon Name", st.session_state.config["anon_name"], placeholder="Display name", label_visibility="collapsed")
            with col2:
                st.markdown('<span class="label-small">Anonymous Sender Email</span>', unsafe_allow_html=True)
                st.session_state.config["anon_email"] = st.text_input("Anon Email", st.session_state.config["anon_email"], placeholder="sender@example.com", label_visibility="collapsed")
        
        st.markdown('<div class="section-title">Email Subject</div>', unsafe_allow_html=True)
        st.session_state.config["subject"] = st.text_area("Subject", st.session_state.config["subject"], placeholder="Hi {name}...", height=80, label_visibility="collapsed")
        
        if st.button("🔗 TEST SMTP CONNECTION", use_container_width=True):
            try:
                server = smtplib.SMTP(st.session_state.config["smtp_host"], st.session_state.config["smtp_port"], timeout=10)
                server.starttls()
                server.login(st.session_state.config["smtp_email"], st.session_state.config["smtp_password"])
                server.quit()
                st.markdown('<div class="status-success">✓ Connection successful!</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="status-error">✗ Failed: {str(e)}</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="section-title">Email Content Mode</div>', unsafe_allow_html=True)
        
        email_mode = st.radio("Choose email type:", ["📄 HTML Template", "✉️ Plain Text"], 
                             horizontal=True, label_visibility="collapsed",
                             index=0 if st.session_state.config["email_mode"] == "html" else 1)
        
        st.session_state.config["email_mode"] = "html" if email_mode == "📄 HTML Template" else "text"
        
        st.markdown('<div class="section-title">Email Content</div>', unsafe_allow_html=True)
        
        if st.session_state.config["email_mode"] == "html":
            st.markdown('<span class="label-small">HTML Template</span>', unsafe_allow_html=True)
            html_file = st.file_uploader("Upload HTML", type=["html", "htm"], key="html")
            if html_file:
                st.session_state.config["html_file"] = html_file.read().decode("utf-8")
                st.markdown('<div class="status-success">✓ HTML loaded</div>', unsafe_allow_html=True)
                with st.expander("👀 Preview HTML"):
                    st.code(st.session_state.config["html_file"][:300] + "...", language="html")
        else:
            st.markdown('<span class="label-small">Email Body (Plain Text)</span>', unsafe_allow_html=True)
            st.session_state.config["text_content"] = st.text_area(
                "Email Body",
                st.session_state.config["text_content"],
                placeholder="Enter your email message here...\n\nYou can use {variables} like {name}, {company}, {email}",
                height=200,
                label_visibility="collapsed"
            )
            if st.session_state.config["text_content"]:
                st.markdown('<div class="status-success">✓ Text content ready</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="section-title">Recipients</div>', unsafe_allow_html=True)
        st.markdown('<span class="label-small">CSV Recipients</span>', unsafe_allow_html=True)
        csv_file = st.file_uploader("Upload CSV", type=["csv"], key="csv")
        if csv_file:
            st.session_state.config["csv_file"] = pd.read_csv(csv_file)
            st.markdown(f'<div class="status-success">✓ CSV loaded ({len(st.session_state.config["csv_file"])} rows)</div>', unsafe_allow_html=True)
    
    with tab3:
        has_content = (st.session_state.config["html_file"] if st.session_state.config["email_mode"] == "html" else st.session_state.config["text_content"])
        
        if has_content and isinstance(st.session_state.config["csv_file"], pd.DataFrame):
            df = st.session_state.config["csv_file"]
            email_col = next((col for col in ['email', 'Email', 'EMAIL'] if col in df.columns), None)
            
            if email_col:
                selected = st.selectbox("Select recipient:", range(len(df)), format_func=lambda i: f"{df.iloc[i][email_col]}")
                row = df.iloc[selected]
                
                subject = st.session_state.config["subject"]
                
                for col in df.columns:
                    val = str(row[col]) if pd.notna(row[col]) else ""
                    subject = subject.replace(f"{{{col}}}", val)
                
                if st.session_state.config["anonymous"]:
                    from_display = f"{st.session_state.config['anon_name']} <{st.session_state.config['anon_email']}>"
                else:
                    from_display = f"{st.session_state.config['sender_name']} <{st.session_state.config['smtp_email']}>"
                
                st.markdown(f'<div style="background: #1a2a4a; padding: 12px; border-radius: 6px; border: 1px solid #2a3f5f; color: #00d9ff; font-weight: 600; margin-bottom: 8px;">From: {from_display}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background: #1a2a4a; padding: 12px; border-radius: 6px; border: 1px solid #2a3f5f; color: #00d9ff; font-weight: 600; margin-bottom: 16px;">Subject: {subject}</div>', unsafe_allow_html=True)
                
                if st.session_state.config["email_mode"] == "html":
                    html = st.session_state.config["html_file"]
                    for col in df.columns:
                        val = str(row[col]) if pd.notna(row[col]) else ""
                        html = html.replace(f"{{{col}}}", val)
                    st.components.v1.html(html, height=500, scrolling=True)
                else:
                    text_body = st.session_state.config["text_content"]
                    for col in df.columns:
                        val = str(row[col]) if pd.notna(row[col]) else ""
                        text_body = text_body.replace(f"{{{col}}}", val)
                    st.markdown(f'<div style="background: #1a2a4a; padding: 16px; border-radius: 6px; border: 1px solid #2a3f5f; color: #e0e0e0; font-family: monospace; white-space: pre-wrap; line-height: 1.6;">{text_body}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-error">✗ No email column in CSV</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-error">✗ Upload email content and CSV file first</div>', unsafe_allow_html=True)
    
    with tab4:
        has_content = (st.session_state.config["html_file"] if st.session_state.config["email_mode"] == "html" else st.session_state.config["text_content"])
        
        if has_content and isinstance(st.session_state.config["csv_file"], pd.DataFrame):
            df = st.session_state.config["csv_file"]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Recipients</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Status</div><div class="metric-value" style="color: #00ff88;">Ready</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Mode</div><div class="metric-value">Bulk</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Security</div><div class="metric-value" style="color: #00ff88;">TLS</div></div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                send_test = st.checkbox("Send test first", True)
                if send_test:
                    test_email = st.text_input("Test email:")
            with col2:
                delay = st.slider("Delay (sec)", 0, 5, 1)
            
            if st.button("🚀 LAUNCH CAMPAIGN", use_container_width=True):
                email_col = next((col for col in ['email', 'Email', 'EMAIL'] if col in df.columns), None)
                if not all([st.session_state.config["smtp_host"], st.session_state.config["smtp_email"], st.session_state.config["smtp_password"], st.session_state.config["subject"]]):
                    st.markdown('<div class="status-error">Complete SMTP config</div>', unsafe_allow_html=True)
                elif st.session_state.config["anonymous"] and not all([st.session_state.config["anon_name"], st.session_state.config["anon_email"]]):
                    st.markdown('<div class="status-error">Enter anonymous details</div>', unsafe_allow_html=True)
                elif not st.session_state.config["anonymous"] and not st.session_state.config["sender_name"]:
                    st.markdown('<div class="status-error">Enter sender name</div>', unsafe_allow_html=True)
                elif send_test and not test_email:
                    st.markdown('<div class="status-error">Enter test email</div>', unsafe_allow_html=True)
                elif not email_col:
                    st.markdown('<div class="status-error">No email column</div>', unsafe_allow_html=True)
                else:
                    progress = st.progress(0)
                    status = st.empty()
                    results = st.empty()
                    
                    sent = failed = 0
                    errors = []
                    
                    from_name = st.session_state.config["anon_name"] if st.session_state.config["anonymous"] else st.session_state.config["sender_name"]
                    from_email = st.session_state.config["anon_email"] if st.session_state.config["anonymous"] else st.session_state.config["smtp_email"]
                    
                    if send_test:
                        try:
                            server = smtplib.SMTP(st.session_state.config["smtp_host"], st.session_state.config["smtp_port"], timeout=10)
                            server.starttls()
                            server.login(st.session_state.config["smtp_email"], st.session_state.config["smtp_password"])
                            
                            msg = MIMEMultipart("alternative")
                            msg["Subject"] = st.session_state.config["subject"]
                            msg["From"] = f"{from_name} <{from_email}>"
                            msg["To"] = test_email
                            
                            if st.session_state.config["email_mode"] == "html":
                                msg.attach(MIMEText(st.session_state.config["html_file"], "html"))
                            else:
                                msg.attach(MIMEText(st.session_state.config["text_content"], "plain"))
                            
                            server.sendmail(st.session_state.config["smtp_email"], [test_email], msg.as_string())
                            server.quit()
                            status.markdown(f'<div class="status-success">✓ Test sent</div>', unsafe_allow_html=True)
                        except Exception as e:
                            status.markdown(f'<div class="status-error">✗ Test failed: {str(e)}</div>', unsafe_allow_html=True)
                            st.stop()
                    
                    for idx, row in df.iterrows():
                        recipient = row[email_col]
                        try:
                            subject = st.session_state.config["subject"]
                            
                            if st.session_state.config["email_mode"] == "html":
                                content = st.session_state.config["html_file"]
                                content_type = "html"
                            else:
                                content = st.session_state.config["text_content"]
                                content_type = "plain"
                            
                            for col in df.columns:
                                val = str(row[col]) if pd.notna(row[col]) else ""
                                content = content.replace(f"{{{col}}}", val)
                                subject = subject.replace(f"{{{col}}}", val)
                            
                            server = smtplib.SMTP(st.session_state.config["smtp_host"], st.session_state.config["smtp_port"], timeout=10)
                            server.starttls()
                            server.login(st.session_state.config["smtp_email"], st.session_state.config["smtp_password"])
                            
                            msg = MIMEMultipart("alternative")
                            msg["Subject"] = subject
                            msg["From"] = f"{from_name} <{from_email}>"
                            msg["To"] = recipient
                            msg.attach(MIMEText(content, content_type))
                            
                            server.sendmail(st.session_state.config["smtp_email"], [recipient], msg.as_string())
                            server.quit()
                            sent += 1
                        except Exception as e:
                            failed += 1
                            errors.append(f"Row {idx+1}: {str(e)}")
                        
                        progress.progress((idx + 1) / len(df))
                        status.text(f"Sent: {sent} | Failed: {failed}")
                        if delay > 0:
                            time.sleep(delay)
                    
                    progress.empty()
                    status.empty()
                    with results.container():
                        st.markdown('<div class="status-success">✓ COMPLETE</div>', unsafe_allow_html=True)
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.markdown(f'<div class="metric-card"><div class="metric-label">Sent</div><div class="metric-value" style="color: #00ff88;">{sent}</div></div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f'<div class="metric-card"><div class="metric-label">Failed</div><div class="metric-value" style="color: #ff6b6b;">{failed}</div></div>', unsafe_allow_html=True)
                        with col3:
                            rate = (sent / len(df)) * 100 if len(df) > 0 else 0
                            st.markdown(f'<div class="metric-card"><div class="metric-label">Success</div><div class="metric-value">{rate:.1f}%</div></div>', unsafe_allow_html=True)
                        with col4:
                            st.markdown(f'<div class="metric-card"><div class="metric-label">Total</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)

else:
    st.info(f"📍 {st.session_state.current_page.upper()}")
