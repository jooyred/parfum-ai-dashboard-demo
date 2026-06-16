import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import pandas as pd

def generate_daily_pdf_report(data, output_path=None) -> bytes:
    # Extract dataframes
    sales = data["sales"]
    products = data["products"]
    inv_products = data["inventory_products"]
    inv_materials = data["inventory_materials"]
    bom = data["bom"]
    ads = data["ads"]
    prod_plan = data["production_plan"]
    
    from modules.calculations import (
        rupiah, pct, overview_metrics, top_products, inventory_product_status,
        inventory_material_status, suggested_purchase_value
    )
    
    # Metrics calculations
    m = overview_metrics(sales)
    latest_date_str = m["latest_date"].strftime("%d %B %Y")
    
    gross_val = rupiah(m['gross'])
    orders_val = f"{m['orders']} Order"
    profit_val = rupiah(m['profit'])
    margin_val = pct(m['margin'])
    ad_spend_val = rupiah(m['ad_spend'])
    
    invp = inventory_product_status(inv_products)
    invm = inventory_material_status(inv_materials)
    critical_p_df = invp[invp["status"] == "Kritis"]
    critical_m_df = invm[invm["status"] == "Kritis"]
    
    need_m, suggested_purchase_cost = suggested_purchase_value(inv_materials)
    top5 = top_products(sales, latest_only=True).head(5)
    
    # Styling Setup
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#083047')  # Dark Navy
    secondary_color = colors.HexColor('#0d6570')  # Teal
    text_color = colors.HexColor('#1e293b')  # Slate 800
    bg_light = colors.HexColor('#f8fafc')  # Soft Gray
    border_color = colors.HexColor('#e2e8f0')  # Border
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=secondary_color,
        alignment=TA_CENTER
    )
    
    date_style = ParagraphStyle(
        'DocDate',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER
    )
    
    h1_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_color
    )
    
    body_bold_style = ParagraphStyle(
        'BodyTextBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_color
    )
    
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )
    
    # 1. Summary Grid
    summary_data = [
        [Paragraph("<b>Omzet Hari Ini</b>", body_style), Paragraph(gross_val, body_bold_style),
         Paragraph("<b>Profit Bersih</b>", body_style), Paragraph(profit_val, body_bold_style)],
        [Paragraph("<b>Jumlah Order</b>", body_style), Paragraph(orders_val, body_style),
         Paragraph("<b>Margin Bersih</b>", body_style), Paragraph(margin_val, body_bold_style)],
        [Paragraph("<b>Biaya Iklan Teralokasi</b>", body_style), Paragraph(ad_spend_val, body_style),
         Paragraph("<b>Belanja Disarankan</b>", body_style), Paragraph(rupiah(suggested_purchase_cost), body_style)],
        [Paragraph("<b>Produk Stok Kritis</b>", body_style), Paragraph(f"{len(critical_p_df)} SKU", body_style),
         Paragraph("<b>Bahan Baku Kritis</b>", body_style), Paragraph(f"{len(critical_m_df)} Item", body_style)]
    ]
    summary_table = Table(summary_data, colWidths=[130, 120, 135, 130])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 2. Top Products Table
    top_data = [[
        Paragraph("No", table_header_style),
        Paragraph("Produk", table_header_style),
        Paragraph("Terjual", table_header_style),
        Paragraph("Omzet", table_header_style),
        Paragraph("Profit", table_header_style),
        Paragraph("Margin", table_header_style)
    ]]
    for i, row in enumerate(top5.itertuples(index=False), start=1):
        top_data.append([
            Paragraph(str(i), table_cell_style),
            Paragraph(row.product, table_cell_style),
            Paragraph(f"{int(row.terjual)} pcs", table_cell_style),
            Paragraph(rupiah(row.omzet), table_cell_style),
            Paragraph(rupiah(row.profit), table_cell_style),
            Paragraph(pct(row.margin), table_cell_style),
        ])
    top_table = Table(top_data, colWidths=[25, 190, 75, 75, 75, 75])
    top_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 3. Critical Inventories Table
    crit_p_lines = []
    if critical_p_df.empty:
        crit_p_lines.append("<i>Tidak ada produk kritis.</i>")
    else:
        for row in critical_p_df.itertuples(index=False):
            crit_p_lines.append(f"• <b>{row.product}</b>: {int(row.stock)} pcs (min {int(row.min_stock)} pcs) - Habis dlm {row.estimasi_hari_habis} hari.")
             
    crit_m_lines = []
    if critical_m_df.empty:
        crit_m_lines.append("<i>Tidak ada bahan baku kritis.</i>")
    else:
        for row in critical_m_df.itertuples(index=False):
            crit_m_lines.append(f"• <b>{row.material}</b>: {row.stock} {row.unit} (min {row.min_stock} {row.unit}).")
             
    crit_data = [
        [Paragraph("<b>Produk Stok Kritis</b>", body_bold_style), Paragraph("<b>Bahan Baku Kritis</b>", body_bold_style)],
        [Paragraph("<br/>".join(crit_p_lines), body_style), Paragraph("<br/>".join(crit_m_lines), body_style)]
    ]
    crit_table = Table(crit_data, colWidths=[250, 265])
    crit_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,0), bg_light),
        ('PADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
    ]))
    
    # 4. Production Plan Table
    prod_data = [[
        Paragraph("SKU", table_header_style),
        Paragraph("Produk", table_header_style),
        Paragraph("Stok", table_header_style),
        Paragraph("Permintaan 7d", table_header_style),
        Paragraph("Rekomendasi Produksi", table_header_style),
        Paragraph("Bottleneck", table_header_style)
    ]]
    for row in prod_plan.itertuples(index=False):
        if row.recommended_production > 0:
            prod_data.append([
                Paragraph(row.sku, table_cell_style),
                Paragraph(row.product, table_cell_style),
                Paragraph(f"{int(row.stock)} pcs", table_cell_style),
                Paragraph(f"{int(row.demand_7d)} pcs", table_cell_style),
                Paragraph(f"<b>{int(row.recommended_production)} pcs</b>", table_cell_bold),
                Paragraph(row.bottleneck, table_cell_style)
            ])
    if len(prod_data) > 1:
        prod_table = Table(prod_data, colWidths=[65, 170, 70, 70, 70, 70])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), secondary_color),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
            ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('PADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
    else:
        prod_table = Paragraph("<i>Tidak ada rekomendasi produksi mendesak saat ini. Semua stok aman.</i>", body_style)
        
    # 5. Insight AI Section
    insights = []
    if m["margin"] >= 0.25:
        insights.append(f"<b>Kinerja Keuangan Sehat:</b> Margin bersih saat ini mencapai {pct(m['margin'])}, melebihi target minimal 25%. Profitabilitas didukung oleh efisiensi alokasi iklan dan komposisi penjualan SKU premium.")
    else:
        insights.append(f"<b>Optimasi Margin Diperlukan:</b> Margin bersih hari ini sebesar {pct(m['margin'])} berada di bawah target 25%. Evaluasi diskon marketplace dan biaya iklan perlu dilakukan untuk meningkatkan profitabilitas.")
         
    if len(critical_p_df) > 0:
        sku_names = ", ".join(critical_p_df["product"].head(3).tolist())
        insights.append(f"<b>Urgensi Stok Produk:</b> Sebanyak {len(critical_p_df)} SKU ({sku_names}) terdeteksi kritis dan berisiko kosong dalam beberapa hari. Produksi prioritas harus segera dijadwalkan.")
    else:
        insights.append("<b>Stok Produk Aman:</b> Seluruh SKU produk jadi berada dalam kondisi aman di atas batas minimum.")
         
    if len(critical_m_df) > 0:
        mat_names = ", ".join(critical_m_df["material"].head(3).tolist())
        insights.append(f"<b>Pengadaan Bahan Baku:</b> Segera pesan bahan baku kritis ({mat_names}) untuk menghindari hambatan produksi. Estimasi kebutuhan anggaran belanja adalah {rupiah(suggested_purchase_cost)}.")
    else:
        insights.append("<b>Ketersediaan Bahan Baku Aman:</b> Stok bahan baku mencukupi untuk mendukung jalannya produksi dalam minggu ini.")
         
    boncos_ads = ads[ads["status"] == "Boncos"]
    if not boncos_ads.empty:
        campaign_names = ", ".join(boncos_ads["campaign"].tolist())
        insights.append(f"<b>Evaluasi Kinerja Iklan:</b> Campaign iklan <b>{campaign_names}</b> berstatus <i>Boncos</i> dengan ROAS rendah. Disarankan untuk meninjau ulang budget allocation atau materi kreatif iklan tersebut.")
    else:
        insights.append("<b>Efisiensi Iklan Baik:</b> Seluruh campaign iklan berjalan efektif dengan ROAS dalam batas wajar/sehat.")
        
    insights_content = []
    for insight in insights:
        insights_content.append(Paragraph(f"• {insight}", body_style))
        insights_content.append(Spacer(1, 4))
    if insights_content:
        insights_content.pop()
        
    insights_box = Table([[insights_content]], colWidths=[515])
    insights_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e8f4f5')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#0d6570')),
        ('LINELEFT', (0,0), (0,-1), 3, colors.HexColor('#0d6570')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    # Building story
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        output_path if output_path else buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    story = []
    
    # Title Block
    story.append(Paragraph("Laporan Harian Bisnis Parfum", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("AI Business Control Tower", subtitle_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph(f"Tanggal Laporan: {latest_date_str}", date_style))
    story.append(Spacer(1, 8))
    
    # Divider
    divider = Table([['']], colWidths=[515], rowHeights=[1.5])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), secondary_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 10))
    
    # Sections
    story.append(Paragraph("Ringkasan Performa", h1_style))
    story.append(summary_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Produk Terlaris Hari Ini", h1_style))
    story.append(top_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Stok & Rencana Pembelian", h1_style))
    story.append(crit_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Rekomendasi Rencana Produksi", h1_style))
    story.append(prod_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Insight AI & Rencana Aksi", h1_style))
    story.append(insights_box)
    
    doc.build(story)
    
    if output_path:
        return b""
    else:
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

def generate_finance_tax_pdf_report(data, year, output_path=None) -> bytes:
    from modules.calculations import rupiah, pct
    from modules.finance_tax import (
        build_profit_loss_report, build_monthly_omzet_summary,
        calculate_tax_estimate, build_tax_readiness_checklist,
        generate_finance_tax_insights
    )
    
    # Styling Setup
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#083047')  # Dark Navy
    secondary_color = colors.HexColor('#0d6570')  # Teal
    text_color = colors.HexColor('#1e293b')  # Slate 800
    bg_light = colors.HexColor('#f8fafc')  # Soft Gray
    border_color = colors.HexColor('#e2e8f0')  # Border
    
    title_style = ParagraphStyle(
        'FinanceDocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'FinanceDocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=secondary_color,
        alignment=TA_CENTER
    )
    
    date_style = ParagraphStyle(
        'FinanceDocDate',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER
    )
    
    h1_style = ParagraphStyle(
        'FinanceSectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'FinanceBodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_color
    )
    
    table_header_style = ParagraphStyle(
        'FinanceTableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'FinanceTableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=text_color
    )
    
    table_cell_bold = ParagraphStyle(
        'FinanceTableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )
    
    # 1. Disclaimer Callout Box
    disclaimer_text = "<b>PENTING (DISCLAIMER):</b> Estimasi pajak bersifat simulasi internal. Laporan ini bukan dokumen resmi perpajakan dan tidak dapat digunakan sebagai SPT final yang sah. Validasi final tetap harus dilakukan dengan konsultan pajak bersertifikat atau Direktorat Jenderal Pajak (DJP)."
    disclaimer_box = Table([[Paragraph(disclaimer_text, body_style)]], colWidths=[515])
    disclaimer_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fef2f2')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#ef4444')),
        ('LINELEFT', (0,0), (0,-1), 3, colors.HexColor('#ef4444')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 2. Profit and Loss Table
    pl = build_profit_loss_report(data, period="yearly", year=year)
    laba_rugi_data = [
        [Paragraph("<b>Item Laporan Keuangan (Laba Rugi)</b>", table_header_style), Paragraph("<b>Nilai (Rupiah)</b>", table_header_style)],
        [Paragraph("Penjualan Bruto (Gross Revenue)", table_cell_style), Paragraph(rupiah(pl["gross_revenue"]), table_cell_bold if pl["gross_revenue"] > 0 else table_cell_style)],
        [Paragraph("Diskon/Retur Penjualan", table_cell_style), Paragraph(f"- {rupiah(pl['discount'])}", table_cell_style)],
        [Paragraph("<b>Penjualan Bersih (Net Revenue)</b>", table_cell_style), Paragraph(rupiah(pl["net_revenue"]), table_cell_bold)],
        [Paragraph("Harga Pokok Penjualan (HPP)", table_cell_style), Paragraph(f"- {rupiah(pl['hpp'])}", table_cell_style)],
        [Paragraph("<b>Laba Kotor (Gross Profit)</b>", table_cell_style), Paragraph(rupiah(pl["gross_profit"]), table_cell_bold)],
        [Paragraph("Biaya Marketplace (Admin Fee)", table_cell_style), Paragraph(f"- {rupiah(pl['marketplace_fee'])}", table_cell_style)],
        [Paragraph("Biaya Iklan (Marketing Cost)", table_cell_style), Paragraph(f"- {rupiah(pl['ad_cost'])}", table_cell_style)],
        [Paragraph("Biaya Packing", table_cell_style), Paragraph(f"- {rupiah(pl['packing_cost'])}", table_cell_style)],
        [Paragraph("Biaya Operasional Lain (Expenses)", table_cell_style), Paragraph(f"- {rupiah(pl['operating_expenses'])}", table_cell_style)],
        [Paragraph("<b>Laba Bersih Sebelum Pajak (EBT)</b>", table_cell_style), Paragraph(rupiah(pl["net_profit_before_tax"]), table_cell_bold)],
        [Paragraph("Estimasi Beban Pajak", table_cell_style), Paragraph(f"- {rupiah(pl['estimated_tax'])}", table_cell_style)],
        [Paragraph("<b>Laba Bersih Setelah Pajak (EAT)</b>", table_cell_style), Paragraph(rupiah(pl["net_profit_after_tax"]), table_cell_bold)]
    ]
    pl_table = Table(laba_rugi_data, colWidths=[320, 195])
    pl_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 3. Monthly Omzet & Tax Summary Table
    monthly_df = build_monthly_omzet_summary(data, year)
    monthly_data = [[
        Paragraph("Bulan", table_header_style),
        Paragraph("Omzet Bruto", table_header_style),
        Paragraph("Net Revenue", table_header_style),
        Paragraph("Order", table_header_style),
        Paragraph("Est PPh Final", table_header_style),
        Paragraph("Akumulasi", table_header_style),
        Paragraph("Status", table_header_style)
    ]]
    for _, row in monthly_df.iterrows():
        monthly_data.append([
            Paragraph(row["month"], table_cell_style),
            Paragraph(rupiah(row["gross_revenue"]), table_cell_style),
            Paragraph(rupiah(row["net_revenue"]), table_cell_style),
            Paragraph(str(row["order_count"]), table_cell_style),
            Paragraph(rupiah(row["estimated_pph_final"]), table_cell_style),
            Paragraph(rupiah(row["accumulated_gross_revenue"]), table_cell_style),
            Paragraph(row["threshold_status"], table_cell_bold if row["threshold_status"] != "Aman" else table_cell_style)
        ])
    monthly_table = Table(monthly_data, colWidths=[70, 75, 75, 40, 75, 95, 85])
    monthly_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 4. Tax Readiness Checklist Table
    checklist = build_tax_readiness_checklist(data, year)
    chk_data = [[
        Paragraph("<b>Langkah Kesiapan Pajak</b>", table_header_style),
        Paragraph("<b>Status</b>", table_header_style),
        Paragraph("<b>Keterangan</b>", table_header_style)
    ]]
    for item in checklist:
        status_color = colors.HexColor('#065f46') if item["status"] == "Ready" else colors.HexColor('#92400e') if item["status"] == "Warning" else colors.HexColor('#991b1b')
        status_para = Paragraph(f"<font color='{status_color}'><b>{item['status']}</b></font>", table_cell_style)
        chk_data.append([
            Paragraph(item["item"], table_cell_bold if item["status"] == "Ready" else table_cell_style),
            status_para,
            Paragraph(item["description"], table_cell_style)
        ])
    chk_table = Table(chk_data, colWidths=[160, 75, 280])
    chk_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 5. PPN Simulation
    tax_est = calculate_tax_estimate(data, year)
    if tax_est["is_pkp"]:
        ppn_text = (
            f"<b>Status PKP: Aktif (Simulasi Pengusaha Kena Pajak)</b><br/>"
            f"• PPN Keluaran (Output Tax): {rupiah(tax_est['ppn_keluaran'])}<br/>"
            f"• PPN Masukan (Input Tax): {rupiah(tax_est['ppn_masukan'])} (dari pengeluaran deductible)<br/>"
            f"• <b>Estimasi PPN Kurang/(Lebih) Bayar: {rupiah(tax_est['ppn_kurang_bayar'])}</b><br/>"
            f"<i>Catatan: {tax_est['ppn_notes']}</i>"
        )
    else:
        ppn_text = (
            f"<b>Status PPN: WP Non-PKP (Tidak Memungut PPN)</b><br/>"
            f"• PPN Keluaran: Rp 0 (Simulasi non-aktif)<br/>"
            f"• PPN Masukan: Rp 0 (Tidak dapat dikreditkan)<br/>"
            f"<i>Catatan: {tax_est['ppn_notes']}</i>"
        )
    ppn_box = Table([[Paragraph(ppn_text, body_style)]], colWidths=[515])
    ppn_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    
    # 6. AI Insights Section
    insights = generate_finance_tax_insights(data, year)
    insights_content = []
    for insight in insights:
        insights_content.append(Paragraph(f"• {insight}", body_style))
        insights_content.append(Spacer(1, 3))
    if insights_content:
        insights_content.pop()
        
    insights_box = Table([[insights_content]], colWidths=[515])
    insights_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e8f4f5')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#0d6570')),
        ('LINELEFT', (0,0), (0,-1), 3, colors.HexColor('#0d6570')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    # Building story
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        output_path if output_path else buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=35,
        bottomMargin=35
    )
    
    story = []
    
    # Title Block
    story.append(Paragraph("Laporan Keuangan & Tax Readiness", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("AI Business Control Tower — Finance & Tax Pack", subtitle_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph(f"Tahun Pajak / Periode Analisis: {year}", date_style))
    story.append(Spacer(1, 8))
    
    # Divider
    divider = Table([['']], colWidths=[515], rowHeights=[1.5])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), secondary_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 8))
    
    story.append(disclaimer_box)
    story.append(Spacer(1, 8))
    
    # Sections
    story.append(Paragraph("Laporan Laba Rugi Tahunan", h1_style))
    story.append(pl_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Omzet Bulanan & Akumulasi Threshold", h1_style))
    story.append(monthly_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Simulasi Pajak Pertambahan Nilai (PPN)", h1_style))
    story.append(ppn_box)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Checklist Persiapan SPT Tahunan", h1_style))
    story.append(chk_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Insight AI & Rencana Keuangan", h1_style))
    story.append(insights_box)
    
    doc.build(story)
    
    if output_path:
        return b""
    else:
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

def generate_spt_attachment_pack_pdf(data, year) -> bytes:
    from modules.calculations import rupiah, pct
    from modules.finance_tax import (
        build_profit_loss_report, build_monthly_omzet_summary,
        calculate_tax_estimate, build_tax_readiness_checklist,
        parse_settings
    )
    
    # Styling Setup
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#083047')  # Dark Navy
    secondary_color = colors.HexColor('#0d6570')  # Teal
    text_color = colors.HexColor('#1e293b')  # Slate 800
    bg_light = colors.HexColor('#f8fafc')  # Soft Gray
    border_color = colors.HexColor('#e2e8f0')  # Border
    
    title_style = ParagraphStyle(
        'SptDocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'SptDocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        alignment=TA_CENTER
    )
    
    date_style = ParagraphStyle(
        'SptDocDate',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER
    )
    
    h1_style = ParagraphStyle(
        'SptSectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'SptBodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_color
    )
    
    body_bold_style = ParagraphStyle(
        'SptBodyTextBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    table_header_style = ParagraphStyle(
        'SptTableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'SptTableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=text_color
    )
    
    table_cell_bold = ParagraphStyle(
        'SptTableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )
    
    # 1. Disclaimer
    disclaimer_text = "<b>PENTING (DISCLAIMER):</b> Estimasi pajak bersifat simulasi internal. Validasi final tetap perlu dilakukan dengan konsultan pajak atau DJP. Dokumen ini merupakan rekap pendukung internal (Lampiran Pendukung Internal / Rekap Pendukung / Simulasi) dan bukan merupakan SPT resmi yang siap dilaporkan."
    disclaimer_box = Table([[Paragraph(disclaimer_text, body_style)]], colWidths=[515])
    disclaimer_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fef2f2')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#ef4444')),
        ('LINELEFT', (0,0), (0,-1), 3, colors.HexColor('#ef4444')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 2. Identitas Simulasi Bisnis
    settings = parse_settings(data)
    entity_map = {
        "orang_pribadi_umkm": "Wajib Pajak Orang Pribadi - UMKM (PP 55/2022)",
        "badan_umkm": "Wajib Pajak Badan - UMKM",
        "tarif_umum": "Wajib Pajak Badan / Orang Pribadi - Tarif Umum"
    }
    entity_str = entity_map.get(settings.get("business_entity"), str(settings.get("business_entity")))
    pkp_str = "Ya (Pengusaha Kena Pajak)" if settings.get("is_pkp") else "Tidak (Non-PKP)"
    use_pph_final_str = "Ya (PPh Final UMKM 0.5%)" if settings.get("use_pph_final_umkm") else "Tidak (Tarif Umum)"
    
    identitas_data = [
        [Paragraph("<b>Identitas Simulasi Bisnis</b>", table_header_style), Paragraph("", table_header_style)],
        [Paragraph("Jenis Entitas Wajib Pajak", table_cell_style), Paragraph(entity_str, table_cell_bold)],
        [Paragraph("Status Pengusaha Kena Pajak (PKP)", table_cell_style), Paragraph(pkp_str, table_cell_style)],
        [Paragraph("Menggunakan PPh Final UMKM", table_cell_style), Paragraph(use_pph_final_str, table_cell_style)],
        [Paragraph("Batas Threshold Omzet Bruto", table_cell_style), Paragraph(rupiah(settings.get("annual_omzet_threshold")), table_cell_style)],
        [Paragraph("Tarif PPh Final UMKM", table_cell_style), Paragraph(pct(settings.get("pph_final_rate")), table_cell_style)],
        [Paragraph("Tarif PPN", table_cell_style), Paragraph(pct(settings.get("ppn_rate")), table_cell_style)],
        [Paragraph("Tahun Pajak", table_cell_style), Paragraph(str(year), table_cell_bold)]
    ]
    identitas_table = Table(identitas_data, colWidths=[200, 315])
    identitas_table.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 3. Laba Rugi Ringkas
    pl = build_profit_loss_report(data, period="yearly", year=year)
    laba_rugi_data = [
        [Paragraph("<b>Laporan Laba Rugi Ringkas (Simulasi)</b>", table_header_style), Paragraph("<b>Nilai</b>", table_header_style)],
        [Paragraph("Penjualan Bruto (Gross Revenue)", table_cell_style), Paragraph(rupiah(pl["gross_revenue"]), table_cell_bold)],
        [Paragraph("Diskon & Potongan Penjualan", table_cell_style), Paragraph(f"- {rupiah(pl['discount'])}", table_cell_style)],
        [Paragraph("<b>Penjualan Bersih (Net Revenue)</b>", table_cell_style), Paragraph(rupiah(pl["net_revenue"]), table_cell_bold)],
        [Paragraph("Harga Pokok Penjualan (HPP)", table_cell_style), Paragraph(f"- {rupiah(pl['hpp'])}", table_cell_style)],
        [Paragraph("<b>Laba Kotor (Gross Profit)</b>", table_cell_style), Paragraph(rupiah(pl["gross_profit"]), table_cell_bold)],
        [Paragraph("Biaya Operasional - Marketplace Fee", table_cell_style), Paragraph(f"- {rupiah(pl['marketplace_fee'])}", table_cell_style)],
        [Paragraph("Biaya Operasional - Iklan (Ads)", table_cell_style), Paragraph(f"- {rupiah(pl['ad_cost'])}", table_cell_style)],
        [Paragraph("Biaya Operasional - Packing Cost", table_cell_style), Paragraph(f"- {rupiah(pl['packing_cost'])}", table_cell_style)],
        [Paragraph("Biaya Operasional Lainnya (Expenses)", table_cell_style), Paragraph(f"- {rupiah(pl['operating_expenses'])}", table_cell_style)],
        [Paragraph("<b>Laba Bersih Sebelum Pajak (EBT)</b>", table_cell_style), Paragraph(rupiah(pl["net_profit_before_tax"]), table_cell_bold)],
        [Paragraph("Estimasi Beban Pajak (PPh)", table_cell_style), Paragraph(f"- {rupiah(pl['estimated_tax'])}", table_cell_style)],
        [Paragraph("<b>Laba Bersih Setelah Pajak (EAT)</b>", table_cell_style), Paragraph(rupiah(pl["net_profit_after_tax"]), table_cell_bold)]
    ]
    pl_table = Table(laba_rugi_data, colWidths=[320, 195])
    pl_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 4. Rekap Omzet Bulanan
    monthly_df = build_monthly_omzet_summary(data, year)
    monthly_data = [[
        Paragraph("Bulan", table_header_style),
        Paragraph("Omzet Bruto", table_header_style),
        Paragraph("Est PPh Final", table_header_style),
        Paragraph("Akumulasi Omzet", table_header_style),
        Paragraph("Status", table_header_style)
    ]]
    for _, row in monthly_df.iterrows():
        monthly_data.append([
            Paragraph(row["month"], table_cell_style),
            Paragraph(rupiah(row["gross_revenue"]), table_cell_style),
            Paragraph(rupiah(row["estimated_pph_final"]), table_cell_style),
            Paragraph(rupiah(row["accumulated_gross_revenue"]), table_cell_style),
            Paragraph(row["threshold_status"], table_cell_bold if row["threshold_status"] != "Aman" else table_cell_style)
        ])
    monthly_table = Table(monthly_data, colWidths=[90, 100, 100, 120, 105])
    monthly_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 5. Rekap Biaya Operasional (Expenses Grouped by Category)
    expenses = data.get("expenses")
    if expenses is not None and not expenses.empty:
        expenses_year = expenses[pd.to_datetime(expenses["date"], errors="coerce").dt.year == year]
    else:
        expenses_year = pd.DataFrame()
        
    exp_summary_data = [[
        Paragraph("Kategori Biaya", table_header_style),
        Paragraph("Jumlah Transaksi", table_header_style),
        Paragraph("Total Biaya", table_header_style),
        Paragraph("Tax Deductible", table_header_style)
    ]]
    if not expenses_year.empty:
        # Group by category and tax_deductible
        grouped = expenses_year.groupby(['category', 'tax_deductible']).agg(
            total_amount=('amount', 'sum'),
            count=('amount', 'count')
        ).reset_index()
        for _, row in grouped.iterrows():
            deductible_status = "Deductible" if str(row["tax_deductible"]).lower() in ["true", "1", "yes", "ya"] else "Non-Deductible"
            exp_summary_data.append([
                Paragraph(str(row["category"]), table_cell_style),
                Paragraph(f"{row['count']} kali", table_cell_style),
                Paragraph(rupiah(row["total_amount"]), table_cell_style),
                Paragraph(deductible_status, table_cell_bold if deductible_status == "Deductible" else table_cell_style)
            ])
    else:
        exp_summary_data.append([Paragraph("<i>Tidak ada data biaya operasional untuk tahun ini</i>", table_cell_style), "", "", ""])
        
    exp_table = Table(exp_summary_data, colWidths=[150, 100, 140, 125])
    exp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    if expenses_year.empty:
        exp_table.setStyle(TableStyle([('SPAN', (0,1), (3,1))]))
        
    # 6. Rekap Pembayaran Pajak (Tax Payments)
    tax_payments = data.get("tax_payments")
    if tax_payments is not None and not tax_payments.empty:
        payments_year = tax_payments[pd.to_datetime(tax_payments["date"], errors="coerce").dt.year == year]
    else:
        payments_year = pd.DataFrame()
        
    pay_data = [[
        Paragraph("Tanggal", table_header_style),
        Paragraph("Jenis Pajak", table_header_style),
        Paragraph("Masa/Period", table_header_style),
        Paragraph("Jumlah Setoran", table_header_style),
        Paragraph("NTPN/Referensi", table_header_style)
    ]]
    if not payments_year.empty:
        for _, row in payments_year.iterrows():
            pay_date_str = pd.to_datetime(row["date"]).strftime("%d-%m-%Y") if not pd.isna(row["date"]) else "-"
            pay_data.append([
                Paragraph(pay_date_str, table_cell_style),
                Paragraph(str(row["tax_type"]), table_cell_style),
                Paragraph(str(row["period"]), table_cell_style),
                Paragraph(rupiah(row["amount"]), table_cell_style),
                Paragraph(str(row["payment_ref"]), table_cell_bold)
            ])
    else:
        pay_data.append([Paragraph("<i>Tidak ada catatan setoran pajak untuk tahun ini</i>", table_cell_style), "", "", "", ""])
        
    pay_table = Table(pay_data, colWidths=[80, 110, 80, 110, 135])
    pay_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    if payments_year.empty:
        pay_table.setStyle(TableStyle([('SPAN', (0,1), (4,1))]))
        
    # 7. Tax Readiness Checklist
    checklist = build_tax_readiness_checklist(data, year)
    chk_data = [[
        Paragraph("Langkah Kesiapan Pajak", table_header_style),
        Paragraph("Status", table_header_style),
        Paragraph("Keterangan", table_header_style)
    ]]
    for item in checklist:
        status_color = colors.HexColor('#065f46') if item["status"] == "Ready" else colors.HexColor('#92400e') if item["status"] == "Warning" else colors.HexColor('#991b1b')
        status_para = Paragraph(f"<font color='{status_color}'><b>{item['status']}</b></font>", table_cell_style)
        chk_data.append([
            Paragraph(item["item"], table_cell_bold if item["status"] == "Ready" else table_cell_style),
            status_para,
            Paragraph(item["description"], table_cell_style)
        ])
    chk_table = Table(chk_data, colWidths=[160, 75, 280])
    chk_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # 8. Catatan Dokumen Tambahan yang Perlu Disiapkan
    missing_docs = []
    
    # Check what items are not Ready or Warning
    for item in checklist:
        if item["status"] in ["Warning", "Missing"]:
            missing_docs.append(f"• <b>{item['item']}</b>: {item['description']}")
            
    # Add general requirements
    missing_docs.append("• <b>Formulir SPT Tahunan 1770 / 1771</b> (sesuai status entitas bisnis).")
    missing_docs.append("• <b>Daftar Harta & Utang Akhir Tahun</b> (sebagai lampiran wajib SPT Orang Pribadi / Badan).")
    missing_docs.append("• <b>Rekapitulasi Omzet Bulanan</b> yang telah divalidasi ke mutasi rekening koran bank.")
    missing_docs.append("• <b>Bukti Penerimaan Negara (BPN)</b> untuk pembayaran PPh Final 0.5% setiap masa pajak.")
    
    docs_text = "<br/>".join(missing_docs)
    docs_box = Table([[Paragraph(docs_text, body_style)]], colWidths=[515])
    docs_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#3b82f6')),
        ('LINELEFT', (0,0), (0,-1), 3, colors.HexColor('#3b82f6')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    # Build document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=35,
        bottomMargin=35
    )
    
    story = []
    
    # Title Block
    story.append(Paragraph("Paket Lampiran Pendukung SPT Usaha", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("AI Business Control Tower — Laporan Pendukung Internal", subtitle_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"Tahun Pajak: {year} | Dibuat Secara Otomatis", date_style))
    story.append(Spacer(1, 8))
    
    # Divider
    divider = Table([['']], colWidths=[515], rowHeights=[1.5])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), secondary_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 8))
    
    story.append(disclaimer_box)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("A. Identitas Wajib Pajak & Simulasi Kebijakan Pajak", h1_style))
    story.append(identitas_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("B. Rekapitulasi Laba Rugi Tahunan (Simulasi Internal)", h1_style))
    story.append(pl_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("C. Rincian Peredaran Bruto Bulanan & PPh Final UMKM", h1_style))
    story.append(monthly_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("D. Rekapitulasi Biaya Operasional (Expenses)", h1_style))
    story.append(exp_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("E. Daftar Setoran Pajak Tahun Berjalan (Tax Payments)", h1_style))
    story.append(pay_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("F. Checklist Kesiapan Pelaporan Pajak", h1_style))
    story.append(chk_table)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("G. Catatan Dokumen Pendukung yang Masih Harus Disiapkan", h1_style))
    story.append(docs_box)
    
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
