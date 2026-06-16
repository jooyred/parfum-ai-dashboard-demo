# AI Business Control Tower — Demo Bisnis Parfum (V2)

Aplikasi dashboard dan chatbot AI interaktif untuk mengontrol performa bisnis parfum, dirancang khusus untuk mempermudah owner memantau keuangan, stok, HPP, produksi, dan kampanye iklan. Versi V2 ini hadir dengan peningkatan UI/UX premium ala SaaS, validasi upload data transaksi, dan ekspor laporan ke PDF.

## 🔗 Live Demo
Aplikasi ini telah dideploy secara online dan dapat diakses di:
**[https://parfum-ai-dashboard-demo.streamlit.app/](https://parfum-ai-dashboard-demo.streamlit.app/)**

> [!WARNING]
> **Catatan Keamanan:** Demo ini menggunakan data dummy secara default. Jangan mengunggah data bisnis real atau sensitif Anda ke demo publik ini sebelum sistem login/autentikasi terintegrasi.

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

## 🤖 Telegram Bot (V3B & V4A) - Pemantau Bisnis & Keputusan Lokal

Aplikasi ini dilengkapi dengan **Telegram Bot** agar owner dapat memantau performa bisnis, melihat keputusan harian (Control Room), dan mengunduh laporan PDF harian langsung dari Telegram secara real-time (membaca data dari Google Sheets yang sama).

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

## 💡 Catatan Data Source & Keamanan
*   **Default Data Dummy**: Semua data keuangan, stok produk, bahan baku, HPP/BOM, performa iklan, dan chatbot yang dimuat secara default merupakan data simulasi/dummy yang terletak di folder `data/`.
*   **Keamanan Data**: Aplikasi ini **tidak** menggunakan atau menyimpan token, API key, kredensial, atau data bisnis nyata secara hardcoded di dalam source code. Data penjualan yang diunggah oleh pengguna (`sales.csv`) hanya diproses di memori RAM server selama sesi peramban berjalan dan tidak disimpan secara permanen, sehingga aman dari risiko kebocoran data.
*   **Template Pengisian**: Jika Anda ingin mengisi data penjualan milik Anda sendiri, gunakan tombol **Template sales.csv** di halaman **Setup Data** sebagai panduan format.
