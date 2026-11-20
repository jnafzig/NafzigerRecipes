# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "jinja2", "jsonschema"]
# ///
"""Build the recipe website from recipes/*.yaml into build/site/.

    uv run tools/build_site.py
    python3 -m http.server -d build/site     # preview at http://localhost:8000

Pages: index.html (every recipe, searchable), <id>.html (one per recipe), and cards.html
(the printable cards; cards.html?only=<id> prints one recipe). GitHub Actions publishes
build/site/ to GitHub Pages on every push to main.
"""
import argparse
import os
import pathlib
import shutil
import sys

import recipes as rx
import render_cards

SITE_TEMPLATES = pathlib.Path(__file__).parent / "site"
REPO = os.environ.get("GITHUB_REPOSITORY", "jnafzig/NafzigerRecipes")


def search_text(r: dict) -> str:
    """Everything the index search box matches against, lowercased."""
    words = [r["title"], r["category"], r.get("author") or "", r.get("source") or "", *r.get("tags", [])]
    words += [i["item"] for g in r["ingredient_groups"] for i in g["ingredients"]]
    return " ".join(words).lower()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=pathlib.Path, default=rx.ROOT / "build" / "site")
    args = parser.parse_args()

    recipes = rx.load()
    env = render_cards.environment()
    env.loader.searchpath.append(str(SITE_TEMPLATES))
    env.globals["repo_url"] = f"https://github.com/{REPO}"

    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)
    shutil.copy(SITE_TEMPLATES / "site.css", args.out / "site.css")

    sections = [
        (slug, label, [{**r, "search": search_text(r)} for r in recipes if r["category"] == slug])
        for slug, label in rx.CATEGORIES.items()
    ]
    (args.out / "index.html").write_text(env.get_template("index.html.j2").render(
        sections=[s for s in sections if s[2]], count=len(recipes)))

    for r in recipes:
        (args.out / f"{r['id']}.html").write_text(env.get_template("recipe.html.j2").render(r=rx.display(r)))

    (args.out / "cards.html").write_text(render_cards.render(recipes))
    print(f"Wrote {len(recipes)} recipe pages to {args.out.relative_to(rx.ROOT) if args.out.is_relative_to(rx.ROOT) else args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
