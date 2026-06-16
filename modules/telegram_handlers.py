import os
import io
import toml
import json
import asyncio
import zoneinfo
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# Imports from calculations and loader
from modules.calculations import (
    load_data, rupiah, pct, overview_metrics, top_products,
    inventory_product_status, inventory_material_status, suggested_purchase_value
)
from modules.sheets_loader import (
    load_google_sheets_data, validate_sheet_tabs, normalize_google_sheet_data, get_sheet_id_from_url
)
from modules.pdf_report import generate_daily_pdf_report, generate_finance_tax_pdf_report
from modules.finance_tax import (
    build_profit_loss_report, calculate_tax_estimate, build_tax_readiness_checklist
)

SETTINGS_FILE = "runtime_bot_settings.json"

def load_settings():
    """Load scheduler settings from local JSON file."""
    default_settings = {
        "daily_enabled": False,
        "daily_time": "08:00",
        "closing_enabled": False,
        "closing_time": "17:00",
        "target_chats": [],
        "last_daily_run": "",
        "last_closing_run": ""
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return {**default_settings, **json.load(f)}
        except Exception as e:
            print(f"Error loading settings: {e}")
    return default_settings

def save_settings(settings):
    """Save scheduler settings to local JSON file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_bot_data():
    """Load Google Sheets data, fallback to dummy CSV if configuration is missing or fails."""
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            secrets = toml.load(secrets_path)
            sheet_id = secrets.get("GOOGLE_SHEET_ID")
            creds_info = secrets.get("google_service_account")
            if sheet_id and creds_info:
                actual_id = get_sheet_id_from_url(sheet_id)
                raw_data = load_google_sheets_data(actual_id, dict(creds_info))
                is_valid, missing = validate_sheet_tabs(raw_data)
                if is_valid:
                    return normalize_google_sheet_data(raw_data)
                else:
                    print(f"Warning: Google Sheets missing tabs: {missing}. Falling back to dummy CSV.")
            else:
                print("Warning: GOOGLE_SHEET_ID or google_service_account missing in secrets.toml. Falling back to dummy CSV.")
        except Exception as e:
            print(f"Warning: Failed to load Google Sheets ({e}). Falling back to dummy CSV.")
    else:
        print("Warning: .streamlit/secrets.toml not found. Falling back to dummy CSV.")
        
    return load_data()

def is_allowed_user(chat_id: int) -> bool:
    """Check if the given chat_id is whitelisted in ALLOWED_CHAT_IDS."""
    allowed_ids_str = os.getenv("ALLOWED_CHAT_IDS", "")
    if not allowed_ids_str.strip():
        return True
    try:
        allowed_ids = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
        return chat_id in allowed_ids
    except Exception as e:
        print(f"Error parsing ALLOWED_CHAT_IDS: {e}")
        return True

def check_permission(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat_id = update.effective_chat.id
        if not is_allowed_user(chat_id):
            print(f"Blocked unauthorized access from Chat ID: {chat_id}")
            await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def get_top_3_actions(data, m, prod_kritis_count, bahan_kritis_count):
    """Generate 3 urgent actions for summary command."""
    actions = []
    pp = data["production_plan"]
    need_prod = pp[pp["recommended_production"] > 0]
    if not need_prod.empty:
        top_prod = need_prod.sort_values("recommended_production", ascending=False).iloc[0]
        actions.append(f"Produksi <b>{top_prod['product']}</b> ({int(top_prod['recommended_production'])} pcs).")
    else:
        actions.append("Stok produk jadi aman.")
        
    need_m, suggested_cost = suggested_purchase_value(data["inventory_materials"])
    if not need_m.empty:
        mats_list = ", ".join(need_m.head(2)["material"].tolist())
        actions.append(f"Beli bahan kritis: <b>{mats_list}</b>.")
    else:
        actions.append("Stok bahan baku cukup.")
        
    ads_df = data["ads"]
    critical_ads = ads_df[ads_df["status"].isin(["Waspada", "Boncos"])]
    if not critical_ads.empty:
        ads_list = ", ".join(critical_ads.head(2)["campaign"].tolist())
        actions.append(f"Evaluasi iklan: <b>{ads_list}</b>.")
    else:
        actions.append("Kampanye iklan stabil.")
        
    return actions

def check_business_alerts(data):
    """Check operating anomalies and return a list of warning alert strings."""
    sales = data["sales"]
    m = overview_metrics(sales)
    margin_val = m["margin"]
    
    invp = inventory_product_status(data["inventory_products"])
    stock_critical = len(invp[invp["status"] == "Kritis"])
    
    invm = inventory_material_status(data["inventory_materials"])
    materials_critical = len(invm[invm["status"] == "Kritis"])
    
    ads_df = data["ads"]
    critical_ads = len(ads_df[ads_df["status"].isin(["Waspada", "Boncos"])])
    
    # Simple error count logic for Data Health Check
    errors_count = 0
    expected_keys = ["products", "sales", "inventory_products", "inventory_materials", "bom", "ads", "production_plan"]
    for key in expected_keys:
        if key not in data or data[key] is None or data[key].empty:
            errors_count += 1
            
    sales_cols = ["date", "platform", "order_id", "sku", "product", "qty", "price", "discount", "marketplace_fee", "packing_cost", "ad_cost_allocated", "hpp", "gross_revenue", "net_revenue", "net_profit", "net_margin", "order_status"]
    if "sales" in data and not data["sales"].empty:
        for col in sales_cols:
            if col not in data["sales"].columns:
                errors_count += 1
        for col in ["date", "sku", "qty", "price", "net_profit"]:
            if col in data["sales"].columns:
                errors_count += (data["sales"][col].isnull().sum() + (data["sales"][col] == "").sum())
                
    alert_points = []
    if stock_critical > 0:
        alert_points.append(f"* {stock_critical} SKU stok kritis")
    if materials_critical > 0:
        alert_points.append(f"* {materials_critical} bahan baku kritis")
    if critical_ads > 0:
        alert_points.append(f"* {critical_ads} campaign iklan boncos")
    if margin_val < 0.25:
        alert_points.append(f"* Margin bersih di bawah target ({pct(margin_val)})")
    if errors_count > 0:
        alert_points.append(f"* {errors_count} error pada Data Health Check")
        
    return alert_points

async def send_daily_to_chat(bot, chat_id):
    """Generate daily report and PDF, and send to the specified chat_id."""
    data = load_bot_data()
    sales = data["sales"]
    m = overview_metrics(sales)
    margin_val = m["margin"]
    
    invp = inventory_product_status(data["inventory_products"])
    stock_critical = len(invp[invp["status"] == "Kritis"])
    
    invm = inventory_material_status(data["inventory_materials"])
    materials_critical = len(invm[invm["status"] == "Kritis"])
    
    if margin_val < 0.15 or stock_critical > 5 or materials_critical > 12:
        status_bisnis = "Kritis"
        status_emoji = "🔴"
    elif margin_val >= 0.25 and stock_critical <= 3 and materials_critical <= 10:
        status_bisnis = "Sehat"
        status_emoji = "🟢"
    else:
        status_bisnis = "Waspada"
        status_emoji = "🟡"
        
    actions = get_top_3_actions(data, m, stock_critical, materials_critical)
    actions_str = "\n".join(f"{idx+1}. {act}" for idx, act in enumerate(actions))

    text = (
        f"🔔 <b>[SCHEDULED] Laporan Harian Bisnis</b>\n"
        f"📅 Tanggal: {m['latest_date'].date()}\n\n"
        f"🏥 <b>Status Bisnis:</b> {status_emoji} <b>{status_bisnis.upper()}</b>\n\n"
        f"💵 <b>Omzet Hari Ini:</b> {rupiah(m['gross'])}\n"
        f"📈 <b>Profit Bersih:</b> {rupiah(m['profit'])}\n"
        f"💰 <b>Margin Bersih:</b> {pct(m['margin'])}\n"
        f"📦 <b>Jumlah Order:</b> {m['orders']}\n"
        f"📣 <b>Biaya Iklan:</b> {rupiah(m['ad_spend'])}\n\n"
        f"🎯 <b>3 Action Plan Hari Ini:</b>\n{actions_str}"
    )
    await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    
    # Send PDF Report
    pdf_bytes = generate_daily_pdf_report(data)
    await bot.send_document(
        chat_id=chat_id,
        document=io.BytesIO(pdf_bytes),
        filename="laporan_harian_bisnis_parfum.pdf",
        caption=f"📄 PDF Laporan Harian - {m['latest_date'].strftime('%Y-%m-%d')}"
    )

async def send_closing_to_chat(bot, chat_id):
    """Generate and send closing report to the specified chat_id."""
    data = load_bot_data()
    sales = data["sales"]
    m = overview_metrics(sales)
    
    invp = inventory_product_status(data["inventory_products"])
    stock_critical = len(invp[invp["status"] == "Kritis"])
    
    invm = inventory_material_status(data["inventory_materials"])
    materials_critical = len(invm[invm["status"] == "Kritis"])
    
    top = top_products(sales, latest_only=True).head(3)
    top_str = ""
    if top.empty:
        top_str = "- Tidak ada data penjualan hari ini."
    else:
        for row in top.itertuples(index=False):
            top_str += f"- {row.product} ({int(row.terjual)} pcs | Omzet: {rupiah(row.omzet)})\n"
            
    # Action plans
    pp = data["production_plan"]
    need_prod = pp[pp["recommended_production"] > 0]
    need_m, suggested_cost = suggested_purchase_value(data["inventory_materials"])
    actions_besok = []
    if not need_prod.empty:
        top_prod = need_prod.sort_values("recommended_production", ascending=False).iloc[0]
        actions_besok.append(f"Produksi <b>{top_prod['product']}</b> sebanyak {int(top_prod['recommended_production'])} pcs.")
    else:
        actions_besok.append("Jaga stok produk tetap aman.")
        
    if not need_m.empty:
        mats_list = ", ".join(need_m.head(2)["material"].tolist())
        actions_besok.append(f"Belanja bahan kritis: <b>{mats_list}</b>.")
    else:
        actions_besok.append("Pantau bahan baku.")
        
    actions_str = "\n".join(f"{idx+1}. {act}" for idx, act in enumerate(actions_besok))

    text = (
        f"🌆 <b>[CLOSING] Laporan Sore Hari</b>\n"
        f"📅 Tanggal: {m['latest_date'].date()}\n\n"
        f"💵 <b>Omzet Hari Ini:</b> {rupiah(m['gross'])}\n"
        f"📈 <b>Profit Bersih:</b> {rupiah(m['profit'])}\n"
        f"📦 <b>Total Order:</b> {m['orders']}\n"
        f"💰 <b>Margin Bersih:</b> {pct(m['margin'])}\n\n"
        f"🏆 <b>Top Produk Hari Ini:</b>\n{top_str}\n"
        f"⚠️ <b>Kondisi Kritis:</b>\n"
        f"- Produk Stok Kritis: {stock_critical} SKU\n"
        f"- Bahan Baku Kritis: {materials_critical} item\n\n"
        f"📝 <b>Action Plan Besok Pagi:</b>\n{actions_str}"
    )
    await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

async def schedule_loop(application):
    """Background task running loop to check schedules and dispatch daily/closing messages."""
    print("Background scheduler loop started...")
    while True:
        try:
            settings = load_settings()
            if not settings["daily_enabled"] and not settings["closing_enabled"]:
                await asyncio.sleep(20)
                continue
                
            tz = zoneinfo.ZoneInfo("Asia/Jakarta")
            now = datetime.now(tz)
            current_time_str = now.strftime("%H:%M")
            current_date_str = now.strftime("%Y-%m-%d")
            
            allowed_ids_str = os.getenv("ALLOWED_CHAT_IDS", "")
            if allowed_ids_str.strip():
                targets = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
            else:
                targets = settings["target_chats"]
                
            if targets:
                # 1. Daily Report Check
                if settings["daily_enabled"] and current_time_str == settings["daily_time"] and settings["last_daily_run"] != current_date_str:
                    print(f"Scheduler: Triggering daily report at {current_time_str} to targets {targets}")
                    for chat_id in targets:
                        await send_daily_to_chat(application.bot, chat_id)
                    settings["last_daily_run"] = current_date_str
                    save_settings(settings)
                    
                # 2. Closing Report Check
                if settings["closing_enabled"] and current_time_str == settings["closing_time"] and settings["last_closing_run"] != current_date_str:
                    print(f"Scheduler: Triggering closing report at {current_time_str} to targets {targets}")
                    for chat_id in targets:
                        await send_closing_to_chat(application.bot, chat_id)
                    settings["last_closing_run"] = current_date_str
                    save_settings(settings)
                    
        except Exception as e:
            print(f"Error in scheduler loop: {e}")
            
        await asyncio.sleep(20)

@check_permission
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    user = update.effective_user.first_name if update.effective_user else "Owner"
    await update.message.reply_text(
        f"🤖 <b>Bot AI Business Control Tower aktif (V5A).</b>\n\n"
        f"Halo {user}! Saya siap memantau performa bisnis, keuangan, perpajakan, dan mengirim laporan berkala.\n\n"
        f"Ketik /help untuk daftar perintah lengkap.",
        parse_mode="HTML"
    )

@check_permission
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    help_text = (
        "🤖 <b>Daftar Perintah & Fitur Bot (V5A):</b>\n\n"
        "<b>Menu Keuangan & Pajak (Finance & Tax):</b>\n"
        "/finance - 📊 Ringkasan laporan laba rugi tahun ini\n"
        "/tax - 🧾 Simulasi PPh Final UMKM & readiness PPN\n"
        "/tax_report - 📄 Download PDF Laporan Keuangan & Pajak\n"
        "/spt_check - 📋 Checklist dokumen pelaporan SPT Tahunan\n\n"
        "<b>Menu Command Inti:</b>\n"
        "/owner - 👑 Halaman keputusan harian owner (Control Room)\n"
        "/summary - 📊 Ringkasan finansial & action plan hari ini\n"
        "/report - 📄 Unduh Laporan PDF harian secara instan\n"
        "/alert_check - 🚨 Cek operasional dan kirim alert\n\n"
        "<b>Jadwal & Laporan Otomatis:</b>\n"
        "/daily_on | /daily_off - Aktif/nonaktifkan laporan otomatis harian\n"
        "/set_daily_time HH:MM - Atur jam laporan harian (default 08:00)\n"
        "/closing_on | /closing_off - Aktif/nonaktifkan closing report sore\n"
        "/set_closing_time HH:MM - Atur jam closing sore (default 17:00)\n"
        "/schedule_status - Tampilkan status penjadwalan & chat target\n"
        "/send_now - Kirim laporan harian & PDF sekarang juga\n\n"
        "<b>Menu Detail Lainnya:</b>\n"
        "/top_products, /stock, /materials, /production, /ads\n\n"
        "<b>NLP Command (Ketik Biasa):</b>\n"
        "- <i>laporan keuangan tahun ini</i>\n"
        "- <i>simulasi pajak bisnis</i> | <i>checklist spt</i>"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

@check_permission
async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /summary command."""
    try:
        data = load_bot_data()
        sales = data["sales"]
        m = overview_metrics(sales)
        margin_val = m["margin"]
        
        invp = inventory_product_status(data["inventory_products"])
        stock_critical = len(invp[invp["status"] == "Kritis"])
        
        invm = inventory_material_status(data["inventory_materials"])
        materials_critical = len(invm[invm["status"] == "Kritis"])
        
        # Business health logic
        if margin_val < 0.15 or stock_critical > 5 or materials_critical > 12:
            status_bisnis = "Kritis"
            status_emoji = "🔴"
        elif margin_val >= 0.25 and stock_critical <= 3 and materials_critical <= 10:
            status_bisnis = "Sehat"
            status_emoji = "🟢"
        else:
            status_bisnis = "Waspada"
            status_emoji = "🟡"
            
        actions = get_top_3_actions(data, m, stock_critical, materials_critical)
        actions_str = "\n".join(f"{idx+1}. {act}" for idx, act in enumerate(actions))

        text = (
            f"📊 <b>Ringkasan Performa Bisnis</b>\n"
            f"📅 Tanggal: {m['latest_date'].date()}\n\n"
            f"🏥 <b>Status Bisnis:</b> {status_emoji} <b>{status_bisnis.upper()}</b>\n\n"
            f"💵 <b>Omzet Hari Ini:</b> {rupiah(m['gross'])}\n"
            f"📈 <b>Profit Bersih:</b> {rupiah(m['profit'])}\n"
            f"💰 <b>Margin Bersih:</b> {pct(m['margin'])}\n"
            f"📦 <b>Jumlah Order:</b> {m['orders']}\n"
            f"📣 <b>Biaya Iklan:</b> {rupiah(m['ad_spend'])}\n\n"
            f"🎯 <b>3 Action Plan Hari Ini:</b>\n{actions_str}"
        )
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan saat membaca ringkasan data: {e}")

@check_permission
async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /owner command."""
    try:
        data = load_bot_data()
        sales = data["sales"]
        m = overview_metrics(sales)
        margin_val = m["margin"]
        
        invp = inventory_product_status(data["inventory_products"])
        critical_products = invp[invp["status"] == "Kritis"]
        produk_kritis_count = len(critical_products)
        
        invm = inventory_material_status(data["inventory_materials"])
        critical_materials = invm[invm["status"] == "Kritis"]
        bahan_kritis_count = len(critical_materials)
        
        if margin_val < 0.15 or produk_kritis_count > 5 or bahan_kritis_count > 12:
            status_bisnis = "Kritis"
            status_emoji = "🔴"
        elif margin_val >= 0.25 and produk_kritis_count <= 3 and bahan_kritis_count <= 10:
            status_bisnis = "Sehat"
            status_emoji = "🟢"
        else:
            status_bisnis = "Waspada"
            status_emoji = "🟡"
            
        pp = data["production_plan"]
        need_prod = pp[pp["recommended_production"] > 0]
        if not need_prod.empty:
            top_prod = need_prod.sort_values("recommended_production", ascending=False).iloc[0]
            prod_info = f"🛠️ <b>{top_prod['product']}</b> (Produksi {int(top_prod['recommended_production'])} pcs)"
        else:
            prod_info = "🟢 Aman (Tidak ada antrean produksi)"
            
        need_m, suggested_cost = suggested_purchase_value(data["inventory_materials"])
        if not need_m.empty:
            mats_list = ", ".join(need_m.head(3)["material"].tolist())
            bahan_info = f"🛍️ <b>{mats_list}</b> (Est: {rupiah(suggested_cost)})"
        else:
            bahan_info = "🟢 Aman (Stok bahan mencukupi)"
            
        ads_df = data["ads"]
        critical_ads = ads_df[ads_df["status"].isin(["Waspada", "Boncos"])]
        if not critical_ads.empty:
            ads_list = ", ".join(critical_ads.head(2)["campaign"].tolist())
            iklan_info = f"⚠️ <b>{ads_list}</b> (Evaluasi ROAS)"
        else:
            iklan_info = "🟢 Sehat (Semua campaign stabil)"
            
        # 5 Action plans
        action_plans = []
        if not need_prod.empty:
            top_row = need_prod.sort_values("recommended_production", ascending=False).iloc[0]
            action_plans.append(f"Produksi <b>{top_row['product']}</b> sebanyak {int(top_row['recommended_production'])} pcs.")
        else:
            action_plans.append("Jaga stok produk jadi tetap aman.")
            
        if not need_m.empty:
            mats_list = ", ".join(need_m.head(3)["material"].tolist())
            action_plans.append(f"Belanja bahan kritis: <b>{mats_list}</b> (Est: {rupiah(suggested_cost)}).")
        else:
            action_plans.append("Pantau stok bahan baku secara berkala.")
            
        if not critical_ads.empty:
            ads_list = ", ".join(critical_ads["campaign"].tolist())
            action_plans.append(f"Sesuaikan budget campaign iklan: <b>{ads_list}</b>.")
        else:
            action_plans.append("Pertahankan alokasi budget iklan saat ini.")
            
        top_prod_df = top_products(sales, latest_only=False)
        if not top_prod_df.empty:
            cuan_row = top_prod_df.iloc[0]
            action_plans.append(f"Push marketing <b>{cuan_row['product']}</b> (Margin: {pct(cuan_row['margin'])}).")
        else:
            action_plans.append("Dorong promo penjualan bundling.")
            
        action_plans.append("Cross-check fisik stok botol kemasan sebelum SPK produksi.")
        
        actions_str = "\n".join(f"{idx+1}. {act}" for idx, act in enumerate(action_plans))
        
        text = (
            f"👑 <b>Owner Control Room - Keputusan Harian</b>\n"
            f"📅 Tanggal: {m['latest_date'].strftime('%Y-%m-%d')}\n\n"
            f"🏥 <b>Status Bisnis:</b> {status_emoji} <b>{status_bisnis.upper()}</b>\n\n"
            f"💵 <b>Keuangan:</b>\n"
            f"  - Omzet: {rupiah(m['gross'])}\n"
            f"  - Profit: {rupiah(m['profit'])}\n"
            f"  - Margin: {pct(margin_val)}\n\n"
            f"🏭 <b>Produksi Prioritas:</b>\n"
            f"  {prod_info}\n\n"
            f"🧪 <b>Belanja Bahan Baku:</b>\n"
            f"  {bahan_info}\n\n"
            f"📣 <b>Iklan Perlu Dicek:</b>\n"
            f"  {iklan_info}\n\n"
            f"🎯 <b>5 Action Plan Hari Ini:</b>\n"
            f"{actions_str}"
        )
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal memuat keputusan owner: {e}")

@check_permission
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /report command."""
    status_msg = await update.message.reply_text("📄 Laporan sedang dibuat...")
    try:
        data = load_bot_data()
        pdf_bytes = generate_daily_pdf_report(data)
        await update.message.reply_document(
            document=io.BytesIO(pdf_bytes),
            filename="laporan_harian_bisnis_parfum.pdf",
            caption=f"📄 <b>Laporan Harian Bisnis Parfum</b>\nTanggal: {data['sales']['date'].max().strftime('%Y-%m-%d')}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal membuat laporan: {str(e)}")
    finally:
        try:
            await status_msg.delete()
        except Exception:
            pass

@check_permission
async def alert_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /alert_check command."""
    try:
        data = load_bot_data()
        alert_points = check_business_alerts(data)
        
        if not alert_points:
            await update.message.reply_text("✅ <b>Semua Aman!</b> Tidak ada alert operasional saat ini.", parse_mode="HTML")
        else:
            alert_str = "\n".join(alert_points)
            text = (
                f"🚨 <b>Alert Bisnis Parfum</b>\n"
                f"{alert_str}\n"
                f"* <b>Rekomendasi:</b> cek Owner Control Room /owner"
            )
            await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal melakukan pengecekan alert: {e}")

@check_permission
async def finance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /finance command."""
    try:
        data = load_bot_data()
        sales = data["sales"]
        sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
        if not sales.empty:
            year = int(sales["date"].max().year)
        else:
            year = datetime.now().year
            
        pl = build_profit_loss_report(data, period="yearly", year=year)
        text = (
            f"📊 <b>Ringkasan Keuangan (Tahun Pajak {year})</b>\n\n"
            f"💵 <b>Omzet Bruto Tahunan:</b> {rupiah(pl['gross_revenue'])}\n"
            f"📈 <b>Laba Bersih Sebelum Pajak (EBT):</b> {rupiah(pl['net_profit_before_tax'])}\n"
            f"🛍️ <b>Biaya Operasional (Expenses):</b> {rupiah(pl['operating_expenses'])}\n"
            f"💰 <b>Estimasi Profit Bersih Setelah Pajak (EAT):</b> {rupiah(pl['net_profit_after_tax'])}\n\n"
            f"💡 <i>Disclaimer: Data bersifat simulasi internal. Hubungi konsultan pajak/DJP untuk validasi resmi.</i>"
        )
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal memuat ringkasan keuangan: {e}")

@check_permission
async def tax_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /tax command."""
    try:
        data = load_bot_data()
        sales = data["sales"]
        sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
        if not sales.empty:
            year = int(sales["date"].max().year)
        else:
            year = datetime.now().year
            
        tax_est = calculate_tax_estimate(data, year)
        
        pkp_status = "Ya (PKP)" if tax_est["is_pkp"] else "Tidak (Non-PKP)"
        ppn_detail = ""
        if tax_est["is_pkp"]:
            ppn_detail = (
                f"  - PPN Keluaran: {rupiah(tax_est['ppn_keluaran'])}\n"
                f"  - PPN Masukan: {rupiah(tax_est['ppn_masukan'])}\n"
                f"  - PPN Kurang Bayar: {rupiah(tax_est['ppn_kurang_bayar'])}\n"
            )
        else:
            ppn_detail = "  - Status: Tidak memungut PPN (WP Non-PKP)\n"
            
        text = (
            f"🧾 <b>Simulasi Pajak Bisnis (Tahun {year})</b>\n\n"
            f"🏢 <b>Status PKP:</b> {pkp_status}\n"
            f"💰 <b>Omzet Bruto Tahunan:</b> {rupiah(tax_est['annual_gross'])}\n"
            f"💵 <b>Estimasi PPh Final UMKM:</b> {rupiah(tax_est['estimated_pph_final'])}\n\n"
            f"⚖️ <b>Readiness PPN:</b>\n{ppn_detail}\n"
            f"⚠️ <b>Disclaimer:</b> Estimasi pajak bersifat simulasi internal. Validasi final tetap perlu dilakukan dengan konsultan pajak atau DJP."
        )
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal memuat simulasi pajak: {e}")

@check_permission
async def tax_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /tax_report command."""
    status_msg = await update.message.reply_text("📄 Laporan Pajak & Keuangan sedang dibuat...")
    try:
        data = load_bot_data()
        sales = data["sales"]
        sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
        if not sales.empty:
            year = int(sales["date"].max().year)
        else:
            year = datetime.now().year
            
        pdf_bytes = generate_finance_tax_pdf_report(data, year)
        await update.message.reply_document(
            document=io.BytesIO(pdf_bytes),
            filename=f"laporan_keuangan_pajak_parfum_{year}.pdf",
            caption=f"📄 <b>Laporan Keuangan & Tax Readiness - Tahun {year}</b>\n\n⚠️ <i>Simulasi internal. Validasi final dengan konsultan pajak/DJP.</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal membuat laporan keuangan/pajak: {e}")
    finally:
        try:
            await status_msg.delete()
        except Exception:
            pass

@check_permission
async def spt_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /spt_check command."""
    try:
        import pandas as pd
        data = load_bot_data()
        sales = data["sales"]
        sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
        if not sales.empty:
            year = int(sales["date"].max().year)
        else:
            year = datetime.now().year
            
        checklist = build_tax_readiness_checklist(data, year)
        
        expenses_status = "Tersedia" if "expenses" in data and not data["expenses"].empty else "Kosong / Default"
        settings_status = "Tersedia" if "tax_settings" in data and not data["tax_settings"].empty else "Kosong / Default"
        payments_status = "Tersedia" if "tax_payments" in data and not data["tax_payments"].empty else "Kosong / Default"
        
        has_payments = "Ya" if "tax_payments" in data and not data["tax_payments"].empty and len(data["tax_payments"]) > 0 else "Tidak ada"
        
        lines = [
            f"📋 <b>Tax Readiness Checklist (Tahun {year})</b>\n",
            f"📊 <b>Status Tab Google Sheets/CSV:</b>",
            f"• <code>expenses</code>: {expenses_status}",
            f"• <code>tax_settings</code>: {settings_status}",
            f"• <code>tax_payments</code>: {payments_status}\n",
            f"💰 <b>Setoran Pajak Terdaftar:</b> {has_payments}\n",
            "🔍 <b>Detail Kelengkapan:</b>"
        ]
        
        missing_count = 0
        warning_count = 0
        missing_docs = []
        
        for item in checklist:
            emoji = "✅" if item["status"] == "Ready" else "⚠️" if item["status"] == "Warning" else "❌"
            if item["status"] == "Warning":
                warning_count += 1
                missing_docs.append(f"• <b>{item['item']}</b>: {item['description']}")
            elif item["status"] == "Missing":
                missing_count += 1
                missing_docs.append(f"• <b>{item['item']}</b>: {item['description']}")
            lines.append(f"{emoji} <b>{item['item']}:</b> {item['status']}\n   <i>{item['description']}</i>")
            
        # Add general documents needed if warning/missing
        missing_docs.append("• <b>Formulir SPT Tahunan 1770 / 1771</b> (sesuai status entitas bisnis).")
        missing_docs.append("• <b>Daftar Harta & Utang Akhir Tahun</b> (sebagai lampiran wajib SPT Orang Pribadi / Badan).")
        missing_docs.append("• <b>Rekapitulasi Omzet Bulanan</b> yang telah divalidasi ke mutasi rekening koran bank.")
        missing_docs.append("• <b>Bukti Penerimaan Negara (BPN)</b> untuk pembayaran PPh Final 0.5% setiap masa pajak.")
        
        lines.append("\n📝 <b>Catatan Dokumen yang Kurang / Perlu Disiapkan:</b>")
        for doc_item in missing_docs:
            lines.append(doc_item)
            
        text = "\n".join(lines)
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal memuat checklist SPT: {e}")

@check_permission
async def spt_pack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /spt_pack command."""
    status_msg = await update.message.reply_text("⏳ <i>Sedang memproses dan membuat Paket Lampiran Pendukung SPT...</i>", parse_mode="HTML")
    try:
        import pandas as pd
        data = load_bot_data()
        sales = data["sales"]
        sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
        if not sales.empty:
            year = int(sales["date"].max().year)
        else:
            year = datetime.now().year
            
        from modules.pdf_report import generate_spt_attachment_pack_pdf
        pdf_bytes = generate_spt_attachment_pack_pdf(data, year)
        
        # Kirim PDF sebagai dokumen
        await update.message.reply_document(
            document=io.BytesIO(pdf_bytes),
            filename=f"spt_attachment_pack_{year}.pdf",
            caption=f"💼 <b>Paket Lampiran Pendukung SPT Usaha - Tahun {year}</b>\n\n"
                    f"⚠️ <i>Estimasi pajak bersifat simulasi internal. Validasi final tetap perlu dilakukan dengan konsultan pajak atau DJP.</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal membuat Paket Lampiran SPT: {e}")
    finally:
        try:
            await status_msg.delete()
        except Exception:
            pass

# Scheduler configuration commands
@check_permission
async def daily_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    settings = load_settings()
    if chat_id not in settings["target_chats"]:
        settings["target_chats"].append(chat_id)
    settings["daily_enabled"] = True
    save_settings(settings)
    await update.message.reply_text(
        f"🟢 <b>Laporan Harian Otomatis Aktif</b>\n\n"
        f"Setiap pukul <code>{settings['daily_time']}</code> WIB, bot akan mengirimkan ringkasan bisnis dan laporan PDF harian ke chat ini.",
        parse_mode="HTML"
    )

@check_permission
async def daily_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()
    settings["daily_enabled"] = False
    save_settings(settings)
    await update.message.reply_text("🔴 <b>Laporan Harian Otomatis Dinonaktifkan</b>.", parse_mode="HTML")

@check_permission
async def set_daily_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ Gunakan format: /set_daily_time HH:MM (contoh: /set_daily_time 08:30)")
        return
    time_str = context.args[0].strip()
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError()
        h, m = int(parts[0]), int(parts[1])
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError()
        time_formatted = f"{h:02d}:{m:02d}"
    except ValueError:
        await update.message.reply_text("❌ Format waktu salah! Gunakan format HH:MM 24-jam (contoh: 08:00).")
        return
        
    settings = load_settings()
    settings["daily_time"] = time_formatted
    save_settings(settings)
    await update.message.reply_text(f"🕒 Jadwal laporan harian diatur ke pukul <b>{time_formatted} WIB</b> (Asia/Jakarta).", parse_mode="HTML")

@check_permission
async def closing_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    settings = load_settings()
    if chat_id not in settings["target_chats"]:
        settings["target_chats"].append(chat_id)
    settings["closing_enabled"] = True
    save_settings(settings)
    await update.message.reply_text(
        f"🟢 <b>Laporan Closing Sore Aktif</b>\n\n"
        f"Setiap pukul <code>{settings['closing_time']}</code> WIB, bot akan mengirimkan ringkasan omzet, profit, dan top produk hari ini ke chat ini.",
        parse_mode="HTML"
    )

@check_permission
async def closing_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()
    settings["closing_enabled"] = False
    save_settings(settings)
    await update.message.reply_text("🔴 <b>Laporan Closing Sore Dinonaktifkan</b>.", parse_mode="HTML")

@check_permission
async def set_closing_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ Gunakan format: /set_closing_time HH:MM (contoh: /set_closing_time 17:30)")
        return
    time_str = context.args[0].strip()
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError()
        h, m = int(parts[0]), int(parts[1])
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError()
        time_formatted = f"{h:02d}:{m:02d}"
    except ValueError:
        await update.message.reply_text("❌ Format waktu salah! Gunakan format HH:MM 24-jam (contoh: 17:00).")
        return
        
    settings = load_settings()
    settings["closing_time"] = time_formatted
    save_settings(settings)
    await update.message.reply_text(f"🕒 Jadwal laporan closing diatur ke pukul <b>{time_formatted} WIB</b> (Asia/Jakarta).", parse_mode="HTML")

@check_permission
async def schedule_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /schedule_status command."""
    try:
        settings = load_settings()
        allowed_ids_str = os.getenv("ALLOWED_CHAT_IDS", "")
        
        target_source = "Whitelist (.env)" if allowed_ids_str.strip() else "Dynamic (/daily_on)"
        daily_status = "Aktif" if settings["daily_enabled"] else "Nonaktif"
        closing_status = "Aktif" if settings["closing_enabled"] else "Nonaktif"
        
        if allowed_ids_str.strip():
            targets = [x.strip() for x in allowed_ids_str.split(",") if x.strip()]
        else:
            targets = [str(x) for x in settings["target_chats"]]
            
        targets_str = ", ".join(targets) if targets else "Belum ada penerima"
        
        text = (
            f"🕒 <b>Status Jadwal & Laporan Otomatis</b>\n\n"
            f"📅 <b>Laporan Harian (Daily):</b> {daily_status}\n"
            f"  - Waktu: <code>{settings['daily_time']}</code>\n\n"
            f"🌆 <b>Laporan Closing (Sore):</b> {closing_status}\n"
            f"  - Waktu: <code>{settings['closing_time']}</code>\n\n"
            f"🌍 <b>Timezone:</b> Asia/Jakarta\n"
            f"🎯 <b>Target Penerima:</b> {targets_str} ({target_source})"
        )
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal memuat status schedule: {e}")

@check_permission
async def send_now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /send_now command."""
    chat_id = update.effective_chat.id
    status_msg = await update.message.reply_text("📤 Mengirim laporan harian & PDF harian sekarang...")
    try:
        await send_daily_to_chat(context.bot, chat_id)
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal mengirim laporan: {e}")
    finally:
        try:
            await status_msg.delete()
        except Exception:
            pass

@check_permission
async def top_products_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /top_products command."""
    try:
        data = load_bot_data()
        top = top_products(data["sales"], latest_only=True).head(5)
        text = "🏆 <b>Top 5 Produk Terlaris Hari Ini</b>\n\n"
        if top.empty:
            text += "Tidak ada data penjualan hari ini."
        else:
            for i, row in enumerate(top.itertuples(index=False), start=1):
                text += f"{i}. <b>{row.product}</b>\n   Terjual: {int(row.terjual)} pcs\n   Omzet: {rupiah(row.omzet)} | Profit: {rupiah(row.profit)} ({pct(row.margin)})\n\n"
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal mengambil produk terlaris: {e}")

@check_permission
async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /stock command."""
    try:
        data = load_bot_data()
        invp = inventory_product_status(data["inventory_products"])
        critical = invp[invp["status"] == "Kritis"]
        text = "⚠️ <b>Daftar Produk Stok Kritis</b>\n\n"
        if critical.empty:
            text += "🟢 Semua stok produk jadi aman!"
        else:
            for row in critical.itertuples(index=False):
                text += f"• <b>{row.product}</b> (SKU: <code>{row.sku}</code>)\n  Stok: {int(row.stock)} / Min: {int(row.min_stock)} pcs\n  Estimasi Habis: <b>{row.estimasi_hari_habis} hari</b>\n\n"
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal memuat data stok: {e}")

@check_permission
async def materials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /materials command."""
    try:
        data = load_bot_data()
        invm = inventory_material_status(data["inventory_materials"])
        critical = invm[invm["status"] == "Kritis"]
        need_m, suggested_cost = suggested_purchase_value(data["inventory_materials"])
        text = "🧪 <b>Status Bahan Baku Kritis</b>\n\n"
        if critical.empty:
            text += "🟢 Semua bahan baku aman!\n\n"
        else:
            for row in critical.itertuples(index=False):
                text += f"• <b>{row.material}</b>\n  Stok: {row.stock} {row.unit} (Minimum: {row.min_stock} {row.unit})\n\n"
        if not need_m.empty:
            text += "🛍️ <b>Rekomendasi Rencana Belanja Bahan:</b>\n"
            for row in need_m.itertuples(index=False):
                text += f"- <b>{row.material}</b>: beli {row.recommended_qty:.1f} {row.unit} (Est: {rupiah(row.estimated_cost)})\n"
            text += f"\n💰 <b>Total Estimasi Belanja:</b> {rupiah(suggested_cost)}"
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal memuat data bahan baku: {e}")

@check_permission
async def production_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /production command."""
    try:
        data = load_bot_data()
        pp = data["production_plan"]
        need_prod = pp[pp["recommended_production"] > 0]
        text = "🏭 <b>Rekomendasi Rencana Produksi</b>\n\n"
        if need_prod.empty:
            text += "🟢 Stok mencukupi, tidak ada rekomendasi produksi baru."
        else:
            for row in need_prod.itertuples(index=False):
                text += f"• <b>{row.product}</b> (SKU: <code>{row.sku}</code>)\n  Stok: {int(row.stock)} | Permintaan 7 Hari: {int(row.demand_7d)}\n  🛠️ <b>Rekomendasi Produksi: {int(row.recommended_production)} pcs</b>\n  ⚠️ Bottleneck: {row.bottleneck}\n\n"
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal memuat rencana produksi: {e}")

@check_permission
async def ads_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /ads command."""
    try:
        data = load_bot_data()
        ads = data["ads"]
        text = "📣 <b>Performa Kampanye Iklan</b>\n\n"
        if ads.empty:
            text += "Tidak ada data iklan."
        else:
            for row in ads.itertuples(index=False):
                status_emoji = "🟢" if row.status == "Sehat" else "🟡" if row.status == "Waspada" else "🔴"
                text += f"{status_emoji} <b>{row.campaign}</b> ({row.platform})\n  Spend: {rupiah(row.spend)} | Revenue: {rupiah(row.revenue)}\n  ROAS: <b>{row.roas:.2f}x</b> | Status: <b>{row.status}</b>\n\n"
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal memuat data performa iklan: {e}")

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Router for normal text based queries to command mappings."""
    chat_id = update.effective_chat.id
    if not is_allowed_user(chat_id):
        print(f"Blocked unauthorized message from Chat ID: {chat_id}")
        await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
        return

    text = update.message.text.lower().strip()
    if any(k in text for k in ["laporan keuangan", "laba rugi"]):
        await finance_command(update, context)
    elif any(k in text for k in ["pph final", "ppn", "pajak"]):
        await tax_command(update, context)
    elif any(k in text for k in ["lampiran spt", "paket spt", "rekap spt"]):
        await spt_pack_command(update, context)
    elif any(k in text for k in ["spt", "checklist pajak"]):
        await spt_check_command(update, context)
    elif any(k in text for k in ["profit", "omzet", "ringkasan", "summary"]):
        await summary_command(update, context)
    elif any(k in text for k in ["laporan", "pdf", "report", "harian"]):
        await report_command(update, context)
    elif any(k in text for k in ["produk paling laku", "top produk", "terlaris", "paling untung"]):
        await top_products_command(update, context)
    elif any(k in text for k in ["stok kritis", "stok"]):
        await stock_command(update, context)
    elif any(k in text for k in ["bahan", "material", "dibeli", "belanja"]):
        await materials_command(update, context)
    elif any(k in text for k in ["produksi", "sku produksi"]):
        await production_command(update, context)
    elif any(k in text for k in ["iklan", "ads", "boncos", "roas"]):
        await ads_command(update, context)
    elif any(k in text for k in ["owner", "keputusan hari ini", "apa yang harus dilakukan", "action plan"]):
        await owner_command(update, context)
    else:
        await update.message.reply_text(
            "🤖 Saya kurang memahami pesan tersebut.\n\n"
            "Gunakan perintah /help atau tanyakan hal seperti:\n"
            "- <i>laporan keuangan tahun ini</i>\n"
            "- <i>simulasi pajak bisnis</i>\n"
            "- <i>spt checklist</i>\n"
            "- <i>apa yang harus dilakukan hari ini</i>",
            parse_mode="HTML"
        )
