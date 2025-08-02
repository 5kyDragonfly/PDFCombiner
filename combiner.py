#!/usr/bin/env python3
"""
combiner.py
• Library use: `combine_pdfs(folder, order)`  → bytes
  (nothing is written to disk; Streamlit sends the bytes to the browser)
• CLI use:  `python combiner.py <input_folder> <output_name> [file1 file2 ...]`
  → writes combined PDF to ~/Downloads/ and prints the path
"""

import io
import os
import sys
from pathlib import Path
from typing import List

from pypdf import PdfReader, PdfWriter


def _merge_order(folder: Path, order: List[str]) -> List[Path]:
    """Return a list of PDF paths in the requested order (or alpha if blank)."""
    if order:
        return [folder / name for name in order]
    return sorted(
        (p for p in folder.iterdir() if p.suffix.lower() == ".pdf"),
        key=lambda p: p.name.casefold(),
    )


def combine_pdfs(input_folder: Path, pdf_order: List[str]) -> bytes:
    """
    Merge PDFs from `input_folder` following `pdf_order`.
    Returns: bytes of the combined PDF (no file is written).
    """
    writer = PdfWriter()
    added = 0

    for pdf_path in _merge_order(input_folder, pdf_order):
        if pdf_path.is_file() and pdf_path.suffix.lower() == ".pdf":
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                writer.add_page(page)
            added += 1

    if added == 0:
        raise ValueError("No valid PDFs found to merge.")

    buf = io.BytesIO()
    writer.write(buf)
    writer.close()
    buf.seek(0)
    return buf.read()


# ───────── CLI fallback (keeps old behaviour) ─────────
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python combiner.py <input_folder> <output_filename> [file1 file2 ...]")
        sys.exit(1)

    folder = Path(sys.argv[1])
    out_name = sys.argv[2]
    names = sys.argv[3:]

    try:
        pdf_bytes = combine_pdfs(folder, names)

        # Save to user's Downloads (only makes sense when running locally)
        if os.name == "nt":
            downloads = Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads"
        else:
            downloads = Path.home() / "Downloads"
        downloads.mkdir(parents=True, exist_ok=True)

        output_path = downloads / out_name
        output_path.write_bytes(pdf_bytes)
        print(f"✔ Combined PDF saved to {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
