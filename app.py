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

# Load data and override if uploaded
data = load_data()
if st.session_state["uploaded_sales"] is not None:
    data["sales"] = st.session_state["uploaded_sales"]

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
    
    page = st.radio(
        "Navigasi",
        [
            "Dashboard Overview",
            "Stok, HPP & Produksi",
            "Chatbot AI Bisnis",
            "Laporan Harian",
            "Setup Data",
            "Data Dummy"
        ],
        label_visibility="collapsed"
    )
    st.markdown("---")
    
    # Data source status indicator in sidebar
    if st.session_state["uploaded_sales"] is not None:
        st.sidebar.markdown(f"**Data Source:**<br/>{status_badge('Uploaded sales.csv')}", unsafe_allow_html=True)
        st.sidebar.markdown("<br/>", unsafe_allow_html=True)
        if st.sidebar.button("Reset ke Data Dummy", use_container_width=True):
            st.session_state["uploaded_sales"] = None
            reset_pdf_states()
            st.rerun()
    else:
        st.sidebar.markdown(f"**Data Source:**<br/>{status_badge('Data Dummy')}", unsafe_allow_html=True)
        
    st.markdown("---")
    st.caption("Demo V2 • Data dummy / uploaded CSV")

# Routing Pages
if page == "Dashboard Overview":
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
    st.markdown("### 3️⃣ Unduh Template CSV Bawaan")
    st.caption("Gunakan file CSV demo bawaan ini sebagai acuan format pengisian data Anda.")
    
    c_d1, c_d2, c_d3, c_d4 = st.columns(4)
    with c_d1:
        with open(DATA_DIR / "products.csv", "rb") as f:
            st.download_button("📥 Template products.csv", f, "products.csv", "text/csv", use_container_width=True)
        with open(DATA_DIR / "inventory_products.csv", "rb") as f:
            st.download_button("📥 Template inventory_products.csv", f, "inventory_products.csv", "text/csv", use_container_width=True)
            
    with c_d2:
        with open(DATA_DIR / "sales.csv", "rb") as f:
            st.download_button("📥 Template sales.csv", f, "sales.csv", "text/csv", use_container_width=True)
        with open(DATA_DIR / "inventory_materials.csv", "rb") as f:
            st.download_button("📥 Template inventory_materials.csv", f, "inventory_materials.csv", "text/csv", use_container_width=True)
            
    with c_d3:
        with open(DATA_DIR / "bom_hpp.csv", "rb") as f:
            st.download_button("📥 Template bom_hpp.csv", f, "bom_hpp.csv", "text/csv", use_container_width=True)
        with open(DATA_DIR / "ads.csv", "rb") as f:
            st.download_button("📥 Template ads.csv", f, "ads.csv", "text/csv", use_container_width=True)
            
    with c_d4:
        with open(DATA_DIR / "production_plan.csv", "rb") as f:
            st.download_button("📥 Template production_plan.csv", f, "production_plan.csv", "text/csv", use_container_width=True)
            
    st.markdown("---")
    st.markdown("### 4️⃣ Catatan Implementasi & Keterbatasan Demo")
    st.markdown("""
    * Demo saat ini menerima upload **sales.csv** secara dinamis ke memory session berjalan.
    * Data master lainnya seperti stok (`inventory_products.csv`, `inventory_materials.csv`), iklan (`ads.csv`), HPP/BOM (`bom_hpp.csv`), dan rencana produksi (`production_plan.csv`) masih menggunakan data dummy bawaan.
    * Pada tahap implementasi ril, sistem dapat dikembangkan agar mendukung pengunggahan seluruh file master di atas, atau langsung dihubungkan dengan API database POS, ERP, atau dashboard marketplace Anda.
    """)

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
