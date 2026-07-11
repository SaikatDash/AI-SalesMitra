import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
import warnings
from io import BytesIO

warnings.filterwarnings("ignore")

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="SalesMitra AI",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS to hide default sidebar elements if desired
st.markdown("""
<style>
section[data-testid="stSidebar"]{
    width:300px !important;
    min-width:300px !important;
    max-width:300px !important;
}
[data-testid="stSidebarNav"]{
    display:none;
}
</style>
""", unsafe_allow_html=True)


# ======================================================
# API & CONFIG
# ======================================================
def get_api_url():
    env_url = os.getenv("API_BASE_URL")
    if env_url:
        return env_url.rstrip("/")
    try:
        return st.secrets["API_BASE_URL"].rstrip("/")
    except Exception:
        pass
    return "http://localhost:8000"

API_BASE_URL = get_api_url()

def backend_available():
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=3)
        return response.status_code == 200
    except Exception:
        return False

# ======================================================
# SESSION STATE
# ======================================================
DEFAULT_SESSION = {
    "user_logged_in": False,
    "user_id": None,
    "user_email": "",
    "user_name": "",
    "dark_mode": False,
    "current_page": "🏠 Dashboard",
    "show_signup_form": False,
    "chat_history": []
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ======================================================
# AUTH FUNCTIONS
# ======================================================
def register_user(email, password, full_name=""):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/register",
            json={"email": email, "password": password, "full_name": full_name},
            timeout=20,
        )
        if response.status_code in (200, 201):
            return {"success": True, "data": response.json()}
        return {"success": False, "message": response.json().get("detail", "Registration failed")}
    except Exception as e:
        return {"success": False, "message": str(e)}

def login_user(email, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/login",
            json={"email": email, "password": password},
            timeout=20,
        )
        if response.status_code == 200:
            user = response.json()
            st.session_state.user_logged_in = True
            st.session_state.user_id = user.get("id")
            st.session_state.user_email = user.get("email")
            return {"success": True, "data": user}
        return {"success": False, "message": response.json().get("detail", "Invalid credentials")}
    except Exception as e:
        return {"success": False, "message": str(e)}

def logout():
    for key in ["user_logged_in", "user_id", "user_email", "user_name", "chat_history"]:
        st.session_state[key] = DEFAULT_SESSION[key]
    st.rerun()

# ======================================================
# DATA & AI FUNCTIONS
# ======================================================
def ask_chatbot(question):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chatbot/query",
            json={"query": question},
            timeout=60,
        )
        if response.status_code == 200:
            return response.json()
        return {"answer": "Chatbot returned an error."}
    except Exception as e:
        return {"answer": str(e)}

def load_sales():
    try:
        response = requests.get(f"{API_BASE_URL}/api/sales", timeout=30)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except Exception:
        pass
    return pd.DataFrame()

def load_summary():
    try:
        response = requests.get(f"{API_BASE_URL}/api/sales/summary", timeout=20)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {"total_records": 0, "total_sales": 0, "total_qty": 0, "avg_sales": 0}

def load_clusters():
    try:
        response = requests.get(f"{API_BASE_URL}/api/analytics/product-location-clusters", timeout=60)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}

# ======================================================
# UI PAGES
# ======================================================

def render_auth():
    st.markdown("<h1 style='text-align: center;'>💊 SalesMitra AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>AI Powered Sales Analytics</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.show_signup_form:
            st.subheader("Login")
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.warning("Please enter both email and password.")
                    else:
                        with st.spinner("Logging in..."):
                            res = login_user(email, password)
                            if res["success"]:
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error(res["message"])
            if st.button("Need an account? Sign up here", use_container_width=True):
                st.session_state.show_signup_form = True
                st.rerun()
        else:
            st.subheader("Sign Up")
            with st.form("signup_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Register", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.warning("Please fill out all fields.")
                    else:
                        with st.spinner("Registering..."):
                            res = register_user(email, password, name)
                            if res["success"]:
                                st.success("Registration successful! Please log in.")
                                st.session_state.show_signup_form = False
                                st.rerun()
                            else:
                                st.error(res["message"])
            if st.button("Already have an account? Log in", use_container_width=True):
                st.session_state.show_signup_form = False
                st.rerun()

def render_dashboard():
    st.title("📊 Sales Dashboard")
    st.caption("AI Powered Medicine Sales Analytics")
    
    st.markdown(f"""
    <div style="padding:15px; border-radius:10px; background:linear-gradient(135deg,#2563eb,#7c3aed); color:white; margin-bottom:20px;">
    <h3>Welcome back 👋, {st.session_state.user_email}</h3>
    </div>
    """, unsafe_allow_html=True)

    summary = load_summary()
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("💰 Total Sales", f"₹ {summary.get('total_sales', 0):,.2f}")
    with col2: st.metric("📦 Total Quantity", f"{summary.get('total_qty', 0):,.0f}")
    with col3: st.metric("📄 Total Records", f"{summary.get('total_records', 0):,}")
    with col4: st.metric("📈 Average Sales", f"₹ {summary.get('avg_sales', 0):,.2f}")

    st.divider()
    df = load_sales()

    if df.empty:
        st.warning("No sales data available.")
    else:
        st.subheader("Sales Dataset")
        st.dataframe(df, use_container_width=True, height=300)

        # Download Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            "⬇ Download Excel",
            buffer.getvalue(),
            "sales.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if "sales_amt" in df.columns:
                fig = px.histogram(df, x="sales_amt", nbins=40, title="Sales Amount Distribution")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "sales_qty" in df.columns:
                fig = px.histogram(df, x="sales_qty", nbins=30, title="Sales Quantity Distribution")
                st.plotly_chart(fig, use_container_width=True)

        if "brand_name" in df.columns:
            st.divider()
            brand_sales = df.groupby("brand_name")["sales_amt"].sum().sort_values(ascending=False).head(10).reset_index()
            fig = px.bar(brand_sales, x="brand_name", y="sales_amt", title="Top 10 Brands")
            st.plotly_chart(fig, use_container_width=True)

    if st.button("🔄 Refresh Dashboard"):
        st.rerun()

def render_analytics():
    st.title("📈 Sales Analytics")
    st.caption("Advanced AI Powered Analytics")
    df = load_sales()

    if df.empty:
        st.warning("No sales data found.")
        return

    st.sidebar.subheader("Filters")
    if "zone" in df.columns:
        zones = ["All"] + sorted(df["zone"].dropna().unique().tolist())
        selected_zone = st.sidebar.selectbox("Zone", zones)
        if selected_zone != "All":
            df = df[df["zone"] == selected_zone]

    if "brand_name" in df.columns:
        brands = ["All"] + sorted(df["brand_name"].dropna().unique().tolist())
        selected_brand = st.sidebar.selectbox("Brand", brands)
        if selected_brand != "All":
            df = df[df["brand_name"] == selected_brand]

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Filtered Records", len(df))
    with c2: 
        if "sales_amt" in df.columns: st.metric("Sales", f"₹ {df['sales_amt'].sum():,.2f}")
    with c3:
        if "sales_qty" in df.columns: st.metric("Quantity", f"{df['sales_qty'].sum():,.0f}")

    st.subheader("Filtered Dataset")
    st.dataframe(df, use_container_width=True, height=300)

    chart1, chart2 = st.columns(2)
    with chart1:
        if "zone" in df.columns:
            zone_sales = df.groupby("zone")["sales_amt"].sum().reset_index()
            fig = px.pie(zone_sales, names="zone", values="sales_amt", title="Sales by Zone")
            st.plotly_chart(fig, use_container_width=True)
    with chart2:
        if "branch_name" in df.columns:
            branch_sales = df.groupby("branch_name")["sales_amt"].sum().reset_index()
            fig = px.bar(branch_sales, x="branch_name", y="sales_amt", title="Branch Sales")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🧠 Product Location Cluster Analysis")
    clusters = load_clusters()
    if clusters:
        summary = clusters.get("summary", {})
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Clusters", summary.get("cluster_count", 0))
        with col2: st.metric("Projected Profit", f"₹ {summary.get('projected_profit',0):,.2f}")
        with col3: st.metric("Products", summary.get("product_count",0))

        records = clusters.get("records", [])
        if len(records):
            cluster_df = pd.DataFrame(records)
            if "cluster" in cluster_df.columns:
                fig = px.scatter(cluster_df, x="sales_amt", y="predicted_profit", color="cluster", hover_name="brand_name", title="Cluster Visualization")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No cluster analysis available.")

def render_chatbot():
    st.title("🤖 SalesMitra AI Assistant")
    st.caption("Ask anything about Sales, Products, Forecasting or Navigation.")

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🗑 Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    st.divider()
    
    if len(st.session_state.chat_history) == 0:
        st.info("Try asking:\n• Show top selling brands\n• Which zone has highest sales?\n• Predict next month's sales")

    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    prompt = st.chat_input("Ask SalesMitra AI...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = ask_chatbot(prompt)
                answer = result.get("answer", "No response.")
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

def render_profile():
    st.title("👤 Profile & Settings")
    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("User Information")
        st.text_input("Email", value=st.session_state.user_email, disabled=True)
        st.text_input("User ID", value=str(st.session_state.user_id), disabled=True)

    with col2:
        st.subheader("Application")
        st.metric("Backend API", API_BASE_URL)
        
    st.divider()
    st.subheader("System Status")
    
    if st.button("🔄 Test Backend Connection"):
        if backend_available():
            st.success("Connection Successful - Backend is Healthy")
        else:
            st.error("Backend Connection Failed")

# ======================================================
# MAIN ROUTING LOGIC
# ======================================================

if not st.session_state.user_logged_in:
    # Render the login / registration form if not logged in
    render_auth()
else:
    # Render sidebar and main navigation if logged in
    with st.sidebar:
        st.markdown("# 💊 SalesMitra AI")
        st.success(f"👤 {st.session_state.user_email}")
        st.divider()
        
        page = st.radio(
            "Navigation",
            ["🏠 Dashboard", "📊 Sales Analytics", "🤖 AI Chatbot", "👤 Profile"]
        )
        
        st.divider()
        if backend_available():
            st.success("🟢 Backend Connected")
        else:
            st.error("🔴 Backend Offline")
            
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    # Render Selected Page
    if page == "🏠 Dashboard":
        render_dashboard()
    elif page == "📊 Sales Analytics":
        render_analytics()
    elif page == "🤖 AI Chatbot":
        render_chatbot()
    elif page == "👤 Profile":
        render_profile()