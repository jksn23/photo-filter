# CullaGrace Culling Engine

Dokumen ini merangkum arsitektur modular yang diadaptasi dari roadmap PhotoSort tanpa menyalin implementasi PhotoSort.

## Pipeline

```text
Import folder
Generate thumbnail cache
Analyze technical score
Group similar photos
Analyze face quality
Analyze body/subject blur
Calculate final score
Pick best photo per cluster
Copy selected/review/rejected
Write CSV + JSON audit report
```

## Modul Utama

- `src/core/photo`: data model `PhotoItem`, `PhotoScore`, `PhotoCluster`, `CullingResult`, metadata, loader.
- `src/core/cache`: thumbnail cache dan analysis cache berbasis path + size + modified time.
- `src/core/scoring`: technical, face, body, final, dan aesthetic scoring adapter.
- `src/core/similarity`: perceptual hash dan similarity clustering.
- `src/core/culling`: best-photo picker, culling engine, explainable reasons.
- `src/core/export`: export selected photos dan JSON report.

## Mode Culling

- `conservative`: menyimpan kandidat yang skornya dekat.
- `balanced`: default, memilih satu pemenang dan bisa menyimpan kandidat dekat pada cluster besar.
- `aggressive`: memilih satu pemenang per cluster.

## Alasan Keputusan

Setiap item dapat menyimpan `CullingReason` dengan `type`, `code`, `message`, dan `score`. UI dan JSON audit memakai alasan ini untuk menjelaskan kenapa foto dipilih atau ditolak.

