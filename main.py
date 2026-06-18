"""
Employee File Verifier: scan a local folder and export a yes/no checklist per employee.
"""

import argparse
import os
import sys

from config import OUTPUT_DIR, load_config
from utils.document_inventory import (
    DEFAULT_DOCUMENT_ALIASES,
    run_inventory,
)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Build an employee document checklist from local folder filenames."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Path to the folder containing employee documents",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help=f"Where to save the CSV (default: {OUTPUT_DIR})",
    )
    args = parser.parse_args()

    folder = args.folder
    if not folder:
        folder = input("Enter the folder path containing employee documents: ").strip().strip('"')
    folder = os.path.abspath(folder)

    if not os.path.isdir(folder):
        print(f"Error: Not a valid folder: {folder}")
        sys.exit(1)

    config = load_config()
    output_dir = os.path.abspath(args.output_dir or config.get("output_dir", OUTPUT_DIR))
    aliases = config.get("document_aliases", DEFAULT_DOCUMENT_ALIASES)

    print(f"\nScanning: {folder}")
    print("Reading file names only (no OCR, no cloud download).\n")

    try:
        csv_path, emp_count, doc_slots = run_inventory(
            folder,
            output_dir,
            aliases=aliases,
        )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("Done.")
    print(f"  Employees found: {emp_count}")
    print(f"  Document entries: {doc_slots}")
    print(f"  Report saved to: {csv_path}\n")


if __name__ == "__main__":
    main()
