import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
from io import BytesIO
import warnings
from pathlib import Path
import sys

# ============================================
# CONFIGURATION
# ============================================
API_BASE_URL = "http://localhost:8000"  # Backend URL
st.set_page_config(page_title="SalesMitraAI:You Personal Sales Assistant API", layout="wide", initial_sidebar_state="collapsed")

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "show_login_form" not in st.session_state:
    st.session_state.show_login_form = False

if "show_signup_form" not in st.session_state:
    st.session_state.show_signup_form = False

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ============================================
# THEME DETECTION
# ============================================
def get_theme_colors():
    """Get color scheme based on current theme"""
    if st.session_state.dark_mode:
        return {
            'bg_primary': '#0f172a',
            'bg_secondary': '#1e293b',
            'text_primary': '#f1f5f9',
            'text_secondary': '#cbd5e1',
            'accent_blue': '#3b82f6',
            'accent_cyan': '#0ea5e9',
            'accent_purple': '#8b5cf6',
            'accent_red': '#ef4444',
            'border_color': 'rgba(148, 163, 184, 0.2)',
            'shadow': 'rgba(0, 0, 0, 0.3)',
        }
    else:
        return {
            'bg_primary': '#ffffff',
            'bg_secondary': '#f8fafc',
            'text_primary': '#1e293b',
            'text_secondary': '#64748b',
            'accent_blue': '#3b82f6',
            'accent_cyan': '#0ea5e9',
            'accent_purple': '#8b5cf6',
            'accent_red': '#ef4444',
            'border_color': 'rgba(59, 130, 246, 0.2)',
            'shadow': 'rgba(59, 130, 246, 0.15)',
        }

# ============================================
# API FUNCTIONS
# ============================================
def register_user(email: str, password: str) -> dict:
    """Register a new user with backend"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/register",
            json={"email": email, "password": password},
            timeout=15
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend server"}
    except Exception as e:
        return {"error": str(e)}


def login_user(email: str, password: str) -> dict:
    """Login user with backend"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/login",
            json={"email": email, "password": password},
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Login failed")
            return {"success": False, "message": error_detail}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Cannot connect to backend server"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def logout_user():
    """Logout user"""
    st.session_state.user_logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.success("Logged out successfully!")

# ============================================
# DYNAMIC STYLING WITH THEME SUPPORT
# ============================================
def get_custom_css():
    """Generate dynamic CSS based on current theme"""
    colors = get_theme_colors()
    
    css = f"""
    <style>
    :root {{
        --bg-primary: {colors['bg_primary']};
        --bg-secondary: {colors['bg_secondary']};
        --text-primary: {colors['text_primary']};
        --text-secondary: {colors['text_secondary']};
        --accent-blue: {colors['accent_blue']};
        --accent-cyan: {colors['accent_cyan']};
        --accent-purple: {colors['accent_purple']};
        --accent-red: {colors['accent_red']};
        --border-color: {colors['border_color']};
        --shadow: {colors['shadow']};
    }}
    
    * {{
        color: {colors['text_primary']};
    }}
    
    /* Main Container */
    .main {{
        background-color: {colors['bg_primary']};
    }}
    
    [data-testid="stAppViewContainer"] {{
        background-color: {colors['bg_primary']};
    }}
    
    [data-testid="stHeader"] {{
        background-color: {colors['bg_primary']};
    }}
    
    /* Login Container */
    .login-container {{
        max-width: 500px;
        margin: 50px auto;
        padding: 50px;
        background: linear-gradient(135deg, {colors['bg_secondary']} 0%, {colors['bg_secondary']} 100%);
        border-radius: 20px;
        border: 2px solid {colors['border_color']};
        box-shadow: 0 20px 60px {colors['shadow']};
        transition: all 0.3s ease;
    }}
    
    .login-container:hover {{
        transform: translateY(-5px);
        box-shadow: 0 30px 80px {colors['shadow']};
    }}
    
    .form-header {{
        text-align: center;
        color: {colors['accent_blue']};
        margin-bottom: 40px;
    }}
    
    .form-header h1 {{
        margin: 0;
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(135deg, {colors['accent_blue']} 0%, {colors['accent_purple']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    .form-header p {{
        color: {colors['text_secondary']};
        margin: 10px 0 0 0;
        font-size: 16px;
    }}
    
    .form-group {{
        margin-bottom: 25px;
    }}
    
    /* Input Fields */
    input {{
        background-color: {colors['bg_primary']};
        color: {colors['text_primary']};
        border: 2px solid {colors['border_color']};
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 16px;
        transition: all 0.3s ease;
    }}
    
    input:focus {{
        border-color: {colors['accent_blue']};
        box-shadow: 0 0 0 3px {colors['shadow']};
        outline: none;
    }}
    
    input::placeholder {{
        color: {colors['text_secondary']};
    }}
    
    /* Buttons */
    .auth-button {{
        width: 100%;
        padding: 14px;
        border-radius: 12px;
        border: none;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 16px;
    }}
    
    .primary-button {{
        background: linear-gradient(135deg, {colors['accent_blue']} 0%, {colors['accent_cyan']} 100%);
        color: white;
        box-shadow: 0 10px 30px {colors['shadow']};
    }}
    
    .primary-button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 15px 40px {colors['shadow']};
    }}
    
    .primary-button:active {{
        transform: translateY(-1px);
    }}
    
    .button-group {{
        display: flex;
        gap: 12px;
        margin-top: 20px;
    }}
    
    .toggle-form-text {{
        text-align: center;
        color: {colors['text_secondary']};
        margin-top: 25px;
        font-size: 14px;
    }}
    
    .toggle-form-text a {{
        color: {colors['accent_blue']};
        text-decoration: none;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .toggle-form-text a:hover {{
        text-decoration: underline;
        color: {colors['accent_cyan']};
    }}
    
    /* Navbar Styling */
    .navbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        border-bottom: 2px solid {colors['border_color']};
        margin-bottom: 30px;
        background: linear-gradient(90deg, {colors['bg_secondary']} 0%, {colors['bg_primary']} 100%);
    }}
    
    .navbar-title {{
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, {colors['accent_blue']} 0%, {colors['accent_purple']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    .navbar-user {{
        display: flex;
        align-items: center;
        gap: 20px;
    }}
    
    .user-email {{
        color: {colors['text_secondary']};
        font-weight: 500;
        padding: 8px 16px;
        background-color: {colors['bg_secondary']};
        border-radius: 8px;
        border: 1px solid {colors['border_color']};
    }}
    
    .logout-button {{
        background: linear-gradient(135deg, {colors['accent_red']} 0%, #dc2626 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px {colors['shadow']};
    }}
    
    .logout-button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 25px {colors['shadow']};
    }}
    
    .theme-toggle {{
        background: linear-gradient(135deg, {colors['accent_purple']} 0%, {colors['accent_blue']} 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px {colors['shadow']};
        font-size: 16px;
    }}
    
    .theme-toggle:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 25px {colors['shadow']};
    }}
    
    .dashboard-container {{
        padding: 20px 0;
        background-color: {colors['bg_primary']};
    }}
    
    /* Home Page Styling */
    .home-container {{
        text-align: center;
        padding: 40px 20px;
    }}
    
    .home-title {{
        font-size: 48px;
        font-weight: 700;
        background: linear-gradient(135deg, {colors['accent_blue']} 0%, {colors['accent_purple']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 10px;
    }}
    
    .home-subtitle {{
        font-size: 20px;
        color: {colors['text_secondary']};
        margin-bottom: 40px;
    }}
    
    .features-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin: 30px 0;
    }}
    
    .feature-card {{
        padding: 25px;
        background: linear-gradient(135deg, {colors['bg_secondary']} 0%, {colors['bg_secondary']} 100%);
        border-radius: 15px;
        border: 2px solid {colors['border_color']};
        transition: all 0.3s ease;
    }}
    
    .feature-card:hover {{
        transform: translateY(-10px);
        box-shadow: 0 20px 50px {colors['shadow']};
    }}
    
    .feature-card h3 {{
        color: {colors['accent_blue']};
        margin-top: 0;
    }}
    
    .demo-box {{
        background: linear-gradient(135deg, {colors['bg_secondary']} 0%, {colors['bg_secondary']} 100%);
        padding: 30px;
        border-radius: 15px;
        border: 2px solid {colors['border_color']};
        margin: 30px 0;
        box-shadow: 0 10px 30px {colors['shadow']};
    }}
    
    .demo-box h3 {{
        color: {colors['accent_blue']};
        margin-top: 0;
    }}
    
    .demo-credentials {{
        text-align: left;
        background-color: {colors['bg_primary']};
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid {colors['accent_blue']};
        font-family: 'Courier New', monospace;
    }}
    
    .demo-credentials p {{
        margin: 8px 0;
        color: {colors['text_secondary']};
    }}
    
    .demo-credentials strong {{
        color: {colors['accent_blue']};
    }}
    
    /* Success/Error Messages */
    .stSuccess {{
        background-color: {colors['bg_secondary']};
        border-left: 4px solid #10b981;
    }}
    
    .stError {{
        background-color: {colors['bg_secondary']};
        border-left: 4px solid {colors['accent_red']};
    }}
    
    .stInfo {{
        background-color: {colors['bg_secondary']};
        border-left: 4px solid {colors['accent_blue']};
    }}
    
    .stWarning {{
        background-color: {colors['bg_secondary']};
        border-left: 4px solid #f59e0b;
    }}
    
    /* Divider */
    hr {{
        border-color: {colors['border_color']};
        margin: 30px 0;
    }}
    
    /* Form labels */
    label {{
        color: {colors['text_primary']};
        font-weight: 500;
    }}
    
    /* Back button */
    .back-button {{
        background-color: {colors['bg_secondary']};
        color: {colors['accent_blue']};
        border: 2px solid {colors['border_color']};
        padding: 10px 20px;
        border-radius: 10px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .back-button:hover {{
        background-color: {colors['border_color']};
        transform: translateX(-5px);
    }}
    
    /* Animations */
    @keyframes slideIn {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .login-container {{
        animation: slideIn 0.5s ease;
    }}
    
    /* Responsive Design */
    @media (max-width: 768px) {{
        .navbar {{
            flex-direction: column;
            gap: 15px;
            padding: 15px 0;
        }}
        
        .navbar-user {{
            width: 100%;
            justify-content: space-between;
        }}
        
        .home-title {{
            font-size: 36px;
        }}
        
        .login-container {{
            margin: 20px 10px;
            padding: 30px;
        }}
    }}
    
    </style>
    """
    return css

st.markdown(get_custom_css(), unsafe_allow_html=True)

# ============================================
# MAIN APPLICATION
# ============================================

# Show navbar if logged in
if st.session_state.user_logged_in:
    col1, col2, col3, col4 = st.columns([2, 2, 1.2, 0.8])
    with col1:
        st.markdown("### 💊 SalesMitraAI:You Personal Sales Report Analyzer Assistant")
    with col2:
        st.markdown(f"**Welcome, {st.session_state.user_email}**")
    with col3:
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            logout_user()
            st.rerun()
    with col4:
        theme_emoji = "🌙 Dark" if not st.session_state.dark_mode else "☀️ Light"
        if st.button(theme_emoji, key="theme_toggle", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    st.divider()

# ============================================
# NOT LOGGED IN - SHOW AUTH FORMS
# ============================================
if not st.session_state.user_logged_in:
    
    # SIGNUP FORM
    if st.session_state.show_signup_form:
        # Add theme toggle at top right on signup page
        col_spacer, col_theme = st.columns([8, 1])
        with col_theme:
            theme_emoji = "🌙 Dark" if not st.session_state.dark_mode else "☀️ Light"
            if st.button(theme_emoji, key="theme_toggle_signup", use_container_width=True):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div class="form-header">
                    <h1>📝 Create Account</h1>
                    <p>Join us today & start analyzing</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("signup_form", clear_on_submit=True):
                email = st.text_input("📧 Email Address", placeholder="your@example.com")
                password = st.text_input("🔐 Password", type="password", placeholder="Enter a strong password")
                confirm_password = st.text_input("🔐 Confirm Password", type="password", placeholder="Confirm your password")
                
                st.markdown("""
                    **Password Requirements:**
                    - Minimum 6 characters
                    - Should be secure
                """)
                
                submitted = st.form_submit_button("✅ Sign Up", use_container_width=True)
                
                if submitted:
                    if not email or not password or not confirm_password:
                        st.error("❌ Please fill in all fields")
                    elif password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    elif "@" not in email:
                        st.error("❌ Please enter a valid email address")
                    else:
                        result = register_user(email, password)
                        if "error" in result:
                            st.error(f"❌ {result['error']}")
                        else:
                            st.success("✅ Registration successful! Please login.")
                            st.session_state.show_signup_form = False
                            st.session_state.show_login_form = True
                            st.rerun()
            
            st.markdown("""
                <div class="toggle-form-text">
                    Already have an account? Click login below
                </div>
            """, unsafe_allow_html=True)
            
            col_back, col_login = st.columns(2)
            with col_back:
                if st.button("← Back to Auth", key="back_from_signup", use_container_width=True):
                    st.session_state.show_signup_form = False
                    st.rerun()
            with col_login:
                if st.button("🔐 Go to Login", key="go_to_login", use_container_width=True):
                    st.session_state.show_signup_form = False
                    st.session_state.show_login_form = True
                    st.rerun()
    
    # LOGIN FORM
    elif st.session_state.show_login_form:
        # Add theme toggle at top right on login page
        col_spacer, col_theme = st.columns([8, 1])
        with col_theme:
            theme_emoji = "🌙 Dark" if not st.session_state.dark_mode else "☀️ Light"
            if st.button(theme_emoji, key="theme_toggle_login", use_container_width=True):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div class="form-header">
                    <h1>🔐 Login</h1>
                    <p>Welcome back to your dashboard</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=True):
                email = st.text_input("📧 Email Address", placeholder="your@example.com")
                password = st.text_input("🔐 Password", type="password", placeholder="Enter your password")
                
                submitted = st.form_submit_button("✅ Login", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.error("❌ Please fill in all fields")
                    else:
                        result = login_user(email, password)
                        if result.get("id"):
                            st.session_state.user_logged_in = True
                            st.session_state.user_id = result.get("id")
                            st.session_state.user_email = email
                            st.session_state.show_login_form = False
                            st.success("✅ Login successful! Welcome back!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result.get('message', 'Login failed')}")
            
            st.markdown("""
                <div class="toggle-form-text">
                    New here? Click sign up below
                </div>
            """, unsafe_allow_html=True)
            
            col_back, col_signup = st.columns(2)
            with col_back:
                if st.button("← Back to Auth", key="back_from_login", use_container_width=True):
                    st.session_state.show_login_form = False
                    st.rerun()
            with col_signup:
                if st.button("📝 Go to Sign Up", key="go_to_signup", use_container_width=True):
                    st.session_state.show_login_form = False
                    st.session_state.show_signup_form = True
                    st.rerun()
    
    # HOME PAGE - SHOW LOGIN/SIGNUP BUTTONS
    else:
        # Add theme toggle at top right on home page
        col_spacer, col_theme = st.columns([8, 1])
        with col_theme:
            theme_emoji = "🌙 Dark" if not st.session_state.dark_mode else "☀️ Light"
            if st.button(theme_emoji, key="theme_toggle_home", use_container_width=True):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div class="home-container">
                    <div class="home-title">💊 SalesMitraAI</div>
                    <div class="home-subtitle">You Personal Sales Reposrt Making Assistant </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                ### Welcome to Medicine Sales Analytics
                
                Unlock the power of data-driven insights for your medicine business.
                
            """)
            
            # Feature cards
            st.markdown("""
                <div class="features-grid">
                    <div class="feature-card">
                        <h3>📊 Sales Forecasting</h3>
                        <p>ARIMA, Prophet & ML models for accurate predictions</p>
                    </div>
                    <div class="feature-card">
                        <h3>📈 Advanced Analytics</h3>
                        <p>Territory & customer analysis with real-time insights</p>
                    </div>
                    <div class="feature-card">
                        <h3>📋 Smart Reports</h3>
                        <p>Automated insights & interactive dashboards</p>
                    </div>
                    <div class="feature-card">
                        <h3>🎯 Predictions</h3>
                        <p>Churn & demand forecasting for better planning</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🔐 Login", use_container_width=True, key="nav_login"):
                    st.session_state.show_login_form = True
                    st.rerun()
            
            with col_btn2:
                if st.button("📝 Sign Up", use_container_width=True, key="nav_signup"):
                    st.session_state.show_signup_form = True
                    st.rerun()
            
            st.markdown("""
                <div class="demo-box">
                    <h3>🎯 Try Demo Credentials</h3>
                    <div class="demo-credentials">
                        <p><strong>Email:</strong> admin@example.com</p>
                        <p><strong>Password:</strong> admin123</p>
                    </div>
                    <p style="margin-top: 15px; font-size: 14px;">Click "Login" and use these credentials to explore the full dashboard.</p>
                </div>
            """, unsafe_allow_html=True)

# ============================================
# LOGGED IN - SHOW SALES DASHBOARD
# ============================================
else:
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    
    # Load and display sales4 dashboard
    try:
        warnings.filterwarnings('ignore')
        
        # Find sales4.py
        sales4_path = Path(__file__).parent / "sales4.py"
        
        if not sales4_path.exists():
            st.error(f"❌ sales4.py not found at {sales4_path}")
        else:
            # Read the sales4 file with UTF-8 encoding
            with open(sales4_path, 'r', encoding='utf-8') as f:
                sales4_code = f.read()
            
            # Remove st.set_page_config to avoid conflicts
            sales4_code = sales4_code.replace('st.set_page_config(', '# st.set_page_config(')
            
            # Create execution context with necessary imports
            exec_globals = {
                '__name__': '__main__',
                '__file__': str(sales4_path),
                'st': st,
                'pd': pd,
                'px': px,
                'BytesIO': BytesIO,
                'warnings': warnings,
                'json': json,
                'requests': requests,
            }
            
            # Execute the code
            exec(sales4_code, exec_globals)
            
    except Exception as e:
        st.error(f"❌ Error loading sales dashboard: {str(e)}")
        with st.expander("See error details"):
            import traceback
            st.code(traceback.format_exc())
    
    st.markdown('</div>', unsafe_allow_html=True)
