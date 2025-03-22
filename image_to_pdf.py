from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import tempfile
import os
from io import BytesIO
import pytesseract
import re
from datetime import datetime
import cv2
import numpy as np

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\yonil_n6n6nsl\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


def preprocess_receipt_image(image):
    """Advanced preprocessing specifically for Hebrew receipts on thermal paper"""
    # Convert PIL Image to OpenCV format
    cv_image = np.array(image.convert('RGB'))
    cv_image = cv_image[:, :, ::-1].copy()  # RGB to BGR

    # Convert to grayscale
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    # Increase contrast with CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Bilateral filtering to preserve edges while reducing noise
    filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)

    # Otsu's thresholding for better binarization
    _, binary = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological operations to clean up the image
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # Convert back to PIL
    result_img = Image.fromarray(opening)

    # Further enhance with PIL
    enhancer = ImageEnhance.Contrast(result_img)
    result_img = enhancer.enhance(2.0)

    # Sharpen to make text clearer
    result_img = result_img.filter(ImageFilter.SHARPEN)

    return result_img


def extract_hebrew_receipt_text(image):
    """Extract text from Hebrew receipt with multiple processing approaches"""
    processed_img = preprocess_receipt_image(image)

    # Save processed image for debugging if needed
    # processed_img.save("processed_receipt.png")

    # Try different OCR configurations and select best result
    results = []

    # Configuration options
    configs = [
        # PSM 6: Assume a single uniform block of text
        '--psm 6 --oem 3',
        # PSM 4: Assume a single column of text of variable sizes
        '--psm 4 --oem 3',
        # PSM 3: Fully automatic page segmentation, but no OSD (default)
        '--psm 3 --oem 3',
        # Try with orientation detection
        '--psm 0 --oem 3'
    ]

    # Languages to try
    langs = ['heb', 'heb+eng']

    try:
        for config in configs:
            for lang in langs:
                try:
                    text = pytesseract.image_to_string(processed_img, lang=lang, config=config)
                    # Only add non-empty results
                    if text.strip():
                        results.append(text)
                except Exception as e:
                    print(f"Error with config {config}, lang {lang}: {e}")

        # If Hebrew fails, try with just English
        if not results:
            for config in configs:
                try:
                    text = pytesseract.image_to_string(processed_img, config=config)
                    if text.strip():
                        results.append(text)
                except Exception as e:
                    print(f"Error with English OCR, config {config}: {e}")
    except Exception as e:
        print(f"Error during OCR processing: {e}")

    # Return the longest result, which is likely the most complete
    if results:
        # Sort by length (descending)
        results.sort(key=len, reverse=True)

        # Display all results for debugging
        for i, text in enumerate(results):
            print(f"\nResult {i + 1} (length: {len(text)}):")
            print(text[:200] + "..." if len(text) > 200 else text)

        return results[0]
    else:
        return "No text could be extracted"


def extract_receipt_info_hebrew(text):
    """Extract key information from Hebrew receipt text"""
    info = {
        'title': "קבלה",  # Default receipt title in Hebrew
        'date': None,
        'time': None,
        'total': None,
        'merchant': None,
        'items': []
    }

    # Date patterns for Israeli receipts (both Hebrew and standard formats)
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # 22/01/25
        r'\d{2}/\d{2}/\d{2,4}',  # Match both DD/MM/YY and DD/MM/YYYY
        r'\d{1,2}\.\d{1,2}\.\d{2,4}',  # DD.MM.YYYY
        r'\d{1,2}-\d{1,2}-\d{2,4}'  # DD-MM-YYYY
    ]

    # Time patterns
    time_patterns = [
        r'\d{1,2}:\d{2}',  # HH:MM
    ]

    # Total amount patterns in Hebrew receipts
    total_patterns = [
        r'סה"כ\s*\d+\.\d+',  # "סה"כ" followed by number with decimal
        r'סה"כ\s*\d+',  # "סה"כ" followed by whole number
        r'סך הכל\s*\d+\.\d+',  # "סך הכל" followed by number with decimal
        r'סך הכל\s*\d+',  # "סך הכל" followed by whole number
        r'לתשלום\s*\d+\.\d+',  # "לתשלום" followed by number with decimal
        r'לתשלום\s*\d+',  # "לתשלום" followed by whole number
        r'ש"ח\s*\d+\.\d+',  # "ש"ח" followed by number
        r'\d+\.\d+\s*ש"ח'  # Number followed by "ש"ח"
    ]

    # Common merchant patterns in header of Israeli receipts
    merchant_patterns = [
        r'פז',  # Paz gas station
        r'דלק',  # Delek gas station
        r'סונול',  # Sonol gas station
        r'בע"מ'  # Ltd. suffix for companies
    ]

    # Extract date
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            info['date'] = matches[0]
            break

    # Extract time
    for pattern in time_patterns:
        matches = re.findall(pattern, text)
        if matches:
            info['time'] = matches[0]
            break

    # Extract total amount
    for pattern in total_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Extract just the numerical part
            number_match = re.search(r'\d+\.?\d*', matches[0])
            if number_match:
                info['total'] = number_match.group(0)
                break

    # Try to identify merchant from first few lines
    lines = text.split('\n')
    first_lines = [line.strip() for line in lines[:5] if line.strip()]

    # Look for common merchant indicators
    for line in first_lines:
        for pattern in merchant_patterns:
            if re.search(pattern, line):
                info['merchant'] = line
                break
        if info['merchant']:
            break

    # If we still don't have a merchant, use first non-empty line
    if not info['merchant'] and first_lines:
        info['merchant'] = first_lines[0]

    # Generate title based on available information
    if info['merchant'] and info['date']:
        info['title'] = f"{info['merchant']} - {info['date']}"
    elif info['merchant']:
        info['title'] = info['merchant']
    elif info['date']:
        info['title'] = f"קבלה - {info['date']}"

    # Look for items in the middle of the receipt
    # This is a simplified approach - a more complex analysis would be needed for proper line item extraction
    item_lines = []
    reading_items = False

    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue

        # Common indicators that we're in the items section (quantities, prices)
        if re.search(r'\d+\.\d+', line) and not any(pat in line for pat in ['סה"כ', 'סך הכל', 'לתשלום']):
            reading_items = True
            item_lines.append(line)
        elif reading_items and line:
            item_lines.append(line)

    info['items'] = item_lines

    return info


def image_to_pdf(uploaded_file, max_width=5 * inch, max_height=7 * inch):
    """Convert Hebrew receipt image to PDF with enhanced OCR"""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        # Save the uploaded file to the temporary file
        img = Image.open(uploaded_file)
        img.save(tmp_file.name)
        tmp_filename = tmp_file.name

    # Extract text with advanced processing
    extracted_text = extract_hebrew_receipt_text(img)

    # Print extracted text for debugging
    print("Final extracted text from image:")
    print(extracted_text)

    # Extract structured information
    receipt_info = extract_receipt_info_hebrew(extracted_text)

    # Create filename
    if receipt_info['title']:
        filename = receipt_info['title']
    else:
        # Fallback filename with date
        current_date = datetime.now().strftime("%d-%m-%y")
        filename = f"קבלה - {current_date}"

    # Clean filename (remove invalid characters)
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    if len(filename.strip()) == 0:
        filename = "receipt"

    # Get image dimensions
    img_width, img_height = img.size

    # Calculate aspect ratio
    aspect = img_width / img_height

    # Determine dimensions to fit within max_width and max_height while preserving aspect ratio
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

    # Calculate position to center the image on the page
    x_pos = (8.5 * inch - new_width) / 2
    y_pos = (11 * inch - new_height) / 2

    # Draw the image on the canvas
    c.drawImage(tmp_filename, x_pos, y_pos, width=new_width, height=new_height)

    # Add metadata to PDF
    if receipt_info['merchant']:
        c.setTitle(receipt_info['merchant'])
    if receipt_info['date']:
        c.setSubject(f"Receipt - {receipt_info['date']}")

    # Save the PDF
    c.save()

    # Clean up temporary file
    os.unlink(tmp_filename)

    # Reset buffer position
    pdf_buffer.seek(0)

    return pdf_buffer, filename + ".pdf"
    # receipt_info