Berikut prompt yang bisa langsung Anda berikan ke **Codex / AI Agent**.

````markdown
# Tugas Codex: Tambahkan Human-Aware Blur Detection dan Best Duplicate Selection pada CullaGrace

Anda bertindak sebagai **Computer Vision Engineer**, **Senior Python Engineer**, dan **QA Engineer**.

Repository:

**https://github.com/jksn23/photo-filter.git**

Aplikasi ini adalah **CullaGrace**, aplikasi lokal/offline berbasis **Streamlit + Python + OpenCV + ImageHash** untuk melakukan photo culling dokumentasi gereja.

Masalah yang ingin diperbaiki:

Saat ada **dua foto yang mirip**, sistem kadang memilih foto yang memiliki **blur lokal pada tubuh manusia**, misalnya tangan bergerak/goyang, karena blur global masih dianggap cukup tajam. Padahal jika ada foto lain yang mirip dan lebih bersih, sistem harus memilih foto yang **subjek manusianya lebih tajam dan bebas motion blur**.

Tujuan perubahan ini adalah menambahkan fitur:

**Human-Aware Blur Detection**  
**Person Body Blur Scoring**  
**Localized Person Blur Detection**  
**Best Duplicate Selection berdasarkan kualitas subjek manusia**

Gunakan pendekatan ringan. Jangan training model dari nol.

---

## 1. Prinsip Utama

Sistem tidak boleh hanya menilai:

**global_blur_score**

Sistem harus menilai juga:

- **person_count**
- **main_person_box**
- **main_person_blur_score**
- **avg_person_blur_score**
- **min_person_blur_score**
- **localized_person_blur**
- **human_quality_score**
- **duplicate_quality_rank**
- **is_best_duplicate**

Jika ada beberapa foto mirip dalam satu duplicate group, sistem harus memilih foto terbaik berdasarkan kualitas manusia, bukan hanya skor global.

---

## 2. Dependency Baru

Tambahkan dependency berikut ke `requirements.txt`:

```txt
ultralytics>=8.0
````

Tetap pertahankan dependency lama:

```txt
streamlit>=1.30
opencv-python>=4.8
Pillow>=10.0
imagehash>=4.3
numpy>=1.24
pandas>=2.0
```

Gunakan **YOLO nano pretrained model** untuk deteksi manusia. Ultralytics YOLO mendukung object detection dengan output bounding box, class label, dan confidence score, serta dapat digunakan dari Python untuk prediction/inference. Gunakan model ringan seperti **yolov8n.pt** atau fallback ke model nano terbaru yang tersedia. Jangan training model baru. ([Ultralytics Docs][1])

---

## 3. Tambahkan Modul Baru `src/person_detector.py`

Buat file:

```text
src/person_detector.py
```

Isi fungsi berikut:

```python
from pathlib import Path
from typing import List, Tuple, Optional

PersonBox = tuple[int, int, int, int]  # x, y, w, h


def detect_person_boxes(
    image_path: Path,
    confidence_threshold: float = 0.35,
    model_name: str = "yolov8n.pt"
) -> list[PersonBox]:
    ...
```

Ketentuan:

1. Gunakan **Ultralytics YOLO** pretrained detection model.
2. Deteksi hanya class **person**.
3. Return list bounding box format `(x, y, w, h)`.
4. Filter box dengan confidence di bawah threshold.
5. Jika model gagal load, return list kosong dan jangan crash seluruh pipeline.
6. Jangan melakukan face recognition.
7. Jangan melakukan identifikasi orang.
8. Cache model agar tidak di-load ulang untuk setiap gambar.

Tambahkan helper:

```python
def select_main_person_box(
    boxes: list[PersonBox],
    image_width: int,
    image_height: int
) -> PersonBox | None:
    ...
```

Aturan memilih main person:

* Utamakan box dengan area terbesar.
* Tambahkan bobot jika box dekat tengah gambar.
* Return `None` jika tidak ada person box.

Contoh scoring:

```python
area_score = box_area / image_area
center_score = 1.0 - normalized_distance_to_center
main_score = area_score * 0.75 + center_score * 0.25
```

---

## 4. Tambahkan Person Blur Analysis

Tambahkan file baru:

```text
src/person_blur_analyzer.py
```

Buat fungsi:

```python
from pathlib import Path
from typing import List, Tuple
import numpy as np

PersonBox = tuple[int, int, int, int]


def calculate_blur_for_box(
    image: np.ndarray,
    box: PersonBox
) -> float:
    ...
```

Ketentuan:

* Crop area box dari image.
* Convert ke grayscale.
* Hitung **variance of Laplacian**.
* Return skor blur.
* Jika crop invalid, return `0.0`.

Buat fungsi:

```python
def calculate_person_blur_scores(
    image_path: Path,
    person_boxes: list[PersonBox]
) -> dict:
    ...
```

Return dict minimal:

```python
{
    "person_count": int,
    "main_person_blur_score": float | None,
    "avg_person_blur_score": float | None,
    "min_person_blur_score": float | None,
}
```

Ketentuan:

* Gunakan main person box dari `select_main_person_box`.
* Hitung blur semua person box.
* `main_person_blur_score` = skor blur pada main person.
* `avg_person_blur_score` = rata-rata semua person blur score.
* `min_person_blur_score` = skor paling rendah.

---

## 5. Tambahkan Localized Person Blur Detection

Masih di `src/person_blur_analyzer.py`, buat fungsi:

```python
def detect_localized_person_blur(
    image: np.ndarray,
    main_person_box: PersonBox,
    grid_rows: int = 3,
    grid_cols: int = 3,
    patch_blur_threshold: float = 75.0,
    min_blurry_patch_ratio: float = 0.25
) -> bool:
    ...
```

Logika:

1. Crop area main person.
2. Bagi crop menjadi grid **3x3**.
3. Hitung blur score setiap patch.
4. Hitung jumlah patch dengan blur score < `patch_blur_threshold`.
5. Jika rasio patch blur >= `min_blurry_patch_ratio`, return `True`.

Tujuan:

Mendeteksi blur lokal seperti **tangan bergerak/goyang** pada tubuh manusia, walaupun global blur score masih tinggi.

---

## 6. Tambahkan Human Quality Score

Di `src/scorer.py`, tambahkan fungsi:

```python
def calculate_human_quality_score(
    face_count: int,
    global_blur_score: float,
    main_person_blur_score: float | None,
    avg_person_blur_score: float | None,
    localized_person_blur: bool,
    exposure_status: str
) -> int:
    ...
```

Aturan scoring:

```text
Base: 100

Face:
- face_count > 0: +20
- face_count == 0: -15

Global blur:
- global_blur_score >= 180: +10
- 100 <= global_blur_score < 180: 0
- 50 <= global_blur_score < 100: -25
- global_blur_score < 50: -60

Main person blur:
- main_person_blur_score is None: -10
- main_person_blur_score >= 150: +25
- 100 <= main_person_blur_score < 150: +10
- 60 <= main_person_blur_score < 100: -25
- main_person_blur_score < 60: -50

Average person blur:
- avg_person_blur_score is None: 0
- avg_person_blur_score >= 130: +10
- 80 <= avg_person_blur_score < 130: 0
- avg_person_blur_score < 80: -20

Localized person blur:
- True: -35
- False: 0

Exposure:
- NORMAL: 0
- UNDEREXPOSED: -15
- OVEREXPOSED: -15
```

Clamp hasil akhir ke rentang:

```text
0 sampai 150
```

---

## 7. Perbarui `PhotoAnalysis` Dataclass

Di `src/scorer.py`, tambahkan field berikut ke `PhotoAnalysis`:

```python
person_count: int
main_person_blur_score: float | None
avg_person_blur_score: float | None
min_person_blur_score: float | None
localized_person_blur: bool
human_quality_score: int
duplicate_quality_rank: int | None
is_best_duplicate: bool
```

Pastikan seluruh pipeline, CSV, UI, dan test menyesuaikan perubahan dataclass.

---

## 8. Perbaiki Duplicate Best Selection

Di `src/culling_pipeline.py`, ubah logika pemilihan foto terbaik dalam duplicate group.

Saat ada group berisi lebih dari satu foto, jangan pilih best hanya berdasarkan:

* global blur
* face count
* exposure

Gunakan prioritas baru:

```text
1. human_quality_score tertinggi
2. localized_person_blur == False
3. main_person_blur_score tertinggi
4. face_count tertinggi
5. global_blur_score tertinggi
6. exposure_status == NORMAL
```

Implementasikan fungsi helper:

```python
def rank_duplicate_group(analyses: list[PhotoAnalysis]) -> list[PhotoAnalysis]:
    ...
```

Return list yang sudah diurutkan dari terbaik ke terburuk.

Setelah ranking:

* ranking pertama:

  * `is_best_duplicate = True`
  * `duplicate_quality_rank = 1`
* ranking berikutnya:

  * `is_best_duplicate = False`
  * `duplicate_quality_rank = 2`, `3`, dst.

---

## 9. Aturan Status Baru

Perbarui `classify_status` atau logic final status.

Aturan penting:

```text
Jika duplicate group memiliki lebih dari satu foto:
- hanya foto rank 1 yang boleh masuk SELECTED
- foto rank > 1 maksimal REVIEW
- jika rank > 1 dan kualitas jauh lebih buruk, boleh REJECTED
```

Aturan blur manusia:

```text
Jika localized_person_blur == True:
- status maksimal REVIEW
- kecuali tidak ada alternatif mirip yang lebih baik, tetap REVIEW, bukan SELECTED

Jika main_person_blur_score < 60:
- status maksimal REVIEW
- jika final_score rendah, REJECTED

Jika face blur sudah ada dari fitur sebelumnya dan face blur buruk:
- status maksimal REVIEW atau REJECTED
```

Contoh implementasi:

```python
if localized_person_blur and status == "SELECTED":
    status = "REVIEW"

if duplicate_quality_rank is not None and duplicate_quality_rank > 1:
    if status == "SELECTED":
        status = "REVIEW"
```

Untuk duplicate group:

```python
best = rank 1
others = rank > 1
```

Jika foto rank > 1 memiliki:

```text
human_quality_score < best_human_quality_score - 25
```

maka boleh diturunkan ke:

```text
REJECTED
```

---

## 10. Update CSV Report

Di `src/report_generator.py`, tambahkan kolom:

```text
person_count
main_person_blur_score
avg_person_blur_score
min_person_blur_score
localized_person_blur
human_quality_score
duplicate_quality_rank
is_best_duplicate
final_reason
```

Contoh `final_reason`:

```text
Selected as best duplicate because human subject is cleaner and no localized body blur detected.
```

```text
Moved to REVIEW because localized person blur was detected.
```

```text
Rejected because a similar photo has much better human quality score.
```

---

## 11. Update UI Streamlit

Di `app.py`, tampilkan kolom penting pada tabel:

```text
filename
status
final_score
human_quality_score
blur_score
blur_level
person_count
main_person_blur_score
localized_person_blur
face_count
duplicate_group
duplicate_quality_rank
is_best_duplicate
final_reason
```

Tambahkan teks penjelasan di UI:

```text
Sistem sekarang membandingkan foto mirip berdasarkan kualitas subjek manusia. Jika ada foto mirip yang lebih bersih dan tubuh manusianya lebih tajam, foto tersebut akan diprioritaskan.
```

Tambahkan sidebar setting:

```text
Enable Human-Aware Blur Detection
Person Detection Confidence
Person Patch Blur Threshold
Localized Blur Patch Ratio
```

Default:

```text
Enable Human-Aware Blur Detection: True
Person Detection Confidence: 0.35
Person Patch Blur Threshold: 75.0
Localized Blur Patch Ratio: 0.25
```

Jika user mematikan fitur ini, pipeline harus tetap berjalan dengan logic lama.

---

## 12. Performa dan Keterbatasan

Karena aplikasi harus tetap cocok untuk laptop tanpa NVIDIA GPU:

1. Gunakan model YOLO nano.
2. Jalankan inference di CPU.
3. Cache model.
4. Resize image untuk person detection jika perlu.
5. Jangan proses model berat.
6. Jangan gunakan PyTorch secara eksplisit selain dependency yang dibawa oleh Ultralytics.
7. Jangan training.
8. Jangan membutuhkan internet saat runtime setelah model tersedia.

Catatan: model pretrained mungkin akan diunduh pertama kali oleh Ultralytics jika belum ada. Setelah itu harus bisa berjalan lokal.

---

## 13. Fallback Jika YOLO Gagal

Jika Ultralytics/YOLO gagal load atau inference gagal:

1. Jangan crash aplikasi.
2. Set:

   * `person_count = 0`
   * `main_person_blur_score = None`
   * `avg_person_blur_score = None`
   * `min_person_blur_score = None`
   * `localized_person_blur = False`
   * `human_quality_score` dihitung dengan penalti ringan.
3. Tambahkan `final_reason` bahwa person detection gagal atau tidak tersedia.
4. Pipeline tetap selesai.

---

## 14. Testing

Tambahkan unit test:

### `test_person_blur_analyzer.py`

Test fungsi:

```python
calculate_blur_for_box
detect_localized_person_blur
```

Buat synthetic image sederhana dengan NumPy:

* gambar tajam dengan garis/rectangle
* gambar blur dengan Gaussian blur
* box valid dan invalid

### `test_human_quality_score.py`

Test:

```python
sharp person + no localized blur > blurry person + localized blur
```

Test:

```python
localized_person_blur=True menurunkan human_quality_score
```

### `test_duplicate_ranking.py`

Buat beberapa `PhotoAnalysis` dummy:

* Foto A: face_count tinggi, tetapi localized_person_blur=True
* Foto B: face_count sama, localized_person_blur=False, main_person_blur_score lebih tinggi

Pastikan:

```text
Foto B rank 1
Foto A rank 2
```

Pastikan foto rank 2 tidak boleh masuk SELECTED.

---

## 15. Quality Gate

Setelah selesai, jalankan:

```bash
python -m compileall app.py src tests
python -m unittest discover tests
```

Aplikasi harus tetap bisa dijalankan:

```bash
streamlit run app.py
```

---

## 16. Batasan yang Tidak Boleh Dilanggar

Jangan lakukan:

1. Jangan membuat training model baru.
2. Jangan membuat face recognition.
3. Jangan mengidentifikasi identitas orang.
4. Jangan menghapus file asli user.
5. Jangan memindahkan file asli user.
6. Jangan upload otomatis ke Facebook.
7. Jangan mengubah aplikasi menjadi cloud app.
8. Jangan menghapus fitur blur, exposure, duplicate, dan face detection yang sudah ada.
9. Jangan membuat dependency berat selain Ultralytics untuk person detection.
10. Jangan mengubah nama aplikasi **CullaGrace**.

---

## 17. Ekspektasi Hasil Akhir

Setelah perubahan:

* Sistem bisa mendeteksi area tubuh manusia.
* Sistem bisa menghitung blur khusus area tubuh manusia.
* Sistem bisa mendeteksi localized blur pada tubuh manusia.
* Jika ada dua foto mirip, sistem memilih foto dengan subjek manusia paling bersih.
* Foto dengan blur tubuh lokal tidak otomatis masuk SELECTED.
* Foto mirip yang lebih bersih mendapat rank lebih tinggi.
* CSV report menjelaskan alasan keputusan.
* UI menampilkan metrik human-aware blur.
* Pipeline tetap aman, offline-first, dan cocok untuk laptop tanpa GPU NVIDIA.

Mulai dengan audit struktur repository, lalu implementasikan perubahan secara bertahap.

```

Catatan penting: gunakan fitur ini sebagai **ranking antar foto mirip**, bukan sebagai aturan membuang semua foto dengan blur tubuh. Jadi foto dengan blur tangan masih bisa masuk **REVIEW** jika momennya bagus, tetapi tidak boleh mengalahkan foto mirip yang lebih bersih.
::contentReference[oaicite:1]{index=1}
```

[1]: https://docs.ultralytics.com/modes/predict?utm_source=chatgpt.com "Model Prediction with Ultralytics YOLO"
