# AI Business Control Tower — Demo Bisnis Parfum (V5C)

Aplikasi dashboard dan chatbot AI interaktif untuk mengontrol performa bisnis parfum, dirancang khusus untuk mempermudah owner memantau keuangan, stok, HPP, produksi, dan kampanye iklan. Versi V5C ini dilengkapi dengan sistem keamanan yang kokoh: **Streamlit login & role permission system**, **Telegram Auto Chat ID Detection & activation code flow**, serta fondasi **Audit Log & Confirmation** di dashboard dan Telegram Bot.

## 🔗 Live Demo
Aplikasi ini telah dideploy secara online dan dapat diakses di:
**[https://parfum-ai-dashboard-demo.streamlit.app/](https://parfum-ai-dashboard-demo.streamlit.app/)**

> [!WARNING]
> **Catatan Keamanan:** Demo ini menggunakan data dummy secara default. Untuk data bisnis real atau sensitif Anda, pastikan sistem login/autentikasi secrets.toml dan .env sudah dikonfigurasi dengan benar. Untuk alur keamanan, lihat [SECURITY_AND_ROLES.md](file:///C:/AI%20PROJECT/parfum_ai_dashboard_demo/SECURITY_AND_ROLES.md).

---

## 🛠️ Prasyarat (Prerequisites)
Pastikan Python 3.8+ sudah terinstal di sistem Anda.

---

## 💻 Cara Menjalankan Aplikasi Secara Lokal

### 1. Jalankan Script Otomatis (Windows)
Double-click file:
```text
run_windows.bat
```
Script ini akan membuat virtual environment secara otomatis, menginstal dependencies, dan menjalankan server Streamlit.

### 2. Cara Manual (Terminal/PowerShell)
Jika file batch tidak berjalan, ikuti langkah berikut:

1. Buka Terminal/PowerShell di folder project.
2. Buat virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Aktifkan virtual environment:
   - **PowerShell**:
     ```bash
     .\.venv\Scripts\Activate.ps1
     ```
     *Jika muncul execution policy error, jalankan:*
     ```bash
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     .\.venv\Scripts\Activate.ps1
     ```
   - **Command Prompt (CMD)**:
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
4. Instal dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Jalankan aplikasi Streamlit:
   ```bash
   streamlit run app.py
   ```
   Aplikasi akan terbuka otomatis di peramban Anda pada alamat: `http://localhost:8501`.

---

## 🚀 Cara Deploy ke Streamlit Community Cloud

Aplikasi ini dirancang menggunakan path relatif yang aman, sehingga siap dideploy ke **Streamlit Community Cloud** secara gratis dengan langkah-langkah berikut:

### 1. Siapkan Repository GitHub
1. Buat repository baru di GitHub (bisa bertipe Private atau Public).
2. Pastikan file `.gitignore` sudah ada di root project untuk mengabaikan folder `.venv/`, `.env`, dan folder temporary lainnya agar tidak ter-push ke GitHub.
3. Lakukan inisialisasi Git dan push kode ke GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit V2 parfum dashboard"
   git branch -M main
   git remote add origin <URL_REPOSITORY_GITHUB_ANDA>
   git push -u origin main
   ```

### 2. Deploy ke Streamlit Cloud
1. Masuk ke [Streamlit Share](https://share.streamlit.io/) dan login menggunakan akun GitHub Anda.
2. Klik tombol **"New app"** di sudut kanan atas.
3. Konfigurasikan detail deployment:
   - **Repository**: Pilih repository GitHub dashboard parfum yang baru Anda buat.
   - **Branch**: Pilih `main` (atau branch default Anda).
   - **Main file path**: Isi dengan **`app.py`** (ini adalah entry point utama aplikasi).
4. Klik tombol **"Deploy!"**.
5. Streamlit Cloud akan membaca berkas `requirements.txt` secara otomatis, menginstal semua dependencies (termasuk Pandas, NumPy, dan ReportLab), lalu meluncurkan aplikasi Anda ke internet.

---

## 🤖 Telegram Bot (V3B, V4A, V4B & V5B) - Pemantau Bisnis & Laporan Otomatis

Aplikasi ini dilengkapi dengan **Telegram Bot** agar owner dapat memantau performa bisnis, melihat keputusan harian (Control Room), mengunduh laporan PDF harian langsung dari Telegram secara real-time, serta menerima laporan otomatis terjadwal (Daily & Closing Report) dan alert operasional langsung di Telegram.

### Cara Menjalankan Bot Telegram Lokal
1. Ikuti panduan lengkap pembuatan bot di BotFather dan konfigurasinya di berkas [TELEGRAM_BOT_SETUP.md](file:///C:/AI%20PROJECT/parfum_ai_dashboard_demo/TELEGRAM_BOT_SETUP.md).
2. Buat file `.env` di root project folder Anda.
3. Masukkan token bot Telegram Anda ke file `.env`.
4. Jalankan bot melalui terminal Anda (pastikan virtual environment aktif):
   ```bash
   python telegram_bot.py
   ```

---

## 👑 Fitur V4A - Owner Control Room & Data Health Check

Versi **V4A** ini membawa sistem ke tahap siap operasional untuk owner bisnis parfum:
1. **Owner Control Room:** Halaman khusus di dashboard yang merangkum kesehatan bisnis (Sehat/Waspada/Kritis), menyajikan 5 kartu keputusan strategis (keuangan, produksi, belanja bahan, iklan, produk ter-cuan), 5 rencana aksi harian otomatis, serta ringkasan siap copy ke WhatsApp.
2. **Data Health Check:** Halaman khusus untuk memvalidasi kelengkapan tab, format kolom, konsistensi SKU, data kosong, dan mendeteksi anomali angka pada Google Sheets/dummy dengan memberikan Health Score (0-100).
3. **Refresh Timestamp:** Menampilkan waktu penyegaran data terakhir pada sidebar secara realtime.
4. **Command Telegram Baru (/owner):** Mengirimkan ringkasan Owner Control Room (Status bisnis, keuangan, prioritas operasional, dan action plan) secara langsung melalui bot Telegram.

---

## 🔔 Fitur V4B - Telegram Scheduled Report & Alert

Versi **V4B** menambahkan kemampuan otomatisasi pengiriman informasi operasional dan alert kritis langsung ke Telegram owner/admin:
1. **Scheduled Daily Report:** Bot mengirim ringkasan finansial harian beserta lampiran PDF laporan harian otomatis pada jam tertentu (Default: `08:00` WIB, Timezone: `Asia/Jakarta`). Command: `/daily_on`, `/daily_off`, `/set_daily_time HH:MM`, `/send_now`.
2. **Closing Report Sore:** Ringkasan penjualan, profit, margin bersih, produk terlaris hari ini, serta jumlah stok/bahan baku kritis untuk persiapan operasional besok pagi (Default: `17:00` WIB). Command: `/closing_on`, `/closing_off`, `/set_closing_time HH:MM`.
3. **Alert Check:** Deteksi otomatis kondisi anomali bisnis (stok kritis, bahan kritis, iklan boncos, margin rendah < 25%, data health check error) secara real-time. Command: `/alert_check`.
4. **Schedule Status & Send Now:** Meninjau konfigurasi jadwal aktif dan list target chat ID (`/schedule_status`) serta mengirimkan summary instan (`/send_now`).
5. **Allowed Chat ID target:** Mendukung pembatasan chat whitelist (`ALLOWED_CHAT_IDS` di `.env`). Jika kosong, bot akan menyimpan target penerima laporan terjadwal dari user yang mengaktifkannya (`/daily_on`/`/closing_on`) secara runtime di `runtime_bot_settings.json`.

---

## 📊 Fitur V5A - Finance & Tax Readiness Pack

Versi **V5A** menambahkan modul laporan keuangan (Laba Rugi) dan simulasi kesiapan perpajakan untuk membantu persiapan laporan SPT Tahunan:
1. **Laporan Laba Rugi Tahunan/Bulanan:** Menyajikan ringkasan Penjualan Bruto, Diskon, Penjualan Bersih, HPP, Laba Kotor, Biaya Marketplace, Biaya Iklan, Biaya Packing, Biaya Operasional (Expenses), Laba Bersih Sebelum Pajak, Estimasi Pajak, dan Laba Bersih Setelah Pajak.
2. **Simulasi PPh Final UMKM:** Menghitung otomatis beban PPh Final 0,5% dari peredaran bruto bulanan/tahunan berdasarkan PP 55/2022.
3. **Simulasi PPN (PKP & Non-PKP):** Menganalisis kewajiban PKP berdasarkan threshold omzet tahunan Rp 4,8 Miliar. Jika status PKP aktif, menyajikan simulasi PPN Keluaran, PPN Masukan, dan estimasi kurang/lebih bayar.
4. **Tax Readiness Checklist:** Memandu kelengkapan berkas administrasi dasar (data penjualan 12 bulan, expenses, tax settings, tax payments, konsistensi SKU) sebelum pelaporan SPT Tahunan.
5. **Ekspor Laporan Lengkap:** Mendukung download ringkasan teks (`.txt`), ringkasan bulanan pajak (`.csv`), dan PDF Laporan Laba Rugi & Tax Readiness (`.pdf`) secara instan.
6. **Command Telegram Baru:** Perintah baru `/finance`, `/tax`, `/tax_report`, `/spt_check`, serta integrasi NLP keyword untuk memudahkan akses via Telegram.
7. **Panduan Setup Lengkap:** Lihat panduan detail pengisian tab Google Sheets di berkas [FINANCE_TAX_SETUP.md](file:///C:/AI%20PROJECT/parfum_ai_dashboard_demo/FINANCE_TAX_SETUP.md).

---

## 💼 Fitur V5B - Finance & Tax Google Sheets Template + SPT Attachment Pack

Versi **V5B** melengkapi modul keuangan dengan template tab terintegrasi dan paket dokumen lampiran pendukung SPT:
1. **Template CSV & Google Sheets:** Menambahkan data dummy realistis (12 bulan tahun 2026, 30-60 baris) untuk tab `expenses`, `tax_settings`, dan `tax_payments`.
2. **SPT Attachment Pack di Dashboard:** Section baru di menu Finance & Tax yang menyajikan rekap omzet bulanan/tahunan, laba rugi ringkas, biaya operasional, estimasi PPh Final, setoran pajak, dan checklist kesiapan SPT.
3. **Ekspor Attachment Lengkap:** Menyediakan tombol download untuk:
   * **SPT Summary TXT** (`spt_summary_2026.txt`)
   * **Monthly Omzet CSV** (`monthly_omzet_2026.csv`)
   * **Expenses Recap CSV** (`expenses_recap_2026.csv`)
   * **Tax Payments CSV** (`tax_payments_2026.csv`)
   * **SPT Attachment PDF** (`spt_attachment_pack_2026.pdf`)
4. **Telegram command /spt_pack:** Perintah bot untuk membuat dan mengirim PDF Attachment Pack beserta disclaimer. Mengenali keyword natural seperti *"lampiran spt"*, *"paket spt"*, atau *"rekap spt"*.
5. **Update /spt_check:** Menampilkan status tab `expenses`, `tax_settings`, dan `tax_payments`, status setoran pajak terdaftar, serta daftar dokumen yang kurang untuk SPT.
6. **Validasi Data Health Check:** Validasi expenses nominal <= 0 (Warning), pembayaran pajak < 0 (Error), key tax_settings penting hilang (Warning), dan format kolom `tax_deductible` (Warning).
7. **Script QA Otomatis:** File `scripts/qa_v5b_spt_pack.py` untuk menguji fungsionalitas SPT pack secara otomatis tanpa crash.
8. **Panduan Setup Lengkap:** Selengkapnya di berkas [FINANCE_TAX_SETUP.md](file:///C:/AI%20PROJECT/parfum_ai_dashboard_demo/FINANCE_TAX_SETUP.md).

---

## 🔒 Fitur V5C - Security Foundation

Versi **V5C** menambahkan lapisan otentikasi, otorisasi, manajemen role, dan alur konfirmasi aman:
1. **Streamlit Login & Role Permissions:** Dashboard menggunakan login username dan PBKDF2 password hash. Menu sidebar disesuaikan berdasarkan role (`owner`, `staff`, `viewer`). Hak akses viewer dibatasi *readonly* dan tidak boleh mengunduh/ekspor laporan sensitif. Jika auth belum dikonfigurasi, dashboard otomatis berjalan dalam *Demo Mode* tanpa crash.
2. **Telegram Auto Chat ID Detection:** Telegram Bot mendeteksi chat ID pengirim secara otomatis saat mengetik `/start` atau perintah apa pun.
3. **Setup Mode & Bootstrap:** Jika bot dijalankan pertama kali tanpa owner terdaftar di `.env`, bot otomatis masuk ke *Setup Mode* dan menginstruksikan pengguna untuk menambahkan chat ID mereka ke `OWNER_CHAT_IDS` di `.env`.
4. **Invite Code & Activation Flow:** Owner dapat membuat kode undangan sekali pakai (misal: `STAFF-XXXXX` atau `VIEWER-YYYYY`) yang berlaku 15 menit menggunakan `/create_invite staff/viewer`. User baru melakukan aktivasi via `/activate KODE`, lalu data disimpan di runtime database (`runtime_bot_settings.json`).
5. **Manajemen Hak Akses & Revocation:** Owner dapat meninjau user terdaftar lewat `/list_users` dan mencabut akses user runtime lewat `/revoke_user CHAT_ID`. User dari `.env` terlindungi dari penghapusan runtime.
6. **Command Permissions:** Seluruh command keuangan/pajak (`/finance`, `/tax`, `/tax_report`, `/spt_check`, `/spt_pack`) dan penjadwalan (`/daily_on`, `/closing_on`, dll.) hanya diizinkan untuk role `owner`.
7. **Audit Log & Confirmation Foundations:** Modul audit log (`modules/audit_log.py`) mencatat riwayat aksi sensitif. Alur konfirmasi ganda (`modules/confirmation.py`) menggunakan kode 6 digit berlaku 10 menit untuk tindakan operasional penting (fitur write-back sheets sengaja belum diaktifkan).
8. **Script QA Otomatis:** Script `scripts/qa_v5c_security_foundation.py` memvalidasi 16 skenario uji coba otentikasi, otorisasi, dan invite/activation flow secara instan.
9. **Panduan Keamanan Lengkap:** Selengkapnya di berkas [SECURITY_AND_ROLES.md](file:///C:/AI%20PROJECT/parfum_ai_dashboard_demo/SECURITY_AND_ROLES.md).

---

## 💡 Catatan Data Source & Keamanan
*   **Default Data Dummy**: Semua data keuangan, stok produk, bahan baku, HPP/BOM, performa iklan, dan chatbot yang dimuat secara default merupakan data simulasi/dummy yang terletak di folder `data/`.
*   **Keamanan Data**: Aplikasi ini **tidak** menggunakan atau menyimpan token, API key, kredensial, atau data bisnis nyata secara hardcoded di dalam source code. Data penjualan yang diunggah oleh pengguna (`sales.csv`) hanya diproses di memori RAM server selama sesi peramban berjalan dan tidak disimpan secara permanen, sehingga aman dari risiko kebocoran data.
*   **Template Pengisian**: Jika Anda ingin mengisi data penjualan milik Anda sendiri, gunakan tombol **Template sales.csv** di halaman **Setup Data** sebagai panduan format.
