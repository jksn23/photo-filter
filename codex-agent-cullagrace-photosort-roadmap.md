# Codex Agent Command — Implementasi CullaGrace Photo Culler berdasarkan Referensi PhotoSort

## Konteks

Repository target: `CullaGrace` / `photo-filter`.

Tujuan perubahan ini adalah mengembangkan CullaGrace menjadi photo culler yang lebih cerdas dengan mengambil inspirasi arsitektur dari PhotoSort, tetapi **tidak menyalin PhotoSort secara langsung**.

PhotoSort dijadikan referensi konseptual untuk:

- similarity analysis / near-duplicate grouping,
- blur detection,
- best-shot ranking per cluster,
- thumbnail/cache pipeline,
- batch processing,
- explainable culling decision,
- optional AI/aesthetic scoring.

Namun CullaGrace harus tetap memiliki engine sendiri yang modular, ringan, mudah diuji, dan sesuai kebutuhan utama: **memilih foto terbaik dari kumpulan foto mirip dengan mempertimbangkan wajah, tubuh, tangan, blur, exposure, dan kualitas teknis foto.**

---

## Instruksi Utama untuk Codex Agent

Kerjakan perubahan secara bertahap, aman, dan terukur. Jangan melakukan rewrite total tanpa alasan kuat. Pertahankan struktur project yang sudah ada jika masih memungkinkan, tetapi lakukan refactor jika diperlukan agar engine culling menjadi modular.

Implementasikan seluruh perubahan dalam beberapa milestone berikut.

---

# Milestone 1 — Audit dan Rapikan Struktur Project

## Tujuan

Pastikan project memiliki struktur yang jelas untuk memisahkan:

- UI,
- image loading,
- thumbnail/cache,
- metadata,
- scoring,
- similarity grouping,
- culling decision,
- export.

## Tugas

1. Audit struktur repository saat ini.
2. Identifikasi file/folder yang menangani:
   - import folder,
   - preview image,
   - selected/rejected,
   - image processing,
   - export result.
3. Jika belum ada, buat struktur modular berikut:

```txt
src/
  core/
    photo/
      photo-types.ts
      photo-loader.ts
      photo-metadata.ts
    cache/
      thumbnail-cache.ts
      analysis-cache.ts
    scoring/
      technical-score.ts
      blur-score.ts
      face-score.ts
      body-score.ts
      aesthetic-score.ts
      final-score.ts
    similarity/
      perceptual-hash.ts
      similarity-cluster.ts
      cluster-service.ts
    culling/
      best-photo-picker.ts
      culling-engine.ts
      culling-reasons.ts
    export/
      export-service.ts
  ui/
    components/
    pages/
    hooks/
  tests/
```

Sesuaikan ekstensi file dengan stack project yang digunakan. Jika project memakai JavaScript, gunakan `.js`. Jika TypeScript sudah tersedia atau mudah diaktifkan, gunakan `.ts`.

## Acceptance Criteria

- Struktur module jelas.
- Logic culling tidak bercampur langsung di UI.
- Ada tipe/model data `PhotoItem`, `PhotoScore`, `PhotoCluster`, dan `CullingResult`.
- Tidak ada breaking change pada fitur import/display/export yang sudah ada.

---

# Milestone 2 — Definisikan Data Model Culling

## Tujuan

Buat data model yang bisa dipakai seluruh pipeline.

## Implementasi

Buat atau update model berikut:

```ts
export type PhotoStatus = 'unprocessed' | 'selected' | 'rejected' | 'manual-selected' | 'manual-rejected';

export interface PhotoItem {
  id: string;
  path: string;
  fileName: string;
  thumbnailPath?: string;
  width?: number;
  height?: number;
  createdAt?: string;
  metadata?: PhotoMetadata;
  status: PhotoStatus;
  clusterId?: string;
  scores?: PhotoScore;
  reasons?: CullingReason[];
}

export interface PhotoMetadata {
  camera?: string;
  lens?: string;
  iso?: number;
  aperture?: string;
  shutterSpeed?: string;
  focalLength?: string;
  dateTaken?: string;
}

export interface PhotoScore {
  technicalScore: number;
  sharpnessScore: number;
  exposureScore: number;
  contrastScore: number;
  blurPenalty: number;
  faceScore?: number;
  faceSharpness?: number;
  eyeOpenScore?: number;
  bodySharpnessScore?: number;
  bodyBlurPenalty?: number;
  aestheticScore?: number;
  finalScore: number;
}

export interface PhotoCluster {
  id: string;
  photoIds: string[];
  selectedPhotoId?: string;
  rejectedPhotoIds: string[];
  confidence: number;
}

export interface CullingReason {
  type: 'positive' | 'negative' | 'neutral';
  code: string;
  message: string;
  score?: number;
}

export interface CullingResult {
  selected: PhotoItem[];
  rejected: PhotoItem[];
  clusters: PhotoCluster[];
  summary: CullingSummary;
}

export interface CullingSummary {
  totalPhotos: number;
  selectedCount: number;
  rejectedCount: number;
  clusterCount: number;
  mode: CullingMode;
}

export type CullingMode = 'conservative' | 'balanced' | 'aggressive';
```

## Acceptance Criteria

- Semua module scoring dan culling memakai model yang sama.
- Hasil selected/rejected bisa disertai alasan.
- Data model cukup fleksibel untuk future AI scoring.

---

# Milestone 3 — Thumbnail dan Analysis Cache

## Tujuan

Membuat proses import dan analisis lebih cepat, seperti konsep batch/cache pada PhotoSort.

## Tugas

1. Buat thumbnail cache untuk setiap foto.
2. Cache hasil analisis scoring agar tidak menghitung ulang setiap render.
3. Gunakan hash file atau kombinasi `path + size + modifiedTime` sebagai cache key.
4. Simpan hasil cache secara lokal, misalnya:

```txt
.cullagrace-cache/
  thumbnails/
  analysis/
```

atau gunakan storage yang sesuai dengan stack aplikasi.

## Acceptance Criteria

- Thumbnail dibuat sekali dan dipakai ulang.
- Analysis score tidak dihitung ulang jika file belum berubah.
- UI tetap responsif saat import banyak foto.

---

# Milestone 4 — Technical Scoring Dasar

## Tujuan

Mendeteksi kualitas teknis foto sebelum masuk ke AI yang lebih berat.

## Module

Buat module:

```txt
src/core/scoring/technical-score.ts
src/core/scoring/blur-score.ts
src/core/scoring/final-score.ts
```

## Scoring yang Dibutuhkan

### 1. Sharpness Score

Gunakan metode sederhana terlebih dahulu:

- variance of Laplacian, atau
- Tenengrad / Sobel gradient.

Output harus dinormalisasi ke `0.0 - 1.0`.

### 2. Exposure Score

Hitung histogram brightness.

Berikan penalti untuk:

- terlalu gelap,
- terlalu terang,
- highlight clipping berlebihan,
- shadow clipping berlebihan.

### 3. Contrast Score

Hitung distribusi luminance atau standard deviation brightness.

### 4. Blur Penalty

Jika sharpness terlalu rendah, berikan penalty.

Contoh awal:

```ts
finalTechnicalScore =
  sharpnessScore * 0.5 +
  exposureScore * 0.3 +
  contrastScore * 0.2 -
  blurPenalty;
```

Pastikan score tetap berada di range `0.0 - 1.0`.

## Acceptance Criteria

- Setiap foto memiliki `technicalScore`, `sharpnessScore`, `exposureScore`, `contrastScore`, dan `blurPenalty`.
- Score dapat ditampilkan di UI untuk debugging.
- Foto yang jelas blur mendapat score lebih rendah.

---

# Milestone 5 — Similarity Grouping Versi MVP

## Tujuan

Mengelompokkan foto mirip/near-duplicate agar sistem memilih pemenang di dalam cluster, bukan membandingkan semua foto secara global.

## Implementasi Awal

Gunakan perceptual hash terlebih dahulu:

- pHash,
- dHash,
- aHash,
- atau library image hash yang compatible dengan stack project.

Buat module:

```txt
src/core/similarity/perceptual-hash.ts
src/core/similarity/similarity-cluster.ts
src/core/similarity/cluster-service.ts
```

## Logic

1. Generate perceptual hash untuk setiap foto.
2. Hitung Hamming distance antar hash.
3. Group foto yang jaraknya di bawah threshold.
4. Simpan `clusterId` pada setiap `PhotoItem`.

Contoh parameter awal:

```ts
const SIMILARITY_THRESHOLD = 8;
```

Buat threshold configurable.

## Acceptance Criteria

- Foto yang sangat mirip masuk cluster yang sama.
- Foto berbeda scene tidak digabung.
- UI dapat menampilkan jumlah cluster.
- Cluster bisa dipakai oleh `BestPhotoPicker`.

---

# Milestone 6 — Best Photo Picker per Cluster

## Tujuan

Memilih foto terbaik dalam setiap cluster berdasarkan score.

## Module

Buat:

```txt
src/core/culling/best-photo-picker.ts
src/core/culling/culling-engine.ts
src/core/culling/culling-reasons.ts
```

## Logic

Untuk setiap cluster:

1. Ambil semua foto dalam cluster.
2. Pastikan setiap foto sudah punya score.
3. Urutkan berdasarkan `finalScore`.
4. Pilih foto dengan score tertinggi sebagai `selected`.
5. Tandai sisanya sebagai `rejected`, kecuali mode conservative memilih lebih dari satu kandidat.
6. Generate alasan selected/rejected.

## Mode Culling

Implementasikan 3 mode:

### Conservative

- Jangan terlalu agresif reject.
- Pilih maksimal 2-3 foto terbaik per cluster jika score berdekatan.
- Reject hanya jika score jauh lebih rendah atau jelas blur.

### Balanced

- Default mode.
- Pilih 1 foto terbaik per cluster.
- Jika cluster besar dan score kandidat dekat, boleh pilih 2.

### Aggressive

- Pilih hanya 1 foto terbaik per cluster.
- Reject duplicate/near-duplicate dengan lebih tegas.

## Reason Examples

Tambahkan alasan seperti:

```ts
{
  type: 'positive',
  code: 'BEST_IN_CLUSTER',
  message: 'Foto ini memiliki skor tertinggi dalam grup foto mirip.',
  score: 0.91
}
```

```ts
{
  type: 'negative',
  code: 'LOWER_SHARPNESS_THAN_SELECTED',
  message: 'Foto ini mirip dengan foto terpilih, tetapi memiliki ketajaman lebih rendah.',
  score: 0.62
}
```

## Acceptance Criteria

- Sistem memilih foto terbaik per cluster.
- Foto non-cluster tetap diproses secara masuk akal.
- Hasil selected/rejected menyertakan alasan.
- Mode conservative/balanced/aggressive bekerja berbeda.

---

# Milestone 7 — UI Selected / Rejected dengan Explainable Reasons

## Tujuan

Membuat hasil culling bisa dipercaya dan mudah di-debug.

## Tugas UI

Tambahkan panel atau section yang menampilkan:

- selected photos,
- rejected photos,
- cluster grouping,
- score breakdown,
- alasan selected/rejected.

Untuk setiap foto, tampilkan minimal:

```txt
Final Score
Sharpness
Exposure
Contrast
Blur Penalty
Cluster ID
Reason
```

Contoh tampilan alasan:

```txt
Selected: IMG_2045.jpg
✓ Best in similar group
✓ Higher sharpness score
✓ Better exposure

Rejected: IMG_2044.jpg
✕ Similar to IMG_2045.jpg
✕ Lower sharpness score
✕ Higher blur penalty
```

## Acceptance Criteria

- User dapat melihat kenapa foto dipilih atau ditolak.
- Debugging kesalahan culling menjadi mudah.
- Tidak hanya menampilkan hasil akhir tanpa penjelasan.

---

# Milestone 8 — Face-Aware Scoring

## Tujuan

Untuk portrait/event/wedding, wajah harus lebih diprioritaskan daripada background.

## Module

Buat:

```txt
src/core/scoring/face-score.ts
```

## Implementasi

Gunakan face detection yang tersedia sesuai stack project.

Pilihan:

- MediaPipe Face Detection / Face Mesh,
- OpenCV Haar Cascade,
- TensorFlow.js face landmark,
- library lain yang ringan dan compatible.

Hitung:

- apakah wajah terdeteksi,
- jumlah wajah,
- ukuran wajah relatif terhadap frame,
- face sharpness pada crop wajah,
- eye openness jika memungkinkan,
- penalti jika wajah blur.

## Scoring

Contoh:

```ts
faceScore =
  faceSharpness * 0.55 +
  eyeOpenScore * 0.25 +
  faceSizeScore * 0.10 +
  faceDetectionConfidence * 0.10;
```

Jika tidak ada wajah, jangan otomatis reject semua foto. Berikan fallback ke technical score.

## Acceptance Criteria

- Foto portrait dengan wajah tajam mendapat prioritas.
- Foto dengan wajah blur mendapat penalti.
- Face score tidak merusak foto non-portrait.

---

# Milestone 9 — Body / Subject Blur Detection

## Tujuan

Menyelesaikan kasus penting CullaGrace: dua foto mirip, wajah terlihat cukup baik, tetapi salah satu memiliki blur di tubuh/tangan. Sistem harus memilih foto yang tubuh/subjeknya lebih bersih.

## Module

Buat:

```txt
src/core/scoring/body-score.ts
```

## Implementasi Bertahap

### Versi 1 — Person Bounding Box

Gunakan person detection / segmentation jika tersedia.

Pilihan:

- MediaPipe Pose,
- YOLO person detector,
- TensorFlow.js pose/person model,
- fallback sederhana: gunakan area tengah frame jika person detection belum tersedia.

Hitung sharpness pada:

- area tubuh/person bounding box,
- area non-wajah,
- area tangan/lengan jika landmark tersedia.

### Versi 2 — Region-Based Body Sharpness

Jika pose landmark tersedia, bagi region:

- head/face,
- torso,
- left arm,
- right arm,
- legs jika terlihat.

Hitung sharpness masing-masing region.

### Versi 3 — Penalti Blur Lokal

Jika face sharpness bagus tetapi body sharpness rendah, beri penalti:

```ts
if (faceSharpness > 0.75 && bodySharpnessScore < 0.45) {
  bodyBlurPenalty += 0.2;
}
```

## Integrasi ke Final Score

Update final score:

```ts
finalScore =
  technicalScore * 0.30 +
  faceScore * 0.30 +
  bodySharpnessScore * 0.25 +
  aestheticScore * 0.10 -
  bodyBlurPenalty * 0.20;
```

Jika aesthetic score belum ada, redistribusikan bobotnya ke technical/face/body.

## Acceptance Criteria

- Jika ada dua foto mirip dan salah satunya blur di tubuh/tangan, sistem memilih yang lebih bersih.
- Body blur penalty muncul di reason panel.
- Face-only sharpness tidak lagi menjadi satu-satunya penentu.

---

# Milestone 10 — Optional AI / Aesthetic Scoring

## Tujuan

Menambahkan penilaian visual yang lebih natural, tetapi hanya sebagai pelengkap, bukan pengganti technical scoring.

## Module

Buat:

```txt
src/core/scoring/aesthetic-score.ts
```

## Pilihan Implementasi

Mulai dengan interface kosong/adaptor agar bisa diganti nanti:

```ts
export interface AestheticScorer {
  score(photo: PhotoItem): Promise<number>;
}
```

Implementasi awal boleh:

- disabled by default,
- mock scorer,
- local model jika sudah ada,
- external API jika project memang sudah mendukung.

## Rule

Aesthetic score tidak boleh mengalahkan foto yang jelas blur.

Contoh:

```ts
if (blurPenalty > 0.35 || bodyBlurPenalty > 0.35) {
  aestheticScoreWeight = 0.03;
}
```

## Acceptance Criteria

- Aesthetic score bersifat optional.
- App tetap berjalan tanpa AI model.
- Tidak ada dependency AI berat yang wajib untuk MVP.

---

# Milestone 11 — Testing Dataset dan Unit Tests

## Tujuan

Mencegah perubahan threshold merusak hasil culling.

## Buat Struktur Test Dataset

```txt
tests/fixtures/culling-dataset/
  similar-good-bad/
  blur-face/
  blur-body/
  blur-hand/
  low-light/
  overexposed/
  eyes-closed/
```

Jika belum ada aset gambar, buat test menggunakan mock score terlebih dahulu.

## Tests yang Harus Ada

1. `technical-score.test`
   - sharp image score lebih tinggi dari blur image.
   - underexposed image mendapat penalty.

2. `similarity-cluster.test`
   - near duplicate masuk cluster sama.
   - foto berbeda tidak digabung.

3. `best-photo-picker.test`
   - score tertinggi dipilih.
   - mode conservative memilih lebih dari satu jika score dekat.
   - mode aggressive memilih satu saja.

4. `body-score.test`
   - body blur penalty menurunkan final score.
   - foto dengan face score bagus tapi body blur tetap terkena penalti.

5. `culling-engine.test`
   - pipeline end-to-end menghasilkan selected/rejected/reasons.

## Acceptance Criteria

- Semua module utama punya test.
- Test bisa dijalankan dengan command standar project.
- Logic culling tidak hanya diuji manual lewat UI.

---

# Milestone 12 — Export Selected dan Audit Log

## Tujuan

Hasil culling dapat diekspor dan diaudit.

## Tugas

1. Pastikan selected photos dapat di-copy/export ke folder pilihan.
2. Tambahkan export JSON report:

```json
{
  "summary": {
    "totalPhotos": 100,
    "selectedCount": 35,
    "rejectedCount": 65,
    "clusterCount": 28,
    "mode": "balanced"
  },
  "selected": [],
  "rejected": [],
  "clusters": []
}
```

3. Simpan alasan culling dalam report.

## Acceptance Criteria

- User bisa export foto selected.
- User bisa export report JSON.
- Report menyertakan score dan alasan.

---

# Milestone 13 — Performance dan Batch Processing

## Tujuan

Aplikasi tetap responsif untuk ratusan/ribuan foto.

## Tugas

1. Jalankan analysis secara batch.
2. Hindari blocking UI thread.
3. Tambahkan progress state:

```txt
Scanning images...
Generating thumbnails...
Analyzing sharpness...
Grouping similar photos...
Picking best photos...
Done.
```

4. Tambahkan cancellation support jika memungkinkan.
5. Batasi concurrency agar tidak membekukan komputer.

## Acceptance Criteria

- Import 500+ foto tidak membuat UI freeze.
- Progress terlihat jelas.
- Analysis bisa dilanjutkan dari cache.

---

# Milestone 14 — Configuration dan Threshold Tuning

## Tujuan

Threshold mudah diubah tanpa edit logic inti.

## Buat Config

```ts
export const DEFAULT_CULLING_CONFIG = {
  mode: 'balanced',
  similarityThreshold: 8,
  sharpnessBlurThreshold: 0.45,
  bodyBlurThreshold: 0.45,
  faceScoreWeight: 0.3,
  bodyScoreWeight: 0.25,
  technicalScoreWeight: 0.3,
  aestheticScoreWeight: 0.1,
  conservativeKeepScoreDelta: 0.08,
};
```

## Acceptance Criteria

- Threshold tidak hardcoded tersebar di banyak file.
- Mode conservative/balanced/aggressive punya config masing-masing.
- Mudah tuning berdasarkan hasil dataset.

---

# Prioritas Implementasi

Kerjakan dengan urutan ini:

```txt
1. Data model
2. Cache thumbnail + analysis cache
3. Technical scoring
4. Similarity grouping
5. Best photo picker
6. Explainable reasons UI
7. Face-aware scoring
8. Body blur scoring
9. Export report
10. Tests
11. Performance tuning
12. Optional aesthetic/AI scoring
```

Jangan mulai dari AI/aesthetic scoring sebelum technical scoring, similarity grouping, dan best picker stabil.

---

# Non-Goals

Jangan lakukan hal berikut pada tahap ini:

- Jangan clone atau copy penuh PhotoSort ke dalam CullaGrace.
- Jangan menambahkan dependency AI berat sebagai requirement wajib.
- Jangan membuat auto-reject agresif tanpa explainable reasons.
- Jangan membuat UI baru total jika UI lama masih bisa ditingkatkan.
- Jangan menghapus fitur manual selection/rejection.
- Jangan mengandalkan aesthetic score sebagai penentu utama.

---

# Expected Final Result

Setelah semua milestone selesai, CullaGrace harus memiliki pipeline:

```txt
Import folder
↓
Generate thumbnail cache
↓
Analyze technical score
↓
Group similar photos
↓
Analyze face quality
↓
Analyze body/subject blur
↓
Calculate final score
↓
Pick best photo per cluster
↓
Mark selected/rejected
↓
Show reasons in UI
↓
Export selected photos + JSON report
```

---

# Definition of Done

Perubahan dianggap selesai jika:

1. App masih bisa import dan menampilkan foto.
2. App bisa mengelompokkan foto mirip.
3. App bisa memberi score teknis setiap foto.
4. App bisa memilih selected/rejected otomatis per cluster.
5. Setiap keputusan memiliki alasan yang terlihat di UI.
6. Sistem memberi penalti pada foto blur, termasuk body/subject blur.
7. User tetap bisa override manual selected/rejected.
8. Export selected photos tetap berjalan.
9. Ada test untuk scoring, clustering, dan best picker.
10. Tidak ada dependency berat yang wajib kecuali memang sudah tersedia di project.

---

# Catatan Penting untuk Codex Agent

Jika menemukan perbedaan stack atau struktur project dari asumsi di atas:

1. Jangan berhenti.
2. Adaptasikan nama folder/file sesuai struktur aktual.
3. Pertahankan prinsip modular.
4. Buat perubahan minimal tetapi lengkap.
5. Dokumentasikan perubahan di `CHANGELOG.md` atau `docs/culling-engine.md` jika tersedia.

Fokus utama bukan meniru PhotoSort, tetapi membangun CullaGrace sebagai photo culler yang:

- explainable,
- modular,
- testable,
- bisa memilih foto terbaik dari grup foto mirip,
- lebih peka terhadap blur pada wajah, tubuh, dan tangan.
