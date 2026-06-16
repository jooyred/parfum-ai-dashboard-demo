import os
import sys
import toml
import pandas as pd
import io

# Add project root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.calculations import (
    load_data, rupiah, pct
)
from modules.sheets_loader import (
    load_google_sheets_data, validate_sheet_tabs, normalize_google_sheet_data, get_sheet_id_from_url
)
from modules.pdf_report import generate_spt_attachment_pack_pdf
from modules.finance_tax import (
    parse_settings, build_profit_loss_report, build_monthly_omzet_summary,
    calculate_tax_estimate, build_tax_readiness_checklist
)

def run_qa():
    print("=" * 60)
    print("RUNNING AUTOMATED QA VERIFICATION FOR V5B (SPT ATTACHMENT PACK)")
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
    
    # Verify optional tabs exist in normalized data (or are populated with defaults/dummies)
    for tab in ["expenses", "tax_settings", "tax_payments"]:
        if tab in data:
            print(f"✅ Optional tab '{tab}' is present with {len(data[tab])} rows.")
        else:
            print(f"❌ ERROR: Optional tab '{tab}' missing in normalized data!")
            sys.exit(1)

    sales = data["sales"]
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    year = int(sales["date"].max().year) if not sales.empty else 2026
    
    # 2. Build Finance Tax Report
    pl = build_profit_loss_report(data, period="yearly", year=year)
    monthly_df = build_monthly_omzet_summary(data, year)
    tax_est = calculate_tax_estimate(data, year)
    checklist = build_tax_readiness_checklist(data, year)
    
    print("✅ Finance & Tax reports built successfully.")
    
    # 3. Generate SPT Attachment PDF Bytes
    try:
        pdf_bytes = generate_spt_attachment_pack_pdf(data, year)
        if not pdf_bytes or len(pdf_bytes) < 4000:
            print(f"❌ ERROR: Generated SPT Attachment PDF is empty or too small ({len(pdf_bytes) if pdf_bytes else 0} bytes)!")
            sys.exit(1)
        print(f"✅ SPT Attachment PDF generated successfully. Size: {len(pdf_bytes)} bytes.")
    except Exception as e:
        print(f"❌ ERROR: Failed to generate SPT Attachment PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    # 4. Generate Monthly Omzet CSV bytes/string
    try:
        monthly_csv_str = monthly_df.to_csv(index=False)
        monthly_csv_bytes = monthly_csv_str.encode('utf-8')
        if not monthly_csv_bytes:
            print("❌ ERROR: Monthly Omzet CSV is empty!")
            sys.exit(1)
        print("✅ Monthly Omzet CSV generated successfully.")
    except Exception as e:
        print(f"❌ ERROR: Failed to generate Monthly Omzet CSV: {e}")
        sys.exit(1)
        
    # 5. Generate Expenses Recap CSV bytes/string
    try:
        expenses = data.get("expenses")
        expenses_year = expenses[pd.to_datetime(expenses["date"], errors="coerce").dt.year == year] if expenses is not None and not expenses.empty else pd.DataFrame()
        expenses_csv_str = expenses_year.to_csv(index=False)
        expenses_csv_bytes = expenses_csv_str.encode('utf-8')
        print(f"✅ Expenses Recap CSV generated successfully ({len(expenses_csv_bytes)} bytes).")
    except Exception as e:
        print(f"❌ ERROR: Failed to generate Expenses Recap CSV: {e}")
        sys.exit(1)
        
    # 6. Generate Tax Payments Recap CSV bytes/string
    try:
        tax_payments = data.get("tax_payments")
        payments_year = tax_payments[pd.to_datetime(tax_payments["date"], errors="coerce").dt.year == year] if tax_payments is not None and not tax_payments.empty else pd.DataFrame()
        payments_csv_str = payments_year.to_csv(index=False)
        payments_csv_bytes = payments_csv_str.encode('utf-8')
        print(f"✅ Tax Payments CSV generated successfully ({len(payments_csv_bytes)} bytes).")
    except Exception as e:
        print(f"❌ ERROR: Failed to generate Tax Payments CSV: {e}")
        sys.exit(1)
        
    # 7. Test Telegram /spt_pack text/PDF builder mock
    try:
        # Check that the import works
        from modules.telegram_handlers import spt_pack_command, spt_check_command
        print("✅ Telegram bot command handlers imported successfully.")
    except Exception as e:
        print(f"❌ ERROR: Failed to import Telegram handlers: {e}")
        sys.exit(1)
        
    # 8. Test missing optional tabs does not crash
    data_missing = data.copy()
    data_missing["expenses"] = pd.DataFrame()
    data_missing["tax_settings"] = pd.DataFrame()
    data_missing["tax_payments"] = pd.DataFrame()
    
    try:
        pl_m = build_profit_loss_report(data_missing, period="yearly", year=year)
        monthly_m = build_monthly_omzet_summary(data_missing, year)
        tax_est_m = calculate_tax_estimate(data_missing, year)
        chk_m = build_tax_readiness_checklist(data_missing, year)
        
        pdf_bytes_m = generate_spt_attachment_pack_pdf(data_missing, year)
        if not pdf_bytes_m or len(pdf_bytes_m) < 4000:
            print("❌ ERROR: Generated SPT Attachment PDF is empty or too small when optional tabs are missing!")
            sys.exit(1)
            
        print("✅ Missing optional tabs verification passed (Calculations and PDF generation did not crash).")
    except Exception as e:
        print(f"❌ ERROR: Calculations or PDF generation crashed when optional tabs were missing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("SUMMARY RESULTS FOR V5B QA:")
    print(f"  Data source: {data_source}")
    print(f"  Year evaluated: {year}")
    print(f"  PDF Report byte size: {len(pdf_bytes)} bytes")
    print(f"  Monthly Omzet CSV size: {len(monthly_csv_bytes)} bytes")
    print(f"  Expenses Recap CSV size: {len(expenses_csv_bytes)} bytes")
    print(f"  Tax Payments CSV size: {len(payments_csv_bytes)} bytes")
    print(f"  Crashes on missing tabs: None (OK)")
    print("=" * 60)
    print("🎉 ALL V5B VERIFICATION TESTS COMPLETED SUCCESSFULLY! exit code: 0")
    sys.exit(0)

if __name__ == "__main__":
    run_qa()
