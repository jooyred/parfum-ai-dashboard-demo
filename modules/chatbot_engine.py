
from .calculations import (
    rupiah, pct, overview_metrics, top_products, inventory_product_status,
    inventory_material_status, suggested_purchase_value, daily_report
)

def answer_question(question: str, data: dict) -> str:
    q = question.lower().strip()
    sales = data["sales"]
    ads = data["ads"]
    prod_plan = data["production_plan"]
    inv_products = inventory_product_status(data["inventory_products"])
    inv_materials = inventory_material_status(data["inventory_materials"])

    if any(k in q for k in ["profit", "untung", "laba"]):
        if any(k in q for k in ["produk", "sku", "paling"]):
            top = top_products(sales, latest_only=False).sort_values("profit", ascending=False).head(5)
            lines = ["Produk paling profit:"]
            for i, row in enumerate(top.itertuples(index=False), start=1):
                lines.append(f"{i}. {row.product} — profit {rupiah(row.profit)}, omzet {rupiah(row.omzet)}, margin {pct(row.margin)}")
            lines.append("\nInsight: SKU dengan profit tinggi layak diprioritaskan selama stok dan bahan bakunya aman.")
            return "\n".join(lines)

        m = overview_metrics(sales)
        return "\n".join([
            f"Profit bersih hari ini: {rupiah(m['profit'])}",
            "",
            "Ringkasan:",
            f"- Omzet kotor: {rupiah(m['gross'])}",
            f"- Biaya iklan/order teralokasi: {rupiah(m['ad_spend'])}",
            f"- Jumlah order: {m['orders']}",
            f"- Margin bersih: {pct(m['margin'])}",
            "",
            f"Insight: profit berubah {pct(m['profit_change'])} dibanding kemarin. Kenaikan/penurunan terutama dipengaruhi volume order, diskon, HPP, dan biaya iklan.",
        ])

    if any(k in q for k in ["terlaris", "paling laku", "produk laku", "laku"]):
        top = top_products(sales, latest_only=True).head(5)
        lines = ["Produk paling laku hari ini:"]
        for i, row in enumerate(top.itertuples(index=False), start=1):
            lines.append(f"{i}. {row.product} — terjual {int(row.terjual)} pcs, omzet {rupiah(row.omzet)}, profit {rupiah(row.profit)}, margin {pct(row.margin)}")
        lines.append("\nCatatan: cek stok produk terlaris agar tidak kehilangan potensi penjualan.")
        return "\n".join(lines)

    if any(k in q for k in ["produksi", "diproduksi", "buat stok"]):
        rows = prod_plan[prod_plan["recommended_production"] > 0].sort_values("recommended_production", ascending=False)
        lines = ["Rekomendasi produksi minggu ini:"]
        for i, row in enumerate(rows.itertuples(index=False), start=1):
            lines.append(f"{i}. {row.product}: stok {int(row.stock)} pcs, permintaan 7 hari {int(row.demand_7d)} pcs, produksi disarankan {int(row.recommended_production)} pcs. Bottleneck: {row.bottleneck}.")
        lines.append("\nPrioritas: produksi SKU yang stoknya paling kritis dan profitnya tinggi terlebih dahulu.")
        return "\n".join(lines)

    if any(k in q for k in ["bahan", "beli", "belanja", "restock"]):
        need, total = suggested_purchase_value(data["inventory_materials"])
        need = need.sort_values("estimated_cost", ascending=False)
        lines = ["Bahan yang disarankan untuk dibeli:"]
        for i, row in enumerate(need.head(8).itertuples(index=False), start=1):
            lines.append(f"{i}. {row.material}: stok {row.stock} {row.unit}, minimum {row.min_stock} {row.unit}, rekomendasi beli sekitar {row.recommended_qty:.0f} {row.unit}. Estimasi biaya {rupiah(row.estimated_cost)}.")
        lines.append(f"\nEstimasi total belanja bahan: {rupiah(total)}")
        return "\n".join(lines)

    if any(k in q for k in ["stok", "kritis", "habis"]):
        critical_p = inv_products[inv_products["status"] == "Kritis"]
        critical_m = inv_materials[inv_materials["status"] == "Kritis"]
        lines = ["Stok kritis saat ini:"]
        lines.append("\nProduk:")
        if critical_p.empty:
            lines.append("- Tidak ada produk kritis.")
        else:
            for row in critical_p.itertuples(index=False):
                lines.append(f"- {row.product}: stok {int(row.stock)} pcs, minimum {int(row.min_stock)} pcs, estimasi habis {row.estimasi_hari_habis} hari.")
        lines.append("\nBahan baku:")
        if critical_m.empty:
            lines.append("- Tidak ada bahan kritis.")
        else:
            for row in critical_m.itertuples(index=False):
                lines.append(f"- {row.material}: stok {row.stock} {row.unit}, minimum {row.min_stock} {row.unit}.")
        return "\n".join(lines)

    if any(k in q for k in ["iklan", "ads", "boncos", "roas", "campaign"]):
        bad = ads.sort_values("roas").head(4)
        lines = ["Analisis iklan/campaign:"]
        for i, row in enumerate(bad.itertuples(index=False), start=1):
            lines.append(f"{i}. {row.platform} — {row.campaign}: spend {rupiah(row.spend)}, revenue {rupiah(row.revenue)}, ROAS {row.roas}x, status {row.status}.")
        lines.append("\nRekomendasi: campaign dengan ROAS rendah perlu dievaluasi, terutama jika margin produk setelah iklan sudah tipis.")
        return "\n".join(lines)

    if any(k in q for k in ["margin", "turun", "kenapa"]):
        return (
            "Analisis margin:\n"
            "- Margin bisa turun karena diskon naik, fee marketplace, biaya iklan/order meningkat, atau HPP bahan naik.\n"
            "- Pada data dummy ini, campaign dengan ROAS rendah dan SKU premium berbahan mahal menjadi penyebab utama margin menipis.\n\n"
            "Rekomendasi:\n"
            "1. Evaluasi campaign ROAS di bawah 3x.\n"
            "2. Kurangi diskon untuk SKU margin rendah.\n"
            "3. Cek ulang harga bahan bibit premium dan supplier alternatif."
        )

    if any(k in q for k in ["laporan", "report", "harian"]):
        return daily_report(data)

    return (
        "Aku bisa bantu jawab pertanyaan seperti:\n"
        "- Profit bersih hari ini berapa?\n"
        "- Produk paling laku apa?\n"
        "- Produk paling untung apa?\n"
        "- SKU mana yang harus diproduksi?\n"
        "- Bahan apa yang harus dibeli?\n"
        "- Stok mana yang kritis?\n"
        "- Iklan mana yang boncos?\n"
        "- Buatkan laporan harian."
    )
