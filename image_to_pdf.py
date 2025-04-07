from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import tempfile
import os
import re
import pytesseract
from io import BytesIO
import cv2
import numpy as np


# Set your Tesseract path if needed
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\yonil_n6n6nsl\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def preprocess_receipt_image(image):
    """Optimized preprocessing specifically for receipt images"""
    # Convert PIL Image to OpenCV format
    cv_image = np.array(image.convert('RGB'))
    cv_image = cv_image[:, :, ::-1].copy()  # RGB to BGR

    # Convert to grayscale
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    # Increase contrast with CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Adaptive thresholding - good for varying illumination
    binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)

    # Convert back to PIL
    return Image.fromarray(binary)


def extract_receipt_text(image):
    """Extract text from receipt with optimal OCR settings"""
    processed_img = preprocess_receipt_image(image)

    # Try Hebrew first
    try:
        text = pytesseract.image_to_string(processed_img, lang='heb', config='--psm 6')
        if text.strip():
            return text
    except Exception as e:
        print(f"Hebrew OCR error: {e}")

    # Fallback to English
    try:
        text = pytesseract.image_to_string(processed_img, config='--psm 6')
        if text.strip():
            return text
    except Exception as e:
        print(f"English OCR error: {e}")

    return "No text could be extracted"


def extract_store_and_date(text):
    """Extract store name and date from receipt text"""
    store_name = None
    date = None

    # Get all lines and filter out empty ones
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Store name is typically the first non-empty line
    if lines:
        store_name = lines[0]

    # Look for date pattern
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # DD/MM/YY or DD/MM/YYYY
        r'\d{1,2}\.\d{1,2}\.\d{2,4}',  # DD.MM.YY or DD.MM.YYYY
        r'\d{1,2}-\d{1,2}-\d{2,4}'  # DD-MM-YY or DD-MM-YYYY
    ]

    for pattern in date_patterns:
        for line in lines:
            match = re.search(pattern, line)
            if match:
                date = match.group(0)
                break
        if date:
            break

    return store_name, date


def image_to_pdf(image_file, max_width=5 * inch, max_height=7 * inch):
    """Convert receipt image to PDF with store name and date as filename"""
    # Open the image
    img = Image.open(image_file)

    # Extract text
    extracted_text = extract_receipt_text(img)

    # Extract store name and date
    store_name, date = extract_store_and_date(extracted_text)

    # Create filename
    if store_name and date:
        # Clean store name - limit to first word if too long
        store_name = store_name.split()[0] if len(store_name.split()) > 2 else store_name
        store_name = store_name[:15]  # Limit length
        filename = f"{store_name} - {date}"
    elif store_name:
        store_name = store_name.split()[0] if len(store_name.split()) > 2 else store_name
        store_name = store_name[:15]  # Limit length
        filename = store_name
    elif date:
        filename = f"Receipt - {date}"
    else:
        filename = "Receipt"

    # Clean filename (remove invalid characters)
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    filename = re.sub(r'\s+', " ", filename).strip()
    if not filename.strip():
        filename = "receipt"

    # Get image dimensions
    img_width, img_height = img.size

    # Calculate aspect ratio
    aspect = img_width / img_height

    # Determine dimensions to fit within max size while preserving aspect ratio
    if img_width > max_width or img_height > max_height:
        if img_width / max_width > img_height / max_height:
            # Width is the limiting factor
            new_width = max_width
            new_height = new_width / aspect
        else:
            # Height is the limiting factor
            new_height = max_height
            new_width = new_height * aspect
    else:
        new_width = img_width
        new_height = img_height

    # Create a BytesIO object for the PDF
    pdf_buffer = BytesIO()

    # Create PDF canvas (letter size: 8.5 x 11 inches)
    c = canvas.Canvas(pdf_buffer, pagesize=(8.5 * inch, 11 * inch))

    # Save image to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        img.save(tmp_file.name)
        tmp_filename = tmp_file.name

    # Calculate position to center the image on the page
    x_pos = (8.5 * inch - new_width) / 2
    y_pos = (11 * inch - new_height) / 2

    # Draw the image on the canvas
    c.drawImage(tmp_filename, x_pos, y_pos, width=new_width, height=new_height)

    # Add metadata to PDF
    if store_name:
        c.setTitle(store_name)
    if date:
        c.setSubject(f"Receipt - {date}")

    # Add small text overlay with information
    if store_name or date:
        c.setFont("Helvetica", 10)
        info_text = []
        if store_name:
            info_text.append(f"Store: {store_name}")
        if date:
            info_text.append(f"Date: {date}")

        if info_text:
            c.drawString(1 * inch, 1 * inch, " | ".join(info_text))

    # Save the PDF
    c.save()

    # Clean up temporary file
    os.unlink(tmp_filename)

    # Reset buffer position
    pdf_buffer.seek(0)

    return pdf_buffer, f"{filename}.pdf"

# Example usage:
# with open("receipt.jpg", "rb") as image_file:
#     pdf_buffer, filename = image_to_pdf(image_file)
#     with open(filename, "wb") as pdf_file:
#         pdf_file.write(pdf_buffer.getvalue())