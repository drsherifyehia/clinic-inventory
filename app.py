import io
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime
from difflib import get_close_matches

# =============================================================
# DARK MODE CSS — injected before anything renders
# =============================================================
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root tokens ── */
:root {
    --bg-base:      #0a0d12;
    --bg-surface:   #111620;
    --bg-card:      #161c2a;
    --bg-input:     #1a2235;
    --border:       #1f2d45;
    --border-focus: #2e7cf6;
    --text-primary: #e8edf5;
    --text-muted:   #6b7c99;
    --text-dim:     #3d4f6e;
    --accent-blue:  #2e7cf6;
    --accent-teal:  #0ecfb0;
    --accent-red:   #f63e3e;
    --accent-amber: #f6a623;
    --accent-green: #22c55e;
    --radius:       10px;
    --radius-lg:    16px;
}

/* ── Global reset ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"], .main, .block-container {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stAppViewContainer"] p:not([style*="color"]),
[data-testid="stAppViewContainer"] span:not([style*="color"]),
[data-testid="stAppViewContainer"] li:not([style*="color"]),
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span {
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}
[data-testid="stSidebarNav"] {
    padding-top: 1rem;
}

h1, h2, h3, h4 {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent-blue), #1a56d6) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 12px rgba(46,124,246,0.25) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(46,124,246,0.4) !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {
    background-color: var(--bg-input) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--border-focus) !important;
    box-shadow: 0 0 0 2px rgba(46,124,246,0.15) !important;
}

[data-testid="stFileUploader"] {
    background-color: var(--bg-card) !important;
    border: 1px dashed var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent-blue) !important;
}

[data-testid="stMetric"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] p {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.6rem !important;
}

[data-testid="stDataFrameContainer"] {
    border-radius: var(--radius-lg) !important;
    border: 1px solid var(--border) !important;
    overflow: hidden !important;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: var(--bg-surface) !important;
    border-radius: var(--radius) !important;
    gap: 4px !important;
    padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
.stTabs [data-baseweb="tab"] p {
    color: var(--text-muted) !important;
}
.stTabs [aria-selected="true"] {
    background-color: var(--bg-card) !important;
}
.stTabs [aria-selected="true"] p {
    color: var(--text-primary) !important;
}

.streamlit-expanderHeader {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}
.streamlit-expanderContent {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
}

.stAlert {
    border-radius: var(--radius) !important;
    border: none !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stInfoBox"]    { background-color: rgba(46,124,246,0.08) !important; border-left: 3px solid var(--accent-blue) !important; }
[data-testid="stWarningBox"] { background-color: rgba(246,166,35,0.08) !important; border-left: 3px solid var(--accent-amber) !important; }
[data-testid="stErrorBox"]   { background-color: rgba(246,62,62,0.08) !important;  border-left: 3px solid var(--accent-red) !important; }
[data-testid="stSuccessBox"] { background-color: rgba(34,197,94,0.08) !important;  border-left: 3px solid var(--accent-green) !important; }

[data-baseweb="popover"], [data-baseweb="menu"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
[role="option"] {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
}
[role="option"]:hover {
    background-color: var(--bg-input) !important;
}

hr { border-color: var(--border) !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }

.stDownloadButton > button {
    background: var(--bg-card) !important;
    color: var(--accent-blue) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px rgba(46,124,246,0.15) !important;
}

.stRadio > div {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1rem !important;
    gap: 0.5rem !important;
}
.stRadio label {
    font-family: 'DM Sans', sans-serif !important;
}

[data-baseweb="tag"] {
    background-color: rgba(46,124,246,0.15) !important;
    border: 1px solid rgba(46,124,246,0.3) !important;
    border-radius: 6px !important;
}
[data-baseweb="tag"] span {
    color: var(--accent-blue) !important;
}

[data-testid="stSlider"] > div > div > div {
    background-color: var(--accent-blue) !important;
}

.clinic-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.4rem;
    margin-bottom: 1rem;
}

.page-header {
    padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.page-header h2 {
    margin: 0 !important;
    font-size: 1.4rem !important;
    background: linear-gradient(90deg, var(--text-primary), var(--text-muted));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.page-header p {
    margin: 0.25rem 0 0 0;
    color: var(--text-muted);
    font-size: 0.85rem;
}

.sidebar-logo {
    padding: 1.2rem 1rem 0.5rem 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.sidebar-logo h1 {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-teal));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 !important;
}
.sidebar-logo p {
    color: var(--text-muted);
    font-size: 0.72rem;
    margin: 0.15rem 0 0 0;
}

.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: 'DM Sans', sans-serif;
    letter-spacing: 0.03em;
}
.badge-blue  { background: rgba(46,124,246,0.12); color: var(--accent-blue) !important; border: 1px solid rgba(46,124,246,0.25); }
.badge-green { background: rgba(34,197,94,0.12);  color: var(--accent-green) !important; border: 1px solid rgba(34,197,94,0.25); }
.badge-amber { background: rgba(246,166,35,0.12); color: var(--accent-amber) !important; border: 1px solid rgba(246,166,35,0.25); }
.badge-red   { background: rgba(246,62,62,0.12);  color: var(--accent-red) !important;   border: 1px solid rgba(246,62,62,0.25); }
</style>
"""


# =============================================================
# PASSWORD GATE
# =============================================================
def check_password():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    st.markdown(DARK_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div style="max-width:400px;margin:8rem auto;text-align:center">
        <div style="font-size:3rem;margin-bottom:1rem">🦷</div>
        <h1 style="font-family:'DM Sans',sans-serif;font-size:1.6rem;font-weight:600;
                   background:linear-gradient(90deg,#2e7cf6,#0ecfb0);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   margin-bottom:0.25rem">Clinic Inventory Hub</h1>
        <p style="color:#6b7c99;font-size:0.85rem;margin-bottom:2rem">
            Enter your access password to continue
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        entered = st.text_input(
            "Password",
            type             = "password",
            label_visibility = "collapsed",
            placeholder      = "Enter password...",
            key              = "login_password"
        )
        if st.button("Continue →", use_container_width=True):
            if entered == st.secrets["auth"]["password"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.caption("Contact your clinic administrator if you don't have access.")
    return False

if not check_password():
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title = "Clinic Inventory Hub",
    layout     = "wide",
    page_icon  = "🦷",
    initial_sidebar_state = "expanded"
)
st.markdown(DARK_CSS, unsafe_allow_html=True)


# =============================================================
# CONSTANTS
# =============================================================
METHOD_LABELS = {
    "first_transaction" : "📌 First Transaction Date",
    "rolling_window"    : "🔁 Rolling Window (last N months)",
    "date_range"        : "📅 Custom Date Range",
}

PRICE_METHODS = {
    "Last Recorded Price" : "Price_Last",
    "Highest Price"       : "Price_High",
    "Average Price"       : "Price_Avg",
}

USAGE_FIELDS = {
    "Created" : "📅 Transaction Date",
    "Item"    : "🏷️ Item Name",
    "Type"    : "📂 Category / Type",
    "Amount"  : "🔢 Quantity Used",
    "Price"   : "💰 Unit Price",
}

STOCK_FIELDS = {
    "Item"    : "🏷️ Item Name",
    "Type_S2" : "📂 Category / Type",
    "Branch"  : "🏢 Branch Stock",
    "Master"  : "🗄️ Master Stock",
}

DENTOLIZE_USAGE_IDX  = {"Created": 12, "Item": 8, "Type": 10, "Amount": 2, "Price": 5}
DENTOLIZE_STOCK_IDX  = {"Item": 1, "Type_S2": 3, "Branch": 5, "Master": 6}

MIN_WINDOW_MONTHS = 1 / 30

_BASE_MONTH   = pd.Timestamp.now().normalize().replace(day=1)
MONTH_OPTIONS = [
    (_BASE_MONTH + pd.DateOffset(months=i)).strftime("%B %Y")
    for i in range(12)
]

PAGES = [
    ("📂", "Upload",            "upload"),
    ("📊", "AMU",               "amu"),
    ("⚙️", "Forecast",          "forecast"),
    ("🛒", "Shopping List",     "shopping"),
    ("🛠️", "Adjust",            "adjust"),
    ("🚨", "Anomaly Detection", "anomaly"),
    ("🤖", "AI Assistant",      "ai"),
]


# =============================================================
# HELPERS — UI
# =============================================================
def page_header(title, subtitle=""):
    st.markdown(f"""
    <div class="page-header">
        <h2>{title}</h2>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def card_start():
    st.markdown('<div class="clinic-card">', unsafe_allow_html=True)

def card_end():
    st.markdown('</div>', unsafe_allow_html=True)


def badge(text, color="blue"):
    st.markdown(f'<span class="badge badge-{color}">{text}</span>', unsafe_allow_html=True)


# =============================================================
# TEMPLATE GENERATORS
# =============================================================
@st.cache_resource
def generate_usage_template():
    df     = pd.DataFrame(columns=["Created", "inventoryItem", "inventoryType", "Amount", "Price"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Usage Transactions')
        ws = writer.sheets['Usage Transactions']
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 22
    return output.getvalue()


@st.cache_resource
def generate_stock_template():
    df     = pd.DataFrame(columns=["Name", "Type", "branchAmount", "masterAmount"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventory')
        ws = writer.sheets['Inventory']
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 22
    return output.getvalue()


# =============================================================
# PASTE PARSER
# =============================================================
def parse_pasted_data(pasted_text, source_name):
    if not pasted_text or not pasted_text.strip():
        return None
    try:
        df = pd.read_csv(io.StringIO(pasted_text), sep='\t')
        if len(df.columns) == 1:
            df = pd.read_csv(io.StringIO(pasted_text), sep=',')
        df = df.dropna(how='all')
        if df.empty:
            st.warning(f"⚠️ Pasted data for {source_name} appears empty.")
            return None
        return df
    except Exception as e:
        st.error(f"❌ Could not parse pasted data for {source_name}: {e}")
        return None


# =============================================================
# COLUMN MAPPER UI
# =============================================================
def render_column_mapper(df, fields, key_prefix):
    cols_available = ["— select —"] + list(df.columns)
    mapping  = {}
    complete = True

    grid = st.columns(len(fields))
    for i, (internal, label) in enumerate(fields.items()):
        with grid[i]:
            suggestion  = next(
                (c for c in df.columns if internal.lower() in c.lower() or c.lower() in internal.lower()),
                None
            )
            default_idx = cols_available.index(suggestion) if suggestion else 0
            chosen = st.selectbox(label, options=cols_available, index=default_idx,
                                  key=f"{key_prefix}_{internal}")
            if chosen == "— select —":
                complete = False
            else:
                mapping[internal] = chosen

    return mapping if complete else None


def apply_mapping(df, mapping):
    selected = {v: k for k, v in mapping.items()}
    return df[list(selected.keys())].rename(columns=selected).copy()


def apply_dentolize_usage(df):
    result = pd.DataFrame()
    for internal, idx in DENTOLIZE_USAGE_IDX.items():
        result[internal] = df.iloc[:, idx]
    return result


def apply_dentolize_stock(df):
    result = pd.DataFrame()
    for internal, idx in DENTOLIZE_STOCK_IDX.items():
        result[internal] = df.iloc[:, idx]
    return result


# =============================================================
# MANUAL ENTRY FORM
# =============================================================
def render_manual_entry_form(target):
    if target == 'usage':
        st.markdown("**Add a usage transaction row:**")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: m_date   = st.date_input("Date", key="man_date")
        with c2: m_item   = st.text_input("Item Name", key="man_item")
        with c3: m_type   = st.text_input("Category", key="man_type")
        with c4: m_amount = st.number_input("Quantity", min_value=0.0, key="man_amount")
        with c5: m_price  = st.number_input("Price", min_value=0.0, key="man_price")

        if st.button("➕ Add Row", key="man_add_usage"):
            if m_item:
                new_row = pd.DataFrame([{
                    "Created": pd.to_datetime(m_date),
                    "Item"   : m_item,
                    "Type"   : m_type,
                    "Amount" : m_amount,
                    "Price"  : m_price,
                }])
                existing = st.session_state.get('manual_usage', pd.DataFrame())
                st.session_state.manual_usage = pd.concat([existing, new_row], ignore_index=True)
                st.success("Row added.")
            else:
                st.warning("Item name is required.")

        if 'manual_usage' in st.session_state and not st.session_state.manual_usage.empty:
            st.dataframe(st.session_state.manual_usage, use_container_width=True)
            if st.button("✅ Use this as Usage Data", key="man_use_usage"):
                st.session_state.usage_mapped = st.session_state.manual_usage.copy()
                st.session_state.usage_raw    = st.session_state.manual_usage.copy()
                st.success("✅ Manual usage data saved.")

    else:
        st.markdown("**Add an inventory item:**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: s_item   = st.text_input("Item Name", key="man_s_item")
        with c2: s_type   = st.text_input("Category", key="man_s_type")
        with c3: s_branch = st.number_input("Branch Stock", min_value=0.0, key="man_s_branch")
        with c4: s_master = st.number_input("Master Stock", min_value=0.0, key="man_s_master")

        if st.button("➕ Add Row", key="man_add_stock"):
            if s_item:
                new_row = pd.DataFrame([{
                    "Item"    : s_item,
                    "Type_S2" : s_type,
                    "Branch"  : s_branch,
                    "Master"  : s_master,
                }])
                existing = st.session_state.get('manual_stock', pd.DataFrame())
                st.session_state.manual_stock = pd.concat([existing, new_row], ignore_index=True)
                st.success("Row added.")
            else:
                st.warning("Item name is required.")

        if 'manual_stock' in st.session_state and not st.session_state.manual_stock.empty:
            st.dataframe(st.session_state.manual_stock, use_container_width=True)
            if st.button("✅ Use this as Inventory Data", key="man_use_stock"):
                st.session_state.stock_df     = st.session_state.manual_stock.copy()
                st.session_state.stock_mapped = st.session_state.manual_stock.copy()
                st.success("✅ Manual inventory data saved.")


# =============================================================
# CACHED FILE LOADERS
# =============================================================
@st.cache_data
def load_excel_files(uploaded_files):
    if not uploaded_files:
        return pd.DataFrame()
    dfs = [pd.read_excel(f, engine='openpyxl') for f in uploaded_files]
    return pd.concat(dfs, ignore_index=True)


@st.cache_data
def load_single_excel(uploaded_file):
    if not uploaded_file:
        return None
    try:
        df         = pd.read_excel(uploaded_file, engine='openpyxl')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return f"ERR: {str(e)}"


# =============================================================
# AMU CALCULATION
# =============================================================
def calculate_amu(df_mapped, method, rolling_months=None, date_from=None, date_to=None):
    df            = df_mapped.copy()
    df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
    df['Amount']  = pd.to_numeric(df['Amount'],   errors='coerce').fillna(0)
    df['Price']   = pd.to_numeric(df['Price'],    errors='coerce').fillna(0)
    df            = df.dropna(subset=['Created'])

    now = pd.Timestamp.now()

    if method == 'rolling_window' and rolling_months:
        cutoff        = now - pd.DateOffset(months=rolling_months)
        df            = df[df['Created'] >= cutoff]
        window_months = max(rolling_months, MIN_WINDOW_MONTHS)
    elif method == 'date_range' and date_from and date_to:
        date_from     = pd.to_datetime(date_from)
        date_to       = pd.to_datetime(date_to)
        df            = df[(df['Created'] >= date_from) & (df['Created'] <= date_to)]
        window_months = max((date_to - date_from).days / 30, MIN_WINDOW_MONTHS)
    else:
        window_months = None

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df   = df.sort_values('Created')
    cons = df.groupby(['Item', 'Type']).agg(
        Amount     = ('Amount',  'sum'),
        Price_Avg  = ('Price',   'mean'),
        Price_High = ('Price',   'max'),
        Price_Last = ('Price',   'last'),
        Created    = ('Created', 'min')
    ).reset_index()

    cons['Price_Avg']  = cons['Price_Avg'].round(2)
    cons['Price_Last'] = cons['Price_Last'].round(2)
    cons['Price_High'] = cons['Price_High'].round(2)

    if method == 'first_transaction':
        cons['No. of Months'] = cons['Created'].apply(
            lambda x: max(MIN_WINDOW_MONTHS, (now - x).days / 30)
            if pd.notnull(x) else MIN_WINDOW_MONTHS
        )
    else:
        cons['No. of Months'] = window_months

    cons['AMU'] = np.where(
        cons['No. of Months'] > 0,
        (cons['Amount'] / cons['No. of Months']).round(2), 0
    )

    amu_df = cons[['Item', 'Type', 'Price_Last', 'Price_High', 'Price_Avg', 'AMU']]
    return cons, amu_df


# =============================================================
# VECTORIZED TARGET DATE
# =============================================================
def calc_target_vectorized(master_series, amu_series):
    master = pd.to_numeric(master_series, errors='coerce').fillna(0)
    amu    = pd.to_numeric(amu_series,    errors='coerce').fillna(0)
    months = np.where(amu > 0, np.ceil(master / amu), 0).astype(int)
    base   = pd.Period(pd.Timestamp.now(), 'M')
    return pd.PeriodIndex([base + int(m) for m in months]).to_timestamp()


# =============================================================
# FUZZY MATCH
# =============================================================
@st.cache_data
def run_fuzzy_match(unmatched_items, usage_names_tuple):
    usage_names = list(usage_names_tuple)
    return {
        name: (get_close_matches(name, usage_names, n=1, cutoff=0.6) or ["No Close Match Found"])[0]
        for name in unmatched_items
    }


# =============================================================
# ANOMALY DETECTION
# =============================================================
@st.cache_data
def calculate_anomalies(usage_json, amu_json, lookback, over_t, under_t, types_tuple):
    df            = pd.read_json(io.StringIO(usage_json))
    df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
    df['Amount']  = pd.to_numeric(df['Amount'],   errors='coerce').fillna(0)
    df            = df.dropna(subset=['Created'])

    amu = pd.read_json(io.StringIO(amu_json))
    amu = amu[amu['Type'].isin(list(types_tuple))]

    cutoff = pd.Timestamp.now() - pd.DateOffset(months=lookback)
    window = df[df['Created'] >= cutoff]
    if window.empty:
        return pd.DataFrame()

    actual = window.groupby(['Item', 'Type']).agg(Actual_Usage=('Amount', 'sum')).reset_index()
    ref    = amu[['Item', 'Type', 'AMU']].copy()
    ref['Expected_Usage'] = (ref['AMU'] * lookback).round(2)

    r                  = pd.merge(ref, actual, on=['Item', 'Type'], how='left')
    r['Actual_Usage']  = r['Actual_Usage'].fillna(0)
    r['Variance']      = (r['Actual_Usage'] - r['Expected_Usage']).round(2)
    r['Variance_%_raw']= np.where(
        r['Expected_Usage'] > 0,
        ((r['Variance'] / r['Expected_Usage']) * 100).round(1),
        np.where(r['Actual_Usage'] > 0, 999.0, 0.0)
    )

    pct  = r['Variance_%_raw']
    r['Flag'] = np.select(
        [pct >= over_t*2.5, pct >= over_t, pct <= -under_t*2.5, pct <= -under_t],
        ['🔴 Investigate', '🟡 Watch', '🔵 Severely Under', '🔵 Under'],
        default='🟢 Normal'
    )
    r['Variance_%'] = r['Variance_%_raw'].apply(
        lambda x: '⚠️ New Item' if x == 999.0 else f"{x:+.1f}%"
    )
    return r.sort_values('Variance_%_raw', ascending=False)


# =============================================================
# AI ASSISTANT — FIXED WITH GROQ + DEEPSEEK R1
# =============================================================
def build_data_context():
    """Builds full data context for deep AI analysis."""
    parts = []

    if st.session_state.shared_amu is not None:
        amu = st.session_state.shared_amu
        parts.append(f"=== AMU TABLE ({len(amu)} items) ===")
        parts.append(amu.to_string(index=False))

    if st.session_state.merged_data is not None:
        m = st.session_state.merged_data
        parts.append(f"\n=== FORECAST TABLE ({len(m)} items) ===")
        parts.append(m[['Item', 'Type', 'AMU', 'Branch', 'Master', 'TargetDate']].to_string(index=False))

    if st.session_state.stock_df is not None:
        s = st.session_state.stock_df
        parts.append(f"\n=== INVENTORY TABLE ({len(s)} items) ===")
        parts.append(s.to_string(index=False))

    if not parts:
        return "No data loaded yet. Ask the user to upload data first."

    return "\n\n".join(parts)


def ask_ai(question, history):
    """Calls Groq API with full data context and deep analysis instructions."""
    context = build_data_context()

    system = f"""You are an expert inventory analyst for a dental clinic with deep knowledge of supply chain management.

You have access to the clinic's COMPLETE inventory data below.
Perform detailed analysis when asked — calculate totals, identify patterns,
flag risks, compare items, and give specific actionable recommendations.
Always cite specific item names and numbers from the data.
If asked to rank or compare, show a proper analysis.
Respond in the same language as the user (English or Arabic).

{context}"""

    messages = [{"role": "system", "content": system}]
    for h in history:
        messages.append({"role": "user",      "content": h["user"]})
        messages.append({"role": "assistant", "content": h["ai"]})
    messages.append({"role": "user", "content": question})

    try:
        api_key = st.secrets["groq"]["api_key"]

        import requests
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type"  : "application/json",
                "Authorization" : f"Bearer {api_key}",
            },
            json={
                "model"      : "deepseek-r1-distill-llama-70b",
                "messages"   : messages,
                "max_tokens" : 2000,
            },
            timeout=30
        )

        data = resp.json()

        if resp.status_code != 200:
            return f"⚠️ Error {resp.status_code}: {data.get('error', {}).get('message', str(data))}"

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"⚠️ Could not reach AI: {str(e)}"


# =============================================================
# INITIALIZE SESSION STATE
# =============================================================
defaults = {
    'usage_raw'    : pd.DataFrame(),
    'usage_mapped' : None,
    'stock_df'     : None,
    'stock_mapped' : None,
    'shared_amu'   : None,
    'merged_data'  : None,
    'cons_view'    : None,
    'amu_method'         : 'first_transaction',
    'amu_rolling_months' : 6,
    'amu_date_from'      : date(2024, 1, 1),
    'amu_date_to'        : date.today(),
    'data_hash'          : None,
    'current_page'       : 'upload',
    'ai_open'            : False,
    'ai_history'         : [],
    'ai_input'           : '',
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =============================================================
# SIDEBAR NAVIGATION
# =============================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h1>🦷 Clinic Hub</h1>
        <p>Inventory Management System</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Navigation**")
    for icon, label, page_key in PAGES:
        is_active = st.session_state.current_page == page_key
        btn_label = f"{icon}  {label}"
        if is_active:
            st.markdown(f"""
            <div style="background:rgba(46,124,246,0.12);border:1px solid rgba(46,124,246,0.25);
                        border-radius:8px;padding:0.5rem 0.8rem;margin-bottom:4px;
                        color:#2e7cf6;font-family:'DM Sans',sans-serif;font-weight:600;font-size:0.88rem">
                {icon} {label}
            </div>""", unsafe_allow_html=True)
        else:
            if st.button(btn_label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()

    st.divider()

    st.markdown("**Data Status**")
    usage_ok = st.session_state.usage_mapped is not None
    stock_ok = st.session_state.stock_df is not None
    amu_ok   = st.session_state.shared_amu is not None

    st.markdown(f"""
    <div style="display:flex;flex-direction:column;gap:6px;margin-top:4px">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="color:#6b7c99;font-size:0.8rem;font-family:'DM Sans',sans-serif">Usage Data</span>
            <span class="badge {'badge-green' if usage_ok else 'badge-amber'}">
                {'✓ Ready' if usage_ok else '○ Empty'}
            </span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="color:#6b7c99;font-size:0.8rem;font-family:'DM Sans',sans-serif">Inventory</span>
            <span class="badge {'badge-green' if stock_ok else 'badge-amber'}">
                {'✓ Ready' if stock_ok else '○ Empty'}
            </span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="color:#6b7c99;font-size:0.8rem;font-family:'DM Sans',sans-serif">AMU Calculated</span>
            <span class="badge {'badge-green' if amu_ok else 'badge-amber'}">
                {'✓ Done' if amu_ok else '○ Pending'}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if amu_ok:
        st.divider()
        st.markdown(f"""
        <div style="color:#6b7c99;font-size:0.75rem;font-family:'DM Sans',sans-serif">
            Method: <span style="color:#2e7cf6">{METHOD_LABELS[st.session_state.amu_method]}</span>
        </div>
        """, unsafe_allow_html=True)


page = st.session_state.current_page


# =============================================================
# PAGE: UPLOAD
# =============================================================
if page == 'upload':
    page_header("Data Upload", "Connect your clinic data to get started")

    st.markdown("### 📋 Usage Transactions")

    dl_col, _ = st.columns([2, 3])
    with dl_col:
        st.download_button(
            "⬇️ Download Template",
            data                = generate_usage_template(),
            file_name           = "usage_template.xlsx",
            mime                = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width = True,
            key                 = "dl_usage",
        )

    usage_mode = st.radio(
        "Entry method",
        ["☁️ Upload any sheet", "⚡ Upload Dentolize export", "📋 Copy & Paste", "✏️ Manual entry"],
        horizontal        = True,
        key               = "usage_entry_mode",
        label_visibility  = "collapsed",
    )

    usage_source_raw = None

    if usage_mode == "☁️ Upload any sheet":
        files = st.file_uploader(
            "Upload one or more Excel files",
            accept_multiple_files = True,
            key                   = "up_usage_generic"
        )
        if files:
            usage_source_raw = load_excel_files(files)

    elif usage_mode == "⚡ Upload Dentolize export":
        st.info("⚡ Dentolize mode — columns are mapped automatically.")
        files = st.file_uploader(
            "Upload Dentolize transaction export(s)",
            accept_multiple_files = True,
            key                   = "up_usage_dentolize"
        )
        if files:
            raw = load_excel_files(files)
            if not raw.empty:
                try:
                    mapped = apply_dentolize_usage(raw)
                    st.session_state.usage_raw    = raw
                    st.session_state.usage_mapped = mapped
                    st.success(f"✅ Dentolize usage data loaded — {len(mapped):,} rows, auto-mapped.")
                    with st.expander("Preview"):
                        st.dataframe(mapped.head(5), use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Could not auto-map Dentolize columns: {e}")

    elif usage_mode == "📋 Copy & Paste":
        st.caption("Copy rows directly from Excel and paste below.")
        pasted = st.text_area(
            "Paste here",
            height      = 180,
            placeholder = "Created\tinventoryItem\tinventoryType\tAmount\tPrice",
            key         = "paste_usage_text"
        )
        if pasted:
            usage_source_raw = parse_pasted_data(pasted, "Usage Transactions")
            if usage_source_raw is not None:
                st.success(f"✅ Detected {len(usage_source_raw):,} rows.")
                st.dataframe(usage_source_raw.head(5), use_container_width=True)

    elif usage_mode == "✏️ Manual entry":
        render_manual_entry_form('usage')

    if usage_source_raw is not None and not usage_source_raw.empty:
        st.markdown("**Map columns to required fields:**")
        mapping = render_column_mapper(usage_source_raw, USAGE_FIELDS, "usage")
        if mapping:
            st.session_state.usage_raw    = usage_source_raw
            st.session_state.usage_mapped = apply_mapping(usage_source_raw, mapping)
            st.success("✅ Column mapping complete.")
            with st.expander("Preview mapped data"):
                st.dataframe(st.session_state.usage_mapped.head(5), use_container_width=True)

    st.divider()

    st.markdown("### 🗄️ Inventory")

    dl_col2, _ = st.columns([2, 3])
    with dl_col2:
        st.download_button(
            "⬇️ Download Template",
            data                = generate_stock_template(),
            file_name           = "inventory_template.xlsx",
            mime                = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width = True,
            key                 = "dl_stock",
        )

    stock_mode = st.radio(
        "Entry method",
        ["☁️ Upload any sheet", "⚡ Upload Dentolize export", "📋 Copy & Paste", "✏️ Manual entry"],
        horizontal       = True,
        key              = "stock_entry_mode",
        label_visibility = "collapsed",
    )

    stock_source_raw = None

    if stock_mode == "☁️ Upload any sheet":
        sf = st.file_uploader("Upload inventory Excel file", type=["xlsx"], key="up_stock_generic")
        if sf:
            res = load_single_excel(sf)
            if isinstance(res, str):
                st.error(f"❌ {res}")
            else:
                stock_source_raw = res

    elif stock_mode == "⚡ Upload Dentolize export":
        st.info("⚡ Dentolize mode — columns are mapped automatically.")
        sf = st.file_uploader("Upload Dentolize inventory export", type=["xlsx"], key="up_stock_dentolize")
        if sf:
            res = load_single_excel(sf)
            if isinstance(res, str):
                st.error(f"❌ {res}")
            else:
                try:
                    mapped = apply_dentolize_stock(res)
                    mapped = mapped.dropna(how='all')
                    st.session_state.stock_df     = mapped
                    st.session_state.stock_mapped = mapped
                    st.success(f"✅ Dentolize inventory loaded — {len(mapped):,} items, auto-mapped.")
                    with st.expander("Preview"):
                        st.dataframe(mapped.head(5), use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Could not auto-map Dentolize columns: {e}")

    elif stock_mode == "📋 Copy & Paste":
        st.caption("Copy rows directly from Excel and paste below.")
        pasted_s = st.text_area(
            "Paste here",
            height      = 180,
            placeholder = "Name\tType\tbranchAmount\tmasterAmount",
            key         = "paste_stock_text"
        )
        if pasted_s:
            stock_source_raw = parse_pasted_data(pasted_s, "Inventory")
            if stock_source_raw is not None:
                st.success(f"✅ Detected {len(stock_source_raw):,} rows.")
                st.dataframe(stock_source_raw.head(5), use_container_width=True)

    elif stock_mode == "✏️ Manual entry":
        render_manual_entry_form('stock')

    if stock_source_raw is not None and not stock_source_raw.empty:
        st.markdown("**Map columns to required fields:**")
        s_mapping = render_column_mapper(stock_source_raw, STOCK_FIELDS, "stock")
        if s_mapping:
            mapped = apply_mapping(stock_source_raw, s_mapping).dropna(how='all')
            st.session_state.stock_df     = mapped
            st.session_state.stock_mapped = mapped
            st.success("✅ Column mapping complete.")
            with st.expander("Preview mapped data"):
                st.dataframe(mapped.head(5), use_container_width=True)

    st.divider()

    st.markdown("### 📐 AMU Calculation Method")

    selected_label = st.selectbox(
        "Method",
        options          = list(METHOD_LABELS.values()),
        index            = list(METHOD_LABELS.keys()).index(st.session_state.amu_method),
        label_visibility = "collapsed",
    )
    chosen_method = [k for k, v in METHOD_LABELS.items() if v == selected_label][0]

    if chosen_method == 'rolling_window':
        rolling_val = st.slider("Lookback (months)", 1, 24, st.session_state.amu_rolling_months)
        st.caption(f"Using last **{rolling_val} months** of data.")
    elif chosen_method == 'date_range':
        dc1, dc2 = st.columns(2)
        with dc1: date_from_val = st.date_input("From", value=st.session_state.amu_date_from)
        with dc2: date_to_val   = st.date_input("To",   value=st.session_state.amu_date_to)
        if date_from_val >= date_to_val:
            st.warning("'From' must be before 'To'.")
    else:
        st.caption("Uses each item's earliest transaction as the window start.")

    st.divider()

    if st.button("🚀 Process & Sync All Data", use_container_width=True):
        st.session_state.amu_method = chosen_method
        if chosen_method == 'rolling_window':
            st.session_state.amu_rolling_months = rolling_val
        elif chosen_method == 'date_range':
            st.session_state.amu_date_from = date_from_val
            st.session_state.amu_date_to   = date_to_val

        if st.session_state.usage_mapped is not None:
            cons_df, amu_df = calculate_amu(
                st.session_state.usage_mapped,
                method         = st.session_state.amu_method,
                rolling_months = st.session_state.amu_rolling_months,
                date_from      = st.session_state.amu_date_from,
                date_to        = st.session_state.amu_date_to,
            )
            if cons_df.empty:
                st.error("❌ No data in the selected window. Try a wider range.")
            else:
                st.session_state.cons_view   = cons_df
                st.session_state.shared_amu  = amu_df
                st.session_state.merged_data = None
                st.session_state.data_hash   = str(pd.Timestamp.now())
                st.success(f"✅ {len(amu_df):,} items processed — AMU calculated.")
        else:
            st.warning("⚠️ Upload and map usage data first.")

        if st.session_state.stock_mapped is not None:
            st.session_state.stock_df    = st.session_state.stock_mapped
            st.session_state.merged_data = None
            st.success(f"✅ {len(st.session_state.stock_df):,} inventory items synced.")
        else:
            st.warning("⚠️ Upload and map inventory data first.")

    with st.expander("📖 How to use this page / كيفية استخدام هذه الصفحة"):
        st.markdown("""
        ### 🇬🇧 Four ways to get your data in
        - **Upload any sheet** — upload any Excel file then use the dropdowns to tell the app which column is which
        - **Upload Dentolize export** — upload directly from Dentolize — no configuration needed
        - **Copy & Paste** — copy rows from any spreadsheet and paste directly
        - **Manual entry** — type rows one by one using the form fields

        ---
        ### 🇸🇦 أربع طرق لإدخال البيانات
        - **رفع أي ملف** — ارفع أي ملف Excel ثم حدد أي عمود يمثل كل حقل
        - **رفع تصدير Dentolize** — ارفع مباشرة من Dentolize دون أي إعداد إضافي
        - **نسخ ولصق** — انسخ الصفوف من أي جدول بيانات والصقها مباشرة
        - **إدخال يدوي** — أدخل الصفوف واحداً تلو الآخر
        """)


# =============================================================
# PAGE: AMU
# =============================================================
elif page == 'amu':
    page_header("Average Monthly Usage", "Consumption burn rate per item")

    if st.session_state.usage_raw is None or st.session_state.usage_raw.empty:
        st.warning("⚠️ Upload usage data first — go to the Upload page.")
    else:
        st.markdown(f"""
        <span class="badge badge-blue">{METHOD_LABELS[st.session_state.amu_method]}</span>
        """, unsafe_allow_html=True)
        st.markdown("")

        t_raw, t_cons, t_final = st.tabs(["Raw Data", "Consolidation", "Final AMU"])

        with t_raw:
            st.dataframe(st.session_state.usage_raw, use_container_width=True)

        with t_cons:
            if st.session_state.cons_view is not None:
                st.dataframe(st.session_state.cons_view, use_container_width=True)
            else:
                st.warning("Process data in the Upload page first.")

        with t_final:
            if st.session_state.shared_amu is not None:
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Items",   len(st.session_state.shared_amu))
                m2.metric("Avg AMU",       f"{st.session_state.shared_amu['AMU'].mean():.2f}")
                m3.metric("Max AMU",       f"{st.session_state.shared_amu['AMU'].max():.2f}")
                st.dataframe(st.session_state.shared_amu, use_container_width=True)
                st.download_button(
                    "⬇️ Download AMU Table",
                    data      = st.session_state.shared_amu.to_csv(index=False),
                    file_name = "amu_table.csv",
                    mime      = "text/csv",
                    key       = "dl_amu",
                )
            else:
                st.warning("Process data in the Upload page first.")


# =============================================================
# PAGE: FORECAST
# =============================================================
elif page == 'forecast':
    page_header("Inventory Forecast", "Predicted depletion dates based on AMU")

    if st.session_state.shared_amu is None:
        st.warning("⚠️ Process AMU data first — go to the Upload page.")
    elif st.session_state.stock_df is None:
        st.warning("⚠️ Upload inventory data first — go to the Upload page.")
    else:
        if st.session_state.merged_data is None:
            df_a = st.session_state.shared_amu.copy()
            df_s = st.session_state.stock_df.copy()
            df_a['MKey'] = df_a['Item'].astype(str).str.strip().str.lower()
            df_s['MKey'] = df_s['Item'].astype(str).str.strip().str.lower()

            merged = pd.merge(
                df_a[['Item', 'Type', 'Price_Last', 'Price_High', 'Price_Avg', 'AMU', 'MKey']],
                df_s.drop(columns=['Item']),
                on="MKey", how="inner"
            )
            merged['TargetDate']         = calc_target_vectorized(merged['Master'], merged['AMU'])
            st.session_state.merged_data = merged

        merged = st.session_state.merged_data

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Matched Items",  len(merged))
        m2.metric("Avg Master Stock", f"{pd.to_numeric(merged['Master'], errors='coerce').mean():.0f}")
        m3.metric("Depleting This Month", len(merged[merged['TargetDate'].dt.month == pd.Timestamp.now().month]))
        m4.metric("Depleting Next 3M",
                  len(merged[merged['TargetDate'] <= (pd.Timestamp.now() + pd.DateOffset(months=3))]))

        t_match, t_forecast = st.tabs(["Match Check", "Depletion Forecast"])

        with t_match:
            st.dataframe(merged[['Item', 'Type', 'AMU', 'Branch', 'Master']], use_container_width=True)

        with t_forecast:
            st.dataframe(merged[['Item', 'Master', 'AMU', 'TargetDate']], use_container_width=True)
            st.download_button(
                "⬇️ Download Forecast",
                data      = merged[['Item', 'Master', 'AMU', 'TargetDate']].to_csv(index=False),
                file_name = "depletion_forecast.csv",
                mime      = "text/csv",
                key       = "dl_forecast",
            )


# =============================================================
# PAGE: SHOPPING LIST
# =============================================================
elif page == 'shopping':
    page_header("Shopping List", "3-month rolling purchase plan")

    if st.session_state.merged_data is None:
        st.warning("⚠️ Complete the Forecast page first.")
    else:
        merged    = st.session_state.merged_data
        all_types = sorted(merged['Type'].unique().astype(str).tolist())

        f1, f2, f3, f4 = st.columns([2, 1, 2, 2])
        with f1: search_query = st.text_input("🔍 Search", placeholder="Item name...", label_visibility="collapsed")
        with f2:
            sel_month_str = st.selectbox("Month", MONTH_OPTIONS, label_visibility="collapsed")
            sel_date      = pd.to_datetime(sel_month_str)
        with f3: sel_types   = st.multiselect("Category", all_types, default=all_types, label_visibility="collapsed")
        with f4:
            price_label = st.selectbox("💰 Price", list(PRICE_METHODS.keys()), label_visibility="collapsed")

        price_col         = PRICE_METHODS[price_label]
        all_shopping_rows = []
        st.divider()

        for i in range(3):
            current_target = sel_date + pd.DateOffset(months=i)
            target_label   = current_target.strftime("%B %Y")

            mask = (
                (merged['TargetDate'].dt.month == current_target.month) &
                (merged['TargetDate'].dt.year  == current_target.year)  &
                (merged['Type'].isin(sel_types))
            )
            if search_query:
                mask = mask & merged['Item'].str.contains(search_query, case=False, na=False)

            m_df = merged[mask].copy()

            st.markdown(f"#### 🗓️ {target_label}")

            if not m_df.empty:
                m_df['Qty_AMU']        = np.where(m_df['AMU'] < 1, 1.0, np.ceil(m_df['AMU']))
                m_df['Price_Active']   = m_df[price_col]
                m_df['Price_Variance'] = (m_df['Price_High'] - m_df['Price_Avg']).round(2)
                m_df['Order_Month']    = target_label
                all_shopping_rows.append(m_df)

                min_cost  = (m_df['Price_Active'] * 1).sum()
                pred_cost = (m_df['Price_Active'] * m_df['Qty_AMU']).sum()

                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Min Cost (1 unit)",    f"${min_cost:,.2f}")
                mc2.metric("Predicted Cost (AMU)", f"${pred_cost:,.2f}")
                mc3.metric("Items",                len(m_df))

                col_rename = {
                    'Price_Last'    : '💰 Last',
                    'Price_Avg'     : '📊 Avg',
                    'Price_High'    : '📈 High',
                    'Price_Variance': '↕️ Variance',
                    'Price_Active'  : f'✅ Active',
                }
                st.dataframe(
                    m_df[['Item', 'Type', 'Price_Last', 'Price_Avg', 'Price_High',
                           'Price_Variance', 'Price_Active', 'AMU', 'Qty_AMU', 'Branch', 'Master']
                    ].rename(columns=col_rename),
                    use_container_width=True
                )
            else:
                st.caption(f"Nothing predicted for {target_label}.")
            st.write("")

        if all_shopping_rows:
            export_df = pd.concat(all_shopping_rows, ignore_index=True)[
                ['Order_Month', 'Item', 'Type', 'Price_Active', 'AMU', 'Qty_AMU', 'Branch', 'Master']
            ].rename(columns={'Price_Active': f'Price ({price_label})', 'Order_Month': 'Month'})

            st.download_button(
                "⬇️ Download Full Shopping List",
                data                = export_df.to_csv(index=False),
                file_name           = "shopping_list.csv",
                mime                = "text/csv",
                use_container_width = True,
                key                 = "dl_shop",
            )


# =============================================================
# PAGE: ADJUST
# =============================================================
elif page == 'adjust':
    page_header("Name Alignment", "Fix item name mismatches between files")

    if st.session_state.shared_amu is None or st.session_state.stock_df is None:
        st.warning("⚠️ Upload both files first.")
    else:
        df_a = st.session_state.shared_amu.copy()
        df_s = st.session_state.stock_df.copy()
        df_a['MKey'] = df_a['Item'].astype(str).str.strip().str.lower()
        df_s['MKey'] = df_s['Item'].astype(str).str.strip().str.lower()
        unmatched    = df_s[~df_s['MKey'].isin(df_a['MKey'])].copy()

        m1, m2 = st.columns(2)
        m1.metric("Total Inventory Items",  len(df_s))
        m2.metric("Unmatched Items",        len(unmatched))

        if not unmatched.empty:
            match_results = run_fuzzy_match(
                tuple(unmatched['Item'].tolist()),
                tuple(df_a['Item'].unique().tolist())
            )
            unmatched['Suggested Match'] = unmatched['Item'].map(match_results)
            display_cols = ['Item', 'Suggested Match']
            if 'Type_S2' in unmatched.columns: display_cols.append('Type_S2')
            if 'Branch'  in unmatched.columns: display_cols.append('Branch')

            st.dataframe(unmatched[display_cols], use_container_width=True)
            st.download_button(
                "⬇️ Download Mismatch Report",
                data      = unmatched[display_cols].to_csv(index=False),
                file_name = "mismatches.csv",
                mime      = "text/csv",
                key       = "dl_mismatch",
            )
        else:
            st.success("✅ All inventory items are aligned with usage data.")


# =============================================================
# PAGE: ANOMALY DETECTION
# =============================================================
elif page == 'anomaly':
    page_header("Anomaly Detection", "Flag unusual consumption patterns")

    if st.session_state.usage_mapped is None:
        st.warning("⚠️ Upload and process usage data first.")
    elif st.session_state.shared_amu is None:
        st.warning("⚠️ Process AMU data first.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: lookback    = st.slider("Lookback (months)", 1, 24, 3)
        with c2: over_thresh = st.slider("🔴 Overuse threshold (%)", 5, 100, 20, 5)
        with c3: under_thresh= st.slider("🔵 Underuse threshold (%)", 5, 100, 30, 5)

        all_types_a = sorted(st.session_state.shared_amu['Type'].unique().astype(str).tolist())
        sel_types_a = st.multiselect("Filter by Category", all_types_a, default=all_types_a, key="an_types")

        st.divider()

        anomaly_df = calculate_anomalies(
            usage_json  = st.session_state.usage_mapped.to_json(),
            amu_json    = st.session_state.shared_amu.to_json(),
            lookback    = lookback,
            over_t      = over_thresh,
            under_t     = under_thresh,
            types_tuple = tuple(sel_types_a),
        )

        if anomaly_df.empty:
            st.warning("No data in the selected window.")
        else:
            total = len(anomaly_df)
            n_inv = (anomaly_df['Flag'] == '🔴 Investigate').sum()
            n_wat = (anomaly_df['Flag'] == '🟡 Watch').sum()
            n_und = anomaly_df['Flag'].str.startswith('🔵').sum()
            n_nor = (anomaly_df['Flag'] == '🟢 Normal').sum()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Items",    total)
            m2.metric("🔴 Investigate", n_inv)
            m3.metric("🟡 Watch",       n_wat)
            m4.metric("🔵 Underuse",    n_und)
            m5.metric("🟢 Normal",      n_nor)

            st.divider()

            dcols = ['Item', 'Type', 'AMU', 'Expected_Usage', 'Actual_Usage', 'Variance', 'Variance_%', 'Flag']
            drename = {
                'AMU'            : 'AMU/mo',
                'Expected_Usage' : f'Expected ({lookback}m)',
                'Actual_Usage'   : f'Actual ({lookback}m)',
                'Variance'       : 'Variance (units)',
                'Variance_%'     : 'Variance %',
            }

            t_all, t_red, t_yel, t_blu, t_grn = st.tabs([
                f"All ({total})", f"🔴 ({n_inv})", f"🟡 ({n_wat})",
                f"🔵 ({n_und})", f"🟢 ({n_nor})"
            ])

            with t_all:
                st.dataframe(anomaly_df[dcols].rename(columns=drename), use_container_width=True)
                st.download_button("⬇️ Download Report",
                    anomaly_df[dcols].rename(columns=drename).to_csv(index=False),
                    "anomaly_report.csv", "text/csv", key="dl_an_all")

            with t_red:
                red = anomaly_df[anomaly_df['Flag'] == '🔴 Investigate']
                if red.empty: st.success("None.")
                else:
                    st.error(f"{len(red)} item(s) — check for leakage or theft.")
                    st.dataframe(red[dcols].rename(columns=drename), use_container_width=True)
                    st.download_button("⬇️ Download", red[dcols].rename(columns=drename).to_csv(index=False),
                        "investigate.csv", "text/csv", key="dl_an_red")

            with t_yel:
                yel = anomaly_df[anomaly_df['Flag'] == '🟡 Watch']
                if yel.empty: st.success("None.")
                else:
                    st.warning(f"{len(yel)} item(s) slightly over — monitor.")
                    st.dataframe(yel[dcols].rename(columns=drename), use_container_width=True)

            with t_blu:
                blu = anomaly_df[anomaly_df['Flag'].str.startswith('🔵')]
                if blu.empty: st.success("None.")
                else:
                    st.info(f"{len(blu)} item(s) under consumed.")
                    st.dataframe(blu[dcols].rename(columns=drename), use_container_width=True)

            with t_grn:
                grn = anomaly_df[anomaly_df['Flag'] == '🟢 Normal']
                if grn.empty: st.info("None.")
                else:
                    st.success(f"{len(grn)} item(s) normal.")
                    st.dataframe(grn[dcols].rename(columns=drename), use_container_width=True)


# =============================================================
# PAGE: AI ASSISTANT
# =============================================================
elif page == 'ai':
    page_header("AI Assistant", "Ask questions about your clinic inventory data")

    st.markdown("""
    <div style="background:rgba(46,124,246,0.06);border:1px solid rgba(46,124,246,0.15);
                border-radius:12px;padding:1rem 1.2rem;margin-bottom:1.5rem">
        <p style="margin:0;color:#6b7c99;font-size:0.85rem;font-family:'DM Sans',sans-serif">
            🤖 Ask anything about your inventory — depletion dates, top consuming items,
            anomalies, budget estimates, or what to order next month.
            Powered by DeepSeek R1 reasoning model via Groq.
            Responds in English or Arabic based on your question.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.ai_history:
        for h in st.session_state.ai_history:
            with st.chat_message("user"):
                st.markdown(h["user"])
            with st.chat_message("assistant"):
                st.markdown(h["ai"])

    user_q = st.chat_input("Ask about your inventory data...")
    if user_q:
        with st.chat_message("user"):
            st.markdown(user_q)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_resp = ask_ai(user_q, st.session_state.ai_history)
            st.markdown(ai_resp)
        st.session_state.ai_history.append({"user": user_q, "ai": ai_resp})

    if st.session_state.ai_history:
        if st.button("🗑️ Clear conversation", key="clear_ai"):
            st.session_state.ai_history = []
            st.rerun()

    st.divider()
    st.markdown("**Example questions / أمثلة على الأسئلة:**")
    examples = [
        "Which items are running out soonest?",
        "What should I order next month?",
        "Which category has the highest consumption?",
        "ما هي الأصناف التي ستنفد قريباً؟",
        "ما هو متوسط استخدام القفازات شهرياً؟",
    ]
    cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        with cols[i]:
            if st.button(ex, key=f"ex_{i}", use_container_width=True):
                with st.chat_message("user"):
                    st.markdown(ex)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        ai_resp = ask_ai(ex, st.session_state.ai_history)
                    st.markdown(ai_resp)
                st.session_state.ai_history.append({"user": ex, "ai": ai_resp})
                st.rerun()


# =============================================================
# FLOATING AI BUBBLE
# =============================================================
if page != 'ai':
    st.markdown("""
    <div style="position:fixed;bottom:2rem;right:2rem;z-index:9999">
        <a href="?page=ai" style="text-decoration:none">
            <div style="width:56px;height:56px;border-radius:50%;
                        background:linear-gradient(135deg,#2e7cf6,#0ecfb0);
                        display:flex;align-items:center;justify-content:center;
                        box-shadow:0 4px 24px rgba(46,124,246,0.4);
                        font-size:1.4rem;cursor:pointer">🤖</div>
        </a>
    </div>
    """, unsafe_allow_html=True)
