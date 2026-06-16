import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.calculations import load_data
import pandas as pd

def test_health_check():
    print("Testing Data Health Check logic mocks...")
    data = load_data()
    
    # Check that expenses amount check does not crash on dummy data
    if "expenses" in data:
        expenses_df = data["expenses"]
        if "amount" in expenses_df.columns:
            bad_exp = len(expenses_df[expenses_df["amount"] <= 0])
            print(f"  - Bad expenses amount: {bad_exp} rows found")
            
        if "tax_deductible" in expenses_df.columns:
            invalid_deductible = expenses_df[
                ~expenses_df["tax_deductible"].astype(str).str.lower().isin(["true", "false", "1", "0", "yes", "no", "ya", "tidak"]) & 
                ~expenses_df["tax_deductible"].isnull()
            ]
            print(f"  - Invalid deductible flag: {len(invalid_deductible)} rows found")
            
    if "tax_payments" in data:
        payments_df = data["tax_payments"]
        if "amount" in payments_df.columns:
            bad_pay = len(payments_df[payments_df["amount"] < 0])
            print(f"  - Bad payments amount: {bad_pay} rows found")
            
    if "tax_settings" in data:
        settings_df = data["tax_settings"]
        if "key" in settings_df.columns:
            existing_keys = set(settings_df["key"].astype(str).str.strip().tolist())
            important_keys = ["business_entity", "is_pkp", "use_pph_final_umkm", "pph_final_rate", "annual_omzet_threshold", "ppn_rate", "tax_year"]
            missing_important = [k for k in important_keys if k not in existing_keys]
            print(f"  - Missing important tax keys: {missing_important}")
            
    print("Health check logic verified successfully!")

if __name__ == "__main__":
    test_health_check()
