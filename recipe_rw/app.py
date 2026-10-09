from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QScrollArea,)
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLineEdit, QFormLayout, QTextEdit, QMessageBox

from recipe_rw import pdf
from recipe_rw.models import Recipe
from recipe_rw.ocr import image_to_text, parse_recipe_text
from recipe_rw.db import init_db, save_recipe, search_recipes, get_recipes, update_recipe, delete_recipe

# function to convert a PyMuPDF pixmap to a QPixmap for display in a QLabel
def pixmap_to_qpixmap(pix):
    """Turn a PyMuPDF pixmap into a Qt QPixmap a QLabel can display."""
    fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
    image = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
    return QPixmap.fromImage(image)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()                       # run QMainWindow's own setup first — REQUIRED
        self.setWindowTitle("Recipe Reader / Writer")
        self.resize(900, 650)

        # --- RECIPE EDIT FIELDS ---
        self.title_edit       = QLineEdit()
        self.source_edit      = QLineEdit()
        self.servings_edit    = QLineEdit()
        self.tags_edit        = QLineEdit()
        self.ingredients_edit = QTextEdit()
        self.steps_edit       = QTextEdit()
        self.current_id = None     

        # --- RECIPE FORM LAYOUT ---
        form = QFormLayout()
        form.addRow("Title:",       self.title_edit)
        form.addRow("Source:",      self.source_edit)
        form.addRow("Servings:",    self.servings_edit)
        form.addRow("Tags:",        self.tags_edit)
        form.addRow("Ingredients:", self.ingredients_edit)
        form.addRow("Steps:",       self.steps_edit)

        # --- STATE: the things we must remember between clicks ---
        self.doc = None            # the open PDF (None = nothing open yet)
        self.page_number = 0       # which page we're viewing
        self.zoom = 2.0            # default zoom level for the PDF rendering
        self.current_id = None     # None = new recipe; an int = editing that row

        # --- WIDGETS ---
        self.heading = QLabel("No PDF open yet")
        self.image_label = QLabel()            # the page image will go here
        open_button = QPushButton("Open PDF")
        prev_button = QPushButton("Prev")
        next_button = QPushButton("Next")
        ocr_button = QPushButton("OCR")

        # --- WIRING: connect each button to a method below ---
        open_button.clicked.connect(self.open_pdf)
        prev_button.clicked.connect(self.prev_page)
        next_button.clicked.connect(self.next_page)
        ocr_button.clicked.connect(self.ocr_page)

        # --- ZOOM BUTTONS ---
        zoom_in_button = QPushButton("Zoom +")
        zoom_out_button = QPushButton("Zoom -")
        zoom_in_button.clicked.connect(self.zoom_in)
        zoom_out_button.clicked.connect(self.zoom_out)

        # --- BUTTON ROW ---
        button_row = QHBoxLayout()
        for b in (open_button, prev_button, next_button, zoom_in_button, zoom_out_button, ocr_button):
            button_row.addWidget(b)

        # --- SCROLL AREA: make the image scrollable ---
        scroll = QScrollArea()
        scroll.setWidget(self.image_label)
        scroll.setWidgetResizable(False)

        # --- LEFT COLUMN: the PDF viewer ---
        left_column = QVBoxLayout()
        left_column.addWidget(self.heading)
        left_column.addLayout(button_row)
        left_column.addWidget(scroll)

        # --- SEARCH WIDGETS (create BEFORE adding to the layout) ---
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search recipes by title…")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.do_search)
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.load_selected)   # double-click a result

        # --- SAVE BUTTON ---
        save_button = QPushButton("Save Recipe")
        save_button.clicked.connect(self.on_save)
        new_button = QPushButton("New Recipe")
        new_button.clicked.connect(self.new_recipe)
        
        # --- DELETE BUTTON ---
        delete_button = QPushButton("Delete Recipe")
        delete_button.clicked.connect(self.on_delete)

        # --- RIGHT COLUMN: search + results + recipe form + save ---
        right_column = QVBoxLayout()
        right_column.addWidget(self.search_edit)
        right_column.addWidget(search_button)
        right_column.addWidget(self.results_list)
        right_column.addLayout(form)
        right_column.addWidget(new_button)
        right_column.addWidget(save_button)
        right_column.addWidget(delete_button)

        # --- ROOT: left | right side by side ---
        root = QHBoxLayout()
        root.addLayout(left_column, 2)      # left gets ~2/3 width
        root.addLayout(right_column, 1)     # right gets ~1/3 width

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    # ---- these methods are the "slots" the buttons call ----

    def open_pdf(self):
        # QFileDialog returns (path, filter). We only want the path.
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF files (*.pdf)")
        if not path:                 # user hit Cancel
            return
        self.doc = pdf.open_pdf(path)
        self.page_number = 0          # start at the first page
        self.show_page()

    def show_page(self):
        if self.doc is None:
            return
        pix = pdf.render_page(self.doc, self.page_number, zoom=self.zoom)   # PDF → pixels
        self.image_label.setPixmap(pixmap_to_qpixmap(pix))  # pixels → screen
        self.image_label.adjustSize()  # make the label fit the image
        self.heading.setText(f"Page {self.page_number + 1} of {len(self.doc)}")

    def next_page(self):
        if self.doc and self.page_number < len(self.doc) - 1:  # don't go past the end
            self.page_number += 1
            self.show_page()

    def prev_page(self):
        if self.doc and self.page_number > 0:                  # don't go before page 1
            self.page_number -= 1
            self.show_page()

    def zoom_in(self):
        self.zoom = min(self.zoom * 1.2, 6.0)  # limit zoom to 6x
        self.show_page()

    def zoom_out(self):
        self.zoom = max(self.zoom / 1.2, 0.2)  # limit zoom to 0.2x
        self.show_page()

    def ocr_page(self):
        if self.doc is None:
            return
        pix = pdf.render_page(self.doc, self.page_number, zoom=self.zoom)
        text = image_to_text(pix)
        ingredients, steps = parse_recipe_text(text)
        self.ingredients_edit.setPlainText("\n".join(ingredients))
        self.steps_edit.setPlainText("\n".join(steps))

    def build_recipe(self):
        title = self.title_edit.text()
        source = self.source_edit.text()
        servings = int(self.servings_edit.text() or 0)
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
        ingredients = [line.strip() for line in self.ingredients_edit.toPlainText().split("\n") if line.strip()]
        steps = [line.strip() for line in self.steps_edit.toPlainText().split("\n") if line.strip()]

        return Recipe(
            title=title,
            source=source,
            servings=servings,
            tags=tags,
            ingredients=ingredients,
            steps=steps,
        )          # build only — saving happens in on_save

    def do_search(self):
        self.results_list.clear()                               # wipe old results
        for recipe_id, title in search_recipes(self.search_edit.text()):
            item = QListWidgetItem(title)              # the visible row = the title
            item.setData(Qt.UserRole, recipe_id)      # secretly attach the id to the row
            self.results_list.addItem(item)

    def load_selected(self, item):
        recipe_id = item.data(Qt.UserRole)
        recipe = get_recipes(recipe_id)
        if recipe:
            self.current_id = recipe_id          # ← remember what we loaded
            self.load_recipe_into_form(recipe)

    def load_recipe_into_form(self, recipe):
        """Reverse of build_recipe: Recipe object → fill the form widgets."""
        self.title_edit.setText(recipe.title)
        self.source_edit.setText(recipe.source)
        self.servings_edit.setText(str(recipe.servings))      # int → text
        self.tags_edit.setText(", ".join(recipe.tags))        # list → comma string
        self.ingredients_edit.setPlainText("\n".join(recipe.ingredients))  # list → lines
        self.steps_edit.setPlainText("\n".join(recipe.steps))
        
    def on_save(self):
        recipe = self.build_recipe()
        if not recipe.title:
            self.heading.setText("⚠ Can't save: Title is empty")
            return
        if self.current_id is None:
            new_id = save_recipe(recipe)                  # INSERT
            self.current_id = new_id                      # remember it → next save updates, not duplicates
            self.heading.setText(f"✓ Saved new recipe #{new_id}: {recipe.title}")
        else:
            update_recipe(self.current_id, recipe)        # UPDATE the loaded row
            self.heading.setText(f"✓ Updated recipe #{self.current_id}: {recipe.title}")
    
    def new_recipe(self):
        self.current_id = None
        self.load_recipe_into_form(Recipe("", "", 0, [], [], []))
        self.heading.setText("New recipe")
        
    def on_delete(self):
        if self.current_id is None:                         # nothing loaded to delete
            self.heading.setText("⚠ Load a recipe first to delete it")
            return

        # destructive action → confirm first
        answer = QMessageBox.question(
            self, "Delete recipe",
            f"Delete recipe #{self.current_id}? This can't be undone.",
        )
        if answer != QMessageBox.StandardButton.Yes:        # user clicked No / closed
            return

        deleted_id = self.current_id
        delete_recipe(deleted_id)
        self.current_id = None                              # nothing is loaded now
        self.load_recipe_into_form(Recipe("", "", 0, [], [], []))  # clear the form
        self.do_search()                                    # refresh list so it disappears
        self.heading.setText(f"🗑 Deleted recipe #{deleted_id}")


def main():
    app = QApplication([])
    init_db()                 # create the table if it's not there yet
    window = MainWindow()
    window.show()
    app.exec()
