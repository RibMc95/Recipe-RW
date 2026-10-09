import sqlite3 
import json

from recipe_rw.models import Recipe

DB_PATH = "recipes.db"      # the single file your whole database lives in

def init_db():
    """Create the recipes table if it doesn't already exist."""
    conn = sqlite3.connect(DB_PATH)      # opens (or creates) the .db file
    cursor = conn.cursor()               # a cursor runs SQL commands
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,  -- unique id, auto-assigned
            title       TEXT NOT NULL,
            source      TEXT,
            servings    INTEGER,
            ingredients TEXT,    -- JSON string: ["2 eggs", ...]
            steps       TEXT,    -- JSON string
            tags        TEXT,    -- JSON string
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP      -- auto-stamps the time
        )
    """)
    conn.commit()     # SAVE the change to the file (without this, nothing persists)
    conn.close()      # close the connection
    
def save_recipe(recipe): 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO recipes (title, source, servings, ingredients, steps, tags) VALUES (?, ?, ?, ?, ?, ?)",
        (
            recipe.title,
            recipe.source,
            recipe.servings,
            json.dumps(recipe.ingredients),
            json.dumps(recipe.steps),
            json.dumps(recipe.tags),
        )
    )
    conn.commit()     # SAVE the change to the file (without this, nothing persists)
    new_id = cursor.lastrowid
    conn.close()      # close the connection
    return new_id

def get_recipes(recipe_id):
    """Load one recipes back into a Recipe object"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    row = conn.execute("SELECT title, source, servings, ingredients, steps, tags FROM recipes WHERE id = ?",
    (recipe_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    title, source, servings, ingredients_json, steps_json, tags_json = row
    return Recipe(
        title, source, servings,
        json.loads(ingredients_json),   # JSON text → list
        json.loads(steps_json),
        json.loads(tags_json),
    )

def search_recipes(query):
    """Return [(id, title), ...] for recipes whose title matches the query."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, title FROM recipes WHERE title LIKE ? ORDER BY title",
        (f"%{query}%",),            # % are SQL wildcards; still passed via ? placeholder
    ).fetchall()
    conn.close()
    return rows

def update_recipe(recipe_id, recipe):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """UPDATE recipes
           SET title = ?, source = ?, servings = ?, ingredients = ?, steps = ?, tags = ?
           WHERE id = ?""",
        (
            recipe.title,
            recipe.source,
            recipe.servings,
            json.dumps(recipe.ingredients),
            json.dumps(recipe.steps),
            json.dumps(recipe.tags),
            recipe_id,                     # ← the WHERE value goes LAST (matches ? order)
        ),

    )
    conn.commit()
    conn.close()
    
def delete_recipe(recipe_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))   # WHERE is critical!
    conn.commit()
    conn.close()
        
