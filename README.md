# 📋 Employee File Verifier

A local, lightweight tool designed for college HR departments to quickly audit employee documents. It scans folders/files, matches document types using configurable naming aliases (no OCR, no cloud access needed), and generates a simple **Yes/No** compliance spreadsheet.

---

## 🚀 Quick Start Guide

Follow these simple steps to run the tool after importing the project:

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Install Dependencies (For Dashboard UI)
Open your terminal (PowerShell/CMD) and install the required visualization libraries:
```powershell
pip install streamlit pandas
```

### 3. Run the Project

You can interact with this tool in two ways:

#### Option A: Interactive Web Dashboard (Recommended)
Start the web-based operation portal, which automatically opens in your default browser (usually at `http://localhost:8501`):
```powershell
streamlit run dashboard.py
```
*Note: If `streamlit` is not recognized, you can run:*
```powershell
python -m streamlit run dashboard.py
```

#### Option B: Command Line Interface (CLI)
Run the script by directly passing the folder path of the employee documents:
```powershell
python main.py "C:\path\to\your\employee\folder"
```
Or run the script without arguments to be prompted for the folder path:
```powershell
python main.py
```

---

## 📂 Supported Folder Layouts

The tool automatically detects files using either of the following structures:

### Structure 1: One folder per employee
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

### Structure 2: All files in a single flat folder
```
MyEmployees/
├── Aditi Sarang - Aadhar Card.pdf
├── Aditi Sarang - PAN Card.pdf
└── Rajesh Kumar - Joining Letter.pdf
```

> **💡 Filename Tip:** File names are matched case-insensitively. Name order does not matter (e.g., `Aditi Sarang - Aadhar Card.pdf` and `Aadhar Card - Aditi Sarang.pdf` both work perfectly).

---

## 📊 Sample Output Report

The scanner writes a CSV report into the `output/` directory, formatted with UTF-8 with BOM for compatibility with Microsoft Excel:

| Employee Code | Employee Name | Appointment Letter | Educational Documents | Aadhar Card | PAN Card | ... | Missing Docs |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Yes | Aditi Sarang | Yes | No | Yes | Yes | ... | Educational Documents, DOJ, Department |
| Yes | Rajesh Kumar | No | Yes | Yes | Yes | ... | Appointment Letter, Experience Letter |

---

## ⚙️ Customizing Document Types & Aliases

You can easily adjust what documents the system looks for by editing [config.json](file:///c:/Users/Lenovo/Desktop/EmployeeOCR/config.json). 

Each key represents the column name in the output spreadsheet, and the list values are the keywords (aliases) the program searches for in the filenames:
```json
"document_aliases": {
    "Aadhar Card": ["aadhar card", "aadhaar card", "adhar", "aadhar"],
    "PAN Card": ["pan card", "pan"],
    "Bonafide Certificate": ["bonafide", "bonafide certificate"]
}
```

---

## 🛠️ Project Structure
* `main.py` - Core CLI scanner.
* `dashboard.py` - Streamlit interactive dashboard UI.
* `config.py` / `config.json` - Custom settings & document name matching criteria.
* `output/` - Location of all generated checklist report CSVs.
