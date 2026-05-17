Berikut perintah/prompt yang bisa langsung Anda berikan ke **AI Agent Codex** untuk memperbaiki repository Anda.

````markdown
# Tugas Codex: Audit dan Perbaikan MVP CullaGrace / Photo Filter

Anda bertindak sebagai **Senior Python Engineer**, **Software Architect**, dan **QA Engineer**.

Repository yang harus diperbaiki:

**https://github.com/jksn23/photo-filter.git**

Aplikasi ini adalah **CullaGrace - Church Photo Culling v1**, yaitu aplikasi lokal/offline berbasis **Streamlit + Python + OpenCV + ImageHash** untuk membantu tim multimedia gereja melakukan culling foto dokumentasi. Berdasarkan README, fitur inti aplikasi adalah membaca foto JPG/JPEG/PNG, melakukan **blur detection**, **exposure detection**, **duplicate detection**, **face detection**, memberi skor otomatis, menyalin foto ke folder **01_SELECTED**, **02_REVIEW**, **03_REJECTED**, serta membuat laporan CSV. README repository sudah menyebut fitur dan struktur output tersebut, jadi perbaikan harus mempertahankan arah produk ini. 

## 1. Tujuan Utama Perbaikan

Perbaiki repository agar aplikasi benar-benar bisa:

1. Di-install dengan `pip install -r requirements.txt`.
2. Dijalankan dengan `streamlit run app.py`.
3. Memproses folder berisi foto `.jpg`, `.jpeg`, dan `.png`.
4. Melakukan analisis:
   - **Blur detection** menggunakan variance of Laplacian.
   - **Exposure detection** berdasarkan brightness.
   - **Duplicate / similar photo detection** menggunakan perceptual hash.
   - **Face detection** menggunakan OpenCV Haar Cascade untuk versi 1.
5. Menghasilkan folder output:
   - **01_SELECTED**
   - **02_REVIEW**
   - **03_REJECTED**
   - **04_REPORT**
6. Membuat file laporan CSV berisi detail analisis setiap foto.
7. Tidak menghapus atau memindahkan file asli.
8. Lulus test dasar dengan `python -m unittest discover tests`.

## 2. Masalah yang Harus Dicek Terlebih Dahulu

Lakukan audit semua file `.py`, terutama:

- `app.py`
- semua file di folder `src/`
- semua file di folder `tests/`

Ada indikasi beberapa file Python mungkin tersimpan sebagai **satu baris panjang tanpa newline dan indentasi yang benar**. Jika benar, ini akan menyebabkan **SyntaxError**. Perbaiki semua file agar:

- Setiap import berada pada baris sendiri.
- Setiap class/function memiliki indentasi valid.
- Docstring terpisah dari import.
- File mengikuti standar Python yang rapi.
- Bisa dikompilasi dengan `python -m py_compile`.

Contoh format salah yang harus diperbaiki:

```python
"""Streamlit UI.""" from pathlib import Path import os import platform
````

Harus menjadi:

```python
"""Streamlit UI."""

from pathlib import Path
import os
import platform
```

## 3. Perbaiki `requirements.txt`

Pastikan `requirements.txt` berisi satu dependency per baris.

Gunakan minimal:

```txt
streamlit>=1.30
opencv-python>=4.8
Pillow>=10.0
imagehash>=4.3
numpy>=1.24
pandas>=2.0
```

Jangan tulis dependency dalam satu baris seperti:

```txt
streamlit opencv-python Pillow imagehash numpy pandas
```

## 4. Perbaiki README

Perbaiki instruksi aktivasi virtual environment Windows.

Ubah yang salah:

```bat
venv\S cripts\a ctivate
```

Menjadi:

```bat
venv\Scripts\activate
```

Pastikan README tetap menjelaskan:

* Cara install.
* Cara menjalankan aplikasi.
* Cara menggunakan aplikasi.
* Struktur output.
* Penjelasan threshold.
* Batasan versi 1.
* Cara menjalankan test.

## 5. Struktur Arsitektur yang Harus Dipertahankan

Pertahankan struktur modular berikut. Jika belum rapi, rapikan sesuai struktur ini:

```text
photo-filter/
  app.py
  requirements.txt
  README.md
  src/
    __init__.py
    image_loader.py
    blur_detector.py
    exposure_detector.py
    duplicate_detector.py
    face_detector.py
    scorer.py
    file_manager.py
    report_generator.py
    culling_pipeline.py
  tests/
    test_blur_detector.py
    test_exposure_detector.py
    test_duplicate_detector.py
    test_scorer.py
```

Jangan menaruh semua logic di `app.py`. `app.py` hanya bertanggung jawab untuk UI Streamlit dan memanggil pipeline.

## 6. Spesifikasi Modul

### 6.1 `image_loader.py`

Buat fungsi:

```python
def scan_images(input_dir: Path) -> list[Path]:
    ...
```

Ketentuan:

* Menerima folder input.
* Mengembalikan list file gambar dengan ekstensi `.jpg`, `.jpeg`, `.png`.
* Case-insensitive.
* Urutkan berdasarkan nama file agar hasil deterministik.
* Abaikan folder dan file non-gambar.
* Jika folder tidak ada, raise `FileNotFoundError`.

### 6.2 `blur_detector.py`

Buat fungsi:

```python
def calculate_blur_score(image_path: Path) -> float:
    ...
```

Dan:

```python
def is_blurry(blur_score: float, threshold: float = 100.0) -> bool:
    ...
```

Ketentuan:

* Gunakan OpenCV.
* Baca gambar.
* Convert ke grayscale.
* Hitung variance of Laplacian.
* Semakin kecil skor, semakin blur.
* Jika gambar tidak bisa dibaca, raise `ValueError`.

### 6.3 `exposure_detector.py`

Buat fungsi:

```python
def calculate_brightness(image_path: Path) -> float:
    ...
```

Dan:

```python
def classify_exposure(
    brightness: float,
    under_threshold: float = 50.0,
    over_threshold: float = 210.0
) -> str:
    ...
```

Return harus salah satu:

```text
UNDEREXPOSED
NORMAL
OVEREXPOSED
```

Ketentuan:

* Gunakan rata-rata brightness grayscale untuk versi 1.
* Jangan membuat model deep learning untuk exposure di versi ini.

### 6.4 `duplicate_detector.py`

Buat fungsi:

```python
def calculate_phash(image_path: Path) -> imagehash.ImageHash:
    ...
```

Dan fungsi grouping:

```python
def group_duplicates(
    image_paths: list[Path],
    hash_threshold: int = 8
) -> dict[str, list[Path]]:
    ...
```

Ketentuan:

* Gunakan `imagehash.phash`.
* Foto dianggap mirip jika jarak hash <= `hash_threshold`.
* Untuk versi 1, boleh menggunakan perbandingan sederhana O(n²), tetapi kode harus jelas dan aman.
* Return dictionary group id ke list foto.
* Foto yang tidak memiliki duplikat tetap boleh menjadi group tunggal.
* Jangan hapus file duplikat.

### 6.5 `face_detector.py`

Buat fungsi:

```python
def count_faces(image_path: Path) -> int:
    ...
```

Ketentuan:

* Gunakan OpenCV Haar Cascade.
* Gunakan `cv2.data.haarcascades`.
* Jika cascade tidak ditemukan, return 0 atau raise error yang jelas.
* Untuk versi 1, tidak perlu MediaPipe dulu.
* Jangan melakukan face recognition. Hanya deteksi jumlah wajah.

### 6.6 `scorer.py`

Buat dataclass:

```python
@dataclass
class PhotoAnalysis:
    path: Path
    filename: str
    blur_score: float
    is_blurry: bool
    brightness: float
    exposure_status: str
    face_count: int
    duplicate_group: str | None
    is_best_in_duplicate_group: bool
    final_score: int
    status: str
```

Buat fungsi:

```python
def calculate_score(
    is_blurry: bool,
    exposure_status: str,
    face_count: int,
    is_duplicate_non_best: bool,
    is_best_in_duplicate_group: bool
) -> int:
    ...
```

Aturan scoring:

```text
Base score: 100
Jika blur: -40
Jika UNDEREXPOSED atau OVEREXPOSED: -25
Jika face_count == 0: -10
Jika face_count > 0: +15
Jika duplicate non-best: -30
Jika best in duplicate group: +10
```

Buat fungsi:

```python
def classify_status(
    final_score: int,
    selected_min: int = 80,
    review_min: int = 50
) -> str:
    ...
```

Return harus salah satu:

```text
SELECTED
REVIEW
REJECTED
```

### 6.7 `file_manager.py`

Buat fungsi:

```python
def prepare_output_dirs(output_dir: Path) -> dict[str, Path]:
    ...
```

Harus membuat:

```text
01_SELECTED/
02_REVIEW/
03_REJECTED/
04_REPORT/
```

Buat fungsi:

```python
def copy_photo_to_status_folder(
    photo_path: Path,
    status: str,
    output_dirs: dict[str, Path]
) -> Path:
    ...
```

Ketentuan:

* File asli tidak boleh dihapus.
* File asli tidak boleh dipindahkan.
* Copy file ke folder sesuai status.
* Jika nama file bentrok, buat nama unik, misalnya `IMG_001_1.jpg`.

### 6.8 `report_generator.py`

Buat fungsi:

```python
def write_csv_report(
    analyses: list[PhotoAnalysis],
    report_dir: Path
) -> Path:
    ...
```

CSV wajib memiliki kolom:

```text
filename
path
blur_score
is_blurry
brightness
exposure_status
face_count
duplicate_group
is_best_in_duplicate_group
final_score
status
```

Buat juga fungsi summary opsional:

```python
def build_summary(analyses: list[PhotoAnalysis]) -> dict:
    ...
```

Summary minimal:

* total photos
* selected count
* review count
* rejected count
* blurry count
* underexposed count
* overexposed count
* duplicate groups count

### 6.9 `culling_pipeline.py`

Buat fungsi utama:

```python
def run_culling(
    input_dir: Path,
    output_dir: Path | None = None,
    blur_threshold: float = 100.0,
    under_threshold: float = 50.0,
    over_threshold: float = 210.0,
    duplicate_hash_threshold: int = 8,
    selected_min: int = 80,
    review_min: int = 50,
    progress_callback: callable | None = None
) -> tuple[list[PhotoAnalysis], Path, dict]:
    ...
```

Ketentuan:

* Jika `output_dir` kosong, buat default `<input_folder_name>_CULLED` di sebelah folder input.
* Jalankan semua analisis.
* Tentukan foto terbaik dalam duplicate group berdasarkan skor awal:

  * Prioritaskan tidak blur.
  * Prioritaskan exposure normal.
  * Prioritaskan blur score tertinggi.
  * Prioritaskan face_count lebih besar.
* Copy hasil ke folder status.
* Buat CSV report.
* Return:

  * list analysis
  * path report CSV
  * summary dict
* Tangani error per foto. Jika satu foto gagal diproses, jangan hentikan seluruh pipeline. Catat sebagai error di log/summary jika memungkinkan.

## 7. Spesifikasi UI Streamlit `app.py`

Buat UI dalam Bahasa Indonesia dengan struktur:

### Header

Tampilkan:

```text
CullaGrace
AI Photo Culling untuk Dokumentasi Gereja
```

Tambahkan deskripsi singkat:

```text
Aplikasi lokal untuk membantu menyortir foto dokumentasi gereja berdasarkan ketajaman, pencahayaan, kemiripan, dan jumlah wajah.
```

### Sidebar

Sidebar wajib berisi:

1. Input text untuk **Folder Foto Input**.
2. Input text untuk **Folder Output** opsional.
3. Slider/input number untuk:

   * **Blur Threshold**
   * **Underexposed Threshold**
   * **Overexposed Threshold**
   * **Duplicate Hash Threshold**
   * **Selected Score Minimum**
   * **Review Score Minimum**
4. Tombol utama:

   * **Mulai Culling**
5. Info singkat:

   * File asli tidak akan dihapus.
   * Aplikasi berjalan lokal/offline.

### Main Area

Sebelum proses:

* Tampilkan kartu/panel “Cara Kerja Singkat”.
* Jelaskan 4 analisis:

  * Blur
  * Exposure
  * Duplicate
  * Face Detection

Saat proses:

* Tampilkan progress bar.
* Tampilkan status teks: “Memproses foto X dari Y”.

Setelah proses:

Tampilkan metrics:

* Total Foto
* Selected
* Review
* Rejected
* Blur
* Exposure Bermasalah
* Duplicate Groups

Tampilkan:

* Path folder output.
* Path laporan CSV.
* Tabel dataframe hasil analisis.
* Tombol download CSV jika memungkinkan.

## 8. Testing

Buat atau perbaiki unit test minimal.

Test wajib:

### `test_blur_detector.py`

* `is_blurry(50, 100)` harus True.
* `is_blurry(150, 100)` harus False.

### `test_exposure_detector.py`

* brightness 30 -> UNDEREXPOSED.
* brightness 120 -> NORMAL.
* brightness 230 -> OVEREXPOSED.

### `test_scorer.py`

* score normal dengan face > 0 harus lebih tinggi dari score tanpa face.
* blur menurunkan score.
* `classify_status(90)` -> SELECTED.
* `classify_status(60)` -> REVIEW.
* `classify_status(30)` -> REJECTED.

### `test_duplicate_detector.py`

Jika sulit membuat test gambar, minimal test fungsi utilitas jika ada. Jangan buat test yang rapuh.

Pastikan semua test berjalan dengan:

```bash
python -m unittest discover tests
```

## 9. Quality Gate

Setelah perbaikan, jalankan perintah berikut dan pastikan berhasil:

```bash
python -m py_compile app.py
python -m py_compile src/*.py
python -m unittest discover tests
```

Jika shell tidak mendukung wildcard pada environment tertentu, jalankan kompilasi menggunakan script Python kecil atau `compileall`:

```bash
python -m compileall app.py src tests
```

Aplikasi juga harus bisa dijalankan dengan:

```bash
streamlit run app.py
```

## 10. Batasan yang Tidak Boleh Dilanggar

Jangan lakukan hal berikut:

1. Jangan membuat training model AI dari nol.
2. Jangan menambahkan upload otomatis ke Facebook.
3. Jangan menghapus file asli pengguna.
4. Jangan memindahkan file asli pengguna.
5. Jangan menambahkan dependency berat seperti PyTorch atau TensorFlow untuk versi 1.
6. Jangan mengubah aplikasi menjadi cloud app.
7. Jangan memerlukan GPU NVIDIA.
8. Jangan mengubah nama produk utama kecuali diperlukan. Gunakan **CullaGrace**.
9. Jangan membuat fitur editing foto otomatis untuk versi ini.
10. Jangan membuat face recognition atau identifikasi orang.

## 11. Ekspektasi Hasil Akhir

Setelah selesai, repository harus berada dalam kondisi:

* Struktur kode rapi dan modular.
* `requirements.txt` valid.
* README valid dan instruksi Windows benar.
* Aplikasi Streamlit bisa dijalankan.
* Pipeline culling berjalan end-to-end.
* Output folder dibuat otomatis.
* CSV report dibuat otomatis.
* Unit test dasar lulus.
* File asli pengguna aman.

## 12. Output dari Codex

Setelah melakukan perubahan, berikan ringkasan:

1. File apa saja yang diubah.
2. Bug apa saja yang diperbaiki.
3. Cara menjalankan aplikasi.
4. Cara menjalankan test.
5. Catatan batasan yang masih tersisa untuk versi berikutnya.

Mulai dengan audit repository, lalu lakukan perbaikan secara langsung.

```

Tambahan kecil: README repository Anda memang sudah menjelaskan fitur inti seperti **blur detection**, **exposure detection**, **duplicate detection**, **face detection**, output folder, dan laporan CSV, jadi prompt di atas sengaja menjaga agar Codex tidak mengubah arah produk dari MVP yang sudah benar. :contentReference[oaicite:0]{index=0}
::contentReference[oaicite:1]{index=1}
```
