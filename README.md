# NafzigerRecipes
Nafziger Family Recipes

- `recipes/<id>.yaml` is the source of truth: one file per recipe, with its ingredients, directions, notes, story, and who wrote it. The file name must match the recipe's `id`.
- `recipe.schema.json` describes a recipe file. Editors with YAML language support (e.g. VS Code's YAML extension) validate and autocomplete against it.

Both tools below need [uv](https://docs.astral.sh/uv/). They validate every recipe file against the schema first and stop with an error naming the file if something's wrong.

Pull requests run that same check (`.github/workflows/check.yml`), so a recipe file that doesn't match the schema fails the check before it's merged.

## Website

Every push to `main` rebuilds the site and publishes it to GitHub Pages (`.github/workflows/pages.yml`). To preview locally:

```sh
uv run tools/build_site.py
python3 -m http.server -d build/site     # http://localhost:8000
```

Each recipe page has an **Edit on GitHub** button that opens its YAML file in GitHub's editor. People with write access can commit straight to `main`. Anyone else gets a fork and a pull request to review. Each recipe page also has a **Print card** button.

## Printing recipe cards

```sh
uv run tools/render_cards.py                          # all recipes -> build/recipe-cards.html
uv run tools/render_cards.py --only corn-pone,pesto   # just these recipe ids
uv run tools/render_cards.py --category cookies,cakes
```

The website's `cards.html` is the same page (`cards.html?only=corn-pone,pesto` works there too).

Open `build/recipe-cards.html` in a browser and print it: **landscape**, letter paper, margins **None**, background graphics on. Each sheet holds two 5.5×8.5 in cards; cut along the dashed line. Recipes that don't fit on one card shrink their type slightly, then continue onto a second card.
