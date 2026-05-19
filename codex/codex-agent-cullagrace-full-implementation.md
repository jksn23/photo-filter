# Codex Agent Command — Implement CullaGrace Photo Culling Engine 100%

## Context

You are working on this repository:

```text
https://github.com/jksn23/photo-filter
```

The project is a photo culling application. The desired product direction is **CullaGrace**: an explainable intelligent photo culler inspired by PhotoSort concepts, but implemented as our own clean, modular engine.

Important: **Do not copy PhotoSort code directly.** Use PhotoSort only as conceptual inspiration:
- similarity grouping,
- technical image quality scoring,
- best photo picking per similar cluster,
- face-aware scoring,
- person/body blur scoring,
- explainable selected/rejected reasons,
- CSV/report output.

The current repository already has a basic MVP with:
- Streamlit UI,
- blur detection,
- exposure detection,
- duplicate detection via perceptual hash,
- face count detection,
- scoring,
- Selected / Review / Rejected output folders,
- CSV report.

However, the current implementation is not yet aligned with the full CullaGrace architecture. Your task is to refactor and implement the missing architecture and features properly.

---

# Main Goal

Transform the current project into a modular CullaGrace photo culling engine with this pipeline:

```text
Import folder
→ Build PhotoItem objects
→ Generate/load thumbnails/cache metadata
→ Compute technical score
→ Compute similarity clusters
→ Compute face-aware score
→ Compute person/body blur score
→ Pick best photo per cluster
→ Assign selected/review/rejected
→ Generate explainable reasons
→ Export selected/review/rejected images
→ Generate detailed CSV/JSON report
→ Expose result clearly in Streamlit UI
```

The final system must be able to handle this case correctly:

```text
Given two visually similar photos:
- Photo A has a sharper face but blurred hand/body
- Photo B has similarly good face quality but cleaner body/hand sharpness

The system must prefer Photo B, because full-subject/body blur should affect the final choice when faces are similar.
```

---

# Non-Negotiable Requirements

1. Keep the app runnable with Streamlit.
2. Keep existing basic features working.
3. Do not remove useful existing functionality without replacing it.
4. Add a clean modular backend under `src/core`.
5. Existing old modules may remain as wrappers, but the main culling pipeline should use the new engine.
6. Add tests for every new core module.
7. Make the test suite pass.
8. Avoid heavyweight AI dependencies for the first implementation unless optional.
9. Prefer OpenCV, NumPy, Pillow, imagehash, and lightweight rule-based scoring for MVP.
10. Make every automatic decision explainable.

---

# Target Folder Structure

Create or refactor the project toward this structure:

```text
src/
  core/
    __init__.py

    photo/
      __init__.py
      photo_types.py
      image_loader.py
      thumbnail_cache.py

    quality/
      __init__.py
      technical_score.py
      blur_metrics.py
      exposure_metrics.py

    similarity/
      __init__.py
      similarity_cluster.py
      perceptual_hash.py

    subject/
      __init__.py
      face_analyzer.py
      person_blur_analyzer.py
      body_score.py

    scoring/
      __init__.py
      final_score.py
      reason_builder.py

    culling/
      __init__.py
      best_photo_picker.py
      culling_engine.py

    export/
      __init__.py
      file_exporter.py
      report_writer.py

  blur_detector.py
  exposure_detector.py
  duplicate_detector.py
  face_detector.py
  scorer.py
  culling_pipeline.py
  report_generator.py
```

The old root-level modules under `src/` should either:
- delegate to the new `src/core` modules, or
- remain backward-compatible wrappers.

Do not leave duplicated conflicting logic.

---

# Data Models

Create `src/core/photo/photo_types.py`.

Implement dataclasses similar to this:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

PhotoStatus = Literal["unprocessed", "selected", "review", "rejected"]

@dataclass
class TechnicalScore:
    sharpness: float = 0.0
    exposure: float = 0.0
    contrast: float = 0.0
    global_blur_penalty: float = 0.0

@dataclass
class FaceScore:
    face_detected: bool = False
    face_count: int = 0
    face_sharpness: float = 0.0
    face_score: float = 0.0

@dataclass
class BodyScore:
    person_detected: bool = False
    body_sharpness: float = 0.0
    body_blur_penalty: float = 0.0
    subject_score: float = 0.0

@dataclass
class PhotoScore:
    technical: TechnicalScore = field(default_factory=TechnicalScore)
    face: FaceScore = field(default_factory=FaceScore)
    body: BodyScore = field(default_factory=BodyScore)
    duplicate_penalty: float = 0.0
    final_score: float = 0.0
    reasons: list[str] = field(default_factory=list)

@dataclass
class PhotoItem:
    id: str
    path: Path
    filename: str
    width: int = 0
    height: int = 0
    cluster_id: str | None = None
    is_cluster_winner: bool = False
    status: PhotoStatus = "unprocessed"
    score: PhotoScore = field(default_factory=PhotoScore)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PhotoCluster:
    id: str
    photos: list[PhotoItem]
    selected_photo_id: str | None = None
```

You may adjust names if necessary, but the same concepts must exist.

---

# Technical Score

Create `src/core/quality/technical_score.py`.

Implement:

```python
compute_technical_score(image) -> TechnicalScore
```

It must calculate:

1. **Sharpness**
   - Use variance of Laplacian and/or Tenengrad.
   - Normalize into a 0–1 score.

2. **Exposure**
   - Use grayscale brightness.
   - Penalize underexposed and overexposed images.
   - Normalize into 0–1.

3. **Contrast**
   - Use grayscale standard deviation.
   - Normalize into 0–1.

4. **Global blur penalty**
   - Higher penalty for low sharpness.

Suggested behavior:

```text
sharpness near 1.0 = sharp
sharpness near 0.0 = blurry
exposure near 1.0 = well exposed
contrast near 1.0 = good contrast
global_blur_penalty near 1.0 = very blurry
```

Add tests:
- sharp synthetic image should score higher than blurred synthetic image.
- dark image should have lower exposure score.
- over-bright image should have lower exposure score.

---

# Similarity Clustering

Create `src/core/similarity/perceptual_hash.py`.

Implement:

```python
compute_phash(path: Path) -> imagehash.ImageHash
hash_distance(hash_a, hash_b) -> int
```

Create `src/core/similarity/similarity_cluster.py`.

Implement:

```python
build_similarity_clusters(photo_items: list[PhotoItem], threshold: int = 8) -> list[PhotoCluster]
```

Requirements:
- Use perceptual hash for MVP.
- Similar photos should share the same cluster.
- Unique photos should each become their own cluster.
- Assign `cluster_id` on each `PhotoItem`.
- Do not mark selected/rejected here. Clustering only groups images.

Add tests:
- identical/similar generated images go into the same cluster.
- clearly different generated images go into different clusters.
- each PhotoItem receives a cluster ID.

---

# Face Analyzer

Create `src/core/subject/face_analyzer.py`.

Implement:

```python
analyze_face(image) -> FaceScore
```

Requirements:
- Use OpenCV Haar Cascade initially, or reuse existing `face_detector.py`.
- Detect face count.
- If a face is found, crop face region and compute face sharpness.
- Normalize face sharpness 0–1.
- Produce `face_score`.

Suggested behavior:
- No face:
  - `face_detected = False`
  - `face_score` may be neutral or low depending on mode.
- Face found:
  - score increases with face sharpness.
  - multiple faces should not break the calculation.

Do not add MediaPipe dependency yet unless already available.

Add tests:
- function returns a valid FaceScore for image without faces.
- face_score values are bounded between 0 and 1.
- no exception on small/invalid-looking images.

---

# Person / Body Blur Analyzer

Create `src/core/subject/person_blur_analyzer.py`.

Implement:

```python
analyze_person_body_blur(image, face_regions: list[tuple[int, int, int, int]] | None = None) -> BodyScore
```

MVP implementation may be heuristic-based.

Requirements:
- Estimate subject/body sharpness beyond the face.
- If no person detector is available, use a central subject region heuristic:
  - central vertical crop,
  - exclude detected face regions if available,
  - compute Laplacian/Tenengrad sharpness on remaining region.
- Normalize body sharpness 0–1.
- Compute `body_blur_penalty`.
- Set `person_detected` to True if body/subject region can be estimated.

Important:
The body score must help solve the known issue:
- two similar images,
- both acceptable faces,
- one has blur in hand/body,
- choose the cleaner body image.

Suggested formula:

```text
body_blur_penalty = 1.0 - body_sharpness
subject_score = body_sharpness - weighted_body_blur_penalty
```

Clamp values to 0–1.

Add tests:
- a sharp synthetic image region should score higher than a blurred version.
- body_blur_penalty should be higher for blurred image.
- values must remain within 0–1.

---

# Final Scoring

Create `src/core/scoring/final_score.py`.

Implement:

```python
compute_final_score(
    technical: TechnicalScore,
    face: FaceScore,
    body: BodyScore,
    mode: str = "balanced",
) -> float
```

Modes:

## Conservative
- Reject fewer images.
- Lower duplicate/body penalties.
- More photos go to review.

## Balanced
Default.

## Aggressive
- Stronger duplicate and blur penalties.
- Select fewer photos.
- Reject more duplicates.

Suggested balanced formula:

```text
final_score =
    0.30 * technical.sharpness
  + 0.20 * technical.exposure
  + 0.10 * technical.contrast
  + 0.25 * face.face_score
  + 0.15 * body.subject_score
  - 0.15 * technical.global_blur_penalty
  - 0.20 * body.body_blur_penalty
```

Clamp final score to 0–1.

Important:
- Body blur must be meaningful enough to change ranking inside a cluster.
- If faces are similar, body sharpness should be a strong tie-breaker.

Add tests:
- higher body blur penalty lowers final score.
- sharper face increases final score.
- mode changes thresholds or penalties predictably.
- score remains in 0–1.

---

# Reason Builder

Create `src/core/scoring/reason_builder.py`.

Implement:

```python
build_reasons(photo: PhotoItem, cluster: PhotoCluster | None = None) -> list[str]
```

Reasons should include human-readable explanations such as:

```text
"Selected as best image in similar cluster"
"Rejected because similar photo has higher final score"
"Sharp face detected"
"Body/subject blur detected"
"Low global sharpness"
"Good exposure"
"Underexposed"
"Overexposed"
"No face detected"
"Unique image"
```

The reasons must be shown in report output and optionally UI.

Add tests:
- selected cluster winner receives selected reason.
- non-winner duplicate receives rejected reason.
- body blur penalty adds body blur reason.

---

# Best Photo Picker

Create `src/core/culling/best_photo_picker.py`.

Implement:

```python
pick_best_photos(
    clusters: list[PhotoCluster],
    mode: str = "balanced",
    keep_per_cluster: int = 1,
) -> list[PhotoCluster]
```

Requirements:
- Sort each cluster by `photo.score.final_score`.
- Mark highest scoring photo as `is_cluster_winner = True`.
- Assign `selected_photo_id`.
- For duplicate clusters:
  - winner status = `selected`
  - non-winners status = `rejected` or `review` depending on mode and score gap.
- For unique clusters:
  - high score = selected
  - medium score = review
  - low score = rejected.
- The score gap threshold should vary by mode.

Suggested thresholds:
- Conservative:
  - selected >= 0.55
  - review >= 0.35
  - duplicate loser goes review if close.
- Balanced:
  - selected >= 0.65
  - review >= 0.45
- Aggressive:
  - selected >= 0.75
  - review >= 0.55
  - duplicate losers usually rejected.

Add tests:
- highest scoring photo in cluster becomes selected.
- lower scoring duplicate becomes rejected/review.
- unique low score becomes rejected.
- mode affects statuses.

---

# Culling Engine

Create `src/core/culling/culling_engine.py`.

Implement a clean high-level function:

```python
run_culling_engine(
    input_dir: Path,
    output_dir: Path | None = None,
    mode: str = "balanced",
    recursive: bool = True,
    copy_files: bool = True,
) -> list[PhotoItem]
```

Pipeline:
1. Load image file paths.
2. Create PhotoItem objects.
3. For each image:
   - load image,
   - compute technical score,
   - analyze face,
   - analyze body/person blur,
   - compute final score.
4. Build similarity clusters.
5. Pick best photo per cluster.
6. Build reasons for every photo.
7. Optionally copy files into:
   - `Selected`
   - `Review`
   - `Rejected`
8. Generate CSV and JSON report.

The old `src/culling_pipeline.py` should call this new engine or be refactored to use it.

Keep public compatibility if Streamlit currently imports `run_culling`.

---

# Exporter and Report

Create `src/core/export/file_exporter.py`.

Implement:

```python
export_photos(photo_items: list[PhotoItem], output_dir: Path) -> None
```

Folders:

```text
Selected/
Review/
Rejected/
```

Create `src/core/export/report_writer.py`.

Implement:

```python
write_csv_report(photo_items: list[PhotoItem], output_dir: Path) -> Path
write_json_report(photo_items: list[PhotoItem], output_dir: Path) -> Path
```

CSV should include:

```text
filename
path
status
cluster_id
is_cluster_winner
final_score
technical_sharpness
technical_exposure
technical_contrast
global_blur_penalty
face_detected
face_count
face_sharpness
face_score
person_detected
body_sharpness
body_blur_penalty
subject_score
reasons
```

JSON should include all structured scoring fields.

The existing `report_generator.py` may delegate to `report_writer.py`.

---

# Streamlit UI Update

Update `app.py`.

The UI should clearly support:

1. Input folder selection.
2. Output folder selection.
3. Culling mode:
   - Conservative
   - Balanced
   - Aggressive
4. Run culling.
5. Show summary:
   - total photos,
   - selected count,
   - review count,
   - rejected count,
   - cluster count.
6. Show selected/review/rejected tabs.
7. Show score details per photo:
   - final score,
   - face score,
   - body score,
   - technical score,
   - reasons.
8. Show warning that culling is automatic and should be reviewed manually.

Do not make UI claims that are not supported by backend.

If body blur analysis is heuristic, label it as heuristic.

---

# Backward Compatibility

Update old modules:

## `src/blur_detector.py`
Should delegate to `src/core/quality/blur_metrics.py` or technical score logic.

## `src/exposure_detector.py`
Should delegate to `src/core/quality/exposure_metrics.py`.

## `src/duplicate_detector.py`
Should expose:
- current old function names,
- plus compatibility functions expected by existing tests if any.

If tests expect `map_duplicate_groups`, either:
- implement it, or
- update tests to match the new architecture, but do not leave broken imports.

## `src/scorer.py`
Should delegate to `src/core/scoring/final_score.py`.

## `src/culling_pipeline.py`
Should be a wrapper around `run_culling_engine`.

---

# Testing Requirements

Run and fix:

```bash
python -m pytest -q
```

Add tests if missing:

```text
tests/test_photo_types.py
tests/test_technical_score.py
tests/test_similarity_cluster.py
tests/test_face_analyzer.py
tests/test_person_blur_analyzer.py
tests/test_final_score.py
tests/test_reason_builder.py
tests/test_best_photo_picker.py
tests/test_culling_engine.py
tests/test_report_writer.py
```

All tests must pass.

Where tests currently import nonexistent modules, fix by implementing the modules, not by deleting the tests.

---

# Quality Gates

Before finishing, verify:

```bash
python -m compileall src
python -m pytest -q
```

If formatting tools exist in the repo, run them. If not, do not introduce unnecessary tooling.

---

# Implementation Strategy

Implement in this order:

## Step 1 — Create dataclasses
Create `photo_types.py` first. Update imports.

## Step 2 — Implement technical scoring
Create reusable blur/exposure/contrast metrics.

## Step 3 — Implement similarity clustering
Use perceptual hash. Assign cluster IDs.

## Step 4 — Implement face analyzer
Use existing OpenCV face detection if possible.

## Step 5 — Implement body blur analyzer
Start with central-subject heuristic. Exclude face crop where possible.

## Step 6 — Implement final score
Make scoring mode-aware and clamp values.

## Step 7 — Implement best photo picker
Make cluster selection and status assignment deterministic.

## Step 8 — Implement reason builder
Make every decision explainable.

## Step 9 — Implement culling engine
Connect all modules into the actual production pipeline.

## Step 10 — Update export/report
Write detailed CSV and JSON.

## Step 11 — Update Streamlit UI
Show score breakdown and reasons.

## Step 12 — Fix tests
Make the complete test suite pass.

---

# Acceptance Criteria

The task is complete only when all of these are true:

1. `src/core` exists with the modular structure.
2. Main pipeline uses `run_culling_engine`.
3. Similar images are clustered before selection.
4. Each cluster has a selected best photo.
5. Face sharpness affects final score.
6. Body/subject blur affects final score.
7. Body blur can change the selected winner when faces are similarly good.
8. Every photo has final score and reasons.
9. Selected/Review/Rejected export still works.
10. CSV report includes detailed score breakdown.
11. JSON report exists.
12. Streamlit UI displays selected/review/rejected and reasons.
13. Tests pass with `python -m pytest -q`.
14. Source compiles with `python -m compileall src`.
15. README is updated to accurately describe the implemented features.

---

# README Update

Update `README.md` to describe the new CullaGrace engine:

```text
CullaGrace uses an explainable culling pipeline:
- technical sharpness/exposure/contrast scoring,
- similarity clustering,
- face-aware quality scoring,
- heuristic subject/body blur scoring,
- best-photo-per-cluster selection,
- selected/review/rejected export,
- detailed CSV/JSON reports.
```

Also document limitations:

```text
Body blur detection is currently heuristic-based and may be improved later with person segmentation or pose estimation.
```

---

# Important Notes

- Keep implementation simple and reliable first.
- Do not introduce CLIP, DINOv2, PyTorch, MediaPipe, or ONNX unless explicitly required later.
- The current goal is a strong explainable MVP, not a heavy AI system.
- The system should be easy to debug.
- Scores must be visible in reports.
- Reasons must be human-readable.
- Avoid overfitting to one test image.
- Avoid magic constants without comments.
- Use clear thresholds and document them.

---

# Final Output Expected From Codex Agent

When finished, provide:

1. Summary of implemented changes.
2. Files created.
3. Files modified.
4. Tests added/updated.
5. Test results.
6. Any limitations still remaining.
7. Next recommended improvements.

