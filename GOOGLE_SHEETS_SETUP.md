# Panduan Setup Google Sheets Data Source (V3A)

Aplikasi "AI Business Control Tower" mendukung sinkronisasi data real-time menggunakan Google Sheets sebagai data source utama. Dokumentasi ini memandu Anda membuat lembar kerja, mengonfigurasi Service Account Google Cloud, dan mengamankan kredensial Anda.

---

## 1. Persiapan Google Spreadsheet

### A. Membuat Spreadsheet & Tab Wajib
1. Buat spreadsheet baru di Google Drive Anda.
2. Buat **7 sheet (tab)** di dalam spreadsheet tersebut dengan nama persis seperti berikut:
   *   **`products`**
   *   **`sales`**
   *   **`inventory_products`**
   *   **`inventory_materials`**
   *   **`bom_hpp`**
   *   **`ads`**
   *   **`production_plan`**

### B. Daftar Kolom Wajib Setiap Tab
Pastikan baris pertama pada setiap tab berisi header kolom berikut (huruf kecil):

1. **`products`**:
   `sku`, `product`, `size`, `category`, `price`, `hpp`, `target_margin`
2. **`sales`**:
   `date`, `platform`, `order_id`, `sku`, `product`, `qty`, `price`, `discount`, `marketplace_fee`, `packing_cost`, `ad_cost_allocated`, `hpp`, `gross_revenue`, `net_revenue`, `net_profit`, `net_margin`, `order_status`
3. **`inventory_products`**:
   `sku`, `product`, `stock`, `min_stock`, `avg_daily_sold`
4. **`inventory_materials`**:
   `material`, `unit`, `stock`, `min_stock`, `unit_cost`
5. **`bom_hpp`**:
   `sku`, `component`, `unit`, `qty_usage`, `component_cost`
6. **`ads`**:
   `platform`, `campaign`, `spend`, `revenue`, `orders`, `roas`, `status`
7. **`production_plan`**:
   `sku`, `product`, `demand_7d`, `stock`, `recommended_production`, `bottleneck`

*Catatan: Anda dapat menyalin data awal dari file CSV template di folder `data/` project ini.*

---

## 2. Konfigurasi Google Cloud & Service Account

Sistem membutuhkan kredensial Service Account untuk membaca data dari Google Sheets API secara aman.

### A. Membuat Service Account
1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Buat project baru (atau pilih project yang sudah ada).
3. Cari dan aktifkan **Google Sheets API** dan **Google Drive API** melalui API Library.
4. Masuk ke menu **IAM & Admin** > **Service Accounts**.
5. Klik **"Create Service Account"**:
   * Masukkan nama (misalnya `parfum-dashboard-loader`).
   * Klik **Create and Continue**, lalu **Done**.
6. Klik pada Service Account yang baru dibuat, masuk ke tab **Keys**, klik **Add Key** > **Create new key** > Pilih tipe **JSON** > Klik **Create**.
7. File JSON berisi kredensial Service Account akan otomatis terunduh ke komputer Anda.

### B. Membagikan Akses Spreadsheet
1. Buka file JSON credentials yang diunduh tadi, cari kolom `"client_email"` (misalnya `parfum-dashboard-loader@project-id.iam.gserviceaccount.com`).
2. Buka Google Spreadsheet data parfum Anda, klik tombol **Bagikan (Share)** di pojok kanan atas.
3. Tempelkan email service account tersebut, berikan peran sebagai **Editor** atau **Viewer**, hilangkan opsi kirim notifikasi, lalu klik **Bagikan/Kirim**.

---

## 3. Konfigurasi Kredensial (Secrets)

> [!WARNING]
> **Catatan Keamanan Penting:** Jangan pernah meletakkan berkas credentials JSON Anda langsung di dalam direktori project atau meng-commit-nya ke GitHub! Hal ini dapat menyebabkan kebocoran kredensial cloud Anda.

### A. Uji Coba Lokal (secrets.toml)
Streamlit membaca berkas `.streamlit/secrets.toml` secara lokal untuk mengimulasi secret environment. Berkas ini sudah masuk ke `.gitignore` sehingga tidak akan di-upload ke GitHub.

1. Buka folder `.streamlit/` di root project.
2. Buat berkas baru bernama `secrets.toml`.
3. Tulis data berikut dengan menyalin isi berkas JSON credentials Anda ke format TOML:
   ```toml
   # .streamlit/secrets.toml

   GOOGLE_SHEET_ID = "MASUKKAN_ID_SPREADSHEET_ANDA"

   [google_service_account]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "..."
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."
   universe_domain = "googleapis.com"
   ```
4. Jalankan aplikasi Streamlit secara lokal. Jika format benar, aplikasi akan langsung melakukan auto-load ke Google Sheets Anda.

### B. Deployment ke Streamlit Community Cloud
1. Masuk ke dashboard [Streamlit Share](https://share.streamlit.io/).
2. Cari aplikasi Anda, klik tombol menu tiga titik (**...**) > Pilih **Settings** > Masuk ke tab **Secrets**.
3. Tempelkan seluruh isi dari berkas `secrets.toml` lokal ke area input teks Secrets.
4. Klik **Save**. Aplikasi di Streamlit Cloud akan melakukan restart otomatis dan membaca Google Sheets Anda.
