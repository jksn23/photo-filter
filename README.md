# CullaGrace - Church Photo Culling v2

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
- Workflow review final V2: user memberi keputusan Posts, Save, Delete, atau Undecided setelah melihat rekomendasi AI.

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

## CullaGrace V2 Review Workflow

CullaGrace V2 memisahkan rekomendasi AI dari keputusan final manusia.

AI recommendation buckets:

- `Selected`: AI menilai foto paling layak dipakai.
- `Review`: AI meminta foto dicek manual.
- `Rejected`: AI menilai foto kurang layak, tetapi tetap bisa direview.

Final human decisions:

- `Posts`: foto final untuk dipakai atau diposting.
- `Save`: foto disimpan sebagai arsip atau cadangan.
- `Delete`: kandidat untuk dihapus setelah dicek manual.
- `Undecided`: belum ada keputusan final.

Workflow:

1. Jalankan culling seperti biasa.
2. Buka tab **Final Review**.
3. Review foto dari bucket Selected, Review, Rejected, atau All Photos.
4. Lihat score, alasan keputusan AI, dan foto lain dalam cluster yang sama.
5. Beri keputusan final: Posts, Save, Delete, atau Undecided.
6. Klik **Export Final** untuk membuat folder keputusan final.

Keamanan:

- Keputusan `Delete` tidak menghapus file asli.
- CullaGrace tidak memindahkan atau menghapus source photo secara permanen.
- Keputusan final disimpan sebagai metadata di `reports/final_decisions.json`.
- Folder final hanya dibuat ketika user menekan **Export Final**.
- Export final menyalin file ke folder final dan menangani nama file duplikat dengan suffix.

Output final V2:

```text
<OUTPUT_FOLDER>/
  02_FINAL_DECISION/
    Posts/
    Save/
    Delete/
  reports/
    final_decisions.json
    final_decision_report.csv
    final_decision_audit.json
```

Foto `Undecided` tidak diekspor ke folder final secara default, tetapi tetap muncul di report final.

## Batasan Versi 2

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
