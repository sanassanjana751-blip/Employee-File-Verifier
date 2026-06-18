import pytesseract
from PIL import Image
from config import config
from utils.image_preprocessor import preprocess_image

# Set Tesseract executable path from config
tesseract_cmd = config.get("tesseract_cmd", "tesseract")
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

def is_ocr_available():
    """
    Check if the Tesseract binary is accessible and working.
    Returns True if Tesseract responds, False otherwise.
    """
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def ocr_single_image(pil_image, preprocess=True):
    """
    Run Tesseract OCR on a single PIL Image.
    Optionally applies OpenCV preprocessing before OCR.
    """
    if not is_ocr_available():
        error_msg = (
            "OCR Error: Tesseract OCR is not installed or the executable path in config.json is invalid.\n"
            f"Currently configured path: '{pytesseract.pytesseract.tesseract_cmd}'\n"
            "Please install Tesseract OCR and configure the path, or process text-based PDFs only."
        )
        print(error_msg)
        raise RuntimeError(error_msg)
        
    try:
        # Preprocess if requested
        if preprocess:
            processed_img = preprocess_image(pil_image, config.get("preprocessing"))
        else:
            processed_img = pil_image
            
        # Run OCR with English language
        text = pytesseract.image_to_string(processed_img, lang="eng")
        return text
    except Exception as e:
        print(f"Error during OCR execution: {e}")
        return ""

def ocr_multi_images(images, preprocess=True):
    """
    Run OCR on a list of PIL Images (e.g., pages of a scanned PDF).
    """
    extracted_texts = []
    for i, img in enumerate(images):
        print(f"Running OCR on page {i+1}/{len(images)}...")
        page_text = ocr_single_image(img, preprocess=preprocess)
        extracted_texts.append(f"--- Page {i+1} ---\n{page_text}")
    return "\n".join(extracted_texts)
