<div align="center">

#  Recipe Reader / Writer

**Turn scanned cookbook pages into a searchable, editable recipe library.**

![Python](https://img.shields.io/badge/Python-3.9-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?logo=sqlite&logoColor=white)
![Tesseract](https://img.shields.io/badge/OCR-Tesseract-5C2D91)
![Stars](https://img.shields.io/github/stars/RibMc95/Recipe-RW?style=social)

[Features](#features) · [Requirements](#requirements) · [Setup](#setup) · [Usage](#usage) · [How it works](#how-it-works)

</div>

---

## Features 

- Open scanned cookbook **PDFs** and page through them
-  **Zoom** and scroll any page
-  **OCR** a page (Tesseract) and auto-split the text into ingredients & steps
-  **Checklist-style** ingredient and step editing — tick items off while you cook
-  **Save** recipes to a local SQLite database (full create / read / update / delete)
-  **Search** your saved recipes by title and reload them

## Requirements

- **Python 3.9+**
- **Tesseract-OCR** installed on your machine
  (Windows installer: <https://github.com/UB-Mannheim/tesseract/wiki>)

## Setup

```bash
# 1. create & activate a virtual environment
py -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell

# 2. install the Python dependencies
pip install -r requirements.txt
```

If `tesseract` isn't on your PATH, the app points at the default install location
(`C:\Program Files\Tesseract-OCR\tesseract.exe`) in `recipe_rw/ocr.py`.

## Usage

```bash
python -m recipe_rw
```

Open a cookbook PDF, navigate to a recipe, click **OCR**, tidy up the auto-split
ingredients and steps, fill in the title, and hit **Save Recipe**. Search for it
any time and double-click to reload.

## How it works

```
PDF page  ──►  render to image   (pdf.py,  PyMuPDF)
          ──►  image → text      (ocr.py,  Tesseract)
          ──►  split ingredients / steps   (ocr.py heuristics)
          ──►  Recipe object     (models.py, dataclass)
          ──►  save / search     (db.py,   SQLite)
                 ▲
          app.py (PySide6) ties the UI to all of the above
```

## Tech stack

| Concern | Library |
|---|---|
| Desktop GUI | PySide6 (Qt) |
| PDF rendering | PyMuPDF |
| OCR | pytesseract + Tesseract |
| Images | Pillow |
| Storage & search | SQLite (built into Python) |
