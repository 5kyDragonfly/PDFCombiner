#!/usr/bin/env python3
"""
ui.py – PDF Combiner front-end
• Upload PDFs
• Custom list with ↑ / ↓ / ✖
• Combines via combiner.combine_pdfs()
• Saves to Downloads + toast notification
"""

from __future__ import annotations
import os, platform, tempfile
from pathlib import Path

import streamlit as st
import combiner  # combiner.py in the same folder


# ---------- helpers ----------
def _rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()  # pragma: no cover


def _init_state() -> None:
    if "files" not in st.session_state:
        st.session_state.files = []  # type: list[dict]  # {name, data, key}


def _add_uploads(uploaded) -> None:
    for up in uploaded:
        data = up.read()
        if any(f["name"] == up.name and len(f["data"]) == len(data) for f in st.session_state.files):
            continue
        st.session_state.files.append({"name": up.name, "data": data, "key": f"{up.name}-{len(data)}"})


def _move(idx: int, delta: int) -> None:
    j = idx + delta
    if 0 <= j < len(st.session_state.files):
        st.session_state.files[idx], st.session_state.files[j] = (
            st.session_state.files[j],
            st.session_state.files[idx],
        )


def _downloads_path() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads"
    return Path.home() / "Downloads"


def _open_folder(path: Path) -> None:
    """Try to open the folder in the local file explorer (no-op on Streamlit Cloud)."""
    try:
        if os.name == "nt":
            os.startfile(str(path))
        elif platform.system() == "Darwin":
            os.system(f"open {path}")
        elif platform.system() == "Linux":
            os.system(f"xdg-open {path}")
    except Exception:
        pass  # ignore silently


# ---------- UI ----------
st.set_page_config(page_title="PDF Combiner", layout="wide")
_init_state()

# Hide the default uploader preview to avoid duplicate rows
st.markdown(
    """
    <style>
    /* 1️⃣ Hide <ul> list + its <li> rows */
    div[data-testid="stFileUploader"] ul {display:none !important;}

    /* 2️⃣ Hide "Showing page X of Y" footer + pagination arrows */
    div[data-testid="stFileUploader"] button[data-testid="file-uploader-pagination-next"],
    div[data-testid="stFileUploader"] button[data-testid="file-uploader-pagination-prev"],
    div[data-testid="stFileUploader"] span[data-testid="file-uploader-pagination"] {
        display:none !important;
    }

    /* 3️⃣ Remove extra margin the list leaves behind */
    div[data-testid="stFileUploader"] > section > div:first-child {
        margin-bottom:0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("PDF Combiner")

combine_clicked = st.button("Combine PDFs", type="primary")
st.caption("Upload PDFs, reorder with ↑ / ↓, remove with ✖, then click Combine.")

uploads = st.file_uploader(
    "Drag & drop PDFs here or click Browse",
    type=["pdf"],
    accept_multiple_files=True,
)
if uploads:
    _add_uploads(uploads)

# custom list
for i, f in enumerate(list(st.session_state.files)):
    cols = st.columns([6, 1, 1, 1])
    cols[0].markdown(f"**{f['name']}**")
    if cols[1].button("↑", key=f"up-{f['key']}"):
        _move(i, -1)
        _rerun()
    if cols[2].button("↓", key=f"down-{f['key']}"):
        _move(i, +1)
        _rerun()
    if cols[3].button("✖", key=f"del-{f['key']}"):
        st.session_state.files.pop(i)
        _rerun()

# combine action
if combine_clicked:
    if not st.session_state.files:
        st.warning("No PDFs selected.")
    else:
        tmpdir = tempfile.mkdtemp()
        folder = Path(tmpdir)
        for it in st.session_state.files:
            (folder / it["name"]).write_bytes(it["data"])
        names = [it["name"] for it in st.session_state.files]

        try:
            out_path = combiner.combine_pdfs(folder, names, "combined.pdf")
            st.toast("Combined PDF saved to Downloads 📁", icon="✅")
            # Button to open folder (works only on local desktop)
            if st.button("Open Downloads folder"):
                _open_folder(out_path.parent)
        except Exception as e:
            st.toast(f"Merge failed: {e}", icon="❌")
