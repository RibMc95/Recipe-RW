import pytesseract
import re
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image
UNIT_WORDS = {
    "cup", "cups", "tablespoon", "tablespoons", "tbsp", "teaspoon", "teaspoons",
    "tsp", "oz", "ounce", "ounces", "pound", "pounds", "lb", "lbs", "gram",
    "grams", "ml", "clove", "cloves", "pinch", "can", "cans",
}

def image_to_text(pix):
    """fitz pixmap → Pillow image → text."""
    mode = "RGBA" if pix.alpha else "RGB"                      # transparency or not
    image = Image.frombytes(mode, (pix.width, pix.height), pix.samples)  # raw pixels → PIL image
    return pytesseract.image_to_string(image)                 # PIL image → text


def image_to_text_from_file(file_path): 
    return pytesseract.image_to_string(file_path)

def looks_like_ingredient(line):
    """Guess whether one line is an ingredient (vs a step)."""
    words = line.lower().split()
    if not words:
        return False
    # signal 1: starts with a quantity — a digit or a fraction glyph
    starts_with_qty = bool(re.match(r"^\s*(½|¼|¾|⅓|⅔|\d)", line))
    # signal 2: a measurement word appears near the start
    has_unit = any(w.strip(",.") in UNIT_WORDS for w in words[:3])
    # ingredients are SHORT; long lines are almost always steps
    short = len(words) <= 8
    return (starts_with_qty or has_unit) and short

def parse_recipe_text(text):
    """Split raw OCR text into (ingredients, steps) lists using heuristics."""
    ingredients, steps = [], []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:                 # skip blank lines
            continue
        if looks_like_ingredient(line):
            ingredients.append(line)
        else:
            steps.append(line)
    return ingredients, steps