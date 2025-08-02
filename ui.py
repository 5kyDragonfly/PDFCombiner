#!/usr/bin/env python3
"""
ui.py – Streamlit front-end for PDFCombiner
• Drag-and-drop or browse to add PDFs
• Inline PDF preview
• ← / → buttons to reorder, ✖ to remove
• “Combine PDFs” writes combined.pdf and offers a download
"""

from __future__ import annotations
import base64, io, os, tempfile
from pathlib import Path

import streamlit as st
from pypdf import PdfReader, PdfWriter


# ---------- helpers -------------------------------------------------
def _init_state() -> None:
    if "files" not in st.session_state:
        st.session_state.files: list[dict] = []  # {name,data,key}


def _add_uploads(uploaded) -> None:
    for up in uploaded:
        data = up.read()
        # dedupe on name + size
        if any(f["name"] == up.name and len(f["data"]) == len(data) for f in st.session_state.files):
            continue
        st.session_state.files.append(
            {"name": up.name, "data": data, "key": f"{up.name}-{len(data)}"}
        )


def _pdf_pages(data: bytes) -> int:
    try:
        return len(PdfReader(io.BytesIO(data)).pages)
    except Exception:
        return 0


def _pdf_preview(data: bytes, height: int = 240, **kwargs) -> None:
    """Embed a PDF via data URL. Extra kwargs are passed to Streamlit HTML component."""
    b64 = base64.b64encode(data).decode()
    html = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="{height}"></iframe>'
    st.components.v1.html(html, height=height + 6, **kwargs)


def _move(idx: int, delta: int) -> None:
    j = idx + delta
    if 0 <= j < len(st.session_state.files):
        st.session_state.files[idx], st.session_state.files[j] = (
            st.session_state.files[j],
            st.session_state.files[idx],
        )


def _combine(files: list[dict]) -> bytes:
    writer, added = PdfWriter(), 0
    for f in files:
        reader = PdfReader(io.BytesIO(f["data"]))
        for p in reader.pages:
            writer.add_page(p)
        added += 1
    buf = io.BytesIO()
    writer.write(buf)
    writer.close()
    buf.seek(0)
    return buf.read() if added else b""


def _dl_path() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads"
    return Path.home() / "Downloads"


# ---------- UI ------------------------------------------------------
st.set_page_config(page_title="PDF Combiner", layout="wide")
_init_state()

st.title("PDF Combiner")

# top bar
combine_now = st.button("Combine PDFs", type="primary")
st.caption("Add PDFs, set the order, then click **Combine PDFs**.")

# uploader
uploads = st.file_uploader(
    "Drop PDF files here or click to browse",
    type=["pdf"],
    accept_multiple_files=True,
)
if uploads:
    _add_uploads(uploads)

# list with controls & preview (wrapped in placeholder)
placeholder = st.empty()
with placeholder.container():
    for i, f in enumerate(list(st.session_state.files)):  # copy so index stable
        with st.container(border=True):
            cols = st.columns([5, 1, 1, 1])
            cols[0].markdown(f"**{f['name']}** ({_pdf_pages(f['data'])} pg)")
            if cols[1].button("←", key=f"left-{f['key']}"):
                _move(i, -1)
                st.experimental_rerun()
            if cols[2].button("→", key=f"right-{f['key']}"):
                _move(i, 1)
                st.experimental_rerun()
            if cols[3].button("✖", key=f"del-{f['key']}"):
                st.session_state.files.pop(i)
                st.experimental_rerun()
            _pdf_preview(f["data"], key=f"prev-{f['key']}")  # unique key per preview

# combine action
if combine_now:
    if not st.session_state.files:
        st.warning("No PDFs selected.")
    else:
        pdf_bytes = _combine(st.session_state.files)
        if not pdf_bytes:
            st.error("Merge failed.")
        else:
            st.success("Combined PDF ready!")
            st.download_button(
                label="Download combined.pdf",
                data=pdf_bytes,
                file_name="combined.pdf",
                mime="application/pdf",
            )
            # local dev: also write to Downloads
            try:
                local = _dl_path() / "combined.pdf"
                local.write_bytes(pdf_bytes)
                st.caption(f"Saved a copy to **{local}**")
            except Exception:
                pass
