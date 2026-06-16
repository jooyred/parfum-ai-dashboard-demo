import os
import io
import toml
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
from modules.pdf_report import generate_daily_pdf_report

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
    
    # 1. Production check
    pp = data["production_plan"]
    need_prod = pp[pp["recommended_production"] > 0]
    if not need_prod.empty:
        top_prod = need_prod.sort_values("recommended_production", ascending=False).iloc[0]
        actions.append(f"Produksi <b>{top_prod['product']}</b> ({int(top_prod['recommended_production'])} pcs).")
    else:
        actions.append("Stok produk jadi aman.")
        
    # 2. Materials check
    need_m, suggested_cost = suggested_purchase_value(data["inventory_materials"])
    if not need_m.empty:
        mats_list = ", ".join(need_m.head(2)["material"].tolist())
        actions.append(f"Beli bahan kritis: <b>{mats_list}</b>.")
    else:
        actions.append("Stok bahan baku cukup.")
        
    # 3. Ads check
    ads_df = data["ads"]
    critical_ads = ads_df[ads_df["status"].isin(["Waspada", "Boncos"])]
    if not critical_ads.empty:
        ads_list = ", ".join(critical_ads.head(2)["campaign"].tolist())
        actions.append(f"Evaluasi iklan: <b>{ads_list}</b>.")
    else:
        actions.append("Kampanye iklan stabil.")
        
    return actions

@check_permission
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    user = update.effective_user.first_name if update.effective_user else "Owner"
    await update.message.reply_text(
        f"🤖 <b>Bot AI Business Control Tower aktif (V4A).</b>\n\n"
        f"Halo {user}! Saya siap membantu memantau performa bisnis dan mengambil keputusan harian.\n\n"
        f"Ketik /help untuk melihat daftar menu lengkap.",
        parse_mode="HTML"
    )

@check_permission
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    help_text = (
        "🤖 <b>Daftar Perintah & Fitur Bot (V4A):</b>\n\n"
        "<b>Menu Command:</b>\n"
        "/owner - 👑 Halaman keputusan harian owner (Control Room)\n"
        "/summary - 📊 Ringkasan performa finansial & 3 rencana aksi hari ini\n"
        "/report - 📄 Unduh Laporan PDF Harian secara instan\n"
        "/top_products - 🏆 Tampilkan 5 produk terlaris hari ini\n"
        "/stock - ⚠️ Tampilkan produk dengan stok kritis\n"
        "/materials - 🧪 Tampilkan status bahan baku & rencana belanja\n"
        "/production - 🏭 Tampilkan rekomendasi rencana produksi\n"
        "/ads - 📣 Tampilkan performa kampanye iklan aktif\n\n"
        "<b>Perintah Natural Language (Ketik Biasa):</b>\n"
        "- <i>apa yang harus dilakukan hari ini</i> atau <i>action plan</i>\n"
        "- <i>profit hari ini</i> atau <i>omzet hari ini</i>\n"
        "- <i>stok kritis</i> atau <i>produk terlaris</i>\n"
        "- <i>kirim pdf</i> atau <i>laporan harian</i>"
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
            f"⚠️ <b>Status Operasional:</b>\n"
            f"- Produk Stok Kritis: {stock_critical} SKU\n"
            f"- Bahan Baku Kritis: {materials_critical} item\n\n"
            f"🎯 <b>3 Action Plan Hari Ini:</b>\n{actions_str}"
        )
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan saat membaca ringkasan data: {e}")

@check_permission
async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /owner command (Owner Control Room)."""
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
        
        # Business health logic
        if margin_val < 0.15 or produk_kritis_count > 5 or bahan_kritis_count > 12:
            status_bisnis = "Kritis"
            status_emoji = "🔴"
        elif margin_val >= 0.25 and produk_kritis_count <= 3 and bahan_kritis_count <= 10:
            status_bisnis = "Sehat"
            status_emoji = "🟢"
        else:
            status_bisnis = "Waspada"
            status_emoji = "🟡"
            
        # 1. Produksi prioritas
        pp = data["production_plan"]
        need_prod = pp[pp["recommended_production"] > 0]
        if not need_prod.empty:
            top_prod = need_prod.sort_values("recommended_production", ascending=False).iloc[0]
            prod_info = f"🛠️ <b>{top_prod['product']}</b> (Produksi {int(top_prod['recommended_production'])} pcs)"
        else:
            prod_info = "🟢 Aman (Tidak ada antrean produksi)"
            
        # 2. Bahan urgent
        need_m, suggested_cost = suggested_purchase_value(data["inventory_materials"])
        if not need_m.empty:
            mats_list = ", ".join(need_m.head(3)["material"].tolist())
            bahan_info = f"🛍️ <b>{mats_list}</b> (Est: {rupiah(suggested_cost)})"
        else:
            bahan_info = "🟢 Aman (Stok bahan mencukupi)"
            
        # 3. Iklan dicek
        ads_df = data["ads"]
        critical_ads = ads_df[ads_df["status"].isin(["Waspada", "Boncos"])]
        if not critical_ads.empty:
            ads_list = ", ".join(critical_ads.head(2)["campaign"].tolist())
            iklan_info = f"⚠️ <b>{ads_list}</b> (Evaluasi ROAS)"
        else:
            iklan_info = "🟢 Sehat (Semua campaign stabil)"
            
        # 5 Action points
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
            
        # Top profit product
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
                text += (
                    f"{i}. <b>{row.product}</b>\n"
                    f"   Terjual: {int(row.terjual)} pcs\n"
                    f"   Omzet: {rupiah(row.omzet)} | Profit: {rupiah(row.profit)} ({pct(row.margin)})\n\n"
                )
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
                text += (
                    f"• <b>{row.product}</b> (SKU: <code>{row.sku}</code>)\n"
                    f"  Stok: {int(row.stock)} / Min: {int(row.min_stock)} pcs\n"
                    f"  Estimasi Habis: <b>{row.estimasi_hari_habis} hari</b>\n\n"
                )
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
                text += (
                    f"• <b>{row.material}</b>\n"
                    f"  Stok: {row.stock} {row.unit} (Minimum: {row.min_stock} {row.unit})\n\n"
                )
                
        if not need_m.empty:
            text += "🛍️ <b>Rekomendasi Rencana Belanja Bahan:</b>\n"
            for row in need_m.itertuples(index=False):
                text += (
                    f"- <b>{row.material}</b>: beli {row.recommended_qty:.1f} {row.unit} "
                    f"(Est: {rupiah(row.estimated_cost)})\n"
                )
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
                text += (
                    f"• <b>{row.product}</b> (SKU: <code>{row.sku}</code>)\n"
                    f"  Stok: {int(row.stock)} | Permintaan 7 Hari: {int(row.demand_7d)}\n"
                    f"  🛠️ <b>Rekomendasi Produksi: {int(row.recommended_production)} pcs</b>\n"
                    f"  ⚠️ Bottleneck: {row.bottleneck}\n\n"
                )
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
                text += (
                    f"{status_emoji} <b>{row.campaign}</b> ({row.platform})\n"
                    f"  Spend: {rupiah(row.spend)} | Revenue: {rupiah(row.revenue)}\n"
                    f"  ROAS: <b>{row.roas:.2f}x</b> | Status: <b>{row.status}</b>\n\n"
                )
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
    
    # Matching keywords
    if any(k in text for k in ["profit", "omzet", "ringkasan", "summary"]):
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
            "- <i>apa yang harus dilakukan hari ini</i>\n"
            "- <i>profit hari ini</i>\n"
            "- <i>stok kritis</i>\n"
            "- <i>buat laporan harian</i>",
            parse_mode="HTML"
        )
