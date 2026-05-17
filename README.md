# CullaGrace - Church Photo Culling v1

CullaGrace adalah aplikasi Streamlit lokal untuk membantu tim multimedia gereja melakukan culling foto dokumentasi secara lebih cepat. Aplikasi menganalisis ketajaman, pencahayaan, kemiripan foto, dan jumlah wajah, lalu menyalin hasil ke folder Selected, Review, dan Rejected.

Aplikasi berjalan lokal/offline. File asli tidak dihapus dan tidak dipindahkan.

## Fitur Utama

- Membaca foto `.jpg`, `.jpeg`, dan `.png`.
- Blur detection dengan variance of Laplacian.
- Exposure detection berdasarkan brightness rata-rata.
- Duplicate detection dengan perceptual hash.
- Face detection offline menggunakan OpenCV Haar Cascade.
- Human-aware blur detection untuk menilai ketajaman subjek manusia pada foto mirip.
- Technical scoring ternormalisasi: sharpness, exposure, contrast, dan blur penalty.
- Similarity clustering dan best-photo picker dengan mode conservative, balanced, aggressive.
- Thumbnail dan analysis cache lokal di `.cullagrace-cache/`.
- Export audit JSON berisi summary, skor, dan alasan keputusan.
- Scoring otomatis untuk menentukan Selected, Review, atau Rejected.
- Menyalin file hasil ke folder output.
- Membuat laporan CSV untuk audit hasil.
- UI Bahasa Indonesia dengan panduan threshold.

## Instalasi

Windows:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Linux atau macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Cara Menggunakan

1. Jalankan aplikasi dengan `streamlit run app.py`.
2. Masukkan path folder foto pada sidebar.
3. Jika perlu, isi folder output. Jika dikosongkan, aplikasi membuat folder `<nama_folder>_CULLED` di dalam folder input.
4. Atur threshold sesuai kebutuhan.
5. Klik **Mulai Culling**.
6. Setelah selesai, buka folder output dan review folder Selected serta Review.

## Struktur Output

Secara default, aplikasi membuat struktur berikut:

```text
<NAMA_FOLDER_INPUT>/
  <NAMA_FOLDER_INPUT>_CULLED/
    01_SELECTED/
    02_REVIEW/
    03_REJECTED/
    04_REPORT/
      culling_report_<timestamp>.csv
      culling_audit_<timestamp>.json
```

Jika file tidak bisa dibaca atau gagal disalin, statusnya dicatat sebagai `ERROR` di laporan.

## Penjelasan Threshold

- **Blur Threshold**: nilai lebih tinggi berarti penilaian ketajaman lebih ketat. Default 100.
- **Underexposed Threshold**: brightness di bawah nilai ini dianggap terlalu gelap. Default 50.
- **Overexposed Threshold**: brightness di atas nilai ini dianggap terlalu terang. Default 210.
- **Duplicate Hash Threshold**: nilai lebih kecil berarti pencocokan duplikat lebih ketat. Default 8.
- **Human-Aware Blur Detection**: memakai YOLO nano jika tersedia untuk mendeteksi tubuh manusia, lalu menilai blur lokal pada subjek.
- **Mode Culling**: `conservative` menyimpan kandidat dekat, `balanced` adalah default, `aggressive` memilih satu pemenang per grup mirip.
- **Selected Score Minimum**: skor minimum agar foto masuk Selected. Default 80.
- **Review Score Minimum**: skor minimum agar foto masuk Review. Default 50.

## Aturan Scoring

Skor dasar adalah 100.

- Blur: -40
- Underexposed atau overexposed: -25
- Tidak ada wajah: -10
- Ada wajah: +15
- Duplikat non-terbaik: -30
- Duplikat terbaik dalam grup: +10

Klasifikasi default:

- `SELECTED`: final score >= 80
- `REVIEW`: final score >= 50 dan < 80
- `REJECTED`: final score < 50

## Batasan Versi 1

- Belum melakukan editing foto otomatis.
- Belum melakukan upload otomatis ke media sosial.
- Belum melakukan training AI khusus.
- Belum mendukung penuh file RAW seperti `.cr2`, `.nef`, `.arw`, atau `.dng`.
- Deteksi wajah memakai OpenCV Haar Cascade, sehingga hasil tetap perlu dicek manual.
- Person detection memakai Ultralytics YOLO nano. Model pretrained dapat diunduh otomatis saat pertama kali digunakan jika belum tersedia di mesin lokal.

## Menjalankan Test

```bash
python -m unittest discover tests
```

## Cache dan Audit

Aplikasi membuat cache lokal:

```text
.cullagrace-cache/
  thumbnails/
  analysis/
```

Cache dipakai ulang selama file foto belum berubah. Laporan JSON audit dibuat di `04_REPORT` bersama CSV agar alasan culling bisa diperiksa ulang.
