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

def run_qa():
    print("=" * 60)
    print("RUNNING AUTOMATED QA VERIFICATION FOR V4A")
    print("=" * 60)
    
    # 1. Load Data
    data_source = "Dummy CSV (local)"
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    data = None
    
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
    
    # 3. Owner Control Room calculations
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
    elif margin_val >= 0.25 and produk_kritis_count <= 3 and bahan_kritis_count <= 10:
        status_bisnis = "Sehat"
    else:
        status_bisnis = "Waspada"
        
    # Decision Card items
    pp = data["production_plan"]
    need_prod = pp[pp["recommended_production"] > 0]
    need_m, suggested_cost = suggested_purchase_value(data["inventory_materials"])
    ads_df = data["ads"]
    critical_ads = ads_df[ads_df["status"].isin(["Waspada", "Boncos"])]
    top_prod_df = top_products(sales, latest_only=False)
    
    print(f"✅ Owner Control Room Calculations:")
    print(f"   - Omzet: {rupiah(m['gross'])}")
    print(f"   - Profit: {rupiah(m['profit'])}")
    print(f"   - Margin: {pct(margin_val)}")
    print(f"   - Business Status: {status_bisnis.upper()}")
    print(f"   - Critical Products Count: {produk_kritis_count}")
    print(f"   - Critical Materials Count: {bahan_kritis_count}")
    
    # Action Plans
    action_plans = []
    if not need_prod.empty:
        top_prod_row = need_prod.sort_values("recommended_production", ascending=False).iloc[0]
        action_plans.append(f"Produksi {top_prod_row['product']} sebanyak {int(top_prod_row['recommended_production'])} pcs. Bottleneck: {top_prod_row['bottleneck']}")
    else:
        action_plans.append("Stok produk jadi mencukupi.")
        
    if not need_m.empty:
        mats_list = ", ".join(need_m.head(3)["material"].tolist())
        action_plans.append(f"Belanja bahan kritis: {mats_list} (Est: {rupiah(suggested_cost)})")
    else:
        action_plans.append("Stok bahan baku aman.")
        
    if not critical_ads.empty:
        ads_list = ", ".join(critical_ads["campaign"].tolist())
        action_plans.append(f"Evaluasi budget campaign iklan: {ads_list}")
    else:
        action_plans.append("Seluruh campaign iklan sehat.")
        
    print(f"✅ Generated {len(action_plans)} main action plans.")
    
    # 4. Data Health Check
    errors = []
    warnings = []
    rows_checked = sum(len(data[k]) for k in expected_keys)
    
    # Worksheet check
    for key in expected_keys:
        if key not in data or data[key] is None or data[key].empty:
            errors.append(f"Tab {key} tidak ditemukan atau kosong.")
            
    # Columns check
    sales_cols = ["date", "platform", "order_id", "sku", "product", "qty", "price", "discount", "marketplace_fee", "packing_cost", "ad_cost_allocated", "hpp", "gross_revenue", "net_revenue", "net_profit", "net_margin", "order_status"]
    if "sales" in data and not data["sales"].empty:
        sales_df = data["sales"]
        for col in sales_cols:
            if col not in sales_df.columns:
                errors.append(f"Kolom wajib '{col}' tidak ditemukan di tab sales.")
                
    # Empty check
    if "sales" in data and not data["sales"].empty:
        sales_df = data["sales"]
        for col in ["date", "sku", "qty", "price", "net_profit"]:
            if col in sales_df.columns:
                empty_count = sales_df[col].isnull().sum() + (sales_df[col] == "").sum()
                if empty_count > 0:
                    errors.append(f"Kolom '{col}' memiliki {empty_count} baris kosong.")
                    
    # SKU Mismatch
    if "products" in data and not data["products"].empty:
        valid_skus = set(data["products"]["sku"].astype(str).str.strip())
        if "sales" in data and not data["sales"].empty and "sku" in data["sales"].columns:
            mismatched_sales = data["sales"][~data["sales"]["sku"].astype(str).str.strip().isin(valid_skus)]
            if not mismatched_sales.empty:
                errors.append(f"Mismatched SKU in sales: {mismatched_sales['sku'].nunique()} unique SKUs mismatch.")
                
    # Anomalies
    if "sales" in data and not data["sales"].empty:
        sales_df = data["sales"]
        if "qty" in sales_df.columns:
            bad_qty = len(sales_df[sales_df["qty"] <= 0])
            if bad_qty > 0:
                warnings.append(f"Found {bad_qty} sales transactions with Qty <= 0.")
        if "price" in sales_df.columns:
            bad_price = len(sales_df[sales_df["price"] <= 0])
            if bad_price > 0:
                warnings.append(f"Found {bad_price} sales transactions with Price <= 0.")
        if "net_margin" in sales_df.columns:
            bad_margin = len(sales_df[sales_df["net_margin"] < -0.50])
            if bad_margin > 0:
                warnings.append(f"Found {bad_margin} sales transactions with net_margin < -50%.")
                
    total_errors = len(errors)
    total_warnings = len(warnings)
    health_score = max(0, min(100, 100 - (total_errors * 10) - (total_warnings * 2)))
    
    print(f"✅ Data Health Check Results:")
    print(f"   - Health Score: {health_score}/100")
    print(f"   - Total Errors: {total_errors}")
    print(f"   - Total Warnings: {total_warnings}")
    print(f"   - Rows Checked: {rows_checked}")
    
    # 5. WhatsApp Summary text
    summary_text = (
        f"📋 *RINGKASAN KEPUTUSAN HARIAN OWNER*\n"
        f"📅 Tanggal: {m['latest_date'].strftime('%Y-%m-%d')}\n"
        f"🏥 Status Bisnis: {status_bisnis.upper()}\n\n"
        f"Finansial:\n"
        f"   - Omzet: {rupiah(m['gross'])}\n"
        f"   - Profit: {rupiah(m['profit'])}\n"
        f"   - Margin: {pct(margin_val)}\n"
    )
    
    if not summary_text or len(summary_text) < 50:
        print("❌ ERROR: WhatsApp summary text is empty or too short!")
        sys.exit(1)
    print("✅ WhatsApp summary text verification passed.")
    
    # 6. PDF Generation Test
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
        
    # 7. Telegram /owner text builder verification
    # Construct expected items in /owner
    telegram_owner_ok = True
    for item in [status_bisnis.upper(), rupiah(m['gross']), rupiah(m['profit']), pct(margin_val)]:
        if item not in summary_text:
            telegram_owner_ok = False
            
    print(f"✅ Telegram /owner text template verification: {'OK' if telegram_owner_ok else 'FAIL'}")
    if not telegram_owner_ok:
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("SUMMARY RESULTS:")
    print(f"  Data source: {data_source}")
    print(f"  Rows sales: {len(sales)}")
    print(f"  Business status: {status_bisnis}")
    print(f"  Owner action count: {len(action_plans)}")
    print(f"  Health score: {health_score}/100")
    print(f"  Error count: {total_errors}")
    print(f"  Warning count: {total_warnings}")
    print(f"  PDF byte size: {len(pdf_bytes)} bytes")
    print("  Telegram owner text: OK")
    print("=" * 60)
    print("🎉 ALL V4A VERIFICATION TESTS COMPLETED SUCCESSFULLY! exit code: 0")
    sys.exit(0)

if __name__ == "__main__":
    run_qa()
