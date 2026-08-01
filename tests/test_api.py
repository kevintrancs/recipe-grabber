from __future__ import annotations

import pytest

from recipe_grabber import create_app

RECIPE_HTML = """
<!doctype html>
<html>
  <head>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": "Tomato Toast",
        "recipeIngredient": ["2 ripe tomatoes", "1 tbsp olive oil"]
      }
    </script>
  </head>
  <body><h1>Tomato Toast</h1></body>
</html>
"""


@pytest.fixture
def client():
    app = create_app(
        {
            "TESTING": True,
            "DEBUG": False,
            "FETCH_HTML": lambda url: (RECIPE_HTML, url),
        }
    )
    return app.test_client()


def test_health(client) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_scrape_returns_ordered_named_ingredients(client) -> None:
    response = client.post("/api/scrape", json={"url": "https://recipes.example/toast"})

    assert response.status_code == 200
    assert response.get_json() == {
        "title": "Tomato Toast",
        "source_url": "https://recipes.example/toast",
        "ingredients": [
            {"text": "2 ripe tomatoes", "name": "ripe tomatoes"},
            {"text": "1 tbsp olive oil", "name": "olive oil"},
        ],
    }


def test_scrape_rejects_missing_input(client) -> None:
    response = client.post("/api/scrape", json={})

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_request"


def test_unknown_api_path_returns_json_not_the_spa(client) -> None:
    response = client.get("/api/scrape")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_scrape_rejects_unusable_url_without_crashing() -> None:
    """An over-long DNS label used to escape the idna codec as a 500."""
    client = create_app({"TESTING": True, "DEBUG": False}).test_client()

    response = client.post("/api/scrape", json={"url": f"https://{'a' * 70}.example/recipe"})

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_url"
