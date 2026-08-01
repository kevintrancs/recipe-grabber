from __future__ import annotations

import os
from dataclasses import dataclass

# NLTK 3.10 refuses to import its own dependencies when they resolve inside the working
# directory, which is every one of them once .venv lives in the project. It blocked even
# stdlib `locale` in testing, and PYTHONSAFEPATH does not turn it off. setdefault leaves
# the choice overridable from the environment.
# ponytail: revisit when NLTK ships a fix; 3.10.1 is the newest release.
os.environ.setdefault("NLTK_DISABLE_IMPORT_SECURITY", "1")

from ingredient_parser import parse_ingredient  # must follow the line above


@dataclass(frozen=True, slots=True)
class ImportedIngredient:
    text: str  # the original recipe line
    name: str  # the food to shop for, e.g. "garlic"


def parse_ingredient_line(text: str) -> ImportedIngredient:
    """Reduce a recipe line to the food it names, keeping the line itself.

    Never raises: one unparseable line must not fail the whole import.
    """
    try:
        parsed = parse_ingredient(text)
        # Several names means "chicken or beef stock". The first is a fair grocery entry
        # and the original line rides along, so nothing is hidden from the shopper.
        name = parsed.name[0].text.strip() if parsed.name else ""
    except Exception:  # the parser raises a different type per failure mode
        name = ""
    return ImportedIngredient(text=text, name=name or text)
