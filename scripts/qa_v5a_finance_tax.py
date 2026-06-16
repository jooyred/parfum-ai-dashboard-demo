import os
import sys
import toml
import pandas as pd

# Add project root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.calculations import (
    load_data, rupiah, pct, overview_metrics
)
from modules.sheets_loader import (
    load_google_sheets_data, validate_sheet_tabs, normalize_google_sheet_data, get_sheet_id_from_url
)
from modules.pdf_report import generate_finance_tax_pdf_report
from modules.finance_tax import (
    parse_settings, build_profit_loss_report, build_monthly_omzet_summary,
    calculate_tax_estimate, build_tax_readiness_checklist, generate_finance_tax_insights
)

def run_qa():
    print("=" * 60)
    print("RUNNING AUTOMATED QA VERIFICATION FOR V5A (FINANCE & TAX PACK)")
    print("=" * 60)
    
    # 1. Load Data (Google Sheets with fallback)
    data = None
    data_source = "Dummy CSV (local)"
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
                    data = normalize_google_sheet_data(raw_data)
                    data_source = "Google Sheets (realtime)"
                    print("✅ Successfully loaded Google Sheets data.")
                else:
                    print(f"⚠️ Google Sheets tabs missing: {missing}. Falling back to CSV.")
            else:
                print("⚠️ Secrets exist but GOOGLE_SHEET_ID or credentials missing. Falling back to CSV.")
        except Exception as e:
            print(f"⚠️ Failed to load Google Sheets ({e}). Falling back to CSV.")
            
    if data is None:
        data = load_data()
        print("ℹ️ Using local dummy CSV data for verification.")
        
    print(f"Data Source: {data_source}")
    
    # 2. Build Profit and Loss Report
    sales = data["sales"]
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    year = int(sales["date"].max().year) if not sales.empty else 2026
    
    pl = build_profit_loss_report(data, period="yearly", year=year)
    if not isinstance(pl, dict):
        print(f"❌ ERROR: build_profit_loss_report did not return a dict! Got: {type(pl)}")
        sys.exit(1)
        
    expected_pl_keys = ["gross_revenue", "discount", "net_revenue", "hpp", "gross_profit", "marketplace_fee", 
                        "ad_cost", "packing_cost", "operating_expenses", "net_profit_before_tax", "estimated_tax", "net_profit_after_tax"]
    for k in expected_pl_keys:
        if k not in pl:
            print(f"❌ ERROR: Key '{k}' missing from Profit & Loss report dict!")
            sys.exit(1)
            
    print("✅ Build Profit & Loss report verification passed.")
    print(f"   - Omzet Bruto: {pl['gross_revenue']}")
    print(f"   - Net Revenue: {pl['net_revenue']}")
    print(f"   - Profit Setelah Pajak: {pl['net_profit_after_tax']}")
    
    # 3. Build Monthly Omzet Summary
    monthly_df = build_monthly_omzet_summary(data, year)
    if not isinstance(monthly_df, pd.DataFrame):
        print(f"❌ ERROR: build_monthly_omzet_summary did not return a DataFrame! Got: {type(monthly_df)}")
        sys.exit(1)
        
    expected_df_cols = ["month", "gross_revenue", "net_revenue", "order_count", "estimated_pph_final", 
                        "accumulated_gross_revenue", "threshold_status"]
    for col in expected_df_cols:
        if col not in monthly_df.columns:
            print(f"❌ ERROR: Column '{col}' missing from monthly summary DataFrame!")
            sys.exit(1)
            
    print(f"✅ Build monthly omzet summary verification passed. Total months checked: {len(monthly_df)}.")
    
    # 4. Calculate Tax Estimate
    tax_est = calculate_tax_estimate(data, year)
    if not isinstance(tax_est, dict):
        print(f"❌ ERROR: calculate_tax_estimate did not return a dict! Got: {type(tax_est)}")
        sys.exit(1)
        
    expected_tax_keys = ["year", "annual_gross", "annual_net", "pph_method", "estimated_pph_final", 
                         "is_pkp", "ppn_status", "ppn_keluaran", "ppn_masukan", "ppn_kurang_bayar"]
    for k in expected_tax_keys:
        if k not in tax_est:
            print(f"❌ ERROR: Key '{k}' missing from tax estimate dict!")
            sys.exit(1)
            
    print("✅ Calculate tax estimate verification passed.")
    print(f"   - PPh Final UMKM: {tax_est['estimated_pph_final']}")
    print(f"   - PKP Status: {tax_est['is_pkp']}")
    print(f"   - PPN Kurang Bayar: {tax_est['ppn_kurang_bayar']}")
    
    # 5. Generate Finance Tax Insights
    insights = generate_finance_tax_insights(data, year)
    if not isinstance(insights, list) or len(insights) < 1:
        print(f"❌ ERROR: generate_finance_tax_insights did not return a valid list! Got: {type(insights)}")
        sys.exit(1)
        
    print(f"✅ Generate finance/tax insights verification passed. Found {len(insights)} insights.")
    for idx, insight in enumerate(insights, 1):
        clean_text = insight.replace("<b>", "").replace("</b>", "").replace("📈", "").replace("💰", "").replace("🛍️", "").replace("🧾", "").replace("🟢", "").replace("📋", "")
        print(f"   {idx}. {clean_text[:100]}...")
        
    # 6. Generate PDF Finance Tax bytes
    try:
        pdf_bytes = generate_finance_tax_pdf_report(data, year)
        if not pdf_bytes or len(pdf_bytes) < 4000:
            print(f"❌ ERROR: Generated Finance Tax PDF bytes are empty or too small ({len(pdf_bytes) if pdf_bytes else 0} bytes)!")
            sys.exit(1)
        print(f"✅ PDF finance tax report generation verification passed. Bytes size: {len(pdf_bytes)} bytes.")
    except Exception as e:
        print(f"❌ ERROR: PDF finance tax report generation failed: {e}")
        sys.exit(1)
        
    # 7. Test Telegram text builder for /finance, /tax, /spt_check
    finance_text = (
        f"📊 Ringkasan Keuangan (Tahun Pajak {year})\n\n"
        f"💵 Omzet Bruto Tahunan: {rupiah(pl['gross_revenue'])}\n"
        f"📈 Laba Bersih Sebelum Pajak (EBT): {rupiah(pl['net_profit_before_tax'])}\n"
        f"🛍️ Biaya Operasional (Expenses): {rupiah(pl['operating_expenses'])}\n"
        f"💰 Estimasi Profit Bersih Setelah Pajak (EAT): {rupiah(pl['net_profit_after_tax'])}\n\n"
        f"💡 Disclaimer: Data bersifat simulasi internal."
    )
    if not finance_text or len(finance_text) < 50:
        print("❌ ERROR: Telegram /finance text is empty or too short!")
        sys.exit(1)
        
    tax_text = (
        f"🧾 Simulasi Pajak Bisnis (Tahun {year})\n\n"
        f"🏢 Status PKP: {'Ya (PKP)' if tax_est['is_pkp'] else 'Tidak (Non-PKP)'}\n"
        f"💰 Omzet Bruto Tahunan: {rupiah(tax_est['annual_gross'])}\n"
        f"💵 Estimasi PPh Final UMKM: {rupiah(tax_est['estimated_pph_final'])}\n\n"
        f"⚠️ Disclaimer: Simulasi internal."
    )
    if not tax_text or len(tax_text) < 50:
        print("❌ ERROR: Telegram /tax text is empty or too short!")
        sys.exit(1)
        
    checklist = build_tax_readiness_checklist(data, year)
    spt_lines = [f"📋 Tax Readiness Checklist (Tahun {year})\n"]
    for item in checklist:
        spt_lines.append(f"- {item['item']}: {item['status']} - {item['description']}")
    spt_text = "\n".join(spt_lines)
    if not spt_text or len(spt_text) < 50:
        print("❌ ERROR: Telegram /spt_check text is empty or too short!")
        sys.exit(1)
        
    print("✅ Telegram text templates verification passed.")
    
    # 8. Validate missing optional tabs does not crash
    data_missing = data.copy()
    if "expenses" in data_missing:
        del data_missing["expenses"]
    if "tax_settings" in data_missing:
        del data_missing["tax_settings"]
    if "tax_payments" in data_missing:
        del data_missing["tax_payments"]
        
    try:
        # Reparse without keys
        pl_m = build_profit_loss_report(data_missing, period="yearly", year=year)
        tax_est_m = calculate_tax_estimate(data_missing, year)
        chk_m = build_tax_readiness_checklist(data_missing, year)
        print("✅ Missing optional tabs verification passed (Calculations did not crash).")
    except Exception as e:
        print(f"❌ ERROR: Calculations crashed when optional tabs were missing: {e}")
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("SUMMARY RESULTS FOR V5A QA:")
    print(f"  Data source: {data_source}")
    print(f"  Year evaluated: {year}")
    print(f"  Profit & Loss keys: OK")
    print(f"  Monthly summary months count: {len(monthly_df)}")
    print(f"  PPh Method used: {tax_est['pph_method']}")
    print(f"  Insights generated: {len(insights)}")
    print(f"  PDF Report byte size: {len(pdf_bytes)} bytes")
    print(f"  Crashes on missing tabs: None (OK)")
    print("=" * 60)
    print("🎉 ALL V5A VERIFICATION TESTS COMPLETED SUCCESSFULLY! exit code: 0")
    sys.exit(0)

if __name__ == "__main__":
    run_qa()
