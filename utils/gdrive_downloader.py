import os
import re
import zipfile
import gdown
from config import DOCUMENTS_DIR, TEMP_DIR, config, save_config

def extract_gdrive_id(url):
    """
    Extracts the Google Drive file or folder ID and type from a URL.
    """
    if not url:
        return None, None
        
    # Match file URL: /file/d/<id>/
    file_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if file_match:
        return file_match.group(1), "file"
        
    # Match folder URL: /folders/<id>
    folder_match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url)
    if folder_match:
        return folder_match.group(1), "folder"
        
    # Check if the input is already just a raw Google Drive ID
    if re.match(r'^[a-zA-Z0-9_-]{28,45}$', url.strip()):
        return url.strip(), "file"
        
    return None, None

def download_from_gdrive(folder_url=None):
    """
    Downloads documents from Google Drive.
    Supports both Google Drive folders and shared ZIP files.
    """
    if not folder_url:
        folder_url = config.get("gdrive_folder_url")
        
    if not folder_url:
        return False, "No Google Drive folder or ZIP URL found in configuration."
        
    # Persist the URL in the configuration if it has changed
    if folder_url != config.get("gdrive_folder_url"):
        config["gdrive_folder_url"] = folder_url
        save_config(config)
        
    gdrive_id, gdrive_type = extract_gdrive_id(folder_url)
    
    if not gdrive_id:
        return False, "Invalid Google Drive URL. Ensure it contains a valid folder or file ID."
        
    import shutil
    try:
        # Clear existing documents to avoid mixing old/mock files with new GDrive download
        if os.path.exists(DOCUMENTS_DIR):
            print("🧹 Clearing existing local documents folder...")
            for item in os.listdir(DOCUMENTS_DIR):
                item_path = os.path.join(DOCUMENTS_DIR, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception as e:
                    print(f"   ⚠️ Warning: Could not remove {item_path}: {e}")
                    
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        if gdrive_type == "folder":
            print(f"📁 Attempting to download Google Drive folder ID: {gdrive_id}")
            try:
                gdown.download_folder(
                    url=folder_url,
                    output=DOCUMENTS_DIR,
                    quiet=False,
                    use_cookies=False
                )
                return True, "Google Drive folder sync completed successfully!"
            except Exception as e:
                error_str = str(e)
                # Check for common Google Drive API block (401 code)
                if "401" in error_str or "permission" in error_str.lower() or "Failed to retrieve folder" in error_str:
                    return False, (
                        "Google Drive Folder Access Blocked (401 Unauthorized).\n\n"
                        "Google has restricted anonymous folder listings. To resolve this:\n"
                        "1. Zip your 'documents' folder containing employee subfolders locally.\n"
                        "2. Upload the ZIP file to Google Drive.\n"
                        "3. Share the ZIP file as 'Anyone with the link can view'.\n"
                        "4. Paste the ZIP file's sharing link here to sync seamlessly."
                    )
                raise e
                
        elif gdrive_type == "file":
            print(f"📦 Attempting to download Google Drive ZIP/File ID: {gdrive_id}")
            zip_temp_path = os.path.join(TEMP_DIR, "gdrive_download.zip")
            
            # Download file
            gdown.download(id=gdrive_id, output=zip_temp_path, quiet=False)
            
            # Verify if it is a ZIP archive and extract it
            if zipfile.is_zipfile(zip_temp_path):
                print("   -> Extracting ZIP contents to documents directory...")
                with zipfile.ZipFile(zip_temp_path, 'r') as zip_ref:
                    zip_ref.extractall(DOCUMENTS_DIR)
                
                # Cleanup temp ZIP
                try:
                    os.remove(zip_temp_path)
                except Exception:
                    pass
                return True, "Google Drive ZIP sync completed and extracted successfully!"
            else:
                return False, "Downloaded file from Google Drive is not a valid ZIP file. Please upload a ZIP archive."
                
    except Exception as e:
        return False, f"An unexpected error occurred during Google Drive download: {str(e)}"
