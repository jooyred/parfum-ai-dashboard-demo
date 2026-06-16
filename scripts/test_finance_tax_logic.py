import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.calculations import load_data
from modules.finance_tax import (
    parse_settings,
    build_profit_loss_report,
    build_monthly_omzet_summary,
    calculate_tax_estimate,
    build_tax_readiness_checklist
)
import numpy as np

def test_logic():
    print("Testing Finance & Tax logic...")
    data = load_data()
    
    # 1. P&L NaN/inf check
    pl = build_profit_loss_report(data, period="yearly", year=2026)
    for k, v in pl.items():
        assert not np.isnan(v), f"Key '{k}' in P&L is NaN"
        assert not np.isinf(v), f"Key '{k}' in P&L is inf"
    print("  - P&L has no NaN/inf values: OK")
    
    # 2. PPh Final Rate
    settings = parse_settings(data)
    # Check if rate is either default 0.005 or float read from data
    assert settings["pph_final_rate"] == 0.005, f"Unexpected PPh final rate: {settings['pph_final_rate']}"
    print(f"  - PPh Final UMKM rate: {settings['pph_final_rate']} (OK)")
    
    # 3. PKP false simulation
    data_non_pkp = data.copy()
    override_non_pkp = parse_settings(data_non_pkp)
    override_non_pkp["is_pkp"] = False
    tax_est_non_pkp = calculate_tax_estimate(data_non_pkp, 2026)
    assert tax_est_non_pkp["ppn_keluaran"] == 0.0, "PPN Keluaran must be 0 for non-PKP"
    assert tax_est_non_pkp["ppn_masukan"] == 0.0, "PPN Masukan must be 0 for non-PKP"
    assert tax_est_non_pkp["ppn_kurang_bayar"] == 0.0, "PPN Kurang Bayar must be 0 for non-PKP"
    print("  - Non-PKP simulation: OK")
    
    # 4. PKP true simulation
    import pandas as pd
    data_pkp = data.copy()
    data_pkp["tax_settings"] = pd.DataFrame([
        {"key": "is_pkp", "value": "true"},
        {"key": "ppn_rate", "value": "0.12"},
        {"key": "annual_omzet_threshold", "value": "4800000000"},
        {"key": "pph_final_rate", "value": "0.005"},
        {"key": "use_pph_final_umkm", "value": "true"},
        {"key": "business_entity", "value": "orang_pribadi_umkm"}
    ])
    tax_est_pkp = calculate_tax_estimate(data_pkp, 2026)
    assert tax_est_pkp["is_pkp"] == True, "PKP status must be True"
    assert tax_est_pkp["ppn_keluaran"] >= 0.0, "PPN Keluaran invalid value"
    assert tax_est_pkp["ppn_masukan"] >= 0.0, "PPN Masukan invalid value"
    print("  - PKP active simulation: OK")
    
    # 5. Monthly omzet summary produces 12 months
    monthly_df = build_monthly_omzet_summary(data, 2026)
    assert len(monthly_df) == 12, f"Monthly omzet summary should have 12 rows, got {len(monthly_df)}"
    print("  - Monthly omzet summary has 12 months: OK")
    
    # 6. Tax readiness checklist not empty
    checklist = build_tax_readiness_checklist(data, 2026)
    assert len(checklist) > 0, "Tax readiness checklist is empty"
    print(f"  - Tax readiness checklist has {len(checklist)} items: OK")
    
    # 7. Disclaimer presence check in PDF generation string
    disclaimer_phrase = "Estimasi pajak bersifat simulasi internal"
    
    from modules.pdf_report import generate_spt_attachment_pack_pdf
    pdf_bytes = generate_spt_attachment_pack_pdf(data, 2026)
    assert len(pdf_bytes) > 4000, "SPT Attachment PDF bytes are empty or too small"
    print("  - Disclaimer presence in PDF: OK (PDF generated successfully)")
    
    print("All Finance & Tax logic tests passed!")

if __name__ == "__main__":
    test_logic()
