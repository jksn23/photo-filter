# Codex Agent Guide — CullaGrace V2 Review Workflow

## Repository

Work on this repository:

```text
https://github.com/jksn23/photo-filter
```

Project name: **CullaGrace**

You are implementing **CullaGrace V2**.

CullaGrace V1 already performs automatic photo culling and groups photos into AI recommendation buckets:

```text
Selected
Review
Rejected
```

CullaGrace V2 must add a **human review workflow** after culling, where the user can review photos from any AI bucket and assign a final human decision:

```text
Posts
Save
Delete
Undecided
```

Important distinction:

```text
Selected / Review / Rejected = AI recommendation status
Posts / Save / Delete / Undecided = final human decision
```

Do not replace the AI status with the final decision. They are separate fields.

---

# Main Goal

Implement a complete V2 review workflow:

```text
1. Run automatic culling
2. Show AI result buckets:
   - Selected
   - Review
   - Rejected

3. User opens one AI bucket
4. User reviews photos in that bucket
5. User assigns final decision:
   - Post
   - Save
   - Delete
   - Undecided

6. User can inspect score/reasons while deciding
7. User can compare similar cluster photos
8. User can track review progress
9. User can export final decision folders:
   - Posts
   - Save
   - Delete

10. System writes final decision reports:
   - final_decision_report.csv
   - final_decision_audit.json
```

The workflow must be safe, reversible, explainable, and not destructive by default.

---

# Critical Product Principle

Do **not** physically move or delete original photos immediately when the user clicks Post / Save / Delete.

Instead:

1. Store the final decision as metadata.
2. Allow the user to change the decision.
3. Only create `Posts`, `Save`, and `Delete` folders when the user clicks **Export Final**.
4. `Delete` means “candidate to delete”, not permanent deletion.

This is mandatory.

---

# Target User Workflow

## Step 1 — User runs culling

Existing V1 flow:

```text
Input folder
→ Run culling
→ AI buckets generated:
   Selected
   Review
   Rejected
```

Keep this working.

## Step 2 — User enters V2 review dashboard

After culling finishes, show:

```text
AI Recommendation
- Selected: 120 photos
- Review: 45 photos
- Rejected: 300 photos

Final Decision Progress
- Posts: 0
- Save: 0
- Delete: 0
- Undecided: 465
```

Buttons:

```text
Open Selected
Open Review
Open Rejected
Open All Photos
Export Final Decisions
```

## Step 3 — User opens one bucket

Example: User opens `Review`.

Show all photos in that AI bucket in a grid/list.

Each photo card should show:
- thumbnail,
- filename,
- AI status,
- final decision,
- final score,
- body blur warning if any,
- cluster ID,
- quick action buttons:
  - Post
  - Save
  - Delete
  - Undecided

## Step 4 — User opens one photo

Show detail view:

```text
Large preview
Filename
AI Status: Review
Final Decision: Undecided
Cluster ID: cluster_0007
Final Score: 72%
Technical Score
Face Score
Body Score
Reasons
```

Decision buttons:

```text
Post
Save
Delete
Undecided
Previous
Next
```

Keyboard shortcuts if possible:

```text
P = Post
S = Save
D = Delete
U = Undecided
ArrowRight = Next
ArrowLeft = Previous
```

Keyboard shortcuts are useful but optional for the first implementation if Streamlit limitations make it difficult.

## Step 5 — User compares similar cluster photos

In detail view, show:

```text
Similar photos in this cluster
- cluster winner
- review candidates
- rejected alternatives
```

This lets the user decide whether another photo in the same cluster should be Post/Save/Delete.

## Step 6 — User exports final

When user clicks **Export Final**, create:

```text
output/
  02_FINAL_DECISION/
    Posts/
    Save/
    Delete/

  reports/
    final_decision_report.csv
    final_decision_audit.json
```

Do not export `Undecided` into final folders by default. Include them in reports.

---

# Target Folder Structure

Add new modules under:

```text
src/core/review/
  __init__.py
  review_types.py
  decision_store.py
  review_session.py
  decision_exporter.py
  review_report_writer.py
```

Optional UI helper module:

```text
src/ui/
  __init__.py
  review_components.py
  result_adapters.py
```

If the project does not currently have `src/ui`, you may either:
- create it, or
- keep UI helpers inside `app.py` initially.

Prefer creating `src/ui` if it keeps `app.py` clean.

---

# Data Model Requirements

Create `src/core/review/review_types.py`.

Implement dataclasses and literals similar to:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

AIStatus = Literal["selected", "review", "rejected"]
FinalDecision = Literal["post", "save", "delete", "undecided"]

@dataclass
class ReviewDecision:
    photo_id: str
    filename: str
    original_path: str
    ai_status: AIStatus
    final_decision: FinalDecision = "undecided"
    decision_source: str = "manual"
    decision_updated_at: str | None = None
    notes: str = ""

@dataclass
class ReviewItem:
    photo_id: str
    filename: str
    original_path: Path
    ai_status: AIStatus
    final_decision: FinalDecision = "undecided"
    cluster_id: str | None = None
    is_cluster_winner: bool = False
    final_score: float = 0.0
    face_score: float = 0.0
    body_sharpness: float = 0.0
    body_blur_penalty: float = 0.0
    thumbnail_path: Path | None = None
    reasons: list[str] = field(default_factory=list)

@dataclass
class ReviewProgress:
    total: int = 0
    posts: int = 0
    save: int = 0
    delete: int = 0
    undecided: int = 0
    selected_total: int = 0
    review_total: int = 0
    rejected_total: int = 0

@dataclass
class ReviewSession:
    items: list[ReviewItem]
    decisions: dict[str, ReviewDecision] = field(default_factory=dict)
```

You may adjust the model to match existing `PhotoItem`, but keep the same concepts.

---

# Important Data Mapping

The V2 review system must be created from the V1 culling output.

Map V1 `PhotoItem` or report rows into V2 `ReviewItem`.

Mapping:

```text
PhotoItem.status              → ReviewItem.ai_status
PhotoItem.score.final_score   → ReviewItem.final_score
PhotoItem.cluster_id          → ReviewItem.cluster_id
PhotoItem.is_cluster_winner   → ReviewItem.is_cluster_winner
PhotoItem.score.face.*        → ReviewItem.face_score
PhotoItem.score.body.*        → ReviewItem.body_sharpness / body_blur_penalty
PhotoItem.score.reasons       → ReviewItem.reasons
PhotoItem.path                → ReviewItem.original_path
PhotoItem.thumbnail_path      → ReviewItem.thumbnail_path if available
```

If the culling output is currently a dictionary/list in `app.py`, create an adapter to convert it into `ReviewItem`.

---

# Decision Store

Create `src/core/review/decision_store.py`.

Purpose: persist user decisions so review progress is not lost.

Required functions:

```python
load_decisions(path: Path) -> dict[str, ReviewDecision]

save_decisions(
    decisions: dict[str, ReviewDecision],
    path: Path,
) -> None

set_decision(
    decisions: dict[str, ReviewDecision],
    item: ReviewItem,
    decision: FinalDecision,
    notes: str = "",
) -> ReviewDecision

clear_decision(
    decisions: dict[str, ReviewDecision],
    photo_id: str,
) -> None
```

Storage file:

```text
output/reports/final_decisions.json
```

Rules:
- If no decision exists for a photo, default is `undecided`.
- Use `photo_id` as key.
- Save after each user action if possible.
- Decisions must be reloadable across app refreshes.
- Store timestamp in ISO format.
- Never fail if file does not exist; return empty dict.

JSON format example:

```json
{
  "IMG_0012.jpg": {
    "photo_id": "IMG_0012.jpg",
    "filename": "IMG_0012.jpg",
    "original_path": "/path/to/IMG_0012.jpg",
    "ai_status": "review",
    "final_decision": "post",
    "decision_source": "manual",
    "decision_updated_at": "2026-05-19T12:00:00",
    "notes": ""
  }
}
```

---

# Review Session

Create `src/core/review/review_session.py`.

Required functions:

```python
build_review_items_from_photo_items(photo_items: list[PhotoItem]) -> list[ReviewItem]

build_review_session(
    photo_items: list[PhotoItem],
    decisions_path: Path,
) -> ReviewSession

get_items_by_ai_status(
    session: ReviewSession,
    ai_status: AIStatus | str,
) -> list[ReviewItem]

get_items_by_final_decision(
    session: ReviewSession,
    decision: FinalDecision | str,
) -> list[ReviewItem]

get_cluster_items(
    session: ReviewSession,
    cluster_id: str,
) -> list[ReviewItem]

get_review_progress(session: ReviewSession) -> ReviewProgress

apply_decision_to_item(
    session: ReviewSession,
    item: ReviewItem,
    decision: FinalDecision,
    decisions_path: Path,
) -> ReviewDecision
```

Behavior:
- Merge persisted decisions into `ReviewItem.final_decision`.
- If decision exists, show it.
- If no decision exists, `undecided`.
- Review progress must count all photos.
- AI bucket progress should also be available.

Optional:
- `get_next_item`
- `get_previous_item`
- `get_undecided_items`

---

# Decision Exporter

Create `src/core/review/decision_exporter.py`.

Required function:

```python
export_final_decisions(
    session: ReviewSession,
    output_dir: Path,
    copy_files: bool = True,
    include_undecided: bool = False,
) -> dict[str, int]
```

Required output folders:

```text
output/
  02_FINAL_DECISION/
    Posts/
    Save/
    Delete/
```

If `include_undecided=True`, optionally create:

```text
Undecided/
```

Rules:
- Copy files by default.
- Do not move files.
- Do not delete source files.
- Skip missing files safely and report them.
- Preserve original filename.
- If duplicate filenames collide, add suffix:
  - `IMG_001.jpg`
  - `IMG_001_1.jpg`
  - `IMG_001_2.jpg`

Return counts:

```python
{
  "post": 12,
  "save": 30,
  "delete": 100,
  "undecided": 5,
  "missing": 0,
}
```

---

# Review Report Writer

Create `src/core/review/review_report_writer.py`.

Required functions:

```python
write_final_decision_csv(session: ReviewSession, output_dir: Path) -> Path

write_final_decision_json(session: ReviewSession, output_dir: Path) -> Path
```

CSV columns:

```text
photo_id
filename
original_path
ai_status
final_decision
cluster_id
is_cluster_winner
final_score
face_score
body_sharpness
body_blur_penalty
decision_updated_at
decision_source
reasons
notes
```

JSON should include:

```json
{
  "summary": {
    "total": 465,
    "posts": 30,
    "save": 120,
    "delete": 250,
    "undecided": 65,
    "selected_total": 120,
    "review_total": 45,
    "rejected_total": 300
  },
  "items": [],
  "clusters": []
}
```

Cluster JSON should group items by `cluster_id` and include:
- winner,
- all items,
- final decisions.

---

# Streamlit UI V2 Requirements

Update `app.py` or create UI helper modules.

The UI must support two stages:

```text
Stage 1: Auto Culling
Stage 2: Human Review
```

---

## Stage 1 — Auto Culling

Keep existing V1 functionality.

After culling completes, store culling result in `st.session_state`.

Suggested keys:

```python
st.session_state["culling_result"] = result
st.session_state["review_session"] = session
st.session_state["current_review_bucket"] = "review"
st.session_state["current_photo_id"] = None
```

---

## Stage 2 — Review Dashboard

Add a section/page:

```text
Final Review Workflow
```

Show:
- AI bucket counts:
  - Selected
  - Review
  - Rejected
- Final decision counts:
  - Posts
  - Save
  - Delete
  - Undecided
- progress bar:
  - decided / total

Buttons:
- Open Selected
- Open Review
- Open Rejected
- Open All
- Export Final

---

## Bucket View

When a bucket is selected, show items from that AI bucket.

For each item card:
- image thumbnail,
- filename,
- AI status,
- final decision badge,
- score,
- cluster ID,
- warnings:
  - body blur penalty high,
  - low face score,
  - low global score if available,
- buttons:
  - Post
  - Save
  - Delete
  - Undecided
  - Open Detail

When a button is clicked:
- update session decision,
- persist decision to JSON,
- refresh progress.

---

## Detail View

When user opens detail:

Show:
- large image,
- filename,
- AI status,
- final decision,
- final score,
- face score,
- body sharpness,
- body blur penalty,
- cluster ID,
- reasons,
- decision buttons,
- previous/next navigation.

Also show:

```text
Similar photos in this cluster
```

For each cluster item:
- thumbnail,
- filename,
- AI status,
- final decision,
- final score,
- body blur penalty,
- quick decision buttons.

---

## Export Final Button

When user clicks Export Final:

1. Call `export_final_decisions`.
2. Call `write_final_decision_csv`.
3. Call `write_final_decision_json`.
4. Show result counts.
5. Show output path.

Warning before export:

```text
Export copies photos into Posts/Save/Delete folders. It does not delete original files.
```

---

# Recommended UI Layout

Use tabs:

```text
[Auto Culling]
[Review Dashboard]
[Selected]
[Review]
[Rejected]
[Clusters]
[Final Export]
```

If this is too much for one implementation, use:
- Auto Culling section,
- Review Dashboard section,
- dynamic bucket selector.

Keep UI simple and stable.

---

# Final Folder Structure

When culling and final export are complete, output should look like:

```text
output/
  01_AI_CULLING/
    Selected/
    Review/
    Rejected/

  02_FINAL_DECISION/
    Posts/
    Save/
    Delete/

  reports/
    culling_report.csv
    culling_audit.json
    final_decisions.json
    final_decision_report.csv
    final_decision_audit.json
```

If existing V1 currently exports directly to:

```text
output/Selected
output/Review
output/Rejected
```

Do not break existing behavior unless you migrate cleanly.

Preferred:
- keep backward compatibility,
- but document V2 structure.

---

# Backward Compatibility

The existing app must still work if user only wants auto culling.

V2 review should not be mandatory.

Rules:
- User can run culling and stop there.
- User can continue to review.
- Existing reports still generated.
- Existing Selected/Review/Rejected exports still work.
- New final decision reports are added, not replacing old reports.

---

# Testing Requirements

Add tests for the new review system.

Suggested tests:

```text
tests/test_review_types.py
tests/test_decision_store.py
tests/test_review_session.py
tests/test_decision_exporter.py
tests/test_review_report_writer.py
tests/test_v2_review_workflow.py
```

---

## Test: Decision Store

Cover:
- load missing decision file returns empty dict,
- save and reload decisions,
- set decision updates timestamp,
- clear decision removes decision.

---

## Test: Review Session

Cover:
- build review items from fake PhotoItem objects,
- persisted decision is merged into item,
- get items by AI status works,
- get items by final decision works,
- get cluster items works,
- progress counts are correct.

---

## Test: Decision Exporter

Cover:
- exports post/save/delete files into correct folders,
- does not move/delete original files,
- handles duplicate filenames,
- skips missing files safely.

---

## Test: Review Report Writer

Cover:
- CSV contains required columns,
- JSON contains summary/items/clusters,
- body blur fields are included,
- final decision is included.

---

## Test: End-to-End V2 Workflow

Create temporary sample image files and fake PhotoItems.

Flow:
1. Build review session.
2. Set decisions:
   - one post,
   - one save,
   - one delete,
   - one undecided.
3. Export final.
4. Write reports.
5. Assert folder counts and report contents.

---

# Quality Gates

Before finishing, run:

```bash
python -m compileall src
python -m pytest -q
```

If the repo has formatting/linting tools, run them too. Do not introduce unnecessary tools.

---

# README Update

Update `README.md` with a new section:

```text
## CullaGrace V2 Review Workflow
```

Explain:

```text
AI recommendation buckets:
- Selected
- Review
- Rejected

Final human decisions:
- Posts
- Save
- Delete
- Undecided
```

Document workflow:

```text
1. Run culling.
2. Review AI buckets.
3. Assign final decisions.
4. Export final folders.
```

Document safety:

```text
CullaGrace does not permanently delete source photos. The Delete decision marks photos as candidates for deletion and exports them into a Delete folder.
```

Document output:

```text
02_FINAL_DECISION/
  Posts/
  Save/
  Delete/
```

Document reports:

```text
final_decisions.json
final_decision_report.csv
final_decision_audit.json
```

---

# Implementation Order

Follow this exact order to avoid confusion:

## Phase 1 — Data Models

Create:
- `review_types.py`

Add:
- `FinalDecision`
- `ReviewDecision`
- `ReviewItem`
- `ReviewProgress`
- `ReviewSession`

Run basic tests.

---

## Phase 2 — Decision Store

Create:
- `decision_store.py`

Implement:
- load,
- save,
- set,
- clear.

Run decision store tests.

---

## Phase 3 — Review Session

Create:
- `review_session.py`

Implement:
- mapping from PhotoItem to ReviewItem,
- merge persisted decisions,
- get by AI status,
- get by final decision,
- get cluster items,
- progress,
- apply decision.

Run review session tests.

---

## Phase 4 — Final Decision Exporter

Create:
- `decision_exporter.py`

Implement:
- export Posts/Save/Delete,
- copy-only behavior,
- duplicate filename handling,
- missing file safety.

Run exporter tests.

---

## Phase 5 — Final Decision Reports

Create:
- `review_report_writer.py`

Implement:
- CSV report,
- JSON audit,
- cluster grouping.

Run report tests.

---

## Phase 6 — Streamlit Integration

Update UI:
- store culling results in session state,
- build review session after culling,
- show review dashboard,
- show bucket views,
- show photo detail,
- show cluster photos,
- support decision buttons,
- support export final.

Keep UI simple first. Do not over-engineer.

---

## Phase 7 — README Update

Add V2 documentation.

---

## Phase 8 — Full Test and Compile

Run:
- `python -m compileall src`
- `python -m pytest -q`

Fix all failures.

---

# Acceptance Criteria

The V2 implementation is complete only if all of these are true:

1. User can run existing auto culling.
2. User can see AI buckets Selected/Review/Rejected.
3. User can open each AI bucket.
4. User can assign Post/Save/Delete/Undecided to any photo.
5. Final decision is persisted to JSON.
6. Decision survives app refresh/reload.
7. User can change a previous decision.
8. User can see review progress.
9. User can inspect score/reasons while deciding.
10. User can see cluster-related photos.
11. User can export final decisions.
12. Export creates Posts/Save/Delete folders.
13. Export copies files and does not delete originals.
14. Final CSV report is generated.
15. Final JSON audit is generated.
16. Tests cover review workflow.
17. `python -m compileall src` passes.
18. `python -m pytest -q` passes.
19. README documents V2 clearly.
20. UI makes clear that Delete is not permanent deletion.

---

# Nice-to-Have Features

Only implement these if the main requirements are complete:

1. Undo last decision.
2. Keyboard shortcuts:
   - P, S, D, U,
   - previous/next.
3. Filter by:
   - undecided only,
   - high body blur,
   - low score,
   - cluster ID.
4. Sort by:
   - final score descending,
   - body blur penalty descending,
   - filename.
5. Bulk actions:
   - mark all selected as Save,
   - mark all rejected as Delete,
   - mark all review as Undecided.

If implementing bulk actions, add a confirmation warning.

---

# Important Safety Notes

- Never permanently delete files.
- Never overwrite files without collision handling.
- Never assume AI status equals final decision.
- Never hide Rejected photos from review.
- Never force all photos to be decided before export.
- Never make final decision irreversible.
- Never download external models during tests.

---

# Deliverables From Codex Agent

When finished, report:

1. Summary of V2 implementation.
2. Files created.
3. Files modified.
4. New review workflow behavior.
5. How decisions are stored.
6. How final export works.
7. Test files added.
8. Exact test results:
   - `python -m compileall src`
   - `python -m pytest -q`
9. Remaining limitations or future improvements.
