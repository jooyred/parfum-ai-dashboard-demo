import streamlit as st
import pandas as pd
from pathlib import Path
from modules.calculations import (
    load_data, rupiah, pct, status_badge, overview_metrics, top_products, trend_daily,
    platform_revenue, product_mix, inventory_product_status, inventory_material_status,
    suggested_purchase_value, daily_report
)
from modules.chatbot_engine import answer_question
from modules.pdf_report import generate_daily_pdf_report

st.set_page_config(
    page_title="AI Business Control Tower - Parfum",
    page_icon="🧴",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).resolve().parent / "data"

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    .main { background: #f8fafc; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #051d2d 0%, #0c4a54 100%) !important;
    }
    [data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }
    
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        font-weight: 600;
        color: #d4af37 !important;
    }
    
    .metric-card {
        padding: 20px;
        background: white;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        margin-bottom: 12px;
        min-height: 120px;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.05);
    }
    .metric-card-good { border-top: 4px solid #10b981; }
    .metric-card-warning { border-top: 4px solid #f59e0b; }
    .metric-card-danger { border-top: 4px solid #ef4444; }
    
    .metric-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .metric-value { color: #0f172a; font-size: 1.5rem; font-weight: 800; margin-bottom: 4px; }
    .metric-delta { font-size: 0.8rem; font-weight: 600; display: flex; align-items: center; gap: 4px; }
    .metric-delta-good { color: #10b981; }
    .metric-delta-warning { color: #f59e0b; }
    .metric-delta-danger { color: #ef4444; }
    
    .ai-box {
        padding: 16px; background: #e8f4f5; border-left: 5px solid #0d6570;
        border-radius: 12px; color: #0b1f2e; margin-bottom: 14px;
        box-shadow: 0 2px 4px rgba(13,101,112,0.05);
        border-top: 1px solid rgba(13,101,112,0.1);
        border-right: 1px solid rgba(13,101,112,0.1);
        border-bottom: 1px solid rgba(13,101,112,0.1);
    }
    .warning-box {
        padding: 16px; background: #fff3ed; border-left: 5px solid #e8b14c;
        border-radius: 12px; color: #0b1f2e; margin-bottom: 14px;
        box-shadow: 0 2px 4px rgba(232,177,76,0.05);
        border-top: 1px solid rgba(232,177,76,0.1);
        border-right: 1px solid rgba(232,177,76,0.1);
        border-bottom: 1px solid rgba(232,177,76,0.1);
    }
    
    .chat-bubble-user {
        background: #0d6570; color: white; padding: 12px 16px;
        border-radius: 16px 16px 2px 16px; margin: 8px 0 8px auto;
        max-width: 80%; white-space: pre-wrap;
        box-shadow: 0 4px 6px rgba(13,101,112,0.15);
    }
    .chat-bubble-ai {
        background: white; color: #0f172a; padding: 14px 18px;
        border-radius: 16px 16px 16px 2px; margin: 8px auto 8px 0;
        border: 1px solid #e2e8f0; max-width: 88%; white-space: pre-wrap;
        box-shadow: 0 4px 6px rgba(15,23,42,0.05);
    }

    /* Custom Styled HTML Table */
    .styled-table-container {
        width: 100%;
        overflow-x: auto;
        margin-bottom: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        background: white;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .custom-styled-table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
    }
    .custom-styled-table th {
        background-color: #083047;
        color: white;
        font-weight: 600;
        padding: 12px 16px;
        font-size: 0.85rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .custom-styled-table td {
        padding: 12px 16px;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
        font-size: 0.85rem;
        vertical-align: middle;
    }
    .custom-styled-table tr:last-child td {
        border-bottom: none;
    }
    .custom-styled-table tr:nth-child(even) {
        background-color: #f8fafc;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session state initialization
if "uploaded_sales" not in st.session_state:
    st.session_state["uploaded_sales"] = None

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "display_name" not in st.session_state:
    st.session_state["display_name"] = None

import hashlib

def hash_password(password: str) -> str:
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), b"parfum_ai_secure_salt", 100000)
    return dk.hex()

def verify_password(stored_hash: str, password: str) -> bool:
    return hash_password(password) == stored_hash

has_auth = "auth_users" in st.secrets

if not has_auth:
    st.warning("⚠️ Auth belum dikonfigurasi. App berjalan dalam mode demo.")
    st.session_state["authenticated"] = True
    # Let user select role in sidebar
    st.sidebar.markdown("### 🛠️ Demo Mode Controls")
    demo_role = st.sidebar.selectbox("Pilih Role (Demo)", ["owner", "staff", "viewer"], key="demo_role_selection")
    st.session_state["role"] = demo_role
    st.session_state["display_name"] = f"Demo {demo_role.capitalize()}"
    st.session_state["username"] = f"demo_{demo_role}"
else:
    if not st.session_state.get("authenticated"):
        st.subheader("🧴 AI Business Control Tower - Login")
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Masuk", use_container_width=True)
            
            if submit_login:
                # Iterate and find username
                found_user = None
                for key, user_cfg in st.secrets["auth_users"].items():
                    if user_cfg.get("username") == username_input:
                        found_user = user_cfg
                        break
                
                if found_user and verify_password(found_user.get("password_hash"), password_input):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = found_user.get("username")
                    st.session_state["role"] = found_user.get("role")
                    st.session_state["display_name"] = found_user.get("display_name", username_input.capitalize())
                    st.success("Login sukses!")
                    st.rerun()
                else:
                    st.error("Username atau password salah.")
        st.stop()

# PDF Session States
if "daily_pdf_bytes" not in st.session_state:
    st.session_state["daily_pdf_bytes"] = None
if "daily_pdf_ready" not in st.session_state:
    st.session_state["daily_pdf_ready"] = False
if "daily_pdf_filename" not in st.session_state:
    st.session_state["daily_pdf_filename"] = ""

if "chatbot_pdf_bytes" not in st.session_state:
    st.session_state["chatbot_pdf_bytes"] = None
if "chatbot_pdf_ready" not in st.session_state:
    st.session_state["chatbot_pdf_ready"] = False
if "chatbot_pdf_filename" not in st.session_state:
    st.session_state["chatbot_pdf_filename"] = ""

def reset_pdf_states():
    st.session_state["daily_pdf_bytes"] = None
    st.session_state["daily_pdf_ready"] = False
    st.session_state["daily_pdf_filename"] = ""
    st.session_state["chatbot_pdf_bytes"] = None
    st.session_state["chatbot_pdf_ready"] = False
    st.session_state["chatbot_pdf_filename"] = ""

# Google Sheets Data Source Session States
if "data_source_mode" not in st.session_state:
    st.session_state["data_source_mode"] = "dummy"

if "google_sheets_data" not in st.session_state:
    st.session_state["google_sheets_data"] = None

if "active_sheet_id" not in st.session_state:
    st.session_state["active_sheet_id"] = None

# Helper to get active data based on source mode
def get_active_data():
    mode = st.session_state.get("data_source_mode", "dummy")
    if mode == "google_sheets" and st.session_state.get("google_sheets_data") is not None:
        return st.session_state["google_sheets_data"]
    if st.session_state.get("uploaded_sales") is not None:
        active = load_data()
        active["sales"] = st.session_state["uploaded_sales"]
        return active
    return load_data()

# Initialize dynamic sheets autoload
if st.session_state.get("google_sheets_data") is None:
    has_creds = "google_service_account" in st.secrets
    sheet_id = st.secrets.get("GOOGLE_SHEET_ID")
    if has_creds and sheet_id:
        try:
            from modules.sheets_loader import load_google_sheets_data, validate_sheet_tabs, normalize_google_sheet_data, get_sheet_id_from_url
            actual_id = get_sheet_id_from_url(sheet_id)
            creds_info = dict(st.secrets["google_service_account"])
            raw_data = load_google_sheets_data(actual_id, creds_info)
            is_valid, missing = validate_sheet_tabs(raw_data)
            if is_valid:
                st.session_state["google_sheets_data"] = normalize_google_sheet_data(raw_data)
                st.session_state["data_source_mode"] = "google_sheets"
                st.session_state["active_sheet_id"] = actual_id
                st.session_state["last_refresh_timestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                st.warning(f"⚠️ Google Sheets auto-load gagal! Tab wajib berikut tidak ditemukan: {', '.join(missing)}")
        except Exception as e:
            st.warning(f"⚠️ Google Sheets auto-load gagal! Terjadi error: {str(e)}")

data = get_active_data()

def render_metric(label, value, delta=None, status="good"):
    if status == "good":
        card_class = "metric-card-good"
        delta_class = "metric-delta-good"
    elif status == "warning":
        card_class = "metric-card-warning"
        delta_class = "metric-delta-warning"
    else:  # danger
        card_class = "metric-card-danger"
        delta_class = "metric-delta-danger"
        
    delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
        <div class="metric-card {card_class}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

def render_decision_card(title, value_html, desc):
    st.markdown(f"""
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; min-height: 180px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 12px;">
        <div style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 8px;">{title}</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 6px;">{value_html}</div>
        <div style="font-size: 0.75rem; color: #334155; line-height: 1.3;">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

def as_rp_df(df, cols):
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = out[c].apply(rupiah)
    return out

def render_styled_table(df):
    html = df.to_html(escape=False, index=False, justify='left')
    html = html.replace('border="1"', '').replace('class="dataframe"', 'class="custom-styled-table"')
    st.markdown(f'<div class="styled-table-container">{html}</div>', unsafe_allow_html=True)

def text_status_emoji(status):
    status_lower = str(status).strip().lower()
    if status_lower in ["aman", "sehat", "completed", "complete"]:
        return f"🟢 {status}"
    elif status_lower in ["rendah", "waspada"]:
        return f"🟡 {status}"
    elif status_lower in ["kritis", "boncos", "returned"]:
        return f"🔴 {status}"
    elif status_lower in ["shipped"]:
        return f"🔵 {status}"
    return status

# Sidebar Navigation
with st.sidebar:
    st.markdown("## 🧴 AI Business")
    st.markdown("### Control Tower")
    st.caption("Demo Bisnis Parfum V2")
    
    st.markdown(f"👤 **{st.session_state.get('display_name')}** ({st.session_state.get('role', 'viewer').upper()})")
    
    if has_auth:
        if st.button("Logout 🚪", use_container_width=True, key="app_logout_btn"):
            st.session_state["authenticated"] = False
            st.session_state["username"] = None
            st.session_state["role"] = None
            st.session_state["display_name"] = None
            st.rerun()
            
    st.markdown("---")
    
    role = st.session_state.get("role", "viewer")
    allowed_pages = {
        "owner": [
            "Owner Control Room",
            "Dashboard Overview",
            "Stok, HPP & Produksi",
            "Chatbot AI Bisnis",
            "Laporan Harian",
            "Finance & Tax",
            "Setup Data",
            "Data Health Check",
            "Data Dummy"
        ],
        "staff": [
            "Owner Control Room",
            "Dashboard Overview",
            "Stok, HPP & Produksi",
            "Chatbot AI Bisnis",
            "Laporan Harian",
            "Setup Data",
            "Data Health Check",
            "Data Dummy"
        ],
        "viewer": [
            "Owner Control Room",
            "Dashboard Overview",
            "Laporan Harian",
            "Data Health Check"
        ]
    }
    
    page_options = allowed_pages.get(role, ["Dashboard Overview"])
    
    page = st.radio(
        "Navigasi",
        page_options,
        label_visibility="collapsed"
    )
    
    if page not in allowed_pages.get(role, []):
        st.error("Akses ditolak untuk role Anda.")
        st.stop()
        
    st.markdown("---")
    
    # Data source status indicator in sidebar
    mode = st.session_state.get("data_source_mode", "dummy")
    if mode == "google_sheets" and st.session_state.get("google_sheets_data") is not None:
        st.sidebar.markdown(f"**Data Source:**<br/>{status_badge('Google Sheets')}", unsafe_allow_html=True)
        st.sidebar.markdown("<br/>", unsafe_allow_html=True)
        
        # Refresh button
        if st.sidebar.button("Refresh Google Sheets Data", use_container_width=True):
            with st.spinner("Refreshing Google Sheets..."):
                try:
                    from modules.sheets_loader import load_google_sheets_data, validate_sheet_tabs, normalize_google_sheet_data, get_sheet_id_from_url
                    actual_id = st.session_state.get("active_sheet_id") or get_sheet_id_from_url(st.secrets.get("GOOGLE_SHEET_ID", ""))
                    if actual_id:
                        creds_info = dict(st.secrets["google_service_account"])
                        raw_data = load_google_sheets_data(actual_id, creds_info)
                        is_valid, missing = validate_sheet_tabs(raw_data)
                        if is_valid:
                            st.session_state["google_sheets_data"] = normalize_google_sheet_data(raw_data)
                            st.session_state["last_refresh_timestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                            reset_pdf_states()
                            st.sidebar.success("Data di-refresh!")
                            st.rerun()
                        else:
                            st.sidebar.error(f"Refresh gagal! Tab hilang: {', '.join(missing)}")
                    else:
                        st.sidebar.error("Tidak ada Sheet ID aktif untuk di-refresh.")
                except Exception as e:
                    st.sidebar.error(f"Refresh gagal: {str(e)}")
                    
        if st.sidebar.button("Reset ke Dummy CSV", use_container_width=True, key="reset_from_sheets_sidebar"):
            st.session_state["data_source_mode"] = "dummy"
            st.session_state["google_sheets_data"] = None
            reset_pdf_states()
            st.rerun()
            
    elif mode == "uploaded_sales" or st.session_state["uploaded_sales"] is not None:
        st.sidebar.markdown(f"**Data Source:**<br/>{status_badge('Uploaded sales.csv')}", unsafe_allow_html=True)
        st.sidebar.markdown("<br/>", unsafe_allow_html=True)
        if st.sidebar.button("Reset ke Dummy CSV", use_container_width=True, key="reset_from_upload_sidebar"):
            st.session_state["uploaded_sales"] = None
            st.session_state["data_source_mode"] = "dummy"
            reset_pdf_states()
            st.rerun()
    else:
        st.sidebar.markdown(f"**Data Source:**<br/>{status_badge('Dummy CSV')}", unsafe_allow_html=True)
        
    # Refresh timestamp
    if mode == "google_sheets":
        ts = st.session_state.get("last_refresh_timestamp", "-")
        st.sidebar.markdown(f"<div style='margin-top: -5px; margin-bottom: 10px;'><small style='color: #cbd5e1;'>Last refresh: {ts}</small></div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"<div style='margin-top: 5px; margin-bottom: 10px;'><small style='color: #cbd5e1;'>Last refresh: local dummy data</small></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Demo V4A • Data dummy / Google Sheets")

# Routing Pages
# Routing Pages
if page == "Owner Control Room":
    st.title("Owner Control Room 👑")
    st.caption("Ringkasan keputusan harian untuk owner bisnis parfum berdasarkan data aktif.")
    
    # Financial metrics
    sales = data["sales"]
    m = overview_metrics(sales)
    margin_val = m["margin"]
    
    # Stock status
    invp = inventory_product_status(data["inventory_products"])
    critical_products = invp[invp["status"] == "Kritis"]
    produk_kritis_count = len(critical_products)
    
    # Materials status
    invm = inventory_material_status(data["inventory_materials"])
    critical_materials = invm[invm["status"] == "Kritis"]
    bahan_kritis_count = len(critical_materials)
    
    # Business health logic
    if margin_val < 0.15 or produk_kritis_count > 5 or bahan_kritis_count > 12:
        status_bisnis = "Kritis"
        status_class = "metric-card-danger"
        status_desc = "🔴 **Kondisi Kritis:** Profitabilitas di bawah batas minimal (15%) atau terjadi kelangkaan stok/bahan yang parah. Tindakan korektif segera diperlukan!"
    elif margin_val >= 0.25 and produk_kritis_count <= 3 and bahan_kritis_count <= 10:
        status_bisnis = "Sehat"
        status_class = "metric-card-good"
        status_desc = "🟢 **Kondisi Sehat:** Profitabilitas sangat prima (>= 25%) dan level stok produk kritis serta bahan baku masih terkendali. Pertahankan!"
    else:
        status_bisnis = "Waspada"
        status_class = "metric-card-warning"
        status_desc = "🟡 **Kondisi Waspada:** Margin laba sedang atau terdapat produk/bahan kritis yang butuh perhatian. Lakukan tindakan preventif."

    # Render Business Status Card
    st.markdown(f"""
    <div class="metric-card {status_class}" style="min-height: auto; padding: 15px; margin-bottom: 20px;">
        <div class="metric-label">Status Kesehatan Bisnis Hari Ini</div>
        <div class="metric-value" style="font-size: 2rem; display: flex; align-items: center; gap: 10px;">
            {status_bisnis.upper()}
        </div>
        <div style="font-size: 0.9rem; margin-top: 8px; color: #1e293b;">{status_desc}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Gather decision cards data
    # 1. Financial summary
    fin_desc = "Profitabilitas sangat prima." if margin_val >= 0.25 else "Profitabilitas cukup stabil." if margin_val >= 0.15 else "Profitabilitas rendah, tekan biaya operasional."
    fin_val_html = f"{rupiah(m['profit'])} <span style='font-size: 0.8rem; font-weight: normal; color: #64748b;'>({pct(margin_val)} Margin)</span>"
    
    # 2. Production priority
    pp = data["production_plan"]
    need_prod = pp[pp["recommended_production"] > 0]
    if not need_prod.empty:
        top_prod = need_prod.sort_values("recommended_production", ascending=False).iloc[0]
        prod_val_html = top_prod['product']
        prod_desc = f"Rekomendasi produksi <b>{int(top_prod['recommended_production'])} pcs</b> karena stock rendah ({int(top_prod['stock'])} pcs) & demand 7d tinggi ({int(top_prod['demand_7d'])} pcs). Bottleneck: {top_prod['bottleneck']}."
    else:
        prod_val_html = "Aman"
        prod_desc = "Semua stok produk mencukupi, tidak ada antrean produksi mendesak."
        
    # 3. Materials shopping
    need_m, suggested_cost = suggested_purchase_value(data["inventory_materials"])
    if not need_m.empty:
        mats_list = ", ".join(need_m.head(3)["material"].tolist())
        mats_val_html = mats_list
        mats_desc = f"Beli bahan baku kritis: {mats_list}. Estimasi total anggaran belanja: <b>{rupiah(suggested_cost)}</b>."
    else:
        mats_val_html = "Aman"
        mats_desc = "Stok bahan baku aman dan mencukupi kebutuhan operasional."
        
    # 4. Ads review
    ads_df = data["ads"]
    critical_ads = ads_df[ads_df["status"].isin(["Waspada", "Boncos"])]
    if not critical_ads.empty:
        ads_list = ", ".join(critical_ads.head(2)["campaign"].tolist())
        ads_val_html = ads_list
        ads_desc = f"Campaign <b>{ads_list}</b> performa Waspada/Boncos. Rekomendasi: Evaluasi creative, turunkan budget, atau pause campaign."
    else:
        ads_val_html = "Sehat"
        ads_desc = "Seluruh campaign iklan berjalan lancar dengan ROAS di atas target."
        
    # 5. Top Profit Product
    top_prod_df = top_products(sales, latest_only=False)
    if not top_prod_df.empty:
        cuan_row = top_prod_df.iloc[0]
        cuan_val_html = cuan_row['product']
        cuan_desc = f"Produk bermargin profit tertinggi (<b>{pct(cuan_row['margin'])}</b>). Rekomendasi: Dorong volume penjualan via bundling/promo."
    else:
        cuan_val_html = "N/A"
        cuan_desc = "Data produk tidak tersedia."
        
    # Render 5 columns
    col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
    with col_c1:
        render_decision_card("💵 Keuangan", fin_val_html, fin_desc)
    with col_c2:
        render_decision_card("🏭 Produksi Prioritas", prod_val_html, prod_desc)
    with col_c3:
        render_decision_card("🧪 Belanja Bahan", mats_val_html, mats_desc)
    with col_c4:
        render_decision_card("📣 Iklan Perlu Dicek", ads_val_html, ads_desc)
    with col_c5:
        render_decision_card("🏆 Produk Ter-Cuan", cuan_val_html, cuan_desc)
        
    st.markdown("---")
    
    # Action Plan & WhatsApp Export
    col_ap1, col_ap2 = st.columns([3, 2])
    with col_ap1:
        st.subheader("🎯 Action Plan Hari Ini")
        st.markdown("Berikut adalah rekomendasi rencana aksi operasional hari ini secara otomatis:")
        
        action_plans = []
        if not need_prod.empty:
            top_prod_row = need_prod.sort_values("recommended_production", ascending=False).iloc[0]
            action_plans.append(f"Produksi <b>{top_prod_row['product']}</b> sebanyak <b>{int(top_prod_row['recommended_production'])} pcs</b> untuk memenuhi demand. Bottleneck: {top_prod_row['bottleneck']}.")
        else:
            action_plans.append("Stok produk jadi mencukupi, tidak perlu jadwal produksi baru hari ini.")

        if not need_m.empty:
            mats_list = ", ".join(need_m.head(3)["material"].tolist())
            action_plans.append(f"Lakukan pengadaan bahan baku kritis: <b>{mats_list}</b> dengan estimasi anggaran <b>{rupiah(suggested_cost)}</b>.")
        else:
            action_plans.append("Stok bahan baku aman, tidak ada rencana belanja mendesak.")

        if not critical_ads.empty:
            ads_list = ", ".join(critical_ads["campaign"].tolist())
            action_plans.append(f"Evaluasi creative atau sesuaikan budget campaign iklan: <b>{ads_list}</b> karena performa Waspada/Boncos.")
        else:
            action_plans.append("Seluruh campaign iklan berjalan sehat dengan ROAS di atas target.")

        if not top_prod_df.empty:
            cuan_row = top_prod_df.iloc[0]
            action_plans.append(f"Optimalkan pemasaran produk bermargin tinggi <b>{cuan_row['product']}</b> ({pct(cuan_row['margin'])}) untuk meningkatkan profit bersih.")
        else:
            action_plans.append("Pertahankan harga jual saat ini untuk menjaga kestabilan margin.")

        action_plans.append("Verifikasi silang (cross-check) stok fisik botol kemasan sebelum meluncurkan surat perintah kerja produksi.")
        
        for idx, plan in enumerate(action_plans, start=1):
            st.markdown(f"{idx}. {plan}", unsafe_allow_html=True)
            
    with col_ap2:
        st.subheader("📋 Ringkasan WhatsApp")
        st.caption("Salin ringkasan keputusan harian di bawah ini untuk dikirimkan ke WhatsApp tim Anda.")
        
        summary_text = (
            f"📋 *RINGKASAN KEPUTUSAN HARIAN OWNER*\n"
            f"📅 Tanggal: {m['latest_date'].strftime('%Y-%m-%d')}\n"
            f"🏥 Status Bisnis: {status_bisnis.upper()}\n\n"
            f"💵 Finansial:\n"
            f"   - Omzet: {rupiah(m['gross'])}\n"
            f"   - Profit Bersih: {rupiah(m['profit'])}\n"
            f"   - Margin: {pct(margin_val)}\n\n"
            f"🎯 Rencana Aksi Hari Ini:\n"
        )
        for idx, plan in enumerate(action_plans, start=1):
            clean_plan = plan.replace("<b>", "").replace("</b>", "")
            summary_text += f"{idx}. {clean_plan}\n"
            
        st.text_area("WhatsApp Copy-Paste", value=summary_text, height=200, label_visibility="collapsed")
        
        if st.session_state.get("role") != "viewer":
            st.download_button(
                "📥 Unduh Ringkasan Owner (.txt)",
                summary_text,
                file_name="owner_summary_harian.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("ℹ️ Mode Readonly: Ekspor ringkasan dinonaktifkan untuk role Viewer.")

elif page == "Dashboard Overview":
    st.title("Dashboard Overview 📊")
    st.caption("Ringkasan performa bisnis parfum berdasarkan data dummy atau uploaded CSV.")
    
    # Indicators
    col_ind1, col_ind2 = st.columns([2, 1])
    with col_ind1:
        if st.session_state["uploaded_sales"] is not None:
            st.markdown(f"💡 **Data Aktif:** {status_badge('Uploaded sales.csv')}", unsafe_allow_html=True)
        else:
            st.markdown(f"💡 **Data Aktif:** {status_badge('Data Dummy')}", unsafe_allow_html=True)
            
    sales = data["sales"]
    m = overview_metrics(sales)
    invp = inventory_product_status(data["inventory_products"])
    stock_critical = len(invp[invp["status"] == "Kritis"])
    
    # KPI cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    gross_change_label = f"▲ {pct(m['gross_change'])} vs kemarin" if m['gross_change'] >= 0 else f"▼ {pct(abs(m['gross_change']))} vs kemarin"
    gross_status = "good" if m['gross_change'] >= 0 else "warning"
    with c1: 
        render_metric("Omzet Hari Ini", rupiah(m["gross"]), gross_change_label, gross_status)
        
    profit_change_label = f"▲ {pct(m['profit_change'])} vs kemarin" if m['profit_change'] >= 0 else f"▼ {pct(abs(m['profit_change']))} vs kemarin"
    profit_status = "good" if m['profit_change'] >= 0 else "danger"
    with c2: 
        render_metric("Profit Bersih", rupiah(m["profit"]), profit_change_label, profit_status)
        
    margin_status = "good" if m["margin"] >= 0.25 else ("warning" if m["margin"] >= 0.15 else "danger")
    with c3: 
        render_metric("Margin Bersih", pct(m["margin"]), "target > 25%", margin_status)
        
    orders_change_label = f"▲ {pct(m['orders_change'])} vs kemarin" if m['orders_change'] >= 0 else f"▼ {pct(abs(m['orders_change']))} vs kemarin"
    orders_status = "good" if m['orders_change'] >= 0 else "warning"
    with c4: 
        render_metric("Order", f"{m['orders']:,}".replace(",", "."), orders_change_label, orders_status)
        
    ad_change_label = f"▲ {pct(m['ad_change'])} vs kemarin" if m['ad_change'] >= 0 else f"▼ {pct(abs(m['ad_change']))} vs kemarin"
    ad_status = "good" if m["ad_change"] <= 0.1 else "warning"
    with c5: 
        render_metric("Ad Cost", rupiah(m["ad_spend"]), ad_change_label, ad_status)
        
    critical_status = "good" if stock_critical == 0 else "danger"
    with c6: 
        render_metric("Stok Kritis", f"{stock_critical} SKU", "perlu tindakan", critical_status)

    st.markdown("---")
    st.markdown("### Tren & Performa Marketplace")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Tren Omzet vs Profit (14 Hari Terakhir)")
        trend = trend_daily(sales).tail(14).set_index("date")
        st.line_chart(trend[["Omzet", "Profit"]])
    with col_b:
        st.subheader("Omzet per Marketplace")
        pr = platform_revenue(sales).set_index("platform")
        st.bar_chart(pr["omzet"])

    st.markdown("---")
    col_c, col_d = st.columns([1, 2])
    with col_c:
        st.markdown("### Mix Produk")
        mix = product_mix(sales).head(6)
        mix_show = as_rp_df(mix, ["omzet"])
        mix_show.columns = ["Produk", "Omzet"]
        render_styled_table(mix_show)
    with col_d:
        st.markdown("### Top Produk Hari Ini")
        top = top_products(sales, latest_only=True).head(8)
        top = top.merge(invp[["sku", "stock", "status"]], on="sku", how="left")
        show = top[["product", "terjual", "omzet", "profit", "margin", "stock", "status"]].copy()
        
        # Rename columns to Indonesian
        show.columns = ["Produk", "Terjual (pcs)", "Omzet", "Profit", "Margin", "Stok Jadi", "Status Stok"]
        show["Margin"] = show["Margin"].apply(pct)
        show = as_rp_df(show, ["Omzet", "Profit"])
        show["Status Stok"] = show["Status Stok"].apply(status_badge)
        
        render_styled_table(show)

    st.markdown("---")
    st.markdown("### Insight AI Hari Ini")
    
    # 4 dynamic insights
    # 1. Finance
    if m["margin"] >= 0.25:
        ins_1 = f"<b>Omzet & profit sedang positif</b><br/>Margin bersih hari ini mencapai {pct(m['margin'])} (di atas target 25%). Komposisi penjualan SKU premium mendukung performa ini."
        box_1_class = "ai-box"
    else:
        ins_1 = f"<b>Margin di bawah target</b><br/>Margin bersih hari ini {pct(m['margin'])} berada di bawah target 25%. Pertimbangkan mengurangi diskon atau optimasi biaya iklan."
        box_1_class = "warning-box"

    # 2. Inventory
    if stock_critical > 0:
        ins_2 = f"<b>Stok kritis perlu ditindaklanjuti</b><br/>Terdapat {stock_critical} SKU produk jadi dengan stok di bawah minimum. Silakan jadwalkan pengisian stok."
        box_2_class = "warning-box"
    else:
        ins_2 = "<b>Stok produk aman</b><br/>Seluruh stok produk jadi berada dalam kondisi aman di atas batas minimum."
        box_2_class = "ai-box"

    # 3. Production Recommendation
    rec_prod_names = data["production_plan"][data["production_plan"]["recommended_production"] > 0]["product"].tolist()
    if rec_prod_names:
        ins_3 = f"<b>Rekomendasi produksi prioritas</b><br/>Prioritaskan jadwal produksi minggu ini untuk SKU: {', '.join(rec_prod_names[:3])}."
        box_3_class = "ai-box"
    else:
        ins_3 = "<b>Rencana produksi aman</b><br/>Tidak ada jadwal produksi mendesak untuk minggu ini. Semua kebutuhan terpenuhi."
        box_3_class = "ai-box"

    # 4. Ads
    boncos_campaigns = data["ads"][data["ads"]["status"] == "Boncos"]["campaign"].tolist()
    if boncos_campaigns:
        ins_4 = f"<b>Iklan perlu evaluasi</b><br/>Campaign {', '.join(boncos_campaigns)} terdeteksi boncos (ROAS rendah). Sebaiknya kurangi budget sementara."
        box_4_class = "warning-box"
    else:
        ins_4 = "<b>Iklan berjalan efisien</b><br/>Seluruh campaign iklan memiliki ROAS sehat dan memberikan profit optimal."
        box_4_class = "ai-box"
        
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown(f"<div class='{box_1_class}'>{ins_1}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='{box_2_class}'>{ins_2}</div>", unsafe_allow_html=True)
    with col_i2:
        st.markdown(f"<div class='{box_3_class}'>{ins_3}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='{box_4_class}'>{ins_4}</div>", unsafe_allow_html=True)

elif page == "Stok, HPP & Produksi":
    st.title("Stok, HPP & Produksi 📦")
    st.caption("Kontrol stok barang jadi, bahan baku, HPP per botol, dan rekomendasi produksi.")
    
    invp = inventory_product_status(data["inventory_products"])
    invm = inventory_material_status(data["inventory_materials"])
    need, suggested_value = suggested_purchase_value(data["inventory_materials"])
    avg_hpp = data["products"]["hpp"].mean()
    
    # Calculate Nilai Stok
    total_stock_value = invp.merge(data["products"][["sku", "hpp"]], on="sku", how="left")
    total_stock_value = (total_stock_value["stock"] * total_stock_value["hpp"]).sum()
    
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: 
        render_metric("Nilai Stok", rupiah(total_stock_value), "berdasarkan HPP", "good")
    with c2: 
        num_crit_m = len(invm[invm['status']=='Kritis'])
        render_metric("Bahan Kritis", f"{num_crit_m} item", "cek pembelian", "warning" if num_crit_m > 0 else "good")
    with c3: 
        num_crit_p = len(invp[invp['status']=='Kritis'])
        render_metric("Produk Kritis", f"{num_crit_p} SKU", "cek produksi", "warning" if num_crit_p > 0 else "good")
    with c4: 
        render_metric("HPP Rata-rata", rupiah(avg_hpp), "per botol", "good")
    with c5: 
        render_metric("Belanja Disarankan", rupiah(suggested_value), "estimasi restok", "warning" if suggested_value > 0 else "good")

    st.markdown("---")
    st.markdown("### Stok Barang Jadi")
    show_invp = invp[["sku", "product", "stock", "min_stock", "avg_daily_sold", "estimasi_hari_habis", "status"]].copy()
    show_invp.columns = ["SKU", "Produk", "Stok", "Min Stok", "Rata-rata Terjual/Hari", "Estimasi Habis (Hari)", "Status Stok"]
    show_invp["Status Stok"] = show_invp["Status Stok"].apply(status_badge)
    
    render_styled_table(show_invp)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Bahan Baku")
        show_invm = invm.sort_values(["status", "material"]).copy()
        show_invm["unit_cost"] = show_invm["unit_cost"].apply(rupiah)
        show_invm.columns = ["Bahan Baku", "Satuan", "Stok", "Min Stok", "Biaya per Unit", "Status"]
        show_invm["Status"] = show_invm["Status"].apply(status_badge)
        
        render_styled_table(show_invm)
    with col2:
        st.markdown("### Rekomendasi Produksi")
        show_prod = data["production_plan"].copy()
        show_prod.columns = ["SKU", "Produk", "Permintaan 7 Hari", "Stok Saat Ini", "Produksi Disarankan", "Bottleneck"]
        
        def format_bottleneck(b):
            if b == "Aman":
                return f'<span style="color: #10b981; font-weight: 600;">{b}</span>'
            else:
                return f'<span style="color: #ef4444; font-weight: 600;">⚠️ {b}</span>'
        show_prod["Bottleneck"] = show_prod["Bottleneck"].apply(format_bottleneck)
        
        render_styled_table(show_prod)

    st.markdown("---")
    st.markdown("### Rincian HPP per SKU")
    sku_options = data["products"]["sku"].tolist()
    prod_index = data["products"].set_index("sku")
    selected_sku = st.selectbox("Pilih SKU untuk Rincian HPP", sku_options, format_func=lambda sku: f"{sku} - {prod_index.loc[sku, 'product']} {prod_index.loc[sku, 'size']}")
    bom = data["bom"][data["bom"]["sku"] == selected_sku].copy()
    if bom.empty:
        st.info("Detail BOM/HPP untuk SKU ini belum diisi pada data dummy.")
    else:
        total = bom["component_cost"].sum()
        bom["% HPP"] = (bom["component_cost"] / total).fillna(0)
        col_h1, col_h2 = st.columns([1.2, 1])
        with col_h1:
            bom_show = bom[["component", "unit", "qty_usage", "component_cost", "% HPP"]].copy()
            bom_show["component_cost"] = bom_show["component_cost"].apply(rupiah)
            bom_show["% HPP"] = bom_show["% HPP"].apply(pct)
            bom_show.columns = ["Komponen", "Satuan", "Kebutuhan", "Biaya Komponen", "% HPP"]
            render_styled_table(bom_show)
            st.success(f"Total HPP per botol: {rupiah(total)}")
        with col_h2:
            st.bar_chart(bom.set_index("component")["component_cost"])

    st.markdown("---")
    st.markdown("### Rekomendasi AI")
    st.markdown(f"<div class='ai-box'><b>Rencana Belanja Bahan Baku:</b><br/>Estimasi total kebutuhan anggaran pembelian bahan saat ini adalah <b>{rupiah(suggested_value)}</b>. Prioritaskan bahan dengan status <i>Kritis</i> sebelum menaikkan target produksi atau anggaran iklan untuk varian terkait.</div>", unsafe_allow_html=True)

elif page == "Chatbot AI Bisnis":
    st.title("Chatbot AI Bisnis 🤖")
    st.caption("Demo chatbot AI Bisnis Parfum ini. Versi berikutnya dapat dihubungkan ke AI API agar lebih fleksibel.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [("ai", "Halo! Aku siap membantu menganalisis data bisnis parfum Anda. Coba tanyakan hal-macam seperti:\n- Profit bersih hari ini berapa?\n- Produk paling laku apa?\n- Stok mana yang kritis?\n- Bahan apa yang harus dibeli?\n- Buatkan laporan harian.")]

    col_left, col_chat, col_right = st.columns([1.0, 2.2, 1.0])
    with col_left:
        st.markdown("### ⚡ Aksi Cepat")
        quicks = [
            "Profit bersih hari ini berapa?",
            "Produk paling laku apa?",
            "Produk paling untung apa?",
            "SKU mana yang harus diproduksi minggu ini?",
            "Bahan apa yang harus dibeli?",
            "Stok mana yang kritis?",
            "Iklan mana yang boncos?",
            "Buatkan laporan harian.",
        ]
        for q in quicks:
            if st.button(q, use_container_width=True, key=f"quick_{q}"):
                st.session_state.messages.append(("user", q))
                st.session_state.messages.append(("ai", answer_question(q, data)))
                st.rerun()

    with col_chat:
        st.markdown("### 💬 Percakapan")
        chat_box = st.container(height=520)
        with chat_box:
            for role, msg in st.session_state.messages:
                if role == "user":
                    st.markdown(f'<div class="chat-bubble-user">{msg}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble-ai">{msg}</div>', unsafe_allow_html=True)
                    
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Tanya sesuatu", placeholder="Tanya soal penjualan, stok, HPP, iklan, atau profit...", label_visibility="collapsed")
            submitted = st.form_submit_button("Kirim", use_container_width=True)
            
        if submitted and user_input:
            st.session_state.messages.append(("user", user_input))
            st.session_state.messages.append(("ai", answer_question(user_input, data)))
            st.rerun()
            
        if st.button("Reset Chat", use_container_width=True):
            st.session_state.messages = [("ai", "Chat direset. Halo! Silakan ajukan pertanyaan Anda mengenai performa bisnis.")]
            st.rerun()

    with col_right:
        st.markdown("### 📊 Ringkasan Hari Ini")
        m = overview_metrics(data["sales"])
        st.metric("Omzet Hari Ini", rupiah(m["gross"]), f"{pct(m['gross_change'])} vs kemarin")
        st.metric("Profit Bersih", rupiah(m["profit"]), f"{pct(m['profit_change'])} vs kemarin")
        st.metric("Margin Bersih", pct(m["margin"]))
        
        st.markdown("---")
        st.markdown("### 📥 Download Laporan")
        report = daily_report(data)
        
        # Download TXT
        st.download_button(
            label="📄 Download Laporan (TXT)",
            data=report,
            file_name=f"laporan_harian_parfum_{m['latest_date'].date()}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        # Download PDF
        if st.session_state["chatbot_pdf_ready"]:
            st.download_button(
                label="📥 Download Laporan (PDF)",
                data=st.session_state["chatbot_pdf_bytes"],
                file_name=st.session_state["chatbot_pdf_filename"],
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf_report_chatbot"
            )
            if st.button("Buat Ulang PDF", key="regenerate_pdf_report_chatbot", use_container_width=True):
                st.session_state["chatbot_pdf_ready"] = False
                st.session_state["chatbot_pdf_bytes"] = None
                st.rerun()
        else:
            if st.button("Generate Laporan PDF", key="generate_pdf_report_chatbot", use_container_width=True):
                pdf_bytes = generate_daily_pdf_report(data)
                st.session_state["chatbot_pdf_bytes"] = pdf_bytes
                st.session_state["chatbot_pdf_ready"] = True
                st.session_state["chatbot_pdf_filename"] = f"laporan_harian_parfum_{m['latest_date'].date()}.pdf"
                st.success("PDF berhasil dibuat. Silakan klik Download Laporan (PDF) di atas.")
                st.rerun()
        
        st.markdown("---")
        st.info("💡 **Catatan:** Demo chatbot ini masih rule-based. Versi berikutnya dapat dihubungkan ke AI API (seperti Gemini API) agar lebih fleksibel.")

elif page == "Laporan Harian":
    st.title("Laporan Harian 📋")
    st.caption("Contoh output laporan otomatis yang bisa dikirim ke owner, WhatsApp, atau Telegram, serta diekspor ke PDF.")
    
    report = daily_report(data)
    st.text_area("Preview Laporan (Text)", report, height=480)
    
    if st.session_state.get("role") != "viewer":
        c_l1, c_l2 = st.columns(2)
        with c_l1:
            st.download_button(
                label="📥 Download Laporan (TXT)",
                data=report,
                file_name="laporan_harian_bisnis_parfum.txt",
                mime="text/plain",
                use_container_width=True
            )
        with c_l2:
            if st.session_state["daily_pdf_ready"]:
                st.download_button(
                    label="📥 Download Laporan (PDF)",
                    data=st.session_state["daily_pdf_bytes"],
                    file_name=st.session_state["daily_pdf_filename"],
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_pdf_report_daily"
                )
                if st.button("Buat Ulang PDF", key="regenerate_pdf_report_daily", use_container_width=True):
                    st.session_state["daily_pdf_ready"] = False
                    st.session_state["daily_pdf_bytes"] = None
                    st.rerun()
            else:
                if st.button("Generate PDF Report", key="generate_pdf_report_daily", use_container_width=True):
                    m = overview_metrics(data["sales"])
                    pdf_bytes = generate_daily_pdf_report(data)
                    st.session_state["daily_pdf_bytes"] = pdf_bytes
                    st.session_state["daily_pdf_ready"] = True
                    st.session_state["daily_pdf_filename"] = f"laporan_harian_bisnis_parfum_{m['latest_date'].date()}.pdf"
                    st.success("PDF berhasil dibuat. Silakan klik Download Laporan (PDF) di atas.")
                    st.rerun()
    else:
        st.info("ℹ️ Mode Readonly: Unduh laporan PDF/TXT dinonaktifkan untuk role Viewer.")

elif page == "Setup Data":
    st.title("Setup Data ⚙️")
    st.caption("Halaman ini membantu Anda menyiapkan data bisnis nyata Anda untuk diintegrasikan ke control tower.")
    
    st.markdown("""
    ### ⚙️ Cara Mengintegrasikan Data Anda
    Untuk beralih dari mode demo/dummy ke data real bisnis Anda, sistem membutuhkan beberapa file data utama. 
    Format kolom harus konsisten agar sistem perhitungan dan AI engine dapat berjalan tanpa error.
    """)
    
    st.markdown("### 1️⃣ Struktur Data yang Dibutuhkan")
    setup_info = pd.DataFrame([
        {"Nama File": "products.csv", "Fungsi": "Master data produk & SKU", "Contoh Kolom": "sku, product, size, category, price, hpp, target_margin"},
        {"Nama File": "sales.csv", "Fungsi": "Data transaksi penjualan marketplace", "Contoh Kolom": "date, platform, order_id, sku, product, qty, price, discount, marketplace_fee, packing_cost, ad_cost_allocated, hpp, gross_revenue, net_revenue, net_profit, net_margin, order_status"},
        {"Nama File": "inventory_products.csv", "Fungsi": "Stok barang jadi (botol siap jual)", "Contoh Kolom": "sku, product, stock, min_stock, avg_daily_sold"},
        {"Nama File": "inventory_materials.csv", "Fungsi": "Stok bahan baku (bibit, alkohol, botol, box, dll)", "Contoh Kolom": "material, unit, stock, min_stock, unit_cost"},
        {"Nama File": "bom_hpp.csv", "Fungsi": "Formula / Bill of Materials (BOM) & HPP per SKU", "Contoh Kolom": "sku, component, unit, qty_usage, component_cost"},
        {"Nama File": "ads.csv", "Fungsi": "Data performa iklan berbayar", "Contoh Kolom": "platform, campaign, spend, revenue, orders, roas, status"},
        {"Nama File": "production_plan.csv", "Fungsi": "Rekomendasi rencana produksi mingguan", "Contoh Kolom": "sku, product, demand_7d, stock, recommended_production, bottleneck"},
    ])
    
    setup_info.columns = ["Nama File", "Fungsi", "Contoh Kolom"]
    render_styled_table(setup_info)
    
    st.markdown("---")
    st.markdown("### 2️⃣ Unggah Data Penjualan Anda (sales.csv)")
    st.info("Cobalah mengunggah file `sales.csv` Anda di sini. Sistem akan memvalidasi kolom dan langsung menggunakannya pada dashboard, chatbot, dan laporan selama sesi berjalan.")
    
    uploaded_file = st.file_uploader("Pilih file sales.csv", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = [
                "date", "platform", "order_id", "sku", "product", "qty", "price", "discount",
                "marketplace_fee", "packing_cost", "ad_cost_allocated", "hpp", "gross_revenue",
                "net_revenue", "net_profit", "net_margin", "order_status"
            ]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"⚠️ Upload Gagal! Kolom berikut tidak ditemukan: {', '.join(missing_cols)}")
            else:
                # Parse date
                df["date"] = pd.to_datetime(df["date"])
                # Cast numericals safely
                numeric_cols = ["qty", "price", "discount", "marketplace_fee", "packing_cost", "ad_cost_allocated", "hpp", "gross_revenue", "net_revenue", "net_profit", "net_margin"]
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                
                st.session_state["uploaded_sales"] = df
                st.session_state["data_source_mode"] = "uploaded_sales"
                st.session_state["google_sheets_data"] = None  # Disable sheets when uploading CSV
                reset_pdf_states()
                st.success("🎉 File sales.csv berhasil diunggah! Seluruh halaman dashboard, chatbot, dan laporan saat ini menggunakan data penjualan Anda.")
                st.rerun()
        except Exception as e:
            st.error(f"Error saat memproses file: {str(e)}")
            
    if st.session_state["uploaded_sales"] is not None:
        df_uploaded = st.session_state["uploaded_sales"]
        st.markdown("#### Preview 20 Baris Pertama Data Uploaded")
        preview_df = df_uploaded.head(20).copy()
        # Use simple status emojis for native streamlit dataframe display
        preview_df["order_status"] = preview_df["order_status"].apply(text_status_emoji)
        st.dataframe(preview_df, hide_index=True, use_container_width=True)
        
        st.markdown("#### Ringkasan Data yang Diunggah")
        num_rows = len(df_uploaded)
        min_date = df_uploaded["date"].min().strftime("%Y-%m-%d")
        max_date = df_uploaded["date"].max().strftime("%Y-%m-%d")
        num_platforms = df_uploaded["platform"].nunique()
        num_skus = df_uploaded["sku"].nunique()
        total_gross = df_uploaded["gross_revenue"].sum()
        total_profit = df_uploaded["net_profit"].sum()
        
        c_s1, c_s2, c_s3 = st.columns(3)
        with c_s1:
            st.metric("Jumlah Transaksi", f"{num_rows} baris")
            st.metric("Jumlah Platform", f"{num_platforms}")
        with c_s2:
            st.metric("Periode Data", f"{min_date} s/d {max_date}")
            st.metric("Jumlah SKU", f"{num_skus}")
        with c_s3:
            st.metric("Total Omzet", rupiah(total_gross))
            st.metric("Total Profit", rupiah(total_profit))

    st.markdown("---")
    st.markdown("### 3️⃣ Google Sheets Data Source 📊")
    st.markdown("""
    Anda dapat menghubungkan Control Tower ini langsung ke Google Sheets Anda agar data ter-update secara real-time.
    Spreadsheet Anda harus memiliki nama tab wajib berikut:
    `products`, `sales`, `inventory_products`, `inventory_materials`, `bom_hpp`, `ads`, `production_plan`
    """)
    
    # Check if service account is configured
    has_creds = "google_service_account" in st.secrets
    if not has_creds:
        st.warning("⚠️ **Service Account belum dikonfigurasi!** Untuk mengaktifkan Google Sheets, masukkan kredensial Service Account Anda ke dalam berkas `.streamlit/secrets.toml` (jika berjalan secara lokal) atau tambahkan ke Secrets di dashboard Streamlit Cloud.")
    else:
        st.success("✅ **Service Account siap digunakan.**")
        
        # Enter Sheet ID or URL
        sheet_url_input = st.text_input(
            "Masukkan URL atau ID Google Sheets", 
            value=st.secrets.get("GOOGLE_SHEET_ID", ""),
            placeholder="https://docs.google.com/spreadsheets/d/.../edit",
            key="sheet_url_input_field"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Test Load & Aktifkan Google Sheets", use_container_width=True, key="btn_test_load_sheets"):
                if not sheet_url_input:
                    st.error("Masukkan URL atau ID Google Sheets terlebih dahulu.")
                else:
                    with st.spinner("Menghubungkan ke Google Sheets..."):
                        try:
                            from modules.sheets_loader import load_google_sheets_data, validate_sheet_tabs, normalize_google_sheet_data, get_sheet_id_from_url
                            actual_id = get_sheet_id_from_url(sheet_url_input)
                            creds_info = dict(st.secrets["google_service_account"])
                            raw_data = load_google_sheets_data(actual_id, creds_info)
                            is_valid, missing = validate_sheet_tabs(raw_data)
                            
                            if is_valid:
                                st.session_state["google_sheets_data"] = normalize_google_sheet_data(raw_data)
                                st.session_state["data_source_mode"] = "google_sheets"
                                st.session_state["active_sheet_id"] = actual_id
                                st.session_state["uploaded_sales"] = None  # Clear uploaded CSV if loading Sheets
                                reset_pdf_states()  # Reset stale PDF bytes
                                st.success("🎉 Google Sheets berhasil dimuat dan diaktifkan sebagai sumber data utama!")
                                st.rerun()
                            else:
                                st.error(f"Tab wajib tidak lengkap! Tab berikut hilang atau kosong: {', '.join(missing)}")
                        except Exception as e:
                            st.error(f"Gagal memuat Google Sheets: {str(e)}")
        with col_btn2:
            if st.session_state["google_sheets_data"] is not None:
                if st.button("Nonaktifkan Google Sheets", use_container_width=True, key="btn_disable_sheets"):
                    st.session_state["data_source_mode"] = "dummy"
                    st.session_state["google_sheets_data"] = None
                    st.session_state["active_sheet_id"] = None
                    reset_pdf_states()
                    st.success("Google Sheets dinonaktifkan. Sistem kembali ke data dummy.")
                    st.rerun()
                    
        # Preview data if Google Sheets is loaded
        if st.session_state["google_sheets_data"] is not None:
            st.markdown("#### Preview Data Google Sheets")
            tabs_preview = st.tabs(list(st.session_state["google_sheets_data"].keys()))
            for idx, tab_name in enumerate(st.session_state["google_sheets_data"].keys()):
                with tabs_preview[idx]:
                    df_preview = st.session_state["google_sheets_data"][tab_name]
                    st.markdown(f"Menampilkan data dari tab `{tab_name}` ({len(df_preview)} baris):")
                    preview_df = df_preview.head(10).copy()
                    if "order_status" in preview_df.columns:
                        preview_df["order_status"] = preview_df["order_status"].apply(text_status_emoji)
                    if "status" in preview_df.columns:
                        preview_df["status"] = preview_df["status"].apply(text_status_emoji)
                    if "bottleneck" in preview_df.columns:
                        preview_df["bottleneck"] = preview_df["bottleneck"].apply(text_status_emoji)
                    st.dataframe(preview_df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### 4️⃣ Unduh Template CSV Bawaan")
    st.caption("Gunakan file CSV demo bawaan ini sebagai acuan format pengisian data Anda.")
    
    c_d1, c_d2, c_d3, c_d4 = st.columns(4)
    with c_d1:
        with open(DATA_DIR / "products.csv", "rb") as f:
            st.download_button("📥 Template products.csv", f, "products.csv", "text/csv", use_container_width=True, key="dl_products_setup")
        with open(DATA_DIR / "inventory_products.csv", "rb") as f:
            st.download_button("📥 Template inventory_products.csv", f, "inventory_products.csv", "text/csv", use_container_width=True, key="dl_inv_p_setup")
            
    with c_d2:
        with open(DATA_DIR / "sales.csv", "rb") as f:
            st.download_button("📥 Template sales.csv", f, "sales.csv", "text/csv", use_container_width=True, key="dl_sales_setup")
        with open(DATA_DIR / "inventory_materials.csv", "rb") as f:
            st.download_button("📥 Template inventory_materials.csv", f, "inventory_materials.csv", "text/csv", use_container_width=True, key="dl_inv_m_setup")
            
    with c_d3:
        with open(DATA_DIR / "bom_hpp.csv", "rb") as f:
            st.download_button("📥 Template bom_hpp.csv", f, "bom_hpp.csv", "text/csv", use_container_width=True, key="dl_bom_setup")
        with open(DATA_DIR / "ads.csv", "rb") as f:
            st.download_button("📥 Template ads.csv", f, "ads.csv", "text/csv", use_container_width=True, key="dl_ads_setup")
            
    with c_d4:
        with open(DATA_DIR / "production_plan.csv", "rb") as f:
            st.download_button("📥 Template production_plan.csv", f, "production_plan.csv", "text/csv", use_container_width=True, key="dl_prod_setup")
            
    st.markdown("---")
    st.markdown("### 5️⃣ Catatan Implementasi & Keterbatasan Demo")
    st.markdown("""
    * Demo saat ini menerima upload **sales.csv** secara dinamis ke memory session berjalan atau integrasi ke **Google Sheets** menggunakan API Service Account.
    * Setelah data real siap, modul berikutnya bisa dibuat agar semua file bisa upload atau disinkronkan langsung dengan database ERP Anda.
    """)

elif page == "Data Health Check":
    st.title("Data Health Check 🔍")
    st.caption("Mengecek kualitas data Google Sheets atau dummy agar data siap dipakai.")
    
    # Compute health check values
    errors = []
    warnings = []
    rows_checked = 0

    # 1. Worksheets Check
    expected_keys = ["products", "sales", "inventory_products", "inventory_materials", "bom", "ads", "production_plan"]
    for key in expected_keys:
        if key not in data or data[key] is None or data[key].empty:
            errors.append({
                "Severity": "🔴 Error",
                "Area": "Struktur Berkas",
                "Issue": f"Tab '{key}' tidak ditemukan atau kosong.",
                "Recommendation": f"Pastikan tab '{key}' ada di Google Sheets dan berisi data."
            })
        else:
            rows_checked += len(data[key])

    # Check optional V5A tabs
    optional_keys = ["expenses", "tax_payments", "tax_settings"]
    for key in optional_keys:
        if key not in data or data[key] is None or data[key].empty:
            warnings.append({
                "Severity": "🟡 Warning",
                "Area": "Struktur Berkas (Opsional)",
                "Issue": f"Tab opsional '{key}' tidak ditemukan atau kosong.",
                "Recommendation": f"Buat tab '{key}' di Google Sheets/file lokal untuk mengaktifkan modul Finance & Tax lengkap."
            })
        elif key == "tax_settings" and len(data[key]) == 6 and "orang_pribadi_umkm" in data[key]["value"].values:
            warnings.append({
                "Severity": "🟡 Warning",
                "Area": "Pengaturan Pajak (Opsional)",
                "Issue": "Pengaturan pajak di tab 'tax_settings' menggunakan nilai default.",
                "Recommendation": "Sesuaikan pengaturan entitas dan PKP Anda di tab 'tax_settings'."
            })
            rows_checked += len(data[key])
        else:
            rows_checked += len(data[key])

    # 2. Columns Check
    sales_cols = ["date", "platform", "order_id", "sku", "product", "qty", "price", "discount", "marketplace_fee", "packing_cost", "ad_cost_allocated", "hpp", "gross_revenue", "net_revenue", "net_profit", "net_margin", "order_status"]
    if "sales" in data and not data["sales"].empty:
        sales_df = data["sales"]
        for col in sales_cols:
            if col not in sales_df.columns:
                errors.append({
                    "Severity": "🔴 Error",
                    "Area": "Kolom Penjualan",
                    "Issue": f"Kolom wajib '{col}' tidak ditemukan di tab sales.",
                    "Recommendation": f"Tambahkan kolom '{col}' ke tab sales."
                })

    # 3. Empty values check in sales
    if "sales" in data and not data["sales"].empty:
        sales_df = data["sales"]
        for col in ["date", "sku", "qty", "price", "net_profit"]:
            if col in sales_df.columns:
                empty_count = sales_df[col].isnull().sum() + (sales_df[col] == "").sum()
                if empty_count > 0:
                    errors.append({
                        "Severity": "🔴 Error",
                        "Area": "Konsistensi Data",
                        "Issue": f"Kolom '{col}' memiliki {empty_count} baris kosong/null.",
                        "Recommendation": f"Isi data kosong pada kolom '{col}' di tab sales."
                    })

    # 4. SKU Mismatch
    if "products" in data and not data["products"].empty:
        valid_skus = set(data["products"]["sku"].astype(str).str.strip())
        
        # Check sales
        if "sales" in data and not data["sales"].empty and "sku" in data["sales"].columns:
            mismatched_sales = data["sales"][~data["sales"]["sku"].astype(str).str.strip().isin(valid_skus)]
            if not mismatched_sales.empty:
                mismatched_count = mismatched_sales["sku"].nunique()
                errors.append({
                    "Severity": "🔴 Error",
                    "Area": "Relasi SKU",
                    "Issue": f"Terdapat {mismatched_count} SKU di tab sales yang tidak terdaftar di tab products.",
                    "Recommendation": "Daftarkan SKU baru tersebut ke tab products agar HPP & Margin terhitung benar."
                })
                
        # Check inventory products
        if "inventory_products" in data and not data["inventory_products"].empty and "sku" in data["inventory_products"].columns:
            mismatched_inv = data["inventory_products"][~data["inventory_products"]["sku"].astype(str).str.strip().isin(valid_skus)]
            if not mismatched_inv.empty:
                errors.append({
                    "Severity": "🔴 Error",
                    "Area": "Relasi SKU",
                    "Issue": f"Terdapat {len(mismatched_inv)} SKU di tab inventory_products yang tidak terdaftar di tab products.",
                    "Recommendation": "Pastikan semua SKU di stok produk jadi ada di daftar master produk."
                })
                
        # Check bom
        if "bom" in data and not data["bom"].empty and "sku" in data["bom"].columns:
            mismatched_bom = data["bom"][~data["bom"]["sku"].astype(str).str.strip().isin(valid_skus)]
            if not mismatched_bom.empty:
                errors.append({
                    "Severity": "🔴 Error",
                    "Area": "Relasi SKU",
                    "Issue": f"Terdapat {mismatched_bom['sku'].nunique()} SKU di tab bom yang tidak terdaftar di tab products.",
                    "Recommendation": "Tambahkan formula BOM hanya untuk SKU yang valid di master produk."
                })

    # 5. Anomalies check
    if "sales" in data and not data["sales"].empty:
        sales_df = data["sales"]
        if "qty" in sales_df.columns:
            bad_qty = len(sales_df[sales_df["qty"] <= 0])
            if bad_qty > 0:
                warnings.append({
                    "Severity": "🟡 Warning",
                    "Area": "Nilai Angka",
                    "Issue": f"Terdapat {bad_qty} transaksi dengan Qty <= 0.",
                    "Recommendation": "Periksa apakah transaksi tersebut merupakan order retur atau kesalahan input."
                })
        if "price" in sales_df.columns:
            bad_price = len(sales_df[sales_df["price"] <= 0])
            if bad_price > 0:
                warnings.append({
                    "Severity": "🟡 Warning",
                    "Area": "Nilai Angka",
                    "Issue": f"Terdapat {bad_price} transaksi dengan Harga Jual <= 0.",
                    "Recommendation": "Periksa jika ada produk gratis/gift atau kesalahan input nominal."
                })
        if "net_margin" in sales_df.columns:
            bad_margin = len(sales_df[sales_df["net_margin"] < -0.50])
            if bad_margin > 0:
                warnings.append({
                    "Severity": "🟡 Warning",
                    "Area": "Nilai Angka",
                    "Issue": f"Terdapat {bad_margin} transaksi dengan margin boncos di bawah -50%.",
                    "Recommendation": "Periksa apakah alokasi iklan atau diskon terlalu besar pada order ini."
                })

    # Negative stock
    if "inventory_products" in data and not data["inventory_products"].empty and "stock" in data["inventory_products"].columns:
        neg_p = len(data["inventory_products"][data["inventory_products"]["stock"] < 0])
        if neg_p > 0:
            errors.append({
                "Severity": "🔴 Error",
                "Area": "Nilai Angka",
                "Issue": f"Terdapat {neg_p} SKU produk jadi dengan stok negatif.",
                "Recommendation": "Lakukan stock opname fisik untuk memperbaiki stok negatif."
            })
            
    if "inventory_materials" in data and not data["inventory_materials"].empty and "stock" in data["inventory_materials"].columns:
        neg_m = len(data["inventory_materials"][data["inventory_materials"]["stock"] < 0])
        if neg_m > 0:
            errors.append({
                "Severity": "🔴 Error",
                "Area": "Nilai Angka",
                "Issue": f"Terdapat {neg_m} bahan baku dengan stok negatif.",
                "Recommendation": "Periksa pencatatan mutasi penggunaan bahan baku."
            })

    # ROAS < 0
    if "ads" in data and not data["ads"].empty and "roas" in data["ads"].columns:
        neg_roas = len(data["ads"][data["ads"]["roas"] < 0])
        if neg_roas > 0:
            warnings.append({
                "Severity": "🟡 Warning",
                "Area": "Nilai Angka",
                "Issue": f"Terdapat {neg_roas} campaign iklan dengan ROAS negatif.",
                "Recommendation": "Periksa input pendapatan atau spend iklan agar bernilai positif."
            })

    # V5B: Additional checks for Finance & Tax tabs
    if "expenses" in data and not data["expenses"].empty:
        expenses_df = data["expenses"]
        if "amount" in expenses_df.columns:
            bad_exp_amt = len(expenses_df[expenses_df["amount"] <= 0])
            if bad_exp_amt > 0:
                warnings.append({
                    "Severity": "🟡 Warning",
                    "Area": "Finance & Tax (Expenses)",
                    "Issue": f"Terdapat {bad_exp_amt} pencatatan biaya di tab expenses dengan nominal <= 0.",
                    "Recommendation": "Periksa tab expenses dan pastikan seluruh pengeluaran bernilai positif."
                })
        if "tax_deductible" in expenses_df.columns:
            invalid_deductible = expenses_df[
                ~expenses_df["tax_deductible"].astype(str).str.lower().isin(["true", "false", "1", "0", "yes", "no", "ya", "tidak"]) & 
                ~expenses_df["tax_deductible"].isnull()
            ]
            if not invalid_deductible.empty:
                warnings.append({
                    "Severity": "🟡 Warning",
                    "Area": "Finance & Tax (Expenses)",
                    "Issue": f"Terdapat {len(invalid_deductible)} baris di tab expenses dengan kolom tax_deductible tidak valid (bukan true/false/yes/no/ya/tidak).",
                    "Recommendation": "Gunakan format boolean (TRUE/FALSE atau YA/TIDAK) pada kolom tax_deductible."
                })

    if "tax_payments" in data and not data["tax_payments"].empty:
        payments_df = data["tax_payments"]
        if "amount" in payments_df.columns:
            bad_pay_amt = len(payments_df[payments_df["amount"] < 0])
            if bad_pay_amt > 0:
                errors.append({
                    "Severity": "🔴 Error",
                    "Area": "Finance & Tax (Tax Payments)",
                    "Issue": f"Terdapat {bad_pay_amt} pembayaran pajak di tab tax_payments dengan nominal < 0.",
                    "Recommendation": "Periksa tab tax_payments dan pastikan nilai setoran pajak tidak negatif."
                })

    if "tax_settings" in data and not data["tax_settings"].empty:
        settings_df = data["tax_settings"]
        if "key" in settings_df.columns:
            existing_keys = set(settings_df["key"].astype(str).str.strip().tolist())
            important_keys = ["business_entity", "is_pkp", "use_pph_final_umkm", "pph_final_rate", "annual_omzet_threshold", "ppn_rate", "tax_year"]
            missing_important = [k for k in important_keys if k not in existing_keys]
            if missing_important:
                warnings.append({
                    "Severity": "🟡 Warning",
                    "Area": "Finance & Tax (Tax Settings)",
                    "Issue": f"Pengaturan penting berikut hilang dari tax_settings: {', '.join(missing_important)}.",
                    "Recommendation": "Tambahkan key tersebut ke tab tax_settings agar perhitungan pajak berjalan presisi."
                })

    # Health Score computation
    total_errors = len(errors)
    total_warnings = len(warnings)
    score = 100
    score -= total_errors * 10
    score -= total_warnings * 2
    score = max(0, min(100, score))
    
    # Render KPI cards
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Kesehatan Data", f"{score}/100")
    with col_k2:
        st.metric("Total Error", total_errors)
    with col_k3:
        st.metric("Total Warning", total_warnings)
    with col_k4:
        st.metric("Rows Checked", rows_checked)
        
    st.markdown("---")
    
    st.subheader("Daftar Temuan Masalah & Rekomendasi")
    
    # Issues Table
    issues_list = errors + warnings
    if len(issues_list) == 0:
        st.success("✅ **Data terlihat sehat untuk demo/operasional awal.** Tidak ditemukan error maupun warning.")
    else:
        issues_df = pd.DataFrame(issues_list)
        render_styled_table(issues_df)

elif page == "Finance & Tax":
    st.title("Finance & Tax Readiness 📊")
    st.caption("Laporan keuangan dan simulasi pajak internal untuk membantu persiapan pencatatan usaha dan lampiran SPT.")
    
    # Disclaimer Box
    st.error(
        "⚠️ **Disclaimer:** Estimasi pajak bersifat simulasi internal. Laporan ini bukan dokumen resmi perpajakan "
        "dan tidak dapat digunakan sebagai SPT final yang sah. Validasi final tetap perlu dilakukan dengan konsultan pajak atau DJP."
    )
    
    # Check if optional tax/expenses tables exist or are empty (original loaded data)
    missing_tabs = []
    if "expenses" not in data or data["expenses"].empty:
        missing_tabs.append("expenses")
    if "tax_settings" not in data or data["tax_settings"].empty:
        missing_tabs.append("tax_settings")
    if "tax_payments" not in data or data["tax_payments"].empty:
        missing_tabs.append("tax_payments")
        
    if missing_tabs:
        st.warning(
            f"ℹ️ **Informasi:** Tab opsional berikut belum terisi penuh atau belum dibuat di Google Sheets: **{', '.join(missing_tabs)}**. "
            "Aplikasi menggunakan data default simulasi/kosong agar tidak crash. "
            "Anda dapat membuat tab-tab ini di Google Sheets untuk mengaktifkan sinkronisasi riwayat pengeluaran & setoran pajak."
        )

    # Copy data to avoid mutating original
    data_filtered = data.copy()
    
    from modules.finance_tax import (
        parse_settings, build_profit_loss_report, build_monthly_omzet_summary,
        calculate_tax_estimate, build_tax_readiness_checklist, generate_finance_tax_insights
    )
    
    current_settings = parse_settings(data)
    
    # Filter
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        years_list = sorted(list(data["sales"]["date"].dt.year.dropna().unique()), reverse=True)
        if not years_list:
            years_list = [2026]
        selected_year = st.selectbox("Tahun Pajak", years_list, index=0)
        
    with col_f2:
        months_list = ["Semua Bulan", "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                       "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        selected_month_str = st.selectbox("Bulan (Opsional)", months_list, index=0)
        selected_month = None if selected_month_str == "Semua Bulan" else months_list.index(selected_month_str)
        
    with col_f3:
        entity_opts = ["orang_pribadi_umkm", "badan_umkm", "orang_pribadi_umum", "badan_umum"]
        entity_labels = {
            "orang_pribadi_umkm": "Orang Pribadi (UMKM Final 0.5%)",
            "badan_umkm": "Badan / PT / CV (UMKM Final 0.5%)",
            "orang_pribadi_umum": "Orang Pribadi (Tarif Umum)",
            "badan_umum": "Badan / PT / CV (Tarif Umum 22%)"
        }
        default_entity = current_settings.get("business_entity", "orang_pribadi_umkm")
        if default_entity not in entity_opts:
            default_entity = "orang_pribadi_umkm"
        selected_entity_label = st.selectbox(
            "Jenis Entitas Pajak", 
            [entity_labels[opt] for opt in entity_opts], 
            index=entity_opts.index(default_entity)
        )
        selected_entity = [k for k, v in entity_labels.items() if v == selected_entity_label][0]
        
    with col_f4:
        default_pkp = current_settings.get("is_pkp", False)
        pkp_opts = ["Non-PKP (Batas 4.8M)", "PKP (Wajib PPN)"]
        selected_pkp_str = st.selectbox(
            "Status PKP",
            pkp_opts,
            index=1 if default_pkp else 0
        )
        selected_pkp = selected_pkp_str == "PKP (Wajib PPN)"

    # Overwrite the settings in data_filtered
    use_pph_final = "umkm" in selected_entity
    override_df = pd.DataFrame([
        {"key": "business_entity", "value": selected_entity, "notes": "Overridden by UI"},
        {"key": "is_pkp", "value": "true" if selected_pkp else "false", "notes": "Overridden by UI"},
        {"key": "pph_final_rate", "value": str(current_settings.get("pph_final_rate", 0.005)), "notes": ""},
        {"key": "annual_omzet_threshold", "value": str(current_settings.get("annual_omzet_threshold", 4800000000.0)), "notes": ""},
        {"key": "ppn_rate", "value": str(current_settings.get("ppn_rate", 0.12)), "notes": ""},
        {"key": "use_pph_final_umkm", "value": "true" if use_pph_final else "false", "notes": "Overridden by UI"}
    ])
    data_filtered["tax_settings"] = override_df

    # Calculate reports
    period_type = "yearly" if selected_month is None else "monthly"
    pl_report = build_profit_loss_report(data_filtered, period=period_type, year=selected_year, month=selected_month)
    tax_est = calculate_tax_estimate(data_filtered, selected_year)
    
    # KPI cards
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        render_metric("Omzet Tahunan", rupiah(tax_est["annual_gross"]))
        render_metric("Biaya Operasional", rupiah(pl_report["operating_expenses"]), status="warning" if pl_report["operating_expenses"] > 0 else "good")
    with col_k2:
        render_metric("Profit Sebelum Pajak", rupiah(pl_report["net_profit_before_tax"]), status="good" if pl_report["net_profit_before_tax"] > 0 else "danger")
        render_metric("Estimasi Pajak (PPh)", rupiah(pl_report["estimated_tax"]), status="warning" if pl_report["estimated_tax"] > 0 else "good")
    with col_k3:
        render_metric("Profit Setelah Pajak", rupiah(pl_report["net_profit_after_tax"]), status="good" if pl_report["net_profit_after_tax"] > 0 else "danger")
        
        # Threshold Status
        threshold = current_settings.get("annual_omzet_threshold", 4800000000.0)
        pct_threshold = (tax_est["annual_gross"] / threshold) * 100
        if tax_est["annual_gross"] > threshold:
            render_metric("Status Threshold", "Wajib PKP", f"Melebihi 4.8M ({pct_threshold:.1f}%)", status="danger")
        elif tax_est["annual_gross"] >= threshold * 0.8:
            render_metric("Status Threshold", "Waspada PKP", f"Mendekati 4.8M ({pct_threshold:.1f}%)", status="warning")
        else:
            render_metric("Status Threshold", "Aman", f"{pct_threshold:.1f}% dari limit 4.8M", status="good")
            
    # Laba Rugi & Bulanan Layout
    st.markdown("---")
    col_l1, col_l2 = st.columns([2, 3])
    
    with col_l1:
        st.subheader("Laporan Laba Rugi")
        st.caption(f"Periode: {selected_month_str} {selected_year}" if selected_month else f"Periode: Tahun {selected_year}")
        
        pl_items = [
            ("Penjualan Bruto", pl_report["gross_revenue"]),
            ("Diskon/Retur Penjualan", -pl_report["discount"]),
            ("Penjualan Bersih (Net Revenue)", pl_report["net_revenue"]),
            ("Harga Pokok Penjualan (HPP)", -pl_report["hpp"]),
            ("Laba Kotor (Gross Profit)", pl_report["gross_profit"]),
            ("Biaya Marketplace", -pl_report["marketplace_fee"]),
            ("Biaya Iklan (Marketing)", -pl_report["ad_cost"]),
            ("Biaya Packing", -pl_report["packing_cost"]),
            ("Biaya Operasional Lain (Expenses)", -pl_report["operating_expenses"]),
            ("Laba Bersih Sebelum Pajak (EBT)", pl_report["net_profit_before_tax"]),
            ("Estimasi Pajak", -pl_report["estimated_tax"]),
            ("Laba Bersih Setelah Pajak (EAT)", pl_report["net_profit_after_tax"])
        ]
        pl_rows = [{"Item": item, "Nilai": rupiah(val)} for item, val in pl_items]
        pl_df = pd.DataFrame(pl_rows)
        render_styled_table(pl_df)
        
    with col_l2:
        st.subheader("Omzet Bulanan & Estimasi PPh Final")
        st.caption(f"Akumulasi Peredaran Bruto tahun {selected_year} terhadap threshold Rp 4,8 Miliar")
        
        monthly_df = build_monthly_omzet_summary(data_filtered, selected_year)
        monthly_display = monthly_df.copy()
        
        # Format monthly df
        monthly_display["gross_revenue"] = monthly_display["gross_revenue"].apply(rupiah)
        monthly_display["net_revenue"] = monthly_display["net_revenue"].apply(rupiah)
        monthly_display["estimated_pph_final"] = monthly_display["estimated_pph_final"].apply(rupiah)
        monthly_display["accumulated_gross_revenue"] = monthly_display["accumulated_gross_revenue"].apply(rupiah)
        monthly_display["threshold_status"] = monthly_display["threshold_status"].apply(text_status_emoji)
        
        monthly_display = monthly_display[["month", "gross_revenue", "net_revenue", "order_count", "estimated_pph_final", "accumulated_gross_revenue", "threshold_status"]]
        monthly_display.columns = ["Bulan", "Omzet Bruto", "Net Revenue", "Order", "Est. PPh Final (0.5%)", "Akumulasi Omzet", "Status Threshold"]
        render_styled_table(monthly_display)
        
    st.markdown("---")
    col_t1, col_t2 = st.columns([1, 1])
    
    with col_t1:
        st.subheader("Simulasi Pajak Pertambahan Nilai (PPN)")
        if not selected_pkp:
            st.info(
                f"ℹ️ **Status: Non-PKP.** WP Non-PKP tidak memungut PPN Keluaran. "
                f"Simulasi di bawah ini hanya acuan jika Anda mendaftar PKP dengan tarif PPN {current_settings.get('ppn_rate', 0.12)*100:.0f}%. "
                f"Batas kewajiban PKP adalah jika omzet bruto melebihi Rp 4,8 Miliar setahun."
            )
            st.markdown(f"**PPN Keluaran (Output):** Rp 0")
            st.markdown(f"**PPN Masukan (Input):** Rp 0")
            st.markdown(f"**Estimasi Kurang Bayar:** Rp 0")
        else:
            st.success(
                f"✅ **Status: PKP Aktif.** Simulasi pemungutan PPN Keluaran {current_settings.get('ppn_rate', 0.12)*100:.0f}% "
                f"dan pengkreditan PPN Masukan dari expenses yang deductible."
            )
            st.markdown(f"**PPN Keluaran (Omzet Bruto * {current_settings.get('ppn_rate', 0.12)*100:.0f}%):** {rupiah(tax_est['ppn_keluaran'])}")
            st.markdown(f"**PPN Masukan (Expenses Deductible * {current_settings.get('ppn_rate', 0.12)*100:.0f}%):** {rupiah(tax_est['ppn_masukan'])}")
            st.markdown(f"**Estimasi PPN Kurang/(Lebih) Bayar:** **{rupiah(tax_est['ppn_kurang_bayar'])}**")
            st.caption(f"*Catatan: {tax_est['ppn_notes']}")
            
        st.subheader("Tax Readiness Checklist")
        st.caption("Status kelengkapan data administrasi untuk pelaporan SPT Tahunan")
        
        checklist = build_tax_readiness_checklist(data_filtered, selected_year)
        chk_rows = []
        for item in checklist:
            chk_rows.append({
                "Langkah Kesiapan": item["item"],
                "Status": text_status_emoji(item["status"]),
                "Keterangan": item["description"]
            })
        chk_df = pd.DataFrame(chk_rows)
        render_styled_table(chk_df)
        
    with col_t2:
        st.subheader("Insight Pajak & Keuangan")
        st.caption("Rekomendasi otomatis berbasis data untuk persiapan perpajakan")
        
        insights = generate_finance_tax_insights(data_filtered, selected_year)
        for insight in insights:
            st.markdown(f"<div class='ai-box'>{insight}</div>", unsafe_allow_html=True)
            
        # Download Pack
        st.subheader("Unduh Laporan (Export)")
        st.caption("Ekspor laporan keuangan & tax readiness dalam berbagai format")
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            # PDF Download Button
            try:
                from modules.pdf_report import generate_finance_tax_pdf_report
                pdf_bytes = generate_finance_tax_pdf_report(data_filtered, selected_year)
                st.download_button(
                    label="📄 Download Laporan PDF",
                    data=pdf_bytes,
                    file_name=f"laporan_keuangan_pajak_parfum_{selected_year}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Gagal generate PDF: {e}")
                
            # CSV Download Button
            csv_data = monthly_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Download CSV Bulanan",
                data=csv_data,
                file_name=f"ringkasan_bulanan_pajak_parfum_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_e2:
            # TXT Summary Download Button
            txt_lines = [
                "============================================================",
                "LAPORAN KEUANGAN & TAX READINESS REPORT - SIMULASI INTERNAL",
                "============================================================",
                f"Tahun Analisis: {selected_year}",
                f"Jenis Entitas: {selected_entity}",
                f"Status PKP: {'Ya (PKP)' if selected_pkp else 'Tidak (Non-PKP)'}",
                "------------------------------------------------------------",
                "RINGKASAN METRIK KEUANGAN:",
                f"- Omzet Bruto Tahunan: {rupiah(pl_report['gross_revenue'])}",
                f"- Penjualan Bersih (Net): {rupiah(pl_report['net_revenue'])}",
                f"- HPP Tahunan: {rupiah(pl_report['hpp'])}",
                f"- Laba Kotor: {rupiah(pl_report['gross_profit'])}",
                f"- Biaya Operasional (Expenses): {rupiah(pl_report['operating_expenses'])}",
                f"- Laba Bersih Sebelum Pajak (EBT): {rupiah(pl_report['net_profit_before_tax'])}",
                f"- Estimasi Pajak: {rupiah(pl_report['estimated_tax'])}",
                f"- Laba Bersih Setelah Pajak (EAT): {rupiah(pl_report['net_profit_after_tax'])}",
                "------------------------------------------------------------",
                "PPN READINESS STATUS:",
                f"Status: {tax_est['ppn_status']}",
                f"PPN Keluaran: {rupiah(tax_est['ppn_keluaran'])}",
                f"PPN Masukan: {rupiah(tax_est['ppn_masukan'])}",
                f"PPN Kurang Bayar: {rupiah(tax_est['ppn_kurang_bayar'])}",
                "------------------------------------------------------------",
                "DOKUMEN SPT YANG PERLU DISIAPKAN:",
                "- Rekapitulasi peredaran bruto bulanan.",
                "- Bukti penyetoran PPh Final UMKM bulanan (SSP/BPN).",
                "- Daftar aset & kewajiban akhir tahun untuk Form SPT 1770 Lampiran IV.",
                "------------------------------------------------------------",
                "DISCLAIMER:",
                "Estimasi pajak bersifat simulasi internal. Validasi final tetap perlu dilakukan dengan konsultan pajak atau DJP."
            ]
            txt_content = "\n".join(txt_lines)
            st.download_button(
                label="📝 Download Ringkasan TXT",
                data=txt_content.encode('utf-8'),
                file_name=f"ringkasan_keuangan_pajak_parfum_{selected_year}.txt",
                mime="text/plain",
                use_container_width=True
            )

    # V5B: SPT Attachment Pack Section
    st.markdown("---")
    st.subheader("💼 SPT Attachment Pack")
    st.caption("Dokumen lampiran pendukung internal untuk kelengkapan administrasi perpajakan.")
    
    # Disclaimer
    st.info(
        "📝 **Disclaimer:** Estimasi pajak bersifat simulasi internal. Validasi final tetap perlu dilakukan dengan konsultan pajak atau DJP. "
        "Seluruh dokumen di bawah ini merupakan lampiran pendukung internal / rekap pendukung simulasi."
    )
    
    # Document checklist
    missing_docs = []
    for item in checklist:
        if item["status"] in ["Warning", "Missing"]:
            missing_docs.append(f"• **{item['item']}**: {item['description']}")
    # Add general ones
    missing_docs.append("• **Formulir SPT Tahunan 1770 / 1771** (sesuai status entitas bisnis).")
    missing_docs.append("• **Daftar Harta & Utang Akhir Tahun** (sebagai lampiran wajib SPT Orang Pribadi / Badan).")
    missing_docs.append("• **Rekapitulasi Omzet Bulanan** yang telah divalidasi ke mutasi rekening koran bank.")
    missing_docs.append("• **Bukti Penerimaan Negara (BPN)** untuk pembayaran PPh Final 0.5% setiap masa pajak.")
    
    spt_tabs = st.tabs(["Ringkasan Laporan", "Rincian Omzet Bulanan", "Rekap Biaya Operasional", "Setoran Pajak", "Unduh Dokumen"])
    
    with spt_tabs[0]:
        st.markdown("##### Ringkasan Laporan Laba Rugi & SPT")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown(f"**Jenis Entitas:** {selected_entity_label}")
            st.markdown(f"**Status PKP:** {'Ya (PKP)' if selected_pkp else 'Tidak (Non-PKP)'}")
            st.markdown(f"**Peredaran Bruto (Omzet Tahunan):** {rupiah(pl_report['gross_revenue'])}")
            st.markdown(f"**Penjualan Bersih (Net Revenue):** {rupiah(pl_report['net_revenue'])}")
        with col_s2:
            st.markdown(f"**Laba Kotor (Gross Profit):** {rupiah(pl_report['gross_profit'])}")
            st.markdown(f"**Laba Bersih Sebelum Pajak (EBT):** {rupiah(pl_report['net_profit_before_tax'])}")
            st.markdown(f"**Estimasi PPh Final UMKM:** {rupiah(pl_report['estimated_tax'])}")
            st.markdown(f"**Laba Bersih Setelah Pajak (EAT):** {rupiah(pl_report['net_profit_after_tax'])}")
            
    with spt_tabs[1]:
        st.markdown("##### Rincian Peredaran Bruto Bulanan")
        st.dataframe(monthly_display, hide_index=True, use_container_width=True)
        
    with spt_tabs[2]:
        st.markdown("##### Rekapitulasi Biaya Operasional (Expenses)")
        expenses = data_filtered.get("expenses")
        if expenses is not None and not expenses.empty:
            expenses_year = expenses[pd.to_datetime(expenses["date"], errors="coerce").dt.year == selected_year]
        else:
            expenses_year = pd.DataFrame()
            
        if not expenses_year.empty:
            exp_grp = expenses_year.groupby(["category", "tax_deductible"]).agg({"amount": "sum", "description": "count"}).reset_index()
            exp_grp.columns = ["Kategori", "Tax Deductible", "Total Biaya", "Jumlah Transaksi"]
            exp_grp["Total Biaya"] = exp_grp["Total Biaya"].apply(rupiah)
            st.dataframe(exp_grp, hide_index=True, use_container_width=True)
            
            with st.expander("Lihat Rincian Transaksi Biaya"):
                exp_detail = expenses_year.copy()
                exp_detail["date"] = exp_detail["date"].dt.strftime("%Y-%m-%d")
                exp_detail["amount"] = exp_detail["amount"].apply(rupiah)
                st.dataframe(exp_detail, hide_index=True, use_container_width=True)
        else:
            st.info("Tidak ada data pengeluaran operasional.")
            
    with spt_tabs[3]:
        st.markdown("##### Riwayat Pembayaran Pajak (Tax Payments)")
        tax_payments = data_filtered.get("tax_payments")
        if tax_payments is not None and not tax_payments.empty:
            payments_year = tax_payments[pd.to_datetime(tax_payments["date"], errors="coerce").dt.year == selected_year]
        else:
            payments_year = pd.DataFrame()
            
        if not payments_year.empty:
            pay_disp = payments_year.copy()
            pay_disp["date"] = pay_disp["date"].dt.strftime("%Y-%m-%d")
            pay_disp["amount"] = pay_disp["amount"].apply(rupiah)
            pay_disp.columns = ["Tanggal", "Jenis Pajak", "Masa/Period", "Jumlah Setoran", "NTPN/Referensi", "Catatan"]
            st.dataframe(pay_disp, hide_index=True, use_container_width=True)
        else:
            st.warning("Belum ada catatan setoran pajak yang diinput.")
            
    with spt_tabs[4]:
        st.markdown("##### Unduh Paket Lampiran Pendukung SPT")
        st.caption("Pilih format dokumen pendukung untuk diunduh secara lokal:")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            use_pph_final_str = "Ya (PPh Final UMKM 0.5%)" if use_pph_final else "Tidak (Tarif Umum)"
            spt_txt_lines = [
                "============================================================",
                "PAKET LAMPIRAN PENDUKUNG SPT USAHA (SIMULASI INTERNAL)",
                "============================================================",
                f"Tahun Pajak: {selected_year}",
                f"Jenis Entitas: {selected_entity_label}",
                f"Status PKP: {'Ya (PKP)' if selected_pkp else 'Tidak (Non-PKP)'}",
                f"Menggunakan PPh Final UMKM: {use_pph_final_str}",
                "------------------------------------------------------------",
                "A. REKAPITULASI LABA RUGI TAHUNAN:",
                f"- Peredaran Bruto (Gross Revenue): {rupiah(pl_report['gross_revenue'])}",
                f"- Diskon/Potongan Penjualan: - {rupiah(pl_report['discount'])}",
                f"- Penjualan Bersih (Net Revenue): {rupiah(pl_report['net_revenue'])}",
                f"- Harga Pokok Penjualan (HPP): - {rupiah(pl_report['hpp'])}",
                f"- Laba Kotor (Gross Profit): {rupiah(pl_report['gross_profit'])}",
                f"- Biaya Marketplace: - {rupiah(pl_report['marketplace_fee'])}",
                f"- Biaya Iklan (Marketing): - {rupiah(pl_report['ad_cost'])}",
                f"- Biaya Packing: - {rupiah(pl_report['packing_cost'])}",
                f"- Biaya Operasional Lain (Expenses): - {rupiah(pl_report['operating_expenses'])}",
                f"- Laba Bersih Sebelum Pajak (EBT): {rupiah(pl_report['net_profit_before_tax'])}",
                f"- Estimasi PPh Terutang: - {rupiah(pl_report['estimated_tax'])}",
                f"- Laba Bersih Setelah Pajak (EAT): {rupiah(pl_report['net_profit_after_tax'])}",
                "------------------------------------------------------------",
                "B. CHECKLIST DOKUMEN KESIAPAN PAJAK:",
            ]
            for item in checklist:
                spt_txt_lines.append(f"- [{item['status']}] {item['item']}: {item['description']}")
            spt_txt_lines.append("------------------------------------------------------------")
            spt_txt_lines.append("C. CATATAN DOKUMEN YANG HARUS DISIAPKAN:")
            for doc_item in missing_docs:
                spt_txt_lines.append(doc_item.replace("• ", "").replace("**", ""))
            spt_txt_lines.append("------------------------------------------------------------")
            spt_txt_lines.append("DISCLAIMER:")
            spt_txt_lines.append("Estimasi pajak bersifat simulasi internal. Validasi final tetap perlu dilakukan dengan konsultan pajak atau DJP.")
            
            spt_txt_content = "\n".join(spt_txt_lines)
            st.download_button(
                label="📄 Download SPT Summary TXT",
                data=spt_txt_content.encode('utf-8'),
                file_name=f"spt_summary_{selected_year}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            spt_monthly_csv = monthly_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Download Monthly Omzet CSV",
                data=spt_monthly_csv,
                file_name=f"monthly_omzet_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            spt_expenses_csv = (
                expenses_year.to_csv(index=False).encode('utf-8') 
                if not expenses_year.empty 
                else pd.DataFrame(columns=["date", "category", "description", "amount", "payment_method", "vendor", "tax_deductible", "notes"]).to_csv(index=False).encode('utf-8')
            )
            st.download_button(
                label="🛍️ Download Expenses Recap CSV",
                data=spt_expenses_csv,
                file_name=f"expenses_recap_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_d2:
            spt_payments_csv = (
                payments_year.to_csv(index=False).encode('utf-8')
                if not payments_year.empty
                else pd.DataFrame(columns=["date", "tax_type", "period", "amount", "payment_ref", "notes"]).to_csv(index=False).encode('utf-8')
            )
            st.download_button(
                label="💳 Download Tax Payments CSV",
                data=spt_payments_csv,
                file_name=f"tax_payments_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            try:
                from modules.pdf_report import generate_spt_attachment_pack_pdf
                spt_pdf_bytes = generate_spt_attachment_pack_pdf(data_filtered, selected_year)
                st.download_button(
                    label="📕 Download SPT Attachment PDF",
                    data=spt_pdf_bytes,
                    file_name=f"spt_attachment_pack_{selected_year}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Gagal generate SPT Attachment PDF: {e}")

elif page == "Data Dummy":
    st.title("Data Dummy 📁")
    st.caption("File-file data dummy bawaan sistem. Data ini dapat dijadikan sebagai template pengisian data real bisnis Anda.")
    
    st.info("ℹ️ Seluruh tabel di bawah dapat diunduh untuk acuan pengisian data real Anda.")
    
    tabs = st.tabs(["Produk", "Penjualan (200 Baris)", "Stok Produk", "Stok Bahan", "HPP/BOM", "Iklan", "Rencana Produksi"])
    
    with tabs[0]: 
        st.markdown("#### Master Produk (`products.csv`)")
        p_df = data["products"].copy()
        p_df["price"] = p_df["price"].apply(rupiah)
        p_df["hpp"] = p_df["hpp"].apply(rupiah)
        p_df["target_margin"] = p_df["target_margin"].apply(pct)
        p_df.columns = ["SKU", "Produk", "Ukuran", "Kategori", "Harga Jual", "HPP", "Target Margin"]
        st.dataframe(p_df, hide_index=True, use_container_width=True)
        
    with tabs[1]: 
        st.markdown("#### Data Penjualan (`sales.csv`)")
        st.markdown("ℹ️ *Menampilkan 200 transaksi terakhir. Format ini wajib diikuti jika Anda ingin mengunggah file data penjualan Anda sendiri.*")
        sales_show = data["sales"].tail(200).copy()
        sales_show["date"] = sales_show["date"].dt.strftime("%Y-%m-%d")
        sales_show = as_rp_df(sales_show, ["price", "discount", "marketplace_fee", "packing_cost", "ad_cost_allocated", "hpp", "gross_revenue", "net_revenue", "net_profit"])
        sales_show["net_margin"] = sales_show["net_margin"].apply(pct)
        sales_show["order_status"] = sales_show["order_status"].apply(text_status_emoji)
        sales_show.columns = ["Tanggal", "Platform", "ID Order", "SKU", "Produk", "Qty", "Harga", "Diskon", "Biaya Marketplace", "Biaya Packing", "Biaya Iklan", "HPP", "Gross Revenue", "Net Revenue", "Net Profit", "Net Margin", "Status Order"]
        st.dataframe(sales_show, hide_index=True, use_container_width=True)
        
    with tabs[2]: 
        st.markdown("#### Stok Produk Jadi (`inventory_products.csv`)")
        ip_df = inventory_product_status(data["inventory_products"])[["sku", "product", "stock", "min_stock", "avg_daily_sold", "estimasi_hari_habis", "status"]].copy()
        ip_df["status"] = ip_df["status"].apply(text_status_emoji)
        ip_df.columns = ["SKU", "Produk", "Stok", "Min Stok", "Rata-rata Terjual/Hari", "Estimasi Habis (Hari)", "Status Stok"]
        st.dataframe(ip_df, hide_index=True, use_container_width=True)
        
    with tabs[3]: 
        st.markdown("#### Stok Bahan Baku (`inventory_materials.csv`)")
        im_df = inventory_material_status(data["inventory_materials"])[["material", "unit", "stock", "min_stock", "unit_cost", "status"]].copy()
        im_df["unit_cost"] = im_df["unit_cost"].apply(rupiah)
        im_df["status"] = im_df["status"].apply(text_status_emoji)
        im_df.columns = ["Bahan Baku", "Satuan", "Stok", "Min Stok", "Biaya per Unit", "Status"]
        st.dataframe(im_df, hide_index=True, use_container_width=True)
        
    with tabs[4]: 
        st.markdown("#### Detail Formula & HPP / BOM (`bom_hpp.csv`)")
        bom_df = data["bom"].copy()
        bom_df["component_cost"] = bom_df["component_cost"].apply(rupiah)
        bom_df.columns = ["SKU", "Komponen", "Satuan", "Kebutuhan Penggunaan", "Biaya Komponen"]
        st.dataframe(bom_df, hide_index=True, use_container_width=True)
        
    with tabs[5]: 
        st.markdown("#### Performa Iklan (`ads.csv`)")
        ads_df = data["ads"].copy()
        ads_df["spend"] = ads_df["spend"].apply(rupiah)
        ads_df["revenue"] = ads_df["revenue"].apply(rupiah)
        ads_df["roas"] = ads_df["roas"].apply(lambda r: f"{r:.2f}x")
        ads_df["status"] = ads_df["status"].apply(text_status_emoji)
        ads_df.columns = ["Platform", "Campaign", "Pengeluaran (Spend)", "Pendapatan (Revenue)", "Total Order", "ROAS", "Status Performa"]
        st.dataframe(ads_df, hide_index=True, use_container_width=True)
        
    with tabs[6]: 
        st.markdown("#### Rencana Produksi (`production_plan.csv`)")
        pp_df = data["production_plan"].copy()
        pp_df["bottleneck"] = pp_df["bottleneck"].apply(text_status_emoji)
        pp_df.columns = ["SKU", "Produk", "Permintaan 7 Hari", "Stok Saat Ini", "Rekomendasi Produksi", "Bottleneck"]
        st.dataframe(pp_df, hide_index=True, use_container_width=True)
