
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def load_data():
    return {
        "products": pd.read_csv(DATA_DIR / "products.csv"),
        "sales": pd.read_csv(DATA_DIR / "sales.csv", parse_dates=["date"]),
        "inventory_products": pd.read_csv(DATA_DIR / "inventory_products.csv"),
        "inventory_materials": pd.read_csv(DATA_DIR / "inventory_materials.csv"),
        "bom": pd.read_csv(DATA_DIR / "bom_hpp.csv"),
        "ads": pd.read_csv(DATA_DIR / "ads.csv"),
        "production_plan": pd.read_csv(DATA_DIR / "production_plan.csv"),
    }

def rupiah(value):
    try:
        value = float(value)
    except Exception:
        return "Rp0"
    return "Rp{:,.0f}".format(value).replace(",", ".")

def pct(value):
    try:
        return "{:.1f}%".format(float(value) * 100).replace(".", ",")
    except Exception:
        return "0,0%"

def status_stock(stock, min_stock):
    if stock <= min_stock:
        return "Kritis"
    if stock <= min_stock * 1.5:
        return "Rendah"
    return "Aman"

def status_badge(status):
    status_lower = str(status).strip().lower()
    bg_color = "#e2e8f0"
    text_color = "#475569"
    
    if status_lower in ["aman", "sehat", "completed", "complete"]:
        bg_color = "#d1fae5"  # Emerald 100
        text_color = "#065f46"  # Emerald 800
    elif status_lower in ["rendah", "waspada"]:
        bg_color = "#fef3c7"  # Amber 100
        text_color = "#92400e"  # Amber 800
    elif status_lower in ["kritis", "boncos", "returned"]:
        bg_color = "#fee2e2"  # Red 100
        text_color = "#991b1b"  # Red 800
    elif status_lower in ["shipped"]:
        bg_color = "#dbeafe"  # Blue 100
        text_color = "#1e40af"  # Blue 800
        
    return f'<span style="background-color: {bg_color}; color: {text_color}; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; display: inline-block; border: 1px solid rgba(0,0,0,0.05);">{status}</span>'

def overview_metrics(sales):
    latest_date = sales["date"].max()
    today = sales[sales["date"] == latest_date]
    yesterday = sales[sales["date"] == latest_date - pd.Timedelta(days=1)]
    gross = today["gross_revenue"].sum()
    profit = today["net_profit"].sum()
    margin = profit / gross if gross else 0
    orders = today["order_id"].nunique()
    ad_spend = today["ad_cost_allocated"].sum()
    gross_y = yesterday["gross_revenue"].sum()
    profit_y = yesterday["net_profit"].sum()
    orders_y = yesterday["order_id"].nunique()
    ad_y = yesterday["ad_cost_allocated"].sum()
    def change(now, prev):
        return 0 if prev == 0 else (now - prev) / prev
    return {
        "latest_date": latest_date,
        "gross": gross,
        "profit": profit,
        "margin": margin,
        "orders": orders,
        "ad_spend": ad_spend,
        "gross_change": change(gross, gross_y),
        "profit_change": change(profit, profit_y),
        "orders_change": change(orders, orders_y),
        "ad_change": change(ad_spend, ad_y),
    }

def top_products(sales, latest_only=True):
    df = sales.copy()
    if latest_only:
        df = df[df["date"] == df["date"].max()]
    grouped = df.groupby(["sku", "product"], as_index=False).agg(
        terjual=("qty", "sum"),
        omzet=("gross_revenue", "sum"),
        profit=("net_profit", "sum")
    )
    grouped["margin"] = grouped["profit"] / grouped["omzet"]
    return grouped.sort_values("omzet", ascending=False)

def trend_daily(sales):
    return sales.groupby("date", as_index=False).agg(
        Omzet=("gross_revenue", "sum"),
        Profit=("net_profit", "sum")
    ).sort_values("date")

def platform_revenue(sales):
    latest = sales[sales["date"] == sales["date"].max()]
    return latest.groupby("platform", as_index=False).agg(omzet=("gross_revenue", "sum")).sort_values("omzet", ascending=False)

def product_mix(sales):
    latest = sales[sales["date"] == sales["date"].max()]
    return latest.groupby("product", as_index=False).agg(omzet=("gross_revenue", "sum")).sort_values("omzet", ascending=False)

def inventory_product_status(inv):
    df = inv.copy()
    df["estimasi_hari_habis"] = (df["stock"] / df["avg_daily_sold"]).round(1)
    df["status"] = df.apply(lambda r: status_stock(r["stock"], r["min_stock"]), axis=1)
    return df

def inventory_material_status(materials):
    df = materials.copy()
    df["status"] = df.apply(lambda r: status_stock(r["stock"], r["min_stock"]), axis=1)
    return df

def suggested_purchase_value(materials):
    df = inventory_material_status(materials)
    need = df[df["status"].isin(["Kritis", "Rendah"])].copy()
    need["recommended_qty"] = (need["min_stock"] * 1.5 - need["stock"]).clip(lower=0)
    need["estimated_cost"] = need["recommended_qty"] * need["unit_cost"]
    return need, need["estimated_cost"].sum()

def daily_report(data):
    sales = data["sales"]
    invp = inventory_product_status(data["inventory_products"])
    invm = inventory_material_status(data["inventory_materials"])
    ads = data["ads"]
    prod_plan = data["production_plan"]
    m = overview_metrics(sales)
    top = top_products(sales, latest_only=True).head(3)
    critical_products = invp[invp["status"] == "Kritis"]
    critical_materials = invm[invm["status"] == "Kritis"]
    boncos = ads[ads["status"] == "Boncos"]
    lines = []
    lines.append("Laporan Harian Bisnis Parfum")
    lines.append(f"Tanggal: {m['latest_date'].date()}")
    lines.append("")
    lines.append("Ringkasan:")
    lines.append(f"- Omzet: {rupiah(m['gross'])}")
    lines.append(f"- Order: {m['orders']}")
    lines.append(f"- Profit bersih: {rupiah(m['profit'])}")
    lines.append(f"- Margin bersih: {pct(m['margin'])}")
    lines.append(f"- Estimasi biaya iklan/order teralokasi: {rupiah(m['ad_spend'])}")
    lines.append(f"- Produk stok kritis: {len(critical_products)} SKU")
    lines.append(f"- Bahan kritis: {len(critical_materials)} item")
    lines.append("")
    lines.append("Produk terlaris hari ini:")
    for i, row in enumerate(top.itertuples(index=False), start=1):
        lines.append(f"{i}. {row.product} - {int(row.terjual)} pcs - omzet {rupiah(row.omzet)} - profit {rupiah(row.profit)}")
    lines.append("")
    lines.append("Alert:")
    for row in critical_products.head(3).itertuples(index=False):
        lines.append(f"- {row.product}: stok {int(row.stock)} pcs, estimasi habis {row.estimasi_hari_habis} hari.")
    for row in critical_materials.head(3).itertuples(index=False):
        lines.append(f"- {row.material}: stok {row.stock} {row.unit}, minimum {row.min_stock} {row.unit}.")
    if not boncos.empty:
        lines.append(f"- Campaign iklan perlu evaluasi: {', '.join(boncos['campaign'].tolist())}.")
    lines.append("")
    lines.append("Rekomendasi produksi:")
    for row in prod_plan[prod_plan["recommended_production"] > 0].head(3).itertuples(index=False):
        lines.append(f"- Produksi {row.product} minimal {int(row.recommended_production)} pcs. Bottleneck: {row.bottleneck}.")
    return "\n".join(lines)
