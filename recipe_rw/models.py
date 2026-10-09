from dataclasses import dataclass, field

@dataclass
class Recipe:
    # --- required fields (no defaults) MUST come first ---
    title: str
    source: str
    # --- optional fields (with defaults) come after ---
    servings: int = 0
    ingredients: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
