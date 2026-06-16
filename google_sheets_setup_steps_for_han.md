# Setup Google Sheets Data Source - AI Business Control Tower Parfum

## File yang disediakan
- `google_sheets_template_parfum_v3a.xlsx`
- `streamlit_secrets_template_google_sheets.txt`

## 1. Buat Google Sheets template real
1. Buka Google Drive.
2. Upload file `google_sheets_template_parfum_v3a.xlsx`.
3. Klik kanan file > Open with > Google Sheets.
4. Google akan membuat spreadsheet dengan tab:
   - products
   - sales
   - inventory_products
   - inventory_materials
   - bom_hpp
   - ads
   - production_plan

## 2. Isi data dummy ke Google Sheets
File template sudah berisi data dummy. Untuk test awal, jangan ubah dulu. Setelah koneksi sukses, baru edit beberapa angka untuk membuktikan dashboard berubah.

Contoh test mudah:
- Ubah `products!price` untuk salah satu SKU.
- Ubah `inventory_products!stock` untuk salah satu produk.
- Ubah beberapa baris di `sales`.
- Save otomatis oleh Google Sheets.
- Klik Refresh Google Sheets Data di dashboard.

## 3. Buat Service Account
1. Buka Google Cloud Console.
2. Buat project baru, misalnya `parfum-dashboard-demo`.
3. Aktifkan Google Sheets API.
4. Aktifkan Google Drive API bila loader membutuhkan akses spreadsheet via gspread.
5. Buka IAM & Admin > Service Accounts.
6. Create service account.
7. Masuk ke service account tersebut > Keys > Add key > Create new key > JSON.
8. Download file JSON credentials.

## 4. Share Google Sheets ke service account
1. Buka file JSON credentials.
2. Cari field `client_email`.
3. Copy email tersebut.
4. Buka Google Sheets template.
5. Klik Share.
6. Share ke email `client_email` sebagai Viewer atau Editor.
   - Viewer cukup untuk dashboard baca data.
   - Editor hanya perlu kalau app nanti ingin menulis ke Sheets.

## 5. Isi `.streamlit/secrets.toml` lokal
1. Di folder project lokal, buat folder `.streamlit` jika belum ada.
2. Buat file:
   `.streamlit/secrets.toml`
3. Copy isi dari `streamlit_secrets_template_google_sheets.txt`.
4. Ganti `GOOGLE_SHEET_ID` dengan ID spreadsheet.
5. Isi bagian `[google_service_account]` dari JSON credentials.

Spreadsheet ID bisa diambil dari URL:
`https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit...`

## 6. Test lokal
Jalankan:

```powershell
cd "C:\AI PROJECT\parfum_ai_dashboard_demo"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Cek:
- Sidebar menampilkan Data Source: Google Sheets.
- Setup Data bisa preview tab Google Sheets.
- Dashboard Overview berubah mengikuti data Sheets.
- Chatbot menjawab memakai data Sheets.
- Laporan Harian PDF memakai data Sheets.

## 7. Isi Secrets di Streamlit Cloud
1. Buka Streamlit Community Cloud.
2. Buka app `parfum-ai-dashboard-demo`.
3. Masuk ke Settings > Secrets.
4. Paste seluruh isi `.streamlit/secrets.toml` lokal.
5. Save.
6. App akan redeploy/restart.

## 8. Test live app
Buka:
https://parfum-ai-dashboard-demo.streamlit.app/

Cek:
- Sidebar berubah ke Google Sheets.
- Klik Refresh Google Sheets Data.
- Ubah data di Google Sheets, lalu refresh di app.
- Cek Dashboard, Chatbot, dan PDF report.

## 9. Baru lanjut Telegram Bot
Setelah Google Sheets stabil, baru lanjut Telegram bot. Bot nanti akan baca Google Sheets yang sama sehingga angka dashboard dan bot konsisten.

## Catatan keamanan
- Jangan commit `.streamlit/secrets.toml`.
- Jangan upload credentials JSON ke GitHub.
- Jangan share private_key.
- Untuk demo publik, tetap gunakan data dummy atau data yang sudah disamarkan.
