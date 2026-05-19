# Codex Agent Guide — CullaGrace Performance Architecture Update

## Repository

Work on this repository:

```text
https://github.com/jksn23/photo-filter
```

Project name: **CullaGrace**

This guide describes the next architecture update for CullaGrace. The goal is to make the culling process faster, more memory-efficient, more configurable, and safer for large photo folders.

CullaGrace currently has:
- automatic photo culling,
- AI recommendation buckets: `Selected`, `Review`, `Rejected`,
- V2 review workflow with final decisions: `Posts`, `Save`, `Delete`, `Undecided`,
- Streamlit UI,
- modular `src/core` architecture,
- technical scoring,
- face analysis,
- body blur analysis,
- similarity clustering,
- best photo picker,
- reports.

The next update must add a **performance-oriented culling architecture**.

---

# Main Goal

Implement a configurable and optimized culling pipeline:

```text
User chooses folder
↓
User chooses performance settings
↓
System scans files
↓
System checks analysis cache
↓
Only new/changed photos are analyzed
↓
Analysis uses resized images, not full-resolution images
↓
Optional parallel workers analyze pending photos
↓
Similarity clustering runs using cached/new hashes
↓
Best photo picker assigns Selected / Review / Rejected
↓
Reports are generated
↓
Optional file copy/export is performed
↓
V2 review workflow continues
```

The system must be faster because it should:

1. Cache expensive analysis results.
2. Avoid full-resolution analysis unless explicitly requested.
3. Process photos incrementally.
4. Allow Fast / Balanced / Accurate modes.
5. Use controlled parallel processing.
6. Avoid unnecessary file copying.
7. Keep original images only for review/export, not routine scoring.

---

# Critical Design Principles

## 1. Original Image Is Not for Routine Analysis

Use original files only for:
- final export,
- full-resolution detail review,
- crop inspection,
- opening original file/folder.

Use resized analysis images for:
- blur detection,
- exposure/contrast,
- face analysis,
- body blur analysis,
- pHash,
- technical scoring.

Use thumbnails for:
- grid UI,
- bucket cards,
- fast browsing.

Never confuse these three:

```text
Thumbnail image        → UI grid
Resized analysis image → culling engine scoring
Original image         → detail review/export
```

---

## 2. Cache Everything Expensive

If a photo has already been analyzed and the file has not changed, do not recompute:
- thumbnail,
- pHash,
- technical score,
- face score,
- body score,
- final score input fields.

Cache should be invalidated when:
- file path changes,
- file size changes,
- modified time changes,
- analysis mode changes,
- max analysis size changes,
- cache version changes,
- scoring version changes.

---

## 3. Performance Must Be User-Controlled

The user should be able to choose:

```text
Fast
Balanced
Accurate
```

The user should also be able to configure:
- max analysis size,
- worker count,
- use cache,
- face analysis on/off,
- body blur analysis on/off,
- similarity grouping on/off,
- copy files after culling on/off,
- generate thumbnails on/off.

---

## 4. Do Not Load All Images Into RAM

Never store original image arrays in `PhotoItem`.

A `PhotoItem` should store:
- path,
- metadata,
- thumbnail path,
- score fields,
- cluster ID,
- status,
- reasons.

It should not store:
- full image arrays,
- OpenCV matrices,
- PIL Image objects.

---

## 5. Copying Files Should Be Optional

Copying large photos into `Selected`, `Review`, and `Rejected` can be slow.

Add option:

```text
Copy files after culling: ON/OFF
```

If OFF:
- generate reports,
- create review session,
- keep paths to original files,
- do not copy AI bucket folders immediately.

Final export after V2 review should still work.

---

# Target Architecture

Add or update these modules.

Preferred structure:

```text
src/core/performance/
  __init__.py
  performance_config.py
  presets.py
  resource_limits.py

src/core/cache/
  __init__.py
  analysis_cache.py
  cache_types.py
  cache_key.py

src/core/pipeline/
  __init__.py
  photo_analyzer.py
  parallel_runner.py
  progress_events.py

src/core/culling/
  culling_engine.py
```

If the current repository already has some of these folders, extend them rather than duplicating functionality.

If a simpler structure is currently more consistent, at minimum implement:

```text
src/core/performance/performance_config.py
src/core/cache/analysis_cache.py
src/core/pipeline/photo_analyzer.py
src/core/pipeline/parallel_runner.py
src/core/pipeline/progress_events.py
```

---

# Phase 1 — Performance Config

Create:

```text
src/core/performance/performance_config.py
src/core/performance/presets.py
```

## Required Dataclass

```python
from dataclasses import dataclass
from typing import Literal

PerformanceMode = Literal["fast", "balanced", "accurate"]

@dataclass(frozen=True)
class PerformanceConfig:
    mode: PerformanceMode = "balanced"
    max_analysis_size: int = 1600
    worker_count: int = 4
    use_cache: bool = True
    enable_face_analysis: bool = True
    enable_body_blur_analysis: bool = True
    enable_similarity_grouping: bool = True
    copy_files_after_culling: bool = True
    generate_thumbnails: bool = True
    force_reanalyze: bool = False
    cache_version: str = "2.1"
    scoring_version: str = "2.1"
```

## Presets

Implement:

```python
def get_performance_preset(mode: str) -> PerformanceConfig:
    ...
```

Preset rules:

### Fast

```text
mode = fast
max_analysis_size = 1024
worker_count = auto max 4
use_cache = true
enable_face_analysis = true but light
enable_body_blur_analysis = false or light
enable_similarity_grouping = true
copy_files_after_culling = false
generate_thumbnails = true
```

### Balanced

```text
mode = balanced
max_analysis_size = 1600
worker_count = auto max 4
use_cache = true
enable_face_analysis = true
enable_body_blur_analysis = true
enable_similarity_grouping = true
copy_files_after_culling = true
generate_thumbnails = true
```

### Accurate

```text
mode = accurate
max_analysis_size = 2400
worker_count = auto max 2
use_cache = true
enable_face_analysis = true
enable_body_blur_analysis = true
enable_similarity_grouping = true
copy_files_after_culling = true
generate_thumbnails = true
```

Do not use original size by default in Accurate mode. Allow user override later, but default should remain safe.

## Resource Limits

Create:

```text
src/core/performance/resource_limits.py
```

Implement:

```python
def resolve_worker_count(requested: int | str, mode: str) -> int:
    ...
```

Rules:
- `auto` allowed.
- auto should use CPU count but cap:
  - fast: max 4
  - balanced: max 4
  - accurate: max 2
- minimum 1.
- never use all CPU cores by default if that would freeze UI.

## Acceptance Criteria

- `PerformanceConfig` exists.
- Fast/Balanced/Accurate presets exist.
- Worker count is capped safely.
- Tests cover each preset.

---

# Phase 2 — Analysis Cache

Create:

```text
src/core/cache/cache_types.py
src/core/cache/cache_key.py
src/core/cache/analysis_cache.py
```

## Cache Storage

Use JSON cache for this implementation.

Recommended folder:

```text
output/
  .cullagrace_cache/
    analysis_cache.json
    thumbnails/
```

If the repository already has a cache folder convention, use the existing convention but keep these concepts.

## Cache Record

Implement dataclass:

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class AnalysisCacheRecord:
    photo_id: str
    path: str
    file_size: int
    mtime: float
    thumbnail_path: str | None = None
    phash: str | None = None
    technical: dict[str, Any] = field(default_factory=dict)
    face: dict[str, Any] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)
    final_score: float = 0.0
    cluster_id: str | None = None
    ai_status: str | None = None
    analysis_mode: str = "balanced"
    analysis_size: int = 1600
    cache_version: str = "2.1"
    scoring_version: str = "2.1"
```

## Cache Key

Implement:

```python
def build_cache_key(path: Path) -> str:
    ...
```

Rules:
- Stable across runs.
- Avoid unsafe filename characters.
- Prefer hash of absolute path or normalized path.

## Cache Validation

Implement:

```python
def is_cache_record_valid(
    record: AnalysisCacheRecord,
    path: Path,
    config: PerformanceConfig,
) -> bool:
    ...
```

Valid only if:
- path exists,
- file size matches,
- mtime matches,
- analysis mode matches,
- analysis size matches,
- cache version matches,
- scoring version matches,
- unless `config.force_reanalyze` is True.

## Cache Manager

Implement class:

```python
class AnalysisCache:
    def __init__(self, cache_dir: Path):
        ...

    def load(self) -> None:
        ...

    def save(self) -> None:
        ...

    def get(self, path: Path) -> AnalysisCacheRecord | None:
        ...

    def set(self, path: Path, record: AnalysisCacheRecord) -> None:
        ...

    def get_valid(self, path: Path, config: PerformanceConfig) -> AnalysisCacheRecord | None:
        ...

    def invalidate(self, path: Path) -> None:
        ...

    def clear(self) -> None:
        ...
```

## Acceptance Criteria

- Missing cache file returns empty cache.
- Cache saves and reloads.
- Changed file invalidates cache.
- Changed mode invalidates cache.
- Changed max analysis size invalidates cache.
- Force reanalyze ignores cache.
- Cache is JSON-readable for debugging.

---

# Phase 3 — Image Resizing for Analysis

Update or create image utility functions.

Suggested file:

```text
src/core/photo/image_loader.py
```

or:

```text
src/core/pipeline/photo_analyzer.py
```

## Required Helpers

```python
def load_image_for_analysis(path: Path, max_size: int) -> np.ndarray:
    ...
```

Rules:
- Load original file safely.
- Convert to consistent format expected by existing analyzers.
- Resize so longest side <= max_size.
- Preserve aspect ratio.
- If max_size <= 0, allow original, but do not use original by default.
- Return image array.
- Do not keep file handles open.
- Handle invalid files gracefully.

```python
def resize_for_analysis(image: np.ndarray, max_size: int) -> np.ndarray:
    ...
```

## Important

All analysis modules should receive the resized analysis image:
- technical score,
- face analyzer,
- body blur analyzer,
- pHash if currently image-based.

The original path must still be stored in `PhotoItem`.

## Acceptance Criteria

- A 6000x4000 image becomes longest side <= selected max size.
- Aspect ratio is preserved.
- Small images are not enlarged unnecessarily.
- Original image is not stored in `PhotoItem`.

---

# Phase 4 — Per-Photo Analyzer

Create:

```text
src/core/pipeline/photo_analyzer.py
```

## Purpose

Analyze a single photo using:
- cache if valid,
- resized analysis image if cache is invalid,
- existing technical/face/body/scoring modules,
- thumbnail generation if enabled.

## Required Function

```python
def analyze_photo(
    path: Path,
    config: PerformanceConfig,
    cache: AnalysisCache | None = None,
    output_dir: Path | None = None,
) -> PhotoItem:
    ...
```

Behavior:
1. Check valid cache unless disabled.
2. If cache valid:
   - rebuild `PhotoItem` from cache record.
   - do not reload image for analysis.
3. If cache invalid:
   - load resized image using `config.max_analysis_size`.
   - generate thumbnail if enabled and missing.
   - compute pHash.
   - compute technical score.
   - compute face score only if enabled.
   - compute body blur score only if enabled.
   - compute final score.
   - save result to cache.
4. Return `PhotoItem`.

## Cache → PhotoItem Mapping

Implement helper:

```python
def photo_item_from_cache_record(record: AnalysisCacheRecord) -> PhotoItem:
    ...
```

## PhotoItem → Cache Mapping

Implement helper:

```python
def cache_record_from_photo_item(
    item: PhotoItem,
    path: Path,
    config: PerformanceConfig,
) -> AnalysisCacheRecord:
    ...
```

## Feature Toggles

If `enable_face_analysis=False`:
- return neutral/default `FaceScore`,
- add reason: `Face analysis skipped by performance settings`.

If `enable_body_blur_analysis=False`:
- return neutral/default `BodyScore`,
- add reason: `Body blur analysis skipped by performance settings`.

If `generate_thumbnails=False`:
- do not generate new thumbnails,
- keep existing thumbnail path if available.

## Acceptance Criteria

- Cached photo does not recompute analysis.
- New photo is analyzed and cached.
- Face/body feature toggles work.
- Thumbnail generation respects config.
- `PhotoItem` contains path and scores, not image arrays.

---

# Phase 5 — Parallel Runner

Create:

```text
src/core/pipeline/parallel_runner.py
```

## Required Function

```python
def analyze_photos_batch(
    paths: list[Path],
    config: PerformanceConfig,
    cache: AnalysisCache | None,
    output_dir: Path | None,
    progress_callback: callable | None = None,
) -> list[PhotoItem]:
    ...
```

Use `ThreadPoolExecutor` first.

Rules:
- Use resolved worker count.
- Do not exceed configured max workers.
- If worker_count == 1, run sequentially.
- Catch per-photo errors and continue.
- Create a `PhotoItem` with rejected/review status or error metadata if a photo fails.
- Call progress callback after each photo.
- Preserve deterministic output order as much as possible.

## Why ThreadPool First

ThreadPool is simpler and safer in Streamlit. OpenCV/NumPy often release the GIL enough for this to help.

Do not use `ProcessPoolExecutor` yet unless explicitly necessary.

## Acceptance Criteria

- Sequential mode works.
- Parallel mode works.
- Errors in one photo do not stop the whole batch.
- Progress callback receives updates.
- Output count matches input count where possible.

---

# Phase 6 — Progress Events

Create:

```text
src/core/pipeline/progress_events.py
```

## Dataclass

```python
from dataclasses import dataclass

@dataclass
class ProgressEvent:
    stage: str
    current: int = 0
    total: int = 0
    message: str = ""
    filename: str | None = None
```

Stages:

```text
scanning
loading_cache
thumbnailing
analyzing
clustering
picking
exporting
writing_report
done
error
```

Use this in:
- culling engine,
- batch analyzer,
- Streamlit UI progress bar.

## Acceptance Criteria

- Progress events are emitted during major stages.
- Streamlit can display stage, current/total, and current filename.
- Long operations no longer feel frozen.

---

# Phase 7 — Update Culling Engine

Update:

```text
src/core/culling/culling_engine.py
```

Do not rewrite the entire engine if not needed. Integrate the performance architecture.

## Required Signature Update

Support:

```python
def run_culling_engine(
    input_dir: Path,
    output_dir: Path | None = None,
    mode: str = "balanced",
    recursive: bool = True,
    copy_files: bool | None = None,
    performance_config: PerformanceConfig | None = None,
    progress_callback: callable | None = None,
) -> CullingResult:
    ...
```

Behavior:
1. Build or receive `PerformanceConfig`.
2. If `copy_files` argument is not None, override `config.copy_files_after_culling`.
3. Scan image paths.
4. Load cache.
5. Analyze photos through `analyze_photos_batch`.
6. Run similarity clustering if enabled.
   - If disabled, each photo becomes its own cluster.
7. Run best photo picker.
8. Build reasons.
9. Save updated cache.
10. Write reports.
11. Export/copy files only if `config.copy_files_after_culling=True`.
12. Return `CullingResult`.

## Important

Similarity clustering should work with cached pHash values.

If cache records already contain pHash, do not recompute pHash.

## Acceptance Criteria

- Existing callers still work.
- New performance config works.
- Fast/Balanced/Accurate affect behavior.
- Copy OFF skips file copying but still generates report and review session can still use original paths.
- Cache is saved after analysis.
- Progress callback works.

---

# Phase 8 — Streamlit UI Settings

Update:

```text
app.py
```

Add a new section in sidebar or culling configuration panel:

```text
Performance Settings
```

Fields:

```text
Performance Mode:
- Fast
- Balanced
- Accurate

Use cache: checkbox
Force reanalyze: checkbox
Max analysis size: selectbox / slider
Worker count: selectbox
Enable face analysis: checkbox
Enable body blur analysis: checkbox
Enable similarity grouping: checkbox
Generate thumbnails: checkbox
Copy files after culling: checkbox
```

Suggested defaults:
- mode: Balanced
- use cache: ON
- force reanalyze: OFF
- max analysis size follows preset
- worker count: Auto
- face analysis: ON
- body blur analysis: ON
- similarity grouping: ON
- generate thumbnails: ON
- copy files after culling: ON or OFF depending current workflow

For V2 review workflow, recommend:

```text
Copy files after culling: OFF
```

because final export happens after human review.

But allow user to turn it ON.

## UI Explanation

Add help text:

```text
Fast mode is quicker but less precise for body/hand blur.
Balanced is recommended.
Accurate is slower but more detailed.
Original files are still used for review and final export.
```

## Progress UI

Display:
- current stage,
- progress bar,
- current file,
- total processed.

## Acceptance Criteria

- User can configure performance before culling.
- Settings are passed to `run_culling_engine`.
- Progress is visible.
- UI does not freeze without feedback.
- UI clearly explains speed vs accuracy tradeoff.

---

# Phase 9 — Export Behavior

Update exporter integration.

If `copy_files_after_culling=False`:
- do not create/copy into `Selected`, `Review`, `Rejected`,
- still write reports,
- still build review session from `PhotoItem.original_path`,
- UI should still show photos from original paths/thumbnails.

If `copy_files_after_culling=True`:
- preserve existing behavior.

## Acceptance Criteria

- Copy OFF works.
- Review workflow still works.
- Final decision export still works.
- Reports clearly state whether files were copied.

---

# Phase 10 — Reports

Update culling CSV/JSON report to include performance metadata:

```text
performance_mode
max_analysis_size
worker_count
used_cache
cache_hit
cache_key
analysis_size
face_analysis_enabled
body_blur_analysis_enabled
similarity_grouping_enabled
copy_files_after_culling
```

At minimum, JSON audit should include a `performance` section:

```json
{
  "performance": {
    "mode": "balanced",
    "max_analysis_size": 1600,
    "worker_count": 4,
    "use_cache": true,
    "copy_files_after_culling": false
  }
}
```

Each photo record should indicate:
- cache hit or miss,
- analysis size,
- thumbnail path.

## Acceptance Criteria

- Reports help debug speed and cache behavior.
- User can tell whether a result came from cache.

---

# Phase 11 — README Update

Update README with a new section:

```text
## Performance Modes and Cache
```

Explain:

```text
Fast:
- fastest
- smaller analysis image
- lighter body blur analysis
- recommended for large folders

Balanced:
- default
- good speed/accuracy tradeoff

Accurate:
- slower
- larger analysis image
- better detail
```

Explain cache:

```text
CullaGrace caches expensive analysis results.
If a photo has not changed, future culling runs reuse cached scores.
Cache invalidates when file size, modified time, analysis mode, analysis size, or cache version changes.
```

Explain memory:

```text
CullaGrace analyzes resized images to reduce RAM usage.
Original files are used for review and export.
```

Explain copy option:

```text
You can skip copying Selected/Review/Rejected during culling and export final Posts/Save/Delete later after review.
```

---

# Phase 12 — Tests

Add tests:

```text
tests/test_performance_config.py
tests/test_analysis_cache.py
tests/test_image_analysis_resize.py
tests/test_photo_analyzer_cache.py
tests/test_parallel_runner.py
tests/test_progress_events.py
tests/test_culling_engine_performance.py
tests/test_copy_files_option.py
```

## Required Test Coverage

### Performance Config
- Fast preset values.
- Balanced preset values.
- Accurate preset values.
- Worker count caps.

### Cache
- Missing cache loads empty.
- Save/reload works.
- Cache valid when file unchanged.
- Cache invalid when file size changes.
- Cache invalid when mtime changes.
- Cache invalid when mode changes.
- Cache invalid when max size changes.
- Force reanalyze bypasses cache.

### Resize
- Large image resized to max dimension.
- Aspect ratio preserved.
- Small image not enlarged.

### Photo Analyzer
- First run analyzes and writes cache.
- Second run uses cache.
- Face analysis disabled returns neutral face score.
- Body analysis disabled returns neutral body score.
- Generated PhotoItem has no image array.

### Parallel Runner
- Sequential and parallel runs both return expected count.
- Progress callback called.
- Error in one file does not stop all files.

### Culling Engine
- Existing API still works.
- Performance config accepted.
- Copy OFF skips AI bucket copy.
- Reports still generated.
- Review session can still use original paths.

### Reports
- Performance metadata exists.
- Cache hit/miss visible.

---

# Quality Gates

Run:

```bash
python -m compileall src
python -m pytest -q
```

Fix all errors.

Do not introduce tests that require:
- external network,
- external model downloads,
- large test files,
- GPU.

---

# Implementation Order

Follow this exact order:

## Step 1
Create performance config and presets.

## Step 2
Create cache types and JSON cache manager.

## Step 3
Add image resize/load helpers for analysis.

## Step 4
Create single-photo analyzer using cache.

## Step 5
Create parallel batch analyzer with progress callback.

## Step 6
Add progress event dataclass and wire it into analyzer.

## Step 7
Integrate performance config into culling engine.

## Step 8
Add copy-files-after-culling behavior.

## Step 9
Update Streamlit UI settings and progress display.

## Step 10
Update reports with performance/cache metadata.

## Step 11
Update README.

## Step 12
Add tests and fix failures.

---

# Acceptance Criteria

This update is complete only if:

1. User can select Fast/Balanced/Accurate mode.
2. User can configure cache, worker count, max analysis size, and feature toggles.
3. Engine analyzes resized images, not original images by default.
4. Original images are still used for detail review and export.
5. Cache prevents recomputation on unchanged files.
6. Cache invalidates correctly when file/mode/config changes.
7. Worker count is capped safely.
8. Progress is visible in Streamlit.
9. Copying Selected/Review/Rejected is optional.
10. Review workflow still works when copy is OFF.
11. Reports include performance/cache metadata.
12. README documents performance modes and cache.
13. All tests pass.
14. `python -m compileall src` passes.
15. No external model or network dependency is introduced.

---

# Safety Notes

- Never permanently delete original files.
- Never use original-resolution image for routine analysis unless user explicitly requests it.
- Never store image arrays in cache JSON.
- Never let a cache hit happen when file metadata or config changed.
- Never use all CPU cores by default.
- Never break V2 review workflow.
- Never break final export workflow.
- Never remove existing scoring/reasoning functionality.

---

# Deliverables From Codex Agent

When finished, report:

1. Files created.
2. Files modified.
3. Summary of architecture changes.
4. How performance modes work.
5. How cache works.
6. How resize analysis works.
7. How worker count/progress works.
8. How copy OFF behaves.
9. Test files added.
10. Exact command results:
    - `python -m compileall src`
    - `python -m pytest -q`
11. Remaining limitations or recommended future improvements.
