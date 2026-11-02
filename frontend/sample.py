import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
import warnings
import base64
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

/* Give Streamlit's native widgets a polished, component-like treatment. */
.main .block-container{
    max-width:1500px;
    padding-top:2rem;
    padding-bottom:3rem;
}
.main h1,.main h2,.main h3{
    letter-spacing:-.035em;
    font-weight:720;
}
.main h1{font-size:2.25rem;}
div[data-testid="stVerticalBlockBorderWrapper"]{
    border:1px solid rgba(126,145,180,.24) !important;
    border-radius:18px !important;
    background:linear-gradient(145deg,rgba(99,102,241,.09),rgba(14,165,233,.035)) !important;
    box-shadow:0 10px 30px rgba(15,23,42,.10);
    transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover{
    transform:translateY(-2px);
    border-color:rgba(99,102,241,.48) !important;
    box-shadow:0 14px 34px rgba(15,23,42,.17);
}
div[data-testid="stMetric"]{
    padding:1rem 1.05rem;
    border:1px solid rgba(126,145,180,.22);
    border-radius:16px;
    background:linear-gradient(145deg,rgba(99,102,241,.10),rgba(14,165,233,.04));
}
div[data-testid="stMetricLabel"] p{font-weight:600;}
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] > button{
    min-height:2.65rem;
    border-radius:12px;
    font-weight:650;
    transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease;
}
div[data-testid="stButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover{
    transform:translateY(-1px);
    border-color:rgba(99,102,241,.7);
    box-shadow:0 7px 18px rgba(79,70,229,.18);
}
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stFormSubmitButton"] > button[kind="primary"]{
    border:0;
    background:linear-gradient(110deg,#4f46e5,#0ea5e9);
    color:#fff;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
div[data-testid="stTextInput"] [data-baseweb="input"]{
    border-radius:11px;
}
section[data-testid="stSidebar"] [role="radiogroup"] label{
    transition:background .16s ease,transform .16s ease;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover{
    background:rgba(129,140,248,.14);
}
section[data-testid="stSidebar"] [role="radiogroup"] input[type="radio"]{
    display:none;
}
section[data-testid="stSidebar"] [role="radiogroup"] label{
    padding:.6rem .75rem;
    border:1px solid transparent;
    border-radius:12px;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
    border-color:rgba(129,140,248,.35);
    background:linear-gradient(100deg,rgba(99,102,241,.26),rgba(14,165,233,.12));
}
div[data-testid="stPopover"]{
    position:fixed !important;
    right:24px !important;
    bottom:22px !important;
    z-index:99999 !important;
    width:56px !important;
    min-width:56px !important;
    max-width:56px !important;
}
div[data-testid="stPopover"] [data-testid="stPopoverButton"]{
    box-sizing:border-box !important;
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    width:56px !important;
    height:56px !important;
    min-width:56px !important;
    max-width:56px !important;
    padding:0 !important;
    border:3px solid rgba(255,255,255,.88) !important;
    border-radius:50% !important;
    background:linear-gradient(145deg,#22c55e,#15803d) !important;
    box-shadow:0 8px 26px rgba(15,23,42,.3),0 0 0 5px rgba(34,197,94,.16);
    color:white !important;
}
div[data-testid="stPopover"] [data-testid="stPopoverButton"]:hover{
    transform:scale(1.06);
    box-shadow:none !important;
}
div[data-testid="stPopoverBody"]{
    width:min(390px,calc(100vw - 32px)) !important;
    max-height:72vh !important;
    overflow-y:auto !important;
    border:1px solid rgba(126,145,180,.3) !important;
    border-radius:20px !important;
    box-shadow:0 18px 55px rgba(15,23,42,.3) !important;
}
.salesmitra-chat-teaser{
    position:fixed;
    right:98px;
    bottom:34px;
    z-index:99998;
    display:flex;
    align-items:center;
    gap:.65rem;
    padding:.85rem 1rem;
    border:1px solid rgba(126,145,180,.24);
    border-radius:16px;
    background:var(--background-color);
    box-shadow:0 8px 26px rgba(15,23,42,.2);
    color:var(--text-color);
    font-weight:650;
    white-space:nowrap;
}
.salesmitra-chat-teaser:after{
    content:"";
    position:absolute;
    right:-7px;
    width:13px;
    height:13px;
    transform:rotate(45deg);
    border-top:1px solid rgba(126,145,180,.24);
    border-right:1px solid rgba(126,145,180,.24);
    background:var(--background-color);
}
.salesmitra-chat-status{
    width:10px;
    height:10px;
    border-radius:50%;
    background:#22c55e;
    box-shadow:0 0 0 4px rgba(34,197,94,.14);
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
API_TIMEOUT = (10, 180)  # Includes cold starts and slower Gemini-backed operations.
CHAT_TIMEOUT = (10, 150)

SUGGESTED_HELP_QUESTIONS = [
    "How do I upload a sales file, and which formats are supported?",
    "What does each dashboard and analytics option do?",
    "How do I fix missing or invalid values in my uploaded data?",
    "How can I compare sales by product, branch, or region?",
    "How do I read the sales forecast and its error metrics?",
    "What does the product cluster analysis show?",
    "How do I download or export my analysis?",
    "Why was my repeated upload reused instead of saved again?",
    "How do I manage my account and sign out?",
    "What should I do if Gemini or the backend is unavailable?",
    "Can you explain this chart or screenshot?",
    "What should I check when an upload fails?",
]

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
def ask_chatbot(question, image=None):
    payload = {"query": question}
    if image is not None:
        payload.update({
            "image_data": base64.b64encode(image.getvalue()).decode("ascii"),
            "image_mime_type": image.type or "image/png",
        })
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chatbot/query",
            json=payload,
            timeout=CHAT_TIMEOUT,
        )
        if response.status_code == 200:
            result = response.json()
            if not isinstance(result, dict):
                return {"answer": "The AI service returned an unexpected response. Please retry."}
            answer = result.get("answer")
            if not isinstance(answer, str) or not answer.strip():
                result["answer"] = "I received your question, but the AI service returned an empty reply. Check the backend Gemini key and logs, then retry."
            elif answer.strip().casefold() == question.strip().casefold():
                result["answer"] = "I received your question, but the AI service returned it unchanged. Check that the deployed backend has a valid GEMINI_API_KEY and retry."
            return result
        return {"answer": response_detail(response, "The assistant could not answer that request.")}
    except requests.Timeout:
        return {"answer": "The AI request took too long to finish. Try a shorter question or a smaller image, then retry."}
    except requests.RequestException as exc:
        return {"answer": f"Could not reach the AI assistant: {exc}"}
    except (ValueError, TypeError) as exc:
        return {"answer": f"The AI service returned an unreadable response ({type(exc).__name__}). Please retry."}

def load_sales(dataset_id=None):
    try:
        if dataset_id is None:
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


def _sync_active_dataset_selector():
    """Keep the selected saved analysis in sync when users change the picker."""
    st.session_state.active_dataset_id = st.session_state.get("active_dataset_selector")


def render_saved_dataset_selector(datasets, *, label):
    """Select a saved upload and keep the dashboard and analytics views aligned."""
    if not datasets:
        return None
    by_id = {item["id"]: item for item in datasets}
    dataset_ids = list(by_id)
    active_id = st.session_state.get("active_dataset_id")
    if active_id not in by_id:
        active_id = dataset_ids[0]
        st.session_state.active_dataset_id = active_id
    if st.session_state.get("active_dataset_selector") != active_id:
        st.session_state.active_dataset_selector = active_id

    selected_id = st.selectbox(
        label,
        options=dataset_ids,
        format_func=lambda dataset_id: (
            f"{by_id[dataset_id].get('name', 'Uploaded dataset')} "
            f"({by_id[dataset_id].get('row_count', 0):,} rows)"
        ),
        key="active_dataset_selector",
        on_change=_sync_active_dataset_selector,
    )
    st.session_state.active_dataset_id = selected_id
    return by_id[selected_id]


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


def render_uploaded_dataset(dataset, *, include_advanced=False):
    """Show useful analytics for arbitrary uploaded table columns."""
    # Bind the query to the chosen saved analysis directly. This prevents a
    # stale selector/session value from silently loading another upload.
    df = load_sales(dataset.get("id"))
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
    render_data_quality_report(df)
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
    if include_advanced:
        st.divider()
        render_sales4_style_analysis(df, dataset["id"])
    st.subheader("Uploaded data")
    st.dataframe(df, width="stretch", height=360)


def render_data_quality_report(df):
    """Show actionable, non-blocking checks for common sales-file problems."""
    issues = []
    missing = df.isna() | df.astype("string").apply(lambda column: column.str.strip().eq(""))
    for column, count in missing.sum().items():
        if count:
            issues.append((
                f"{column}: {int(count):,} blank value(s)",
                "Fill the missing cells if the value is known, or leave them blank if unknown. For sales or quantity fields, check that blanks are intentional before relying on totals.",
            ))

    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        issues.append((
            f"{duplicate_count:,} exact duplicate row(s)",
            "Review the repeated rows against the source file. Remove them if they are accidental; keep them if each row is a valid separate transaction.",
        ))

    numeric_terms = ("sales", "revenue", "amount", "price", "profit", "cost", "qty", "quantity", "units")
    for column in df.columns:
        if not any(term in str(column).casefold() for term in numeric_terms):
            continue
        source = df[column].astype("string").str.strip()
        present = source.notna() & source.ne("")
        cleaned = source.str.replace(r"[,₹$€£]", "", regex=True)
        parsed = pd.to_numeric(cleaned, errors="coerce")
        invalid = present & parsed.isna()
        count = int(invalid.sum())
        if count:
            examples = ", ".join(repr(value) for value in source[invalid].dropna().astype(str).unique()[:3])
            issues.append((
                f"{column}: {count:,} value(s) are not numeric (examples: {examples})",
                "Use plain numbers in this column. Remove words, units, or unexpected symbols; keep currency symbols and thousands separators consistent. Values like 'N/A' should be blank or corrected to a number.",
            ))

    with st.expander(f"Data quality checks · {len(issues)} item(s)", expanded=bool(issues)):
        if not issues:
            st.success("No missing cells, exact duplicate rows, or invalid values in sales-like numeric columns were found.")
            return
        st.caption("These checks do not change your uploaded data. Review each item and re-upload a corrected file if needed.")
        for issue, fix in issues:
            st.markdown(f"**{issue}**")
            st.caption(f"How to fix: {fix}")


def _numeric_series(values):
    cleaned = values.astype("string").str.replace(r"[,₹$€£]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def _find_column(df, terms, *, numeric=False):
    """Find an uploaded column by common sales-data names, preferring exact names."""
    normalized = {str(column).strip().casefold().replace("_", " "): column for column in df.columns}
    for term in terms:
        key = term.casefold().replace("_", " ")
        if key in normalized:
            column = normalized[key]
            if not numeric or _numeric_series(df[column]).notna().any():
                return column
    for column in df.columns:
        name = str(column).strip().casefold().replace("_", " ")
        if any(term.casefold().replace("_", " ") in name for term in terms):
            if not numeric or _numeric_series(df[column]).notna().any():
                return column
    return None


def render_product_location_insights(df, dataset_id, *, sales_column=None):
    """Let a user choose a product and inspect its best-performing region and branch."""
    product = _find_column(df, ("brand_name", "brand", "product_name", "product", "item", "sku"))
    region = _find_column(df, ("zone", "region", "territory", "state", "province"))
    place = _find_column(df, ("branch_name", "branch", "store", "outlet", "location", "city", "place"))
    sales = sales_column or _find_column(
        df, ("sales_amt", "sales_amount", "sales", "revenue", "total_sales", "amount", "order_value"), numeric=True
    )
    if not product or not sales:
        st.info("Product location insights need a product/brand column and a numeric sales or revenue column. Check the uploaded file headers and try again.")
        return

    work = df[[product, sales] + ([region] if region and region != product else []) + ([place] if place and place not in (product, region) else [])].copy()
    work[product] = work[product].fillna("Unknown").astype(str)
    work["_sales"] = _numeric_series(work[sales])
    work = work.dropna(subset=["_sales"])
    if work.empty:
        st.info(f"No numeric sales values were found in '{sales}'. Correct that column and upload the file again.")
        return

    totals = work.groupby(product)["_sales"].sum().sort_values(ascending=False)
    product_key = f"cluster_product_{dataset_id}"
    selected = st.selectbox(
        "Choose a product to inspect its strongest sales locations",
        totals.index.tolist(),
        index=0,
        key=product_key,
    )
    selected_rows = work[work[product] == selected]
    location_columns = []
    if region:
        location_columns.append(region)
    if place and place not in location_columns:
        location_columns.append(place)
    if not location_columns:
        st.info("Add a region, zone, branch, store, outlet, city, or location column to see where this product sells best.")
        return

    label_column = location_columns[-1]
    ranking = (selected_rows.groupby(location_columns, dropna=False)["_sales"].sum()
               .sort_values(ascending=False).reset_index())
    if ranking.empty:
        st.info("No sales locations were found for this product.")
        return
    best = ranking.iloc[0]
    place_label = " / ".join(str(best[column]) for column in location_columns)
    first, second, third = st.columns(3)
    first.metric("Selected product", str(selected))
    second.metric("Top-selling region / place", place_label)
    third.metric("Sales at top location", f"{best['_sales']:,.2f}")
    chart = ranking.copy()
    chart["Location"] = chart[location_columns].fillna("Unknown").astype(str).agg(" / ".join, axis=1)
    fig = px.bar(chart.head(20), x="Location", y="_sales", title=f"{selected}: sales by region and place")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(ranking.rename(columns={"_sales": str(sales)}), hide_index=True, width="stretch")


def render_sales4_style_analysis(df, dataset_id):
    """Offer the sales4 analysis menu while applying every view to the active upload."""
    menu = (
        "Quarter vs Year", "Business Metrics", "Branch Analysis", "Product Insights",
        "Credit Notes", "Branch Compare", "Category Compare", "Product Clusters", "ARIMA Forecast",
    )
    selected = st.selectbox("Choose an analysis", menu, key=f"uploaded_analysis_{dataset_id}")
    sales = _find_column(df, ("sales_amt", "sales_amount", "sales", "revenue", "total_sales", "amount", "order_value"), numeric=True)
    quantity = _find_column(df, ("sales_qty", "quantity", "qty", "units_sold", "units", "volume"), numeric=True)
    date = _find_column(df, ("order_date", "sales_date", "date", "mmyyyy", "month", "period", "transaction_date"))
    product = _find_column(df, ("brand_name", "brand", "product_name", "product", "item", "sku"))
    branch = _find_column(df, ("branch_name", "branch", "store", "outlet", "location", "city", "place"))
    region = _find_column(df, ("zone", "region", "territory", "state"))
    category = _find_column(df, ("mkt_type", "category", "product_category", "segment", "channel"))

    def need(columns):
        missing = [label for column, label in columns if column is None]
        if missing:
            st.info("This analysis needs " + " and ".join(missing) + ". Add those columns to the uploaded file to enable it.")
            return False
        return True

    st.subheader(f"📊 {selected}")
    if selected == "Business Metrics":
        if not sales and not quantity:
            need([(sales, "a numeric sales/revenue column"), (quantity, "a numeric quantity column")])
            return
        metrics = st.columns(3)
        metrics[0].metric("Records", f"{len(df):,}")
        if sales:
            values = _numeric_series(df[sales])
            metrics[1].metric("Total sales", f"{values.sum():,.2f}")
            metrics[2].metric("Average sales", f"{values.mean():,.2f}")
        elif quantity:
            metrics[1].metric("Total units", f"{_numeric_series(df[quantity]).sum():,.2f}")
        if quantity and sales:
            st.metric("Total quantity", f"{_numeric_series(df[quantity]).sum():,.2f}")
        dimensions = [c for c in (region, branch, category, product) if c]
        if sales and dimensions:
            dimension = st.selectbox("Compare sales by", dimensions, key=f"metrics_dim_{dataset_id}")
            grouped = df.assign(_value=_numeric_series(df[sales])).groupby(dimension, dropna=False)["_value"].sum().sort_values(ascending=False).head(20).reset_index()
            fig = px.bar(grouped, x=dimension, y="_value", title=f"Sales by {dimension}")
            st.plotly_chart(fig, width="stretch")
    elif selected in ("Quarter vs Year", "Branch Analysis", "Branch Compare"):
        if not need([(sales, "a numeric sales/revenue column"), (date, "a date/order-date column")] + ([] if selected == "Quarter vs Year" else [(branch, "a branch/location column")])):
            return
        work = df.copy()
        work["_date"] = pd.to_datetime(work[date], errors="coerce")
        work["_sales"] = _numeric_series(work[sales])
        work = work.dropna(subset=["_date", "_sales"])
        if work.empty:
            st.info(f"No usable date and numeric sales pairs in '{date}' and '{sales}'. Check the date format and sales values.")
            return
        work["Year"] = work["_date"].dt.year
        work["Quarter"] = "Q" + work["_date"].dt.quarter.astype(str)
        work["Month"] = work["_date"].dt.to_period("M").dt.to_timestamp()
        if selected == "Quarter vs Year":
            quarter = st.selectbox("Quarter", sorted(work["Quarter"].unique()), key=f"quarter_{dataset_id}")
            grouped = work[work["Quarter"] == quarter].groupby("Year", as_index=False)["_sales"].sum()
            fig = px.bar(grouped, x="Year", y="_sales", title=f"{quarter} sales by year")
        elif selected == "Branch Analysis":
            grouped = work.groupby(["Month", branch], as_index=False)["_sales"].sum()
            fig = px.line(grouped, x="Month", y="_sales", color=branch, title="Monthly branch sales")
        else:
            locations = sorted(work[branch].dropna().astype(str).unique())
            chosen = st.multiselect("Branches to compare", locations, default=locations[:min(5, len(locations))], key=f"branch_compare_{dataset_id}")
            grouped = work[work[branch].astype(str).isin(chosen)].groupby(["Month", branch], as_index=False)["_sales"].sum()
            fig = px.line(grouped, x="Month", y="_sales", color=branch, markers=True, title="Branch sales comparison")
        st.plotly_chart(fig, width="stretch")
        st.dataframe(grouped, hide_index=True, width="stretch")
    elif selected == "Product Insights":
        if not need([(sales, "a numeric sales/revenue column"), (product, "a product/brand column")]):
            return
        grouped = df.assign(_sales=_numeric_series(df[sales])).groupby(product, dropna=False)["_sales"].sum().sort_values(ascending=False).head(20).reset_index()
        fig = px.bar(grouped, x=product, y="_sales", title="Top products by sales")
        st.plotly_chart(fig, width="stretch")
        render_product_location_insights(df, dataset_id, sales_column=sales)
    elif selected == "Credit Notes":
        credit = _find_column(df, ("credit_note_amount", "credit amount", "cn_amt", "refund_amount", "refund", "return_amount", "returns", "credit note"), numeric=True)
        if not need([(credit, "a numeric credit-note, refund, or return amount column")]):
            return
        work = df.assign(_credit=_numeric_series(df[credit]))
        st.metric("Total credit notes / returns", f"{work['_credit'].sum():,.2f}")
        dimensions = [column for column in (branch, region, product) if column]
        if dimensions:
            dimension = st.selectbox("Break down credit notes by", dimensions, key=f"credit_dim_{dataset_id}")
            grouped = work.groupby(dimension, dropna=False)["_credit"].sum().sort_values(ascending=False).head(20).reset_index()
            st.plotly_chart(px.bar(grouped, x=dimension, y="_credit", title=f"Credit notes by {dimension}"), width="stretch")
    elif selected == "Category Compare":
        if not need([(sales, "a numeric sales/revenue column"), (category, "a category/channel column")]):
            return
        grouped = df.assign(_sales=_numeric_series(df[sales])).groupby(category, dropna=False)["_sales"].sum().sort_values(ascending=False).reset_index()
        st.plotly_chart(px.bar(grouped.head(30), x=category, y="_sales", title="Sales by category"), width="stretch")
        st.dataframe(grouped, hide_index=True, width="stretch")
    elif selected == "Product Clusters":
        render_uploaded_cluster_analysis(df)
        render_product_location_insights(df, dataset_id, sales_column=sales)
    else:
        render_uploaded_arima_forecast(df)


def render_uploaded_arima_forecast(df):
    """Fit an ARIMA forecast when the uploaded table has dates and a numeric measure."""
    st.subheader("🔮 ARIMA sales forecast")
    date_terms = ("date", "time", "month", "period", "mmyyyy")
    date_column = next(
        (column for column in df.columns if any(term in str(column).casefold() for term in date_terms)),
        None,
    )
    metric_terms = ("sales", "revenue", "amount", "turnover", "total", "price", "profit", "quantity", "qty", "units")
    metric_column = next(
        (column for column in df.columns
         if any(term in str(column).casefold() for term in metric_terms)
         and _numeric_series(df[column]).notna().sum() >= 3),
        None,
    )
    if date_column is None or metric_column is None:
        missing = []
        if date_column is None:
            missing.append("a date/order date column")
        if metric_column is None:
            missing.append("a numeric sales, revenue, amount, or quantity column")
        st.info("ARIMA needs " + " and ".join(missing) + ". Add those columns to the uploaded file to enable forecasting.")
        return

    dated_values = pd.to_datetime(df[date_column], errors="coerce")
    amount_values = _numeric_series(df[metric_column])
    dated = pd.DataFrame({"date": dated_values, "value": amount_values}).dropna()
    if dated.empty:
        st.info(f"No usable date and numeric value pairs were found in '{date_column}' and '{metric_column}'. Correct those columns and upload the file again.")
        return

    dated["month"] = dated["date"].dt.to_period("M").dt.to_timestamp()
    monthly = dated.groupby("month")["value"].sum().sort_index().asfreq("MS", fill_value=0)
    if len(monthly) < 8:
        st.info(f"ARIMA needs at least 8 months of history; this file has {len(monthly)} usable month(s). Upload a longer date range to forecast.")
        return
    if monthly.nunique() < 2:
        st.info("The sales measure is constant over time, so an ARIMA forecast would not be meaningful.")
        return

    try:
        from statsmodels.tsa.arima.model import ARIMA

        order = (1, 1, 1) if len(monthly) >= 18 else (1, 1, 0)
        fitted = ARIMA(
            monthly.astype(float),
            order=order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit()
        prediction = fitted.get_forecast(steps=6)
        forecast_values = prediction.predicted_mean
        intervals = prediction.conf_int()
        forecast = pd.DataFrame({
            "month": forecast_values.index,
            "value": forecast_values.values,
            "lower": intervals.iloc[:, 0].values,
            "upper": intervals.iloc[:, 1].values,
            "series": "Forecast",
        })
        history = pd.DataFrame({"month": monthly.index, "value": monthly.values, "series": "Historical"})
        first, second = st.columns(2)
        first.metric("History", f"{len(monthly)} months")
        second.metric("Next 6 months forecast", f"{forecast['value'].sum():,.2f}")
        chart = pd.concat([history, forecast[["month", "value", "series"]]], ignore_index=True)
        fig = px.line(chart, x="month", y="value", color="series", markers=True,
                      title=f"Monthly {metric_column}: actuals and ARIMA forecast")
        fig.update_layout(xaxis_title="Month", yaxis_title=str(metric_column), legend_title="")
        st.plotly_chart(fig, width="stretch")
        with st.expander("Forecast values and confidence range"):
            st.dataframe(
                forecast.rename(columns={"month": "Month", "value": "Forecast", "lower": "Lower range", "upper": "Upper range"}),
                hide_index=True,
                width="stretch",
            )
    except Exception as exc:
        st.warning(f"ARIMA could not fit this series ({type(exc).__name__}). Check that the date and sales values are valid and try again.")


def render_uploaded_cluster_analysis(df):
    """Cluster uploaded rows with K-means, leaving ID-like columns out of the model."""
    st.subheader("🧩 Product and order clusters")
    identifier_terms = ("id", "code", "phone", "postal", "zip")
    features = {}
    for column in df.columns:
        name = str(column).casefold()
        if any(term in name for term in identifier_terms):
            continue
        values = _numeric_series(df[column])
        if values.notna().sum() >= 3 and values.nunique(dropna=True) > 1:
            features[column] = values

    if not features:
        st.info("Clustering needs at least one varying numeric measure, such as sales, order value, quantity, or profit. Add a numeric measure column to this file.")
        return

    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler

        measures = pd.DataFrame(features).replace([float("inf"), float("-inf")], float("nan"))
        measures = measures.dropna(how="all").fillna(measures.median(numeric_only=True))
        cluster_count = min(3, len(measures.drop_duplicates()))
        if cluster_count < 2:
            st.info("These numeric measures do not contain enough distinct values to form meaningful clusters.")
            return
        labels = KMeans(n_clusters=cluster_count, random_state=42, n_init=10).fit_predict(StandardScaler().fit_transform(measures))
        clustered = measures.copy()
        clustered["Cluster"] = [f"Cluster {label + 1}" for label in labels]
        summary = clustered.groupby("Cluster", as_index=False).size().rename(columns={"size": "Records"})
        averages = clustered.groupby("Cluster", as_index=False)[list(features)].mean()
        summary = summary.merge(averages, on="Cluster")
        st.caption(f"K-means grouped {len(clustered):,} rows using {len(features)} numeric measure(s). Identifier columns were excluded.")
        chart_columns = list(features)
        if len(chart_columns) >= 2:
            fig = px.scatter(clustered, x=chart_columns[0], y=chart_columns[1], color="Cluster",
                             title=f"Clusters by {chart_columns[0]} and {chart_columns[1]}", opacity=0.72)
        else:
            fig = px.box(clustered, x="Cluster", y=chart_columns[0], color="Cluster",
                         title=f"{chart_columns[0]} by cluster")
        st.plotly_chart(fig, width="stretch")
        with st.expander("Cluster averages and row counts"):
            st.dataframe(summary, hide_index=True, width="stretch")
    except Exception as exc:
        st.warning(f"Clustering could not run on these values ({type(exc).__name__}). Review the numeric columns in the data checks above.")


def render_dataset_upload(container=None, key_prefix="sidebar"):
    target = container if container is not None else st.sidebar
    target.caption("CSV, Excel, or PDF · up to 40 MB")
    with target.form(f"{key_prefix}_sales_dataset_upload", clear_on_submit=True):
        uploaded = st.file_uploader(
            "Choose a sales file",
            type=["csv", "xls", "xlsx", "xlsm", "pdf"],
            key=f"{key_prefix}_sales_upload",
        )
        submitted = st.form_submit_button("Upload and analyze", width="stretch")
    if submitted:
        if not uploaded:
            target.warning("Choose a file first.")
        else:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/datasets/upload",
                    headers=dataset_headers(),
                    files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")},
                    timeout=(10, 240),
                )
                if response.status_code == 200:
                    try:
                        result = response.json()
                    except ValueError:
                        target.error("The backend returned an unreadable response. Please try again.")
                        return
                    if not isinstance(result, dict) or "id" not in result:
                        target.error("The backend returned an incomplete upload result. Please try again.")
                        return
                    st.session_state.active_dataset_id = result["id"]
                    # The saved-analysis widget may still hold an older choice.
                    # Set both values before rerunning so a new upload stays active.
                    st.session_state.active_dataset_selector = result["id"]
                    st.session_state.last_upload_result = result
                    st.rerun()
                else:
                    target.error(upload_error_message(response))
            except requests.RequestException as exc:
                target.error(f"Upload failed: {exc}")


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
    email = st.session_state.get("user_email", "")
    display_name = st.session_state.get("user_name") or email.split("@", 1)[0] or "there"
    with st.container(border=True):
        st.caption("YOUR AI SALES WORKSPACE")
        st.title(f"Welcome to SalesMitra, {display_name} 👋")
        st.markdown(
            "Turn sales files into clear summaries, charts, comparisons, and forecasts. "
            "Spot changes sooner and spend less time cleaning spreadsheets or building reports by hand."
        )
    with st.container(border=True):
        st.markdown("### 🚀 Get started")
        st.write("Upload a sales file to create a saved analysis with summaries, charts, and data checks.")
        render_dataset_upload(container=st.container(), key_prefix="dashboard")
    purpose_columns = st.columns(3)
    purpose_cards = [
        ("📊  Understand performance", "See key sales, quantity, and product metrics at a glance."),
        ("🔎  Find useful patterns", "Compare products, branches, and regions to see what is changing."),
        ("⚡  Save time", "Upload a file once, reopen saved analyses, and get a head start on reporting."),
    ]
    for column, (title, description) in zip(purpose_columns, purpose_cards):
        with column:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.caption(description)

    datasets = load_datasets()
    if datasets:
        st.subheader("Your previous analyses")
        st.caption("Your uploads are saved to your account. Choose one to reopen its charts, summary, and data checks.")
        history = pd.DataFrame([
            {
                "File": item.get("name", "Uploaded dataset"),
                "Uploaded": (item.get("created_at") or "").replace("T", " ")[:16] or "Date unavailable",
                "Rows": item.get("row_count", 0),
                "Columns": len(item.get("columns", [])),
            }
            for item in datasets[:10]
        ])
        st.dataframe(history, hide_index=True, width="stretch")
        selected_dataset = render_saved_dataset_selector(datasets, label="Open a saved analysis")
        render_uploaded_dataset(selected_dataset)
        return

    st.info("Start by uploading a CSV, Excel, or PDF sales file in the sidebar. Your analysis will appear here and be saved to your account for next time.")

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
    active = render_saved_dataset_selector(uploaded_sets, label="Sales dataset for this analysis")
    if active is not None:
        render_uploaded_dataset(active, include_advanced=True)
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
    render_uploaded_arima_forecast(df)

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
        st.info("The saved-sales clustering service returned no cluster records. Showing local clusters from the available numeric sales data instead.")
        render_uploaded_cluster_analysis(df)

def render_shared_assistant():
    """Render the fixed bottom-right assistant launcher on signed-in pages."""
    st.markdown(
        '<div class="salesmitra-chat-teaser"><span class="salesmitra-chat-status"></span>How may I help you?</div>',
        unsafe_allow_html=True,
    )
    with st.popover("💬", type="primary", help="Ask SalesMitra AI", width="content", key="salesmitra_help_launcher"):
        st.markdown("### SalesMitra help")
        st.caption("Ask about the platform or attach a screenshot of a chart or error.")
        for chat in st.session_state.chat_history[-8:]:
            with st.chat_message(chat["role"]):
                st.markdown(chat["content"])
        if not st.session_state.chat_history:
            st.info("Try: How do I upload data? · What does this chart mean? · How can I fix my file?")
        if st.button("Clear conversation", key="clear_floating_chat"):
            st.session_state.chat_history = []
            st.rerun()
        with st.form("floating_chat_form", clear_on_submit=True):
            question = st.text_input("Your question", placeholder="Ask SalesMitra…", key="floating_chat_question")
            image = st.file_uploader(
                "Attach a screenshot (optional)",
                type=["png", "jpg", "jpeg", "webp"],
                key="floating_chat_image",
            )
            submitted = st.form_submit_button("Send to SalesMitra AI", type="primary", width="stretch")
        if submitted:
            question = (question or "").strip()
            if not question and not image:
                st.warning("Enter a question or attach an image.")
            else:
                if not question:
                    question = "Explain this image in the context of SalesMitra and tell me how to fix any visible error."
                _submit_assistant_question(question, image=image)


def _submit_assistant_question(question, image=None):
    user_text = question + (f"\n\n_Attached image: {image.name}_" if image else "")
    st.session_state.chat_history.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        with st.spinner("SalesMitra AI is checking your question…"):
            result = ask_chatbot(question, image=image)
        answer = result.get("answer", "No response was returned.")
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
            ["🏠 Dashboard", "📊 Sales Analytics", "👤 Profile"]
        )

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
    elif page == "👤 Profile":
        render_profile()
    render_shared_assistant()
