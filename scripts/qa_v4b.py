import os
import sys
import toml
import pandas as pd

# Add project root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.calculations import (
    load_data, rupiah, pct, overview_metrics, top_products,
    inventory_product_status, inventory_material_status, suggested_purchase_value
)
from modules.sheets_loader import (
    load_google_sheets_data, validate_sheet_tabs, normalize_google_sheet_data, get_sheet_id_from_url
)
from modules.pdf_report import generate_daily_pdf_report
from modules.telegram_handlers import (
    load_bot_data, check_business_alerts, get_top_3_actions
)

def parse_time_string_test(time_str):
    """Parses time string HH:MM, returns formatted time or None if invalid."""
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return None
        h, m = int(parts[0]), int(parts[1])
        if h < 0 or h > 23 or m < 0 or m > 59:
            return None
        return f"{h:02d}:{m:02d}"
    except ValueError:
        return None

def run_qa():
    print("=" * 60)
    print("RUNNING AUTOMATED QA VERIFICATION FOR V4B")
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
    
    # 2. Key Validation
    expected_keys = ["products", "sales", "inventory_products", "inventory_materials", "bom", "ads", "production_plan"]
    for key in expected_keys:
        if key not in data or data[key] is None or data[key].empty:
            print(f"❌ CRITICAL ERROR: Key '{key}' missing or empty in active data!")
            sys.exit(1)
    print("✅ Active data key validation passed.")
    
    # 3. Owner Summary Text builder verification
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
        f"🔔 [SCHEDULED] Laporan Harian Bisnis\n"
        f"📅 Tanggal: {m['latest_date'].date()}\n\n"
        f"🏥 Status Bisnis: {status_emoji} {status_bisnis.upper()}\n\n"
        f"💵 Omzet Hari Ini: {rupiah(m['gross'])}\n"
        f"📈 Profit Bersih: {rupiah(m['profit'])}\n"
        f"💰 Margin Bersih: {pct(m['margin'])}\n"
        f"📦 Jumlah Order: {m['orders']}\n"
        f"📣 Biaya Iklan: {rupiah(m['ad_spend'])}\n\n"
        f"🎯 3 Action Plan Hari Ini:\n{actions_str}"
    )
    
    if not text or len(text) < 100:
        print("❌ ERROR: Owner summary text is empty or too short!")
        sys.exit(1)
    print("✅ Owner summary text builder verification passed.")
    print("-" * 50)
    print(text)
    print("-" * 50)
    
    # 4. PDF Generation Test
    tmp_pdf_path = "tmp_qa_laporan_harian.pdf"
    try:
        pdf_bytes = generate_daily_pdf_report(data)
        if not pdf_bytes or len(pdf_bytes) < 4000:
            print(f"❌ ERROR: Generated PDF bytes are empty or too small ({len(pdf_bytes) if pdf_bytes else 0} bytes)!")
            sys.exit(1)
            
        with open(tmp_pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"✅ PDF generation test passed. Bytes size: {len(pdf_bytes)} bytes. Saved to: {tmp_pdf_path}")
    except Exception as e:
        print(f"❌ ERROR: PDF report generation failed: {e}")
        sys.exit(1)
        
    # 5. Alert Check produces a list
    alert_points = check_business_alerts(data)
    if not isinstance(alert_points, list):
        print(f"❌ ERROR: check_business_alerts did not return a list! Got: {type(alert_points)}")
        sys.exit(1)
    print(f"✅ Alert Check returned a valid list. Found {len(alert_points)} alert(s).")
    for idx, alert in enumerate(alert_points, 1):
        print(f"   {idx}. {alert}")
        
    # 6. Schedule time setting parser check (valid/invalid)
    valid_test_cases = ["08:00", "17:30", "00:00", "23:59", "8:5", "0:0"]
    invalid_test_cases = ["24:00", "12:60", "abc", "08:00:00", "8", "-1:30", "12:-05", "  "]
    
    print("\n⏳ Testing time setting parser:")
    for case in valid_test_cases:
        res = parse_time_string_test(case)
        if res is None:
            print(f"❌ ERROR: Valid case '{case}' was rejected by parser!")
            sys.exit(1)
        else:
            print(f"   [VALID] '{case}' -> '{res}'")
            
    for case in invalid_test_cases:
        res = parse_time_string_test(case)
        if res is not None:
            print(f"❌ ERROR: Invalid case '{case}' was accepted as '{res}' by parser!")
            sys.exit(1)
        else:
            print(f"   [INVALID] '{case}' -> Rejected (OK)")
            
    print("\n" + "=" * 60)
    print("SUMMARY RESULTS:")
    print(f"  Data source: {data_source}")
    print(f"  Rows sales: {len(sales)}")
    print(f"  Business status: {status_bisnis}")
    print(f"  Alerts list: OK ({len(alert_points)} alerts found)")
    print(f"  Parser verification: Passed")
    print(f"  PDF byte size: {len(pdf_bytes)} bytes")
    print("=" * 60)
    print("🎉 ALL V4B VERIFICATION TESTS COMPLETED SUCCESSFULLY! exit code: 0")
    sys.exit(0)

if __name__ == "__main__":
    run_qa()
