"""
Scan a local folder of employee documents and build a yes/no inventory matrix
from file and folder names (no OCR or cloud sync).
"""

import csv
import os
import re
from collections import defaultdict
from datetime import datetime

# Extensions HR typically stores; extend via config if needed
DEFAULT_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff",
    ".doc", ".docx", ".xls", ".xlsx",
}

# Only these document types are tracked (order = CSV column order)
DEFAULT_DOCUMENT_ALIASES = {
    "Appointment Letter": [
        "appointment letter", "appointments letter", "appointment",
    ],
    "Educational Documents": [
        "educational documents", "educational document", "educational",
        "education document", "education documents",
        "marksheet", "mark sheet", "marks sheet",
        "degree certificate", "degree", "certificate",
    ],
    "Experience Letter": [
        "experience letter", "experiance letter", "experience",
    ],
    "Increment Letter": [
        "increment letter", "increment",
    ],
    "Aadhar Card": [
        "aadhar card", "aadhaar card", "adhar card",
        "aadhar", "aadhaar", "adhar",
    ],
    "PAN Card": [
        "pan card", "pan",
    ],
    "Employee Code": [
        "employee code", "emp code", "code",
    ],
    "DOJ": [
        "doj", "date of joining", "joining date",
    ],
    "Designation": [
        "designation", "desg", "desig",
    ],
    "Department": [
        "department", "dept",
    ],
    "Employee Category": [
        "employee category", "emp category", "category",
    ],
}


# Noise words sometimes added by HR; stripped when extracting the employee name
FILLER_TOKENS = frozenset({
    "copy", "scanned", "scan", "signed", "final", "document", "doc", "file",
    "original", "duplicate", "attested", "verified",
})


def _normalize_display_name(text: str) -> str:
    text = re.sub(r"[_\-|]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.title() if text.islower() or "_" in text else text.strip()


def _aliases_sorted(aliases: dict) -> list[tuple[str, str]]:
    """Return (canonical_label, pattern) pairs sorted by pattern length descending."""
    pairs = []
    for label, patterns in aliases.items():
        for pattern in patterns:
            pairs.append((label, pattern.lower()))
    pairs.sort(key=lambda x: len(x[1]), reverse=True)
    return pairs


def _pattern_in_filename(pattern: str, stem: str) -> bool:
    """
    Match document keywords anywhere in the filename.
    Short or single-word patterns use word boundaries to avoid false hits.
    """
    if " " in pattern or len(pattern) > 4:
        return pattern in stem.lower()
    return bool(re.search(rf"\b{re.escape(pattern)}\b", stem, re.IGNORECASE))


def _remove_pattern_ignore_case(text: str, pattern: str) -> str:
    if " " in pattern or len(pattern) > 4:
        regex = re.compile(re.escape(pattern), re.IGNORECASE)
    else:
        regex = re.compile(rf"\b{re.escape(pattern)}\b", re.IGNORECASE)
    return regex.sub("", text)


def detect_document_type(stem: str, aliases: dict) -> str | None:
    """Find document type in the filename — works whether it appears before or after the name."""
    for label, pattern in _aliases_sorted(aliases):
        if _pattern_in_filename(pattern, stem):
            return label
    return None


def _patterns_for_label(doc_type: str, aliases: dict) -> list[str]:
    for label, patterns in aliases.items():
        if label == doc_type:
            return sorted(patterns, key=len, reverse=True)
    return []


def parse_filename(stem: str, aliases: dict) -> tuple[str, str | None]:
    """
    Split a filename stem into (employee_name, document_type).
    Order-independent: both 'Aditi Sarang - Aadhar Card' and 'Aadhar Card - Aditi Sarang' work.
    """
    doc_type = detect_document_type(stem, aliases)
    employee = extract_employee_from_stem(stem, doc_type, aliases)
    return employee, doc_type


def extract_employee_from_stem(stem: str, doc_type: str | None, aliases: dict) -> str:
    """Remove the matched document label; whatever remains is the employee name."""
    remaining = stem
    if doc_type:
        for pattern in _patterns_for_label(doc_type, aliases):
            if _pattern_in_filename(pattern, remaining):
                remaining = _remove_pattern_ignore_case(remaining, pattern)
                break

    remaining = re.sub(r"[\s_\-|]+", " ", remaining).strip(" -_|")
    remaining = re.sub(r"\b\d{4,}\b", "", remaining).strip()

    tokens = [t for t in remaining.split() if t.lower() not in FILLER_TOKENS]
    remaining = " ".join(tokens).strip()

    return _normalize_display_name(remaining) if remaining else ""


def _folder_employee_name(rel_dir: str) -> str:
    parts = [p for p in rel_dir.replace("\\", "/").split("/") if p and p != "."]
    if not parts:
        return ""
    return _normalize_display_name(parts[-1])


def scan_folder(
    folder_path: str,
    *,
    aliases: dict | None = None,
    extensions: set | None = None,
    include_subfolders: bool = True,
) -> tuple[dict[str, set[str]], list[str]]:
    """
    Walk folder_path and return:
      - employee_name -> set of document type labels present
      - ordered list of all document type column names
    """
    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    aliases = aliases or DEFAULT_DOCUMENT_ALIASES
    extensions = extensions or DEFAULT_EXTENSIONS
    inventory: dict[str, set[str]] = defaultdict(set)

    if include_subfolders:
        walker = os.walk(folder_path)
    else:
        walker = [(folder_path, [], os.listdir(folder_path))]

    for dirpath, _dirnames, filenames in walker:
        rel_dir = os.path.relpath(dirpath, folder_path)
        in_subfolder = rel_dir not in (".", "")

        for filename in filenames:
            if filename.startswith("."):
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext not in extensions:
                continue

            stem = os.path.splitext(filename)[0]
            file_emp, doc_type = parse_filename(stem, aliases)

            if in_subfolder:
                folder_emp = _folder_employee_name(rel_dir)
                name_is_doc_only = (
                    not file_emp
                    or (doc_type and file_emp.lower() == doc_type.lower())
                )
                employee = folder_emp if name_is_doc_only else file_emp or folder_emp
            else:
                employee = extract_employee_from_stem(stem, doc_type, aliases)
                if not employee:
                    employee = _normalize_display_name(stem)

            if not employee:
                continue

            if not doc_type:
                continue

            inventory[employee].add(doc_type)

    columns = list(aliases.keys())

    return dict(inventory), columns


def write_inventory_csv(
    inventory: dict[str, set[str]],
    columns: list[str],
    output_path: str,
) -> str:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    missing_col = "Missing Docs"
    
    # Ensure "Employee Code" is at the very first column before "Employee Name"
    has_emp_code = "Employee Code" in columns
    other_columns = [col for col in columns if col != "Employee Code"]
    
    if has_emp_code:
        fieldnames = ["Employee Code", "Employee Name"] + other_columns + [missing_col]
    else:
        fieldnames = ["Employee Name"] + columns + [missing_col]

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for employee in sorted(inventory.keys(), key=lambda x: x.lower()):
            row = {"Employee Name": employee}
            present = inventory[employee]
            missing = []
            
            if has_emp_code:
                if "Employee Code" in present:
                    row["Employee Code"] = "Yes"
                else:
                    row["Employee Code"] = "No"
                    missing.append("Employee Code")

            for col in other_columns:
                if col in present:
                    row[col] = "Yes"
                else:
                    row[col] = "No"
                    missing.append(col)
            row[missing_col] = ", ".join(missing)
            writer.writerow(row)

    return output_path


def build_output_path(input_folder: str, output_dir: str) -> str:
    folder_label = os.path.basename(os.path.normpath(input_folder)) or "inventory"
    safe_label = re.sub(r'[<>:"/\\|?*]', "_", folder_label)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_label}_document_inventory_{timestamp}.csv"
    return os.path.join(output_dir, filename)


def run_inventory(
    folder_path: str,
    output_dir: str,
    *,
    aliases: dict | None = None,
    extensions: set | None = None,
) -> tuple[str, int, int]:
    """
    Scan folder and write CSV. Returns (output_path, employee_count, file_count).
    """
    inventory, columns = scan_folder(
        folder_path,
        aliases=aliases,
        extensions=extensions,
    )
    if not inventory:
        raise ValueError(
            f"No supported documents found in '{folder_path}'. "
            f"Supported extensions: {', '.join(sorted(extensions or DEFAULT_EXTENSIONS))}"
        )

    output_path = build_output_path(folder_path, output_dir)
    write_inventory_csv(inventory, columns, output_path)
    file_count = sum(len(docs) for docs in inventory.values())
    return output_path, len(inventory), file_count
