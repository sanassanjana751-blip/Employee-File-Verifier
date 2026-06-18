import re

def clean_extracted_text(text):
    """
    Cleans up noisy text by normalizing whitespace, removing weird artifacts, 
    but retaining casing and lines.
    """
    if not text:
        return ""
    # Replace multiple spaces with single space, keep line breaks
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        cleaned = re.sub(r'\s+', ' ', line).strip()
        if cleaned:
            cleaned_lines.append(cleaned)
    return "\n".join(cleaned_lines)

def classify_document_type(text, file_name=""):
    """
    Determine the type of document based on text content keywords and filename.
    """
    text_lower = text.lower()
    fn_lower = file_name.lower()
    
    # 1. Aadhaar Card detection
    if (
        "aadhaar" in text_lower or 
        "aadhar" in text_lower or 
        "uidai" in text_lower or 
        "unique identification" in text_lower or 
        "identification authority" in text_lower or 
        "enrollment no" in text_lower or 
        "enrolment no" in text_lower
    ):
        return "Aadhaar"
    if "aadhaar" in fn_lower or "aadhar" in fn_lower:
        return "Aadhaar"
        
    # 2. PAN Card detection
    if "permanent account number" in text_lower or "income tax department" in text_lower or "pan card" in text_lower:
        return "PAN"
    if "pan" in fn_lower:
        return "PAN"
        
    # 3. Marksheet detection
    if "marksheet" in text_lower or "statement of marks" in text_lower or "grade card" in text_lower or "roll number" in text_lower or "marks sheet" in text_lower or "passing certificate" in text_lower:
        return "Marksheet"
    if "marksheet" in fn_lower or "marks" in fn_lower or "grade" in fn_lower or "result" in fn_lower:
        return "Marksheet"
        
    # 4. Salary Slip detection
    if "payslip" in text_lower or "salary slip" in text_lower or "pay slip" in text_lower or "earnings" in text_lower or "net pay" in text_lower:
        return "Salary Slip"
    if "payslip" in fn_lower or "salary" in fn_lower:
        return "Salary Slip"
        
    # 5. Passport detection
    if "passport" in text_lower or "republic of india" in text_lower or "passport no" in text_lower:
        return "Passport"
    if "passport" in fn_lower:
        return "Passport"
        
    return "Other Legal Document"

def extract_aadhaar(text):
    """
    Extract and clean Aadhaar Card number (12 digits, often spaced in 4-4-4).
    """
    # Regex: 12 digits, potentially separated by space or hyphen
    patterns = [
        r"\b\d{4}\s\d{4}\s\d{4}\b",  # Standard 12 digits spaced
        r"\b\d{12}\b",                # 12 digits continuous
        r"\b\d{4}-\d{4}-\d{4}\b"     # 12 digits hyphenated
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Clean it into standard 'XXXX XXXX XXXX' format
            digits = re.sub(r"\D", "", match.group(0))
            return f"{digits[0:4]} {digits[4:8]} {digits[8:12]}"
    return None

def extract_pan(text):
    """
    Extract and clean PAN Number (5 letters, 4 digits, 1 letter).
    """
    # Standard PAN Card regex pattern
    pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
    match = re.search(pattern, text.upper())  # Normalize to uppercase for regex matching
    if match:
        return match.group(0)
    
    # Sometimes OCR misinterprets O/0 or I/1. We can do a relaxed check if no direct match is found
    # But for strict HR databases, keeping standard is best. Let's stick to standard to avoid trash data.
    return None

def extract_dob(text):
    """
    Extract Date of Birth (DOB) from text.
    """
    # Common DOB labels
    dob_label_patterns = [
        r"dob\s*[:\-]?\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
        r"date of birth\s*[:\-]?\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
        r"birth\s*[:\-]?\s*(\d{2}[/\-]\d{2}[/\-]\d{4})"
    ]
    
    for pattern in dob_label_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
            
    # Generic Date finder
    date_patterns = [
        r"\b\d{2}[/\-]\d{2}[/\-]\d{4}\b",  # DD/MM/YYYY or DD-MM-YYYY
        r"\b\d{4}[/\-]\d{2}[/\-]\d{2}\b"   # YYYY-MM-DD
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            # Let's verify it looks like a valid DOB and not just some other date (like document issue date)
            # Typically DOB will appear near birth-related words.
            # But if that's all we have, we extract it.
            return match.group(0)
            
    return None

def extract_name(text, doc_type=""):
    """
    Heuristically extract the candidate's name based on document type and keywords.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    if not lines:
        return None

    # Helper function to clean names from common trash characters
    def clean_name_string(s):
        # Remove labels
        s = re.sub(r"(?i)^(name|candidate name|full name|employee name|name of candidate|shri|smt|mr|mrs|ms)[:.\-\s]+", "", s)
        # Keep only letters and spaces
        s = re.sub(r"[^a-zA-Z\s]", "", s)
        # Clean double spaces
        s = " ".join(s.split())
        return s if len(s) > 2 else ""

    # Strategy 1: Search for explicit labels
    name_labels = [
        r"(?i)\bname\s*[:\-]\s*([A-Za-z\s'\.]+)",
        r"(?i)\bcandidate's name\s*[:\-]?\s*([A-Za-z\s'\.]+)",
        r"(?i)\bcandidate name\s*[:\-]?\s*([A-Za-z\s'\.]+)",
        r"(?i)\bname of candidate\s*[:\-]?\s*([A-Za-z\s'\.]+)",
        r"(?i)\bname of the candidate\s*[:\-]?\s*([A-Za-z\s'\.]+)",
    ]
    for pattern in name_labels:
        for line in lines:
            match = re.search(pattern, line)
            if match:
                cleaned = clean_name_string(match.group(1))
                if cleaned:
                    return cleaned

    # Strategy 2: Specific Document Type Heuristics
    
    # 2A: PAN Card Heuristics
    if doc_type == "PAN" or "permanent account number" in text.lower():
        # In Indian PAN cards, the name is typically a standalone line in UPPERCASE
        # below "INCOME TAX DEPARTMENT" and "GOVT OF INDIA", and above the father's name.
        for idx, line in enumerate(lines):
            line_upper = line.upper()
            if "INCOME TAX" in line_upper or "GOVT" in line_upper or "DEPARTMENT" in line_upper:
                # Look at the next few lines (max 5)
                for next_idx in range(idx + 1, min(idx + 6, len(lines))):
                    candidate_line = lines[next_idx]
                    cleaned = clean_name_string(candidate_line)
                    # Candidate name must be uppercase, at least 2 words, and not a govt header/father's name
                    excluded_pan = ["GOVT", "GOVERNMENT", "INDIA", "INCOME", "TAX", "DEPARTMENT", "FATHER", "CARD", "SIGNATURE"]
                    if cleaned and candidate_line.isupper() and len(cleaned.split()) >= 2:
                        if not any(h in candidate_line.upper() for h in excluded_pan):
                            return cleaned

    # 2B: Aadhaar Card Heuristics
    if doc_type == "Aadhaar" or "unique identification" in text.lower():
        # In Aadhaar cards, the name is typically directly above the line containing "DOB" or "Year of Birth"
        for idx, line in enumerate(lines):
            if "dob" in line.lower() or "year of birth" in line.lower() or "yob" in line.lower() or "birth" in line.lower() or re.search(r"\d{2}[/\-]\d{2}[/\-]\d{4}", line):
                # The line above is usually the name
                if idx > 0:
                    candidate_line = lines[idx - 1]
                    # Filter out government headers
                    if "government" not in candidate_line.lower() and "india" not in candidate_line.lower() and "uidai" not in candidate_line.lower():
                        cleaned = clean_name_string(candidate_line)
                        if cleaned:
                            return cleaned

    # Strategy 3: Fallback general heuristic
    # Look for the first line that looks like a name (only alphabetical words, 2-4 words long, capitalized)
    for line in lines[:10]:  # Check first 10 lines
        line_clean = clean_name_string(line)
        if line_clean and 2 <= len(line_clean.split()) <= 4:
            # Exclude known headers and metadata words
            line_lower = line.lower()
            excluded_words = [
                "government", "india", "department", "board", "secondary", 
                "examination", "marksheet", "certificate", "roll",
                "authority", "identification", "unique", "tique", 
                "enrolment", "enrollment", "national", "signature", 
                "address", "number", "issue", "date"
            ]
            if not any(word in line_lower for word in excluded_words):
                return line_clean

    return None

def extract_metadata(text, file_name="", doc_type_override=None):
    """
    Extracts all fields (Aadhaar, PAN, DOB, Name, Document Type) from raw text.
    """
    cleaned_text = clean_extracted_text(text)
    
    # Classify document type
    doc_type = doc_type_override if doc_type_override else classify_document_type(cleaned_text, file_name)
    
    # Extract structural fields
    aadhaar_num = extract_aadhaar(cleaned_text)
    pan_num = extract_pan(cleaned_text)
    dob = extract_dob(cleaned_text)
    name = extract_name(cleaned_text, doc_type)
    
    return {
        "Employee_Name": name,
        "Aadhaar_Number": aadhaar_num,
        "PAN_Number": pan_num,
        "DOB": dob,
        "Document_Type": doc_type
    }
