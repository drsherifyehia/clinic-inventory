import io
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from difflib import get_close_matches

# =============================================================
# PASSWORD GATE
# =============================================================
def check_password():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("🦷 Clinic Inventory Hub")
    st.subheader("🔐 Please enter the access password")
    st.caption("Contact your clinic administrator if you don't have the password.")

    col1, col2 = st.columns([2, 3])
    with col1:
        entered = st.text_input(
            "Password",
            type             = "password",
            key              = "login_password",
            label_visibility = "collapsed",
            placeholder      = "Enter password..."
        )
        if st.button("Login", use_container_width=True):
            if entered == st.secrets["auth"]["password"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    return False

if not check_password():
    st.stop()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Clinic Inventory Hub", layout="wide", page_icon="🦷")

# =============================================================
# CONSTANTS
# =============================================================
METHOD_LABELS = {
    "first_transaction" : "📌 First Transaction Date (original)",
    "rolling_window"    : "🔁 Rolling Window (last N months)",
    "date_range"        : "📅 Custom Date Range",
}

PRICE_METHODS = {
    "Last Recorded Price" : "Price_Last",
    "Highest Price"       : "Price_High",
    "Average Price"       : "Price_Avg",
}

USAGE_COL_MAP = {
    "transaction_date" : "Created",
    "item_name"        : "Item",
    "item_type"        : "Type",
    "quantity_used"    : "Amount",
    "unit_price"       : "Price",
}

STOCK_COL_MAP = {
    "item_name"    : "Item",
    "item_type"    : "Type_S2",
    "branch_stock" : "Branch",
    "master_stock" : "Master",
}

MIN_WINDOW_MONTHS = 1 / 30

_BASE_MONTH   = pd.Timestamp.now().normalize().replace(day=1)
MONTH_OPTIONS = [
    (_BASE_MONTH + pd.DateOffset(months=i)).strftime("%B %Y")
    for i in range(12)
]


# =============================================================
# COLUMN MAPPING
# =============================================================
def map_columns(df, col_map, source_name):
    rename  = {}
    missing = []
    for keyword, target in col_map.items():
        match = next(
            (c for c in df.columns if keyword in c.strip().lower()),
            None
        )
        if match:
            rename[match] = target
        else:
            missing.append(keyword)
    if missing:
        st.error(f"❌ {source_name} is missing columns containing: {missing}")
        return None
    return df.rename(columns=rename)[list(col_map.values())]


# =============================================================
# TEMPLATE GENERATORS
# =============================================================
@st.cache_resource
def generate_usage_template():
    df     = pd.DataFrame(columns=list(USAGE_COL_MAP.keys()))
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Usage Transactions')
        ws = writer.sheets['Usage Transactions']
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 22
    return output.getvalue()


@st.cache_resource
def generate_stock_template():
    df     = pd.DataFrame(columns=list(STOCK_COL_MAP.keys()))
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
# CACHED FILE LOADERS
# =============================================================
@st.cache_data
def get_amu_data(uploaded_files):
    if not uploaded_files:
        return pd.DataFrame()
    dfs = [pd.read_excel(f, engine='openpyxl') for f in uploaded_files]
    return pd.concat(dfs, ignore_index=True)


@st.cache_data
def get_stock_data(uploaded_file):
    if not uploaded_file:
        return None
    try:
        df         = pd.read_excel(uploaded_file, engine='openpyxl')
        df.columns = df.columns.str.strip()
        mapped     = map_columns(df, STOCK_COL_MAP, "Inventory file")
        if mapped is None:
            return "ERR_COLS"
        return mapped.dropna(how='all')
    except Exception as e:
        return f"ERR_FILE: {str(e)}"


# =============================================================
# AMU CALCULATION
# =============================================================
def calculate_amu(df_raw, method, rolling_months=None, date_from=None, date_to=None):
    df_raw.columns = df_raw.columns.str.strip()
    df = map_columns(df_raw, USAGE_COL_MAP, "Usage transactions file")
    if df is None:
        return pd.DataFrame(), pd.DataFrame()

    df            = df.copy()
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
        delta_days    = (date_to - date_from).days
        window_months = max(delta_days / 30, MIN_WINDOW_MONTHS)

    else:
        window_months = None

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df = df.sort_values('Created')

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
        (cons['Amount'] / cons['No. of Months']).round(2),
        0
    )

    amu_df = cons[['Item', 'Type', 'Price_Last', 'Price_High', 'Price_Avg', 'AMU']]
    return cons, amu_df


# =============================================================
# VECTORIZED TARGET DATE
# =============================================================
def calc_target_vectorized(master_series, amu_series):
    master = pd.to_numeric(master_series, errors='coerce').fillna(0)
    amu    = pd.to_numeric(amu_series,    errors='coerce').fillna(0)

    months_to_deplete = np.where(
        amu > 0, np.ceil(master / amu), 0
    ).astype(int)

    base    = pd.Period(pd.Timestamp.now(), 'M')
    periods = pd.PeriodIndex([base + int(m) for m in months_to_deplete])
    return periods.to_timestamp()


# =============================================================
# FUZZY MATCH
# =============================================================
@st.cache_data
def run_fuzzy_match(unmatched_items, usage_names_tuple):
    usage_names = list(usage_names_tuple)
    results     = {}
    for name in unmatched_items:
        matches       = get_close_matches(name, usage_names, n=1, cutoff=0.6)
        results[name] = matches[0] if matches else "No Close Match Found"
    return results


# =============================================================
# ANOMALY DETECTION
# =============================================================
@st.cache_data
def calculate_anomalies(usage_raw_json, shared_amu_json, lookback_months, over_threshold, under_threshold, sel_types_tuple):
    df            = pd.read_json(io.StringIO(usage_raw_json))
    df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
    df['Amount']  = pd.to_numeric(df['Amount'],   errors='coerce').fillna(0)
    df            = df.dropna(subset=['Created'])

    shared_amu = pd.read_json(io.StringIO(shared_amu_json))
    shared_amu = shared_amu[shared_amu['Type'].isin(list(sel_types_tuple))]

    cutoff    = pd.Timestamp.now() - pd.DateOffset(months=lookback_months)
    df_window = df[df['Created'] >= cutoff]

    if df_window.empty:
        return pd.DataFrame()

    actual = df_window.groupby(['Item', 'Type']).agg(
        Actual_Usage = ('Amount', 'sum')
    ).reset_index()

    amu_ref                   = shared_amu[['Item', 'Type', 'AMU']].copy()
    amu_ref['Expected_Usage'] = (amu_ref['AMU'] * lookback_months).round(2)

    result                 = pd.merge(amu_ref, actual, on=['Item', 'Type'], how='left')
    result['Actual_Usage'] = result['Actual_Usage'].fillna(0)
    result['Variance']     = (result['Actual_Usage'] - result['Expected_Usage']).round(2)

    result['Variance_%_raw'] = np.where(
        result['Expected_Usage'] > 0,
        ((result['Variance'] / result['Expected_Usage']) * 100).round(1),
        np.where(result['Actual_Usage'] > 0, 999.0, 0.0)
    )

    pct        = result['Variance_%_raw']
    conditions = [
        pct >=  over_threshold  * 2.5,
        pct >=  over_threshold,
        pct <= -under_threshold * 2.5,
        pct <= -under_threshold,
    ]
    choices = [
        '🔴 Investigate',
        '🟡 Watch',
        '🔵 Severely Under',
        '🔵 Under',
    ]
    result['Flag'] = np.select(conditions, choices, default='🟢 Normal')

    result['Variance_%'] = result['Variance_%_raw'].apply(
        lambda x: '⚠️ New Item' if x == 999.0 else f"{x:+.1f}%"
    )

    return result.sort_values('Variance_%_raw', ascending=False)


# =============================================================
# INITIALIZE SESSION STATE
# =============================================================
for key in ['usage_raw', 'stock_df', 'shared_amu', 'merged_data', 'cons_view']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'usage_raw' else pd.DataFrame()

if 'amu_method'         not in st.session_state: st.session_state.amu_method         = 'first_transaction'
if 'amu_rolling_months' not in st.session_state: st.session_state.amu_rolling_months = 6
if 'amu_date_from'      not in st.session_state: st.session_state.amu_date_from      = date(2024, 1, 1)
if 'amu_date_to'        not in st.session_state: st.session_state.amu_date_to        = date.today()
if 'data_hash'          not in st.session_state: st.session_state.data_hash          = None


# =============================================================
# APP TITLE & TABS
# =============================================================
st.title("🦷 Clinic Inventory Hub")

tab_upload, tab_app1, tab_app2, tab_shop, tab_adjust, tab_anomaly = st.tabs([
    "📂 1. Upload",
    "📊 2. Average Monthly Usage",
    "⚙️ 3. Inventory Forecast",
    "🛒 4. Shopping List",
    "🛠️ 5. Adjust",
    "🚨 6. Anomaly Detection",
])


# =============================================================
# TAB 1: UPLOAD
# =============================================================
with tab_upload:
    st.header("Data Upload Center")

    st.subheader("📋 Usage Transactions")
    usage_tmpl_col, _ = st.columns([2, 3])
    with usage_tmpl_col:
        st.download_button(
            label               = "⬇️ Download Usage Template (.xlsx)",
            data                = generate_usage_template(),
            file_name           = "usage_transactions_template.xlsx",
            mime                = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width = True,
            key                 = "dl_usage_template",
        )

    usage_tab_file, usage_tab_paste = st.tabs(["📁 Upload File", "📋 Paste Data"])
    with usage_tab_file:
        amu_files = st.file_uploader(
            "Upload one or more Usage Transaction files",
            accept_multiple_files=True,
            key="up_amu"
        )
    with usage_tab_paste:
        st.caption("Copy your data directly from Excel and paste below. First row must be the header row.")
        usage_pasted = st.text_area(
            "Paste Usage Data here",
            height      = 200,
            placeholder = "transaction_date\titem_name\titem_type\tquantity_used\tunit_price",
            key         = "paste_usage"
        )
        if usage_pasted:
            preview = parse_pasted_data(usage_pasted, "Usage Transactions")
            if preview is not None:
                st.success(f"✅ Detected {len(preview)} rows and {len(preview.columns)} columns.")
                st.dataframe(preview.head(5), use_container_width=True)

    st.divider()

    st.subheader("🗄️ Inventory")
    stock_tmpl_col, _ = st.columns([2, 3])
    with stock_tmpl_col:
        st.download_button(
            label               = "⬇️ Download Inventory Template (.xlsx)",
            data                = generate_stock_template(),
            file_name           = "inventory_template.xlsx",
            mime                = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width = True,
            key                 = "dl_stock_template",
        )

    stock_tab_file, stock_tab_paste = st.tabs(["📁 Upload File", "📋 Paste Data"])
    with stock_tab_file:
        stock_f = st.file_uploader(
            "Upload Inventory file",
            type=["xlsx"],
            key="up_stock"
        )
    with stock_tab_paste:
        st.caption("Copy your inventory data from Excel and paste below. First row must be the header row.")
        stock_pasted = st.text_area(
            "Paste Inventory Data here",
            height      = 200,
            placeholder = "item_name\titem_type\tbranch_stock\tmaster_stock",
            key         = "paste_stock"
        )
        if stock_pasted:
            preview = parse_pasted_data(stock_pasted, "Inventory")
            if preview is not None:
                st.success(f"✅ Detected {len(preview)} rows and {len(preview.columns)} columns.")
                st.dataframe(preview.head(5), use_container_width=True)

    st.divider()

    st.subheader("📐 AMU Calculation Method")
    selected_label = st.selectbox(
        "Choose how to calculate Average Monthly Usage:",
        options = list(METHOD_LABELS.values()),
        index   = list(METHOD_LABELS.keys()).index(st.session_state.amu_method)
    )
    chosen_method = [k for k, v in METHOD_LABELS.items() if v == selected_label][0]

    if chosen_method == 'rolling_window':
        rolling_val = st.slider(
            "Lookback window (months)",
            min_value=1, max_value=24,
            value=st.session_state.amu_rolling_months
        )
        st.caption(f"Only transactions from the last **{rolling_val} months** will be used.")
    elif chosen_method == 'date_range':
        dr_col1, dr_col2 = st.columns(2)
        with dr_col1:
            date_from_val = st.date_input("From", value=st.session_state.amu_date_from)
        with dr_col2:
            date_to_val   = st.date_input("To",   value=st.session_state.amu_date_to)
        if date_from_val >= date_to_val:
            st.warning("⚠️ 'From' date must be before 'To' date.")
    else:
        st.caption("Uses each item's earliest transaction as the start of its window.")

    st.divider()

    if st.button("🚀 Process & Sync All Data", use_container_width=True):

        st.session_state.amu_method = chosen_method
        if chosen_method == 'rolling_window':
            st.session_state.amu_rolling_months = rolling_val
        elif chosen_method == 'date_range':
            st.session_state.amu_date_from = date_from_val
            st.session_state.amu_date_to   = date_to_val

        usage_source = None
        if amu_files:
            usage_source = get_amu_data(amu_files)
        elif usage_pasted and usage_pasted.strip():
            usage_source = parse_pasted_data(usage_pasted, "Usage Transactions")
            if usage_source is not None:
                st.info("📋 Using pasted usage data.")

        if usage_source is not None and not usage_source.empty:
            st.session_state.usage_raw = usage_source
            cons_df, amu_df = calculate_amu(
                usage_source,
                method         = st.session_state.amu_method,
                rolling_months = st.session_state.amu_rolling_months,
                date_from      = st.session_state.amu_date_from,
                date_to        = st.session_state.amu_date_to,
            )
            if cons_df.empty:
                st.error("❌ No data found in the selected date window. Try a wider range.")
            else:
                st.session_state.cons_view   = cons_df
                st.session_state.shared_amu  = amu_df
                st.session_state.merged_data = None
                st.session_state.data_hash   = str(pd.Timestamp.now())
                st.success(f"✅ Usage records synced using: **{selected_label}**")
        else:
            st.warning("⚠️ No valid usage data found. Please check your upload or pasted text.")

        stock_source = None
        if stock_f:
            res = get_stock_data(stock_f)
            if isinstance(res, str):
                if res == "ERR_COLS":
                    st.error("❌ Inventory file is missing required columns.")
                else:
                    st.error(f"❌ File Error: {res}")
            else:
                stock_source = res
        elif stock_pasted and stock_pasted.strip():
            parsed = parse_pasted_data(stock_pasted, "Inventory")
            if parsed is not None:
                parsed.columns = parsed.columns.str.strip()
                mapped         = map_columns(parsed, STOCK_COL_MAP, "Pasted Inventory")
                if mapped is not None:
                    stock_source = mapped.dropna(how='all')
                    st.info("📋 Using pasted inventory data.")

        if stock_source is not None:
            st.session_state.stock_df    = stock_source
            st.session_state.merged_data = None
            st.success("✅ Inventory records synced.")
        else:
            if not stock_f and not (stock_pasted and stock_pasted.strip()):
                st.warning("⚠️ Please upload an inventory file or paste inventory data.")

    if st.session_state.shared_amu is not None:
        st.info(f"📐 **Active AMU method:** {METHOD_LABELS[st.session_state.amu_method]}")

    with st.expander("📖 How to use this tab / كيفية استخدام هذا القسم"):
        st.markdown("""
        ### 🇬🇧 What you do here
        This is your **starting point**. Upload your raw data files or paste directly from Excel,
        then choose how AMU should be calculated before hitting **Process & Sync**.
        Nothing in any other tab will work until this step is complete.

        **Two files are needed:**
        - **Usage Transactions** — every time a material was taken out of stock (date, item, quantity, price)
        - **Inventory** — your current stock levels per item (branch stock and master stock)

        **Three AMU methods to choose from:**
        - 📌 **First Transaction Date** — divides total usage by months since the item first appeared. Best if your data goes back to when the clinic opened.
        - 🔁 **Rolling Window** — only looks at the last N months. Best if your consumption patterns change over time.
        - 📅 **Custom Date Range** — you pick the exact window. Best for seasonal analysis or specific reporting periods.

        ---
        ### 🇸🇦 ماذا تفعل هنا
        هذه هي **نقطة البداية**. قم برفع ملفات البيانات أو لصق البيانات مباشرة من Excel،
        ثم اختر طريقة حساب متوسط الاستخدام الشهري قبل الضغط على **Process & Sync**.
        لن يعمل أي قسم آخر في التطبيق حتى تكتمل هذه الخطوة.

        **ملفان مطلوبان:**
        - **سجلات الاستخدام** — كل مرة تم فيها سحب مادة من المخزون (التاريخ، الصنف، الكمية، السعر)
        - **المخزون** — مستويات المخزون الحالية لكل صنف (مخزون الفرع والمخزون الرئيسي)

        ---
        ### 📋 Example / مثال — Disposable Gloves (Medium)

        | transaction_date | item_name | item_type | quantity_used | unit_price |
        |---|---|---|---|---|
        | 2024-01-10 | Gloves Medium | Disposable | 50 | 0.30 |
        | 2024-02-08 | Gloves Medium | Disposable | 45 | 0.30 |
        | 2024-03-05 | Gloves Medium | Disposable | 60 | 0.32 |

        > 💡 Copy this structure from Excel and paste it directly into the **Paste Data** tab — no file saving needed.
        """)


# =============================================================
# TAB 2: AVERAGE MONTHLY USAGE
# =============================================================
with tab_app1:
    if st.session_state.usage_raw is None or st.session_state.usage_raw.empty:
        st.warning("Please upload usage data in Tab 1.")
    else:
        st.info(f"📐 **AMU Method in use:** {METHOD_LABELS[st.session_state.amu_method]}")

        sub1_raw, sub1_cons, sub1_final = st.tabs([
            "1.a Raw Data", "1.b Consolidation", "1.c Final AMU"
        ])

        with sub1_raw:
            st.dataframe(st.session_state.usage_raw, use_container_width=True)

        with sub1_cons:
            if st.session_state.cons_view is not None:
                st.dataframe(st.session_state.cons_view, use_container_width=True)
            else:
                st.warning("Hit 'Process & Sync' in Tab 1 to calculate.")

        with sub1_final:
            if st.session_state.shared_amu is not None:
                st.dataframe(st.session_state.shared_amu, use_container_width=True)
                st.download_button(
                    "⬇️ Download AMU Table",
                    data      = st.session_state.shared_amu.to_csv(index=False),
                    file_name = "amu_table.csv",
                    mime      = "text/csv",
                    key       = "dl_amu_table",
                )
            else:
                st.warning("Hit 'Process & Sync' in Tab 1 to calculate.")

    with st.expander("📖 What you see here / ما الذي تراه هنا"):
        st.markdown("""
        ### 🇬🇧 What this tab shows
        This tab breaks the AMU calculation into three transparent steps so you can verify the numbers at each stage.

        - **1.a Raw Data** — your uploaded transactions exactly as the system read them. Check here if something looks wrong.
        - **1.b Consolidation** — all transactions grouped by item. You can see total quantity used, the date range, and how many months the calculation covers.
        - **1.c Final AMU** — the burn rate per item per month. This number drives everything else in the app.

        **AMU formula:**
        > AMU = Total Quantity Used ÷ Number of Months in Window

        ---
        ### 🇸🇦 ما الذي يعرضه هذا القسم
        يقسم هذا القسم حساب متوسط الاستخدام الشهري إلى ثلاث خطوات واضحة حتى تتمكن من التحقق من الأرقام في كل مرحلة.

        - **1.a البيانات الخام** — معاملاتك كما قرأها النظام تماماً.
        - **1.b التوحيد** — جميع المعاملات مجمعة حسب الصنف.
        - **1.c متوسط الاستخدام الشهري النهائي** — معدل الاستهلاك لكل صنف شهرياً.

        ---
        ### 📋 Example / مثال — Disposable Gloves (Medium)

        After uploading 3 months of transactions, the consolidation step would show:

        | Item | Type | Total Amount | No. of Months | AMU |
        |---|---|---|---|---|
        | Gloves Medium | Disposable | 155 | 3.0 | **51.67** |

        > 💡 This means the clinic uses roughly **52 boxes of medium gloves per month**.
        > If this number looks too high or too low, go back to Tab 1 and try a different AMU method or date window.

        ---
        ### 🔄 Common scenarios / سيناريوهات شائعة

        | Scenario | What you'll see | What to do |
        |---|---|---|
        | New item added mid-year | Very high AMU because window is short | Switch to Rolling Window in Tab 1 |
        | Item not appearing | Missing from raw data | Check item name spelling in your Excel file |
        | AMU seems too low | Old first transaction date inflating the window | Switch to Rolling Window (last 6 months) |
        | Price column shows 0 | Price column name not matched | Rename column to include the word `price` |
        """)


# =============================================================
# TAB 3: INVENTORY FORECAST
# =============================================================
with tab_app2:
    if st.session_state.shared_amu is None and st.session_state.stock_df is None:
        st.warning("⚠️ Please sync both Usage and Inventory files in Tab 1 first.")
    elif st.session_state.shared_amu is None:
        st.warning("⚠️ Usage data is missing. Please upload and process your Usage Transactions in Tab 1.")
    elif st.session_state.stock_df is None:
        st.warning("⚠️ Inventory data is missing. Please upload and process your Inventory file in Tab 1.")
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

        sub2_match, sub2_forecast = st.tabs(["2.a Match Check", "2.b Depletion Forecast"])

        with sub2_match:
            st.dataframe(
                merged[['Item', 'Type', 'AMU', 'Branch', 'Master']],
                use_container_width=True
            )

        with sub2_forecast:
            st.dataframe(
                merged[['Item', 'Master', 'AMU', 'TargetDate']],
                use_container_width=True
            )
            st.download_button(
                "⬇️ Download Forecast",
                data      = merged[['Item', 'Master', 'AMU', 'TargetDate']].to_csv(index=False),
                file_name = "depletion_forecast.csv",
                mime      = "text/csv",
                key       = "dl_forecast",
            )

    with st.expander("📖 What you see here / ما الذي تراه هنا"):
        st.markdown("""
        ### 🇬🇧 What this tab shows
        This tab matches your **usage data** against your **current stock** and predicts
        when each item will run out.

        - **2.a Match Check** — shows only items successfully matched between your two files. If an item is missing here, its name doesn't match between files — go to Tab 5 to fix it.
        - **2.b Depletion Forecast** — the predicted month each item hits zero, calculated as:

        > Months Remaining = Master Stock ÷ AMU → rounded up to nearest month

        ---
        ### 🇸🇦 ما الذي يعرضه هذا القسم
        يطابق هذا القسم **بيانات الاستخدام** مع **المخزون الحالي** ويتنبأ بموعد نفاد كل صنف.

        - **2.a فحص المطابقة** — يعرض الأصناف التي تمت مطابقتها بنجاح بين الملفين.
        - **2.b توقع النفاد** — الشهر المتوقع لنفاد كل صنف.

        ---
        ### 📋 Example / مثال — Disposable Gloves (Medium)

        | Item | Master Stock | AMU | Months Remaining | Target Depletion |
        |---|---|---|---|---|
        | Gloves Medium | 200 boxes | 51.67 | ceil(200 ÷ 51.67) = **4 months** | July 2025 |

        > 💡 This means if you don't restock, gloves will run out in **July 2025**.
        > The shopping list in Tab 4 will automatically include this item in the correct month.

        ---
        ### 🔄 Common scenarios / سيناريوهات شائعة

        | Scenario | What you'll see | What to do |
        |---|---|---|
        | Item missing from forecast | Not in Match Check | Fix name mismatch in Tab 5 |
        | Depletion date in the past | Stock already depleted or AMU too high | Verify master stock count |
        | Depletion date very far out (5+ years) | AMU very low or stock very high | Check if item is still in active use |
        | All items show same depletion date | Possible data issue | Re-process in Tab 1 |
        """)


# =============================================================
# TAB 4: SHOPPING LIST
# =============================================================
with tab_shop:
    if st.session_state.merged_data is None:
        st.warning("⚠️ Complete Data Matching in Tab 3 first.")
    else:
        st.header("Interactive Shopping List")
        merged    = st.session_state.merged_data
        all_types = sorted(merged['Type'].unique().astype(str).tolist())

        c_search, c_month, c_type = st.columns([2, 1, 2])
        with c_search:
            search_query = st.text_input("🔍 Search Item Name", placeholder="e.g. Gloves")
        with c_month:
            sel_month_str = st.selectbox("📅 Start Month", MONTH_OPTIONS)
            sel_date      = pd.to_datetime(sel_month_str)
        with c_type:
            sel_types = st.multiselect("🏷️ Filter by Category", all_types, default=all_types)

        st.divider()

        pc1, pc2 = st.columns([2, 3])
        with pc1:
            price_label = st.selectbox(
                "💰 Price Method",
                options = list(PRICE_METHODS.keys()),
                index   = 0,
                help    = "Controls which price is used for cost estimates."
            )
        with pc2:
            st.caption("""
            * **Last Recorded:** Most recent transaction price — best for day-to-day ordering.
            * **Highest:** Worst-case budget ceiling — good for management sign-off.
            * **Average:** Smooths out spikes — best for long-term budget planning.
            """)

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
            st.subheader(f"🗓️ {target_label}")

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
                mc3.metric("Price Method",         price_label)

                display_cols = [
                    'Item', 'Type',
                    'Price_Last', 'Price_Avg', 'Price_High',
                    'Price_Variance', 'Price_Active',
                    'AMU', 'Qty_AMU', 'Branch', 'Master'
                ]
                col_rename = {
                    'Price_Last'    : '💰 Last Price',
                    'Price_Avg'     : '📊 Avg Price',
                    'Price_High'    : '📈 High Price',
                    'Price_Variance': '↕️ Variance',
                    'Price_Active'  : f'✅ Active ({price_label})',
                }
                st.dataframe(
                    m_df[display_cols].rename(columns=col_rename),
                    use_container_width=True
                )
            else:
                st.info(f"No restocking predicted for {target_label}.")
            st.write("---")

        if all_shopping_rows:
            export_cols = ['Order_Month', 'Item', 'Type', 'Price_Active', 'AMU', 'Qty_AMU', 'Branch', 'Master']
            export_df   = pd.concat(all_shopping_rows, ignore_index=True)[export_cols].rename(columns={
                'Price_Active' : f'Price ({price_label})',
                'Order_Month'  : 'Month',
            })
            st.download_button(
                "⬇️ Download Full Shopping List (3 months)",
                data                = export_df.to_csv(index=False),
                file_name           = "shopping_list.csv",
                mime                = "text/csv",
                use_container_width = True,
                key                 = "dl_shopping_list",
            )

    with st.expander("📖 What you see here / ما الذي تراه هنا"):
        st.markdown("""
        ### 🇬🇧 What this tab shows
        Your **actionable purchase plan** for the next 3 months starting from your selected month.
        Each month shows only items predicted to run out in that specific month.

        - **Qty_AMU** — how many units to order. Set to 1 for slow-moving items (AMU < 1), otherwise rounded up to the nearest whole number.
        - **Price columns** — all three price variants (Last, Average, Highest) shown side by side so you can compare.
        - **Variance column** — the gap between highest and average price. A large variance means that item's price is unstable.
        - **Active price** — the one used for cost estimate metrics, based on your chosen Price Method.

        **Price method guide:**
        - 💰 Last Recorded — use for day-to-day orders
        - 📈 Highest — use when presenting budgets to management
        - 📊 Average — use for annual planning

        ---
        ### 🇸🇦 ما الذي يعرضه هذا القسم
        **خطة الشراء القابلة للتنفيذ** للأشهر الثلاثة القادمة ابتداءً من الشهر الذي تختاره.
        يعرض كل شهر فقط الأصناف المتوقع نفادها في ذلك الشهر تحديداً.

        - **Qty_AMU** — عدد الوحدات المقترح طلبها.
        - **عمود التباين** — الفجوة بين أعلى سعر ومتوسط السعر. التباين الكبير يعني أن سعر هذا الصنف غير مستقر.

        ---
        ### 📋 Example / مثال — Disposable Gloves (Medium)

        Predicted to deplete in **July 2025**. When you select June 2025 as start month, the July block shows:

        | Item | Last Price | Avg Price | High Price | Variance | Active (Avg) | AMU | Qty_AMU |
        |---|---|---|---|---|---|---|---|
        | Gloves Medium | $0.32 | $0.307 | $0.32 | $0.013 | $0.307 | 51.67 | **52** |

        **Cost metrics:**
        - Min Cost (1 unit): $0.307
        - Predicted Cost (AMU): 52 × $0.307 = **$15.96**

        > 💡 Low variance ($0.013) on gloves means the price is stable — safe to use Average price for budgeting.

        ---
        ### 🔄 Common scenarios / سيناريوهات شائعة

        | Scenario | What you'll see | What to do |
        |---|---|---|
        | Item not in any month | Depletion date outside 3-month window | Move start month earlier or check Tab 3 |
        | Qty_AMU shows 1 for a fast-moving item | AMU calculated as < 1 | Check date window in Tab 1 — likely too wide |
        | High price variance on an item | Large gap between High and Avg price | Use Highest price method for that order |
        | Cost estimate seems too high | AMU inflated | Recheck AMU method in Tab 1 |
        """)


# =============================================================
# TAB 5: ADJUST
# =============================================================
with tab_adjust:
    if st.session_state.shared_amu is None or st.session_state.stock_df is None:
        st.warning("⚠️ Upload data in Tab 1 to use this feature.")
    else:
        st.header("🛠️ Name Alignment Assistant")

        df_a = st.session_state.shared_amu.copy()
        df_s = st.session_state.stock_df.copy()

        df_a['MKey'] = df_a['Item'].astype(str).str.strip().str.lower()
        df_s['MKey'] = df_s['Item'].astype(str).str.strip().str.lower()
        unmatched    = df_s[~df_s['MKey'].isin(df_a['MKey'])].copy()

        if not unmatched.empty:
            usage_names_tuple = tuple(df_a['Item'].unique().tolist())
            match_results     = run_fuzzy_match(
                tuple(unmatched['Item'].tolist()),
                usage_names_tuple
            )
            unmatched['Suggested Match (Usage Sheet)'] = unmatched['Item'].map(match_results)
            st.dataframe(
                unmatched[['Item', 'Suggested Match (Usage Sheet)', 'Type_S2', 'Branch']],
                use_container_width=True
            )
            st.download_button(
                "⬇️ Download Mismatch Report",
                data      = unmatched[['Item', 'Suggested Match (Usage Sheet)', 'Type_S2', 'Branch']].to_csv(index=False),
                file_name = "name_mismatches.csv",
                mime      = "text/csv",
                key       = "dl_mismatch",
            )
        else:
            st.success("✅ All inventory items are perfectly aligned with usage data.")

    with st.expander("📖 What you see here / ما الذي تراه هنا"):
        st.markdown("""
        ### 🇬🇧 What this tab shows
        The **troubleshooter**. If an item appears in your Inventory file but is missing
        from the Forecast in Tab 3, it will appear here with a suggested name match
        from your Usage data.

        This happens because the item name in your Inventory file is slightly different
        from the name in your Usage file — even a single extra space or different
        capitalisation will cause a mismatch.

        **How to fix:**
        1. Look at the **Suggested Match** column
        2. Go to your Excel files and make the names identical in both files
        3. Re-upload and re-process in Tab 1

        ---
        ### 🇸🇦 ما الذي يعرضه هذا القسم
        **قسم استكشاف الأخطاء**. إذا ظهر صنف في ملف المخزون ولكنه مفقود من التوقعات في القسم الثالث،
        فسيظهر هنا مع اقتراح لاسم مطابق من بيانات الاستخدام.

        **طريقة الإصلاح:**
        1. انظر إلى عمود **الاقتراح المطابق**
        2. اجعل الأسماء متطابقة في كلا ملفي Excel
        3. أعد الرفع والمعالجة في القسم الأول

        ---
        ### 📋 Example / مثال — Disposable Gloves (Medium)

        | Item (Inventory file) | Suggested Match (Usage file) | Type | Branch Stock |
        |---|---|---|---|
        | Gloves-Medium | Gloves Medium | Disposable | 50 |
        | Mask Type II | Mask Type 2 | Disposable | 100 |

        > 💡 **Gloves-Medium** vs **Gloves Medium** — the only difference is a hyphen vs a space.
        > The system caught it automatically. Fix the name in either file and re-process.

        ---
        ### 🔄 Common scenarios / سيناريوهات شائعة

        | Scenario | What you'll see | What to do |
        |---|---|---|
        | Many mismatches after first upload | Most items unmatched | Check if you used the correct template column names |
        | Suggested match says "No Close Match Found" | Name is very different between files | Manually find and fix the name in your Excel file |
        | Item keeps reappearing after fix | Fix was in the wrong file | Make sure both files use the exact same name |
        | Tab shows "All items aligned" but item still missing from forecast | Item exists in usage but not inventory | Add the item to your inventory file |
        """)


# =============================================================
# TAB 6: ANOMALY DETECTION
# =============================================================
with tab_anomaly:
    if st.session_state.usage_raw is None or st.session_state.usage_raw.empty:
        st.warning("⚠️ Upload usage data in Tab 1 first.")
    elif st.session_state.shared_amu is None:
        st.warning("⚠️ Process data in Tab 1 first to generate AMU baseline.")
    else:
        st.header("🚨 Usage Anomaly Detection")
        st.caption(
            "Compares actual consumption in your chosen window against "
            "expected usage (AMU × months). Flags items significantly "
            "over or under consumed."
        )

        st.subheader("⚙️ Detection Settings")
        ctrl1, ctrl2, ctrl3 = st.columns(3)
        with ctrl1:
            lookback = st.slider(
                "📅 Lookback Window (months)",
                min_value=1, max_value=24, value=3,
                help="How far back to compare actual vs expected usage."
            )
        with ctrl2:
            over_thresh = st.slider(
                "🔴 Overuse Threshold (%)",
                min_value=5, max_value=100, value=20, step=5,
                help="🟡 Watch = at threshold. 🔴 Investigate = 2.5× threshold."
            )
        with ctrl3:
            under_thresh = st.slider(
                "🔵 Underuse Threshold (%)",
                min_value=5, max_value=100, value=30, step=5,
                help="Flag items consumed this % less than expected."
            )

        all_types_a = sorted(st.session_state.shared_amu['Type'].unique().astype(str).tolist())
        sel_types_a = st.multiselect(
            "🏷️ Filter by Category",
            all_types_a,
            default=all_types_a,
            key="anomaly_types"
        )

        st.divider()

        anomaly_df = calculate_anomalies(
            usage_raw_json  = st.session_state.usage_raw.to_json(),
            shared_amu_json = st.session_state.shared_amu.to_json(),
            lookback_months = lookback,
            over_threshold  = over_thresh,
            under_threshold = under_thresh,
            sel_types_tuple = tuple(sel_types_a),
        )

        if anomaly_df.empty:
            st.warning("No usage data found in the selected lookback window.")
        else:
            total         = len(anomaly_df)
            n_investigate = (anomaly_df['Flag'] == '🔴 Investigate').sum()
            n_watch       = (anomaly_df['Flag'] == '🟡 Watch').sum()
            n_under       = anomaly_df['Flag'].str.startswith('🔵').sum()
            n_normal      = (anomaly_df['Flag'] == '🟢 Normal').sum()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Items",    total)
            m2.metric("🔴 Investigate", n_investigate)
            m3.metric("🟡 Watch",       n_watch)
            m4.metric("🔵 Underuse",    n_under)
            m5.metric("🟢 Normal",      n_normal)

            st.divider()

            display_cols   = ['Item', 'Type', 'AMU', 'Expected_Usage', 'Actual_Usage', 'Variance', 'Variance_%', 'Flag']
            col_rename_map = {
                'AMU'            : 'AMU (monthly)',
                'Expected_Usage' : f'Expected ({lookback}m)',
                'Actual_Usage'   : f'Actual ({lookback}m)',
                'Variance'       : 'Variance (units)',
                'Variance_%'     : 'Variance %',
            }

            tab_all, tab_red, tab_yellow, tab_blue, tab_green = st.tabs([
                f"All ({total})",
                f"🔴 Investigate ({n_investigate})",
                f"🟡 Watch ({n_watch})",
                f"🔵 Underuse ({n_under})",
                f"🟢 Normal ({n_normal})",
            ])

            with tab_all:
                st.dataframe(
                    anomaly_df[display_cols].rename(columns=col_rename_map),
                    use_container_width=True
                )
                st.download_button(
                    "⬇️ Download Full Anomaly Report",
                    data      = anomaly_df[display_cols].rename(columns=col_rename_map).to_csv(index=False),
                    file_name = "anomaly_report.csv",
                    mime      = "text/csv",
                    key       = "dl_anomaly_all",
                )

            with tab_red:
                red_df = anomaly_df[anomaly_df['Flag'] == '🔴 Investigate']
                if red_df.empty:
                    st.success("No items require investigation.")
                else:
                    st.error(f"{len(red_df)} item(s) significantly over consumed — check for leakage or theft.")
                    st.dataframe(red_df[display_cols].rename(columns=col_rename_map), use_container_width=True)
                    st.download_button(
                        "⬇️ Download Investigate List",
                        data      = red_df[display_cols].rename(columns=col_rename_map).to_csv(index=False),
                        file_name = "investigate_items.csv",
                        mime      = "text/csv",
                        key       = "dl_anomaly_red",
                    )

            with tab_yellow:
                yellow_df = anomaly_df[anomaly_df['Flag'] == '🟡 Watch']
                if yellow_df.empty:
                    st.success("No items in watch list.")
                else:
                    st.warning(f"{len(yellow_df)} item(s) slightly over consumed — worth monitoring.")
                    st.dataframe(yellow_df[display_cols].rename(columns=col_rename_map), use_container_width=True)

            with tab_blue:
                blue_df = anomaly_df[anomaly_df['Flag'].str.startswith('🔵')]
                if blue_df.empty:
                    st.success("No underuse detected.")
                else:
                    st.info(f"{len(blue_df)} item(s) under consumed — possible hoarding, expiry risk, or data gaps.")
                    st.dataframe(blue_df[display_cols].rename(columns=col_rename_map), use_container_width=True)

            with tab_green:
                green_df = anomaly_df[anomaly_df['Flag'] == '🟢 Normal']
                if green_df.empty:
                    st.info("No items in normal range.")
                else:
                    st.success(f"{len(green_df)} item(s) within normal consumption range.")
                    st.dataframe(green_df[display_cols].rename(columns=col_rename_map), use_container_width=True)

    with st.expander("📖 What you see here / ما الذي تراه هنا"):
        st.markdown("""
        ### 🇬🇧 What this tab shows
        Compares **what was actually consumed** in your chosen lookback window against
        **what was expected** based on AMU. Items that deviate significantly are flagged.

        **Flag meanings:**
        - 🔴 **Investigate** — consumed 2.5× more than your threshold above expected. Check for leakage, theft, or data entry errors.
        - 🟡 **Watch** — consumed more than expected but not extreme. Monitor over the next window.
        - 🔵 **Underuse** — consumed significantly less than expected. Could mean hoarding, items nearing expiry, or missing transaction records.
        - 🟢 **Normal** — consumption within expected range.
        - ⚠️ **New Item** — no historical AMU baseline exists yet. Any consumption will flag here until enough history builds up.

        **Recommended starting settings:**
        - Lookback window: **3 months**
        - Overuse threshold: **20%**
        - Underuse threshold: **30%**

        If you get too many false flags, increase the thresholds or widen the window.

        ---
        ### 🇸🇦 ما الذي يعرضه هذا القسم
        يقارن **ما تم استهلاكه فعلياً** في الفترة الزمنية المحددة مع **ما كان متوقعاً** بناءً على متوسط الاستخدام الشهري.

        **معاني العلامات:**
        - 🔴 **يحتاج تحقيق** — الاستهلاك أعلى بـ 2.5 مرة من الحد المسموح به.
        - 🟡 **مراقبة** — الاستهلاك أعلى من المتوقع لكن ليس مفرطاً.
        - 🔵 **استخدام منخفض** — الاستهلاك أقل بكثير من المتوقع.
        - 🟢 **طبيعي** — الاستهلاك ضمن النطاق المتوقع.

        ---
        ### 📋 Example / مثال — Disposable Gloves (Medium)

        Settings: 3-month lookback, 20% overuse threshold, 30% underuse threshold.
        AMU = 51.67 → Expected over 3 months = **155 units**

        | Scenario | Actual Used | Variance | Variance % | Flag |
        |---|---|---|---|---|
        | Normal month | 158 units | +3 | +1.9% | 🟢 Normal |
        | Busy period | 185 units | +30 | +19.4% | 🟢 Normal (just under threshold) |
        | Suspected overuse | 195 units | +40 | +25.8% | 🟡 Watch |
        | Possible theft or leakage | 260 units | +105 | +67.7% | 🔴 Investigate |
        | Low usage month (holiday) | 100 units | -55 | -35.5% | 🔵 Under |

        > 💡 A single 🔴 flag on gloves could mean a box was unrecorded, damaged, or taken.
        > Cross-check against your supplier invoices for the same period to confirm.

        ---
        ### 🔄 Common scenarios / سيناريوهات شائعة

        | Scenario | What you'll see | What to do |
        |---|---|---|
        | Everything is 🔴 on first run | Thresholds too low | Increase overuse threshold to 40–50% and re-evaluate |
        | New item shows ⚠️ New Item | No AMU history yet | Normal — will resolve after a few months of data |
        | Gloves flagged every month | Consistent unrecorded usage | Audit transaction logging process |
        | Underuse on a critical item | Possible expiry or hoarding | Do a physical spot check on that item only |
        """)
