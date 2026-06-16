import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.calculations import (
    load_data, rupiah, pct, overview_metrics, top_products,
    inventory_product_status, inventory_material_status, suggested_purchase_value
)
from modules.finance_tax import (
    build_profit_loss_report, build_monthly_omzet_summary,
    calculate_tax_estimate, build_tax_readiness_checklist,
    generate_finance_tax_insights
)
from modules.pdf_report import generate_spt_attachment_pack_pdf
import pandas as pd
import numpy as np

def run_edge_cases():
    print("Testing edge cases...")
    base_data = load_data()
    
    # Edge Case 1: Empty sales
    print("  - Testing edge case: Empty sales...")
    data_mock = base_data.copy()
    data_mock["sales"] = pd.DataFrame(columns=["date", "platform", "order_id", "sku", "product", "qty", "price", "discount", "marketplace_fee", "packing_cost", "ad_cost_allocated", "hpp", "gross_revenue", "net_revenue", "net_profit", "net_margin", "order_status"])
    pl = build_profit_loss_report(data_mock, period="yearly", year=2026)
    monthly = build_monthly_omzet_summary(data_mock, 2026)
    tax_est = calculate_tax_estimate(data_mock, 2026)
    checklist = build_tax_readiness_checklist(data_mock, 2026)
    insights = generate_finance_tax_insights(data_mock, 2026)
    pdf_bytes = generate_spt_attachment_pack_pdf(data_mock, 2026)
    assert len(pdf_bytes) > 0, "PDF generation crashed on empty sales"
    print("    OK")

    # Edge Case 2: Sales with 1 day of data
    print("  - Testing edge case: Sales with 1 day of data...")
    data_mock = base_data.copy()
    data_mock["sales"] = base_data["sales"].head(1).copy()
    pl = build_profit_loss_report(data_mock, period="yearly", year=2026)
    pdf_bytes = generate_spt_attachment_pack_pdf(data_mock, 2026)
    assert len(pdf_bytes) > 0, "PDF generation crashed on 1-day sales"
    print("    OK")

    # Edge Case 3: Empty inventory
    print("  - Testing edge case: Empty inventory...")
    data_mock = base_data.copy()
    data_mock["inventory_products"] = pd.DataFrame(columns=["sku", "product", "stock", "min_stock", "avg_daily_sold"])
    data_mock["inventory_materials"] = pd.DataFrame(columns=["material", "unit", "stock", "min_stock", "unit_cost"])
    invp = inventory_product_status(data_mock["inventory_products"])
    invm = inventory_material_status(data_mock["inventory_materials"])
    assert invp.empty, "Product status not empty"
    assert invm.empty, "Material status not empty"
    print("    OK")

    # Edge Case 4: Empty expenses & tax payments
    print("  - Testing edge case: Empty expenses and tax payments...")
    data_mock = base_data.copy()
    data_mock["expenses"] = pd.DataFrame()
    data_mock["tax_payments"] = pd.DataFrame()
    pl = build_profit_loss_report(data_mock, period="yearly", year=2026)
    tax_est = calculate_tax_estimate(data_mock, 2026)
    pdf_bytes = generate_spt_attachment_pack_pdf(data_mock, 2026)
    assert len(pdf_bytes) > 0, "PDF generation crashed on empty expenses/payments"
    print("    OK")

    # Edge Case 5: SKU Mismatch
    print("  - Testing edge case: SKU Mismatch...")
    data_mock = base_data.copy()
    # Change SKUs in sales to mismatched ones
    data_mock["sales"] = base_data["sales"].copy()
    data_mock["sales"]["sku"] = "MISMATCHED-SKU-999"
    checklist = build_tax_readiness_checklist(data_mock, 2026)
    # The checklist SKU Consistency item should warning or ready=false
    sku_item = [item for item in checklist if "SKU" in item["item"]][0]
    assert sku_item["status"] in ["Warning", "Missing"], "SKU mismatch not detected by checklist"
    print("    OK (Mismatch detected)")

    # Edge Case 6: Numeric strings with comma/dot formatting
    print("  - Testing edge case: Numeric strings with commas/dots...")
    data_mock = base_data.copy()
    if "bom" in data_mock:
        data_mock["bom_hpp"] = data_mock.pop("bom")
    data_mock["sales"] = base_data["sales"].copy()
    data_mock["sales"]["price"] = "1.000,50"  # String with formatting
    # Should not crash on loading/normalization
    from modules.sheets_loader import normalize_google_sheet_data
    normalized = normalize_google_sheet_data(data_mock)
    assert isinstance(normalized["sales"]["price"].iloc[0], (int, float)), "Price string parsing failed"
    print("    OK")

    # Edge Case 7: Invalid Dates
    print("  - Testing edge case: Invalid Dates...")
    data_mock = base_data.copy()
    if "bom" in data_mock:
        data_mock["bom_hpp"] = data_mock.pop("bom")
    data_mock["sales"] = base_data["sales"].copy()
    data_mock["sales"]["date"] = data_mock["sales"]["date"].astype(str)
    data_mock["sales"].loc[data_mock["sales"].index[0], "date"] = "tanggal-palsu-123"
    # normalize should fix date or ffill
    normalized = normalize_google_sheet_data(data_mock)
    assert not pd.isna(normalized["sales"]["date"].iloc[0]), "Invalid date fallback failed"
    print("    OK")

    print("All edge cases tests completed successfully!")

if __name__ == "__main__":
    run_edge_cases()
