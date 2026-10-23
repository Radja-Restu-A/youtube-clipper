# YouTube Clipper

Otomatisasi pembuatan video klip pendek (*short-form content*) untuk TikTok, Instagram Reels, dan YouTube Shorts dari video YouTube panjang maupun file video lokal, didukung oleh transkripsi AI dan deteksi momen viral.

---

## 1. Deskripsi & Tujuan

### Deskripsi
**YouTube Clipper** adalah aplikasi full-stack yang dirancang untuk memproses video berdurasi panjang dan mengekstrak momen-momen terbaik menjadi beberapa klip siap unggah berdurasi singkat (30–60 detik). 

Selain memotong video, aplikasi ini secara otomatis mentranskripsi audio ke teks menggunakan **OpenAI Whisper**, menghasilkan subtitle dinamis per kata dengan animasi *highlight/outline* bergaya **Opus Clip**, serta memanfaatkan kecerdasan buatan (**Google Gemini 1.5 Flash**) untuk menganalisis konteks video dan memilih segmen dengan potensi viral paling tinggi.

### Tujuan Proyek
- **Efisiensi Konten Kreator**: Menghemat waktu proses kurasi manual dan *editing* video panjang menjadi konten pendek.
- **Deteksi Momen Cerdas**: Memberikan opsi fleksibel dalam pemilihan segmen menarik berdasarkan intensitas audio (volume/keseruan), semantik percakapan, atau analisis viral berbasis LLM.
- **Teks Otomatis Siap Pakai**: Menyediakan subtitle animasi yang langsung menyatu (*burned-in*) ke video tanpa perlu software editing video tambahan.

---

## 2. Fitur Utama

- **Dua Sumber Input Video**:
  - Input URL video YouTube (diunduh otomatis menggunakan `yt-dlp`).
  - Upload file video lokal (mendukung file hingga 2 GB dalam format MP4, MKV, AVI, MOV, WebM, FLV, WMV).
- **3 Mode Deteksi Klip**:
  - **Audio Mode**: Menganalisis gelombang audio dan skor engagement berdasarkan energi suara.
  - **Context Mode**: Mengelompokkan transkrip percakapan berdasarkan bobot dan keterkaitan makna bahasan.
  - **Viral Mode (Google Gemini AI)**: Menggunakan model Gemini 1.5 Flash untuk menganalisis judul, deskripsi, dan isi transkrip demi mencari bagian yang paling memikat (*hook* kuat).
- **Animasi Subtitle ala Opus Clip**:
  - Transkripsi akurat tingkat kata (*word-level timestamps*).
  - Styling subtitle `.ass` yang dinamis (tampil kata per kata dengan kontras dan warna jelas).
  - Pembakaran subtitle langsung ke dalam video (*hardsub*) melalui FFmpeg.
- **Kustomisasi Rentang & Jumlah Klip**:
  - Pilihan rentang video yang ingin diproses (Kuartal 1, 2, 3, 4, atau 100% video utuh).
  - Pengaturan jumlah klip yang dihasilkan (antara 1 hingga 20 klip).
- **Dasbor & Riwayat Interaktif**:
  - Pemantauan progres real-time.
  - Panel riwayat video yang pernah diproses beserta pemutar video (*preview*) dan tautan unduh per klip.

---

## 3. Teknologi yang Digunakan

### Backend
- **Bahasa & Runtime**: Python 3.10+
- **Framework Web**: [FastAPI](https://fastapi.tiangolo.com/), Uvicorn
- **Speech-to-Text**: [OpenAI Whisper](https://github.com/openai/whisper)
- **Generative AI**: [Google Generative AI SDK](https://pypi.org/project/google-generativeai/) (`gemini-1.5-flash`)
- **Pengolah Media**: FFmpeg, `ffmpeg-python`, `yt-dlp`, Librosa, Soundfile
- **Deep Learning / Akselerasi GPU**: PyTorch (mendukung CUDA 11.8)

### Frontend
- **Framework & Build Tool**: React 18, [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Ikon**: Lucide React

---

## 4. Prasyarat Sistem (Prerequisites)

Sebelum menjalankan aplikasi, pastikan sistem Anda telah terpasang:
1. **Python** (versi 3.10 atau lebih baru)
2. **Node.js** (versi 18 atau lebih baru) dan **npm**
3. **FFmpeg** terpasang dan sudah terdaftar di variabel lingkungan (`PATH`) sistem:
   - Verifikasi melalui terminal: `ffmpeg -version`
4. *(Opsional tapi disarankan)* **NVIDIA GPU + CUDA Toolkit** untuk proses transkripsi Whisper yang lebih cepat.
5. *(Opsional)* **Google Gemini API Key** untuk mengaktifkan fitur *Viral Mode*.

---

## 5. Cara Menjalankan

### Langkah 1: Clone Repository
```bash
git clone https://github.com/Radja-Restu-A/youtube-clipper.git
cd youtube-clipper
```

---

### Langkah 2: Setup dan Menjalankan Backend

1. Masuk ke direktori backend:
   ```bash
   cd backend
   ```

2. Buat dan aktifkan virtual environment Python:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Pasang seluruh dependensi:
   ```bash
   pip install -r requirements.txt
   ```

4. *(Opsional)* Jika menggunakan GPU NVIDIA dengan CUDA 11.8, pastikan PyTorch CUDA terpasang dengan benar. Jalankan pengecekan:
   ```bash
   python check_cuda.py
   ```

5. Buat file `.env` di dalam folder `backend/` untuk mengaktifkan fitur Gemini AI:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

6. Jalankan server backend:
   ```bash
   python main.py
   ```
   *Backend akan berjalan di `http://localhost:8000` (dokumentasi Swagger API dapat diakses di `http://localhost:8000/docs`).*

---

### Langkah 3: Setup dan Menjalankan Frontend

Buka terminal baru, lalu:

1. Masuk ke direktori frontend:
   ```bash
   cd frontend
   ```

2. Pasang dependensi Node.js:
   ```bash
   npm install
   ```

3. Jalankan server pengembangan Vite:
   ```bash
   npm run dev
   ```
   *Frontend akan berjalan dan dapat diakses di `http://localhost:5173`.*

---

## 6. Struktur Direktori Proyek

```text
youtube-clipper/
├── backend/
│   ├── config.py                 # konfigurasi path, model, dan environment
│   ├── main.py                   # endpoint fastapi dan pipeline video
│   ├── check_cuda.py             # utilitas diagnostik status cuda/gpu
│   ├── requirements.txt          # daftar dependensi python
│   ├── models/                   # skema pydantic request/response
│   ├── repositories/             # state tracking dan history storage
│   ├── services/                 # layanan bisnis (whisper, gemini, audio, ffmpeg, dll.)
│   └── utils/                    # fungsi pembantu waktu dan file
├── frontend/
│   ├── package.json              # dependensi dan script frontend
│   ├── vite.config.js            # konfigurasi build vite
│   ├── tailwind.config.js        # konfigurasi tema tailwind css
│   └── src/
│       ├── app.jsx               # komponen root aplikasi
│       ├── components/           # komponen ui (input url, upload, preview, history)
│       ├── hooks/                # custom hook pemrosesan dan polling
│       └── services/             # client pemanggilan api backend
└── README.md
```

---

## 7. Catatan Penggunaan

- Jika `GEMINI_API_KEY` tidak diisi di file `.env`, aplikasi tetap dapat berjalan secara normal menggunakan **Audio Mode** dan **Context Mode**, namun fitur **Viral Mode** akan dinonaktifkan.
- Pastikan koneksi internet stabil saat memproses URL YouTube karena backend akan mengunduh video dan mengunduh model Whisper pada eksekusi pertama.
