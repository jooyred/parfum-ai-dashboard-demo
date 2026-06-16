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
                # Load Google Sheets data
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
        # Empty whitelist means everyone is allowed for local demo
        return True
    try:
        allowed_ids = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
        return chat_id in allowed_ids
    except Exception as e:
        print(f"Error parsing ALLOWED_CHAT_IDS: {e}")
        return True

# Decorator or helper check
def check_permission(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat_id = update.effective_chat.id
        if not is_allowed_user(chat_id):
            print(f"Blocked unauthorized access from Chat ID: {chat_id}")
            await update.message.reply_text("❌ Maaf, Anda tidak memiliki akses ke bot ini.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

@check_permission
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    user = update.effective_user.first_name if update.effective_user else "Owner"
    await update.message.reply_text(
        f"🤖 <b>Bot AI Business Control Tower aktif.</b>\n\n"
        f"Halo {user}! Saya adalah asisten bot lokal Anda untuk memantau performa bisnis parfum.\n\n"
        f"Ketik /help untuk melihat daftar menu lengkap dan perintah natural language yang bisa saya jawab.",
        parse_mode="HTML"
    )

@check_permission
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    help_text = (
        "🤖 <b>Daftar Perintah & Fitur Bot:</b>\n\n"
        "<b>Menu Command:</b>\n"
        "/summary - Ringkasan performa finansial dan operasional hari ini\n"
        "/report - Membuat dan mengirimkan Laporan PDF harian\n"
        "/top_products - Menampilkan 5 produk terlaris hari ini\n"
        "/stock - Melihat produk yang mengalami stok kritis\n"
        "/materials - Melihat status bahan baku dan rekomendasi belanja\n"
        "/production - Melihat rencana dan rekomendasi produksi\n"
        "/ads - Melihat performa kampanye iklan aktif\n\n"
        "<b>Contoh Pertanyaan Natural Language (Ketik Biasa):</b>\n"
        "- <i>profit hari ini</i> atau <i>omzet hari ini</i>\n"
        "- <i>stok kritis</i> atau <i>produk terlaris</i>\n"
        "- <i>bahan apa yang harus dibeli</i>\n"
        "- <i>sku mana yang harus diproduksi</i>\n"
        "- <i>iklan mana yang boncos</i>\n"
        "- <i>buat laporan</i> atau <i>kirim pdf</i>"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

@check_permission
async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /summary command."""
    try:
        data = load_bot_data()
        sales = data["sales"]
        m = overview_metrics(sales)
        
        invp = inventory_product_status(data["inventory_products"])
        stock_critical = len(invp[invp["status"] == "Kritis"])
        
        invm = inventory_material_status(data["inventory_materials"])
        materials_critical = len(invm[invm["status"] == "Kritis"])
        
        # Build insight list
        insights = []
        if stock_critical > 0:
            insights.append(f"⚠️ {stock_critical} SKU produk jadi kritis.")
        else:
            insights.append("🟢 Stok produk jadi aman.")
            
        if materials_critical > 0:
            insights.append(f"⚠️ {materials_critical} bahan baku kritis.")
        else:
            insights.append("🟢 Bahan baku mencukupi.")
            
        if m['margin'] < 0.2:
            insights.append("📉 Margin profit di bawah target 20%.")
        else:
            insights.append("📈 Margin profit sehat (>= 20%).")
            
        insights_str = "\n".join(f"- {ins}" for ins in insights)

        text = (
            f"📊 <b>Ringkasan Performa Bisnis</b>\n"
            f"📅 Tanggal: {m['latest_date'].date()}\n\n"
            f"💵 <b>Omzet Hari Ini:</b> {rupiah(m['gross'])}\n"
            f"📈 <b>Profit Bersih:</b> {rupiah(m['profit'])}\n"
            f"💰 <b>Margin Bersih:</b> {pct(m['margin'])}\n"
            f"📦 <b>Jumlah Order:</b> {m['orders']}\n"
            f"📣 <b>Biaya Iklan:</b> {rupiah(m['ad_spend'])}\n\n"
            f"⚠️ <b>Status Operasional:</b>\n"
            f"- Produk Stok Kritis: {stock_critical} SKU\n"
            f"- Bahan Baku Kritis: {materials_critical} item\n\n"
            f"💡 <b>Insight Harian:</b>\n{insights_str}"
        )
        await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan saat membaca ringkasan data: {e}")

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
        # Clean up sending status message
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
    else:
        await update.message.reply_text(
            "🤖 Saya kurang memahami pesan tersebut.\n\n"
            "Gunakan perintah /help atau tanyakan hal seperti:\n"
            "- <i>profit hari ini</i>\n"
            "- <i>stok kritis</i>\n"
            "- <i>iklan boncos</i>\n"
            "- <i>buat laporan harian</i>",
            parse_mode="HTML"
        )
