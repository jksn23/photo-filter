# CullaGrace - Church Photo Culling v1

CullaGrace adalah aplikasi Streamlit lokal untuk membantu tim multimedia gereja melakukan culling foto dokumentasi secara lebih cepat. Aplikasi menganalisis ketajaman, pencahayaan, kemiripan foto, dan jumlah wajah, lalu menyalin hasil ke folder Selected, Review, dan Rejected.

Aplikasi berjalan lokal/offline. File asli tidak dihapus dan tidak dipindahkan.

## Fitur Utama

- Membaca foto `.jpg`, `.jpeg`, dan `.png`.
- Blur detection dengan variance of Laplacian.
- Exposure detection berdasarkan brightness rata-rata.
- Duplicate detection dengan perceptual hash.
- Face detection offline menggunakan OpenCV Haar Cascade.
- Human-aware blur detection berbasis heuristik OpenCV untuk menilai ketajaman area subjek manusia.
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
4. Atur mode culling dan opsi proses sesuai kebutuhan.
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

## Scoring dan Keputusan

CullaGrace memakai scoring ternormalisasi 0.0 sampai 1.0 di engine inti. UI dan CSV dapat menampilkan `final_score` sebagai persentase agar lebih mudah dibaca.

Sub-score utama:

- `technical.sharpness`
- `technical.exposure`
- `technical.contrast`
- `technical.global_blur_penalty`
- `face.face_score`
- `body.subject_score`
- `body.body_blur_penalty`
- `final_score`

Alur keputusan:

1. Menganalisis setiap gambar.
2. Mengelompokkan gambar yang mirip dengan perceptual hash.
3. Meranking foto di dalam setiap cluster.
4. Memilih foto terbaik per cluster.
5. Mengirim kandidat dekat ke Review sesuai mode.
6. Menolak duplicate yang kualitasnya jelas lebih rendah.

Mode culling:

- `conservative`: lebih banyak kandidat dekat dipertahankan untuk Review.
- `balanced`: mode default, menjaga satu pemenang dan kandidat yang skornya sangat dekat.
- `aggressive`: lebih ketat terhadap duplicate alternatif.

Body blur detection bersifat heuristik. Engine memperkirakan ketajaman area subject/body memakai person-region detector opsional bila tersedia; jika tidak tersedia, CullaGrace fallback ke analisis region subjek tengah. Person detection opsional, tidak wajib terpasang, dan fallback heuristic tetap berjalan offline.

## Batasan Versi 1

- Belum melakukan editing foto otomatis.
- Belum melakukan upload otomatis ke media sosial.
- Belum melakukan training AI khusus.
- Belum mendukung penuh file RAW seperti `.cr2`, `.nef`, `.arw`, atau `.dng`.
- Deteksi wajah memakai OpenCV Haar Cascade, sehingga hasil tetap perlu dicek manual.
- Deteksi area tubuh masih heuristik, bukan model AI khusus, sehingga hasil tetap perlu divalidasi pada foto ramai atau pencahayaan ekstrem.

## Menjalankan Test

```bash
python -m pytest -q
```

## Cache dan Audit

Aplikasi membuat cache lokal:

```text
.cullagrace-cache/
  thumbnails/
  analysis/
```

Cache dipakai ulang selama file foto belum berubah. Laporan JSON audit dibuat di `04_REPORT` bersama CSV agar alasan culling bisa diperiksa ulang.
