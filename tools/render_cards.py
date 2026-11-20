# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "jinja2", "jsonschema"]
# ///
"""Render recipes/*.yaml as printable half-letter recipe cards, two per landscape letter sheet.

    uv run tools/render_cards.py                      # every recipe -> build/recipe-cards.html
    uv run tools/render_cards.py --only corn-pone,pesto
    uv run tools/render_cards.py --category cookies

Open the HTML file in a browser and print it: landscape, margins "None", background graphics on.
"""
import argparse
import pathlib
import sys

import jinja2

import recipes as rx


def environment() -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent),
        autoescape=True, trim_blocks=True, lstrip_blocks=True,
    )


def render(recipes: list[dict]) -> str:
    return environment().get_template("cards.html.j2").render(recipes=[rx.display(r) for r in recipes])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=pathlib.Path, default=rx.ROOT / "build" / "recipe-cards.html")
    parser.add_argument("--only", help="comma-separated recipe ids")
    parser.add_argument("--category", help="comma-separated category slugs")
    args = parser.parse_args()

    recipes = rx.load()
    if args.only:
        wanted = args.only.split(",")
        unknown = set(wanted) - {r["id"] for r in recipes}
        if unknown:
            print(f"Unknown recipe ids: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 1
        recipes = [r for r in recipes if r["id"] in wanted]
    if args.category:
        cats = set(args.category.split(","))
        recipes = [r for r in recipes if r["category"] in cats]
    if not recipes:
        print("No recipes matched.", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(recipes))
    print(f"Wrote {len(recipes)} recipes to {args.out.relative_to(rx.ROOT) if args.out.is_relative_to(rx.ROOT) else args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
