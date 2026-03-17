import io
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime
from difflib import get_close_matches

# =============================================================
# DARK MODE CSS — Injected for the Midnight Pro look
# =============================================================
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg-base:      #020617;
    --bg-surface:   #0f172a;
    --bg-card:      #1e293b;
    --bg-input:     #1e293b;
    --border:       #334155;
    --border-focus: #3b82f6;
    --text-primary: #f8fafc;
    --text-muted:   #94a3b8;
    --accent-blue:  #3b82f6;
    --accent-teal:  #0ea5e9;
    --accent-red:   #ef4444;
    --accent-green: #22c55e;
    --radius:       12px;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}

.stButton > button {
    background: var(--accent-blue) !important;
    color: #fff !important;
    border-radius: var(--radius) !important;
    border: none !important;
    font-weight: 600 !important;
    width: 100%;
}

[data-testid="stMetric"] {
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
}

.page-header {
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
</style>
"""

# =============================================================
# AUTHENTICATION
# =============================================================
def check_password():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    st.markdown(DARK_CSS, unsafe_allow_html=True)
    st.title("🦷 Clinic Inventory Hub")
    pwd = st.text_input("Access Password", type="password")
    if st.button("Login"):
        if pwd == st.secrets["auth"]["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid Password")
    return False

if not check_password():
    st.stop()

# --- CONFIG ---
st.set_page_config(page_title="Clinic Hub", layout="wide")
st.markdown(DARK_CSS, unsafe_allow_html=True)

# =============================================================
# CONSTANTS & SESSION STATE
# =============================================================
if 'merged_data' not in st.session_state: st.session_state.merged_data = None
if 'shared_amu' not in st.session_state: st.session_state.shared_amu = None
if 'stock_df' not in st.session_state: st.session_state.stock_df = None
if 'usage_mapped' not in st.session_state: st.session_state.usage_mapped = None

_BASE_MONTH = pd.Timestamp.now().normalize().replace(day=1)
MONTH_OPTIONS = [(_BASE_MONTH + pd.DateOffset(months=i)).strftime("%B %Y") for i in range(12)]

# =============================================================
# SIDEBAR NAVIGATION
# =============================================================
with st.sidebar:
    st.markdown("### 🛠️ Menu")
    page = st.radio("Navigate", ["Upload", "AMU", "Forecast", "Shopping List", "Purchase Tender", "AI Assistant"], label_visibility="collapsed")

# =============================================================
# PAGE: UPLOAD
# =============================================================
if page == "Upload":
    st.markdown('<div class="page-header"><h2>📂 Data Upload</h2></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        u_file = st.file_uploader("Upload Usage (Dentolize)", type="xlsx")
    with c2:
        s_file = st.file_uploader("Upload Stock (Dentolize)", type="xlsx")
    
    if st.button("Sync Data"):
        if u_file and s_file:
            # Process Usage
            df_u = pd.read_excel(u_file)
            st.session_state.usage_mapped = df_u.rename(columns={"inventoryItem":"Item", "inventoryType":"Type", "Created":"Created", "Amount":"Amount", "Price":"Price"})
            
            # Process Stock
            df_s = pd.read_excel(s_file)
            st.session_state.stock_df = df_s.rename(columns={"Name":"Item", "branchAmount":"Branch", "masterAmount":"Master"})
            
            # Simple AMU Calc
            df_u['Amount'] = pd.to_numeric(df_u['Amount'], errors='coerce').fillna(0)
            amu_df = df_u.groupby('Item')['Amount'].sum().reset_index()
            amu_df['AMU'] = (amu_df['Amount'] / 6).round(2) # Default 6 month window
            st.session_state.shared_amu = amu_df
            st.success("Database Updated!")

# =============================================================
# PAGE: FORECAST & SHOPPING
# =============================================================
elif page in ["AMU", "Forecast", "Shopping List"]:
    if st.session_state.shared_amu is None:
        st.warning("Please upload data first.")
    else:
        # Merge logic for forecasting
        df_a = st.session_state.shared_amu
        df_s = st.session_state.stock_df
        merged = pd.merge(df_a, df_s, on="Item", how="inner")
        
        # Calculate Depletion
        merged['Months_Left'] = np.where(merged['AMU'] > 0, (merged['Master'] / merged['AMU']).floor(), 12)
        merged['TargetDate'] = merged['Months_Left'].apply(lambda x: _BASE_MONTH + pd.DateOffset(months=int(x)))
        st.session_state.merged_data = merged

        if page == "AMU":
            st.dataframe(df_a, use_container_width=True)
        elif page == "Forecast":
            st.dataframe(merged[['Item', 'Master', 'AMU', 'TargetDate']], use_container_width=True)
        elif page == "Shopping List":
            sel_m = st.selectbox("Buying for Month", MONTH_OPTIONS)
            sel_d = pd.to_datetime(sel_m)
            shop = merged[merged['TargetDate'].dt.month == sel_d.month]
            st.dataframe(shop[['Item', 'AMU']], use_container_width=True)

# =============================================================
# PAGE: PURCHASE TENDER (THE NEW PART)
# =============================================================
elif page == "Purchase Tender":
    st.markdown('<div class="page-header"><h2>📝 Purchase Tender</h2></div>', unsafe_allow_html=True)
    
    if st.session_state.merged_data is None:
        st.warning("Run Forecast first to see items.")
    else:
        t1, t2 = st.tabs(["📤 1. Create Tender", "📥 2. Compare Quotes"])
        
        with t1:
            col1, col2 = st.columns([1, 2])
            with col1:
                target_str = st.selectbox("Target Month", MONTH_OPTIONS, key="t_month")
                target_dt = pd.to_datetime(target_str)
            
            # Pre-select items running out in that month
            merged = st.session_state.merged_data
            auto_items = merged[merged['TargetDate'].dt.month == target_dt.month]['Item'].tolist()
            
            with col2:
                final_list = st.multiselect("Select Items", options=sorted(merged['Item'].unique()), default=auto_items)
            
            if final_list:
                tender_df = merged[merged['Item'].isin(final_list)].copy()
                tender_df['Required'] = tender_df['AMU'].apply(lambda x: max(1, np.ceil(x)))
                
                st.dataframe(tender_df[['Item', 'Master', 'AMU', 'Required']], use_container_width=True)
                
                # Excel Export for Vendor
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export = tender_df[['Item', 'Required']].copy()
                    export['Unit Price'] = "" # Blank for vendor
                    export.to_excel(writer, index=False, sheet_name='Quote')
                
                st.download_button("📥 Download Excel Template", data=output.getvalue(), 
                                 file_name=f"Tender_{target_str.replace(' ','_')}.xlsx", type="primary")

        with t2:
            st.markdown("### Upload Vendor Sheets")
            files = st.file_uploader("Drop vendor files here", accept_multiple_files=True, type=['xlsx'])
            
            if files:
                all_q = []
                for f in files:
                    v_name = f.name.replace(".xlsx", "").replace("Tender_", "")
                    v_df = pd.read_excel(f)
                    if 'Unit Price' in v_df.columns:
                        v_df['Vendor'] = v_name
                        v_df['Unit Price'] = pd.to_numeric(v_df['Unit Price'], errors='coerce')
                        all_q.append(v_df[['Item', 'Required', 'Unit Price', 'Vendor']])
                
                if all_q:
                    combined = pd.concat(all_q)
                    best_idx = combined.groupby('Item')['Unit Price'].idxmin()
                    winners = combined.loc[best_idx]
                    
                    st.success("Comparison Complete!")
                    st.dataframe(winners, use_container_width=True, hide_index=True)
                    
                    with st.expander("Full Price Matrix"):
                        matrix = combined.pivot(index='Item', columns='Vendor', values='Unit Price')
                        st.dataframe(matrix.style.highlight_min(axis=1, color='#064e3b'))

# =============================================================
# PAGE: AI ASSISTANT
# =============================================================
elif page == "AI Assistant":
    st.markdown('<div class="page-header"><h2>🤖 Inventory AI</h2></div>', unsafe_allow_html=True)
    st.info("I can answer questions about your stock once data is uploaded.")
