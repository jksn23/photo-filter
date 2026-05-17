# Codex Agent Prompt — Finalize CullaGrace to 100% Based on Review

## Repository

Work on this repository:

```text
https://github.com/jksn23/photo-filter
```

Project name: **CullaGrace**

The project has already been updated with a modular `src/core` architecture and now includes technical scoring, similarity clustering, face analysis, body blur analysis, best-photo picking, reports, cache, and Streamlit integration.

Your task is **not to rebuild everything from scratch**. Your task is to polish and complete the remaining gaps so the project becomes fully consistent, clean, explainable, and aligned with the intended CullaGrace architecture.

---

# Current Review Summary

The project is already around 75–85% aligned with the desired architecture.

What is already mostly correct:
- `src/core` exists.
- Core modules exist for photo types, quality, similarity, subject, scoring, culling, export, and cache.
- `run_culling_engine` exists.
- The pipeline includes technical score, face score, body score, final score, similarity clustering, best photo picker, CSV/JSON report, and Streamlit connection.
- README already mentions human-aware blur detection, technical scoring, similarity clustering, best-photo picker, cache, and JSON audit.

Remaining gaps to fix:
1. `src/culling_pipeline.py` still contains too much legacy logic and should become a thin compatibility wrapper.
2. Streamlit UI does not clearly expose full explainability: final score, technical score, face score, body score, cluster status, and reasons per photo.
3. README still mixes old scoring rules with the new normalized scoring engine.
4. Body/person blur analysis should be improved beyond a simple central crop heuristic, while staying lightweight and optional.
5. Test command/documentation should be consistent with the actual test framework.
6. All tests and source compilation must pass.

---

# Main Goal

Finalize the project so it is 100% aligned with this product direction:

```text
CullaGrace is an explainable photo culling engine that:
1. groups similar photos,
2. scores each photo technically,
3. evaluates face quality,
4. evaluates body/subject blur,
5. picks the best photo per cluster,
6. marks others as review/rejected according to mode,
7. explains every decision in reports and UI.
```

The user must be able to understand **why** a photo was selected, reviewed, or rejected.

---

# Non-Negotiable Rules

1. Do not remove working functionality.
2. Do not copy code from PhotoSort.
3. Keep the app local/offline by default.
4. Avoid adding heavy dependencies unless they are optional.
5. Do not make README or UI claims that backend does not actually support.
6. Make backward compatibility wrappers clean and minimal.
7. Keep all scoring explainable.
8. Make tests pass.
9. Make `python -m compileall src` pass.
10. Make Streamlit app runnable with `streamlit run app.py`.

---

# Task 1 — Clean `src/culling_pipeline.py`

## Problem

`src/culling_pipeline.py` currently still contains too much legacy implementation logic. It should not duplicate the new `src/core` engine.

## Required Change

Refactor `src/culling_pipeline.py` into a thin compatibility wrapper.

It should:
- preserve the public function(s) used by `app.py`,
- call `src.core.culling.culling_engine.run_culling_engine`,
- convert the new `PhotoItem`/`CullingResult` objects into the legacy dictionary/list shape only if the UI still expects that format,
- avoid duplicate scoring, duplicate detection, export, or report logic.

## Expected Result

`src/culling_pipeline.py` should primarily contain:
- imports,
- compatibility adapter function(s),
- small helper to transform core results to UI/report rows.

It should not contain:
- a second culling engine,
- a second duplicate picker,
- a second final score calculator,
- large legacy decision logic.

## Acceptance Criteria

- `app.py` still works.
- Existing public imports do not break.
- Core engine is the single source of truth.
- File is significantly smaller and easier to audit.

---

# Task 2 — Improve Streamlit Explainability UI

## Problem

Backend already produces scores and reasons, but the UI does not clearly show the full score breakdown and decision reasoning per photo.

## Required Change

Update `app.py` so after culling it displays:

### Summary Metrics

Show:
- total photos,
- selected count,
- review count,
- rejected count,
- cluster count,
- average final score,
- body blur warning count.

### Tabs

Use tabs:
- Selected
- Review
- Rejected
- Clusters
- Report / Audit

### Per Photo Detail

For each displayed photo, show:
- thumbnail/image preview,
- filename,
- status,
- cluster ID,
- cluster winner: yes/no,
- final score,
- technical score:
  - sharpness,
  - exposure,
  - contrast,
  - global blur penalty,
- face score:
  - face detected,
  - face count,
  - face sharpness,
  - face score,
- body/subject score:
  - person/subject detected,
  - body sharpness,
  - body blur penalty,
  - subject score,
- reasons.

### Cluster View

Create a cluster comparison view:
- group photos by `cluster_id`,
- show selected winner first,
- show rejected/review alternatives,
- show why winner was selected,
- show score gaps between winner and alternatives.

Example text:

```text
Cluster cluster_0007
Winner: IMG_1042.jpg
Reason: Highest final score, sharper body region, good face sharpness.

Alternatives:
- IMG_1041.jpg rejected: similar to winner, higher body blur penalty.
- IMG_1043.jpg review: close score to winner.
```

### Warning / Transparency

Add UI note:

```text
Human/body blur detection is currently heuristic-based and should be manually reviewed, especially for photos with multiple people or off-center subjects.
```

## Acceptance Criteria

- User can inspect why every photo was selected/rejected.
- `reasons` are visible in UI.
- Body blur penalty is visible in UI.
- Cluster winner and alternatives are visible.
- UI does not claim perfect AI/human detection.

---

# Task 3 — Fix README Scoring Documentation

## Problem

README currently mentions new normalized scoring features but also still describes old scoring rules such as:

```text
Skor dasar adalah 100
Blur: -40
No face: -10
Duplicate non-terbaik: -30
```

This conflicts with the new normalized scoring engine.

## Required Change

Rewrite README scoring section to match actual current implementation.

Document the new scoring model:

```text
CullaGrace calculates normalized sub-scores from 0.0 to 1.0:
- technical.sharpness
- technical.exposure
- technical.contrast
- technical.global_blur_penalty
- face.face_score
- body.subject_score
- body.body_blur_penalty
- final_score
```

Explain that UI/report may display final score as percentage if applicable.

Document mode behavior:
- Conservative
- Balanced
- Aggressive

Document decision workflow:

```text
1. Analyze each image.
2. Group similar images.
3. Rank images inside each cluster.
4. Select the best image per cluster.
5. Send close candidates to Review depending on mode.
6. Reject clearly lower-quality duplicates.
```

Document limitation:

```text
Body blur detection is heuristic. It estimates subject/body sharpness using detected person regions when available, or central-subject fallback when not available.
```

## Also Fix Test Instructions

If the project uses `pytest`, README should say:

```bash
python -m pytest -q
```

If it uses `unittest`, keep unittest. But make the README match the actual tests.

## Acceptance Criteria

- README no longer contradicts the new engine.
- README scoring explanation matches code.
- README clearly states limitations.
- Test command is correct.

---

# Task 4 — Improve Body / Person Blur Analyzer

## Problem

Body blur analysis currently exists but may still be too heuristic. It should better support the real CullaGrace use case:

```text
Given similar photos with similarly good faces, choose the photo with cleaner body/hand/subject sharpness.
```

## Required Change

Improve `src/core/subject/person_blur_analyzer.py`.

### Preferred Lightweight Approach

Implement a layered strategy:

```text
1. If a person detector is available and enabled:
   - detect person bounding boxes,
   - analyze sharpness inside person boxes,
   - exclude face boxes from the body region when possible.

2. If person detector is not available:
   - use central subject fallback,
   - exclude face boxes if available,
   - analyze body/subject region.

3. If even fallback is weak:
   - use weighted central crop region.
```

### Optional Person Detector

If current repo already references YOLO / Ultralytics, make it optional:
- do not crash if `ultralytics` is not installed,
- do not force download in tests,
- provide clear fallback,
- expose a parameter such as `enable_person_detection`.

Suggested API:

```python
analyze_person_body_blur(
    image,
    face_regions: list[tuple[int, int, int, int]] | None = None,
    enable_person_detection: bool = False,
    detector: object | None = None,
) -> BodyScore
```

### Region Analysis Requirements

For each body/subject region:
- compute Laplacian variance,
- compute Tenengrad or Sobel sharpness,
- normalize sharpness to 0–1,
- combine multiple regions robustly,
- ignore tiny regions,
- avoid division by zero,
- clamp values to 0–1.

### Body Blur Penalty

Ensure:

```text
body_blur_penalty = high when body region is blurry
body_blur_penalty = low when body region is sharp
subject_score = high when body/subject is sharp
```

### Face Exclusion

When face regions are passed:
- avoid letting a sharp face hide a blurry body,
- mask or exclude face area from the subject/body sharpness region.

This is important because body blur should matter when the face is already okay.

## Acceptance Criteria

- Blurred body region produces lower `body_sharpness`.
- Blurred body region produces higher `body_blur_penalty`.
- Sharp face alone cannot fully compensate for blurry body in body score.
- Function does not crash without YOLO/Ultralytics.
- Function does not download models during tests.
- Tests cover sharp vs blurred body region.
- Tests cover fallback behavior.

---

# Task 5 — Strengthen Final Score Tie-Breaking

## Problem

Final score must ensure body blur can change the winner when faces are similar.

## Required Change

Update `src/core/scoring/final_score.py` and/or `src/core/culling/best_photo_picker.py`.

Make sure this case passes:

```text
Photo A:
- face_score = 0.90
- body_sharpness = 0.30
- body_blur_penalty = 0.70

Photo B:
- face_score = 0.86
- body_sharpness = 0.80
- body_blur_penalty = 0.20

Expected:
Photo B should outrank Photo A in balanced/aggressive mode.
```

This does not mean body always beats face. It means when faces are close, body blur should become a meaningful tie-breaker.

## Acceptance Criteria

Add test:

```text
test_body_blur_can_change_cluster_winner_when_face_scores_are_close
```

The test should:
- create two `PhotoItem` objects in one `PhotoCluster`,
- manually assign scores,
- run final scoring and best picker,
- assert cleaner body photo becomes selected.

---

# Task 6 — Improve Reason Builder

## Problem

The report and UI should explain not only that a photo was rejected, but why compared to the cluster winner.

## Required Change

Update `src/core/scoring/reason_builder.py`.

Reasons should include:
- selected as best in similar cluster,
- unique image,
- rejected because similar winner has higher final score,
- score gap from winner,
- body blur detected,
- face sharpness good/poor,
- low global sharpness,
- good/poor exposure,
- close candidate kept for review,
- aggressive mode rejected duplicate,
- conservative mode kept close candidate for review.

Add cluster-relative reasons:
- compare non-winner to selected winner,
- mention if non-winner has higher body blur penalty,
- mention if non-winner has lower face score,
- mention if final score gap is small/large.

Example:

```text
Rejected: similar to IMG_1042.jpg; final score lower by 0.18; body blur penalty higher by 0.32.
```

## Acceptance Criteria

- Reasons include cluster-relative comparison.
- Reasons are visible in CSV/JSON and UI.
- Tests verify body blur reason appears when body penalty is high.

---

# Task 7 — Report Improvements

## Problem

CSV/JSON should be complete enough for audit/debugging.

## Required Change

Update `src/core/export/report_writer.py`.

CSV columns should include at minimum:

```text
filename
path
status
cluster_id
is_cluster_winner
selected_photo_id
final_score
score_percent
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
duplicate_penalty
mode
reasons
```

JSON should include:
- summary,
- per-photo records,
- per-cluster records,
- selected winner per cluster,
- score breakdown,
- reasons.

## Acceptance Criteria

- CSV and JSON both include body blur fields.
- JSON includes cluster relationship.
- Report can be used to debug why a photo lost.

---

# Task 8 — Tests and Quality Gates

## Required Commands

Run:

```bash
python -m compileall src
python -m pytest -q
```

If tests use unittest instead of pytest, either:
- migrate to pytest consistently, or
- update README to match actual test command.

Prefer pytest if the existing tests are already pytest-style.

## Required Tests

Ensure these tests exist and pass:

```text
tests/test_culling_pipeline_wrapper.py
tests/test_streamlit_result_adapter.py
tests/test_person_blur_analyzer.py
tests/test_final_score.py
tests/test_best_photo_picker.py
tests/test_reason_builder.py
tests/test_report_writer.py
tests/test_readme_consistency.py
```

The exact filenames can vary, but coverage must include:
- wrapper calls core engine,
- body blur sharp vs blurred comparison,
- body blur changes cluster winner when face scores are close,
- reasons include body blur and cluster comparison,
- report includes body blur fields,
- README does not mention old base-100 scoring rules if engine no longer uses them.

## Acceptance Criteria

- `python -m compileall src` passes.
- `python -m pytest -q` passes.
- No broken imports.
- No test requires downloading external AI models.
- Tests can run offline.

---

# Task 9 — Keep Optional YOLO / Person Detection Safe

If the repo currently mentions or uses YOLO/Ultralytics:

## Required Behavior

- It must be optional.
- It must not break installation if unavailable.
- It must not run in unit tests by default.
- It must not auto-download models unless user explicitly enables it.
- The fallback central-subject analyzer must always work.

## UI Requirement

In Streamlit, if person detection is optional:
- show whether it is enabled,
- show when fallback heuristic is used,
- avoid making claims that YOLO is always active.

## README Requirement

Document:

```text
Person detection is optional. If unavailable, CullaGrace falls back to heuristic subject-region blur analysis.
```

---

# Task 10 — Final Manual Smoke Test

After implementation, do a manual smoke test with a small generated dataset.

Create or use tests to simulate:

```text
input/
  cluster_1_sharp_body.jpg
  cluster_1_blurry_body.jpg
  unique_dark.jpg
  unique_sharp.jpg
```

Run the engine and verify:
- cluster sharp body image is selected,
- blurry body duplicate is rejected/review,
- reports are generated,
- reasons mention body blur,
- output folders are created.

This can be automated as a test.

---

# Deliverables

When finished, provide a summary with:

1. Files modified.
2. Files created.
3. Legacy code removed or wrapped.
4. UI explainability improvements.
5. README changes.
6. Body blur analyzer improvements.
7. Tests added/updated.
8. Exact test results:
   - `python -m compileall src`
   - `python -m pytest -q`
9. Remaining limitations.

---

# Final Definition of Done

The task is complete only when all are true:

- `src/culling_pipeline.py` is a thin wrapper.
- `run_culling_engine` is the single source of truth.
- Streamlit UI shows score breakdown and reasons.
- Cluster comparison is visible.
- README scoring section matches actual normalized scoring.
- Body blur analyzer has optional detector strategy plus safe fallback.
- Body blur can change selected cluster winner when face scores are close.
- CSV and JSON reports include body blur and cluster comparison fields.
- Tests pass offline.
- Source compiles.
- No UI or README claim exceeds what backend actually does.
