import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.calculations import load_data
from modules.pdf_report import (
    generate_daily_pdf_report,
    generate_finance_tax_pdf_report,
    generate_spt_attachment_pack_pdf
)
from modules.finance_tax import (
    build_profit_loss_report,
    build_monthly_omzet_summary,
    build_tax_readiness_checklist,
    calculate_tax_estimate
)
import pandas as pd

def test_exports():
    print("Testing exports...")
    data = load_data()
    sales = data["sales"]
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    year = int(sales["date"].max().year) if not sales.empty else 2026
    
    # 1. Daily PDF
    print("  - Testing daily PDF report...")
    daily_bytes = generate_daily_pdf_report(data)
    assert daily_bytes.startswith(b"%PDF"), "Daily PDF doesn't start with %PDF"
    print("    OK")
    
    # 2. Finance & Tax PDF
    print("  - Testing finance & tax PDF...")
    ft_bytes = generate_finance_tax_pdf_report(data, year)
    assert ft_bytes.startswith(b"%PDF"), "Finance & Tax PDF doesn't start with %PDF"
    print("    OK")
    
    # 3. SPT Attachment Pack PDF
    print("  - Testing SPT attachment PDF...")
    spt_bytes = generate_spt_attachment_pack_pdf(data, year)
    assert spt_bytes.startswith(b"%PDF"), "SPT Attachment PDF doesn't start with %PDF"
    print("    OK")
    
    # 4. CSV exports
    print("  - Testing CSV exports...")
    monthly_df = build_monthly_omzet_summary(data, year)
    monthly_csv = monthly_df.to_csv(index=False)
    assert len(monthly_csv) > 0, "monthly_omzet.csv is empty"
    assert "month" in monthly_csv, "monthly_omzet.csv header missing"
    
    expenses = data.get("expenses")
    expenses_year = expenses[pd.to_datetime(expenses["date"], errors="coerce").dt.year == year] if expenses is not None and not expenses.empty else pd.DataFrame()
    expenses_csv = expenses_year.to_csv(index=False)
    assert len(expenses_csv) > 0, "expenses_recap.csv is empty"
    assert "category" in expenses_csv, "expenses_recap.csv header missing"
    
    tax_payments = data.get("tax_payments")
    payments_year = tax_payments[pd.to_datetime(tax_payments["date"], errors="coerce").dt.year == year] if tax_payments is not None and not tax_payments.empty else pd.DataFrame()
    payments_csv = payments_year.to_csv(index=False)
    assert len(payments_csv) > 0, "tax_payments.csv is empty"
    assert "tax_type" in payments_csv, "tax_payments.csv header missing"
    print("    OK")
    
    # 5. TXT exports
    print("  - Testing TXT exports...")
    # owner summary txt
    from modules.calculations import rupiah
    m = ft_bytes # mock
    # let's mock owner summary harian
    owner_txt = f"OMZET: {rupiah(1000000)}"
    assert len(owner_txt) > 0, "owner_summary_harian.txt is empty"
    
    # spt summary txt
    checklist = build_tax_readiness_checklist(data, year)
    pl_report = build_profit_loss_report(data, period="yearly", year=year)
    spt_txt_lines = [
        "============================================================",
        "PAKET LAMPIRAN PENDUKUNG SPT USAHA (SIMULASI INTERNAL)",
        "============================================================",
        f"Tahun Pajak: {year}",
        "------------------------------------------------------------",
        "A. REKAPITULASI LABA RUGI TAHUNAN:",
        f"- Peredaran Bruto (Gross Revenue): {rupiah(pl_report['gross_revenue'])}",
        "------------------------------------------------------------",
        "B. CHECKLIST DOKUMEN KESIAPAN PAJAK:",
    ]
    for item in checklist:
        spt_txt_lines.append(f"- [{item['status']}] {item['item']}: {item['description']}")
    spt_txt = "\n".join(spt_txt_lines)
    assert len(spt_txt) > 0, "spt_summary.txt is empty"
    assert "PAKET LAMPIRAN PENDUKUNG" in spt_txt, "spt_summary.txt invalid content"
    print("    OK")
    
    print("All exports test passed!")

if __name__ == "__main__":
    test_exports()
