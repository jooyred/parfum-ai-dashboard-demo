import re
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def get_sheet_id_from_url(url_or_id: str) -> str:
    """Extract Google Sheet ID from a full URL or return it if it is already an ID."""
    url_or_id = str(url_or_id).strip()
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url_or_id)
    if match:
        return match.group(1)
    return url_or_id

def load_google_sheets_data(spreadsheet_id: str, credentials_info: dict) -> dict:
    """Connect to Google Sheets API and read all required worksheets."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open the spreadsheet
    spreadsheet = client.open_by_key(spreadsheet_id)
    
    # Required and optional worksheets/tabs
    tabs = ["products", "sales", "inventory_products", "inventory_materials", "bom_hpp", "ads", "production_plan", "expenses", "tax_settings", "tax_payments"]
    data = {}
    
    # Get all worksheets
    worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}
    
    for tab in tabs:
        if tab in worksheets:
            try:
                # Try getting all records (standard header format)
                records = worksheets[tab].get_all_records()
                data[tab] = pd.DataFrame(records)
            except Exception:
                try:
                    # Fallback if get_all_records fails
                    vals = worksheets[tab].get_all_values()
                    if len(vals) > 0:
                        headers = vals[0]
                        rows = vals[1:]
                        data[tab] = pd.DataFrame(rows, columns=headers)
                    else:
                        data[tab] = pd.DataFrame()
                except Exception:
                    data[tab] = pd.DataFrame()
        else:
            data[tab] = pd.DataFrame()
            
    return data

def validate_sheet_tabs(data: dict) -> tuple[bool, list[str]]:
    """Verify that all required tabs exist in the loaded data and contain columns/rows."""
    required_tabs = ["products", "sales", "inventory_products", "inventory_materials", "bom_hpp", "ads", "production_plan"]
    missing = []
    for tab in required_tabs:
        if tab not in data or data[tab].empty or len(data[tab].columns) == 0:
            missing.append(tab)
    return (len(missing) == 0, missing)

def normalize_google_sheet_data(data: dict) -> dict:
    """Parse dates, enforce types, and check mandatory columns, mapping bom_hpp to bom."""
    normalized = {}
    
    required_cols = {
        "products": ["sku", "product", "size", "category", "price", "hpp", "target_margin"],
        "sales": ["date", "platform", "order_id", "sku", "product", "qty", "price", "discount", "marketplace_fee", "packing_cost", "ad_cost_allocated", "hpp", "gross_revenue", "net_revenue", "net_profit", "net_margin", "order_status"],
        "inventory_products": ["sku", "product", "stock", "min_stock", "avg_daily_sold"],
        "inventory_materials": ["material", "unit", "stock", "min_stock", "unit_cost"],
        "bom_hpp": ["sku", "component", "unit", "qty_usage", "component_cost"],
        "ads": ["platform", "campaign", "spend", "revenue", "orders", "roas", "status"],
        "production_plan": ["sku", "product", "demand_7d", "stock", "recommended_production", "bottleneck"],
        "expenses": ["date", "category", "description", "amount", "payment_method", "vendor", "tax_deductible", "notes"],
        "tax_settings": ["key", "value", "notes"],
        "tax_payments": ["date", "tax_type", "period", "amount", "payment_ref", "notes"]
    }
    
    numeric_cols = {
        "products": ["price", "hpp", "target_margin"],
        "sales": ["qty", "price", "discount", "marketplace_fee", "packing_cost", "ad_cost_allocated", "hpp", "gross_revenue", "net_revenue", "net_profit", "net_margin"],
        "inventory_products": ["stock", "min_stock", "avg_daily_sold"],
        "inventory_materials": ["stock", "min_stock", "unit_cost"],
        "bom_hpp": ["qty_usage", "component_cost"],
        "ads": ["spend", "revenue", "orders", "roas"],
        "production_plan": ["demand_7d", "stock", "recommended_production"],
        "expenses": ["amount"],
        "tax_settings": [],
        "tax_payments": ["amount"]
    }
    
    import os
    from pathlib import Path
    local_data_dir = Path(__file__).resolve().parent.parent / "data"
    
    for tab, df in data.items():
        if df is None or df.empty:
            local_file = local_data_dir / f"{tab}.csv" if tab != "bom_hpp" else local_data_dir / "bom_hpp.csv"
            if local_file.exists():
                try:
                    if tab in ["sales", "expenses", "tax_payments"]:
                        df = pd.read_csv(local_file, parse_dates=["date"])
                    else:
                        df = pd.read_csv(local_file)
                except Exception:
                    df = pd.DataFrame(columns=required_cols[tab])
            else:
                if tab == "tax_settings":
                    df = pd.DataFrame([
                        {"key": "business_entity", "value": "orang_pribadi_umkm", "notes": ""},
                        {"key": "is_pkp", "value": "false", "notes": ""},
                        {"key": "pph_final_rate", "value": "0.005", "notes": ""},
                        {"key": "annual_omzet_threshold", "value": "4800000000", "notes": ""},
                        {"key": "ppn_rate", "value": "0.12", "notes": ""},
                        {"key": "use_pph_final_umkm", "value": "true", "notes": ""},
                        {"key": "disclaimer", "value": "Estimasi pajak bersifat simulasi internal", "notes": ""}
                    ])
                else:
                    df = pd.DataFrame(columns=required_cols[tab])
            
        # Ensure all columns are present (fill with defaults if missing)
        for col in required_cols[tab]:
            if col not in df.columns:
                df[col] = 0 if col in numeric_cols[tab] else ""
                
        # Parse dates in date-carrying tabs
        if tab == "sales":
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            if df["date"].isnull().any():
                df["date"] = df["date"].ffill().bfill().fillna(pd.Timestamp.today())
        elif tab in ["expenses", "tax_payments"]:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            
        # Safe type conversion for numeric columns
        for col in numeric_cols[tab]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            
        # Reorder to standard columns and copy
        df = df[required_cols[tab]].copy()
        
        normalized[tab] = df
        
    # Map bom_hpp worksheet to the calculations key 'bom'
    if "bom_hpp" in normalized:
        normalized["bom"] = normalized.pop("bom_hpp")
        
    return normalized
