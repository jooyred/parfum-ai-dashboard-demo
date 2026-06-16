# Panduan Setup Laporan Keuangan & Pajak (Finance & Tax Readiness Pack - V5A)

Modul **Finance & Tax Readiness Pack (V5A)** menambahkan fitur laporan keuangan (laba rugi) dan simulasi pajak (PPh Final UMKM dan PPN) untuk membantu persiapan pencatatan usaha dan lampiran SPT tahunan bisnis parfum Anda.

---

## ⚠️ PENTING (DISCLAIMER)
* **Bukan Pengganti Konsultan Pajak**: Estimasi pajak dan simulasi di dalam sistem ini bersifat simulasi internal untuk membantu pemantauan. Laporan ini bukan dokumen SPT perpajakan resmi.
* **Validasi Final**: Seluruh perhitungan, pengakuan biaya, dan tarif perpajakan wajib divalidasi kembali dengan konsultan pajak bersertifikat atau Kantor Pelayanan Pajak (KPP) Direktorat Jenderal Pajak (DJP).

---

## 1. Struktur Tab Baru di Google Sheets (Opsional)
Untuk mengintegrasikan pencatatan biaya dan pengaturan perpajakan secara live, tambahkan tiga tab baru berikut di spreadsheet Anda. Jika tab belum dibuat, sistem akan otomatis menggunakan data default/simulasi agar tidak crash.

### A. Tab `expenses` (Catatan Pengeluaran Operasional)
Digunakan untuk mencatat semua biaya di luar HPP (seperti sewa gedung, gaji karyawan, utilitas listrik/air, dsb).
* **Format Kolom**:
  * `date` : Tanggal pengeluaran (format: `YYYY-MM-DD`, contoh: `2026-06-16`)
  * `category` : Kategori biaya (contoh: `Sewa`, `Gaji`, `Utilitas`, `Lainnya`)
  * `description` : Deskripsi pengeluaran (contoh: `Bayar sewa ruko Juni 2026`)
  * `amount` : Nominal biaya (contoh: `2500000`)
  * `payment_method` : Metode pembayaran (contoh: `Transfer`, `Kas Kecil`)
  * `vendor` : Nama vendor/penerima (contoh: `Ruko Berkah`)
  * `tax_deductible` : Keterangan biaya pengurang pajak (`true`/`false`)
  * `notes` : Catatan tambahan

### B. Tab `tax_settings` (Pengaturan Pajak Entitas)
Menentukan metode PPh dan status PPN untuk perhitungan simulasi otomatis.
* **Format Kolom**:
  * `key` : Kunci pengaturan
  * `value` : Nilai pengaturan
  * `notes` : Catatan
* **Daftar Kunci yang Didukung & Nilai Default**:
  * `business_entity` : Jenis WP (`orang_pribadi_umkm`, `badan_umkm`, `orang_pribadi_umum`, `badan_umum`)
  * `is_pkp` : Status Pengusaha Kena Pajak (`true` / `false`)
  * `pph_final_rate` : Tarif PPh Final UMKM PP 55/2022 (Default: `0.005` atau 0,5%)
  * `annual_omzet_threshold` : Batas omzet PKP (Default: `4800000000` atau 4,8 Miliar)
  * `ppn_rate` : Tarif PPN yang berlaku (Default: `0.12` atau 12%)
  * `use_pph_final_umkm` : Penggunaan tarif UMKM (`true` / `false`)

### C. Tab `tax_payments` (Riwayat Setoran Pajak)
Pencatatan bukti pembayaran pajak bulanan atau tahunan yang sudah disetor.
* **Format Kolom**:
  * `date` : Tanggal penyetoran (format: `YYYY-MM-DD`)
  * `tax_type` : Jenis pajak (contoh: `PPh Final 0.5%`, `PPN Kurang Bayar`)
  * `period` : Masa pajak (contoh: `Masa Juni 2026`)
  * `amount` : Nominal setoran (contoh: `500000`)
  * `payment_ref` : Nomor NTPN/Kode BPN (contoh: `1234567890ABCDEF`)
  * `notes` : Catatan tambahan

---

## 2. Cara Mengunduh Laporan Keuangan & SPT Attachment Pack (Export)
Pada halaman **Finance & Tax** di dashboard Streamlit, Anda dapat mengunduh data dalam berbagai format:

### Ekspor Dashboard Umum:
1. **Laporan PDF**: PDF Laba Rugi resmi beserta simulasi PPN dan checklist dokumen SPT.
2. **Ringkasan TXT**: Ringkasan cepat metrik laba rugi dan disclaimer perpajakan.
3. **CSV Bulanan**: Data rekap omzet, order, dan estimasi PPh Final 12 bulan dalam format tabular.

### Ekspor SPT Attachment Pack (V5B):
Di bagian bawah halaman Finance & Tax, terdapat panel khusus **SPT Attachment Pack** untuk mengunduh berkas pendukung simulasi SPT Tahunan:
1. **Download SPT Summary TXT** (`spt_summary_2026.txt`): Ringkasan utuh laporan laba rugi ringkas, checklist kesiapan, dan daftar dokumen yang harus disiapkan.
2. **Download Monthly Omzet CSV** (`monthly_omzet_2026.csv`): Perincian peredaran bruto dan estimasi PPh Final 0.5% bulanan untuk 12 bulan.
3. **Download Expenses Recap CSV** (`expenses_recap_2026.csv`): Rincian biaya operasional bisnis parfum yang dikategorikan dan status tax deductible.
4. **Download Tax Payments CSV** (`tax_payments_2026.csv`): Catatan setoran PPh Final / pajak bulanan yang sudah dibayarkan.
5. **Download SPT Attachment PDF** (`spt_attachment_pack_2026.pdf`): PDF lampiran pendukung internal komprehensif berisi semua tabel (identitas, laba rugi ringkas, omzet bulanan, biaya operasional, setoran pajak, dan tax readiness checklist).

---

## 3. Perintah Telegram Baru (V5A & V5B)
Bot Telegram lokal Anda kini dilengkapi dengan perintah khusus keuangan dan pajak:
* `/finance` — Mengirimkan metrik keuangan tahunan (Omzet bruto, EBT, total biaya operasional, dan EAT setelah estimasi pajak).
* `/tax` — Menampilkan simulasi perpajakan tahunan (Status PKP, omzet bruto, estimasi nominal PPh Final UMKM, estimasi PPN kurang bayar, dan disclaimer).
* `/tax_report` — Membuat dan mengirimkan file PDF laporan Keuangan & Tax Readiness langsung ke chat Telegram Anda.
* `/spt_check` — Menampilkan status tab `expenses`, `tax_settings`, dan `tax_payments`, status setoran pajak terdaftar, serta checklist kelengkapan berkas untuk SPT.
* `/spt_pack` — Membuat dan mengirimkan file PDF Paket Lampiran Pendukung SPT Usaha (`spt_attachment_pack_2026.pdf`) langsung ke Telegram Anda.

### NLP Keyword Routing (Ketik Beban Biasa)
Bot otomatis mengenali kata kunci berikut dan mengarahkannya ke perintah terkait:
* `laporan keuangan` / `laba rugi` → memicu `/finance`
* `pajak` / `pph final` / `ppn` → memicu `/tax`
* `spt` / `checklist pajak` → memicu `/spt_check`
* `lampiran spt` / `paket spt` / `rekap spt` → memicu `/spt_pack`

---

## 4. Cara Pengisian & Sinkronisasi Tab Pajak / Expenses
Jika Anda menggunakan Google Sheets sebagai data source utama dan service account memiliki hak akses Editor, Anda dapat menulis data langsung ke tab spreadsheet. Namun, jika service account berstatus Viewer:
1. Unduh file template CSV lokal yang sudah disiapkan di folder `data/`:
   * `data/expenses.csv`
   * `data/tax_settings.csv`
   * `data/tax_payments.csv`
2. Buat tab dengan nama yang persis sama di Google Sheets Anda (`expenses`, `tax_settings`, `tax_payments`).
3. Copy-paste isi file CSV template tersebut ke masing-masing tab Google Sheets Anda.
4. Sesuaikan data dan setoran pajaknya secara manual di Google Sheets Anda.

---

## 5. Langkah Validasi Wajib Pajak ke DJP / Konsultan
Sebelum melaporkan SPT tahunan menggunakan acuan simulasi ini, pastikan Anda:
1. Melakukan rekonsiliasi bank untuk memastikan semua mutasi masuk telah dihitung sebagai omzet bruto penjualan.
2. Memilah kembali biaya non-deductible (seperti keperluan pribadi pemilik) di tab `expenses` dengan menandai `tax_deductible` sebagai `false`.
3. Membawa file ekspor PDF dari dashboard ini ke konsultan pajak terdaftar untuk dibuatkan SPT 1770 atau SPT 1771 resmi beserta lampiran peredaran bruto PP 55/2022.
