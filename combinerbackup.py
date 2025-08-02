#!/usr/bin/env python3
"""
combiner.py
Combine PDFs in a given folder in specified order and save to the user's Downloads folder.
"""

import os
import sys
from pathlib import Path
from pypdf import PdfWriter, PdfReader


def combine_pdfs(input_folder: Path, pdf_order: list[str], output_filename: str = "combined.pdf") -> Path:
    writer = PdfWriter()
    # Determine merge order
    if pdf_order:
        order_paths = [input_folder / name for name in pdf_order]
    else:
        order_paths = sorted(
            (p for p in input_folder.iterdir() if p.suffix.lower() == ".pdf"),
            key=lambda p: p.name.casefold(),
        )

    added = 0
    for p in order_paths:
        if p.is_file() and p.suffix.lower() == ".pdf":
            reader = PdfReader(str(p))
            for page in reader.pages:
                writer.add_page(page)
            added += 1

    if added == 0:
        raise ValueError("No valid PDFs found to merge.")

    # Resolve Downloads folder
    if os.name == "nt":
        downloads = Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads"
    else:
        downloads = Path.home() / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)

    output_path = downloads / output_filename
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python combiner.py <input_folder> <output_filename> [file1 file2 ...]")
        sys.exit(1)

    folder = Path(sys.argv[1])
    out_name = sys.argv[2]
    names = sys.argv[3:]
    try:
        result = combine_pdfs(folder, names, out_name)
        print(f"✔ Combined PDF saved to {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
