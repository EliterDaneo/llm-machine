# 📁 Struktur Folder PDF Intelligence App

Panduan lengkap letak setiap file agar tidak salah tempat.

---

## 🗂️ Gambaran Besar

```
pdf-intelligence-app/
├── backend/          ← Semua kode Python (FastAPI)
└── frontend/         ← Semua kode Next.js (React)
```

---

## 🐍 BACKEND (Python + FastAPI)

```
backend/
│
├── .env                        ← API keys & konfigurasi (JANGAN di-commit ke Git)
├── .env.example                ← Template .env (aman di-commit)
├── requirements.txt            ← Daftar library Python
├── alembic.ini                 ← Konfigurasi migrasi database (production)
├── README.md                   ← Panduan setup backend
│
└── app/                        ← Package utama aplikasi
    │
    ├── __init__.py             ← Penanda Python package (isi kosong)
    ├── main.py                 ← 🚀 Entry point — jalankan file ini
    │
    ├── core/                   ← Konfigurasi & utilitas inti
    │   ├── __init__.py
    │   ├── config.py           ← Baca .env, setting global app
    │   └── security.py         ← JWT token, hash password, cek login
    │
    ├── db/                     ← Semua yang berhubungan dengan database
    │   ├── __init__.py
    │   ├── database.py         ← Koneksi ke PostgreSQL, session factory
    │   └── models.py           ← Skema tabel: User, Quota, Document, dll
    │
    ├── services/               ← Logika bisnis utama (bukan endpoint)
    │   ├── __init__.py
    │   ├── pdf_extractor.py    ← Ekstrak teks dari PDF (pakai PyMuPDF)
    │   └── ai_orchestrator.py  ← Router AI: Gemini → Groq → fallback
    │
    └── api/                    ← Endpoint HTTP (route handler)
        ├── __init__.py
        ├── auth.py             ← /auth/register, /auth/login, /auth/me, dll
        └── documents.py        ← /documents/upload, /analyze, /chat, dll
```

---

## ⚡ Penjelasan Setiap File

### Root Backend

| File               | Fungsi                                                                                        |
| ------------------ | --------------------------------------------------------------------------------------------- |
| `.env`             | Simpan `GEMINI_API_KEY`, `DATABASE_URL`, `SECRET_KEY`, dll. **Tidak boleh di-push ke GitHub** |
| `.env.example`     | Versi kosong `.env` sebagai template untuk tim                                                |
| `requirements.txt` | Jalankan `pip install -r requirements.txt` untuk install semua library                        |
| `alembic.ini`      | Dipakai saat migrasi database di production (opsional saat development)                       |

---

### `app/main.py` — Entry Point 🚀

- File yang dijalankan: `uvicorn app.main:app --reload`
- Mendaftarkan semua router (`auth`, `documents`)
- Mengatur CORS, middleware, error handler
- Menjalankan `init_db()` saat startup (development)

---

### `app/core/config.py` — Konfigurasi

- Membaca semua nilai dari file `.env`
- Menyediakan object `settings` yang dipakai di seluruh app
- Contoh: `settings.GEMINI_API_KEY`, `settings.DATABASE_URL`

---

### `app/core/security.py` — Keamanan

- `hash_password()` — enkripsi password dengan bcrypt
- `verify_password()` — cek password saat login
- `create_access_token()` — buat JWT token
- `get_current_user()` — FastAPI dependency untuk cek siapa yang login

---

### `app/db/database.py` — Koneksi Database

- Membuat koneksi async ke PostgreSQL
- Menyediakan `get_db()` — dependency untuk tiap endpoint yang butuh DB
- `init_db()` — auto-buat tabel saat development

---

### `app/db/models.py` — Skema Tabel

| Model            | Tabel              | Isi                                                   |
| ---------------- | ------------------ | ----------------------------------------------------- |
| `User`           | `users`            | Email, username, password, plan (free/pro/enterprise) |
| `Quota`          | `quotas`           | Sisa kuota harian, total analisis, storage terpakai   |
| `Document`       | `documents`        | Info file PDF, teks hasil ekstraksi, status           |
| `AnalysisResult` | `analysis_results` | Hasil analisis AI, provider yang dipakai, tokens      |
| `ChatHistory`    | `chat_histories`   | Riwayat chat per sesi, feedback like/dislike          |

---

### `app/services/pdf_extractor.py` — Ekstraksi PDF

- Menerima file PDF yang diupload
- Mengekstrak teks, metadata, jumlah halaman
- Mendeteksi bahasa (Indonesia / Inggris)
- Memecah teks panjang jadi chunks untuk AI

---

### `app/services/ai_orchestrator.py` — Router AI

- Mencoba **Gemini** dulu → jika gagal, otomatis ke **Groq**
- Mode analisis: `summary`, `key_points`, `recommendations`, `chat`
- Semua prompt tersedia dalam Bahasa Indonesia
- Method `chat()` untuk percakapan multi-turn dengan konteks

---

### `app/api/auth.py` — Endpoint Autentikasi

| Method   | Path                       | Fungsi                 |
| -------- | -------------------------- | ---------------------- |
| `POST`   | `/api/v1/auth/register`    | Daftar akun baru       |
| `POST`   | `/api/v1/auth/login`       | Login, dapat JWT token |
| `POST`   | `/api/v1/auth/refresh`     | Perpanjang token       |
| `GET`    | `/api/v1/auth/me`          | Lihat profil sendiri   |
| `PUT`    | `/api/v1/auth/me`          | Update nama / username |
| `PUT`    | `/api/v1/auth/me/password` | Ganti password         |
| `DELETE` | `/api/v1/auth/me`          | Nonaktifkan akun       |

---

### `app/api/documents.py` — Endpoint Dokumen & Chat

| Method   | Path                                           | Fungsi                       |
| -------- | ---------------------------------------------- | ---------------------------- |
| `POST`   | `/api/v1/documents/upload`                     | Upload file PDF              |
| `POST`   | `/api/v1/documents/analyze`                    | Analisis AI (ringkasan, dll) |
| `POST`   | `/api/v1/documents/chat`                       | Chat dengan dokumen          |
| `PUT`    | `/api/v1/documents/chat/{id}/feedback`         | Like/dislike jawaban AI      |
| `GET`    | `/api/v1/documents/`                           | Daftar semua dokumen         |
| `GET`    | `/api/v1/documents/history`                    | Riwayat chat & analisis      |
| `GET`    | `/api/v1/documents/stats`                      | Statistik untuk dashboard    |
| `GET`    | `/api/v1/documents/{id}`                       | Detail satu dokumen          |
| `GET`    | `/api/v1/documents/chat/{session_id}/messages` | Isi satu sesi chat           |
| `DELETE` | `/api/v1/documents/{id}`                       | Hapus dokumen                |

---

## ⚛️ FRONTEND (Next.js + React)

> Belum dibuat — ini yang akan dibuat selanjutnya.

```
frontend/
│
├── package.json                ← Daftar library NPM
├── next.config.js              ← Konfigurasi Next.js
├── tailwind.config.js          ← Konfigurasi Tailwind CSS
├── tsconfig.json               ← Konfigurasi TypeScript
│
└── src/
    │
    ├── components/             ← Komponen UI yang bisa dipakai ulang
    │   └── dashboard/
    │       ├── Sidebar.tsx     ← Navigasi kiri (menu, user info)
    │       ├── OverviewStats.tsx ← Statistik tengah (kuota, total dokumen)
    │       └── AnalysisPanel.tsx ← Panel kanan (hasil analisis, copy button)
    │
    └── app/                    ← Halaman (Next.js App Router)
        │
        ├── page.tsx            ← Redirect otomatis ke /dashboard atau /login
        │
        ├── (auth)/             ← Grup halaman publik (tanpa layout dashboard)
        │   ├── login/
        │   │   └── page.tsx    ← Halaman login
        │   └── register/
        │       └── page.tsx    ← Halaman register
        │
        └── dashboard/
            └── page.tsx        ← Halaman utama dashboard
```

---

## 🔄 Alur Data Lengkap

```
User Upload PDF
      │
      ▼
[Frontend] → POST /documents/upload
      │
      ▼
[documents.py] → terima file
      │
      ▼
[pdf_extractor.py] → ekstrak teks, metadata
      │
      ▼
[models.py] → simpan ke tabel documents (PostgreSQL)
      │
      ▼
[Frontend] → POST /documents/analyze
      │
      ▼
[documents.py] → cek quota user
      │
      ▼
[ai_orchestrator.py] → kirim ke Gemini
                              │ gagal?
                              ▼
                           Groq API
      │
      ▼
[models.py] → simpan ke tabel analysis_results
      │
      ▼
[Frontend] → tampilkan hasil + tombol Copy
```

---

## 📋 Urutan Setup

```bash
# 1. Masuk folder backend
cd pdf-intelligence-app/backend

# 2. Buat virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Install library
pip install -r requirements.txt

# 4. Salin dan isi konfigurasi
cp .env.example .env
# Edit .env: isi DATABASE_URL, GEMINI_API_KEY, GROQ_API_KEY, SECRET_KEY

# 5. Buat database di PostgreSQL
# CREATE DATABASE pdf_intelligence;

# 6. Jalankan server
uvicorn app.main:app --reload --port 8000

# 7. Buka dokumentasi API
# http://localhost:8000/docs
```

---

## ⚠️ Aturan Penting

| Aturan                | Penjelasan                                                                    |
| --------------------- | ----------------------------------------------------------------------------- |
| File `.env`           | **Jangan** masukkan ke Git. Sudah ada di `.gitignore`                         |
| File `__init__.py`    | Harus ada di setiap folder dalam `app/` agar Python mengenali sebagai package |
| Folder `__pycache__/` | Otomatis dibuat Python, **abaikan** saja                                      |
| File `alembic.ini`    | Hanya dipakai saat production. Development pakai `init_db()` otomatis         |
| Folder `uploads/`     | Dibuat otomatis saat server pertama dijalankan                                |
