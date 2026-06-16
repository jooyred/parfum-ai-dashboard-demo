import os
import sys
import toml
import pandas as pd
from datetime import datetime, timedelta

# Add project root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Create expenses dummy data (30-60 rows for 12 months of 2026)
expenses_list = []
# Fixed expenses
# Sewa ruko at start of year
expenses_list.append({
    "date": "2026-01-02",
    "category": "Sewa",
    "description": "Sewa Ruko Tahunan 2026",
    "amount": 36000000,
    "payment_method": "Transfer",
    "vendor": "Ruko Agung Mandiri",
    "tax_deductible": "false",  # Under standard PPh Final, sewa is subject to final tax by landlord, not deductible for tenant PPh final
    "notes": "Sewa ruko setahun penuh"
})

months = pd.date_range(start="2026-01-01", end="2026-12-01", freq="MS")
categories_details = {
    "Gaji": ("Pembayaran Gaji Karyawan", 8500000, "Transfer", "Staff Parfum", "false", "Gaji bulanan 2 staff"),
    "Internet": ("Langganan Internet Biznet", 550000, "Auto-debit", "Biznet Networks", "true", "Wifi High-speed"),
    "Operasional": ("Biaya Operasional Toko", 1200000, "Kas Kecil", "Toko ATK & Kelontong", "true", "Kebutuhan harian operasional"),
    "Transport": ("Bensin & Tol Kirim Barang", 800000, "Kas Kecil", "Pertamina", "true", "Operasional delivery"),
    "Ads": ("Iklan Meta & TikTok Ads", 7500000, "Credit Card", "Meta & Bytedance", "true", "Iklan bulanan"),
    "Marketplace Fee": ("Marketplace Admin Fee", 3200000, "Dipotong Sistem", "Shopee & Tokopedia", "true", "Biaya admin platform")
}

for m in months:
    m_str = m.strftime("%Y-%m")
    # For every month, add regular expenses
    for cat, (desc, amt, pay_m, vend, tax_d, notes) in categories_details.items():
        # Add slight variation to amount
        if cat == "Ads":
            amt_var = int(amt * (0.8 + 0.4 * (m.month % 3) / 2)) # Var between 80% to 120%
        elif cat == "Marketplace Fee":
            amt_var = int(amt * (0.9 + 0.2 * (m.month % 2)))
        else:
            amt_var = amt
            
        expenses_list.append({
            "date": f"{m_str}-15",
            "category": cat,
            "description": f"{desc} - {m.strftime('%B %Y')}",
            "amount": amt_var,
            "payment_method": pay_m,
            "vendor": vend,
            "tax_deductible": tax_d,
            "notes": notes
        })

expenses_df = pd.DataFrame(expenses_list)
expenses_df.to_csv(os.path.join(DATA_DIR, "expenses.csv"), index=False)
print(f"✅ Created local template: data/expenses.csv ({len(expenses_df)} rows).")

# 2. Create tax_settings template
tax_settings_list = [
    {"key": "business_entity", "value": "orang_pribadi_umkm", "notes": "Jenis Wajib Pajak: orang_pribadi_umkm / badan_umkm / orang_pribadi_umum / badan_umum"},
    {"key": "is_pkp", "value": "false", "notes": "Status PKP: true / false"},
    {"key": "use_pph_final_umkm", "value": "true", "notes": "Menggunakan PPh Final UMKM 0.5% (PP 55/2022)"},
    {"key": "pph_final_rate", "value": "0.005", "notes": "Tarif PPh Final UMKM 0.5%"},
    {"key": "annual_omzet_threshold", "value": "4800000000", "notes": "Batas omzet PKP Rp 4.8 Miliar per tahun"},
    {"key": "ppn_rate", "value": "0.12", "notes": "Tarif PPN yang berlaku"},
    {"key": "tax_year", "value": "2026", "notes": "Tahun Pajak Laporan"},
    {"key": "disclaimer", "value": "Estimasi pajak bersifat simulasi internal. Validasi final tetap perlu dilakukan dengan konsultan pajak atau DJP.", "notes": "Disclaimer perpajakan"}
]
tax_settings_df = pd.DataFrame(tax_settings_list)
tax_settings_df.to_csv(os.path.join(DATA_DIR, "tax_settings.csv"), index=False)
print("✅ Created local template: data/tax_settings.csv.")

# 3. Create tax_payments template
tax_payments_list = [
    {"date": "2026-02-10", "tax_type": "PPh Final UMKM", "period": "Masa Pajak Januari 2026", "amount": 250000, "payment_ref": "NTPN-DEMO-001", "notes": "Bukti setor dummy untuk demo"},
    {"date": "2026-03-10", "tax_type": "PPh Final UMKM", "period": "Masa Pajak Februari 2026", "amount": 310000, "payment_ref": "NTPN-DEMO-002", "notes": "Bukti setor dummy untuk demo"},
    {"date": "2026-04-10", "tax_type": "PPh Final UMKM", "period": "Masa Pajak Maret 2026", "amount": 280000, "payment_ref": "NTPN-DEMO-003", "notes": "Bukti setor dummy untuk demo"},
    {"date": "2026-05-10", "tax_type": "PPh Final UMKM", "period": "Masa Pajak April 2026", "amount": 340000, "payment_ref": "NTPN-DEMO-004", "notes": "Bukti setor dummy untuk demo"},
    {"date": "2026-06-10", "tax_type": "PPh Final UMKM", "period": "Masa Pajak Mei 2026", "amount": 420000, "payment_ref": "NTPN-DEMO-005", "notes": "Bukti setor dummy untuk demo"},
]
tax_payments_df = pd.DataFrame(tax_payments_list)
tax_payments_df.to_csv(os.path.join(DATA_DIR, "tax_payments.csv"), index=False)
print("✅ Created local template: data/tax_payments.csv.")

# 4. Attempt to write to Google Sheets
secrets_path = os.path.join(".streamlit", "secrets.toml")
if os.path.exists(secrets_path):
    try:
        secrets = toml.load(secrets_path)
        sheet_id = secrets.get("GOOGLE_SHEET_ID")
        creds_info = secrets.get("google_service_account")
        if sheet_id and creds_info:
            print("\n🔄 Mencoba menyinkronkan template ke Google Sheets...")
            import gspread
            from google.oauth2.service_account import Credentials
            from modules.sheets_loader import get_sheet_id_from_url
            
            scopes = ["https://www.googleapis.com/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(dict(creds_info), scopes=scopes)
            client = gspread.authorize(creds)
            
            actual_id = get_sheet_id_from_url(sheet_id)
            spreadsheet = client.open_by_key(actual_id)
            
            # Check worksheets
            worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}
            
            # Helper to create/populate a worksheet
            def sync_sheet(title, df):
                if title in worksheets:
                    print(f"ℹ️ Tab '{title}' sudah ada di Google Sheets. Lewati (tidak di-overwrite).")
                else:
                    try:
                        # Try creating sheet
                        ws = spreadsheet.add_worksheet(title=title, rows="1000", cols="20")
                        # Write headers and values
                        ws.update([df.columns.values.tolist()] + df.values.tolist())
                        print(f"✅ Berhasil membuat & mengisi tab '{title}' di Google Sheets!")
                    except Exception as e:
                        print(f"⚠️ Gagal membuat/mengisi tab '{title}': {e}. Kemungkinan permission service account Anda adalah Viewer.")
                        
            sync_sheet("expenses", expenses_df)
            sync_sheet("tax_settings", tax_settings_df)
            sync_sheet("tax_payments", tax_payments_df)
            
    except Exception as e:
        print(f"\n⚠️ Sinkronisasi Google Sheets dibatalkan/gagal: {e}")
        print("ℹ️ Bot tetap dapat berjalan secara lokal menggunakan file CSV dummy di folder data/.")
else:
    print("\nℹ️ secrets.toml tidak ditemukan. Bot akan menggunakan file CSV lokal saja.")
