import pandas as pd
import numpy as np

def parse_settings(data):
    """Helper to parse tax settings dataframe into a dictionary with typed values."""
    default_settings = {
        "business_entity": "orang_pribadi_umkm",
        "is_pkp": False,
        "pph_final_rate": 0.005,
        "annual_omzet_threshold": 4800000000.0,
        "ppn_rate": 0.12,
        "use_pph_final_umkm": True
    }
    
    tax_settings = data.get("tax_settings")
    if tax_settings is None or tax_settings.empty:
        return default_settings
        
    settings = {}
    for _, row in tax_settings.iterrows():
        key = str(row.get("key", "")).strip()
        val = str(row.get("value", "")).strip().lower()
        if not key:
            continue
            
        if key in ["is_pkp", "use_pph_final_umkm"]:
            settings[key] = val in ["true", "1", "yes", "ya"]
        elif key in ["pph_final_rate", "annual_omzet_threshold", "ppn_rate"]:
            try:
                settings[key] = float(val)
            except ValueError:
                settings[key] = default_settings[key]
        else:
            settings[key] = row.get("value", "")
            
    # Fill missing keys with defaults
    for k, v in default_settings.items():
        if k not in settings:
            settings[k] = v
            
    return settings

def build_profit_loss_report(data, period="yearly", year=None, month=None):
    """
    Build Profit and Loss Report.
    period: 'daily', 'monthly', 'yearly'
    year: filter year (int)
    month: filter month (int)
    """
    sales = data.get("sales")
    if sales is None or sales.empty:
        sales = pd.DataFrame(columns=["date", "gross_revenue", "discount", "net_revenue", "hpp", "marketplace_fee", "ad_cost_allocated", "packing_cost", "order_id"])
    else:
        sales = sales.copy()
        
    expenses = data.get("expenses")
    if expenses is None or expenses.empty:
        expenses = pd.DataFrame(columns=["date", "category", "description", "amount", "payment_method", "vendor", "tax_deductible", "notes"])
    else:
        expenses = expenses.copy()
    
    # Ensure datetime format
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    if "date" in expenses.columns:
        expenses["date"] = pd.to_datetime(expenses["date"], errors="coerce")
    else:
        expenses["date"] = pd.NaT

    # Determine default year/month if not provided
    if year is None:
        if not sales.empty:
            year = int(sales["date"].max().year)
        else:
            year = pd.Timestamp.today().year
            
    if period == "monthly" and month is None:
        if not sales.empty:
            month = int(sales[sales["date"].dt.year == year]["date"].max().month)
            if pd.isna(month):
                month = pd.Timestamp.today().month
        else:
            month = pd.Timestamp.today().month

    # Filter Sales
    if year is not None:
        sales = sales[sales["date"].dt.year == year]
    if period == "monthly" and month is not None:
        sales = sales[sales["date"].dt.month == month]
    elif period == "daily":
        # Filter for latest day in the selected year/month, or today
        if not sales.empty:
            latest_day = sales["date"].max()
            sales = sales[sales["date"] == latest_day]
            
    # Filter Expenses
    if not expenses.empty and "date" in expenses.columns:
        expenses = expenses[expenses["date"].dt.year == year]
        if period == "monthly" and month is not None:
            expenses = expenses[expenses["date"].dt.month == month]
        elif period == "daily" and not sales.empty:
            expenses = expenses[expenses["date"].dt.date == latest_day.date()]

    # Calculations
    gross_revenue = float(sales["gross_revenue"].sum()) if not sales.empty else 0.0
    discount = float(sales["discount"].sum()) if not sales.empty else 0.0
    net_revenue = float(sales["net_revenue"].sum()) if not sales.empty else 0.0
    hpp = float(sales["hpp"].sum()) if not sales.empty else 0.0
    gross_profit = net_revenue - hpp
    
    marketplace_fee = float(sales["marketplace_fee"].sum()) if not sales.empty else 0.0
    ad_cost = float(sales["ad_cost_allocated"].sum()) if not sales.empty else 0.0
    packing_cost = float(sales["packing_cost"].sum()) if not sales.empty else 0.0
    
    operating_expenses = float(expenses["amount"].sum()) if not expenses.empty else 0.0
    
    net_profit_before_tax = gross_profit - (marketplace_fee + ad_cost + packing_cost + operating_expenses)
    
    # Estimate tax for this period
    settings = parse_settings(data)
    if settings["use_pph_final_umkm"]:
        # PPh Final is based on gross revenue
        estimated_tax = gross_revenue * settings["pph_final_rate"]
    else:
        # Standard PPh simulation (e.g. 22% of net profit before tax, min 0)
        estimated_tax = max(0.0, net_profit_before_tax * 0.22)
        
    net_profit_after_tax = net_profit_before_tax - estimated_tax
    
    return {
        "gross_revenue": gross_revenue,
        "discount": discount,
        "net_revenue": net_revenue,
        "hpp": hpp,
        "gross_profit": gross_profit,
        "marketplace_fee": marketplace_fee,
        "ad_cost": ad_cost,
        "packing_cost": packing_cost,
        "operating_expenses": operating_expenses,
        "net_profit_before_tax": net_profit_before_tax,
        "estimated_tax": estimated_tax,
        "net_profit_after_tax": net_profit_after_tax
    }

def build_monthly_omzet_summary(data, year):
    """
    Build monthly summary for a specific year, including cumulative omzet and threshold checks.
    """
    sales = data.get("sales")
    if sales is None or sales.empty:
        sales = pd.DataFrame(columns=["date", "gross_revenue", "net_revenue", "order_id"])
    else:
        sales = sales.copy()
        
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    sales = sales[sales["date"].dt.year == year]
    
    settings = parse_settings(data)
    pph_rate = settings["pph_final_rate"]
    threshold = settings["annual_omzet_threshold"]
    
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
              
    records = []
    accumulated_gross = 0.0
    
    for m_idx in range(1, 13):
        m_sales = sales[sales["date"].dt.month == m_idx]
        
        gross = float(m_sales["gross_revenue"].sum()) if not m_sales.empty else 0.0
        net = float(m_sales["net_revenue"].sum()) if not m_sales.empty else 0.0
        orders = int(m_sales["order_id"].nunique()) if not m_sales.empty else 0
        
        pph = gross * pph_rate if settings["use_pph_final_umkm"] else 0.0
        accumulated_gross += gross
        
        # Determine status
        if accumulated_gross > threshold:
            status = "Melebihi Threshold"
        elif accumulated_gross >= threshold * 0.8:
            status = "Waspada"
        else:
            status = "Aman"
            
        records.append({
            "month_num": m_idx,
            "month": months[m_idx - 1],
            "gross_revenue": gross,
            "net_revenue": net,
            "order_count": orders,
            "estimated_pph_final": pph,
            "accumulated_gross_revenue": accumulated_gross,
            "threshold_status": status
        })
        
    return pd.DataFrame(records)

def calculate_tax_estimate(data, year):
    """
    Simulates PPh and PPN based on tax settings.
    """
    sales = data.get("sales")
    if sales is None or sales.empty:
        sales = pd.DataFrame(columns=["date", "gross_revenue", "net_revenue"])
    else:
        sales = sales.copy()
        
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    sales = sales[sales["date"].dt.year == year]
    
    expenses = data.get("expenses")
    if expenses is None or expenses.empty:
        expenses = pd.DataFrame(columns=["date", "category", "description", "amount", "payment_method", "vendor", "tax_deductible", "notes"])
    else:
        expenses = expenses.copy()
        
    if not expenses.empty and "date" in expenses.columns:
        expenses["date"] = pd.to_datetime(expenses["date"], errors="coerce")
        expenses = expenses[expenses["date"].dt.year == year]
        
    settings = parse_settings(data)
    
    # Gross Revenue
    annual_gross = float(sales["gross_revenue"].sum()) if not sales.empty else 0.0
    annual_net = float(sales["net_revenue"].sum()) if not sales.empty else 0.0
    
    # PPh Estimate
    pph_method = "PPh Final UMKM (PP 55/2022)" if settings["use_pph_final_umkm"] else "PPh Tarif Umum (Simulasi)"
    if settings["use_pph_final_umkm"]:
        # PPh Final
        estimated_pph_final = annual_gross * settings["pph_final_rate"]
    else:
        # Standard corporate PPh simulation (22% of Net profit)
        pl = build_profit_loss_report(data, period="yearly", year=year)
        estimated_pph_final = max(0.0, pl["net_profit_before_tax"] * 0.22)
        
    # PPN Estimate
    is_pkp = settings["is_pkp"]
    ppn_rate = settings["ppn_rate"]
    
    ppn_keluaran = 0.0
    ppn_masukan = 0.0
    ppn_kurang_bayar = 0.0
    ppn_notes = ""
    
    if is_pkp:
        ppn_keluaran = annual_gross * ppn_rate
        # Calculate PPN Masukan from deductible expenses
        if not expenses.empty:
            # Check if tax_deductible is True/Yes
            deductible_exp = expenses[expenses["tax_deductible"].astype(str).str.lower().isin(["true", "1", "yes", "ya", "deductible"])]
            total_deductible = deductible_exp["amount"].sum()
            # Simulate PPN Masukan assuming expenses include 12% PPN or can be claimed
            ppn_masukan = total_deductible * ppn_rate
        else:
            ppn_masukan = 0.0
            
        ppn_kurang_bayar = ppn_keluaran - ppn_masukan
        ppn_status = f"PKP Aktif (Estimasi PPN Kurang/Lebih Bayar)"
        ppn_notes = f"Simulasi PPN Keluaran {ppn_rate*100:.0f}% dari Omzet Bruto dan PPN Masukan dari biaya yang deductible."
    else:
        ppn_status = "Tidak memungut PPN / simulasi saja"
        ppn_notes = "Wajib Pajak Non-PKP tidak memungut PPN Keluaran. Batas omzet untuk wajib PKP adalah Rp4,8 Miliar per tahun."
        
    notes = (
        "1. Estimasi PPh Final menggunakan tarif PP 55/2022 sebesar 0.5% untuk UMKM.\n"
        "2. PPN hanya dihitung jika status PKP diaktifkan di pengaturan pajak.\n"
        "3. Disclaimer: Simulasi internal ini bukan SPT Resmi. Harap konsultasikan dengan ahli pajak Anda."
    )
    
    return {
        "year": year,
        "annual_gross": annual_gross,
        "annual_net": annual_net,
        "pph_method": pph_method,
        "estimated_pph_final": estimated_pph_final,
        "is_pkp": is_pkp,
        "ppn_status": ppn_status,
        "ppn_keluaran": ppn_keluaran,
        "ppn_masukan": ppn_masukan,
        "ppn_kurang_bayar": ppn_kurang_bayar,
        "ppn_notes": ppn_notes,
        "notes": notes
    }

def build_tax_readiness_checklist(data, year):
    """
    Assess tax readiness and checklist items for SPT filing.
    """
    sales = data.get("sales")
    if sales is None or sales.empty:
        sales = pd.DataFrame(columns=["date"])
    else:
        sales = sales.copy()
        
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    sales_year = sales[sales["date"].dt.year == year]
    
    expenses = data.get("expenses")
    if expenses is None:
        expenses = pd.DataFrame(columns=["date"])
    else:
        expenses = expenses.copy()
        
    tax_settings = data.get("tax_settings")
    if tax_settings is None:
        tax_settings = pd.DataFrame(columns=["key", "value"])
    else:
        tax_settings = tax_settings.copy()
        
    tax_payments = data.get("tax_payments")
    if tax_payments is None:
        tax_payments = pd.DataFrame(columns=["date", "amount"])
    else:
        tax_payments = tax_payments.copy()
    
    checklist = []
    
    # 1. Sales Data
    unique_months = sales_year["date"].dt.month.nunique() if not sales_year.empty else 0
    if unique_months == 12:
        status = "Ready"
        desc = "Data penjualan lengkap 12 bulan."
    elif unique_months > 0:
        status = "Warning"
        desc = f"Data penjualan baru terisi {unique_months} dari 12 bulan."
    else:
        status = "Missing"
        desc = "Data penjualan tahun ini kosong."
    checklist.append({"item": "Data Penjualan Lengkap 12 Bulan", "status": status, "description": desc})
    
    # 2. Expenses Data
    if not expenses.empty:
        status = "Ready"
        desc = f"Tersedia {len(expenses)} catatan biaya operasional."
    else:
        status = "Warning"
        desc = "Belum ada biaya operasional yang dicatat di tab expenses."
    checklist.append({"item": "Pencatatan Biaya (Expenses)", "status": status, "description": desc})
    
    # 3. Tax Settings
    if len(tax_settings) > 0 and not tax_settings.empty:
        status = "Ready"
        desc = "Pengaturan entitas dan tarif pajak tersedia."
    else:
        status = "Warning"
        desc = "Menggunakan pengaturan pajak default bawaan sistem."
    checklist.append({"item": "Pengaturan Pajak (Tax Settings)", "status": status, "description": desc})
    
    # 4. Tax Payments
    if not tax_payments.empty:
        status = "Ready"
        desc = f"Ditemukan {len(tax_payments)} riwayat setoran pajak."
    else:
        status = "Warning"
        desc = "Belum ada catatan setoran pajak tahun ini (tax_payments)."
    checklist.append({"item": "Riwayat Setoran Pajak (Tax Payments)", "status": status, "description": desc})
    
    # 5. SKU Mismatch
    sku_mismatch_ok = True
    if "products" in data and "sales" in data:
        valid_skus = set(data["products"]["sku"].astype(str).str.strip())
        sales_skus = set(data["sales"]["sku"].astype(str).str.strip())
        mismatches = sales_skus - valid_skus
        if mismatches:
            sku_mismatch_ok = False
            
    if sku_mismatch_ok:
        status = "Ready"
        desc = "Semua SKU di sales terdaftar di master produk."
    else:
        status = "Warning"
        desc = "Ada SKU transaksi penjualan yang belum terdaftar di produk."
    checklist.append({"item": "Konsistensi SKU Produk", "status": status, "description": desc})
    
    # 6. Omzet & PPh
    tax_est = calculate_tax_estimate(data, year)
    if tax_est["annual_gross"] > 0:
        status = "Ready"
        desc = f"Omzet tahunan terhitung: Rp {tax_est['annual_gross']:,.0f}"
    else:
        status = "Missing"
        desc = "Omzet tahunan bernilai Rp 0."
    checklist.append({"item": "Omzet Tahunan Dihitung", "status": status, "description": desc})
    
    if tax_est["estimated_pph_final"] > 0:
        status = "Ready"
        desc = f"Estimasi PPh Final terhitung: Rp {tax_est['estimated_pph_final']:,.0f}"
    else:
        status = "Warning"
        desc = "Estimasi PPh Final Rp 0."
    checklist.append({"item": "Estimasi Pajak Tersedia", "status": status, "description": desc})
    
    # 7. Exports
    checklist.append({"item": "Ekspor Laporan PDF/TXT Tersedia", "status": "Ready", "description": "Fasilitas download laporan keuangan dan pajak aktif."})
    
    return checklist

def generate_finance_tax_insights(data, year):
    """
    Generate 5-8 automated insights based on finance and tax data.
    """
    sales = data.get("sales")
    if sales is None or sales.empty:
        sales = pd.DataFrame(columns=["date", "gross_revenue", "net_profit", "ad_cost_allocated", "marketplace_fee", "packing_cost"])
    else:
        sales = sales.copy()
        
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    sales_year = sales[sales["date"].dt.year == year]
    
    expenses = data.get("expenses")
    if expenses is None or expenses.empty:
        expenses = pd.DataFrame(columns=["date", "amount"])
    else:
        expenses = expenses.copy()
        
    if not expenses.empty and "date" in expenses.columns:
        expenses["date"] = pd.to_datetime(expenses["date"], errors="coerce")
        expenses_year = expenses[expenses["date"].dt.year == year]
    else:
        expenses_year = pd.DataFrame()
        
    settings = parse_settings(data)
    threshold = settings["annual_omzet_threshold"]
    
    insights = []
    
    # If no sales data
    if sales_year.empty:
        return ["Belum ada transaksi penjualan pada tahun ini untuk analisis insight."]
        
    # 1. Omzet bulanan tertinggi
    monthly_sales = sales_year.groupby(sales_year["date"].dt.month)["gross_revenue"].sum()
    months_name = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                   "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    if not monthly_sales.empty:
        max_month = monthly_sales.idxmax()
        max_val = monthly_sales.max()
        insights.append(f"📈 <b>Omzet Bulanan Tertinggi:</b> Dicapai pada bulan <b>{months_name[max_month-1]}</b> sebesar Rp {max_val:,.0f}.")
        
    # 2. Bulan profit tertinggi
    monthly_profit = sales_year.groupby(sales_year["date"].dt.month)["net_profit"].sum()
    if not monthly_profit.empty:
        max_prof_month = monthly_profit.idxmax()
        max_prof_val = monthly_profit.max()
        insights.append(f"💰 <b>Bulan Profit Tertinggi:</b> Dicapai pada bulan <b>{months_name[max_prof_month-1]}</b> dengan profit bersih Rp {max_prof_val:,.0f} (dari transaksi sales).")
        
    # 3. Biaya Terbesar
    ad_spend = float(sales_year["ad_cost_allocated"].sum()) if "ad_cost_allocated" in sales_year.columns else 0.0
    marketplace_fee = float(sales_year["marketplace_fee"].sum()) if "marketplace_fee" in sales_year.columns else 0.0
    packing_cost = float(sales_year["packing_cost"].sum()) if "packing_cost" in sales_year.columns else 0.0
    op_spend = float(expenses_year["amount"].sum()) if not expenses_year.empty else 0.0
    
    costs = {
        "Biaya Operasional (Expenses)": op_spend,
        "Biaya Iklan (Ads Allocated)": ad_spend,
        "Biaya Marketplace (Admin Fee)": marketplace_fee,
        "Biaya Packing": packing_cost
    }
    max_cost_name = max(costs, key=costs.get)
    max_cost_val = costs[max_cost_name]
    insights.append(f"🛍️ <b>Struktur Biaya Terbesar:</b> Pengeluaran terbesar di luar HPP adalah <b>{max_cost_name}</b> sebesar Rp {max_cost_val:,.0f}.")
    
    # 4. Estimasi pajak
    tax_est = calculate_tax_estimate(data, year)
    insights.append(f"🧾 <b>Estimasi Beban Pajak:</b> Estimasi PPh Final UMKM (0.5%) tahun {year} adalah <b>Rp {tax_est['estimated_pph_final']:,.0f}</b> dari total omzet bruto Rp {tax_est['annual_gross']:,.0f}.")
    
    # 5. Status threshold omzet
    accum_omzet = tax_est["annual_gross"]
    pct_threshold = (accum_omzet / threshold) * 100 if threshold else 0.0
    if accum_omzet > threshold:
        insights.append(f"⚠️ <b>Threshold PKP Terlewati:</b> Omzet tahunan (Rp {accum_omzet:,.0f}) telah <b>melebihi batas Rp 4,8 Miliar</b>. Anda wajib mengajukan pendaftaran Pengusaha Kena Pajak (PKP) dan memungut PPN.")
    elif accum_omzet >= threshold * 0.8:
        insights.append(f"🟡 <b>Hampir Melebihi Threshold:</b> Omzet tahunan telah mencapai <b>{pct_threshold:.1f}%</b> dari batas Rp 4,8 Miliar. Harap persiapkan administrasi PKP.")
    else:
        insights.append(f"🟢 <b>Status Threshold Omzet:</b> Omzet tahunan berada di tingkat <b>{pct_threshold:.1f}%</b> dari batas Rp 4,8 Miliar (Aman untuk WP UMKM Non-PKP).")
        
    # 6. PPN status
    if settings["is_pkp"]:
        insights.append(f"⚖️ <b>Status PPN (PKP):</b> Simulasi PPN Keluaran sebesar Rp {tax_est['ppn_keluaran']:,.0f} dan PPN Masukan Rp {tax_est['ppn_masukan']:,.0f}. Estimasi PPN kurang bayar Rp {tax_est['ppn_kurang_bayar']:,.0f}.")
    else:
        insights.append(f"💡 <b>Peluang Efisiensi PPN:</b> Bisnis saat ini berstatus Non-PKP, sehingga tidak perlu memungut PPN 12% ke pelanggan, menjaga harga jual tetap kompetitif.")
        
    # 7. Dokumen yang perlu disiapkan
    insights.append(
        f"📋 <b>Dokumen SPT yang Perlu Disiapkan:</b>\n"
        f"  - Rekapitulasi peredaran bruto bulanan tahun {year}.\n"
        f"  - Bukti penyetoran PPh Final UMKM (SSP/BPN) tiap bulan.\n"
        f"  - Daftar aset dan kewajiban akhir tahun untuk Form SPT 1770 Lampiran IV."
    )
    
    return insights
