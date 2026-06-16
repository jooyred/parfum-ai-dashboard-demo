# Setup Telegram Bot - AI Business Control Tower (V5A)

Panduan ini menjelaskan cara melakukan setup, mendapatkan token Telegram, dan menjalankan Telegram Bot secara lokal untuk memantau performa bisnis, laporan keuangan, dan kesiapan pajak usaha Anda.

---

## 1. Cara Membuat Bot di BotFather & Mendapatkan Token
Untuk mengaktifkan Telegram Bot, Anda memerlukan token HTTP API dari Telegram.
1. Buka aplikasi **Telegram** Anda.
2. Cari user **`@BotFather`** (pastikan terdapat centang biru verifikasi resmi).
3. Mulai chat dengan mengirimkan command:
   ```text
   /newbot
   ```
4. Masukkan nama bot Anda (contoh: `Parfum AI Control Tower`).
5. Masukkan username unik untuk bot Anda yang diakhiri kata `bot` atau `_bot` (contoh: `parfum_control_tower_bot` atau `parfum_ai_demo_bot`).
6. Setelah sukses, **BotFather** akan mengirimkan pesan berisi token akses HTTP API Anda. Token ini berbentuk seperti:
   `1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ`
7. **Simpan token ini secara aman.** Jangan pernah membagikannya ke publik atau men-commit-nya ke GitHub.

---

## 2. Cara Membuat File Konfigurasi `.env`
1. Di root project folder (`C:\AI PROJECT\parfum_ai_dashboard_demo`), temukan file template `.env.example`.
2. Buat duplikat file tersebut (copy & paste) lalu ubah namanya menjadi **`.env`**.
3. Buka file `.env` menggunakan Notepad atau editor teks pilihan Anda.
4. Masukkan konfigurasi Telegram Bot Anda:
   ```env
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
   OWNER_CHAT_IDS=
   STAFF_CHAT_IDS=
   VIEWER_CHAT_IDS=
   ```
5. Simpan file tersebut. File `.env` ini secara otomatis sudah dimasukkan ke `.gitignore` sehingga aman dan tidak akan ter-commit ke Git.

---

## 3. Cara Bootstrap Owner Pertama & Mengisi Chat ID
Untuk mempermudah setup tanpa mencari Chat ID secara manual, ikuti alur **Auto Chat ID Detection**:

1. Pastikan berkas `.env` sudah dibuat dengan baris `OWNER_CHAT_IDS` dikosongkan.
2. Jalankan bot secara lokal:
   ```bash
   python telegram_bot.py
   ```
3. Buka Telegram, cari bot Anda, dan klik atau kirim perintah `/start`.
4. Bot akan mendeteksi bahwa belum ada owner yang terdaftar, lalu otomatis masuk ke **Setup Mode** dan membalas chat Anda:
   > 🤖 **Bot Setup Mode**  
   > OWNER_CHAT_IDS belum dikonfigurasi di file .env.  
   > Chat ID Anda: `987654321`  
   > Silakan masukkan chat ID ini ke OWNER_CHAT_IDS di file .env, lalu restart bot.
5. Salin Chat ID Anda (`987654321`), lalu masukkan ke berkas `.env` Anda:
   ```env
   OWNER_CHAT_IDS=987654321
   ```
6. Hentikan bot (tekan `Ctrl+C` di terminal) dan jalankan kembali: `python telegram_bot.py`.
7. Sekarang Anda telah resmi terdaftar sebagai **Owner Utama** permanen.

---

## 4. Alur Mengundang Staff & Viewer Baru
Setelah Owner Utama terdaftar, Anda tidak perlu meminta staff atau viewer mencari Chat ID mereka secara manual. Cukup gunakan alur undang-aktivasi:

1. **Owner membuat kode undangan** di Telegram Bot dengan mengetik:
   * `/create_invite staff` (untuk mendaftarkan Staff) -> menghasilkan kode contoh: `STAFF-7K29Q`
   * `/create_invite viewer` (untuk mendaftarkan Viewer) -> menghasilkan kode contoh: `VIEWER-3P10L`
2. **Kirimkan kode tersebut** ke staff atau viewer Anda.
3. **Staff/Viewer baru** membuka bot Telegram tersebut, menekan `/start`, lalu mengetik perintah:
   ```text
   /activate STAFF-7K29Q
   ```
4. Bot secara otomatis membaca Chat ID perangkat mereka, memverifikasi kecocokan kode yang belum expired (berlaku 15 menit), lalu mendaftarkannya ke role terkait secara instan.
5. Owner dapat melihat daftar user aktif dengan `/list_users` dan mencabut akses user runtime lewat `/revoke_user CHAT_ID`.

---

## 4. Cara Menjalankan Bot Secara Lokal
1. Buka Terminal/PowerShell di folder project (`C:\AI PROJECT\parfum_ai_dashboard_demo`).
2. Pastikan virtual environment Anda aktif:
   * **PowerShell**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   * **Command Prompt (CMD)**:
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
3. Jalankan script bot:
   ```bash
   python telegram_bot.py
   ```
4. Anda akan melihat pesan log:
   `Telegram Bot berjalan aktif secara lokal. Tekan Ctrl+C untuk menghentikan.`

> [!IMPORTANT]
> Selama bot berjalan di terminal lokal Anda, terminal tersebut **harus tetap terbuka**. Jika terminal ditutup atau komputer mati, bot akan offline dan tidak merespon di Telegram.

---

## 5. Uji Coba Command & Fitur
Buka bot Telegram Anda yang baru saja dibuat, lalu uji perintah-perintah berikut:

### Menu Command Inti:
* `/start` - Menampilkan pesan pembuka.
* `/help` - Menampilkan daftar perintah lengkap.
* `/owner` - 👑 Menampilkan ringkasan Owner Control Room (Keputusan harian, keuangan, prioritas, dan 5 rencana aksi).
* `/summary` - Menampilkan metrik finansial, status bisnis, dan 3 action plan teratas.
* `/report` - Mengirim file PDF laporan harian langsung ke chat Anda.
* `/alert_check` - 🚨 Memeriksa anomali operasional Google Sheets (stok kritis, bahan kritis, iklan boncos, margin rendah, data health error) dan mengirim ringkasan alert.

### Fitur Keuangan & Pajak (V5A & V5B):
* `/finance` - 📊 Mengirimkan ringkasan metrik laporan laba rugi tahun ini.
* `/tax` - 🧾 Mengirimkan simulasi perpajakan (PPh Final UMKM dan readiness PPN).
* `/tax_report` - 📄 Mengirimkan file PDF Laporan Keuangan & Pajak tahun ini.
* `/spt_check` - 📋 Mengirimkan checklist dokumen administrasi wajib untuk pelaporan SPT Tahunan, lengkap dengan status tab dan setoran pajak terdaftar.
* `/spt_pack` - 💼 Mengirimkan file PDF Paket Lampiran Pendukung SPT Usaha tahun ini.

### Fitur Penjadwalan Laporan Otomatis (V4B):
* `/daily_on` - Mengaktifkan laporan otomatis harian (mengirim metrik harian + PDF).
* `/daily_off` - Mematikan laporan otomatis harian.
* `/set_daily_time HH:MM` - Mengatur jam kirim laporan otomatis harian (contoh: `/set_daily_time 08:00`).
* `/closing_on` - Mengaktifkan closing report otomatis sore hari.
* `/closing_off` - Mematikan closing report otomatis sore hari.
* `/set_closing_time HH:MM` - Mengatur jam kirim closing report sore (contoh: `/set_closing_time 17:00`).
* `/schedule_status` - Menampilkan status keaktifan jadwal harian & closing, jam target, allowed target chat ID, dan timezone.
* `/send_now` - Mengirimkan laporan owner summary + PDF laporan saat ini juga tanpa menunggu jam terjadwal.

> [!NOTE]
> * **Default Timezone**: `Asia/Jakarta` (WIB).
> * **Default Daily Report Time**: `08:00`.
> * **Default Closing Report Time**: `17:00`.

### Menu Detail Lainnya:
* `/top_products` - Menampilkan 5 produk terlaris hari ini.
* `/stock` - Menampilkan daftar produk jadi dengan stok kritis.
* `/materials` - Menampilkan status bahan baku dan nominal rencana belanja.
* `/production` - Menampilkan rekomendasi jumlah produksi per SKU.
* `/ads` - Menampilkan efisiensi ROAS dan status kampanye iklan.

### Uji Coba Pertanyaan Natural Language (Ketik Biasa):
Coba ketik pesan teks biasa berikut ke chat bot:
* `profit hari ini`
* `stok kritis`
* `bahan baku apa yang harus dibeli`
* `buat laporan` atau `kirim pdf`
* `apa yang harus dilakukan hari ini` (memicu control room /owner)
* `laporan keuangan` atau `laba rugi` (memicu /finance)
* `pajak` atau `pph final` atau `ppn` (memicu /tax)
* `spt` atau `checklist pajak` (memicu /spt_check)
* `lampiran spt` atau `paket spt` atau `rekap spt` (memicu /spt_pack)

---

## 6. Catatan Operasional & Deployment Produksi
* **Running Lokal**: Laporan terjadwal otomatis hanya aktif selama proses `python telegram_bot.py` hidup di terminal Anda. Jika terminal ditutup atau komputer mati/sleep, scheduler tidak berjalan.
* **Role Otorisasi & Akses**:
  * Whitelist data diatur melalui berkas `.env` (`OWNER_CHAT_IDS`, `STAFF_CHAT_IDS`, `VIEWER_CHAT_IDS`) dan secara dinamis via kode aktivasi yang disimpan pada berkas lokal `runtime_bot_settings.json` (telah dimasukkan ke `.gitignore`).
  * Hanya Chat ID yang terdaftar sebagai owner, staff, atau viewer yang bisa berinteraksi dengan bot. Command dari user lain yang belum diaktifkan akan ditolak dengan pesan instruksi aktivasi.
  * Laporan harian/closing otomatis hanya dikirimkan ke Chat ID yang aktif dan memiliki otorisasi valid.
* **Deployment Produksi**: Untuk memastikan bot berjalan 24 jam tanpa henti, deploy aplikasi ke server cloud seperti **VPS** (menggunakan PM2/systemd), **Render**, atau **Railway** sebagai background service/worker. Pastikan untuk memindahkan pengaturan environment variables ke panel platform masing-masing.
