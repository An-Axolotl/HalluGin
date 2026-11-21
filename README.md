# HalluGin: an offline drink recommender built on FlavorGraph

Built on **[FlavorGraph](https://github.com/lamypark/FlavorGraph)** ([paper](https://www.nature.com/articles/s41598-020-79422-8)): a large-scale food–chemical graph of 6,653 ingredients and 1,645 flavor compounds. Drinks are matched by chemical similarity (shared flavor compounds), recipe pairing scores, and FlavorGraph's ingredient embeddings.

Type a flavor or a theme ("smoky autumn with maple", "tropical but no coconut", "basil strawberry spritz").
It returns three cocktails with exact quantities scaled to your servings, a glass, a method, garnishes and
seasonings on top, and a short note on *why* the ingredients fit (shared flavor compounds).

There is no LLM, no API key and no network access. Everything runs from `drinkrec/data/flavorgraph.npz` (2.4 MB).

```bash
pip install numpy            # the only dependency (use a venv)
python3 app.py               # web UI ("Flavor Pour") at http://127.0.0.1:8765
python3 -m drinkrec "cozy winter warmer" --servings 4        # CLI
python3 -m pytest -q         # tests
```

## How it works
1. **Prompt parsing**: theme words (`themes.py`, ~40 themes and ~120 synonyms), spirit names ("tequila", "no gin"),
   style words (spritz, sour, toddy...), and *any* of FlavorGraph's 6,653 ingredient names. Misspellings are
   fuzzy-matched. "no X" / "without X" excludes items.
2. **Drinkable screen**: only the ~150 items in `catalog.py` can appear in a recipe: spirits, liqueurs,
   vermouths and wines, beer and cider, citrus, syrups, juices, mixers, dairy, bitters, and garnishes or seasonings.
   Foods in the prompt (e.g. "beef") only *steer* the flavor.
3. **Scoring** each catalog item against the prompt, using three FlavorGraph signals turned into percentiles:
   - chemical: cosine overlap of flavor-compound sets (bottled products use base foods, e.g. lime juice → lime)
   - recipe pairing: ingredient–ingredient co-occurrence scores
   - the 300-d FlavorGraph embedding cosine

   Items tagged with the prompt's themes also get a bonus.
4. **Assembly**: eight classic structures (sour, highball, stirred, spritz, flip, toddy, tiki punch, mule). Each slot
   is filled with the best item that also suits what is already in the glass. Then a garnish and a seasoning are
   added (cinnamon, nutmeg, chili salt, mint...), quantities are scaled, and ABV is estimated.

Rebuild the data from a FlavorGraph checkout: `python3 scripts/build_data.py path/to/FlavorGraph`.

Data: [FlavorGraph](https://github.com/lamypark/FlavorGraph) (Park et al., *Scientific Reports* 2021),
Apache-2.0, see `drinkrec/data/FLAVORGRAPH_LICENSE`.
