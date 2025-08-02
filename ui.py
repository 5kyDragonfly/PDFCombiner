#!/usr/bin/env python3
"""
ui.py – PDF Combiner front-end
• Upload PDFs
• Custom list with ↑ / ↓ / ✖
• Combine → saves to Downloads, shows toast, optional “Open folder” (local)
"""

from __future__ import annotations
import os, platform, tempfile, logging
from pathlib import Path

import streamlit as st
import combiner          # combiner.py must be in the same folder

logging.basicConfig(level=logging.INFO)
DEBUG = False            # flip to True for sidebar debug


# ───────────────────────────────── helpers ──────────────────────────
def _rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()            # for Streamlit < 1.25


def _init_state() -> None:
    if "files" not in st.session_state:    # our working list
        st.session_state.files: list[dict] = []
    if "uploader_key" not in st.session_state:  # forces uploader reset
        st.session_state.uploader_key = 0


def _add_uploads(uploaded) -> None:
    """Append new uploads to session list (dedup by name+size)."""
    for up in uploaded:
        data = up.read()
        if any(f["name"] == up.name and len(f["data"]) == len(data)
               for f in st.session_state.files):
            continue
        key = f"{up.name}-{len(data)}"
        st.session_state.files.append({"name": up.name, "data": data, "key": key})
        logging.info("Added %s", up.name)


def _move(idx: int, delta: int) -> None:
    j = idx + delta
    if 0 <= j < len(st.session_state.files):
        st.session_state.files[idx], st.session_state.files[j] = (
            st.session_state.files[j], st.session_state.files[idx]
        )
        logging.info("Moved %s to pos %d", st.session_state.files[j]["name"], j)


def _open_folder(path: Path) -> None:
    try:
        if os.name == "nt":
            os.startfile(str(path))
        elif platform.system() == "Darwin":
            os.system(f"open {path}")
        elif platform.system() == "Linux":
            os.system(f"xdg-open {path}")
    except Exception:
        pass


# ───────────────────────────────── UI ───────────────────────────────
st.set_page_config(page_title="PDF Combiner", layout="wide")
_init_state()

# Hide Streamlit’s internal file list + footer
st.markdown(
    """
    <style>
    div[data-testid="stFileUploader"] ul {display:none !important;}
    div[data-testid="stFileUploader"] button[data-testid="file-uploader-pagination-next"],
    div[data-testid="stFileUploader"] button[data-testid="file-uploader-pagination-prev"],
    div[data-testid="stFileUploader"] span[data-testid="file-uploader-pagination"] {
        display:none !important;
    }
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
    key=f"uploader-{st.session_state.uploader_key}",    # dynamic key!
)
if uploads:
    _add_uploads(uploads)

# custom list
for i, f in enumerate(list(st.session_state.files)):   # copy keeps index stable
    c1, c2, c3, c4 = st.columns([6, 1, 1, 1])
    c1.markdown(f"**{f['name']}**")
    if c2.button("↑", key=f"up-{f['key']}"):
        _move(i, -1); _rerun()
    if c3.button("↓", key=f"down-{f['key']}"):
        _move(i, +1); _rerun()
    if c4.button("✖", key=f"del-{f['key']}"):
        # remove file, then reset uploader widget so it doesn't re-add it
        st.session_state.files = [x for x in st.session_state.files if x["key"] != f["key"]]
        st.session_state.uploader_key += 1
        logging.info("Deleted %s", f["name"])
        _rerun()

# debug panel
if DEBUG:
    with st.sidebar.expander("Session state"):
        st.json(st.session_state.files)

# combine action
if combine_clicked:
    if not st.session_state.files:
        st.warning("No PDFs selected.")
    else:
        tmpdir = Path(tempfile.mkdtemp())
        for it in st.session_state.files:
            (tmpdir / it["name"]).write_bytes(it["data"])
        order = [it["name"] for it in st.session_state.files]

        try:
            out_path = combiner.combine_pdfs(tmpdir, order, "combined.pdf")
            st.toast("Combined PDF saved to Downloads 📁", icon="✅")
            st.session_state.uploader_key += 1         # clear uploader for next batch
            if st.button("Open Downloads folder"):
                _open_folder(out_path.parent)
        except Exception as e:
            st.toast(f"Merge failed: {e}", icon="❌")
            logging.exception("Merge failed")
