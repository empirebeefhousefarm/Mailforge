import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import sqlite3
from datetime import datetime
import hashlib
import re

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
    
    .metric-card {
        background: linear-gradient(135deg, #1a2a4a 0%, #0f1628 100%);
        border: 1px solid #2a3f5f;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #00d9ff;
        margin: 8px 0;
    }
    
    .metric-label {
        font-size: 12px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .feature-card {
        background: linear-gradient(135deg, rgba(26, 42, 74, 0.8) 0%, rgba(15, 22, 40, 0.8) 100%);
        border: 1px solid #2a3f5f;
        border-radius: 10px;
        padding: 20px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .feature-card:hover {
        border-color: #00d9ff;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.2);
    }
    
    .section-title {
        font-size: 12px;
        font-weight: 700;
        color: #a0a0a0;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin: 24px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #2a3f5f;
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
    
    .status-warning {
        background: rgba(255, 215, 0, 0.1);
        border-left: 3px solid #ffd700;
        color: #ffd700;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 13px;
    }
    
    .status-admin {
        background: rgba(128, 0, 128, 0.1);
        border-left: 3px solid #bb00ff;
        color: #bb00ff;
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
    
    h1 {
        color: #e0e0e0 !important;
        font-size: 36px !important;
        font-weight: 700 !important;
    }
    
    .subtitle {
        color: #888 !important;
        font-size: 14px !important;
        margin: 8px 0 20px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============ DATABASE SETUP ============
def init_db():
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        created_at TIMESTAMP
    )''')
    
    # SMTP profiles table
    c.execute('''CREATE TABLE IF NOT EXISTS smtp_profiles (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        profile_name TEXT,
        smtp_host TEXT,
        smtp_port INTEGER,
        smtp_email TEXT,
        smtp_password TEXT,
        sender_name TEXT,
        created_at TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # Campaign history table
    c.execute('''CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        subject TEXT,
        sent_count INTEGER,
        failed_count INTEGER,
        total_count INTEGER,
        success_rate REAL,
        email_type TEXT,
        created_at TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # Admin settings table
    c.execute('''CREATE TABLE IF NOT EXISTS admin_settings (
        id INTEGER PRIMARY KEY,
        setting_key TEXT UNIQUE,
        setting_value TEXT,
        updated_at TIMESTAMP
    )''')
    
    # Initialize access code if doesn't exist
    c.execute("INSERT OR IGNORE INTO admin_settings (setting_key, setting_value, updated_at) VALUES (?, ?, ?)",
             ("access_code", "272727", datetime.now()))
    
    conn.commit()
    conn.close()

init_db()

# ============ AUTH FUNCTIONS ============
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    try:
        conn = sqlite3.connect("mailforge.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                 (username, hash_password(password), datetime.now()))
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    except Exception as e:
        return False, str(e)

def login_user(username, password):
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", 
             (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_by_id(user_id):
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def get_all_users():
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    c.execute("SELECT id, username, created_at FROM users ORDER BY created_at DESC")
    users = c.fetchall()
    conn.close()
    return users

def get_access_code():
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    c.execute("SELECT setting_value FROM admin_settings WHERE setting_key = ?", ("access_code",))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "272727"

def update_access_code(new_code):
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    c.execute("UPDATE admin_settings SET setting_value = ?, updated_at = ? WHERE setting_key = ?",
             (new_code, datetime.now(), "access_code"))
    conn.commit()
    conn.close()

# ============ SMTP PROFILE FUNCTIONS ============
def save_smtp_profile(user_id, profile_name, smtp_host, smtp_port, smtp_email, smtp_password, sender_name):
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    c.execute('''INSERT INTO smtp_profiles (user_id, profile_name, smtp_host, smtp_port, smtp_email, smtp_password, sender_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
             (user_id, profile_name, smtp_host, smtp_port, smtp_email, smtp_password, sender_name, datetime.now()))
    conn.commit()
    conn.close()

def get_user_smtp_profiles(user_id):
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    c.execute("SELECT id, profile_name, smtp_host, smtp_port, smtp_email, smtp_password, sender_name FROM smtp_profiles WHERE user_id = ? ORDER BY created_at DESC",
             (user_id,))
    profiles = c.fetchall()
    conn.close()
    return profiles

# ============ CAMPAIGN HISTORY ============
def save_campaign(user_id, subject, sent, failed, total, email_type):
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    success_rate = (sent / total * 100) if total > 0 else 0
    c.execute('''INSERT INTO campaigns (user_id, subject, sent_count, failed_count, total_count, success_rate, email_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
             (user_id, subject, sent, failed, total, success_rate, email_type, datetime.now()))
    conn.commit()
    conn.close()

def get_user_campaigns(user_id, limit=10):
    conn = sqlite3.connect("mailforge.db")
    c = conn.cursor()
    c.execute('''SELECT subject, sent_count, failed_count, total_count, success_rate, email_type, created_at 
                FROM campaigns WHERE user_id = ? ORDER BY created_at DESC LIMIT ?''',
             (user_id, limit))
    campaigns = c.fetchall()
    conn.close()
    return campaigns

# ============ EMAIL VALIDATION ============
def validate_emails(emails_text):
    email_list = []
    
    if "," in emails_text:
        email_list = [e.strip() for e in emails_text.split(",") if e.strip()]
    else:
        email_list = [e.strip() for e in emails_text.split("\n") if e.strip()]
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    valid_emails = []
    invalid_emails = []
    
    for email in email_list:
        if re.match(email_pattern, email):
            valid_emails.append(email)
        else:
            invalid_emails.append(email)
    
    duplicates = [e for e in set(valid_emails) if valid_emails.count(e) > 1]
    unique_emails = list(set(valid_emails))
    
    return unique_emails, duplicates, invalid_emails

# ============ INITIALIZE SESSION ============
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

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
        "email_mode": "html",
        "html_file": None,
        "text_content": "",
        "recipient_mode": "upload",
        "csv_file": None,
        "pasted_emails": "",
        "current_server": None,
    }

# ============ LOGIN/REGISTER PAGE ============
if not st.session_state.user_id:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# MailForge Pro")
        st.markdown('<div class="subtitle">Professional Cold Email Campaign Manager</div>', unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab_login:
            st.markdown('<div class="section-title">Sign In</div>', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")
            
            if st.button("🔓 LOGIN", use_container_width=True, key="login_btn"):
                if username == "Dylan" and password == "Segun$45.":
                    st.session_state.user_id = -1
                    st.session_state.is_admin = True
                    st.markdown('<div class="status-admin">✓ Admin logged in!</div>', unsafe_allow_html=True)
                    st.rerun()
                elif username and password:
                    user_id = login_user(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.is_admin = False
                        st.markdown('<div class="status-success">✓ Login successful!</div>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown('<div class="status-error">✗ Invalid username or password</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-error">✗ Fill in all fields</div>', unsafe_allow_html=True)
        
        with tab_register:
            st.markdown('<div class="section-title">Create Account</div>', unsafe_allow_html=True)
            
            st.markdown('<span class="label-small">🔑 Access Code</span>', unsafe_allow_html=True)
            access_code = st.text_input("Access Code", type="password", placeholder="Enter access code", label_visibility="collapsed", key="access_code")
            
            st.markdown('<span class="label-small">Username</span>', unsafe_allow_html=True)
            new_username = st.text_input("Username", placeholder="Choose username", label_visibility="collapsed", key="reg_username")
            
            st.markdown('<span class="label-small">Password</span>', unsafe_allow_html=True)
            new_password = st.text_input("Password", type="password", placeholder="Choose password", label_visibility="collapsed", key="reg_password")
            
            st.markdown('<span class="label-small">Confirm Password</span>', unsafe_allow_html=True)
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password", label_visibility="collapsed", key="reg_confirm")
            
            if st.button("✍️ CREATE ACCOUNT", use_container_width=True, key="register_btn"):
                current_access_code = get_access_code()
                
                if not all([access_code, new_username, new_password, confirm_password]):
                    st.markdown('<div class="status-error">✗ Fill in all fields</div>', unsafe_allow_html=True)
                elif access_code != current_access_code:
                    st.markdown('<div class="status-error">✗ Invalid access code</div>', unsafe_allow_html=True)
                elif new_password != confirm_password:
                    st.markdown('<div class="status-error">✗ Passwords do not match</div>', unsafe_allow_html=True)
                elif len(new_password) < 6:
                    st.markdown('<div class="status-error">✗ Password must be at least 6 characters</div>', unsafe_allow_html=True)
                else:
                    success, message = register_user(new_username, new_password)
                    if success:
                        st.markdown(f'<div class="status-success">✓ {message}</div>', unsafe_allow_html=True)
                        st.info("Now go to Login tab and sign in!")
                    else:
                        st.markdown(f'<div class="status-error">✗ {message}</div>', unsafe_allow_html=True)

else:
    # ============ LOGGED IN - MAIN APP ============
    user_info = get_user_by_id(st.session_state.user_id) if not st.session_state.is_admin else ("Admin",)
    
    with st.sidebar:
        if st.session_state.is_admin:
            st.markdown(f"""
            <div style="padding: 16px 0; margin-bottom: 24px; border-bottom: 1px solid #bb00ff;">
                <div style="font-weight: 700; color: #bb00ff; font-size: 14px;">⚙️ ADMIN PANEL</div>
                <div style="font-size: 12px; color: #bb00ff; margin-top: 8px;">Dylan</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("👥 All Users", use_container_width=True):
                st.session_state.current_page = "admin_users"
            if st.button("🔑 Access Code", use_container_width=True):
                st.session_state.current_page = "admin_access"
            if st.button("📧 MailForge", use_container_width=True):
                st.session_state.current_page = "dashboard"
        else:
            st.markdown(f"""
            <div style="padding: 16px 0; margin-bottom: 24px; border-bottom: 1px solid #2a3f5f;">
                <div style="font-weight: 700; color: #e0e0e0; font-size: 14px;">MailForge Pro</div>
                <div style="font-size: 12px; color: #00d9ff; margin-top: 8px;">👤 {user_info[0]}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.current_page = "dashboard"
            if st.button("📧 Compose", use_container_width=True):
                st.session_state.current_page = "compose"
            if st.button("🖥️ Servers", use_container_width=True):
                st.session_state.current_page = "profiles"
            if st.button("📊 History", use_container_width=True):
                st.session_state.current_page = "history"
        
        st.markdown('<div style="margin-top: 40px; border-top: 1px solid #2a3f5f; padding-top: 20px;">', unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.is_admin = False
            st.session_state.current_page = "login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ============ ADMIN PAGES ============
    if st.session_state.is_admin:
        if st.session_state.current_page == "admin_users":
            st.markdown("# 👥 All Users")
            st.markdown('<div class="subtitle">Manage all MailForge accounts</div>', unsafe_allow_html=True)
            
            users = get_all_users()
            
            if users:
                st.markdown('<div class="section-title">User Accounts</div>', unsafe_allow_html=True)
                
                for user in users:
                    user_id, username, created_at = user
                    campaigns = get_user_campaigns(user_id, limit=100)
                    profiles = get_user_smtp_profiles(user_id)
                    
                    total_sent = sum(c[1] for c in campaigns) if campaigns else 0
                    
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"**👤 {username}**")
                            st.caption(created_at.split('.')[0])
                        
                        with col2:
                            st.metric("Campaigns", len(campaigns))
                        
                        with col3:
                            st.metric("Sent", total_sent)
                        
                        with col4:
                            st.metric("Servers", len(profiles))
                        
                        with col5:
                            if st.button("View", key=f"view_{user_id}", use_container_width=True):
                                st.session_state.current_page = "admin_user_detail"
                                st.session_state.admin_viewing_user = user_id
                                st.rerun()
                        
                        st.divider()
                
                st.markdown(f'<div class="status-admin">⚙️ Total Users: {len(users)}</div>', unsafe_allow_html=True)
            else:
                st.info("No users yet")
        
        elif st.session_state.current_page == "admin_user_detail":
            user_id = st.session_state.admin_viewing_user
            user_info = get_user_by_id(user_id)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"# 👤 {user_info[0]}")
            with col2:
                if st.button("← Back"):
                    st.session_state.current_page = "admin_users"
                    st.rerun()
            
            tab1, tab2, tab3 = st.tabs(["📊 History", "🖥️ Servers", "📋 Details"])
            
            with tab1:
                st.markdown('<div class="section-title">Campaign History</div>', unsafe_allow_html=True)
                campaigns = get_user_campaigns(user_id, limit=50)
                
                if campaigns:
                    for idx, campaign in enumerate(campaigns):
                        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                        with col1:
                            st.write(f"**{campaign[0]}**")
                            st.caption(campaign[6].split('.')[0])
                        with col2:
                            st.metric("Sent", campaign[1])
                        with col3:
                            st.metric("Failed", campaign[2])
                        with col4:
                            st.metric("Total", campaign[3])
                        with col5:
                            st.metric("Rate", f"{campaign[4]:.1f}%")
                        st.divider()
                else:
                    st.info("No campaigns yet")
            
            with tab2:
                st.markdown('<div class="section-title">SMTP Servers</div>', unsafe_allow_html=True)
                profiles = get_user_smtp_profiles(user_id)
                
                if profiles:
                    for idx, profile in enumerate(profiles):
                        with st.container():
                            st.markdown(f"**Server {idx+1}** • {profile[1]}")
                            st.caption(f"Email: {profile[4]}")
                            st.caption(f"Host: {profile[2]}:{profile[3]}")
                            st.caption(f"Sender: {profile[6]}")
                            st.divider()
                else:
                    st.info("No servers configured")
            
            with tab3:
                st.markdown('<div class="section-title">Account Details</div>', unsafe_allow_html=True)
                st.write(f"**Username:** {user_info[0]}")
                st.write(f"**Account Created:** {}")
                total_campaigns = len(get_user_campaigns(user_id, limit=100))
                total_servers = len(get_user_smtp_profiles(user_id))
                st.write(f"**Total Campaigns:** {total_campaigns}")
                st.write(f"**Total Servers:** {total_servers}")
        
        elif st.session_state.current_page == "admin_access":
            st.markdown("# 🔑 Access Code Management")
            st.markdown('<div class="subtitle">Manage registration access codes</div>', unsafe_allow_html=True)
            
            current_code = get_access_code()
            
            st.markdown('<div class="section-title">Current Access Code</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="status-admin">Current Code: **{current_code}**</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="section-title">Change Access Code</div>', unsafe_allow_html=True)
            
            new_code = st.text_input("New Access Code", placeholder="Enter new code", type="password")
            
            if st.button("🔐 UPDATE CODE", use_container_width=True):
                if not new_code:
                    st.markdown('<div class="status-error">✗ Enter a new code</div>', unsafe_allow_html=True)
                elif len(new_code) < 4:
                    st.markdown('<div class="status-error">✗ Code must be at least 4 characters</div>', unsafe_allow_html=True)
                elif new_code == current_code:
                    st.markdown('<div class="status-error">✗ New code must be different</div>', unsafe_allow_html=True)
                else:
                    update_access_code(new_code)
                    st.markdown(f'<div class="status-success">✓ Access code updated to: {new_code}</div>', unsafe_allow_html=True)
    
    # ============ USER PAGES ============
    else:
        if st.session_state.current_page == "dashboard":
            st.markdown("# Welcome back")
            st.markdown(f'<div class="subtitle">Your infrastructure — at a glance</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            campaigns = get_user_campaigns(st.session_state.user_id, limit=100)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 28px; margin-bottom: 12px;">📧</div>
                    <div class="metric-value">{len(campaigns)}</div>
                    <div class="metric-label">Total Campaigns</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                total_sent = sum(c[1] for c in campaigns) if campaigns else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 28px; margin-bottom: 12px;">✓</div>
                    <div class="metric-value">{total_sent}</div>
                    <div class="metric-label">Emails Sent</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                avg_rate = (sum(c[4] for c in campaigns) / len(campaigns)) if campaigns else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 28px; margin-bottom: 12px;">📊</div>
                    <div class="metric-value">{avg_rate:.1f}%</div>
                    <div class="metric-label">Avg Success Rate</div>
                </div>
                """, unsafe_allow_html=True)
        
        elif st.session_state.current_page == "compose":
            st.markdown("# Compose & Send")
            st.markdown('<div class="subtitle">Build and send cold email campaigns</div>', unsafe_allow_html=True)
            
            tab1, tab2, tab3, tab4 = st.tabs(["⚙️ SMTP", "📝 TEMPLATE", "👁️ PREVIEW", "🚀 SEND"])
            
            with tab1:
                st.markdown('<div class="section-title">Quick Load Server</div>', unsafe_allow_html=True)
                
                profiles = get_user_smtp_profiles(st.session_state.user_id)
                if profiles:
                    server_options = [f"Server {idx+1} - {p[1]}" for idx, p in enumerate(profiles)]
                    selected_option = st.selectbox("Select SMTP server:", [""] + server_options)
                    
                    if selected_option:
                        server_idx = int(selected_option.split()[1]) - 1
                        profile = profiles[server_idx]
                        st.session_state.config["smtp_host"] = profile[2]
                        st.session_state.config["smtp_port"] = profile[3]
                        st.session_state.config["smtp_email"] = profile[4]
                        st.session_state.config["smtp_password"] = profile[5]
                        st.session_state.config["sender_name"] = profile[6]
                        st.session_state.config["current_server"] = profile[0]
                        st.markdown(f'<div class="status-success">✓ {selected_option} loaded</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="section-title">SMTP Configuration</div>', unsafe_allow_html=True)
                
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
                    st.session_state.config["smtp_password"] = st.text_input("Password", st.session_state.config["smtp_password"], type="password", label_visibility="collapsed")
                
                st.markdown('<div class="section-title">Save This Server</div>', unsafe_allow_html=True)
                
                profile_name = st.text_input("Server name (optional):", placeholder="e.g., Gmail Account 1")
                
                if st.button("💾 SAVE SERVER", use_container_width=True):
                    if profile_name:
                        save_smtp_profile(st.session_state.user_id, profile_name, st.session_state.config["smtp_host"],
                                        st.session_state.config["smtp_port"], st.session_state.config["smtp_email"],
                                        st.session_state.config["smtp_password"], st.session_state.config["sender_name"])
                        st.markdown('<div class="status-success">✓ Server saved</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="section-title">Sender Identity</div>', unsafe_allow_html=True)
                st.session_state.config["anonymous"] = st.checkbox("🔒 Anonymous Sending", st.session_state.config["anonymous"])
                
                if not st.session_state.config["anonymous"]:
                    st.markdown('<span class="label-small">Display Name</span>', unsafe_allow_html=True)
                    st.session_state.config["sender_name"] = st.text_input("Name", st.session_state.config["sender_name"], label_visibility="collapsed")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown('<span class="label-small">Anon Name</span>', unsafe_allow_html=True)
                        st.session_state.config["anon_name"] = st.text_input("Name", st.session_state.config["anon_name"], label_visibility="collapsed")
                    with col2:
                        st.markdown('<span class="label-small">Anon Email</span>', unsafe_allow_html=True)
                        st.session_state.config["anon_email"] = st.text_input("Email", st.session_state.config["anon_email"], label_visibility="collapsed")
                
                st.markdown('<div class="section-title">Subject Line</div>', unsafe_allow_html=True)
                st.session_state.config["subject"] = st.text_area("Subject", st.session_state.config["subject"], height=80, label_visibility="collapsed")
                
                if st.button("🔗 TEST CONNECTION", use_container_width=True):
                    try:
                        server = smtplib.SMTP(st.session_state.config["smtp_host"], st.session_state.config["smtp_port"], timeout=10)
                        server.starttls()
                        server.login(st.session_state.config["smtp_email"], st.session_state.config["smtp_password"])
                        server.quit()
                        st.markdown('<div class="status-success">✓ Connection successful</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="status-error">✗ Failed: {str(e)}</div>', unsafe_allow_html=True)
            
            with tab2:
                email_mode = st.radio("Email type:", ["📄 HTML", "✉️ Text"], horizontal=True, label_visibility="collapsed")
                st.session_state.config["email_mode"] = "html" if email_mode == "📄 HTML" else "text"
                
                if st.session_state.config["email_mode"] == "html":
                    st.markdown('<span class="label-small">HTML Template</span>', unsafe_allow_html=True)
                    html_file = st.file_uploader("Upload HTML", type=["html", "htm"], key="html")
                    if html_file:
                        st.session_state.config["html_file"] = html_file.read().decode("utf-8")
                        st.markdown('<div class="status-success">✓ HTML loaded</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="label-small">Email Body</span>', unsafe_allow_html=True)
                    st.session_state.config["text_content"] = st.text_area("Body", st.session_state.config["text_content"], height=200, label_visibility="collapsed")
                
                st.markdown('<div class="section-title">Recipients</div>', unsafe_allow_html=True)
                
                recipient_mode = st.radio("Recipients:", ["📤 CSV", "📋 Paste"], horizontal=True, label_visibility="collapsed")
                st.session_state.config["recipient_mode"] = "upload" if recipient_mode == "📤 CSV" else "paste"
                
                if st.session_state.config["recipient_mode"] == "upload":
                    csv_file = st.file_uploader("Upload CSV", type=["csv"], key="csv")
                    if csv_file:
                        st.session_state.config["csv_file"] = pd.read_csv(csv_file)
                        st.markdown(f'<div class="status-success">✓ CSV loaded</div>', unsafe_allow_html=True)
                else:
                    st.session_state.config["pasted_emails"] = st.text_area("Paste emails:", st.session_state.config["pasted_emails"], height=150, label_visibility="collapsed")
                    
                    if st.session_state.config["pasted_emails"]:
                        unique_emails, duplicates, invalid = validate_emails(st.session_state.config["pasted_emails"])
                        
                        st.markdown(f'<div class="status-success">✓ {len(unique_emails)} valid email(s)</div>', unsafe_allow_html=True)
                        
                        if duplicates:
                            st.markdown(f'<div class="status-warning">⚠ {len(duplicates)} duplicate(s)</div>', unsafe_allow_html=True)
                        
                        if invalid:
                            st.markdown(f'<div class="status-error">✗ {len(invalid)} invalid email(s)</div>', unsafe_allow_html=True)
                        
                        st.session_state.config["csv_file"] = pd.DataFrame({"email": unique_emails})
            
            with tab3:
                has_content = (st.session_state.config["html_file"] if st.session_state.config["email_mode"] == "html" else st.session_state.config["text_content"])
                
                if has_content and isinstance(st.session_state.config["csv_file"], pd.DataFrame):
                    df = st.session_state.config["csv_file"]
                    selected = st.selectbox("Preview:", range(len(df)), format_func=lambda i: f"{df.iloc[i]['email']}")
                    row = df.iloc[selected]
                    
                    subject = st.session_state.config["subject"]
                    for col in df.columns:
                        val = str(row[col]) if pd.notna(row[col]) else ""
                        subject = subject.replace(f"{{{col}}}", val)
                    
                    from_display = (f"{st.session_state.config['anon_name']} <{st.session_state.config['anon_email']}>" 
                                   if st.session_state.config["anonymous"] 
                                   else f"{st.session_state.config['sender_name']} <{st.session_state.config['smtp_email']}>")
                    
                    st.markdown(f'<div style="background: #1a2a4a; padding: 12px; border-radius: 6px; color: #00d9ff; font-weight: 600; margin-bottom: 8px;">From: {from_display}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="background: #1a2a4a; padding: 12px; border-radius: 6px; color: #00d9ff; font-weight: 600; margin-bottom: 16px;">Subject: {subject}</div>', unsafe_allow_html=True)
                    
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
                        st.markdown(f'<div style="background: #1a2a4a; padding: 16px; border-radius: 6px; white-space: pre-wrap;">{text_body}</div>', unsafe_allow_html=True)
            
            with tab4:
                has_content = (st.session_state.config["html_file"] if st.session_state.config["email_mode"] == "html" else st.session_state.config["text_content"])
                
                if has_content and isinstance(st.session_state.config["csv_file"], pd.DataFrame):
                    df = st.session_state.config["csv_file"]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f'<div class="metric-card"><div class="metric-label">Recipients</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
                    
                    profiles = get_user_smtp_profiles(st.session_state.user_id)
                    st.markdown('<div class="section-title">Server Settings</div>', unsafe_allow_html=True)
                    
                    use_rotation = False
                    if profiles and len(profiles) > 1:
                        use_rotation = st.checkbox("🔄 Rotate through servers", False)
                        if use_rotation:
                            st.markdown(f'<div class="status-success">✓ Will rotate through {len(profiles)} server(s)</div>', unsafe_allow_html=True)
                    elif profiles and len(profiles) == 1:
                        st.markdown('<div class="status-success">✓ 1 server loaded</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="status-warning">⚠ Add servers to enable rotation</div>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        send_test = st.checkbox("Test first", True)
                        if send_test:
                            test_email = st.text_input("Test email:")
                    with col2:
                        delay = st.slider("Delay (sec)", 0, 5, 1)
                    
                    if st.button("🚀 LAUNCH CAMPAIGN", use_container_width=True):
                        if not all([st.session_state.config["smtp_host"], st.session_state.config["smtp_email"]]):
                            st.markdown('<div class="status-error">✗ Complete SMTP config</div>', unsafe_allow_html=True)
                        else:
                            progress = st.progress(0)
                            status = st.empty()
                            results = st.empty()
                            
                            sent = failed = 0
                            
                            from_name = (st.session_state.config["anon_name"] if st.session_state.config["anonymous"] 
                                       else st.session_state.config["sender_name"])
                            from_email = (st.session_state.config["anon_email"] if st.session_state.config["anonymous"] 
                                        else st.session_state.config["smtp_email"])
                            
                            server_list = profiles if use_rotation and profiles else None
                            
                            if send_test and test_email:
                                try:
                                    server = smtplib.SMTP(st.session_state.config["smtp_host"], st.session_state.config["smtp_port"], timeout=10)
                                    server.starttls()
                                    server.login(st.session_state.config["smtp_email"], st.session_state.config["smtp_password"])
                                    msg = MIMEMultipart("alternative")
                                    msg["Subject"] = st.session_state.config["subject"]
                                    msg["From"] = f"{from_name} <{from_email}>"
                                    msg["To"] = test_email
                                    content_type = "html" if st.session_state.config["email_mode"] == "html" else "plain"
                                    content = st.session_state.config["html_file"] if st.session_state.config["email_mode"] == "html" else st.session_state.config["text_content"]
                                    msg.attach(MIMEText(content, content_type))
                                    server.sendmail(st.session_state.config["smtp_email"], [test_email], msg.as_string())
                                    server.quit()
                                    status.markdown(f'<div class="status-success">✓ Test sent</div>', unsafe_allow_html=True)
                                except Exception as e:
                                    status.markdown(f'<div class="status-error">✗ Test failed: {str(e)}</div>', unsafe_allow_html=True)
                                    st.stop()
                            
                            for idx, row in df.iterrows():
                                recipient = row["email"]
                                
                                if server_list:
                                    current_profile = server_list[idx % len(server_list)]
                                    smtp_host = current_profile[2]
                                    smtp_port = current_profile[3]
                                    smtp_email = current_profile[4]
                                    smtp_password = current_profile[5]
                                    current_server_num = (idx % len(server_list)) + 1
                                else:
                                    smtp_host = st.session_state.config["smtp_host"]
                                    smtp_port = st.session_state.config["smtp_port"]
                                    smtp_email = st.session_state.config["smtp_email"]
                                    smtp_password = st.session_state.config["smtp_password"]
                                    current_server_num = 1
                                
                                try:
                                    content = st.session_state.config["html_file"] if st.session_state.config["email_mode"] == "html" else st.session_state.config["text_content"]
                                    subject = st.session_state.config["subject"]
                                    
                                    for col in df.columns:
                                        val = str(row[col]) if pd.notna(row[col]) else ""
                                        content = content.replace(f"{{{col}}}", val)
                                        subject = subject.replace(f"{{{col}}}", val)
                                    
                                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                                    server.starttls()
                                    server.login(smtp_email, smtp_password)
                                    msg = MIMEMultipart("alternative")
                                    msg["Subject"] = subject
                                    msg["From"] = f"{from_name} <{from_email}>"
                                    msg["To"] = recipient
                                    content_type = "html" if st.session_state.config["email_mode"] == "html" else "plain"
                                    msg.attach(MIMEText(content, content_type))
                                    server.sendmail(smtp_email, [recipient], msg.as_string())
                                    server.quit()
                                    sent += 1
                                except:
                                    failed += 1
                                
                                progress.progress((idx + 1) / len(df))
                                if server_list:
                                    status.text(f"Sent: {sent} | Failed: {failed} | Using: Server {current_server_num}")
                                else:
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
                            
                            save_campaign(st.session_state.user_id, st.session_state.config["subject"], sent, failed, len(df), st.session_state.config["email_mode"])
        
        elif st.session_state.current_page == "profiles":
            st.markdown("# 🖥️ Servers")
            st.markdown('<div class="subtitle">Manage your saved SMTP configurations</div>', unsafe_allow_html=True)
            
            profiles = get_user_smtp_profiles(st.session_state.user_id)
            
            if profiles:
                st.markdown('<div class="section-title">Your Servers</div>', unsafe_allow_html=True)
                
                for idx, profile in enumerate(profiles):
                    with st.container():
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.markdown(f"**Server {idx+1}** • {profile[1]}")
                            st.caption(f"{profile[4]} • {profile[2]}:{profile[3]}")
                        with col2:
                            st.caption(f"Sender: {profile[6]}")
                        with col3:
                            if st.button(f"Load", key=f"load_{profile[0]}", use_container_width=True):
                                st.session_state.config["smtp_host"] = profile[2]
                                st.session_state.config["smtp_port"] = profile[3]
                                st.session_state.config["smtp_email"] = profile[4]
                                st.session_state.config["smtp_password"] = profile[5]
                                st.session_state.config["sender_name"] = profile[6]
                                st.markdown(f'<div class="status-success">✓ Server {idx+1} loaded</div>', unsafe_allow_html=True)
                        st.divider()
                
                st.markdown(f'<div class="status-success">✓ {len(profiles)} server(s) configured</div>', unsafe_allow_html=True)
            else:
                st.info("No servers yet. Create one in Compose → SMTP → Save Server")
        
        elif st.session_state.current_page == "history":
            st.markdown("# 📊 Campaign History")
            st.markdown('<div class="subtitle">Your past email campaigns</div>', unsafe_allow_html=True)
            
            campaigns = get_user_campaigns(st.session_state.user_id)
            
            if campaigns:
                for campaign in campaigns:
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                        with col1:
                            st.write(f"**{campaign[0]}**")
                            st.caption(campaign[6].split('.')[0])
                        with col2:
                            st.metric("Sent", campaign[1])
                        with col3:
                            st.metric("Failed", campaign[2])
                        with col4:
                            st.metric("Total", campaign[3])
                        with col5:
                            st.metric("Rate", f"{campaign[4]:.1f}%")
                        st.divider()
            else:
                st.info("No campaigns yet")
