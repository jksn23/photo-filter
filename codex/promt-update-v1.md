Berikut prompt yang bisa Anda berikan ke AI Agent Codex:

````markdown
# Prompt AI Agent Codex — Perbaikan Full-Resolution Review Viewer CullaGrace

Anda bekerja pada repository CullaGrace:

https://github.com/jksn23/photo-filter

Saya ingin Anda membaca dan memahami struktur aplikasi terbaru terlebih dahulu, khususnya bagian Streamlit UI di `app.py`, modul review V2 di `src/core/review`, dan alur Final Review Workflow. Saat ini aplikasi sudah memiliki bucket review seperti `Selected`, `Review`, dan `Rejected`, serta final decision seperti `Post`, `Save`, `Delete`, dan `Undecided`. Namun ada masalah penting: tampilan review foto di Streamlit masih terasa blur/tidak cukup tajam untuk menilai kualitas foto secara serius, karena gambar di UI kemungkinan ditampilkan sebagai thumbnail atau di-resize oleh layout browser.

Tugas Anda adalah memperbaiki Streamlit review viewer agar lebih layak untuk inspeksi foto, tanpa mengubah engine culling utama.

## Tujuan utama

Perbaiki Final Review UI agar:

1. Grid/bucket view tetap memakai thumbnail agar ringan.
2. Detail view wajib memakai original image, bukan thumbnail.
3. Tambahkan tombol `Open Original File`.
4. Tambahkan tombol `Open Original Folder`.
5. Tambahkan zoom/crop inspection.
6. Tambahkan compare cluster side-by-side.
7. Tampilkan resolusi asli foto.
8. Tampilkan label yang jelas apakah user sedang melihat `Thumbnail Preview` atau `Original Image`.
9. Jangan mengklaim “full resolution” jika gambar masih hanya ditampilkan resize oleh browser.
10. Pastikan engine tetap menganalisis file original, bukan thumbnail.

---

## Prinsip penting

Pisahkan fungsi gambar menjadi tiga level:

```text
Grid View       → pakai thumbnail
Detail View     → pakai original image
Inspection View → pakai crop dari original image
````

Jangan memakai thumbnail untuk detail review dan inspeksi ketajaman.

---

## Task 1 — Audit image path usage

Periksa semua fungsi di `app.py` yang menampilkan image, terutama fungsi seperti:

```python
_review_image_path(...)
render_review_bucket(...)
render_review_detail(...)
render_cluster_comparison(...)
```

Pastikan:

```text
Bucket/grid card memakai thumbnail jika tersedia.
Detail view memakai original_path.
Cluster comparison default boleh thumbnail, tetapi harus punya opsi original/crop comparison.
```

Jika ada fungsi helper seperti `_review_image_path(item, prefer_thumbnail=True)`, pastikan perilakunya jelas:

```python
prefer_thumbnail=True  -> thumbnail path untuk grid
prefer_thumbnail=False -> original path untuk detail
```

Tambahkan helper baru jika perlu:

```python
get_review_thumbnail_path(item)
get_review_original_path(item)
get_image_resolution(path)
```

---

## Task 2 — Tampilkan informasi resolusi asli

Di detail view, tampilkan informasi:

```text
Original Resolution: 6000 x 4000
Displayed Mode: Original Image
Source Path: /path/to/file.jpg
```

Gunakan PIL:

```python
from PIL import Image

with Image.open(path) as img:
    width, height = img.size
```

Pastikan tidak crash jika file tidak ditemukan atau format tidak valid.

---

## Task 3 — Tambahkan label mode tampilan

Pada setiap image yang ditampilkan, tampilkan badge/label:

Untuk grid:

```text
Viewing: Thumbnail Preview
```

Untuk detail:

```text
Viewing: Original Image
```

Untuk crop inspection:

```text
Viewing: 100% Crop from Original
```

Tujuannya agar user tahu apakah gambar yang dilihat adalah thumbnail, original, atau crop dari original.

---

## Task 4 — Tambahkan tombol Open Original File dan Open Original Folder

Di detail view, tambahkan tombol:

```text
Open Original File
Open Original Folder
```

Jika aplikasi berjalan di local desktop, gunakan helper aman dengan `subprocess` atau `os.startfile` sesuai OS.

Implementasikan fungsi cross-platform:

```python
def open_local_file(path: Path) -> bool:
    ...

def open_local_folder(path: Path) -> bool:
    ...
```

Behavior:

* Windows: gunakan `os.startfile`
* macOS: gunakan `open`
* Linux: gunakan `xdg-open`
* Jika gagal, tampilkan error yang jelas di Streamlit.
* Jangan crash jika path tidak ditemukan.

Jika membuka file langsung tidak memungkinkan di environment tertentu, tampilkan path asli agar user bisa membukanya manual.

---

## Task 5 — Tambahkan zoom/crop inspection

Karena Streamlit tidak ideal untuk true 100% zoom/pan, buat fitur inspeksi berbasis crop dari original image.

Di detail view, tambahkan section:

```text
Sharpness Inspection
```

Mode inspection:

```text
Fit View
Center Crop 100%
Face/Upper Body Crop
Body/Subject Crop
Custom Crop
```

Minimal implementasi wajib:

### A. Fit View

Tampilkan original image dengan ukuran menyesuaikan container.

Label:

```text
Viewing: Original Image - Fit View
```

### B. Center Crop 100%

Ambil crop dari tengah original image tanpa resize berlebihan.

Control:

```text
Crop Size: 512 / 768 / 1024 px
```

Tampilkan crop tersebut dengan caption:

```text
Viewing: 100% Center Crop from Original
```

### C. Body/Subject Crop

Ambil crop area tengah vertikal yang mewakili tubuh/subjek.

Contoh crop:

```text
x: 20% - 80% width
y: 20% - 90% height
```

Tampilkan sebagai:

```text
Viewing: Body/Subject Crop from Original
```

### D. Custom Crop sederhana

Tambahkan slider:

```text
Crop center X %
Crop center Y %
Crop size
```

Lalu tampilkan crop berdasarkan koordinat tersebut.

Pastikan crop:

* tidak keluar batas gambar,
* memakai original image,
* aman untuk gambar portrait/landscape,
* tidak crash pada gambar kecil.

Buat helper:

```python
def crop_original_image(
    image_path: Path,
    center_x_ratio: float = 0.5,
    center_y_ratio: float = 0.5,
    crop_size: int = 768,
) -> Image.Image:
    ...
```

---

## Task 6 — Compare cluster side-by-side

Di detail view, bagian `Similar Photos in This Cluster` harus ditingkatkan.

Tambahkan mode comparison:

```text
Comparison Mode:
- Thumbnail
- Original Fit
- Center Crop 100%
- Body Crop
```

Untuk setiap foto dalam cluster, tampilkan side-by-side:

```text
Filename
AI Status
Final Decision
Final Score
Body Blur Penalty
Face Score
Image Preview/Crop
```

Jika mode `Center Crop 100%` atau `Body Crop`, gunakan crop dari original image, bukan thumbnail.

Tujuan fitur ini:

User bisa membandingkan foto mirip dan melihat mana yang benar-benar tajam, bukan hanya melihat preview kecil.

---

## Task 7 — Jangan mengubah engine culling

Jangan refactor besar engine culling.

Perubahan utama harus berada di:

```text
app.py
src/ui/review_components.py  jika ada / jika perlu dibuat
src/ui/image_viewer.py       jika perlu dibuat
```

Boleh membuat modul baru:

```text
src/ui/image_viewer.py
```

Isi helper:

```python
get_image_resolution
open_local_file
open_local_folder
crop_original_image
get_display_path
```

Jika membuat modul baru, update import di `app.py`.

---

## Task 8 — Tambahkan safety fallback

Jika original file tidak ditemukan:

* tampilkan warning,
* fallback ke thumbnail jika tersedia,
* label harus jelas:

```text
Original file not found. Showing thumbnail fallback.
```

Jika thumbnail tidak ada:

```text
Image preview unavailable.
```

Jangan crash.

---

## Task 9 — Update README

Tambahkan bagian dokumentasi:

```markdown
## Full-Resolution Review Viewer

CullaGrace uses thumbnails for fast grid browsing, but the detail review page loads the original image for inspection. The app also provides crop-based inspection modes such as center crop and body crop to help verify blur/sharpness decisions.

Notes:
- Grid view uses thumbnails.
- Detail view uses original images.
- Crop inspection is generated from original images.
- Streamlit may still resize images visually in the browser, so crop inspection is recommended for checking sharpness.
```

Jelaskan juga:

```text
Open Original File
Open Original Folder
```

---

## Task 10 — Testing

Tambahkan test jika memungkinkan:

```text
tests/test_image_viewer_helpers.py
```

Test minimal:

1. `get_image_resolution` mengembalikan width/height yang benar.
2. `crop_original_image` menghasilkan ukuran crop yang benar.
3. Crop tidak keluar batas gambar.
4. Missing file ditangani dengan aman.
5. Thumbnail/original path selection benar.

Jalankan:

```bash
python -m compileall src
python -m pytest -q
```

Pastikan semua test pass.

---

## Acceptance Criteria

Implementasi dianggap selesai jika:

1. Bucket/grid view tetap ringan dan memakai thumbnail.
2. Detail view memakai original image.
3. UI menampilkan resolusi asli foto.
4. UI menampilkan label `Thumbnail Preview`, `Original Image`, atau `100% Crop from Original`.
5. Ada tombol `Open Original File`.
6. Ada tombol `Open Original Folder`.
7. Ada crop inspection dari original image.
8. Ada center crop inspection.
9. Ada body/subject crop inspection.
10. Ada custom crop sederhana dengan slider.
11. Cluster comparison bisa side-by-side memakai thumbnail/original/crop.
12. Missing original file tidak membuat app crash.
13. README menjelaskan behavior viewer.
14. `python -m compileall src` pass.
15. `python -m pytest -q` pass.

---

## Output akhir dari Codex

Setelah selesai, berikan ringkasan:

1. File yang dibuat.
2. File yang dimodifikasi.
3. Bagian UI yang diperbaiki.
4. Cara kerja detail original image viewer.
5. Cara kerja crop inspection.
6. Cara kerja cluster comparison.
7. Hasil test.
8. Limitasi yang masih ada.

```

Inti prompt ini: **jangan mengganti engine dulu**, cukup perbaiki viewer agar review foto di Streamlit lebih layak untuk menilai ketajaman.
```
