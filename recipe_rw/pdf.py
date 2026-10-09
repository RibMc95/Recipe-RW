import fitz

import fitz

def open_pdf(path):
    return fitz.open(path)          # returns a Document you pass to render_page

def render_page(doc, page_number, zoom=2.0):
    page = doc[page_number]
    matrix = fitz.Matrix(zoom, zoom)
    return page.get_pixmap(matrix=matrix)
