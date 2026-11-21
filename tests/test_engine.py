import re
import socket
import threading

import pytest

from drinkrec.catalog import CATALOG
from drinkrec.engine import Recommender

PROMPTS = ["smoky", "tropical", "autumn cinnamon", "refreshing citrus", "coffee dessert", "cozy winter warmer",
           "basil strawberry spritz", "spicy tequila with no lime", "", "asdfgh qwerty", "beef and broccoli",
           "tropcal smokey", "bitter italian aperitivo"]
LABELS = {c["label"] for c in CATALOG.values()}


@pytest.fixture(scope="module")
def rec():
    return Recommender()


@pytest.mark.parametrize("prompt", PROMPTS)
def test_valid_drinks(rec, prompt):
    out = rec.recommend(prompt, servings=2)
    assert 1 <= len(out["drinks"]) <= 3
    for d in out["drinks"]:
        # screen: only catalog (drinkable) items, and every drink has alcohol
        assert all(i["item"] in LABELS or i["item"] == "Egg white" for i in d["ingredients"])
        assert any(i["role"] in ("spirit", "sparkling", "liqueur", "fortified", "beer") for i in d["ingredients"])
        assert d["abv"] > 3
        # quantities
        for i in d["ingredients"]:
            assert re.search(r"\d", i["amount"])
            if i["oz"] is not None:
                assert i["oz"] > 0 and i["ml"] > 0
        # garnish / seasoning on top
        assert d["garnish"] and all(g["prep"] for g in d["garnish"])
        assert len({i["key"] for i in d["ingredients"]}) == len(d["ingredients"])  # no duplicates
        assert d["method"] and d["glass"]


def test_food_words_never_become_ingredients(rec):
    out = rec.recommend("beef and broccoli", servings=1)
    for d in out["drinks"]:
        assert not any(re.search("beef|broccoli", i["item"], re.I) for i in d["ingredients"])


def test_servings_scale(rec):
    one = rec.recommend("tropical", servings=1)["drinks"][0]
    four = rec.recommend("tropical", servings=4)["drinks"][0]
    assert one["name"] == four["name"]
    for a, b in zip(one["ingredients"], four["ingredients"]):
        if a["oz"]:
            assert b["oz"] == pytest.approx(4 * a["oz"])


def test_themes_map_to_expected_flavors(rec):
    smoky = rec.recommend("smoky", 1)["drinks"]
    assert any(i["key"] in ("mezcal", "scotch", "bourbon", "rye", "drambuie") for d in smoky for i in d["ingredients"]) \
        or any(g["key"] in ("smoked_paprika", "rosemary_sprig") for d in smoky for g in d["garnish"])
    trop = rec.recommend("tropical", 1)["drinks"]
    assert any("rum" in i["key"] or i["key"] in ("pineapple_juice", "coconut_water", "passion_fruit", "mango_puree")
               for d in trop for i in d["ingredients"])
    autumn = rec.recommend("autumn cinnamon", 1)["drinks"]
    assert any("cinnamon" in i["key"] or "cinnamon" in g["key"] for d in autumn
               for i in d["ingredients"] for g in d["garnish"])
    coffee = rec.recommend("coffee dessert", 1)["drinks"]
    assert any(i["key"] in ("coffee_liqueur", "espresso", "hot_coffee") for d in coffee for i in d["ingredients"])


def test_requested_spirit_and_exclusion(rec):
    out = rec.recommend("spicy tequila with no lime", 1)
    for d in out["drinks"]:
        keys = {i["key"] for i in d["ingredients"]} | {g["key"] for g in d["garnish"]}
        assert "tequila" in keys
        assert not keys & {"lime_juice", "lime_wheel"}


def test_named_ingredients_used(rec):
    out = rec.recommend("basil strawberry spritz", 1)
    keys = [{i["key"] for i in d["ingredients"]} | {g["key"] for g in d["garnish"]} for d in out["drinks"]]
    assert any("strawberry_puree" in k for k in keys) and any("basil_leaf" in k for k in keys)
    assert out["drinks"][0]["style"] == "spritz"


def test_explanations_cite_chemistry(rec):
    d = rec.recommend("smoky autumn with maple", 1)["drinks"][0]
    assert any("flavor compounds" in w for w in d["why"])


def test_no_network_needed(rec, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network used")
    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr(socket.socket, "connect", boom)
    assert rec.recommend("summer berry", 1)["drinks"]


def test_http_api(rec):
    import json
    import urllib.request
    import app
    from http.server import ThreadingHTTPServer
    app.REC = rec
    srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        assert b"Hallucinagen" in urllib.request.urlopen(base + "/").read()
        out = json.loads(urllib.request.urlopen(base + "/api/recommend?q=cozy%20winter&servings=3").read())
        assert out["drinks"] and out["drinks"][0]["servings"] == 3
    finally:
        srv.shutdown()
