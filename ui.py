#!/usr/bin/env python3
"""
ui.py – Streamlit front-end for PDFCombiner
• Upload PDFs, reorder with ↑ / ↓, remove with ✖
• “Combine PDFs” calls combiner.combine_pdfs()
• Combined file is saved to Downloads; UI shows path + (Windows) folder link
"""

from __future__ import annotations
import os, tempfile
from pathlib import Path

import streamlit as st
import combiner  # combiner.py must be in the same directory


# ---------- helpers -------------------------------------------------
def _rerun() -> None:
    """Streamlit changed API: st.rerun() ≥1.25, st.experimental_rerun() before."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()  # type: ignore[attr-defined]


def _init_state() -> None:
    if "files" not in st.session_state:
        st.session_state.files = []  # type: list[dict]  # each dict: {name, data, key}


def _add_uploads(uploaded) -> None:
    for up in uploaded:
        data = up.read()
        # dedupe on name + size
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


# ---------- UI ------------------------------------------------------
st.set_page_config(page_title="PDF Combiner", layout="wide")
_init_state()

st.title("PDF Combiner")

combine_clicked = st.button("Combine PDFs", type="primary")
st.caption("Upload PDFs below, reorder them with the arrows, then click Combine PDFs.")

uploads = st.file_uploader(
    "Drag & drop PDFs here or click to browse",
    type=["pdf"],
    accept_multiple_files=True,
)
if uploads:
    _add_uploads(uploads)

# list view with ↑ ↓ ✖
for i, f in enumerate(list(st.session_state.files)):
    cols = st.columns([5, 1, 1, 1])
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
            out_path = combiner.combine_pdfs(folder, names, output_filename="combined.pdf")
            st.success(f"Combined PDF saved to: `{out_path}`")
            if os.name == "nt":
                st.markdown(f"[Open Downloads folder](file:///{out_path.parent})")
        except Exception as e:
            st.error(f"Merge failed: {e}")
