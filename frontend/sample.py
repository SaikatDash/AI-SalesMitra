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

# Sidebar layout styled to match the requested SalesMitra navigation.
st.markdown("""
<style>
section[data-testid="stSidebar"]{
    width:300px !important;
    min-width:300px !important;
    max-width:300px !important;
    background:#25262d !important;
    border-right:1px solid #3b3c45;
}
[data-testid="stSidebarNav"]{
    display:none;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1{
    color:#f5f6fa;
    font-size:1.55rem;
    margin-bottom:1rem;
}
section[data-testid="stSidebar"] [data-testid="stAlert"]{
    background:#244a3c;
    border:0;
    border-radius:10px;
}
section[data-testid="stSidebar"] [role="radiogroup"]{
    gap:.12rem;
}
section[data-testid="stSidebar"] [role="radiogroup"] label{
    padding:.35rem .2rem;
    border-radius:4px;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
    background:#484954;
}
</style>
""", unsafe_allow_html=True)


# ======================================================
# API & CONFIG
# ======================================================
def get_api_url():
    local_urls = ("http://localhost", "https://localhost", "http://127.0.0.1", "https://127.0.0.1")
    try:
        secret_url = st.secrets["API_BASE_URL"]
        if secret_url and not secret_url.lower().startswith(local_urls):
            return secret_url.rstrip("/")
    except Exception:
        pass
    env_url = os.getenv("API_BASE_URL")
    if env_url and not env_url.lower().startswith(local_urls):
        return env_url.rstrip("/")
    return "https://ai-salesmitra-dnxg.onrender.com"

API_BASE_URL = get_api_url()
API_TIMEOUT = (10, 120)  # Render instances can take a while to wake from idle.

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
    "access_token": None,
    "active_dataset_id": None,
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
            timeout=API_TIMEOUT,
        )
        if response.status_code in (200, 201):
            return {"success": True, "data": response.json()}
        return {"success": False, "message": response.json().get("detail", "Registration failed")}
    except requests.Timeout:
        return {"success": False, "message": "The backend is taking longer than usual to start. Wait a minute and try again."}
    except requests.RequestException as e:
        return {"success": False, "message": f"Could not reach the backend: {e}"}

def login_user(email, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/login",
            json={"email": email, "password": password},
            timeout=API_TIMEOUT,
        )
        if response.status_code == 200:
            user = response.json()
            st.session_state.user_logged_in = True
            st.session_state.user_id = user.get("id")
            st.session_state.user_email = user.get("email")
            st.session_state.access_token = user.get("access_token")
            return {"success": True, "data": user}
        return {"success": False, "message": response.json().get("detail", "Invalid credentials")}
    except requests.Timeout:
        return {"success": False, "message": "The backend is taking longer than usual to start. Wait a minute and try again."}
    except requests.RequestException as e:
        return {"success": False, "message": f"Could not reach the backend: {e}"}

def logout():
    for key in ["user_logged_in", "user_id", "user_email", "user_name", "chat_history", "access_token", "active_dataset_id"]:
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
        dataset_id = st.session_state.get("active_dataset_id")
        if dataset_id:
            response = requests.get(
                f"{API_BASE_URL}/api/datasets/{dataset_id}/rows",
                headers={"Authorization": f"Bearer {st.session_state.get('access_token', '')}"},
                timeout=API_TIMEOUT,
            )
            if response.status_code == 200:
                return pd.DataFrame(response.json())
        response = requests.get(f"{API_BASE_URL}/api/sales", timeout=API_TIMEOUT)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except Exception:
        pass
    return pd.DataFrame()


def dataset_headers():
    token = st.session_state.get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


def response_detail(response, fallback):
    try:
        payload = response.json()
    except ValueError:
        return fallback
    return payload.get("detail", fallback) if isinstance(payload, dict) else fallback


def upload_error_message(response):
    if response.status_code == 404:
        return (
            "The configured backend does not include the uploaded-data API yet. "
            "Redeploy the backend with this project version, then retry the upload."
        )
    return response_detail(response, "Upload failed.")


def load_datasets():
    try:
        response = requests.get(f"{API_BASE_URL}/api/datasets", headers=dataset_headers(), timeout=API_TIMEOUT)
        datasets = response.json() if response.status_code == 200 else []
        return datasets if isinstance(datasets, list) else []
    except (requests.RequestException, ValueError):
        return []


def render_uploaded_dataset(dataset):
    """Show useful analytics for arbitrary uploaded table columns."""
    df = load_sales()
    if df.empty:
        st.warning("This dataset has no rows to analyze.")
        return
    normalized = {str(column).strip().lower(): column for column in df.columns}
    amount = next((normalized[name] for name in normalized
                   if any(term in name for term in ("sales", "revenue", "amount", "total"))
                   and not any(term in name for term in ("qty", "quantity", "units", "volume"))
                   and pd.to_numeric(df[normalized[name]], errors="coerce").notna().any()), None)
    quantity = next((normalized[name] for name in normalized if any(term in name for term in ("qty", "quantity", "units")) and pd.to_numeric(df[normalized[name]], errors="coerce").notna().any()), None)
    dimensions = [column for column in df.columns if column not in (amount, quantity) and df[column].nunique(dropna=True) <= 100]
    st.caption(f"{dataset['name']} · {len(df):,} records · {len(df.columns)} columns")
    if amount:
        values = pd.to_numeric(df[amount], errors="coerce")
        a, b, c = st.columns(3)
        a.metric(f"Total {amount}", f"{values.sum():,.2f}")
        b.metric(f"Average {amount}", f"{values.mean():,.2f}")
        c.metric("Records", f"{len(df):,}")
    if quantity:
        st.metric(f"Total {quantity}", f"{pd.to_numeric(df[quantity], errors='coerce').sum():,.2f}")
    if amount and dimensions:
        dimension = st.selectbox("Break down sales by", dimensions, key=f"dataset_dimension_{dataset['id']}")
        chart_df = df.assign(_amount=pd.to_numeric(df[amount], errors="coerce")).groupby(dimension, dropna=False)["_amount"].sum().sort_values(ascending=False).head(20).reset_index()
        chart_df[dimension] = chart_df[dimension].astype(str)
        st.plotly_chart(px.bar(chart_df, x=dimension, y="_amount", title=f"{amount} by {dimension}"), width="stretch")
    st.subheader("Uploaded data")
    st.dataframe(df, width="stretch", height=360)


def render_dataset_upload():
    st.sidebar.markdown("### 📤 Upload sales data")
    st.sidebar.caption("CSV, Excel, or PDF · up to 15 MB")
    with st.sidebar.form("sales_dataset_upload", clear_on_submit=True):
        uploaded = st.file_uploader("Choose a sales file", type=["csv", "xls", "xlsx", "xlsm", "pdf"], key="sidebar_sales_upload")
        submitted = st.form_submit_button("Upload and analyze", use_container_width=True)
    if submitted:
        if not uploaded:
            st.sidebar.warning("Choose a file first.")
        else:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/datasets/upload",
                    headers=dataset_headers(),
                    files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")},
                    timeout=180,
                )
                if response.status_code == 200:
                    try:
                        result = response.json()
                    except ValueError:
                        st.sidebar.error("The backend returned an unreadable response. Please try again.")
                        return
                    if not isinstance(result, dict) or "id" not in result:
                        st.sidebar.error("The backend returned an incomplete upload result. Please try again.")
                        return
                    st.session_state.active_dataset_id = result["id"]
                    st.session_state.last_upload_result = result
                    st.rerun()
                else:
                    st.sidebar.error(upload_error_message(response))
            except requests.RequestException as exc:
                st.sidebar.error(f"Upload failed: {exc}")


def render_upload_result():
    result = st.session_state.pop("last_upload_result", None)
    if not result:
        return
    st.success(f"{'Created' if result['created'] else 'Reused'} dataset: {result['name']} ({result['row_count']:,} rows).")
    insight = result.get("insight", "Gemini did not return an analysis for this upload.")
    if "Gemini analysis is unavailable" in insight or "Gemini analysis could not finish" in insight:
        st.error(insight)
    else:
        st.markdown("**Gemini analysis**")
        st.markdown(insight)


def load_summary():
    try:
        response = requests.get(f"{API_BASE_URL}/api/sales/summary", timeout=API_TIMEOUT)
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

    datasets = load_datasets()
    if datasets:
        by_id = {item["id"]: item for item in datasets}
        if st.session_state.get("active_dataset_id") not in by_id:
            st.session_state.active_dataset_id = datasets[0]["id"]
        selected_id = st.selectbox(
            "Active dataset",
            options=list(by_id),
            format_func=lambda dataset_id: f"{by_id[dataset_id]['name']} ({by_id[dataset_id]['row_count']:,} rows)",
            index=list(by_id).index(st.session_state.active_dataset_id),
            key="active_dataset_selector",
        )
        st.session_state.active_dataset_id = selected_id
        render_uploaded_dataset(by_id[selected_id])
        return

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
    uploaded_sets = load_datasets()
    active = next((item for item in uploaded_sets if item["id"] == st.session_state.get("active_dataset_id")), None)
    if active:
        render_uploaded_dataset(active)
        return
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
        records = clusters.get("records", [])
        cluster_groups = clusters.get("clusters", [])
        projected_profit = sum(
            float(record.get("projected_next_year_profit") or 0)
            for record in records
            if isinstance(record, dict)
        )
        product_count = len({record.get("brand_name") for record in records if isinstance(record, dict) and record.get("brand_name")})
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Clusters", len(cluster_groups))
        with col2: st.metric("Projected Profit", f"₹ {projected_profit:,.2f}")
        with col3: st.metric("Products", product_count)

        if len(records):
            cluster_df = pd.DataFrame(records)
            chart_columns = {"total_sales", "projected_next_year_profit", "cluster"}
            if chart_columns.issubset(cluster_df.columns):
                fig = px.scatter(
                    cluster_df,
                    x="total_sales",
                    y="projected_next_year_profit",
                    color="cluster",
                    hover_name="brand_name" if "brand_name" in cluster_df.columns else None,
                    title="Sales vs Projected Profit by Product and Location",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Cluster results are missing the fields needed for this chart.")
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
        render_dataset_upload()
        
        st.divider()
        if backend_available():
            st.success("🟢 Backend Connected")
        else:
            st.error("🔴 Backend Offline")
            
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    render_upload_result()

    # Render Selected Page
    if page == "🏠 Dashboard":
        render_dashboard()
    elif page == "📊 Sales Analytics":
        render_analytics()
    elif page == "🤖 AI Chatbot":
        render_chatbot()
    elif page == "👤 Profile":
        render_profile()
