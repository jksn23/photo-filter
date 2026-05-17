"""Streamlit UI for CullaGrace / Church Photo Culling v1."""

from pathlib import Path
import os
import platform
import subprocess

import pandas as pd
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from src.config import (
    DEFAULT_BLUR_THRESHOLD,
    DEFAULT_DUPLICATE_HASH_THRESHOLD,
    DEFAULT_OVEREXPOSED_THRESHOLD,
    DEFAULT_REVIEW_SCORE_MIN,
    DEFAULT_SELECTED_SCORE_MIN,
    DEFAULT_UNDEREXPOSED_THRESHOLD,
)
from src.culling_pipeline import run_culling_pipeline
from src.file_manager import default_output_folder, normalize_user_path
from src.image_loader import list_image_files
from src.report_generator import results_to_dataframe


APP_NAME = "CullaGrace"
APP_VERSION = "Church Photo Culling v1"
TAGLINE = "Sortir foto pelayanan lebih cepat, rapi, dan bermakna."


def init_state() -> None:
    """Initialize Streamlit session state defaults."""
    defaults = {
        "results_df": pd.DataFrame(),
        "summary": {},
        "process_logs": [],
        "processing_status": "Idle",
        "last_input_folder": "",
        "last_output_folder": "",
        "last_report_path": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def inject_styles() -> None:
    """Apply CullaGrace brand styling on top of Streamlit defaults."""
    st.markdown(
        """
        <style>
        :root {
            --primary: #2563EB;
            --primary-hover: #1D4ED8;
            --gold: #F59E0B;
            --success: #16A34A;
            --danger: #DC2626;
            --info: #0891B2;
            --bg: #F8FAFC;
            --surface: #FFFFFF;
            --border: #E2E8F0;
            --text: #0F172A;
            --muted: #475569;
        }
        html, body, [class*="css"] {
            font-family: "Inter", "Segoe UI", Roboto, Arial, sans-serif;
        }
        .stApp {
            background: var(--bg);
            color: var(--text);
        }
        section[data-testid="stSidebar"] {
            background: var(--surface);
            border-right: 1px solid var(--border);
        }
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
            color: var(--text) !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] div[data-testid="stCheckbox"] p {
            color: var(--text) !important;
            font-weight: 600;
        }
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea {
            background: #FFFFFF !important;
            color: var(--text) !important;
            border-color: #CBD5E1 !important;
            caret-color: var(--primary) !important;
        }
        section[data-testid="stSidebar"] input::placeholder,
        section[data-testid="stSidebar"] textarea::placeholder {
            color: #64748B !important;
            opacity: 1 !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="input"],
        section[data-testid="stSidebar"] div[data-baseweb="input"] > div {
            background: #FFFFFF !important;
            color: var(--text) !important;
            border-color: #CBD5E1 !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="input"]:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button {
            background: #F8FAFC !important;
            color: var(--text) !important;
            border-color: #CBD5E1 !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label span {
            color: var(--text) !important;
        }
        button[data-testid="stBaseButton-primary"],
        button[data-testid="baseButton-primary"],
        div.stButton > button[kind="primary"] {
            background: var(--primary) !important;
            color: #FFFFFF !important;
            border-color: var(--primary) !important;
        }
        button[data-testid="stBaseButton-primary"]:hover,
        button[data-testid="baseButton-primary"]:hover,
        div.stButton > button[kind="primary"]:hover {
            background: var(--primary-hover) !important;
            border-color: var(--primary-hover) !important;
        }
        button[data-testid="stBaseButton-secondary"],
        button[data-testid="baseButton-secondary"],
        div.stButton > button[kind="secondary"] {
            background: #FFFFFF !important;
            color: var(--primary) !important;
            border-color: var(--border) !important;
        }
        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 0 14px 0;
        }
        .brand-icon {
            width: 36px;
            height: 36px;
            border-radius: 12px;
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary);
            font-weight: 800;
        }
        .brand-title {
            font-size: 20px;
            line-height: 1.1;
            font-weight: 700;
            color: var(--text);
        }
        .brand-subtitle {
            font-size: 12px;
            color: var(--muted);
        }
        .hero-panel, .info-card, .stat-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
            padding: 20px;
        }
        .hero-panel {
            margin-bottom: 18px;
        }
        .hero-title {
            font-size: 28px;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 4px;
        }
        .hero-copy {
            color: var(--muted);
            font-size: 14px;
        }
        .safe-note {
            background: #EFF6FF;
            color: #1E40AF;
            border: 1px solid #BFDBFE;
            border-radius: 12px;
            padding: 12px 14px;
            font-size: 14px;
            margin-top: 14px;
        }
        .card-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .card-copy {
            font-size: 14px;
            color: var(--muted);
            margin: 0;
        }
        .stat-value {
            font-size: 30px;
            font-weight: 700;
            color: var(--text);
            line-height: 1;
        }
        .stat-label {
            margin-top: 8px;
            color: var(--muted);
            font-size: 13px;
        }
        .status-selected {
            background: #DCFCE7;
            color: #166534;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 700;
        }
        .status-review {
            background: #FEF3C7;
            color: #92400E;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 700;
        }
        .status-rejected, .status-error {
            background: #FEE2E2;
            color: #991B1B;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 700;
        }
        .small-muted {
            color: var(--muted);
            font-size: 13px;
        }
        div.stButton > button:first-child,
        div.stDownloadButton > button:first-child {
            border-radius: 10px;
            min-height: 40px;
            font-weight: 700;
        }
        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_controls() -> dict:
    """Render sidebar controls and return the selected configuration."""
    st.sidebar.markdown(
        f"""
        <div class="brand-lockup">
            <div class="brand-icon">CG</div>
            <div>
                <div class="brand-title">{APP_NAME}</div>
                <div class="brand-subtitle">{APP_VERSION}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    input_folder = st.sidebar.text_input(
        "Folder Foto Input",
        key="input_folder",
        placeholder=r"Contoh: D:\Dokumentasi Gereja\2026-05-17 Ibadah Minggu",
    )
    output_folder = st.sidebar.text_input(
        "Folder Output",
        key="output_folder",
        placeholder="Kosongkan untuk membuat folder _CULLED otomatis",
    )
    try:
        output_preview = (
            str(normalize_user_path(output_folder))
            if output_folder.strip()
            else default_output_folder(input_folder)
            if input_folder.strip()
            else "-"
        )
        st.sidebar.caption(f"Hasil akan disimpan di: {output_preview}")
    except Exception:
        st.sidebar.caption("Hasil akan disimpan setelah folder input valid.")

    st.sidebar.markdown("### Pengaturan Threshold")
    blur_threshold = st.sidebar.number_input(
        "Blur Threshold",
        min_value=0,
        max_value=1000,
        value=DEFAULT_BLUR_THRESHOLD,
        step=5,
        key="blur_threshold",
    )
    under_threshold = st.sidebar.number_input(
        "Underexposed Threshold",
        min_value=0,
        max_value=255,
        value=DEFAULT_UNDEREXPOSED_THRESHOLD,
        step=1,
        key="under_threshold",
    )
    over_threshold = st.sidebar.number_input(
        "Overexposed Threshold",
        min_value=0,
        max_value=255,
        value=DEFAULT_OVEREXPOSED_THRESHOLD,
        step=1,
        key="over_threshold",
    )
    duplicate_threshold = st.sidebar.number_input(
        "Duplicate Hash Threshold",
        min_value=0,
        max_value=32,
        value=DEFAULT_DUPLICATE_HASH_THRESHOLD,
        step=1,
        key="duplicate_threshold",
    )

    st.sidebar.markdown("### Pengaturan Klasifikasi")
    culling_mode = st.sidebar.selectbox(
        "Mode Culling",
        ["conservative", "balanced", "aggressive"],
        index=1,
        key="culling_mode",
    )
    selected_min = st.sidebar.number_input(
        "Selected Score Minimum",
        min_value=0,
        max_value=150,
        value=DEFAULT_SELECTED_SCORE_MIN,
        step=1,
        key="selected_min",
    )
    review_min = st.sidebar.number_input(
        "Review Score Minimum",
        min_value=0,
        max_value=150,
        value=DEFAULT_REVIEW_SCORE_MIN,
        step=1,
        key="review_min",
    )

    st.sidebar.markdown("### Opsi Proses")
    copy_files = st.sidebar.checkbox("Salin file ke folder output", value=True, key="copy_files")
    create_csv = st.sidebar.checkbox("Buat laporan CSV", value=True, key="create_csv")
    use_faces = st.sidebar.checkbox("Gunakan deteksi wajah", value=True, key="use_faces")
    use_duplicates = st.sidebar.checkbox("Gunakan deteksi duplikat", value=True, key="use_duplicates")
    use_human_aware = st.sidebar.checkbox(
        "Enable Human-Aware Blur Detection",
        value=True,
        key="use_human_aware",
    )
    person_confidence = st.sidebar.number_input(
        "Person Detection Confidence",
        min_value=0.05,
        max_value=0.95,
        value=0.35,
        step=0.05,
        key="person_confidence",
    )
    person_patch_blur_threshold = st.sidebar.number_input(
        "Person Patch Blur Threshold",
        min_value=1.0,
        max_value=300.0,
        value=75.0,
        step=5.0,
        key="person_patch_blur_threshold",
    )
    localized_blur_patch_ratio = st.sidebar.number_input(
        "Localized Blur Patch Ratio",
        min_value=0.05,
        max_value=1.0,
        value=0.25,
        step=0.05,
        key="localized_blur_patch_ratio",
    )

    start_clicked = st.sidebar.button("Mulai Culling", type="primary", use_container_width=True)
    reset_clicked = st.sidebar.button("Reset Pengaturan", use_container_width=True)
    if reset_clicked:
        for key in [
            "blur_threshold",
            "under_threshold",
            "over_threshold",
            "duplicate_threshold",
            "selected_min",
            "review_min",
            "copy_files",
            "create_csv",
            "use_faces",
            "use_duplicates",
            "use_human_aware",
            "person_confidence",
            "person_patch_blur_threshold",
            "localized_blur_patch_ratio",
            "culling_mode",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    return {
        "input_folder": input_folder,
        "output_folder": output_folder,
        "blur_threshold": blur_threshold,
        "underexposed_threshold": under_threshold,
        "overexposed_threshold": over_threshold,
        "duplicate_hash_threshold": duplicate_threshold,
        "selected_score_min": selected_min,
        "review_score_min": review_min,
        "culling_mode": culling_mode,
        "copy_files": copy_files,
        "create_csv": create_csv,
        "use_face_detection": use_faces,
        "use_duplicate_detection": use_duplicates,
        "use_human_aware_detection": use_human_aware,
        "person_detection_confidence": person_confidence,
        "person_patch_blur_threshold": person_patch_blur_threshold,
        "localized_blur_patch_ratio": localized_blur_patch_ratio,
        "start_clicked": start_clicked,
    }


def render_header() -> None:
    """Render the main app header."""
    status = st.session_state.get("processing_status", "Idle")
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-title">{APP_NAME}</div>
            <div class="hero-copy">{APP_VERSION}. {TAGLINE}</div>
            <div class="safe-note">
                Aplikasi ini tidak menghapus file asli. Semua hasil akan disalin ke folder output.
                Status proses: <strong>{status}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_folder_status(input_folder: str) -> tuple[str, list[str], str]:
    """Return status, images, and display message for an input folder."""
    if not input_folder:
        return "warning", [], "Folder input belum dipilih."

    path = normalize_user_path(input_folder)
    if path is None:
        return "warning", [], "Folder input belum dipilih."
    if not path.exists() or not path.is_dir():
        return "error", [], "Folder input tidak ditemukan."

    try:
        image_files = list_image_files(input_folder)
    except Exception as exc:
        return "error", [], str(exc)

    if not image_files:
        return "warning", [], "Tidak ada file foto JPG, JPEG, atau PNG di folder ini."

    return "success", image_files, "Folder input valid."


def render_dashboard(config: dict) -> None:
    """Render Dashboard tab content."""
    st.subheader("Dashboard")
    cards = [
        ("Blur Detection", "Mendeteksi foto yang tidak tajam atau bergoyang."),
        ("Exposure Detection", "Mendeteksi foto terlalu gelap atau terlalu terang."),
        ("Duplicate Detection", "Mengelompokkan foto yang mirip dan memilih kandidat terbaik."),
        ("Face Detection", "Mendeteksi jumlah wajah sebagai indikator foto dokumentasi."),
    ]
    columns = st.columns(4)
    for column, (title, copy) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="card-title">{title}</div>
                    <p class="card-copy">{copy}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Status Folder Input")
    st.info(
        "Sistem sekarang membandingkan foto mirip berdasarkan kualitas subjek manusia. "
        "Jika ada foto mirip yang lebih bersih dan tubuh manusianya lebih tajam, foto tersebut akan diprioritaskan."
    )
    status, image_files, message = get_folder_status(config["input_folder"])
    if status == "success":
        st.success(message)
        extensions = sorted({Path(path).suffix.lower() for path in image_files})
        st.write(f"Jumlah file gambar ditemukan: **{len(image_files)}**")
        st.write(f"Ekstensi ditemukan: **{', '.join(extensions)}**")
        st.info("Proses analisis berjalan lokal di laptop ini tanpa upload ke cloud.")
    elif status == "warning":
        st.warning(message)
    else:
        st.error("Folder input tidak ditemukan. Periksa kembali path folder foto Anda.")

    st.markdown("### Workflow Singkat")
    st.markdown(
        """
        1. Pilih folder foto.
        2. Atur threshold jika diperlukan.
        3. Klik Mulai Culling.
        4. Review folder Selected dan Review.
        5. Upload foto pilihan ke media sosial.
        """
    )


def render_process_panel(config: dict) -> None:
    """Render Culling Process tab content and execute pipeline when requested."""
    st.subheader("Culling Process")
    input_folder = config["input_folder"]
    status, image_files, message = get_folder_status(input_folder)
    output_display = (
        str(normalize_user_path(config["output_folder"]))
        if config["output_folder"].strip()
        else default_output_folder(input_folder)
        if input_folder
        else "Akan dibuat otomatis setelah folder input valid"
    )

    st.markdown("### Konfirmasi Sebelum Proses")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Folder input: `{input_folder or '-'}`")
        st.write(f"Folder output: `{output_display}`")
        st.write(f"Jumlah foto: **{len(image_files)}**")
    with col2:
        st.write(f"Blur threshold: **{config['blur_threshold']}**")
        st.write(
            f"Exposure threshold: **{config['underexposed_threshold']} - {config['overexposed_threshold']}**"
        )
        st.write(f"Duplicate threshold: **{config['duplicate_hash_threshold']}**")
        st.write(
            f"Skor: Selected >= **{config['selected_score_min']}**, Review >= **{config['review_score_min']}**"
        )

    if status != "success":
        if status == "warning":
            st.warning(message)
        else:
            st.error("Folder input tidak ditemukan. Periksa kembali path folder foto Anda.")

    progress_bar = st.progress(0)
    status_text = st.empty()
    log_area = st.empty()

    def log_callback(message: str) -> None:
        st.session_state.process_logs.append(message)
        st.session_state.process_logs = st.session_state.process_logs[-20:]
        log_area.code("\n".join(st.session_state.process_logs), language="text")

    def progress_callback(current: int, total: int, message: str) -> None:
        progress_bar.progress(0 if total == 0 else min(current / total, 1.0))
        status_text.write(message)

    if config["start_clicked"]:
        if status != "success":
            st.error("Proses belum bisa dimulai karena folder input belum valid.")
            return

        st.session_state.process_logs = []
        st.session_state.processing_status = "Processing"
        try:
            results, summary = run_culling_pipeline(
                input_folder=input_folder,
                output_folder=config["output_folder"],
                config=config,
                progress_callback=progress_callback,
                log_callback=log_callback,
            )
            df = results_to_dataframe(results)
            st.session_state.results_df = df
            st.session_state.summary = summary
            st.session_state.last_input_folder = input_folder
            st.session_state.last_output_folder = summary.get("output_folder", "")
            st.session_state.last_report_path = summary.get("report_path", "") or ""
            st.session_state.processing_status = "Completed"
            st.success("Culling selesai. Foto telah dikelompokkan ke folder Selected, Review, dan Rejected.")
            st.info(f"Folder output: {summary.get('output_folder', '-')}")
            if summary.get("report_path"):
                st.info(f"Laporan CSV: {summary.get('report_path')}")
            if int(summary.get("errors", 0)) > 0:
                st.warning("Beberapa file tidak dapat dibaca atau disalin. Detailnya dicatat dalam laporan.")
        except ValueError as exc:
            st.session_state.processing_status = "Idle"
            st.error(str(exc))
        except Exception as exc:
            st.session_state.processing_status = "Idle"
            st.error(f"Terjadi kendala saat proses culling: {exc}")
    else:
        if st.session_state.process_logs:
            log_area.code("\n".join(st.session_state.process_logs[-20:]), language="text")
        else:
            st.markdown(
                '<p class="small-muted">Log proses akan muncul di sini setelah Mulai Culling ditekan.</p>',
                unsafe_allow_html=True,
            )


def open_local_path(path: str) -> tuple[bool, str]:
    """Open a local path with the host operating system file manager."""
    if not path:
        return False, "Path belum tersedia."

    try:
        system_name = platform.system()
        if system_name == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        elif system_name == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True, "Path dibuka."
    except Exception as exc:
        return False, f"Tidak dapat membuka path otomatis: {exc}"


def render_stat_grid(summary: dict) -> None:
    """Render top result statistics."""
    metrics = [
        ("Total Processed", summary.get("total_processed", 0)),
        ("Selected", summary.get("selected", 0)),
        ("Review", summary.get("review", 0)),
        ("Rejected", summary.get("rejected", 0)),
        ("Blur Photos", summary.get("blur_photos", 0)),
        ("Underexposed Photos", summary.get("underexposed_photos", 0)),
        ("Overexposed Photos", summary.get("overexposed_photos", 0)),
        ("Duplicate Groups", summary.get("duplicate_groups", 0)),
        ("Localized Person Blur", summary.get("localized_person_blur_photos", 0)),
    ]
    for row in range(0, len(metrics), 4):
        columns = st.columns(4)
        for column, (label, value) in zip(columns, metrics[row : row + 4]):
            column.metric(label, value)


def render_results() -> None:
    """Render Results tab content."""
    st.subheader("Results")
    df = st.session_state.get("results_df", pd.DataFrame())
    summary = st.session_state.get("summary", {})

    if df.empty:
        st.info("Belum ada foto yang dianalisis. Pilih folder dokumentasi terlebih dahulu untuk mulai.")
        return

    render_stat_grid(summary)
    st.markdown("### Filter Hasil")
    f1, f2, f3, f4 = st.columns(4)
    status_filter = f1.multiselect(
        "Output Status",
        sorted(df["output_status"].dropna().unique()),
        default=sorted(df["output_status"].dropna().unique()),
    )
    exposure_filter = f2.multiselect(
        "Exposure Status",
        sorted(df["exposure_status"].dropna().unique()),
        default=sorted(df["exposure_status"].dropna().unique()),
    )
    blur_filter = f3.selectbox("Blur", ["Semua", "Blur", "Tidak Blur"])
    face_filter = f4.selectbox("Wajah", ["Semua", "Ada Wajah", "Tanpa Wajah"])

    filtered = df.copy()
    if status_filter:
        filtered = filtered[filtered["output_status"].isin(status_filter)]
    if exposure_filter:
        filtered = filtered[filtered["exposure_status"].isin(exposure_filter)]
    if blur_filter == "Blur":
        filtered = filtered[filtered["is_blur"] == True]
    elif blur_filter == "Tidak Blur":
        filtered = filtered[filtered["is_blur"] == False]
    if face_filter == "Ada Wajah":
        filtered = filtered[filtered["has_face"] == True]
    elif face_filter == "Tanpa Wajah":
        filtered = filtered[filtered["has_face"] == False]

    search = st.text_input("Cari nama file", placeholder="Contoh: IMG_1023")
    if search:
        filtered = filtered[filtered["filename"].str.contains(search, case=False, na=False)]

    filtered = filtered.copy()
    if "status" not in filtered.columns and "output_status" in filtered.columns:
        filtered["status"] = filtered["output_status"]
    if "duplicate_group" not in filtered.columns and "duplicate_group_id" in filtered.columns:
        filtered["duplicate_group"] = filtered["duplicate_group_id"]
    if "blur_level" not in filtered.columns and "is_blur" in filtered.columns:
        filtered["blur_level"] = filtered["is_blur"].map({True: "Blur", False: "Sharp"})

    display_columns = [
        "filename",
        "status",
        "final_score",
        "human_quality_score",
        "technical_score",
        "sharpness_score",
        "exposure_score",
        "contrast_score",
        "blur_penalty",
        "blur_score",
        "blur_level",
        "person_count",
        "main_person_blur_score",
        "body_sharpness_score",
        "body_blur_penalty",
        "localized_person_blur",
        "face_count",
        "face_score",
        "duplicate_group",
        "duplicate_quality_rank",
        "is_best_duplicate",
        "culling_mode",
        "final_reason",
    ]
    display_columns = [column for column in display_columns if column in filtered.columns]
    view_mode = st.radio("Tampilan", ["Tabel", "Galeri"], horizontal=True)
    if view_mode == "Tabel":
        st.dataframe(filtered[display_columns], use_container_width=True, hide_index=True)
    else:
        render_gallery(filtered)

    output_folder = summary.get("output_folder", "")
    report_path = summary.get("report_path", "")
    st.markdown("### Lokasi Output")
    st.write(f"Folder output: `{output_folder}`")
    st.write(f"Laporan CSV: `{report_path or 'Tidak dibuat'}`")
    json_report_path = summary.get("json_report_path", "")
    st.write(f"Laporan JSON: `{json_report_path or 'Tidak dibuat'}`")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Buka Folder Output", use_container_width=True):
        ok, msg = open_local_path(output_folder)
        st.success(msg) if ok else st.warning(msg)
    if c2.button("Buka Laporan CSV", use_container_width=True, disabled=not bool(report_path)):
        ok, msg = open_local_path(report_path)
        st.success(msg) if ok else st.warning(msg)
    c3.download_button(
        "Download CSV Report",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="culling_report.csv",
        mime="text/csv",
        use_container_width=True,
    )
    if c4.button("Buka Laporan JSON", use_container_width=True, disabled=not bool(json_report_path)):
        ok, msg = open_local_path(json_report_path)
        st.success(msg) if ok else st.warning(msg)


def render_gallery(df: pd.DataFrame) -> None:
    """Render a lightweight thumbnail grid from copied output files."""
    if df.empty:
        st.info("Tidak ada hasil yang sesuai filter.")
        return

    preview = df.head(60)
    columns = st.columns(4)
    for index, (_, row) in enumerate(preview.iterrows()):
        column = columns[index % 4]
        with column:
            image_path = row.get("output_path") or row.get("original_path")
            if image_path and Path(str(image_path)).exists() and row.get("output_status") != "ERROR":
                st.image(str(image_path), use_container_width=True)
            status = str(row.get("output_status", "")).lower()
            badge_class = f"status-{status}"
            st.markdown(
                f"""
                <div style="margin-bottom: 16px;">
                    <span class="{badge_class}">{row.get('output_status')}</span>
                    <div class="card-title" style="font-size: 13px; margin-top: 8px;">{row.get('filename')}</div>
                    <div class="small-muted">Final Score: {row.get('final_score')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    if len(df) > len(preview):
        st.caption(f"Menampilkan 60 dari {len(df)} foto sesuai filter agar halaman tetap ringan.")


def render_settings_guide() -> None:
    """Render the settings guide tab."""
    st.subheader("Settings Guide")
    st.markdown(
        """
        ### Panduan Blur Threshold
        Nilai blur threshold menentukan seberapa ketat aplikasi menilai ketajaman foto.
        Nilai lebih tinggi = lebih ketat. Nilai lebih rendah = lebih longgar.
        Default: 100.

        ### Panduan Exposure Threshold
        Underexposed threshold default 50. Overexposed threshold default 210.
        Foto dengan brightness di bawah 50 dianggap terlalu gelap.
        Foto dengan brightness di atas 210 dianggap terlalu terang.

        ### Panduan Duplicate Threshold
        Duplicate hash threshold menentukan seberapa mirip dua foto agar dianggap satu grup.
        Nilai lebih kecil = lebih ketat. Nilai lebih besar = lebih longgar.
        Default: 8.

        ### Panduan Score
        Selected berarti foto kemungkinan besar layak dipakai.
        Review berarti foto perlu dicek manual.
        Rejected berarti foto kemungkinan besar tidak layak.

        Aplikasi ini membantu menyaring, bukan menggantikan keputusan akhir manusia.
        """
    )


def render_about() -> None:
    """Render the About tab."""
    st.subheader("About")
    st.markdown(
        f"""
        **{APP_NAME}** adalah {APP_VERSION} untuk membantu tim multimedia gereja
        melakukan culling foto lebih cepat dengan analisis ketajaman, pencahayaan,
        kemiripan foto, dan deteksi wajah.

        **Mode kerja:** lokal/offline di laptop pengguna.

        **Keamanan:** aplikasi tidak menghapus file asli dan tidak memindahkan file sumber.

        **Batasan versi 1:**

        - Belum melakukan editing otomatis.
        - Belum melakukan upload otomatis ke Facebook.
        - Belum melakukan training AI khusus.
        - Belum mendukung penuh file RAW.
        """
    )


def main() -> None:
    if get_script_run_ctx(suppress_warning=True) is None:
        print(
            "\nCullaGrace adalah aplikasi Streamlit.\n"
            "Jalankan dari terminal dengan perintah:\n\n"
            "  streamlit run app.py\n"
        )
        return

    st.set_page_config(
        page_title=f"{APP_NAME} - {APP_VERSION}",
        page_icon=":camera:",
        layout="wide",
    )
    init_state()
    inject_styles()
    config = sidebar_controls()
    render_header()

    dashboard_tab, process_tab, results_tab, guide_tab, about_tab = st.tabs(
        ["Dashboard", "Culling Process", "Results", "Settings Guide", "About"]
    )
    with dashboard_tab:
        render_dashboard(config)
    with process_tab:
        render_process_panel(config)
    with results_tab:
        render_results()
    with guide_tab:
        render_settings_guide()
    with about_tab:
        render_about()


if __name__ == "__main__":
    main()
