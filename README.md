# Employee File Verifier

A simple local tool for college HR: point it at a folder of employee files, and it builds a spreadsheet showing which documents each employee has (**yes** / **no**). It uses **file and folder names only** — no Google Drive, no OCR, no extra setup.

---

## What it does

1. You provide a folder path (all employee files for one batch/dept can live there).
2. The program reads each file name (and subfolder names if files are grouped per employee).
3. It checks these document types: Employee Code, Appointment Letter, Educational Documents, Experience Letter, Increment Letter, Aadhar Card, PAN Card, DOJ, Designation, Department, Employee Category.
4. It writes a CSV in `output/` named after that folder, for example:
   `Teaching_Staff_document_inventory_20260603_143022.csv`

| Employee Code | Employee Name | Appointment Letter | Educational Documents | Experience Letter | Increment Letter | Aadhar Card | PAN Card | DOJ | Designation | Department | Employee Category | Missing Docs |
|---------------|---------------|--------------------|-----------------------|-------------------|------------------|-------------|----------|-----|-------------|------------|-------------------|--------------|
| Yes           | Aditi Sarang  | Yes                | No                    | Yes               | No               | Yes         | Yes      | No  | No          | No         | No                | Educational Documents, Increment Letter, DOJ, Designation, Department, Employee Category |

Each document column shows **Yes** or **No**. The last column **Missing Docs** lists document types marked **No** (comma-separated).

---

## Folder layouts supported

**Option A — one folder per employee**

```
MyEmployees/
├── Aditi Sarang/
│   ├── Aditi Sarang - Aadhar Card.pdf
│   ├── Aditi Sarang - PAN Card.pdf
│   └── Offer Letter - Aditi Sarang.pdf
└── Rajesh Kumar/
    ├── aadhaar.pdf
    └── pan card.pdf
```

**Option B — all files in one folder (descriptive names)**

```
MyEmployees/
├── Aditi Sarang - Aadhar Card.pdf
├── Aditi Sarang - PAN Card.pdf
└── Rajesh Kumar - Joining Letter.pdf
```

Clear names like `Employee Name - Document Type.pdf` work best.

**Name order does not matter** — the program finds the document type and employee name anywhere in the filename, for example:

- `Aditi Sarang - Aadhar Card.pdf`
- `Aadhar Card - Aditi Sarang.pdf`
- `Aditi Sarang_Aadhar Card.pdf`
- `Joining Letter | Rajesh Kumar.pdf`

---

## How to run

### Option 1: Run via Command Line (CLI)

Run the script by passing the folder path containing the employee documents:

```powershell
cd C:\Users\Lenovo\Desktop\EmployeeOCR
python main.py "C:\path\to\your\employee\folder"
```

Or run without arguments and paste the path when prompted:

```powershell
python main.py
```

Optional: custom output directory:

```powershell
python main.py "D:\HR\Records\2024" -o "D:\HR\Reports"
```

### Option 2: Run via Streamlit Dashboard (UI)

First, make sure the dashboard dependencies are installed:

```powershell
pip install streamlit pandas
```

Then start the interactive web-based operation portal:

```powershell
streamlit run dashboard.py
```

If the `streamlit` command is not in your system path, you can also run:

```powershell
python -m streamlit run dashboard.py
```

This will automatically launch the dashboard in your default browser (usually at `http://localhost:8501`). The portal allows you to scan folders, filter compliant/non-compliant employees, analyze missing document frequencies, and inspect folders for individual employees.

Open any generated CSV in Excel — it uses UTF-8 with BOM for correct Indian names.

---

## Custom document types

Edit `document_aliases` in `config.json`. Each key is a **column name**; the list values are **substrings** matched in file names (case-insensitive).

```json
"Bonafide Certificate": ["bonafide", "bonafide certificate"]
```

---

## Requirements

- Python 3.10+
- Standard library only for the core CLI scanner (`main.py`).
- **Dashboard UI Dependencies**: `streamlit`, `pandas` (install via `pip install streamlit pandas`).

Legacy OCR, Google Drive, and SQLite modules remain in `utils/` but are not used by the active inventory tool or dashboard.
