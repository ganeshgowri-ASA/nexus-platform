"""OCR utility functions"""
import os
import hashlib
from pathlib import Path
from typing import Optional
from PIL import Image
import io


def validate_image_file(file_content: bytes, filename: str) -> bool:
    """Validate if file is a valid image"""
    try:
        image = Image.open(io.BytesIO(file_content))
        image.verify()
        return True
    except Exception:
        return False


def get_file_hash(content: bytes) -> str:
    """Generate SHA256 hash of file content"""
    return hashlib.sha256(content).hexdigest()


def ensure_upload_dir(upload_dir: str) -> Path:
    """Ensure upload directory exists"""
    path = Path(upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_uploaded_file(file_content: bytes, filename: str, upload_dir: str) -> str:
    """Save uploaded file and return path"""
    upload_path = ensure_upload_dir(upload_dir)
    file_hash = get_file_hash(file_content)

    # Create unique filename
    file_ext = Path(filename).suffix
    unique_filename = f"{file_hash}{file_ext}"
    file_path = upload_path / unique_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)

    return str(file_path)


def preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocess image for better OCR results"""
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Enhance contrast
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)

    return image


def is_handwriting(text: str, confidence: float) -> bool:
    """Simple heuristic to detect if text might be handwriting"""
    # This is a placeholder - real implementation would use ML model
    # For now, low confidence with irregular spacing might indicate handwriting
    return confidence < 0.7


def extract_text_from_pdf_page(pdf_path: str, page_num: int) -> Image.Image:
    """Extract image from PDF page for OCR"""
    from pdf2image import convert_from_path

    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
    return images[0] if images else None


def calculate_confidence_score(results: dict) -> float:
    """Calculate overall confidence score from OCR results"""
    # Implementation depends on OCR engine response format
    if 'confidence' in results:
        return results['confidence']
    return 0.0
