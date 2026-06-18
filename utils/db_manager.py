import os
import sqlite3
import pandas as pd
from config import DB_PATH, CSV_PATH, config

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database with the necessary tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create employees table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        Employee_ID TEXT PRIMARY KEY,
        Employee_Name TEXT,
        Aadhaar_Number TEXT,
        PAN_Number TEXT,
        DOB TEXT,
        Last_Updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Create documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        Document_ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Employee_ID TEXT,
        Document_Type TEXT,
        File_Name TEXT,
        File_Path TEXT,
        Extracted_Text_Path TEXT,
        Processed_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (Employee_ID) REFERENCES employees (Employee_ID),
        UNIQUE(Employee_ID, File_Name)
    )
    """)
    
    conn.commit()
    conn.close()

def save_employee_record(emp_id, name, aadhaar, pan, dob):
    """
    Saves or updates an employee's master record.
    If fields are None or empty, it doesn't overwrite existing valid data in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if employee already exists
    cursor.execute("SELECT * FROM employees WHERE Employee_ID = ?", (emp_id,))
    existing = cursor.fetchone()
    
    if existing:
        # Merge values: only update if the new value is not None/empty
        updated_name = name if name else existing["Employee_Name"]
        updated_aadhaar = aadhaar if aadhaar else existing["Aadhaar_Number"]
        updated_pan = pan if pan else existing["PAN_Number"]
        updated_dob = dob if dob else existing["DOB"]
        
        cursor.execute("""
        UPDATE employees
        SET Employee_Name = ?, Aadhaar_Number = ?, PAN_Number = ?, DOB = ?, Last_Updated = CURRENT_TIMESTAMP
        WHERE Employee_ID = ?
        """, (updated_name, updated_aadhaar, updated_pan, updated_dob, emp_id))
    else:
        cursor.execute("""
        INSERT INTO employees (Employee_ID, Employee_Name, Aadhaar_Number, PAN_Number, DOB)
        VALUES (?, ?, ?, ?, ?)
        """, (emp_id, name, aadhaar, pan, dob))
        
    conn.commit()
    conn.close()

def save_document_record(emp_id, doc_type, file_name, file_path, extracted_text_path):
    """
    Saves or updates a processed document record.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO documents (Employee_ID, Document_Type, File_Name, File_Path, Extracted_Text_Path)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(Employee_ID, File_Name) DO UPDATE SET
        Document_Type = excluded.Document_Type,
        File_Path = excluded.File_Path,
        Extracted_Text_Path = excluded.Extracted_Text_Path,
        Processed_Date = CURRENT_TIMESTAMP
    """, (emp_id, doc_type, file_name, file_path, extracted_text_path))
    
    conn.commit()
    conn.close()

def get_all_employee_records_flat():
    """
    Retrieve flat synchronized employee document records for CSV exporting.
    """
    conn = get_db_connection()
    # SQL join to generate the exact structure requested by the user
    query = """
    SELECT 
        e.Employee_ID,
        e.Employee_Name,
        e.Aadhaar_Number,
        e.PAN_Number,
        e.DOB,
        d.Document_Type,
        d.File_Name,
        d.File_Path
    FROM employees e
    LEFT JOIN documents d ON e.Employee_ID = d.Employee_ID
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def sync_to_csv():
    """Export the database contents to the target employees.csv file."""
    df = get_all_employee_records_flat()
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    try:
        df.to_csv(CSV_PATH, index=False)
        print(f"Database successfully synchronized with CSV: {CSV_PATH}")
    except PermissionError:
        backup_path = CSV_PATH.replace(".csv", "_backup.csv")
        try:
            df.to_csv(backup_path, index=False)
            print(f"⚠️ Warning: Target CSV file '{CSV_PATH}' is currently locked (likely open in Excel). Saved database to backup instead: {backup_path}")
        except Exception as e:
            print(f"⚠️ Error: Could not synchronize with CSV. File is locked and backup failed: {e}")

def check_duplicates():
    """
    Identifies duplicate Aadhaar/PAN cards registered across different Employee IDs.
    Returns lists of warnings.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    warnings = []
    
    # 1. Check duplicate Aadhaar
    cursor.execute("""
    SELECT Aadhaar_Number, COUNT(DISTINCT Employee_ID) as id_count, GROUP_CONCAT(Employee_ID) as emp_ids
    FROM employees
    WHERE Aadhaar_Number IS NOT NULL AND Aadhaar_Number != ''
    GROUP BY Aadhaar_Number
    HAVING id_count > 1
    """)
    aadhaar_dupes = cursor.fetchall()
    for row in aadhaar_dupes:
        warnings.append({
            "field": "Aadhaar_Number",
            "value": row["Aadhaar_Number"],
            "employees": row["emp_ids"].split(","),
            "message": f"Duplicate Aadhaar Card {row['Aadhaar_Number']} found across employees: {row['emp_ids']}"
        })
        
    # 2. Check duplicate PAN
    cursor.execute("""
    SELECT PAN_Number, COUNT(DISTINCT Employee_ID) as id_count, GROUP_CONCAT(Employee_ID) as emp_ids
    FROM employees
    WHERE PAN_Number IS NOT NULL AND PAN_Number != ''
    GROUP BY PAN_Number
    HAVING id_count > 1
    """)
    pan_dupes = cursor.fetchall()
    for row in pan_dupes:
        warnings.append({
            "field": "PAN_Number",
            "value": row["PAN_Number"],
            "employees": row["emp_ids"].split(","),
            "message": f"Duplicate PAN Card {row['PAN_Number']} found across employees: {row['emp_ids']}"
        })
        
    conn.close()
    return warnings

def check_missing_documents():
    """
    Finds which employees are missing their required documents (e.g. Aadhaar, PAN)
    based on config settings.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    required_types = config.get("required_documents", ["aadhaar", "pan"])
    
    cursor.execute("SELECT Employee_ID, Employee_Name FROM employees")
    employees = cursor.fetchall()
    
    missing_alerts = []
    
    for emp in employees:
        emp_id = emp["Employee_ID"]
        emp_name = emp["Employee_Name"]
        
        # Get processed document types for this employee
        cursor.execute("SELECT DISTINCT LOWER(Document_Type) as doc_type FROM documents WHERE Employee_ID = ?", (emp_id,))
        docs = {row["doc_type"] for row in cursor.fetchall()}
        
        missing = []
        for req in required_types:
            if req.lower() not in docs:
                missing.append(req.capitalize())
                
        if missing:
            missing_alerts.append({
                "Employee_ID": emp_id,
                "Employee_Name": emp_name,
                "missing_documents": missing,
                "message": f"Employee {emp_id} ({emp_name}) is missing required documents: {', '.join(missing)}"
            })
            
    conn.close()
    return missing_alerts

def cleanup_orphaned_records():
    """
    Removes database records for files that no longer exist on disk.
    Also removes employees who have no remaining documents.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all documents
    cursor.execute("SELECT Document_ID, File_Path FROM documents")
    docs = cursor.fetchall()
    
    deleted_count = 0
    for doc in docs:
        if not os.path.exists(doc["File_Path"]):
            cursor.execute("DELETE FROM documents WHERE Document_ID = ?", (doc["Document_ID"],))
            deleted_count += 1
            
    if deleted_count > 0:
        print(f"🧹 Cleaned up {deleted_count} orphaned document records from database.")
        
    # Remove employees with no documents left
    cursor.execute("""
    DELETE FROM employees 
    WHERE Employee_ID NOT IN (SELECT DISTINCT Employee_ID FROM documents)
    """)
    
    conn.commit()
    conn.close()
