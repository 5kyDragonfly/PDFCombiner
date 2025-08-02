#!/usr/bin/env python3
"""
ui.py – PDF Combiner (Streamlit Cloud ready)
"""

from __future__ import annotations
import logging, os, tempfile
from pathlib import Path

import streamlit as st
import combiner                     # combine_pdfs returns bytes

logging.basicConfig(level=logging.INFO)
DEBUG = False                       # set True to see debug info

# ───────────────────────── helpers ──────────────────────────
def _rerun() -> None:
    st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()  # type: ignore[attr-defined]

def _init_state() -> None:
    st.session_state.setdefault("files", [])          # type: list[dict]
    st.session_state.setdefault("uploader_key", 0)    # resets file_uploader

def _add_uploads(uploaded) -> None:
    for up in uploaded:
        data = up.read()
        if any(f["name"] == up.name and len(f["data"]) == len(data)
               for f in st.session_state.files):
            continue
        st.session_state.files.append(
            {"name": up.name, "data": data, "key": f"{up.name}-{len(data)}"}
        )

def _move(idx: int, delta: int) -> None:
    j = idx + delta
    if 0 <= j < len(st.session_state.files):
        st.session_state.files[idx], st.session_state.files[j] = (
            st.session_state.files[j], st.session_state.files[idx]
        )

# ───────────────────────── UI ───────────────────────────────
st.set_page_config(page_title="PDF Combiner", layout="wide")
_init_state()

# Hide Streamlit’s internal preview list & footer
st.markdown(
    """
    <style>
      div[data-testid="stFileUploader"] ul {display:none !important;}
      div[data-testid="stFileUploader"] button[data-testid="file-uploader-pagination-next"],
      div[data-testid="stFileUploader"] button[data-testid="file-uploader-pagination-prev"],
      div[data-testid="stFileUploader"] span[data-testid="file-uploader-pagination"] {
          display:none !important;}
      div[data-testid="stFileUploader"] > section > div:first-child {
          margin-bottom:0 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("PDF Combiner")

combine_clicked = st.button("Combine PDFs", type="primary")
st.caption("Upload PDFs, reorder with ↑ / ↓, remove with ✖, then click Combine.")

uploads = st.file_uploader(
    "Drag & drop PDFs here or Browse",
    type=["pdf"],
    accept_multiple_files=True,
    key=f"uploader-{st.session_state.uploader_key}",
)
if uploads:
    _add_uploads(uploads)

# custom list
for i, f in enumerate(list(st.session_state.files)):
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])   # tighter first column
    c1.markdown(f"**{f['name']}**")
    if c2.button("↑", key=f"up-{f['key']}"):
        _move(i, -1); _rerun()
    if c3.button("↓", key=f"down-{f['key']}"):
        _move(i, +1); _rerun()
    if c4.button("✖", key=f"del-{f['key']}"):
        st.session_state.files = [x for x in st.session_state.files if x["key"] != f["key"]]
        st.session_state.uploader_key += 1
        _rerun()

# ───────── combine & download ───────────────────────────────
if combine_clicked:
    if not st.session_state.files:
        st.warning("No PDFs selected.")
    else:
        tmpdir = Path(tempfile.mkdtemp())
        for it in st.session_state.files:
            (tmpdir / it["name"]).write_bytes(it["data"])
        order = [it["name"] for it in st.session_state.files]

        try:
            pdf_bytes = combiner.combine_pdfs(tmpdir, order)  # returns bytes

            st.toast("Combined PDF ready – download below 👇", icon="✅")
            st.download_button(
                "⬇️ Download combined.pdf",
                data=pdf_bytes,
                mime="application/pdf",
                file_name="combined.pdf",
            )

            # debug block
            if DEBUG:
                st.info(f"Merged {len(order)} files – {len(pdf_bytes):,} bytes")

            # clear list & reset uploader (no immediate rerun -> keeps download button visible)
            st.session_state.files = []
            st.session_state.uploader_key += 1

        except Exception as e:
            st.toast(f"Merge failed: {e}", icon="❌")
            logging.exception("Merge failed")
