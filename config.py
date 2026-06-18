import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(BASE_DIR, "config.json")

# Default Tesseract binary path on Windows (if present)
TESSERACT_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if not os.path.exists(TESSERACT_DEFAULT):
    TESSERACT_DEFAULT = "tesseract"

DEFAULT_CONFIG = {
    "output_dir": os.path.join(BASE_DIR, "output"),
    "tesseract_cmd": TESSERACT_DEFAULT,
    "gdrive_folder_url": "",
    "required_documents": ["Aadhar Card", "PAN Card"],
    "document_aliases": {
        "Appointment Letter": [
            "appointment letter", "appointments letter", "appointment",
        ],
        "Educational Documents": [
            "educational documents", "educational document", "educational",
            "education document", "education documents",
            "marksheet", "mark sheet", "degree certificate", "degree", "certificate",
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
    },
}


def load_config():
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            for key, val in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = val
            return config
        except Exception as e:
            print(f"Error reading config: {e}. Using defaults.")
    return dict(DEFAULT_CONFIG)


def save_config(config):
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


config = load_config()
OUTPUT_DIR = config.get("output_dir", os.path.join(BASE_DIR, "output"))
os.makedirs(OUTPUT_DIR, exist_ok=True)
