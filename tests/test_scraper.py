from recipe_grabber.scraper import extract_recipe


def test_fallback_parser_preserves_order_and_deduplicates() -> None:
    html = """
    <html>
      <body>
        <h1>Simple salad</h1>
        <ul>
          <li class="recipe-ingredient">2 tomatoes</li>
          <li class="recipe-ingredient">  Olive   oil </li>
          <li class="recipe-ingredient">2 TOMATOES</li>
        </ul>
      </body>
    </html>
    """

    recipe = extract_recipe(html, "https://recipes.example/salad")

    assert recipe.title == "Simple salad"
    assert recipe.ingredients == ["2 tomatoes", "Olive oil"]

