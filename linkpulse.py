import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import time
import warnings
warnings.filterwarnings('ignore')

# Import MongoDB
from mongodb import mongo_db

# Page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="LINKPULSE ANALYTICS - LinkedIn Engagement Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize ALL session state variables at the start
def init_session_state():
    """Initialize all session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'page' not in st.session_state:
        st.session_state.page = "landing"
    if 'dashboard_page' not in st.session_state:
        st.session_state.dashboard_page = "home"
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None
    if 'current_data' not in st.session_state:
        st.session_state.current_data = None
    if 'cleaned_data' not in st.session_state:
        st.session_state.cleaned_data = None
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []

# Initialize session state
init_session_state()

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
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
    .landing-container {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: white;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    .insight-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .caution-message {
        background: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
            /* Add to your existing CSS */
.landing-header {
    font-size: 4rem;
    font-weight: 800;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    color: white;
}

.landing-subheader {
    font-size: 2rem;
    margin-bottom: 2rem;
    opacity: 0.9;
    color: white;
}

.landing-description {
    font-size: 1.2rem;
    max-width: 800px;
    text-align: center;
    margin-bottom: 3rem;
    line-height: 1.6;
    opacity: 0.9;
    color: white;
}

.feature-box {
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(10px);
    padding: 2rem;
    border-radius: 20px;
    text-align: center;
    margin: 1rem;
    border: 1px solid rgba(255,255,255,0.2);
    color: white;
}

.feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.nav-buttons {
    position: absolute;
    top: 2rem;
    right: 2rem;
    display: flex;
    gap: 1rem;
    z-index: 1000;
}
    </style>
""", unsafe_allow_html=True)

# Check for saved session token (BEFORE any page rendering)
if not st.session_state.authenticated and st.session_state.session_token:
    result = mongo_db.validate_session(st.session_state.session_token)
    if result and result.get('success'):
        st.session_state.authenticated = True
        st.session_state.user_id = result.get('user_id')
        st.session_state.username = result.get('username')
        st.session_state.user_email = result.get('email')
        st.session_state.page = "dashboard"
        st.rerun()

# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def login(username, password, remember_me=False):
    """Login user"""
    result = mongo_db.authenticate_user(username, password)
    
    if result['success']:
        st.session_state.authenticated = True
        st.session_state.user_id = result['user']['id']
        st.session_state.username = result['user']['username']
        st.session_state.user_email = result['user']['email']
        st.session_state.page = "dashboard"
        st.session_state.dashboard_page = "home"
        
        if remember_me:
            session_result = mongo_db.create_session(result['user']['id'])
            if session_result['success']:
                st.session_state.session_token = session_result['token']
        
        return True
    return False

def signup(username, password, email):
    """Signup new user"""
    result = mongo_db.create_user(username, email, password)
    if result['success']:
        return True, "Account created successfully! Please login."
    else:
        return False, result['message']

def logout():
    """Logout user"""
    if st.session_state.session_token:
        mongo_db.delete_session(st.session_state.session_token)
    
    # Clear all session state
    for key in ['authenticated', 'user_id', 'username', 'user_email', 
                'page', 'dashboard_page', 'session_token', 'current_data', 
                'cleaned_data', 'analysis_history']:
        if key in st.session_state:
            if key == 'page':
                st.session_state.page = "landing"
            elif key == 'dashboard_page':
                st.session_state.dashboard_page = "home"
            elif key in ['authenticated']:
                st.session_state.authenticated = False
            else:
                st.session_state[key] = None
    
    st.rerun()

# ============================================================================
# DATA PROCESSING FUNCTIONS
# ============================================================================

def clean_linkedin_data(df):
    """Clean and preprocess LinkedIn exported data"""
    df_clean = df.copy()
    
    # Remove completely empty rows
    df_clean = df_clean.dropna(how='all')
    
    # Replace string 'None' with actual NaN
    df_clean = df_clean.replace('None', np.nan)
    df_clean = df_clean.replace('none', np.nan)
    df_clean = df_clean.replace('NULL', np.nan)
    df_clean = df_clean.replace('null', np.nan)
    
    # Convert numeric columns (handling commas and special characters)
    for col in df_clean.columns:
        if df_clean[col].isna().all():
            continue
            
        try:
            if df_clean[col].dtype == 'object':
                # Clean the data
                cleaned = df_clean[col].astype(str).str.replace(',', '', regex=False)
                cleaned = cleaned.str.replace('$', '', regex=False)
                cleaned = cleaned.str.replace('%', '', regex=False)
                cleaned = cleaned.str.strip()
                
                # Convert to numeric, coerce errors to NaN
                df_clean[col] = pd.to_numeric(cleaned, errors='coerce')
        except:
            pass
    
    # Convert date columns
    for col in df_clean.columns:
        if any(keyword in col.lower() for keyword in ['date', 'time', 'published', 'created']):
            try:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
            except:
                pass
    
    return df_clean

def identify_linkedin_columns(df):
    """Identify important columns specifically for LinkedIn exports"""
    column_mapping = {
        'date': None,
        'post_url': None,
        'post_text': None,
        'impressions': None,
        'reach': None,
        'likes': None,
        'comments': None,
        'shares': None,
        'reposts': None,
        'followers_gained': None,
        'profile_views': None
    }
    
    # LinkedIn specific column patterns
    linkedin_patterns = {
        'date': ['date', 'time', 'posted', 'published', 'created'],
        'post_url': ['url', 'link', 'post url', 'permalink'],
        'post_text': ['text', 'content', 'post', 'message', 'commentary', 'share-text'],
        'impressions': ['impression', 'views', 'display'],
        'reach': ['reach', 'unique', 'members reached'],
        'likes': ['like', 'reaction', 'thumbs'],
        'comments': ['comment', 'reply'],
        'shares': ['share', 'repost'],
        'reposts': ['repost', 'reshare'],
        'followers_gained': ['follower', 'new follower', 'followers gained'],
        'profile_views': ['profile', 'profile viewer']
    }
    
    for col in df.columns:
        col_lower = str(col).lower().strip()
        
        for key, patterns in linkedin_patterns.items():
            if column_mapping[key] is None:
                for pattern in patterns:
                    if pattern in col_lower:
                        column_mapping[key] = col
                        break
    
    return column_mapping

def generate_visualizations(df, column_mapping):
    """Generate multiple interactive visualizations using Plotly"""
    visualizations = {}
    
    # Helper function to safely get column data
    def get_column_data(col_key):
        col_name = column_mapping.get(col_key)
        if col_name and col_name in df.columns:
            if pd.api.types.is_numeric_dtype(df[col_name]):
                return df[col_name].dropna()
        return None
    
    # 1. Impressions Distribution (Histogram)
    impressions_data = get_column_data('impressions') or get_column_data('reach')
    if impressions_data is not None and len(impressions_data) > 0:
        fig_imp = px.histogram(
            x=impressions_data,
            title="📊 Impressions Distribution",
            color_discrete_sequence=['#667eea'],
            nbins=30,
            labels={'x': 'Impressions', 'count': 'Frequency'}
        )
        fig_imp.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            title_font_size=16,
            title_font_color='#333'
        )
        visualizations['impressions'] = fig_imp
    
    # 2. Engagement Metrics Comparison (Box Plot)
    engagement_data = {}
    for key in ['likes', 'comments', 'shares', 'reposts']:
        data = get_column_data(key)
        if data is not None and len(data) > 0:
            engagement_data[key.replace('_', ' ').title()] = data
    
    if len(engagement_data) >= 2:
        fig_engage = go.Figure()
        colors = ['#667eea', '#764ba2', '#ff6b6b', '#4CAF50']
        
        for i, (key, data) in enumerate(engagement_data.items()):
            fig_engage.add_trace(go.Box(
                y=data,
                name=key,
                marker_color=colors[i % len(colors)],
                boxmean='sd'
            ))
        
        fig_engage.update_layout(
            title="📈 Engagement Metrics Distribution",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            yaxis_title="Count",
            title_font_size=16,
            title_font_color='#333',
            showlegend=False
        )
        visualizations['engagement'] = fig_engage
    
    # 3. Time Series Analysis (Line Chart)
    date_col = column_mapping.get('date')
    if date_col and date_col in df.columns:
        try:
            df_time = df.copy()
            df_time[date_col] = pd.to_datetime(df_time[date_col], errors='coerce')
            df_time = df_time.dropna(subset=[date_col]).sort_values(date_col)
            
            if len(df_time) > 0:
                fig_time = go.Figure()
                
                metrics = []
                for key in ['impressions', 'likes', 'comments', 'shares']:
                    col_name = column_mapping.get(key)
                    if col_name and col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name]):
                        metrics.append((key.replace('_', ' ').title(), col_name))
                
                colors = ['#667eea', '#764ba2', '#ff6b6b', '#4CAF50']
                for i, (key, col_name) in enumerate(metrics[:4]):
                    fig_time.add_trace(go.Scatter(
                        x=df_time[date_col],
                        y=df_time[col_name],
                        name=key,
                        line=dict(color=colors[i % len(colors)], width=2),
                        mode='lines+markers',
                        marker=dict(size=6)
                    ))
                
                fig_time.update_layout(
                    title="📅 Performance Over Time",
                    xaxis_title="Date",
                    yaxis_title="Count",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode='x unified',
                    height=400,
                    title_font_size=16,
                    title_font_color='#333',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                visualizations['timeseries'] = fig_time
        except Exception as e:
            print(f"Time series error: {e}")
    
    # 4. Correlation Heatmap
    numeric_cols = []
    for key in ['impressions', 'reach', 'likes', 'comments', 'shares', 'reposts']:
        col_name = column_mapping.get(key)
        if col_name and col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name]):
            numeric_cols.append(col_name)
    
    if len(numeric_cols) >= 2:
        try:
            corr_matrix = df[numeric_cols].corr()
            fig_corr = px.imshow(
                corr_matrix,
                title="🔗 Correlation Heatmap",
                color_continuous_scale='Viridis',
                aspect='auto',
                height=400,
                labels=dict(x="Metrics", y="Metrics", color="Correlation")
            )
            fig_corr.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#333'
            )
            visualizations['correlation'] = fig_corr
        except Exception as e:
            print(f"Heatmap error: {e}")
    
    # 5. Top Posts (Bar Chart)
    metric_col = None
    for key in ['impressions', 'reach', 'likes']:
        col_name = column_mapping.get(key)
        if col_name and col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name]):
            metric_col = col_name
            break
    
    text_col = column_mapping.get('post_text') or column_mapping.get('post_url')
    
    if metric_col and text_col and text_col in df.columns:
        try:
            # Get top 10 posts
            df_sorted = df.nlargest(10, metric_col)[[text_col, metric_col]]
            
            # Create labels
            labels = []
            for idx, row in df_sorted.iterrows():
                text = str(row[text_col])
                label = text[:40] + '...' if len(text) > 40 else text
                labels.append(label)
            
            fig_top = go.Figure(data=[
                go.Bar(
                    x=df_sorted[metric_col],
                    y=labels,
                    orientation='h',
                    marker_color='#667eea',
                    text=df_sorted[metric_col],
                    textposition='outside'
                )
            ])
            fig_top.update_layout(
                title="🏆 Top 10 Performing Posts",
                xaxis_title=metric_col.replace('_', ' ').title(),
                yaxis_title="Post Preview",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                title_font_size=16,
                title_font_color='#333',
                yaxis=dict(autorange="reversed")
            )
            visualizations['top_posts'] = fig_top
        except Exception as e:
            print(f"Top posts error: {e}")
    
    # 6. Pie Chart for Engagement Distribution
    total_engagement = {}
    for key in ['likes', 'comments', 'shares']:
        data = get_column_data(key)
        if data is not None and len(data) > 0:
            total_engagement[key.title()] = data.sum()
    
    if len(total_engagement) >= 2:
        fig_pie = px.pie(
            values=list(total_engagement.values()),
            names=list(total_engagement.keys()),
            title="🥧 Engagement Distribution",
            color_discrete_sequence=['#667eea', '#764ba2', '#ff6b6b']
        )
        fig_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            title_font_size=16,
            title_font_color='#333'
        )
        visualizations['pie'] = fig_pie
    
    return visualizations
# ============================================================================
# PAGE FUNCTIONS
# ============================================================================
def show_landing_page():
    """Landing page with full description and features"""
    
    # Navigation buttons
    col1, col2, col3 = st.columns([3, 2, 2])
    
    with col2:
        if st.button("🔑 Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
    
    with col3:
        if st.button("📝 Sign Up", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h1 style="font-size: 4rem; color: #667eea;">📊 LINKPULSE ANALYTICS</h1>
        <h2 style="font-size: 2rem; color: #666;">LINKEDLN ENGAGEMENT AND SENTIMENT DASHBOARD</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Description
    st.markdown("""
    <div style="text-align: center; max-width: 800px; margin: 0 auto; padding: 1rem;">
        <p style="font-size: 1.2rem; line-height: 1.6; color: #444;">
        Transform your LinkedIn engagement data into actionable insights. Upload your datasets and get instant 
        visual analytics on impressions, likes, comments, shares, and sentiment analysis to optimize your 
        content strategy. This powerful dashboard helps you understand post performance and make data-driven 
        decisions to improve your LinkedIn engagement strategy.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature boxes using columns
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>✨ Key Features</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); height: 100%;">
            <h1 style="font-size: 3rem; margin: 0;">📈</h1>
            <h4>Real-time Analytics</h4>
            <p style="color: #666;">Track your LinkedIn performance metrics in real-time with interactive visualizations</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); height: 100%;">
            <h1 style="font-size: 3rem; margin: 0;">😊</h1>
            <h4>Sentiment Analysis</h4>
            <p style="color: #666;">Powered analysis of comments to understand audience sentiment</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); height: 100%;">
            <h1 style="font-size: 3rem; margin: 0;">📑</h1>
            <h4>PDF Reports</h4>
            <p style="color: #666;">Generate comprehensive analysis reports with one click</p>
        </div>
        """, unsafe_allow_html=True)
    
    
    # Call to action
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">
        <h3>Ready to optimize your LinkedIn strategy?</h3>
        <p>Join thousands of people who use LINKPULSE to grow their network</p>
    </div>
    """, unsafe_allow_html=True)

def show_login_page():
    """Login page"""
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
                    if login(username, password, remember):
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; padding:1rem; background:#f5f7fb; border-radius:10px;">
            <p><strong>Demo Credentials:</strong></p>
            <p>Username: <code>demo</code> | Password: <code>demo123</code></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_signup_page():
    """Signup page"""
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
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    success, msg = signup(username, password, email)
                    if success:
                        st.success(msg)
                        time.sleep(1)
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(msg)
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard():
    """Main dashboard with sidebar"""
    
    # Sidebar - ALWAYS shown when authenticated
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-header">
            <h2>📊 LINKPULSE</h2>
            <p>Analytics Dashboard</p>
        </div>
        <div class="user-info">
            <strong>👤 {st.session_state.username}</strong><br>
            <small>{st.session_state.user_email}</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
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
    
    # Main content based on selection
    if st.session_state.dashboard_page == "home":
        show_user_home()
    elif st.session_state.dashboard_page == "profile":
        show_profile_page()
    elif st.session_state.dashboard_page == "analyze":
        show_analyze_page()
    elif st.session_state.dashboard_page == "history":
        show_history_page()

def show_user_home():
    """User home page"""
    st.title("🏠 Welcome to LINKPULSE Analytics!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="insight-card">
            <h3>📈 Getting Started</h3>
            <p>Upload your LinkedIn engagement data to get started with analysis. We support:</p>
            <ul>
                <li>✅ CSV files (LinkedIn export format)</li>
                <li>✅ Excel files (XLSX)</li>
                <li>✅ Text files</li>
            </ul>
        </div>
        
        <div class="insight-card">
            <h3>🔍 What We Analyze</h3>
            <ul>
                <li>📊 Impressions and reach</li>
                <li>❤️ Likes, reactions, and comments</li>
                <li>🔄 Shares and reposts</li>
                <li>📈 Engagement rates</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="insight-card">
            <h3>💡 Pro Tips</h3>
            <ul>
                <li>🎯 Post consistently for better engagement</li>
                <li>🖼️ Use visuals in your posts</li>
                <li>💬 Engage with your commenters</li>
                <li>📊 Track what content performs best</li>
                <li>📥 Export your LinkedIn data as CSV</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.current_data is not None:
            st.info(f"📁 Current dataset: {len(st.session_state.current_data)} posts loaded")
        else:
            st.info("🚀 Go to the **Analyze** page to upload your first dataset!")

def show_profile_page():
    """Profile page"""
    st.title("👤 Profile Settings")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div style="text-align:center; padding:2rem; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius:15px; color:white;">
            <div style="font-size:5rem;">👤</div>
            <h3>{st.session_state.username}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        with st.form("profile_form"):
            email = st.text_input("Email", value=st.session_state.user_email)
            current = st.text_input("Current Password", type="password", placeholder="Enter to change password")
            new = st.text_input("New Password", type="password", placeholder="Leave blank to keep current")
            confirm = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Profile", use_container_width=True):
                if new and new != confirm:
                    st.error("New passwords don't match")
                elif new and not current:
                    st.error("Please enter current password")
                else:
                    if new:
                        auth = mongo_db.authenticate_user(st.session_state.username, current)
                        if not auth['success']:
                            st.error("Current password is incorrect")
                            return
                    
                    result = mongo_db.update_user(
                        st.session_state.user_id,
                        email if email != st.session_state.user_email else None,
                        new if new else None
                    )
                    
                    if result['success']:
                        st.session_state.user_email = email
                        st.success("Profile updated!")
                    else:
                        st.error(result['message'])

def show_analyze_page():
    """Analyze page with full functionality and multiple visualizations"""
    st.title("📊 Analyze LinkedIn Data")
    
    # Caution message about data format
    st.markdown("""
    <div style="background: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
        <strong>⚠️ CAUTION:</strong> Your data should contain columns with these patterns:
        <ul style="margin-top: 0.5rem; margin-bottom: 0;">
            <li><strong>Date:</strong> 'date', 'time', 'posted', 'published'</li>
            <li><strong>Impressions:</strong> 'impression', 'views', 'reach', 'members reached'</li>
            <li><strong>Likes:</strong> 'like', 'reaction', 'thumbs'</li>
            <li><strong>Comments:</strong> 'comment', 'reply'</li>
            <li><strong>Shares:</strong> 'share', 'repost', 'reshare'</li>
            <li><strong>Post Text:</strong> 'text', 'content', 'post', 'message'</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your LinkedIn engagement data",
        type=['csv', 'xlsx', 'txt'],
        help="Upload CSV, Excel, or text files containing your LinkedIn post metrics",
        key="file_uploader"
    )
    
    if uploaded_file is not None:
        try:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                content = uploaded_file.read().decode('utf-8')
                from io import StringIO
                df = pd.read_csv(StringIO(content))
            
            st.session_state.current_data = df
            
            # Clean data
            with st.spinner('🧹 Cleaning and processing data...'):
                df_clean = clean_linkedin_data(df)
                st.session_state.cleaned_data = df_clean
            
            # Identify columns
            column_mapping = identify_linkedin_columns(df_clean)
            
            # Display results in tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Raw Data", "✨ Cleaned Data", "🔍 Column Detection", "📈 Visualizations"])
            
            with tab1:
                st.subheader("Raw Data Preview")
                st.dataframe(df.head(100), use_container_width=True)
                st.info(f"📊 Total rows: {len(df)} | Total columns: {len(df.columns)}")
                
                st.subheader("Column Names in Your File")
                for col in df.columns:
                    st.markdown(f"• {col}")
            
            with tab2:
                st.subheader("Cleaned Data Preview")
                st.dataframe(df_clean.head(100), use_container_width=True)
                st.info(f"📊 Total rows after cleaning: {len(df_clean)}")
                
                st.success("✅ Removed 'None' strings and empty values")
                st.success("✅ Converted numeric columns (removed commas)")
                st.success("✅ Processed date columns")
            
            with tab3:
                st.subheader("Detected LinkedIn Columns")
                
                # Create mapping table
                mapping_data = []
                for key, value in column_mapping.items():
                    status = "✅ Found" if value else "❌ Not found"
                    mapping_data.append({
                        "Metric": key.replace('_', ' ').title(),
                        "Status": status,
                        "Detected Column": value if value else "-"
                    })
                
                st.dataframe(pd.DataFrame(mapping_data), use_container_width=True)
                
                # Numeric columns stats
                st.subheader("Numeric Columns Statistics")
                numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    stats_data = []
                    for col in numeric_cols:
                        stats_data.append({
                            "Column": col,
                            "Mean": f"{df_clean[col].mean():,.2f}",
                            "Median": f"{df_clean[col].median():,.2f}",
                            "Max": f"{df_clean[col].max():,.0f}",
                            "Min": f"{df_clean[col].min():,.0f}",
                            "Sum": f"{df_clean[col].sum():,.0f}"
                        })
                    st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
                else:
                    st.warning("No numeric columns found")
                
                # Save to history button - KEPT HERE
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col2:
                    if st.button("💾 Save to History", use_container_width=True, key="save_history_btn"):
                        result = mongo_db.save_analysis(
                            st.session_state.user_id,
                            uploaded_file.name,
                            len(df_clean),
                            {k: v for k, v in column_mapping.items() if v},
                            uploaded_file.getvalue()
                        )
                        if result.get('success'):
                            st.success("✅ Analysis saved to history!")
                        else:
                            st.error("❌ Failed to save analysis")
            
            with tab4:
                st.subheader("📈 Visualization Dashboard")
                
                # Generate visualizations
                with st.spinner('🎨 Generating multiple visualizations...'):
                    visualizations = generate_visualizations(df_clean, column_mapping)
                
                if visualizations:
                    st.success(f"✅ Generated {len(visualizations)} visualizations!")
                    
                    # Display visualizations in a grid (2 per row)
                    viz_items = list(visualizations.items())
                    
                    for i in range(0, len(viz_items), 2):
                        cols = st.columns(2)
                        
                        # First chart
                        with cols[0]:
                            name, fig = viz_items[i]
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Second chart (if exists)
                        if i + 1 < len(viz_items):
                            with cols[1]:
                                name, fig = viz_items[i + 1]
                                st.plotly_chart(fig, use_container_width=True)
                    
                    # Summary statistics
                    st.markdown("---")
                    st.subheader("📊 Quick Statistics")
                    
                    cols = st.columns(4)
                    col_idx = 0
                    
                    # Impressions stats
                    if column_mapping.get('impressions'):
                        imp_col = column_mapping['impressions']
                        if imp_col in df_clean.columns and pd.api.types.is_numeric_dtype(df_clean[imp_col]):
                            with cols[col_idx % 4]:
                                st.metric("Total Impressions", f"{df_clean[imp_col].sum():,.0f}")
                                st.metric("Avg Impressions", f"{df_clean[imp_col].mean():,.0f}")
                                col_idx += 1
                    
                    # Likes stats
                    if column_mapping.get('likes'):
                        likes_col = column_mapping['likes']
                        if likes_col in df_clean.columns and pd.api.types.is_numeric_dtype(df_clean[likes_col]):
                            with cols[col_idx % 4]:
                                st.metric("Total Likes", f"{df_clean[likes_col].sum():,.0f}")
                                st.metric("Avg Likes", f"{df_clean[likes_col].mean():,.0f}")
                                col_idx += 1
                    
                    # Comments stats
                    if column_mapping.get('comments'):
                        comm_col = column_mapping['comments']
                        if comm_col in df_clean.columns and pd.api.types.is_numeric_dtype(df_clean[comm_col]):
                            with cols[col_idx % 4]:
                                st.metric("Total Comments", f"{df_clean[comm_col].sum():,.0f}")
                                st.metric("Avg Comments", f"{df_clean[comm_col].mean():,.0f}")
                                col_idx += 1
                    
                    # Shares stats
                    if column_mapping.get('shares'):
                        share_col = column_mapping['shares']
                        if share_col in df_clean.columns and pd.api.types.is_numeric_dtype(df_clean[share_col]):
                            with cols[col_idx % 4]:
                                st.metric("Total Shares", f"{df_clean[share_col].sum():,.0f}")
                                st.metric("Avg Shares", f"{df_clean[share_col].mean():,.0f}")
                                col_idx += 1
                    
                    # Download options
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv = df_clean.to_csv(index=False)
                        b64 = base64.b64encode(csv.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="cleaned_linkedin_data.csv"><button style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:0.75rem; border:none; border-radius:50px; cursor:pointer; width:100%;">📥 Download Cleaned Data (CSV)</button></a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("📄 Generate Summary Report", use_container_width=True):
                            # Create simple report
                            report = f"""
LINKPULSE ANALYTICS REPORT
==========================
File: {uploaded_file.name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
User: {st.session_state.username}

SUMMARY STATISTICS
-----------------
Total Posts: {len(df_clean)}
"""

                            if column_mapping.get('impressions'):
                                imp_col = column_mapping['impressions']
                                if imp_col in df_clean.columns:
                                    report += f"\nImpressions:"
                                    report += f"\n  - Total: {df_clean[imp_col].sum():,.0f}"
                                    report += f"\n  - Average: {df_clean[imp_col].mean():,.0f}"
                                    report += f"\n  - Maximum: {df_clean[imp_col].max():,.0f}"
                            
                            if column_mapping.get('likes'):
                                likes_col = column_mapping['likes']
                                if likes_col in df_clean.columns:
                                    report += f"\n\nLikes:"
                                    report += f"\n  - Total: {df_clean[likes_col].sum():,.0f}"
                                    report += f"\n  - Average: {df_clean[likes_col].mean():,.0f}"
                            
                            if column_mapping.get('comments'):
                                comm_col = column_mapping['comments']
                                if comm_col in df_clean.columns:
                                    report += f"\n\nComments:"
                                    report += f"\n  - Total: {df_clean[comm_col].sum():,.0f}"
                                    report += f"\n  - Average: {df_clean[comm_col].mean():,.0f}"
                            
                            if column_mapping.get('shares'):
                                share_col = column_mapping['shares']
                                if share_col in df_clean.columns:
                                    report += f"\n\nShares:"
                                    report += f"\n  - Total: {df_clean[share_col].sum():,.0f}"
                                    report += f"\n  - Average: {df_clean[share_col].mean():,.0f}"
                            
                            report += "\n\n=========================="
                            
                            b64 = base64.b64encode(report.encode()).decode()
                            href = f'<a href="data:file/txt;base64,{b64}" download="linkedin_report.txt"><button style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:0.75rem; border:none; border-radius:50px; cursor:pointer; width:100%;">📥 Download Report (TXT)</button></a>'
                            st.markdown(href, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Not enough data to generate visualizations. Please check your data format.")
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")

def show_history_page():
    """History page showing all saved analyses"""
    st.title("📜 Analysis History")
    
    # Get analyses from MongoDB
    analyses = mongo_db.get_user_analyses(st.session_state.user_id)
    
    if not analyses:
        st.info("📭 No analysis history yet. Go to the Analyze page and save some analyses!")
    else:
        st.success(f"✅ Found {len(analyses)} saved analyses")
        
        for i, analysis in enumerate(analyses):
            with st.container():
                # Create a card-like container
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: #333;">📁 {analysis['filename']}</h4>
                    <p style="color: #666; margin: 0.5rem 0;">
                        🕒 {analysis.get('analysis_date', 'Unknown date')} | 
                        📊 {analysis.get('rows_analyzed', 0)} rows |
                        📋 {len(analysis.get('detected_metrics', {}))} metrics detected
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show detected metrics if available
                if analysis.get('detected_metrics'):
                    with st.expander("View detected columns"):
                        metrics_data = []
                        for key, value in analysis['detected_metrics'].items():
                            metrics_data.append({"Metric": key, "Column": value})
                        st.dataframe(pd.DataFrame(metrics_data), use_container_width=True)
                
                st.markdown("---")

# ============================================================================
# MAIN APP LOGIC
# ============================================================================

def main():
    """Main routing function"""
    if st.session_state.authenticated:
        show_dashboard()
    else:
        if st.session_state.page == "landing":
            show_landing_page()
        elif st.session_state.page == "login":
            show_login_page()
        elif st.session_state.page == "signup":
            show_signup_page()
        else:
            show_landing_page()

if __name__ == "__main__":
    main()