from __future__ import annotations

import pytest

from recipe_grabber import ingredients
from recipe_grabber.ingredients import parse_ingredient_line


@pytest.mark.parametrize(
    ("line", "name"),
    [
        ("10 cloves garlic, minced", "garlic"),
        ("3 cloves roasted garlic", "garlic"),
        ("2 large eggs", "eggs"),
        ("1 bunch green onions", "green onions"),
        # Modifiers that change what you buy stay part of the name.
        ("2 tbsp salted butter, softened", "salted butter"),
    ],
)
def test_the_food_is_separated_from_quantity_and_preparation(line: str, name: str) -> None:
    assert parse_ingredient_line(line).name == name


def test_the_original_line_is_kept() -> None:
    assert parse_ingredient_line("10 cloves garlic, minced").text == "10 cloves garlic, minced"


def test_a_line_naming_two_foods_uses_the_first() -> None:
    assert parse_ingredient_line("2 cups chicken or beef stock").name == "chicken stock"


@pytest.mark.parametrize("line", ["For the sauce:", "2 tablespoons", "divided"])
def test_a_line_naming_no_food_falls_back_to_itself(line: str) -> None:
    """Recipe sites list section headers and stray notes alongside real ingredients."""
    parsed = parse_ingredient_line(line)

    assert parsed.name == parsed.text == line


def test_a_parser_crash_never_fails_the_import(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(_: str) -> None:
        raise RuntimeError("parser exploded")

    monkeypatch.setattr(ingredients, "parse_ingredient", explode)

    assert parse_ingredient_line("2 large eggs").name == "2 large eggs"
