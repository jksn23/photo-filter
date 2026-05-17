# Gemini.md

# Instruksi Sistem untuk Agen AI Pembuat Kode Otonom

## 1. Identitas Aplikasi

Bangun aplikasi desktop/lokal bernama **Church Photo Culling v1**.

Aplikasi ini adalah sistem **semi-otomatis untuk melakukan culling foto dokumentasi gereja**. Tujuan utama aplikasi adalah membantu pengguna yang bekerja sendiri sebagai tim multimedia gereja untuk menyaring ribuan foto kegiatan menjadi kumpulan foto yang lebih kecil dan layak direview/upload.

Aplikasi **bukan** sistem AI generatif dan **bukan** sistem editing foto otomatis. Fokus aplikasi versi 1 adalah melakukan analisis kualitas foto berdasarkan parameter sederhana namun berguna:

1. **Blur Detection**: mendeteksi foto blur/tidak tajam.
2. **Exposure Detection**: mendeteksi foto terlalu gelap atau terlalu terang.
3. **Duplicate / Similar Photo Detection**: mendeteksi foto yang mirip atau duplikat.
4. **Face Detection**: mendeteksi jumlah wajah dalam foto sebagai indikator foto dokumentasi yang relevan.
5. **Scoring System**: memberi skor akhir pada setiap foto.
6. **Folder Classification**: menyalin foto ke folder **SELECTED**, **REVIEW**, atau **REJECTED**.
7. **CSV Report**: menghasilkan laporan hasil analisis dalam format CSV.

Aplikasi harus berjalan **lokal/offline** di laptop pengguna dengan spesifikasi menengah, termasuk laptop dengan GPU integrated seperti **Intel Iris Xe Graphics**. Jangan membangun fitur yang bergantung pada GPU NVIDIA/CUDA. Jangan mengharuskan pengguna memiliki server, cloud, atau koneksi internet untuk menjalankan fitur utama.

---

# 2. Tujuan dan Fungsionalitas Utama

## 2.1 Tujuan Utama

Bangun aplikasi yang memungkinkan pengguna untuk:

- Memilih folder berisi foto hasil dokumentasi gereja.
- Menjalankan proses **culling otomatis** pada semua foto dalam folder tersebut.
- Mengurangi jumlah foto yang perlu direview secara manual.
- Mengidentifikasi foto yang **blur**, **terlalu gelap**, **terlalu terang**, **mirip/duplikat**, dan **mengandung wajah**.
- Mengelompokkan foto secara otomatis ke folder hasil.
- Melihat ringkasan hasil proses culling.
- Membuka laporan CSV untuk pengecekan lanjutan.

Aplikasi harus membantu pengguna mengubah workflow dari:

```text
Ribuan foto → sortir manual satu per satu → pilih foto final
```

menjadi:

```text
Ribuan foto → analisis otomatis → SELECTED / REVIEW / REJECTED → review cepat → upload
```

## 2.2 Fungsionalitas Utama

Aplikasi harus memiliki fitur utama berikut.

### 2.2.1 Pilih Folder Foto

Pengguna dapat memilih **folder input** yang berisi foto.

Aplikasi harus mendukung minimal format:

- **.jpg**
- **.jpeg**
- **.png**

Untuk versi 1, format RAW seperti **.cr2**, **.nef**, **.arw**, **.dng** tidak wajib didukung. Jika agen ingin mendukung RAW, implementasikan sebagai fitur opsional dan jangan mengorbankan stabilitas versi 1.

### 2.2.2 Analisis Blur

Aplikasi harus menghitung **blur score** menggunakan metode ringan berbasis OpenCV.

Gunakan metode yang direkomendasikan:

- Convert image ke grayscale.
- Hitung variance dari Laplacian.
- Nilai rendah berarti foto lebih blur.
- Nilai tinggi berarti foto lebih tajam.

Output minimal:

- **blur_score**: angka float/integer.
- **is_blur**: boolean.

Gunakan threshold default yang dapat dikonfigurasi:

```text
blur_threshold = 100
```

Jika `blur_score < blur_threshold`, foto dianggap **blur**.

### 2.2.3 Analisis Exposure

Aplikasi harus menghitung tingkat terang/gelap foto.

Gunakan pendekatan sederhana:

- Convert image ke grayscale atau gunakan channel luminance.
- Hitung nilai rata-rata brightness dari 0 sampai 255.

Output minimal:

- **brightness_score**: angka 0-255.
- **exposure_status**: salah satu dari:
  - **underexposed**
  - **normal**
  - **overexposed**

Gunakan threshold default:

```text
underexposed_threshold = 50
overexposed_threshold = 210
```

Jika `brightness_score < 50`, foto dianggap **terlalu gelap**.

Jika `brightness_score > 210`, foto dianggap **terlalu terang**.

Jika berada di antara kedua nilai tersebut, foto dianggap **normal**.

### 2.2.4 Deteksi Foto Mirip / Duplikat

Aplikasi harus mendeteksi foto yang mirip atau duplikat menggunakan metode ringan.

Gunakan metode yang direkomendasikan:

- **Perceptual Hashing** menggunakan library `imagehash`.
- Gunakan `phash` atau `average_hash`.
- Hitung jarak hash antar foto.
- Kelompokkan foto yang jarak hash-nya di bawah threshold tertentu.

Gunakan threshold default:

```text
duplicate_hash_threshold = 8
```

Output minimal:

- **duplicate_group_id**: string/null.
- **is_duplicate_candidate**: boolean.
- **best_in_duplicate_group**: boolean.

Aturan penting:

- Jika beberapa foto berada dalam satu grup duplikat, aplikasi tidak boleh langsung membuang semuanya.
- Aplikasi harus memilih **foto terbaik dalam grup** berdasarkan skor akhir tertinggi.
- Foto terbaik dalam grup tetap bisa masuk **SELECTED** atau **REVIEW**.
- Foto lainnya dalam grup diberi penalti skor dan biasanya masuk **REVIEW** atau **REJECTED**, tergantung skor akhir.

### 2.2.5 Deteksi Wajah

Aplikasi harus mendeteksi wajah manusia dalam foto.

Gunakan metode ringan dan offline. Pilihan implementasi yang disarankan:

1. **OpenCV Haar Cascade** untuk versi paling sederhana.
2. **MediaPipe Face Detection** jika ingin akurasi lebih baik, tetapi tetap ringan.

Untuk versi 1, prioritaskan kestabilan dan kemudahan instalasi. Jika MediaPipe bermasalah lintas platform, gunakan OpenCV Haar Cascade.

Output minimal:

- **face_count**: jumlah wajah yang terdeteksi.
- **has_face**: boolean.

Aturan scoring:

- Foto dengan wajah mendapat bonus skor.
- Foto tanpa wajah tidak otomatis ditolak, karena foto suasana, panggung, gedung, atau dekorasi gereja tetap bisa berguna.

### 2.2.6 Scoring System

Aplikasi harus menghitung **final_score** untuk setiap foto.

Gunakan sistem skor default berikut:

```text
base_score = 100

Jika blur: -40
Jika underexposed: -25
Jika overexposed: -25
Jika tidak ada wajah: -10
Jika ada 1 wajah atau lebih: +15
Jika foto adalah duplikat non-terbaik dalam grup: -30
Jika foto terbaik dalam grup duplikat: +10
```

Pastikan skor akhir tidak wajib dibatasi, tetapi disarankan tetap dapat dibaca dalam rentang kira-kira 0-130.

### 2.2.7 Klasifikasi Otomatis

Berdasarkan **final_score**, aplikasi harus mengelompokkan foto ke dalam status:

```text
SELECTED: final_score >= 80
REVIEW:   final_score >= 50 dan final_score < 80
REJECTED: final_score < 50
```

Aplikasi harus membuat folder output otomatis di dalam folder input atau lokasi output yang dipilih pengguna.

Struktur folder default:

```text
<NAMA_FOLDER_INPUT>_CULLED/
  01_SELECTED/
  02_REVIEW/
  03_REJECTED/
  04_REPORT/
```

Aplikasi harus **menyalin** file, bukan memindahkan file asli. Jangan pernah menghapus foto asli.

### 2.2.8 Laporan CSV

Aplikasi harus membuat laporan CSV di folder:

```text
04_REPORT/culling_report.csv
```

Kolom CSV wajib:

```text
filename
original_path
output_status
output_path
blur_score
is_blur
brightness_score
exposure_status
face_count
has_face
duplicate_group_id
is_duplicate_candidate
best_in_duplicate_group
final_score
notes
```

Kolom **notes** berisi ringkasan alasan klasifikasi, contoh:

```text
blur; underexposed; no_face
```

atau:

```text
sharp; normal_exposure; has_face; best_duplicate
```

### 2.2.9 Ringkasan Hasil

Setelah proses selesai, aplikasi harus menampilkan ringkasan:

- Total foto diproses.
- Jumlah foto **SELECTED**.
- Jumlah foto **REVIEW**.
- Jumlah foto **REJECTED**.
- Jumlah foto blur.
- Jumlah foto underexposed.
- Jumlah foto overexposed.
- Jumlah grup duplikat.
- Lokasi folder output.
- Lokasi laporan CSV.

---

# 3. Teknologi yang Harus Digunakan

## 3.1 Bahasa Pemrograman

Gunakan **Python 3.10+**.

## 3.2 Library Utama

Gunakan library berikut:

```text
opencv-python
Pillow
imagehash
numpy
pandas
streamlit
```

Opsional:

```text
mediapipe
```

Jika menggunakan MediaPipe, pastikan aplikasi tetap memiliki fallback ke OpenCV Haar Cascade jika MediaPipe gagal diinstal.

## 3.3 Jenis Aplikasi

Untuk versi 1, bangun aplikasi sebagai **web app lokal menggunakan Streamlit**.

Alasan:

- Cepat dibuat.
- Mudah dijalankan oleh pengguna non-programmer.
- Cocok untuk prototype.
- Tidak perlu frontend kompleks.
- Dapat berjalan lokal di browser.

Jalankan aplikasi dengan:

```bash
streamlit run app.py
```

## 3.4 Struktur Folder Proyek

Buat struktur proyek seperti ini:

```text
church-photo-culling/
  app.py
  requirements.txt
  README.md
  Gemini.md
  src/
    __init__.py
    config.py
    models.py
    image_loader.py
    blur_detector.py
    exposure_detector.py
    face_detector.py
    duplicate_detector.py
    scorer.py
    file_manager.py
    report_generator.py
    culling_pipeline.py
  tests/
    test_blur_detector.py
    test_exposure_detector.py
    test_scorer.py
```

Agen harus menjaga kode tetap modular. Jangan menaruh semua logic di `app.py`.

---

# 4. Struktur Navigasi Aplikasi

Aplikasi menggunakan layout Streamlit dengan **sidebar kiri** dan **area konten utama**.

## 4.1 Sidebar Kiri

Sidebar harus memiliki elemen berikut secara berurutan:

1. **Judul Aplikasi**
   - Tampilkan: **Church Photo Culling v1**

2. **Input Folder**
   - Field teks untuk memasukkan path folder foto.
   - Label: **Folder Foto Input**
   - Placeholder: `Contoh: D:\Dokumentasi Gereja\2026-05-17 Ibadah Minggu`

3. **Output Folder**
   - Field teks opsional untuk lokasi output.
   - Label: **Folder Output**
   - Jika kosong, aplikasi otomatis membuat folder `<input_folder>_CULLED`.

4. **Pengaturan Threshold**
   - Slider atau number input untuk:
     - **Blur Threshold** default 100.
     - **Underexposed Threshold** default 50.
     - **Overexposed Threshold** default 210.
     - **Duplicate Hash Threshold** default 8.

5. **Pengaturan Klasifikasi**
   - Number input untuk:
     - **Selected Score Minimum** default 80.
     - **Review Score Minimum** default 50.

6. **Opsi Proses**
   - Checkbox: **Salin file ke folder output** default aktif.
   - Checkbox: **Buat laporan CSV** default aktif.
   - Checkbox: **Gunakan deteksi wajah** default aktif.
   - Checkbox: **Gunakan deteksi duplikat** default aktif.

7. **Tombol Aksi**
   - Tombol utama: **Mulai Culling**.
   - Tombol sekunder: **Reset Pengaturan**.

## 4.2 Header Konten Utama

Di bagian atas konten utama, tampilkan:

```text
Church Photo Culling v1
Semi-automatic photo culling untuk dokumentasi gereja.
```

Tampilkan juga pesan singkat:

```text
Aplikasi ini tidak menghapus file asli. Semua hasil akan disalin ke folder output.
```

## 4.3 Tab Navigasi Utama

Gunakan tab Streamlit berikut:

1. **Dashboard**
2. **Culling Process**
3. **Results**
4. **Settings Guide**
5. **About**

---

# 5. Detail Komponen per Halaman

## 5.1 Halaman Dashboard

Halaman **Dashboard** adalah halaman pembuka yang menjelaskan fungsi aplikasi dan status input.

Komponen wajib:

### 5.1.1 Kartu Ringkasan Aplikasi

Tampilkan empat kartu informasi:

1. **Blur Detection**
   - Deskripsi: `Mendeteksi foto yang tidak tajam atau bergoyang.`

2. **Exposure Detection**
   - Deskripsi: `Mendeteksi foto terlalu gelap atau terlalu terang.`

3. **Duplicate Detection**
   - Deskripsi: `Mengelompokkan foto yang mirip dan memilih kandidat terbaik.`

4. **Face Detection**
   - Deskripsi: `Mendeteksi jumlah wajah sebagai indikator foto dokumentasi.`

### 5.1.2 Status Folder Input

Tampilkan status:

- Jika folder belum diisi: tampilkan warning **Folder input belum dipilih.**
- Jika folder tidak valid: tampilkan error **Folder input tidak ditemukan.**
- Jika folder valid: tampilkan success **Folder input valid.**

Jika folder valid, tampilkan:

- Jumlah file gambar yang ditemukan.
- Daftar ekstensi yang ditemukan.
- Estimasi bahwa proses akan berjalan lokal.

### 5.1.3 Panduan Singkat Workflow

Tampilkan workflow:

```text
1. Pilih folder foto
2. Atur threshold jika diperlukan
3. Klik Mulai Culling
4. Review folder SELECTED dan REVIEW
5. Upload foto pilihan ke media sosial
```

## 5.2 Halaman Culling Process

Halaman **Culling Process** menampilkan proses culling saat berjalan.

Komponen wajib:

### 5.2.1 Panel Konfirmasi Sebelum Proses

Sebelum proses dimulai, tampilkan ringkasan konfigurasi:

- Folder input.
- Folder output.
- Blur threshold.
- Exposure threshold.
- Duplicate threshold.
- Selected minimum score.
- Review minimum score.
- Jumlah foto yang akan diproses.

### 5.2.2 Progress Bar

Saat proses berjalan, tampilkan:

- **Progress bar**.
- Teks status file yang sedang diproses.
- Jumlah foto yang sudah diproses dari total foto.

Contoh:

```text
Memproses IMG_1023.jpg (125/2000)
```

### 5.2.3 Log Proses Ringkas

Tampilkan log ringkas maksimal 20 baris terakhir.

Contoh log:

```text
Loaded 2000 images
Analyzing blur and exposure...
Detecting faces...
Grouping duplicates...
Scoring images...
Copying files to output folders...
Generating report...
Done.
```

### 5.2.4 Error Handling

Jika ada file rusak atau tidak bisa dibaca:

- Jangan hentikan seluruh proses.
- Catat file tersebut dalam laporan dengan status **ERROR**.
- Tampilkan warning bahwa beberapa file gagal diproses.

## 5.3 Halaman Results

Halaman **Results** menampilkan hasil setelah proses selesai.

Komponen wajib:

### 5.3.1 Kartu Statistik Utama

Tampilkan kartu berikut:

1. **Total Processed**
2. **Selected**
3. **Review**
4. **Rejected**
5. **Blur Photos**
6. **Underexposed Photos**
7. **Overexposed Photos**
8. **Duplicate Groups**

### 5.3.2 Tabel Hasil

Tampilkan tabel hasil dari data CSV atau DataFrame internal.

Kolom yang ditampilkan di UI:

```text
filename
output_status
final_score
blur_score
brightness_score
exposure_status
face_count
duplicate_group_id
notes
```

Tabel harus bisa difilter minimal berdasarkan:

- **output_status**
- **exposure_status**
- **is_blur**
- **has_face**

Jika Streamlit mendukung, gunakan komponen filter sederhana seperti selectbox/multiselect.

### 5.3.3 Tombol Buka Lokasi Output

Tampilkan path folder output dalam bentuk teks.

Jika memungkinkan secara cross-platform, sediakan tombol:

- **Buka Folder Output**
- **Buka Laporan CSV**

Jika tombol buka folder tidak mudah dibuat secara aman, cukup tampilkan path yang bisa disalin pengguna.

### 5.3.4 Download Report

Sediakan tombol **Download CSV Report** menggunakan fitur download Streamlit.

## 5.4 Halaman Settings Guide

Halaman **Settings Guide** menjelaskan cara mengatur threshold.

Komponen wajib:

### 5.4.1 Panduan Blur Threshold

Tampilkan:

```text
Nilai blur threshold menentukan seberapa ketat aplikasi menilai ketajaman foto.
Nilai lebih tinggi = lebih ketat.
Nilai lebih rendah = lebih longgar.
Default: 100.
```

### 5.4.2 Panduan Exposure Threshold

Tampilkan:

```text
Underexposed threshold default 50.
Overexposed threshold default 210.
Foto dengan brightness di bawah 50 dianggap terlalu gelap.
Foto dengan brightness di atas 210 dianggap terlalu terang.
```

### 5.4.3 Panduan Duplicate Threshold

Tampilkan:

```text
Duplicate hash threshold menentukan seberapa mirip dua foto agar dianggap satu grup.
Nilai lebih kecil = lebih ketat.
Nilai lebih besar = lebih longgar.
Default: 8.
```

### 5.4.4 Panduan Score

Tampilkan:

```text
SELECTED berarti foto kemungkinan besar layak dipakai.
REVIEW berarti foto perlu dicek manual.
REJECTED berarti foto kemungkinan besar tidak layak.
```

Tambahkan catatan penting:

```text
Aplikasi ini membantu menyaring, bukan menggantikan keputusan akhir manusia.
```

## 5.5 Halaman About

Halaman **About** menjelaskan aplikasi secara ringkas.

Komponen wajib:

- Nama aplikasi: **Church Photo Culling v1**.
- Tujuan: membantu tim multimedia gereja melakukan culling foto lebih cepat.
- Mode kerja: lokal/offline.
- Pernyataan keamanan: aplikasi tidak menghapus file asli.
- Batasan versi 1:
  - Belum melakukan editing otomatis.
  - Belum melakukan upload otomatis ke Facebook.
  - Belum melakukan training AI khusus.
  - Belum mendukung penuh file RAW.

---

# 6. Detail Modul Backend

## 6.1 `config.py`

Berisi default configuration:

```python
DEFAULT_BLUR_THRESHOLD = 100
DEFAULT_UNDEREXPOSED_THRESHOLD = 50
DEFAULT_OVEREXPOSED_THRESHOLD = 210
DEFAULT_DUPLICATE_HASH_THRESHOLD = 8
DEFAULT_SELECTED_SCORE_MIN = 80
DEFAULT_REVIEW_SCORE_MIN = 50
SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
```

## 6.2 `models.py`

Buat dataclass untuk hasil analisis foto.

Minimal:

```python
@dataclass
class PhotoAnalysisResult:
    filename: str
    original_path: str
    output_status: str
    output_path: str | None
    blur_score: float | None
    is_blur: bool
    brightness_score: float | None
    exposure_status: str
    face_count: int
    has_face: bool
    duplicate_group_id: str | None
    is_duplicate_candidate: bool
    best_in_duplicate_group: bool
    final_score: float
    notes: str
    error: str | None = None
```

## 6.3 `image_loader.py`

Tanggung jawab:

- Mencari semua file gambar dalam folder input.
- Memvalidasi path.
- Membaca gambar dengan OpenCV/Pillow.
- Menangani file rusak.

Fungsi minimal:

```python
def list_image_files(input_folder: str) -> list[str]
def load_image(image_path: str):
```

## 6.4 `blur_detector.py`

Tanggung jawab:

- Menghitung blur score.
- Mengembalikan status blur.

Fungsi minimal:

```python
def calculate_blur_score(image) -> float
def is_blurry(blur_score: float, threshold: float) -> bool
```

## 6.5 `exposure_detector.py`

Tanggung jawab:

- Menghitung brightness.
- Mengklasifikasikan exposure.

Fungsi minimal:

```python
def calculate_brightness(image) -> float
def classify_exposure(brightness: float, under_threshold: float, over_threshold: float) -> str
```

## 6.6 `face_detector.py`

Tanggung jawab:

- Deteksi wajah.
- Mengembalikan jumlah wajah.

Fungsi minimal:

```python
def detect_faces(image) -> int
```

Implementasi awal boleh memakai OpenCV Haar Cascade.

Pastikan cascade file tersedia melalui OpenCV:

```python
cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
```

## 6.7 `duplicate_detector.py`

Tanggung jawab:

- Menghasilkan perceptual hash untuk setiap foto.
- Mengelompokkan foto mirip.
- Menentukan duplicate group id.

Fungsi minimal:

```python
def calculate_image_hash(image_path: str)
def group_duplicates(image_paths: list[str], threshold: int) -> dict[str, str | None]
```

Output ideal:

```python
{
  "path/to/IMG_001.jpg": "G001",
  "path/to/IMG_002.jpg": "G001",
  "path/to/IMG_003.jpg": None,
}
```

## 6.8 `scorer.py`

Tanggung jawab:

- Menghitung final score.
- Menentukan status SELECTED/REVIEW/REJECTED.
- Membuat notes.

Fungsi minimal:

```python
def calculate_score(
    is_blur: bool,
    exposure_status: str,
    face_count: int,
    is_duplicate_candidate: bool,
    best_in_duplicate_group: bool,
) -> float


def classify_status(final_score: float, selected_min: float, review_min: float) -> str
```

## 6.9 `file_manager.py`

Tanggung jawab:

- Membuat folder output.
- Menyalin file ke folder hasil.
- Tidak menghapus file asli.

Fungsi minimal:

```python
def create_output_folders(output_base: str) -> dict[str, str]
def copy_to_output(original_path: str, status: str, output_folders: dict[str, str]) -> str
```

Folder status:

```text
SELECTED → 01_SELECTED
REVIEW → 02_REVIEW
REJECTED → 03_REJECTED
ERROR → 04_REPORT/errors atau tidak disalin
```

## 6.10 `report_generator.py`

Tanggung jawab:

- Membuat DataFrame.
- Menulis CSV.
- Menghasilkan ringkasan statistik.

Fungsi minimal:

```python
def results_to_dataframe(results: list[PhotoAnalysisResult])
def save_csv_report(df, report_path: str) -> None
def generate_summary(df) -> dict
```

## 6.11 `culling_pipeline.py`

Tanggung jawab:

- Mengorkestrasi seluruh proses.
- Digunakan oleh Streamlit UI.
- Mendukung progress callback.

Fungsi minimal:

```python
def run_culling_pipeline(
    input_folder: str,
    output_folder: str | None,
    config: dict,
    progress_callback=None,
    log_callback=None,
) -> tuple[list[PhotoAnalysisResult], dict]
```

Urutan proses:

1. Validasi folder input.
2. List semua image files.
3. Buat folder output.
4. Jika duplicate detection aktif, hitung grup duplikat.
5. Untuk setiap foto:
   - Load image.
   - Hitung blur score.
   - Hitung brightness.
   - Deteksi wajah jika aktif.
   - Simpan hasil sementara.
6. Setelah semua foto dianalisis, tentukan foto terbaik di tiap grup duplikat.
7. Hitung final score.
8. Tentukan status output.
9. Salin file ke folder output jika opsi aktif.
10. Buat CSV report.
11. Return results dan summary.

---

# 7. Aturan UI/UX

## 7.1 Bahasa Antarmuka

Gunakan **Bahasa Indonesia** untuk seluruh UI.

Contoh label:

- **Mulai Culling**
- **Folder Foto Input**
- **Foto Terpilih**
- **Perlu Review**
- **Ditolak**
- **Laporan CSV**

Nama variabel dan kode boleh menggunakan Bahasa Inggris agar tetap profesional.

## 7.2 Prinsip UX

Aplikasi harus terasa aman untuk pengguna non-teknis.

Terapkan prinsip berikut:

- Selalu jelaskan bahwa aplikasi **tidak menghapus file asli**.
- Jangan gunakan istilah teknis tanpa penjelasan singkat.
- Tampilkan error dengan bahasa yang mudah dipahami.
- Jangan membuat pengguna harus mengedit file konfigurasi manual.
- Semua threshold penting harus bisa diatur dari UI.

## 7.3 Warna Status

Gunakan status visual:

- **SELECTED**: success/green style.
- **REVIEW**: warning/yellow style.
- **REJECTED**: error/red style.
- **ERROR**: error/red style.

Jika Streamlit default tidak memungkinkan kustomisasi warna detail, gunakan `st.success`, `st.warning`, dan `st.error`.

---

# 8. Aturan Penanganan Error

Aplikasi harus menangani error berikut:

## 8.1 Folder Input Tidak Ada

Jika folder input tidak valid:

```text
Folder input tidak ditemukan. Periksa kembali path folder foto Anda.
```

## 8.2 Tidak Ada Foto

Jika folder valid tetapi tidak berisi foto:

```text
Tidak ada file foto JPG, JPEG, atau PNG di folder ini.
```

## 8.3 File Tidak Bisa Dibaca

Jika ada foto rusak:

- Jangan hentikan proses.
- Tandai sebagai **ERROR** di laporan.
- Isi kolom `error`.

## 8.4 Gagal Menyalin File

Jika file gagal disalin:

- Catat error.
- Tampilkan warning.
- Lanjutkan proses file lain.

## 8.5 Library Opsional Tidak Tersedia

Jika MediaPipe tidak tersedia:

- Jangan crash.
- Gunakan OpenCV Haar Cascade.
- Tampilkan info kecil:

```text
MediaPipe tidak tersedia. Aplikasi menggunakan OpenCV Haar Cascade untuk deteksi wajah.
```

---

# 9. Aturan Performa

Aplikasi harus dirancang untuk memproses **1.000 sampai 3.000 foto JPG** pada laptop menengah.

## 9.1 Optimasi Wajib

- Jangan memuat semua gambar full-size ke memory secara bersamaan.
- Proses gambar satu per satu.
- Untuk hashing, gunakan Pillow dengan resize internal jika perlu.
- Untuk deteksi wajah, resize gambar ke ukuran lebih kecil sebelum deteksi agar lebih cepat.
- Gunakan progress callback agar UI tidak terlihat freeze.

## 9.2 Batasan

Jangan membangun training model AI dari nol.

Jangan mengharuskan GPU CUDA.

Jangan membuat fitur upload media sosial otomatis di versi 1.

Jangan membuat fitur edit foto otomatis di versi 1.

---

# 10. Aturan Keamanan File

Aturan ini wajib dipatuhi:

1. **Jangan pernah menghapus file asli.**
2. **Jangan pernah memindahkan file asli.**
3. Semua hasil harus berupa salinan.
4. Jika nama file bentrok di folder output, tambahkan suffix aman.

Contoh:

```text
IMG_001.jpg
IMG_001_1.jpg
IMG_001_2.jpg
```

5. Jangan overwrite laporan lama tanpa memberi nama unik atau melakukan overwrite yang jelas.

Untuk versi 1, boleh overwrite `culling_report.csv` di folder output yang sama, tetapi lebih baik membuat timestamp:

```text
culling_report_2026-05-17_153000.csv
```

---

# 11. README.md yang Harus Dibuat

Agen harus membuat `README.md` yang berisi:

1. Deskripsi aplikasi.
2. Fitur utama.
3. Cara instalasi.
4. Cara menjalankan.
5. Cara menggunakan.
6. Penjelasan output folder.
7. Penjelasan threshold.
8. Batasan versi 1.

Contoh perintah instalasi:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Untuk Linux/Mac:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

# 12. requirements.txt

Isi minimal:

```text
streamlit
opencv-python
Pillow
imagehash
numpy
pandas
```

Jika memakai MediaPipe, tambahkan:

```text
mediapipe
```

Namun pastikan aplikasi tetap berjalan jika MediaPipe tidak ada.

---

# 13. Acceptance Criteria

Aplikasi dianggap selesai jika memenuhi kriteria berikut:

## 13.1 Functional Criteria

- Pengguna dapat menjalankan aplikasi dengan `streamlit run app.py`.
- Pengguna dapat memasukkan path folder foto.
- Aplikasi dapat membaca file JPG/JPEG/PNG.
- Aplikasi dapat menghitung blur score.
- Aplikasi dapat menghitung brightness score.
- Aplikasi dapat mengklasifikasikan exposure.
- Aplikasi dapat mendeteksi wajah minimal menggunakan OpenCV Haar Cascade.
- Aplikasi dapat mendeteksi foto mirip menggunakan perceptual hash.
- Aplikasi dapat menghitung final score.
- Aplikasi dapat mengelompokkan foto ke **01_SELECTED**, **02_REVIEW**, dan **03_REJECTED**.
- Aplikasi dapat menghasilkan CSV report.
- Aplikasi menampilkan summary hasil.

## 13.2 Safety Criteria

- Aplikasi tidak menghapus foto asli.
- Aplikasi tidak memindahkan foto asli.
- Aplikasi tetap lanjut walau ada beberapa file rusak.
- Aplikasi menampilkan pesan error yang jelas.

## 13.3 UX Criteria

- UI menggunakan Bahasa Indonesia.
- Sidebar berisi semua pengaturan utama.
- Ada tab **Dashboard**, **Culling Process**, **Results**, **Settings Guide**, dan **About**.
- Ada progress indicator selama proses.
- Ada tabel hasil setelah proses selesai.

## 13.4 Code Quality Criteria

- Kode modular di folder `src/`.
- `app.py` hanya mengatur UI dan memanggil pipeline.
- Fungsi-fungsi utama memiliki docstring.
- Tidak ada hardcoded path pribadi pengguna.
- Tidak ada dependency cloud.

---

# 14. Prioritas Implementasi

Agen harus mengerjakan dengan urutan prioritas berikut:

## Prioritas 1 — Core Pipeline

Bangun dulu:

1. List image files.
2. Blur detection.
3. Exposure detection.
4. Face detection sederhana.
5. Scoring.
6. Copy output.
7. CSV report.

## Prioritas 2 — Duplicate Detection

Setelah core pipeline stabil, tambahkan:

1. Perceptual hash.
2. Duplicate grouping.
3. Best photo in duplicate group.
4. Duplicate penalty scoring.

## Prioritas 3 — Streamlit UI

Bangun UI lengkap:

1. Sidebar settings.
2. Dashboard.
3. Progress process.
4. Results table.
5. Download CSV.
6. Settings Guide.
7. About.

## Prioritas 4 — Testing dan Stabilitas

Tambahkan test sederhana untuk:

1. Exposure classification.
2. Blur threshold logic.
3. Scoring logic.

---

# 15. Instruksi Penting untuk Agen AI

Baca dan patuhi instruksi berikut secara ketat:

1. **Jangan membuat aplikasi terlalu kompleks.** Versi 1 harus sederhana, stabil, dan bisa dipakai.
2. **Jangan membuat sistem training AI.** Gunakan metode computer vision ringan.
3. **Jangan membutuhkan GPU NVIDIA.** Aplikasi harus berjalan di CPU/laptop biasa.
4. **Jangan menghapus file asli.** Ini aturan wajib.
5. **Jangan hanya membuat mockup UI.** Aplikasi harus benar-benar memproses foto.
6. **Jangan menaruh semua kode dalam satu file.** Gunakan struktur modular.
7. **Jangan mengabaikan laporan CSV.** CSV adalah output penting untuk audit hasil.
8. **Jangan menghentikan proses hanya karena satu file error.** Catat error dan lanjutkan.
9. **Gunakan Bahasa Indonesia untuk UI.** Pengguna utama adalah tim multimedia gereja Indonesia.
10. **Fokus pada manfaat praktis.** Tujuan akhir adalah memangkas waktu sortir foto sebelum upload media sosial.

---

# 16. Contoh Output yang Diharapkan

Setelah pengguna memilih folder:

```text
D:\Dokumentasi Gereja\2026-05-17 Ibadah Minggu
```

Aplikasi membuat:

```text
D:\Dokumentasi Gereja\2026-05-17 Ibadah Minggu_CULLED\
  01_SELECTED\
    IMG_0012.jpg
    IMG_0045.jpg
    IMG_0088.jpg
  02_REVIEW\
    IMG_0003.jpg
    IMG_0010.jpg
  03_REJECTED\
    IMG_0001.jpg
    IMG_0002.jpg
  04_REPORT\
    culling_report_2026-05-17_153000.csv
```

Ringkasan UI:

```text
Total foto diproses: 2000
Selected: 340
Review: 520
Rejected: 1140
Blur: 410
Underexposed: 220
Overexposed: 75
Duplicate Groups: 300
```

---

# 17. Definisi Selesai

Proyek versi 1 selesai ketika pengguna dapat menjalankan aplikasi secara lokal, memilih folder foto kegiatan gereja, menekan tombol **Mulai Culling**, lalu mendapatkan folder hasil **SELECTED**, **REVIEW**, **REJECTED**, dan laporan **CSV** tanpa kehilangan file asli.

Aplikasi harus menjadi alat bantu praktis untuk mempercepat kerja tim multimedia gereja, bukan eksperimen AI yang terlalu kompleks.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
