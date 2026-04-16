import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def clean_ocr_text(text):
    if not text:
        return ""

    text = re.sub(r"[‘’“”|]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def ocr_image(path):
    img = Image.open(path).convert('L')
    img = img.resize((img.width * 2, img.height * 2))
    text = pytesseract.image_to_string(img, config='--oem 3 --psm 6')
    return clean_ocr_text(text)


def ocr_pdf(path):
    try:
        pages = convert_from_path(path, poppler_path=r"C:\poppler-25.12.0\Library\bin")
        full_text = ""

        for page in pages:
            page = page.convert('L')
            page = page.resize((page.width * 2, page.height * 2))
            text = pytesseract.image_to_string(page, config='--oem 3 --psm 6')
            full_text += text + "\n"

        return clean_ocr_text(full_text)
    except Exception as e:
        raise RuntimeError(f"Poppler/PDF OCR Error: {e}")


def extract_text(path):
    if path.lower().endswith(".pdf"):
        return ocr_pdf(path)
    return ocr_image(path)