import html
import re
import time
import warnings
from datetime import datetime
from io import BytesIO, StringIO

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from mongodb import mongo_db

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="LINKPULSE ANALYTICS - LinkedIn Engagement Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAX_UPLOAD_SIZE_MB = 20
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
MAX_ROWS = 100_000

MISSING_VALUES = ["", "none", "null", "nan", "na", "n/a", "-", "--", "not available"]
NUMERIC_HINTS = [
    "impression", "view", "reach", "like", "reaction", "comment", "reply",
    "share", "repost", "click", "engagement", "follower", "profile",
]
TEXT_HINTS = [
    "text", "content", "post", "message", "commentary", "url", "link",
    "permalink", "caption", "description",
]


if not mongo_db.is_connected() and mongo_db.last_error:
    st.error(f"⚠️ Database connection issue: {mongo_db.last_error}")


def safe_text(value):
    return html.escape(str(value or ""))


def init_session_state():
    defaults = {
        "authenticated": False,
        "user_id": None,
        "username": None,
        "user_email": None,
        "page": "landing",
        "dashboard_page": "home",
        "session_token": None,
        "current_data": None,
        "cleaned_data": None,
        "analysis_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        padding: 2rem;
    }
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .user-info {
        background: #f5f7fb;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(102,126,234,0.4);
    }
    .auth-container {
        background: white;
        padding: 3rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin: 2rem auto;
        max-width: 400px;
    }
    .insight-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if not st.session_state.authenticated and st.session_state.session_token:
    result = mongo_db.validate_session(st.session_state.session_token)
    if result and result.get("success"):
        st.session_state.authenticated = True
        st.session_state.user_id = result.get("user_id")
        st.session_state.username = result.get("username")
        st.session_state.user_email = result.get("email")
        st.session_state.page = "dashboard"
        st.rerun()


def login(username, password, remember_me=False):
    result = mongo_db.authenticate_user(username, password)
    if result.get("success"):
        st.session_state.authenticated = True
        st.session_state.user_id = result["user"]["id"]
        st.session_state.username = result["user"]["username"]
        st.session_state.user_email = result["user"]["email"]
        st.session_state.page = "dashboard"
        st.session_state.dashboard_page = "home"

        if remember_me:
            session_result = mongo_db.create_session(result["user"]["id"])
            if session_result.get("success"):
                st.session_state.session_token = session_result["token"]
        return True
    return False


def signup(username, password, email):
    result = mongo_db.create_user(username, email, password)
    if result.get("success"):
        return True, "Account created successfully! Please login."
    return False, result.get("message", "Could not create account.")


def logout():
    if st.session_state.session_token:
        mongo_db.delete_session(st.session_state.session_token)

    for key in [
        "authenticated", "user_id", "username", "user_email", "page",
        "dashboard_page", "session_token", "current_data", "cleaned_data",
        "analysis_history",
    ]:
        if key == "authenticated":
            st.session_state[key] = False
        elif key == "page":
            st.session_state[key] = "landing"
        elif key == "dashboard_page":
            st.session_state[key] = "home"
        else:
            st.session_state[key] = None
    st.rerun()


def validate_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    if not name.endswith((".csv", ".xlsx", ".txt")):
        raise ValueError("Only CSV, XLSX, and TXT files are supported.")
    if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(f"File is too large. Please upload a file under {MAX_UPLOAD_SIZE_MB} MB.")


def read_uploaded_dataset(uploaded_file):
    validate_uploaded_file(uploaded_file)
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file, encoding_errors="replace")
    if filename.endswith(".xlsx"):
        return pd.read_excel(BytesIO(uploaded_file.getvalue()), engine="openpyxl")

    raw_bytes = uploaded_file.getvalue()
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            content = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Could not decode the text file.")

    return pd.read_csv(StringIO(content))


def validate_dataframe(df):
    if df.empty:
        raise ValueError("The uploaded file is empty.")
    if len(df) > MAX_ROWS:
        raise ValueError(f"Too many rows. Please upload up to {MAX_ROWS:,} rows.")
    if len(df.columns) == 0:
        raise ValueError("No columns were found in the uploaded file.")


def identify_linkedin_columns(df):
    column_mapping = {
        "date": None,
        "post_url": None,
        "post_text": None,
        "impressions": None,
        "reach": None,
        "likes": None,
        "comments": None,
        "shares": None,
        "reposts": None,
        "followers_gained": None,
        "profile_views": None,
    }

    patterns = {
        "date": ["date", "time", "posted", "published", "created"],
        "post_url": ["post url", "permalink", "url", "link"],
        "post_text": ["post text", "commentary", "share text", "content", "message", "caption", "text"],
        "impressions": ["impressions", "impression", "views", "display"],
        "reach": ["reach", "unique viewers", "members reached"],
        "likes": ["likes", "like", "reactions", "reaction"],
        "comments": ["comments", "comment", "replies", "reply"],
        "shares": ["shares", "share"],
        "reposts": ["reposts", "repost", "reshare"],
        "followers_gained": ["followers gained", "new followers", "follower"],
        "profile_views": ["profile views", "profile viewers", "profile"],
    }

    normalized_cols = {
        col: re.sub(r"[^a-z0-9]+", " ", str(col).lower()).strip()
        for col in df.columns
    }

    for metric, metric_patterns in patterns.items():
        for pattern in metric_patterns:
            pattern_norm = re.sub(r"[^a-z0-9]+", " ", pattern.lower()).strip()
            for original_col, normalized_col in normalized_cols.items():
                if pattern_norm in normalized_col:
                    column_mapping[metric] = original_col
                    break
            if column_mapping[metric]:
                break

    if column_mapping["shares"] == column_mapping["reposts"]:
        if column_mapping["shares"] and "repost" in str(column_mapping["shares"]).lower():
            column_mapping["shares"] = None

    return column_mapping


def clean_linkedin_data(df):
    df_clean = df.copy()
    df_clean.columns = [
        re.sub(r"\s+", " ", str(col).strip()).replace("\ufeff", "")
        for col in df_clean.columns
    ]
    df_clean = df_clean.dropna(how="all").drop_duplicates()

    for col in df_clean.columns:
        if df_clean[col].dtype == "object":
            df_clean[col] = df_clean[col].astype(str).str.strip()
            df_clean[col] = df_clean[col].replace(
                {value: np.nan for value in MISSING_VALUES},
                regex=False,
            )

    column_mapping = identify_linkedin_columns(df_clean)
    text_columns = {
        col for col in [column_mapping.get("post_text"), column_mapping.get("post_url")]
        if col
    }

    for col in df_clean.columns:
        col_lower = str(col).lower()
        if col in text_columns or any(hint in col_lower for hint in TEXT_HINTS):
            continue

        likely_numeric = any(hint in col_lower for hint in NUMERIC_HINTS)
        if likely_numeric or df_clean[col].dtype == "object":
            cleaned = (
                df_clean[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace("+", "", regex=False)
                .str.strip()
            )
            numeric = pd.to_numeric(cleaned, errors="coerce")
            if numeric.notna().mean() >= 0.65:
                df_clean[col] = numeric

    for col in df_clean.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ["date", "time", "posted", "published", "created"]):
            parsed = pd.to_datetime(df_clean[col], errors="coerce")
            if parsed.notna().mean() >= 0.5:
                df_clean[col] = parsed

    return df_clean


def get_numeric_series(df, column_mapping, key):
    col_name = column_mapping.get(key)
    if col_name and col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name]):
        return df[col_name].dropna()
    return None


def generate_visualizations(df, column_mapping):
    visualizations = {}
    chart_palette = ["#2563eb", "#7c3aed", "#dc2626", "#16a34a", "#ea580c"]

    impressions_data = get_numeric_series(df, column_mapping, "impressions")
    if impressions_data is None:
        impressions_data = get_numeric_series(df, column_mapping, "reach")

    if impressions_data is not None and not impressions_data.empty:
        fig_imp = px.histogram(
            x=impressions_data,
            title="Impressions Distribution",
            color_discrete_sequence=[chart_palette[0]],
            nbins=min(30, max(5, len(impressions_data) // 2)),
            labels={"x": "Impressions", "count": "Posts"},
        )
        fig_imp.update_layout(showlegend=False, height=400)
        visualizations["impressions"] = fig_imp

    engagement_data = {}
    for key in ["likes", "comments", "shares", "reposts"]:
        data = get_numeric_series(df, column_mapping, key)
        if data is not None and not data.empty:
            engagement_data[key.replace("_", " ").title()] = data

    if len(engagement_data) >= 2:
        fig_engage = go.Figure()
        for i, (key, data) in enumerate(engagement_data.items()):
            fig_engage.add_trace(
                go.Box(y=data, name=key, marker_color=chart_palette[i % len(chart_palette)], boxmean="sd")
            )
        fig_engage.update_layout(
            title="Engagement Metrics Distribution",
            height=400,
            yaxis_title="Count",
            showlegend=False,
        )
        visualizations["engagement"] = fig_engage

    date_col = column_mapping.get("date")
    if date_col and date_col in df.columns:
        df_time = df.copy()
        df_time[date_col] = pd.to_datetime(df_time[date_col], errors="coerce")
        df_time = df_time.dropna(subset=[date_col]).sort_values(date_col)

        metrics = []
        for key in ["impressions", "reach", "likes", "comments", "shares"]:
            col_name = column_mapping.get(key)
            if col_name and col_name in df_time.columns and pd.api.types.is_numeric_dtype(df_time[col_name]):
                metrics.append((key.replace("_", " ").title(), col_name))

        if not df_time.empty and metrics:
            fig_time = go.Figure()
            for i, (key, col_name) in enumerate(metrics[:5]):
                fig_time.add_trace(
                    go.Scatter(
                        x=df_time[date_col],
                        y=df_time[col_name],
                        name=key,
                        mode="lines+markers",
                        line=dict(color=chart_palette[i % len(chart_palette)], width=2),
                    )
                )
            fig_time.update_layout(
                title="Performance Over Time",
                xaxis_title="Date",
                yaxis_title="Count",
                hovermode="x unified",
                height=420,
            )
            visualizations["timeseries"] = fig_time

    numeric_cols = []
    for key in ["impressions", "reach", "likes", "comments", "shares", "reposts"]:
        col_name = column_mapping.get(key)
        if col_name and col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name]):
            numeric_cols.append(col_name)

    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        if not corr_matrix.isna().all().all():
            fig_corr = px.imshow(
                corr_matrix,
                title="Metric Correlation Heatmap",
                color_continuous_scale="RdBu",
                zmin=-1,
                zmax=1,
                aspect="auto",
                height=420,
            )
            visualizations["correlation"] = fig_corr

    metric_col = None
    for key in ["impressions", "reach", "likes"]:
        col_name = column_mapping.get(key)
        if col_name and col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name]):
            metric_col = col_name
            break

    text_col = column_mapping.get("post_text") or column_mapping.get("post_url")
    if metric_col and text_col and text_col in df.columns:
        df_valid = df.dropna(subset=[metric_col])
        if not df_valid.empty:
            df_sorted = df_valid.nlargest(min(10, len(df_valid)), metric_col)[[text_col, metric_col]]
            labels = [
                (str(value)[:55] + "...") if len(str(value)) > 55 else str(value)
                for value in df_sorted[text_col].fillna("(no text)")
            ]
            fig_top = go.Figure(
                data=[
                    go.Bar(
                        x=df_sorted[metric_col],
                        y=labels,
                        orientation="h",
                        marker_color=chart_palette[0],
                        text=df_sorted[metric_col],
                        textposition="outside",
                    )
                ]
            )
            fig_top.update_layout(
                title="Top Performing Posts",
                xaxis_title=str(metric_col).replace("_", " ").title(),
                yaxis_title="Post Preview",
                height=450,
                yaxis=dict(autorange="reversed"),
            )
            visualizations["top_posts"] = fig_top

    total_engagement = {}
    for key in ["likes", "comments", "shares"]:
        data = get_numeric_series(df, column_mapping, key)
        if data is not None and data.sum() > 0:
            total_engagement[key.title()] = data.sum()

    if len(total_engagement) >= 2:
        fig_pie = px.pie(
            values=list(total_engagement.values()),
            names=list(total_engagement.keys()),
            title="Engagement Distribution",
            color_discrete_sequence=chart_palette,
        )
        fig_pie.update_layout(height=400)
        visualizations["pie"] = fig_pie

    return visualizations


def build_report(uploaded_file, df_clean, column_mapping):
    report = f"""LINKPULSE ANALYTICS REPORT
==========================
File: {uploaded_file.name}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
User: {st.session_state.username}

SUMMARY STATISTICS
------------------
Total Posts: {len(df_clean)}
Columns: {len(df_clean.columns)}
"""

    for key in ["impressions", "reach", "likes", "comments", "shares", "reposts"]:
        col = column_mapping.get(key)
        if col and col in df_clean.columns and pd.api.types.is_numeric_dtype(df_clean[col]):
            report += f"""

{key.replace("_", " ").title()}:
  - Total: {df_clean[col].sum():,.0f}
  - Average: {df_clean[col].mean():,.2f}
  - Maximum: {df_clean[col].max():,.0f}
"""

    report += "\n=========================="
    return report


def show_landing_page():
    col1, col2, col3 = st.columns([3, 2, 2])
    with col2:
        if st.button("🔑 Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
    with col3:
        if st.button("📝 Sign Up", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

    st.markdown(
        """
        <div style="text-align: center; padding: 1rem;">
            <h1 style="font-size: 4rem; color: #667eea;">📊 LINKPULSE ANALYTICS</h1>
            <h2 style="font-size: 2rem; color: #666;">LINKEDIN ENGAGEMENT AND SENTIMENT DASHBOARD</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="text-align: center; max-width: 800px; margin: 0 auto; padding: 1rem;">
            <p style="font-size: 1.2rem; line-height: 1.6; color: #444;">
            Transform your LinkedIn engagement data into actionable insights. Upload your datasets and get instant
            visual analytics on impressions, likes, comments, shares, and performance trends.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>✨ Key Features</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="insight-card"><h3>📈 Analytics</h3><p>Interactive charts for performance and engagement.</p></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="insight-card"><h3>🧹 Data Cleaning</h3><p>Safer cleaning that preserves post text and URLs.</p></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="insight-card"><h3>📑 Reports</h3><p>Download cleaned CSV files and summary reports.</p></div>',
            unsafe_allow_html=True,
        )


def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Back", key="login_back"):
            st.session_state.page = "landing"
            st.rerun()

    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<h2 style="text-align:center;">🔐 Login</h2>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            remember = st.checkbox("Remember me")
            if st.form_submit_button("Login", use_container_width=True):
                if username and password:
                    if login(username.strip(), password, remember):
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("Please enter both username and password")

        st.markdown("---")
        st.info("Demo Credentials: username `demo`, password `demo123`")
        st.markdown("</div>", unsafe_allow_html=True)


def show_signup_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Back", key="signup_back"):
            st.session_state.page = "landing"
            st.rerun()

    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<h2 style="text-align:center;">✨ Sign Up</h2>', unsafe_allow_html=True)
        with st.form("signup_form"):
            username = st.text_input("Username", placeholder="Choose username")
            email = st.text_input("Email", placeholder="Enter email")
            password = st.text_input("Password", type="password", placeholder="Create password")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password")

            if st.form_submit_button("Sign Up", use_container_width=True):
                if not all([username, email, password, confirm]):
                    st.warning("Please fill all fields")
                elif password != confirm:
                    st.error("Passwords don't match")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters")
                elif "@" not in email or "." not in email:
                    st.error("Please enter a valid email address")
                else:
                    success, msg = signup(username.strip(), password, email.strip())
                    if success:
                        st.success(msg)
                        time.sleep(1)
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)


def show_dashboard():
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-header">
                <h2>📊 LINKPULSE</h2>
                <p>Analytics Dashboard</p>
            </div>
            <div class="user-info">
                <strong>👤 {safe_text(st.session_state.username)}</strong><br>
                <small>{safe_text(st.session_state.user_email)}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            st.session_state.dashboard_page = "home"
            st.rerun()
        if st.button("👤 Profile", key="nav_profile", use_container_width=True):
            st.session_state.dashboard_page = "profile"
            st.rerun()
        if st.button("📊 Analyze", key="nav_analyze", use_container_width=True):
            st.session_state.dashboard_page = "analyze"
            st.rerun()
        if st.button("📜 History", key="nav_history", use_container_width=True):
            st.session_state.dashboard_page = "history"
            st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout", key="nav_logout", use_container_width=True):
            logout()

    if st.session_state.dashboard_page == "home":
        show_user_home()
    elif st.session_state.dashboard_page == "profile":
        show_profile_page()
    elif st.session_state.dashboard_page == "analyze":
        show_analyze_page()
    elif st.session_state.dashboard_page == "history":
        show_history_page()


def show_user_home():
    st.title("🏠 Welcome to LINKPULSE Analytics!")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="insight-card">
                <h3>📈 Getting Started</h3>
                <p>Upload LinkedIn engagement exports in CSV, XLSX, or TXT format.</p>
            </div>
            <div class="insight-card">
                <h3>🔍 What We Analyze</h3>
                <ul>
                    <li>Impressions and reach</li>
                    <li>Likes, reactions, and comments</li>
                    <li>Shares and reposts</li>
                    <li>Performance trends over time</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="insight-card">
                <h3>💡 Pro Tips</h3>
                <ul>
                    <li>Export clean post analytics from LinkedIn.</li>
                    <li>Use consistent column names where possible.</li>
                    <li>Review detected columns before trusting charts.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.session_state.current_data is not None:
            st.info(f"📁 Current dataset: {len(st.session_state.current_data)} rows loaded")
        else:
            st.info("🚀 Go to the Analyze page to upload your first dataset!")


def show_profile_page():
    st.title("👤 Profile Settings")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(
            f"""
            <div style="text-align:center; padding:2rem; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius:15px; color:white;">
                <div style="font-size:5rem;">👤</div>
                <h3>{safe_text(st.session_state.username)}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        with st.form("profile_form"):
            email = st.text_input("Email", value=st.session_state.user_email or "")
            current = st.text_input("Current Password", type="password", placeholder="Enter to change password")
            new = st.text_input("New Password", type="password", placeholder="Leave blank to keep current")
            confirm = st.text_input("Confirm New Password", type="password")

            submitted = st.form_submit_button("Update Profile", use_container_width=True)
            if submitted:
                if new and new != confirm:
                    st.error("New passwords don't match")
                elif new and len(new) < 8:
                    st.error("New password must be at least 8 characters")
                elif new and not current:
                    st.error("Please enter current password")
                else:
                    proceed = True
                    if new:
                        auth = mongo_db.authenticate_user(st.session_state.username, current)
                        if not auth.get("success"):
                            st.error("Current password is incorrect")
                            proceed = False

                    if proceed:
                        result = mongo_db.update_user(
                            st.session_state.user_id,
                            email.strip() if email != st.session_state.user_email else None,
                            new if new else None,
                        )
                        if result.get("success"):
                            st.session_state.user_email = email.strip()
                            st.success("Profile updated!")
                        else:
                            st.error(result.get("message", "No changes made"))


def show_analyze_page():
    st.title("📊 Analyze LinkedIn Data")
    st.warning(
        "Upload CSV, XLSX, or TXT files under 20 MB. For best results, include columns for date, "
        "post text or URL, impressions/reach, likes, comments, and shares."
    )

    uploaded_file = st.file_uploader(
        "Upload your LinkedIn engagement data",
        type=["csv", "xlsx", "txt"],
        help="Upload CSV, Excel, or text files containing your LinkedIn post metrics",
        key="file_uploader",
    )

    if uploaded_file is None:
        return

    try:
        df = read_uploaded_dataset(uploaded_file)
        validate_dataframe(df)
        st.session_state.current_data = df

        with st.spinner("🧹 Cleaning and processing data..."):
            df_clean = clean_linkedin_data(df)
            st.session_state.cleaned_data = df_clean

        column_mapping = identify_linkedin_columns(df_clean)
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Raw Data", "✨ Cleaned Data", "🔍 Column Detection", "📈 Visualizations"])

        with tab1:
            st.subheader("Raw Data Preview")
            st.dataframe(df.head(100), use_container_width=True)
            st.info(f"📊 Total rows: {len(df)} | Total columns: {len(df.columns)}")
            st.subheader("Column Names in Your File")
            st.write(list(df.columns))

        with tab2:
            st.subheader("Cleaned Data Preview")
            st.dataframe(df_clean.head(100), use_container_width=True)
            st.info(f"📊 Rows after cleaning: {len(df_clean)} | Removed rows: {len(df) - len(df_clean)}")
            st.success("✅ Removed blank rows, duplicate rows, and common missing-value markers")
            st.success("✅ Converted metric-like columns while preserving post text and URLs")
            st.success("✅ Processed date columns when enough values looked like dates")

        with tab3:
            st.subheader("Detected LinkedIn Columns")
            mapping_data = [
                {
                    "Metric": key.replace("_", " ").title(),
                    "Status": "✅ Found" if value else "❌ Not found",
                    "Detected Column": value if value else "-",
                }
                for key, value in column_mapping.items()
            ]
            st.dataframe(pd.DataFrame(mapping_data), use_container_width=True)

            st.subheader("Numeric Columns Statistics")
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                stats_data = []
                for col in numeric_cols:
                    series = df_clean[col].dropna()
                    if series.empty:
                        continue
                    stats_data.append(
                        {
                            "Column": col,
                            "Mean": f"{series.mean():,.2f}",
                            "Median": f"{series.median():,.2f}",
                            "Max": f"{series.max():,.0f}",
                            "Min": f"{series.min():,.0f}",
                            "Sum": f"{series.sum():,.0f}",
                        }
                    )
                st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
            else:
                st.warning("No numeric columns found")

            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col2:
                if st.button("💾 Save to History", use_container_width=True, key="save_history_btn"):
                    result = mongo_db.save_analysis(
                        st.session_state.user_id,
                        uploaded_file.name,
                        len(df_clean),
                        {k: v for k, v in column_mapping.items() if v},
                        uploaded_file.getvalue(),
                    )
                    if result.get("success"):
                        st.success("✅ Analysis saved to history!")
                    else:
                        st.error(result.get("message", "❌ Failed to save analysis"))

        with tab4:
            st.subheader("📈 Visualization Dashboard")
            with st.spinner("🎨 Generating visualizations..."):
                visualizations = generate_visualizations(df_clean, column_mapping)

            if not visualizations:
                st.warning("⚠️ Not enough detected numeric data to generate visualizations.")
                return

            st.success(f"✅ Generated {len(visualizations)} visualizations!")
            viz_items = list(visualizations.items())
            for i in range(0, len(viz_items), 2):
                cols = st.columns(2)
                with cols[0]:
                    st.plotly_chart(viz_items[i][1], use_container_width=True)
                if i + 1 < len(viz_items):
                    with cols[1]:
                        st.plotly_chart(viz_items[i + 1][1], use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Quick Statistics")
            metric_cols = st.columns(4)
            col_idx = 0
            for key in ["impressions", "reach", "likes", "comments", "shares"]:
                col = column_mapping.get(key)
                if col and col in df_clean.columns and pd.api.types.is_numeric_dtype(df_clean[col]):
                    with metric_cols[col_idx % 4]:
                        st.metric(f"Total {key.title()}", f"{df_clean[col].sum():,.0f}")
                        st.metric(f"Avg {key.title()}", f"{df_clean[col].mean():,.0f}")
                    col_idx += 1

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Cleaned Data (CSV)",
                    data=df_clean.to_csv(index=False),
                    file_name="cleaned_linkedin_data.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with col2:
                st.download_button(
                    label="📄 Download Summary Report (TXT)",
                    data=build_report(uploaded_file, df_clean, column_mapping),
                    file_name="linkedin_report.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")


def show_history_page():
    st.title("📜 Analysis History")
    analyses = mongo_db.get_user_analyses(st.session_state.user_id)

    if not analyses:
        st.info("📭 No analysis history yet. Go to the Analyze page and save some analyses!")
        return

    st.success(f"✅ Found {len(analyses)} saved analyses")
    for analysis in analyses:
        st.markdown(
            f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 1rem;">
                <h4 style="margin: 0; color: #333;">📁 {safe_text(analysis.get("filename", "Unknown file"))}</h4>
                <p style="color: #666; margin: 0.5rem 0;">
                    🕒 {safe_text(analysis.get("analysis_date", "Unknown date"))} |
                    📊 {int(analysis.get("rows_analyzed", 0))} rows |
                    📋 {len(analysis.get("detected_metrics", {}))} metrics detected
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if analysis.get("detected_metrics"):
            with st.expander("View detected columns"):
                metrics_data = [
                    {"Metric": key, "Column": value}
                    for key, value in analysis["detected_metrics"].items()
                ]
                st.dataframe(pd.DataFrame(metrics_data), use_container_width=True)
        st.markdown("---")


def main():
    if st.session_state.authenticated:
        show_dashboard()
    elif st.session_state.page == "landing":
        show_landing_page()
    elif st.session_state.page == "login":
        show_login_page()
    elif st.session_state.page == "signup":
        show_signup_page()
    else:
        show_landing_page()


if __name__ == "__main__":
    main()
