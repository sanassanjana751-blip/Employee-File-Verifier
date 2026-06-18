import cv2
import numpy as np
from PIL import Image

def pil_to_cv2(pil_image):
    """Convert a PIL Image to a CV2 image (numpy array in BGR format)."""
    # Handle palette-based images or grayscale
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    open_cv_image = np.array(pil_image)
    # Convert RGB to BGR for OpenCV
    return open_cv_image[:, :, ::-1].copy()

def cv2_to_pil(cv2_image):
    """Convert a CV2 image (numpy array) to a PIL Image."""
    # Convert BGR to RGB
    rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_image)

def deskew(cv2_image):
    """
    Auto-detect the skew angle of the text and rotate the image to straighten it.
    """
    try:
        gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
        # Invert the image (black text on white background -> white text on black background)
        gray = cv2.bitwise_not(gray)
        
        # Threshold the image
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Find all non-zero points (text pixels)
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) == 0:
            return cv2_image
            
        # Compute the minimum area rectangle containing these points
        angle = cv2.minAreaRect(coords)[-1]
        
        # minAreaRect returns angle in range [-90, 0) or [0, 90] depending on OpenCV version.
        # We need to normalize it to correct the text alignment
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
            
        # If rotation angle is small or negligible, don't rotate
        if abs(angle) < 0.5 or abs(angle) > 45:
            return cv2_image
            
        # Rotate the image to deskew
        (h, w) = cv2_image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(cv2_image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated
    except Exception as e:
        print(f"Failed to deskew image: {e}")
        return cv2_image

def preprocess_image(pil_image, settings=None):
    """
    Applies a series of OpenCV preprocessing operations to a PIL Image.
    settings: dict containing booleans for which operations to apply.
    """
    if settings is None:
        settings = {
            "apply_grayscale": True,
            "apply_threshold": True,
            "apply_denoise": True,
            "apply_deskew": True,
            "apply_sharpen": True
        }
        
    # Convert to OpenCV image
    cv_img = pil_to_cv2(pil_image)
    
    # 1. Deskew (Rotation correction) - do this first before other modifications
    if settings.get("apply_deskew", True):
        cv_img = deskew(cv_img)
        
    # Convert to Grayscale
    if settings.get("apply_grayscale", True):
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    else:
        # Fallback if grayscale is disabled (not recommended for Tesseract)
        gray = cv_img.copy()
        
    # 2. Denoising / Noise Removal
    if settings.get("apply_denoise", True) and len(gray.shape) == 2:
        # Use Bilateral Filter to remove noise while keeping edges sharp
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        
    # 3. Sharpening
    if settings.get("apply_sharpen", True) and len(gray.shape) == 2:
        kernel = np.array([[-1,-1,-1], 
                           [-1, 9,-1], 
                           [-1,-1,-1]])
        gray = cv2.filter2D(gray, -1, kernel)
        
    # 4. Thresholding / Binarization (Otsu's Thresholding)
    if settings.get("apply_threshold", True) and len(gray.shape) == 2:
        # Otsu's thresholding automatically calculates the optimal threshold value
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
    # Convert back to PIL Image for PyTesseract
    if len(gray.shape) == 2:
        # Convert single channel grayscale/binary to PIL
        return Image.fromarray(gray)
    else:
        return cv2_to_pil(gray)
