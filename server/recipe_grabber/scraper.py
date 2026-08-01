from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup
from recipe_scrapers import scrape_html

from .errors import AppError
from .ingredients import ImportedIngredient, parse_ingredient_line

INGREDIENT_CLASS = re.compile(r"ingredient", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Recipe:
    title: str
    source_url: str
    ingredients: list[ImportedIngredient]


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split()).strip()


def _ingredients(values: list[str]) -> list[ImportedIngredient]:
    """Clean, drop repeated lines, then name the food on each surviving line."""
    seen: set[str] = set()
    result: list[ImportedIngredient] = []
    for raw_value in values:
        value = _clean_text(raw_value)
        key = value.casefold()
        if value and key not in seen:
            seen.add(key)
            result.append(parse_ingredient_line(value))
    return result


def _structured_recipe(html: str, source_url: str) -> Recipe | None:
    try:
        scraper = scrape_html(html, source_url, supported_only=False)
        ingredients = _ingredients(list(scraper.ingredients()))
        title = _clean_text(scraper.title())
    except Exception:  # recipe_scrapers raises a different type per site.
        return None

    if not ingredients:
        return None
    return Recipe(title=title or "Imported recipe", source_url=source_url, ingredients=ingredients)


def _html_fallback(html: str, source_url: str) -> Recipe | None:
    soup = BeautifulSoup(html, "html.parser")
    candidates = list(soup.select('[itemprop="recipeIngredient"]'))
    if not candidates:
        candidates = list(soup.find_all(class_=INGREDIENT_CLASS))

    ingredients = _ingredients([element.get_text(" ", strip=True) for element in candidates])
    if not ingredients:
        return None

    heading = soup.find("h1")
    title = _clean_text(heading.get_text(" ", strip=True)) if heading else "Imported recipe"
    return Recipe(title=title, source_url=source_url, ingredients=ingredients)


def extract_recipe(html: str, source_url: str) -> Recipe:
    recipe = _structured_recipe(html, source_url) or _html_fallback(html, source_url)
    if recipe is None:
        raise AppError(
            "No ingredients were found on that page. The site may block scraping or use an "
            "unsupported format.",
            code="recipe_not_found",
            status=422,
        )
    return recipe
