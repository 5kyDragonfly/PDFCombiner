#!/usr/bin/env python3
"""
combiner.py
Merge PDFs found in FOLDER_PATH.

• If PDF_ORDER contains filenames, they are merged exactly in that order.
• If PDF_ORDER is empty, all PDFs in the folder are merged
  alphabetically (case-insensitive).

Requires: pip install -U pypdf
"""

from pathlib import Path
from pypdf import PdfWriter, PdfReader

# ------------ CONFIG -------------------------------------------------
FOLDER_PATH = Path(r"pdf_source")
PDF_ORDER: list[str] = []                # put filenames here or leave empty
OUTPUT_FILE = FOLDER_PATH / "combined.pdf"
# ---------------------------------------------------------------------


def default_order(folder: Path) -> list[Path]:
    """Return every *.pdf in the folder, alphabetically."""
    return sorted(
        (p for p in folder.iterdir() if p.suffix.lower() == ".pdf"),
        key=lambda p: p.name.casefold(),
    )


def main() -> None:
    writer = PdfWriter()

    order = [FOLDER_PATH / name for name in PDF_ORDER] if PDF_ORDER else default_order(FOLDER_PATH)

    added = 0
    for pdf_path in order:
        if pdf_path.is_file() and pdf_path.suffix.lower() == ".pdf":
            # PdfWriter has an .append() helper (pypdf ≥3). If unavailable, fall back.
            try:
                writer.append(str(pdf_path))
            except AttributeError:
                reader = PdfReader(str(pdf_path))
                for page in reader.pages:
                    writer.add_page(page)
            print(f"Added {pdf_path.name}")
            added += 1
        else:
            print(f"Skipped {pdf_path} (missing or not a PDF)")

    if added:
        with OUTPUT_FILE.open("wb") as f:
            writer.write(f)
        print(f"✔ Merged {added} PDF(s) into {OUTPUT_FILE}")
    else:
        print("⚠ No valid PDFs found — nothing merged.")


if __name__ == "__main__":
    main()
