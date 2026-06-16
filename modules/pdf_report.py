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
