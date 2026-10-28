import hashlib
import io
import os
import re
import secrets
import smtplib
import psycopg2
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="MailForge Pro",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ CONSTANTS ============
def get_secret(name, default=None):
    """Read a value from Streamlit Secrets (or .streamlit/secrets.toml when running locally)."""
    try:
        value = st.secrets[name]
        return value if value not in ("", None) else default
    except Exception:
        return default


ADMIN_USERNAME = get_secret("ADMIN_USERNAME", "Dylan")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD")
DATABASE_URL = get_secret("DATABASE_URL")
DEFAULT_ACCESS_CODE = get_secret("ACCESS_CODE", "272727")

if not ADMIN_PASSWORD or not DATABASE_URL:
    st.error("Missing secrets. Add ADMIN_PASSWORD and DATABASE_URL in the app's Secrets settings.")
    st.stop()

EMAIL_PATTERN = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
EMAIL_RE = re.compile(EMAIL_PATTERN)

# ============ THEME ============
st.markdown("""
<style>
    * { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; }
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
        border: 1px solid #2a3f5f; border-radius: 10px; padding: 20px; margin: 10px 0;
    }
    .metric-value { font-size: 24px; font-weight: 800; color: #00d9ff; margin: 8px 0; }
    .metric-label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
    .section-title {
        font-size: 12px; font-weight: 700; color: #a0a0a0; text-transform: uppercase;
        letter-spacing: 1.2px; margin: 24px 0 16px 0; padding-bottom: 8px;
        border-bottom: 1px solid #2a3f5f;
    }
    .sidebar-section-header {
        padding: 12px 0 6px 0; color: #a0a0a0; font-size: 10px; font-weight: 700;
        text-transform: uppercase; letter-spacing: 1.2px; margin-top: 16px;
        border-top: 1px solid #2a3f5f;
    }
    .stButton > button {
        background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
        color: #000; border: none; border-radius: 6px; font-weight: 700;
        font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px;
    }
    .status-success {
        background: rgba(0, 255, 136, 0.1); border-left: 3px solid #00ff88; color: #00ff88;
        padding: 12px 16px; border-radius: 4px; font-size: 13px; margin: 8px 0;
    }
    .status-error {
        background: rgba(255, 107, 107, 0.1); border-left: 3px solid #ff6b6b; color: #ff6b6b;
        padding: 12px 16px; border-radius: 4px; font-size: 13px; margin: 8px 0;
    }
    .status-warning {
        background: rgba(255, 215, 0, 0.1); border-left: 3px solid #ffd700; color: #ffd700;
        padding: 12px 16px; border-radius: 4px; font-size: 13px; margin: 8px 0;
    }
    .status-admin {
        background: rgba(187, 0, 255, 0.1); border-left: 3px solid #bb00ff; color: #bb00ff;
        padding: 12px 16px; border-radius: 4px; font-size: 13px; margin: 8px 0;
    }
    .label-small {
        font-size: 11px; color: #00d9ff; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.8px; margin-bottom: 8px; display: block;
    }
    h1 { color: #e0e0e0 !important; font-size: 36px !important; font-weight: 700 !important; }
    .subtitle { color: #888 !important; font-size: 14px !important; margin: 8px 0 20px 0 !important; }
</style>
""", unsafe_allow_html=True)


# ============ DATABASE (Supabase / PostgreSQL) ============
def run(sql, params=(), fetch=None):
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if fetch == "one":
                    return cur.fetchone()
                if fetch == "all":
                    return cur.fetchall()
                return None
    finally:
        conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@st.cache_resource
def init_db():
    run("""CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW())""")
    run("""CREATE TABLE IF NOT EXISTS smtp_profiles (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        profile_name TEXT, smtp_host TEXT, smtp_port INTEGER, smtp_email TEXT,
        smtp_password TEXT, sender_name TEXT,
        created_at TIMESTAMP DEFAULT NOW())""")
    run("""CREATE TABLE IF NOT EXISTS campaigns (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        subject TEXT, sent_count INTEGER, failed_count INTEGER, total_count INTEGER,
        success_rate REAL, email_type TEXT,
        created_at TIMESTAMP DEFAULT NOW())""")
    run("""CREATE TABLE IF NOT EXISTS admin_settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT,
        updated_at TIMESTAMP DEFAULT NOW())""")
    run("""CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER,
        is_admin INTEGER,
        created_at TIMESTAMP DEFAULT NOW())""")
    run("INSERT INTO admin_settings (setting_key, setting_value) VALUES ('access_code', %s) "
        "ON CONFLICT (setting_key) DO NOTHING", (DEFAULT_ACCESS_CODE,))
    run("INSERT INTO users (username, password) VALUES (%s, %s) "
        "ON CONFLICT (username) DO NOTHING", (ADMIN_USERNAME, hash_password(ADMIN_PASSWORD)))


init_db()


# ============ ACCOUNTS ============
def register_user(username, password):
    username = username.strip()
    if not re.match(r'^[A-Za-z0-9_.-]{3,30}$', username):
        return False, "Username must be 3-30 characters (letters, numbers, _ . -)"
    if username.lower() == ADMIN_USERNAME.lower():
        return False, "That username is not available"
    try:
        run("INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hash_password(password)))
        return True, "Account created successfully!"
    except psycopg2.IntegrityError:
        return False, "Username already exists!"


def login_user(username, password):
    row = run("SELECT id FROM users WHERE username = %s AND password = %s",
              (username, hash_password(password)), fetch="one")
    return row[0] if row else None


def get_admin_id():
    return run("SELECT id FROM users WHERE username = %s", (ADMIN_USERNAME,), fetch="one")[0]


def get_user(user_id):
    return run("SELECT username, created_at FROM users WHERE id = %s", (user_id,), fetch="one")


def get_all_users():
    return run("SELECT id, username, created_at FROM users ORDER BY created_at DESC", fetch="all")


def reset_password(user_id, new_password):
    run("UPDATE users SET password = %s WHERE id = %s", (hash_password(new_password), user_id))


def delete_user(user_id):
    run("DELETE FROM sessions WHERE user_id = %s", (user_id,))
    run("DELETE FROM campaigns WHERE user_id = %s", (user_id,))
    run("DELETE FROM smtp_profiles WHERE user_id = %s", (user_id,))
    run("DELETE FROM users WHERE id = %s", (user_id,))


# ============ LOGIN SESSIONS (stay logged in until Sign Out) ============
def create_session(user_id, is_admin):
    token = secrets.token_urlsafe(32)
    run("INSERT INTO sessions (token, user_id, is_admin) VALUES (%s, %s, %s)",
        (token, user_id, int(is_admin)))
    return token


def get_session(token):
    return run("SELECT user_id, is_admin FROM sessions WHERE token = %s", (token,), fetch="one")


def delete_session(token):
    run("DELETE FROM sessions WHERE token = %s", (token,))


def logout_non_admin_sessions():
    run("DELETE FROM sessions WHERE is_admin = 0")


def start_login(user_id, is_admin):
    token = create_session(user_id, is_admin)
    st.session_state.user_id = user_id
    st.session_state.is_admin = is_admin
    st.session_state.current_page = "dashboard"
    st.query_params["s"] = token


def sign_out():
    token = st.query_params.get("s")
    if token:
        delete_session(token)
    st.query_params.clear()
    st.session_state.user_id = None
    st.session_state.is_admin = False
    st.session_state.current_page = "dashboard"


# ============ ACCESS CODE ============
def get_access_code():
    row = run("SELECT setting_value FROM admin_settings WHERE setting_key = 'access_code'", fetch="one")
    return row[0] if row else DEFAULT_ACCESS_CODE


def update_access_code(new_code):
    run("UPDATE admin_settings SET setting_value = %s, updated_at = NOW() WHERE setting_key = 'access_code'",
        (new_code,))


# ============ SMTP SERVERS ============
def save_smtp_profile(user_id, name, host, port, email, password, sender):
    run("""INSERT INTO smtp_profiles (user_id, profile_name, smtp_host, smtp_port,
           smtp_email, smtp_password, sender_name)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (user_id, name, host, int(port), email, password, sender))


def get_user_smtp_profiles(user_id):
    return run("""SELECT id, profile_name, smtp_host, smtp_port, smtp_email,
                  smtp_password, sender_name FROM smtp_profiles
                  WHERE user_id = %s ORDER BY id ASC""", (user_id,), fetch="all")


def delete_smtp_profile(profile_id):
    run("DELETE FROM smtp_profiles WHERE id = %s", (profile_id,))


# ============ CAMPAIGN HISTORY ============
def save_campaign(user_id, subject, sent, failed, total, email_type):
    rate = (sent / total * 100) if total > 0 else 0
    run("""INSERT INTO campaigns (user_id, subject, sent_count, failed_count, total_count,
           success_rate, email_type) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (user_id, subject, sent, failed, total, rate, email_type))


def get_user_campaigns(user_id, limit=100):
    return run("""SELECT subject, sent_count, failed_count, total_count, success_rate,
                  email_type, created_at FROM campaigns WHERE user_id = %s
                  ORDER BY created_at DESC LIMIT %s""", (user_id, limit), fetch="all")


# ============ RECIPIENT VALIDATION ============
def validate_emails(text):
    """Pasted list: returns (valid unique, duplicates, invalid)."""
    raw = [e.strip().lower() for e in re.split(r'[\s,;]+', text) if e.strip()]
    valid, invalid, dupes, seen = [], [], [], set()
    for e in raw:
        if not EMAIL_RE.match(e):
            invalid.append(e)
        elif e in seen:
            if e not in dupes:
                dupes.append(e)
        else:
            seen.add(e)
            valid.append(e)
    return valid, dupes, invalid


def load_csv(raw_bytes):
    """CSV upload: returns (clean dataframe, duplicates removed, invalid removed)."""
    df = pd.read_csv(io.BytesIO(raw_bytes))
    df.columns = [str(c).strip() for c in df.columns]
    col = next((c for c in df.columns if c.lower() == "email"), None)
    if col is None:
        raise ValueError("No 'email' column found in this CSV")
    df = df.rename(columns={col: "email"})
    df["email"] = df["email"].astype(str).str.strip().str.lower()
    dup = df.duplicated(subset="email", keep="first")
    bad = ~df["email"].str.match(EMAIL_PATTERN)
    clean = df[~dup & ~bad].reset_index(drop=True)
    return clean, int(dup.sum()), int(bad.sum())


def fill(text, row):
    """Replace {column} placeholders with values from one recipient row."""
    if row is None or not text:
        return text
    for col in row.index:
        val = "" if pd.isna(row[col]) else str(row[col])
        text = text.replace("{" + str(col) + "}", val)
    return text


def open_smtp(host, port, login, password):
    """Open and log in to an SMTP server. Port 465 uses SSL, other ports use STARTTLS."""
    port = int(port)
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=15)
        server.ehlo()
    else:
        server = smtplib.SMTP(host, port, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
    server.login(login, password.replace(" ", ""))
    return server


def send_one(host, port, login, password, from_header, to, subject, body, ctype):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_header
    msg["To"] = to
    msg.attach(MIMEText(body, "html" if ctype == "html" else "plain", "utf-8"))
    server = open_smtp(host, port, login, password)
    try:
        server.sendmail(login, [to], msg.as_string())
    finally:
        try:
            server.quit()
        except Exception:
            pass


def card(icon, value, label, color="#00d9ff"):
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 28px; margin-bottom: 12px;">{icon}</div>
        <div class="metric-value" style="color: {color};">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)



# ============ SESSION STATE ============
for key, default in {
    "user_id": None,
    "is_admin": False,
    "current_page": "dashboard",
    "admin_viewing_user": None,
    "csv_df": None,
    "html_upload": "",
    "f_host": "", "f_port": 587, "f_email": "", "f_password": "", "f_sender": "",
    "f_anon": False, "f_anon_name": "", "f_anon_email": "", "f_subject": "",
    "f_fmt": "✉️ Plain Text", "f_body": "", "f_html": "", "f_html_src": "✍️ Write / paste HTML",
    "f_rec_mode": "📤 CSV", "f_pasted": "",
}.items():
    st.session_state.setdefault(key, default)

# Restore login from the session token in the URL (keeps you logged in across refreshes)
if st.session_state.user_id is None:
    token = st.query_params.get("s")
    if token:
        sess = get_session(token)
        if sess:
            st.session_state.user_id = sess[0]
            st.session_state.is_admin = bool(sess[1])


def load_server_into_form(p):
    st.session_state.f_host = p[2]
    st.session_state.f_port = int(p[3])
    st.session_state.f_email = p[4]
    st.session_state.f_password = p[5]
    st.session_state.f_sender = p[6] or ""


def get_mode():
    return "html" if st.session_state.f_fmt == "🌐 HTML" else "text"


def current_body():
    if get_mode() == "text":
        return st.session_state.f_body
    if st.session_state.f_html_src == "📁 Upload .html file":
        return st.session_state.html_upload
    return st.session_state.f_html


# ============ LOGIN / REGISTER ============
if st.session_state.user_id is None:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("# MailForge Pro")
        st.markdown('<div class="subtitle">Professional Cold Email Campaign Manager</div>', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

        with tab_login:
            st.markdown('<div class="section-title">Sign In</div>', unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")
            if st.button("🔓 LOGIN", use_container_width=True, key="login_btn"):
                if not username or not password:
                    st.markdown('<div class="status-error">✗ Fill in all fields</div>', unsafe_allow_html=True)
                elif username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    start_login(get_admin_id(), True)
                    st.rerun()
                else:
                    uid = login_user(username, password)
                    if uid:
                        start_login(uid, False)
                        st.rerun()
                    else:
                        st.markdown('<div class="status-error">✗ Invalid username or password</div>', unsafe_allow_html=True)

        with tab_register:
            st.markdown('<div class="section-title">Create Account</div>', unsafe_allow_html=True)
            st.markdown('<span class="label-small">🔑 Access Code</span>', unsafe_allow_html=True)
            access_code = st.text_input("Access Code", type="password", placeholder="Enter access code",
                                        label_visibility="collapsed", key="access_code")
            st.markdown('<span class="label-small">Username</span>', unsafe_allow_html=True)
            new_username = st.text_input("Username", placeholder="Choose username",
                                         label_visibility="collapsed", key="reg_username")
            st.markdown('<span class="label-small">Password</span>', unsafe_allow_html=True)
            new_password = st.text_input("Password", type="password", placeholder="Choose password",
                                         label_visibility="collapsed", key="reg_password")
            st.markdown('<span class="label-small">Confirm Password</span>', unsafe_allow_html=True)
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password",
                                             label_visibility="collapsed", key="reg_confirm")

            if st.button("✍️ CREATE ACCOUNT", use_container_width=True, key="register_btn"):
                if not all([access_code, new_username, new_password, confirm_password]):
                    st.markdown('<div class="status-error">✗ Fill in all fields</div>', unsafe_allow_html=True)
                elif access_code != get_access_code():
                    st.markdown('<div class="status-error">✗ Invalid access code</div>', unsafe_allow_html=True)
                elif new_password != confirm_password:
                    st.markdown('<div class="status-error">✗ Passwords do not match</div>', unsafe_allow_html=True)
                elif len(new_password) < 6:
                    st.markdown('<div class="status-error">✗ Password must be at least 6 characters</div>', unsafe_allow_html=True)
                else:
                    ok, msg = register_user(new_username, new_password)
                    if ok:
                        st.markdown(f'<div class="status-success">✓ {msg}</div>', unsafe_allow_html=True)
                        st.info("Now go to the Login tab and sign in.")
                    else:
                        st.markdown(f'<div class="status-error">✗ {msg}</div>', unsafe_allow_html=True)

# ============ LOGGED IN ============
else:
    uid = st.session_state.user_id
    is_admin = st.session_state.is_admin
    display_name = "Dylan (Admin)" if is_admin else get_user(uid)[0]

    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 12px 0 16px 0; border-bottom: 1px solid #2a3f5f;">
            <div style="font-weight: 700; color: #e0e0e0; font-size: 14px;">MailForge Pro</div>
            <div style="font-size: 12px; color: #00d9ff; margin-top: 8px;">👤 {display_name}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section-header">MailForge</div>', unsafe_allow_html=True)
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
        if st.button("📧 Compose", use_container_width=True):
            st.session_state.current_page = "compose"
        if st.button("🖥️ Servers", use_container_width=True):
            st.session_state.current_page = "profiles"
        if st.button("📊 History", use_container_width=True):
            st.session_state.current_page = "history"

        if is_admin:
            st.markdown('<div class="sidebar-section-header">Admin</div>', unsafe_allow_html=True)
            if st.button("👥 All Users", use_container_width=True):
                st.session_state.current_page = "admin_users"
            if st.button("🔑 Access Code", use_container_width=True):
                st.session_state.current_page = "admin_access"

        st.markdown('<div class="sidebar-section-header">Account</div>', unsafe_allow_html=True)
        if st.button("🔐 My Account", use_container_width=True):
            st.session_state.current_page = "account"
        if st.button("🚪 Sign Out", use_container_width=True):
            sign_out()
            st.rerun()

    page = st.session_state.current_page

    # ----- Admin pages -----
    def render_admin_users():
        st.markdown("# 👥 All Users")
        st.markdown('<div class="subtitle">Every MailForge account, with its activity</div>', unsafe_allow_html=True)
        users = get_all_users()
        if not users:
            st.info("No users yet")
            return
        st.markdown(f'<div class="status-admin">⚙️ Total accounts: {len(users)}</div>', unsafe_allow_html=True)
        for user_id, uname, created in users:
            camps = get_user_campaigns(user_id, 1000)
            profiles = get_user_smtp_profiles(user_id)
            c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
            with c1:
                tag = " (admin)" if uname == ADMIN_USERNAME else ""
                st.markdown(f"**👤 {uname}{tag}**")
                st.caption(str(created)[:19])
            with c2:
                st.metric("Campaigns", len(camps))
            with c3:
                st.metric("Sent", sum(c[1] for c in camps))
            with c4:
                st.metric("Servers", len(profiles))
            with c5:
                if st.button("View", key=f"view_{user_id}", use_container_width=True):
                    st.session_state.admin_viewing_user = user_id
                    st.session_state.current_page = "admin_user_detail"
                    st.rerun()
            st.divider()

    def render_admin_user_detail():
        uid_view = st.session_state.admin_viewing_user
        info = get_user(uid_view) if uid_view else None
        if info is None:
            st.warning("This account no longer exists.")
            if st.button("← Back to users"):
                st.session_state.current_page = "admin_users"
                st.rerun()
            return
        uname, created = info

        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"# 👤 {uname}")
        with c2:
            if st.button("← Back", use_container_width=True):
                st.session_state.current_page = "admin_users"
                st.rerun()

        t1, t2, t3 = st.tabs(["📊 History", "🖥️ Servers", "⚙️ Account"])

        with t1:
            camps = get_user_campaigns(uid_view, 200)
            if not camps:
                st.info("No campaigns yet")
            for camp in camps:
                a, b, c, d, e = st.columns([2, 1, 1, 1, 1])
                with a:
                    st.write(f"**{camp[0]}**")
                    st.caption(str(camp[6])[:19])
                b.metric("Sent", camp[1])
                c.metric("Failed", camp[2])
                d.metric("Total", camp[3])
                e.metric("Rate", f"{camp[4]:.1f}%")
                st.divider()

        with t2:
            profiles = get_user_smtp_profiles(uid_view)
            if not profiles:
                st.info("No servers configured")
            for idx, p in enumerate(profiles):
                a, b = st.columns([4, 1])
                with a:
                    st.markdown(f"**Server {idx+1}** • {p[1]}")
                    st.caption(f"Email: {p[4]}  |  Host: {p[2]}:{p[3]}  |  Sender: {p[6]}")
                with b:
                    if st.button("Delete", key=f"admdel_{p[0]}", use_container_width=True):
                        delete_smtp_profile(p[0])
                        st.rerun()
                st.divider()

        with t3:
            st.markdown(f"**Username:** {uname}")
            st.markdown(f"**Created:** {str(created)[:19]}")
            st.markdown(f"**Campaigns:** {len(get_user_campaigns(uid_view, 1000))}")
            st.markdown(f"**Servers:** {len(get_user_smtp_profiles(uid_view))}")

            st.markdown('<div class="section-title">Reset Password</div>', unsafe_allow_html=True)
            new_pw = st.text_input("New password", type="password", key="admin_reset_pw")
            if st.button("🔐 RESET PASSWORD", key="admin_reset_btn"):
                if len(new_pw) < 6:
                    st.markdown('<div class="status-error">✗ Password must be at least 6 characters</div>', unsafe_allow_html=True)
                else:
                    reset_password(uid_view, new_pw)
                    st.markdown('<div class="status-success">✓ Password updated</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-title">Danger Zone</div>', unsafe_allow_html=True)
            if uname == ADMIN_USERNAME:
                st.markdown('<div class="status-warning">The admin account cannot be deleted.</div>', unsafe_allow_html=True)
            else:
                confirm = st.checkbox("I understand this permanently deletes the account, servers and history")
                if st.button("🗑️ DELETE ACCOUNT", disabled=not confirm, key="admin_delete_btn"):
                    delete_user(uid_view)
                    st.session_state.admin_viewing_user = None
                    st.session_state.current_page = "admin_users"
                    st.rerun()

    def render_admin_access():
        st.markdown("# 🔑 Access Code")
        st.markdown('<div class="subtitle">Control who can create new accounts</div>', unsafe_allow_html=True)
        current = get_access_code()
        st.markdown(f'<div class="status-admin">Current access code: <b>{current}</b></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Change Access Code</div>', unsafe_allow_html=True)
        new_code = st.text_input("New access code", type="password", key="new_code")
        if st.button("🔐 UPDATE CODE", key="update_code_btn"):
            if len(new_code) < 4:
                st.markdown('<div class="status-error">✗ Code must be at least 4 characters</div>', unsafe_allow_html=True)
            elif new_code == current:
                st.markdown('<div class="status-error">✗ New code must be different</div>', unsafe_allow_html=True)
            else:
                update_access_code(new_code)
                st.markdown('<div class="status-success">✓ Access code updated. Existing accounts are not affected.</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Force Logout</div>', unsafe_allow_html=True)
        st.caption("Signs out every user except you. They must log in again.")
        if st.button("⛔ LOG OUT ALL USERS", key="logout_all_btn"):
            logout_non_admin_sessions()
            st.markdown('<div class="status-success">✓ All other users have been signed out</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Database</div>', unsafe_allow_html=True)
        st.caption("Database: Supabase (PostgreSQL)")

    # ----- User pages (also available to admin) -----
    def render_dashboard():
        st.markdown("# Welcome back")
        st.markdown('<div class="subtitle">Your infrastructure — at a glance</div>', unsafe_allow_html=True)
        camps = get_user_campaigns(uid, 1000)
        profiles = get_user_smtp_profiles(uid)
        avg = (sum(c[4] for c in camps) / len(camps)) if camps else 0
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            card("📧", len(camps), "Campaigns")
        with c2:
            card("✓", sum(c[1] for c in camps), "Emails sent", "#00ff88")
        with c3:
            card("📊", f"{avg:.1f}%", "Avg success rate")
        with c4:
            card("🖥️", len(profiles), "SMTP servers")

    def render_servers():
        st.markdown("# 🖥️ Servers")
        st.markdown('<div class="subtitle">Your saved SMTP servers</div>', unsafe_allow_html=True)
        profiles = get_user_smtp_profiles(uid)
        if not profiles:
            st.info("No servers yet. Add one in Compose → SMTP.")
            return
        for idx, p in enumerate(profiles):
            a, b, c = st.columns([3, 2, 1])
            with a:
                st.markdown(f"**Server {idx+1}** • {p[1]}")
                st.caption(f"{p[4]} • {p[2]}:{p[3]}")
            with b:
                st.caption(f"Sender: {p[6]}")
            with c:
                if st.button("Delete", key=f"del_{p[0]}", use_container_width=True):
                    delete_smtp_profile(p[0])
                    st.rerun()
            st.divider()
        st.markdown(f'<div class="status-success">✓ {len(profiles)} server(s) configured</div>', unsafe_allow_html=True)

    def render_history():
        st.markdown("# 📊 Campaign History")
        st.markdown('<div class="subtitle">Your past campaigns</div>', unsafe_allow_html=True)
        camps = get_user_campaigns(uid, 200)
        if not camps:
            st.info("No campaigns yet")
            return
        for camp in camps:
            a, b, c, d, e = st.columns([2, 1, 1, 1, 1])
            with a:
                st.write(f"**{camp[0]}**")
                st.caption(str(camp[6])[:19])
            b.metric("Sent", camp[1])
            c.metric("Failed", camp[2])
            d.metric("Total", camp[3])
            e.metric("Rate", f"{camp[4]:.1f}%")
            st.divider()

    def render_compose():
        st.markdown("# Compose & Send")
        st.markdown('<div class="subtitle">Build and send cold email campaigns</div>', unsafe_allow_html=True)
        tab1, tab2, tab3, tab4 = st.tabs(["⚙️ SMTP", "📝 TEMPLATE", "👁️ PREVIEW", "🚀 SEND"])

        # ---------- SMTP ----------
        with tab1:
            st.markdown('<div class="section-title">Load a Saved Server</div>', unsafe_allow_html=True)
            profiles = get_user_smtp_profiles(uid)
            if profiles:
                labels = [f"Server {i+1} - {p[1]}" for i, p in enumerate(profiles)]
                choice = st.selectbox("Saved servers", labels, key="load_choice")
                st.button("📥 LOAD THIS SERVER", use_container_width=True,
                          on_click=load_server_into_form, args=(profiles[labels.index(choice)],))
            else:
                st.info("No saved servers yet. Fill in the form below and save it.")

            st.markdown('<div class="section-title">SMTP Configuration</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<span class="label-small">SMTP Host</span>', unsafe_allow_html=True)
                st.text_input("Host", key="f_host", placeholder="smtp.gmail.com", label_visibility="collapsed")
                st.markdown('<span class="label-small">SMTP Port</span>', unsafe_allow_html=True)
                st.number_input("Port", key="f_port", min_value=1, max_value=65535, label_visibility="collapsed")
            with c2:
                st.markdown('<span class="label-small">Email Address</span>', unsafe_allow_html=True)
                st.text_input("Email", key="f_email", placeholder="you@gmail.com", label_visibility="collapsed")
                st.markdown('<span class="label-small">App Password</span>', unsafe_allow_html=True)
                st.text_input("Password", key="f_password", type="password", label_visibility="collapsed")

            s1, s2 = st.columns(2)
            with s1:
                if st.button("🔗 TEST CONNECTION", use_container_width=True):
                    try:
                        srv = open_smtp(st.session_state.f_host, st.session_state.f_port,
                                        st.session_state.f_email, st.session_state.f_password)
                        srv.quit()
                        st.markdown('<div class="status-success">✓ Connection successful</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="status-error">✗ Failed: {e}</div>', unsafe_allow_html=True)
            with s2:
                save_name = st.text_input("Server name", placeholder="e.g., Gmail Account 1", key="f_save_name")
                if st.button("💾 SAVE THIS SERVER", use_container_width=True):
                    if not save_name.strip():
                        st.markdown('<div class="status-error">✗ Give this server a name first</div>', unsafe_allow_html=True)
                    elif not st.session_state.f_host or not st.session_state.f_email:
                        st.markdown('<div class="status-error">✗ Fill in host and email first</div>', unsafe_allow_html=True)
                    else:
                        save_smtp_profile(uid, save_name.strip(), st.session_state.f_host,
                                          st.session_state.f_port, st.session_state.f_email,
                                          st.session_state.f_password, st.session_state.f_sender)
                        st.markdown('<div class="status-success">✓ Server saved</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-title">Sender Identity</div>', unsafe_allow_html=True)
            st.checkbox("🔒 Anonymous Sending", key="f_anon")
            if not st.session_state.f_anon:
                st.markdown('<span class="label-small">Display Name</span>', unsafe_allow_html=True)
                st.text_input("Name", key="f_sender", label_visibility="collapsed")
            else:
                a1, a2 = st.columns(2)
                with a1:
                    st.markdown('<span class="label-small">Anon Name</span>', unsafe_allow_html=True)
                    st.text_input("Anon name", key="f_anon_name", label_visibility="collapsed")
                with a2:
                    st.markdown('<span class="label-small">Anon Email</span>', unsafe_allow_html=True)
                    st.text_input("Anon email", key="f_anon_email", label_visibility="collapsed")

            st.markdown('<div class="section-title">Subject Line</div>', unsafe_allow_html=True)
            st.text_area("Subject", key="f_subject", height=80, label_visibility="collapsed",
                         placeholder="Hi {name}, quick question")

        # ---------- TEMPLATE ----------
        with tab2:
            st.markdown('<div class="section-title">Email Format</div>', unsafe_allow_html=True)
            st.radio("Format", ["✉️ Plain Text", "🌐 HTML"], horizontal=True, key="f_fmt",
                     label_visibility="collapsed")

            sample = None
            rec_now = st.session_state.csv_df
            if rec_now is not None and len(rec_now) > 0:
                sample = rec_now.iloc[0]

            if get_mode() == "text":
                st.markdown('<span class="label-small">Email Body</span>', unsafe_allow_html=True)
                st.text_area("Body", key="f_body", height=260, label_visibility="collapsed",
                             placeholder="Hi {name},\n\nI noticed {company} is doing great work...\n\nBest,\nYour name")
                st.caption("Use {column} placeholders, e.g. {name}, {company}. They are filled from your recipient list.")
            else:
                st.markdown('<div class="section-title">HTML Source</div>', unsafe_allow_html=True)
                st.radio("HTML source", ["✍️ Write / paste HTML", "📁 Upload .html file"], horizontal=True,
                         key="f_html_src", label_visibility="collapsed")
                if st.session_state.f_html_src == "✍️ Write / paste HTML":
                    st.text_area("HTML code", key="f_html", height=320, label_visibility="collapsed",
                                 placeholder="<html>\n  <body>\n    <p>Hi {name},</p>\n  </body>\n</html>")
                else:
                    up = st.file_uploader("Upload HTML", type=["html", "htm"], key="f_html_file")
                    if up is not None:
                        st.session_state.html_upload = up.getvalue().decode("utf-8", errors="replace")
                        st.markdown('<div class="status-success">✓ HTML file loaded</div>', unsafe_allow_html=True)

                html_now = current_body()
                if html_now.strip():
                    st.markdown('<div class="section-title">Live Preview</div>', unsafe_allow_html=True)
                    if sample is not None:
                        st.caption(f"Previewing with first recipient: {sample.get('email', '')}")
                    components.html(fill(html_now, sample), height=420, scrolling=True)

            st.markdown('<div class="section-title">Recipients</div>', unsafe_allow_html=True)
            st.radio("Recipients", ["📤 CSV", "📋 Paste"], horizontal=True, key="f_rec_mode",
                     label_visibility="collapsed")

            if st.session_state.f_rec_mode == "📤 CSV":
                up_csv = st.file_uploader("Upload CSV (needs an 'email' column)", type=["csv"], key="f_csv")
                if up_csv is not None:
                    try:
                        df, dup_count, bad_count = load_csv(up_csv.getvalue())
                        st.session_state.csv_df = df
                        st.markdown(f'<div class="status-success">✓ {len(df)} valid recipient(s) ready</div>', unsafe_allow_html=True)
                        if dup_count:
                            st.markdown(f'<div class="status-warning">⚠ {dup_count} duplicate email(s) removed</div>', unsafe_allow_html=True)
                        if bad_count:
                            st.markdown(f'<div class="status-error">✗ {bad_count} invalid email(s) removed</div>', unsafe_allow_html=True)
                    except ValueError as e:
                        st.session_state.csv_df = None
                        st.markdown(f'<div class="status-error">✗ {e}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.session_state.csv_df = None
                        st.markdown(f'<div class="status-error">✗ Could not read CSV: {e}</div>', unsafe_allow_html=True)
                else:
                    st.session_state.csv_df = None
            else:
                st.text_area("Paste emails", key="f_pasted", height=150, label_visibility="collapsed",
                             placeholder="john@example.com\njane@example.com\n\nOne per line, or separated by commas")
                if st.session_state.f_pasted.strip():
                    valid, dupes, invalid = validate_emails(st.session_state.f_pasted)
                    st.markdown(f'<div class="status-success">✓ {len(valid)} valid email(s)</div>', unsafe_allow_html=True)
                    if dupes:
                        st.markdown(f'<div class="status-warning">⚠ {len(dupes)} duplicate(s) removed: {", ".join(dupes[:3])}</div>', unsafe_allow_html=True)
                    if invalid:
                        st.markdown(f'<div class="status-error">✗ {len(invalid)} invalid: {", ".join(invalid[:3])}</div>', unsafe_allow_html=True)
                    st.session_state.csv_df = pd.DataFrame({"email": valid}) if valid else None
                else:
                    st.session_state.csv_df = None

        # ---------- PREVIEW ----------
        with tab3:
            rec = st.session_state.csv_df
            body = current_body()
            if not body.strip() or rec is None or len(rec) == 0:
                st.markdown('<div class="status-error">✗ Add email content and recipients in the TEMPLATE tab first</div>', unsafe_allow_html=True)
            else:
                idx = st.selectbox("Recipient", range(len(rec)), format_func=lambda i: rec.iloc[i]["email"])
                row = rec.iloc[idx]
                subject = fill(st.session_state.f_subject, row)
                anon = st.session_state.f_anon
                from_display = (f"{st.session_state.f_anon_name} <{st.session_state.f_anon_email}>" if anon
                                else f"{st.session_state.f_sender} <{st.session_state.f_email}>")
                st.markdown(f'<div class="metric-card"><b>From:</b> {from_display}<br><b>Subject:</b> {subject}</div>', unsafe_allow_html=True)
                if get_mode() == "html":
                    components.html(fill(body, row), height=520, scrolling=True)
                else:
                    st.markdown(f'<div class="metric-card" style="white-space: pre-wrap;">{fill(body, row)}</div>', unsafe_allow_html=True)

        # ---------- SEND ----------
        with tab4:
            rec = st.session_state.csv_df
            body = current_body()
            if not body.strip() or rec is None or len(rec) == 0:
                st.markdown('<div class="status-error">✗ Add email content and recipients in the TEMPLATE tab first</div>', unsafe_allow_html=True)
            else:
                c1, c2, c3 = st.columns(3)
                with c1:
                    card("👥", len(rec), "Recipients")
                with c2:
                    card("🖥️", max(len(profiles), 1), "Servers available", "#00ff88")
                with c3:
                    card("📨", "HTML" if get_mode() == "html" else "Text", "Format")

                rotate = False
                if len(profiles) >= 2:
                    rotate = st.checkbox("🔄 Rotate through all saved servers", key="f_rotate")
                    if rotate:
                        st.markdown(f'<div class="status-success">✓ Sending will rotate across {len(profiles)} servers</div>', unsafe_allow_html=True)
                else:
                    st.caption("Save 2+ servers to enable rotation.")

                d1, d2 = st.columns(2)
                with d1:
                    send_test = st.checkbox("Send a test email first", value=True, key="f_send_test")
                    test_email = st.text_input("Test email", key="f_test_email") if send_test else ""
                with d2:
                    delay = st.slider("Delay between emails (sec)", 0, 5, 1, key="f_delay")

                if st.button("🚀 LAUNCH CAMPAIGN", use_container_width=True):
                    host = st.session_state.f_host
                    login_email = st.session_state.f_email
                    password = st.session_state.f_password
                    anon = st.session_state.f_anon
                    anon_name = st.session_state.f_anon_name
                    anon_email = st.session_state.f_anon_email
                    sender = st.session_state.f_sender
                    subject_tpl = st.session_state.f_subject
                    ctype = get_mode()

                    problems = []
                    if not host or not login_email or not password:
                        problems.append("Fill in the SMTP host, email and password (SMTP tab)")
                    if not subject_tpl.strip():
                        problems.append("Enter a subject line")
                    if anon and not (anon_name and anon_email):
                        problems.append("Enter the anonymous name and email")
                    if not anon and not sender:
                        problems.append("Enter a display name")
                    if send_test and not test_email:
                        problems.append("Enter a test email address or untick 'Send a test email first'")
                    for p in problems:
                        st.markdown(f'<div class="status-error">✗ {p}</div>', unsafe_allow_html=True)

                    if not problems:
                        if rotate:
                            servers = [(p[2], p[3], p[4], p[5]) for p in profiles]
                        else:
                            servers = [(host, st.session_state.f_port, login_email, password)]

                        def make_from(srv):
                            return formataddr((anon_name, anon_email)) if anon else formataddr((sender, srv[2]))

                        test_ok = True
                        if send_test:
                            try:
                                row0 = rec.iloc[0]
                                send_one(servers[0][0], servers[0][1], servers[0][2], servers[0][3],
                                         make_from(servers[0]), test_email,
                                         fill(subject_tpl, row0), fill(body, row0), ctype)
                                st.markdown('<div class="status-success">✓ Test email sent</div>', unsafe_allow_html=True)
                            except Exception as e:
                                test_ok = False
                                st.markdown(f'<div class="status-error">✗ Test failed: {e}</div>', unsafe_allow_html=True)

                        if test_ok:
                            progress = st.progress(0)
                            status = st.empty()
                            sent, failed, errors = 0, 0, []
                            for i in range(len(rec)):
                                row = rec.iloc[i]
                                srv = servers[i % len(servers)]
                                try:
                                    send_one(srv[0], srv[1], srv[2], srv[3], make_from(srv), row["email"],
                                             fill(subject_tpl, row), fill(body, row), ctype)
                                    sent += 1
                                except Exception as e:
                                    failed += 1
                                    if len(errors) < 10:
                                        errors.append(f"{row['email']}: {e}")
                                progress.progress((i + 1) / len(rec))
                                if rotate:
                                    status.text(f"Sent: {sent} | Failed: {failed} | Server {(i % len(servers)) + 1}")
                                else:
                                    status.text(f"Sent: {sent} | Failed: {failed}")
                                if delay > 0 and i < len(rec) - 1:
                                    time.sleep(delay)

                            progress.empty()
                            status.empty()
                            save_campaign(uid, subject_tpl, sent, failed, len(rec), ctype)

                            st.markdown('<div class="status-success">✓ CAMPAIGN COMPLETE</div>', unsafe_allow_html=True)
                            r1, r2, r3, r4 = st.columns(4)
                            with r1:
                                card("✓", sent, "Sent", "#00ff88")
                            with r2:
                                card("✗", failed, "Failed", "#ff6b6b")
                            with r3:
                                card("📊", f"{(sent / len(rec) * 100):.1f}%", "Success")
                            with r4:
                                card("👥", len(rec), "Total")
                            if errors:
                                with st.expander("View errors"):
                                    for err in errors:
                                        st.write(err)

    def render_account():
        st.markdown("# 🔐 My Account")
        st.markdown('<div class="subtitle">Change your password or delete your account</div>', unsafe_allow_html=True)
        uname = get_user(uid)[0]
        st.markdown(f"**Username:** {uname}")

        st.markdown('<div class="section-title">Change Password</div>', unsafe_allow_html=True)
        if is_admin:
            st.caption("The admin password is stored in Streamlit Secrets. Change it there.")
        else:
            old_pw = st.text_input("Current password", type="password", key="acc_old_pw")
            new_pw = st.text_input("New password", type="password", key="acc_new_pw")
            conf_pw = st.text_input("Confirm new password", type="password", key="acc_conf_pw")
            if st.button("🔐 UPDATE PASSWORD", key="acc_pw_btn"):
                if not login_user(uname, old_pw):
                    st.markdown('<div class="status-error">✗ Current password is incorrect</div>', unsafe_allow_html=True)
                elif len(new_pw) < 6:
                    st.markdown('<div class="status-error">✗ New password must be at least 6 characters</div>', unsafe_allow_html=True)
                elif new_pw != conf_pw:
                    st.markdown('<div class="status-error">✗ New passwords do not match</div>', unsafe_allow_html=True)
                else:
                    reset_password(uid, new_pw)
                    st.markdown('<div class="status-success">✓ Password updated</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Delete Account</div>', unsafe_allow_html=True)
        if is_admin:
            st.caption("The admin account cannot be deleted.")
        else:
            st.markdown('<div class="status-warning">This permanently deletes your account, saved servers and campaign history.</div>', unsafe_allow_html=True)
            confirm = st.checkbox("I understand this cannot be undone", key="acc_del_confirm")
            if st.button("🗑️ DELETE MY ACCOUNT", disabled=not confirm, key="acc_del_btn"):
                delete_user(uid)
                sign_out()
                st.rerun()

    # ----- Router -----
    if is_admin and page == "admin_users":
        render_admin_users()
    elif is_admin and page == "admin_user_detail":
        render_admin_user_detail()
    elif is_admin and page == "admin_access":
        render_admin_access()
    elif page == "compose":
        render_compose()
    elif page == "profiles":
        render_servers()
    elif page == "history":
        render_history()
    elif page == "account":
        render_account()
    else:
        render_dashboard()
