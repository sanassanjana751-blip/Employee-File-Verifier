import os
import io
import fitz  # PyMuPDF
from PIL import Image

def is_text_pdf(pdf_path, text_threshold=50):
    """
    Check if a PDF file contains embedded searchable text.
    Returns True if the extracted text is longer than the threshold, False otherwise.
    """
    try:
        doc = fitz.open(pdf_path)
        total_text_length = 0
        for page in doc:
            text = page.get_text()
            # Clean up whitespace
            text = "".join(text.split())
            total_text_length += len(text)
            if total_text_length > text_threshold:
                doc.close()
                return True
        doc.close()
        return False
    except Exception as e:
        print(f"Error checking PDF type for {pdf_path}: {e}")
        return False

def extract_text_directly(pdf_path):
    """
    Extract text directly from a text-based PDF.
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = []
        for i, page in enumerate(doc):
            page_text = page.get_text()
            full_text.append(f"--- Page {i+1} ---\n{page_text}")
        doc.close()
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error direct-extracting text from {pdf_path}: {e}")
        return ""

def pdf_to_images(pdf_path, zoom_factor=3.0):
    """
    Convert a PDF's pages into PIL Images using PyMuPDF.
    This replaces pdf2image (which relies on Poppler) for seamless Windows support.
    
    zoom_factor: multiplier for scaling the resolution (e.g., 3.0 increases 72 dpi to 216 dpi)
    """
    try:
        doc = fitz.open(pdf_path)
        images = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Zoom matrix for higher resolution (DPI scaling)
            mat = fitz.Matrix(zoom_factor, zoom_factor)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert pixmap to PNG bytes, then load as PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            # Make sure it's loaded in memory fully before closing doc
            img.load()
            images.append(img)
            
        doc.close()
        return images
    except Exception as e:
        print(f"Error converting PDF {pdf_path} to images: {e}")
        return []
