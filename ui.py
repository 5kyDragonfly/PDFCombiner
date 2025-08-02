#!/usr/bin/env python3
"""
ui.py – PDF Combiner (Streamlit Cloud)
• Upload PDFs
• Custom list with ↑ / ↓ / ✖
• Combine → green-outlined Download button beside Combine
"""

from __future__ import annotations
import logging, tempfile
from pathlib import Path

import streamlit as st
import combiner

logging.basicConfig(level=logging.INFO)
DEBUG = False

# ───────────────────── helpers ───────────────────────────
def _rerun():  st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()   # type: ignore[attr-defined]

def _init_state() -> None:
    st.session_state.setdefault("files", [])            # list[dict]
    st.session_state.setdefault("uploader_key", 0)      # reset uploader
    st.session_state.setdefault("combined_bytes", None) # store merged PDF

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

# ───────────────────── UI setup ──────────────────────────
st.set_page_config(page_title="PDF Combiner", layout="wide")
_init_state()

# Hide Streamlit’s internal file list & footer and style Download btn
st.markdown(
    """
    <style>
      /* hide default uploader list */
      div[data-testid="stFileUploader"] ul{display:none !important;}
      div[data-testid="stFileUploader"] button[data-testid^="file-uploader-pagination"],
      div[data-testid="stFileUploader"] span[data-testid="file-uploader-pagination"]{
          display:none !important;}
      div[data-testid="stFileUploader"]>section>div:first-child{
          margin-bottom:0!important;}

      /* make the Download button green-outlined */
      button[data-testid="stDownloadButton"] {
          background-color: transparent !important;
          color: #2ecc71 !important;
          border: 2px solid #2ecc71 !important;
      }
      button[data-testid="stDownloadButton"]:hover {
          background-color: #2ecc71 !important;
          color: white !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("PDF Combiner")

# top-row buttons
col_combine, col_download = st.columns([1,1])
combine_clicked = col_combine.button("Combine PDFs", type="primary")

if st.session_state.get("combined_bytes"):
    col_download.download_button(
        "⬇️ Download combined.pdf",
        data=st.session_state["combined_bytes"],
        mime="application/pdf",
        file_name="combined.pdf",
        key="download_btn",
    )

st.caption("Upload PDFs, reorder with ↑ / ↓, remove with ✖, then click Combine.")

# uploader
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
    c1, c2, c3, c4 = st.columns([3,1,1,1])
    c1.markdown(f"**{f['name']}**")
    if c2.button("↑", key=f"up-{f['key']}"): _move(i, -1); _rerun()
    if c3.button("↓", key=f"down-{f['key']}"): _move(i, +1); _rerun()
    if c4.button("✖", key=f"del-{f['key']}"):
        st.session_state.files = [x for x in st.session_state.files if x["key"] != f["key"]]
        st.session_state.uploader_key += 1
        _rerun()

if DEBUG:
    with st.sidebar.expander("Debug: session files"):
        st.json(st.session_state.files)

# ─────── combine action ──────────────────────────────────
if combine_clicked:
    if not st.session_state.files:
        st.warning("No PDFs selected.")
    else:
        tmpdir = Path(tempfile.mkdtemp())
        for it in st.session_state.files:
            (tmpdir / it["name"]).write_bytes(it["data"])
        order = [it["name"] for it in st.session_state.files]

        try:
            pdf_bytes = combiner.combine_pdfs(tmpdir, order)
            st.session_state["combined_bytes"] = pdf_bytes  # make available to top-row download
            st.toast("Combined PDF ready ✔", icon="✅")

            # clear list & reset uploader
            st.session_state.files = []
            st.session_state.uploader_key += 1
            _rerun()

        except Exception as e:
            st.toast(f"Merge failed: {e}", icon="❌")
            logging.exception("Merge failed")
