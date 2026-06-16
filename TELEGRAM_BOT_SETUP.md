# Setup Telegram Bot - AI Business Control Tower (V3B)

Panduan ini menjelaskan cara melakukan setup, mendapatkan token Telegram, dan menjalankan Telegram Bot secara lokal untuk memantau performa bisnis parfum Anda.

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
4. Masukkan token Telegram Bot Anda pada baris `TELEGRAM_BOT_TOKEN`:
   ```env
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
   ALLOWED_CHAT_IDS=
   ```
5. Simpan file tersebut. File `.env` ini secara otomatis sudah dimasukkan ke `.gitignore` sehingga aman dan tidak akan ter-commit ke Git.

---

## 3. Cara Mendapatkan Chat ID & Mengisi Whitelist (`ALLOWED_CHAT_IDS`)
Untuk alasan keamanan data, Anda dapat membatasi akses bot agar hanya membalas Chat ID Anda sendiri (atau tim tertentu).

### Cara mendapatkan Chat ID Anda:
1. Cari user **`@userinfobot`** di Telegram Anda.
2. Klik **Start**. Bot tersebut akan membalas dengan menampilkan **Id** Anda (berupa baris angka unik, misal: `987654321`).
3. Salin angka tersebut.

### Mengisi Whitelist di `.env`:
* Jika baris `ALLOWED_CHAT_IDS` dikosongkan (default), bot akan merespon semua orang yang mencoba menggunakan bot Anda (berguna untuk demo lokal).
* Jika Anda ingin membatasi akses hanya untuk Anda saja, masukkan Chat ID ke dalam file `.env`:
  ```env
  ALLOWED_CHAT_IDS=987654321
  ```
* Jika ada beberapa user, pisahkan dengan koma:
  ```env
  ALLOWED_CHAT_IDS=987654321,11223344
  ```

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

---

## 6. Catatan Operasional & Deployment Produksi
* **Running Lokal**: Laporan terjadwal otomatis hanya aktif selama proses `python telegram_bot.py` hidup di terminal Anda. Jika terminal ditutup atau komputer mati/sleep, scheduler tidak berjalan.
* **Allowed Chat ID**:
  * Jika `ALLOWED_CHAT_IDS` di berkas `.env` kosong, bot hanya akan mengirimkan laporan terjadwal otomatis ke Chat ID dari user yang mengaktifkannya via `/daily_on` atau `/closing_on`. Chat ID target disimpan sementara secara lokal di `runtime_bot_settings.json` (telah dimasukkan ke `.gitignore`).
  * Jika `ALLOWED_CHAT_IDS` terisi, hanya Chat ID yang ada di whitelist tersebut yang bisa berinteraksi dengan bot, sedangkan command dari Chat ID lain akan ditolak dengan sopan.
* **Deployment Produksi**: Untuk memastikan bot berjalan 24 jam tanpa henti, deploy aplikasi ke server cloud seperti **VPS** (menggunakan PM2/systemd), **Render**, atau **Railway** sebagai background service/worker. Pastikan untuk memindahkan pengaturan environment variables ke panel platform masing-masing.
