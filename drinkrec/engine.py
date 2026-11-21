"""Drink recommender built on FlavorGraph (chemical compounds + recipe pairings + embeddings).

    from drinkrec.engine import Recommender
    r = Recommender()
    r.recommend("smoky autumn drink with maple", servings=2)

Pipeline
1. parse the prompt into seeds (FlavorGraph ingredients), flavor tags, style hints, forced and
   excluded catalog items. No LLM, no network.
2. score every catalog item (drinkable things only) by its similarity to the seeds:
   chemical (shared flavor compounds), pairing (recipe co-occurrence) and embedding cosine,
   each turned into a percentile so they are comparable, plus a tag-match bonus.
3. fill classic cocktail structures (sour, highball, stirred, spritz, flip, toddy, tiki, mule)
   with the best-scoring compatible items, add garnishes/seasonings, scale to servings.
"""
from __future__ import annotations

import difflib
import re
from pathlib import Path

import numpy as np

from .catalog import CATALOG
from .themes import ALIASES, STYLE_WORDS, THEMES

DATA = Path(__file__).resolve().parent / "data" / "flavorgraph.npz"
W_CHEM, W_PAIR, W_EMB = 0.45, 0.30, 0.25

SPIRIT_ALIASES = {
    "vodka": ["vodka", "vanilla_vodka"], "gin": ["gin"], "rum": ["white_rum", "dark_rum", "spiced_rum", "coconut_rum"],
    "tequila": ["tequila"], "mezcal": ["mezcal"], "whiskey": ["bourbon", "rye", "scotch", "irish_whiskey"],
    "whisky": ["bourbon", "rye", "scotch", "irish_whiskey"], "bourbon": ["bourbon"], "rye": ["rye"],
    "scotch": ["scotch"], "brandy": ["brandy", "cognac", "apple_brandy", "cherry_brandy"], "cognac": ["cognac"],
    "calvados": ["apple_brandy"], "pisco": ["pisco"], "cachaca": ["cachaca"], "sake": ["sake"],
    "champagne": ["champagne"], "prosecco": ["prosecco"], "wine": ["red_wine", "white_wine", "rose_wine"],
    "beer": ["lager", "stout"], "stout": ["stout"], "cider": ["hard_cider"], "vermouth": ["sweet_vermouth", "dry_vermouth"],
    "campari": ["campari"], "amaretto": ["amaretto"], "kahlua": ["coffee_liqueur"], "absinthe": ["absinthe"],
    "limoncello": ["limoncello"], "elderflower": ["elderflower"], "port": ["port"], "sherry": ["dry_sherry"],
    "midori": ["melon_liqueur"], "frangelico": ["hazelnut_liqueur"], "cointreau": ["cointreau"],
    "egg": ["egg_white"], "tonic": ["tonic"], "cola": ["cola"],
}
WORD_NODES = {"maple": "maple_syrup", "chili": "cayenne", "chile": "cayenne", "pepper": "black_pepper",
              "vanilla": "vanilla", "caramel": "caramel", "butterscotch": "caramel", "toffee": "caramel",
              "elderflower": "pear", "passionfruit": "passion_fruit", "lychee": "lychee", "matcha": "green_tea",
              "earl": "black_tea", "chai": "cinnamon", "pumpkin": "pumpkin", "smoke": "smoked_paprika",
              "rose": "rose_water", "hibiscus": "cranberry", "salt": "sea_salt", "citrus": "lemon"}
STOP = set("a an the and or of with for to in on my me i some something drink drinks cocktail cocktails make give "
           "want like that is it be really very bit little please would could recipe night evening day tonight "
           "can you any kind good nice great feel feeling vibe vibes mood type taste tasting flavor flavour "
           "profile style theme using use made from but too more less extra lot lots glass round".split())
NEGATORS = {"no", "without", "not", "except", "hate", "avoid", "skip"}

# ---------------------------------------------------------------------------------------------
# cocktail structures. amounts in oz per drink; ("dash", n) for bitters; roles may list options.
TEMPLATES = {
    "sour": dict(name="Sour", glass="chilled coupe", method="Shake hard with ice for 12 s, then double-strain into the glass.",
                 base=("spirit",), slots=[("sour", 0.75, False), ("sweetener", 0.75, False), ("liqueur", 0.5, True), ("egg_white", 1, True)],
                 dilution=0.25),
    "highball": dict(name="Highball", glass="tall Collins glass over ice", method="Build the spirit, citrus and syrup over ice, top with the mixer and stir once.",
                     base=("spirit",), slots=[("sour", 0.5, False), ("sweetener", 0.5, False), ("mixer", 4.0, False)], dilution=0.0),
    "stirred": dict(name="Stirred", glass="rocks glass over one large cube", method="Stir with ice for 30 s until very cold, then strain over the large cube.",
                    base=("spirit",), slots=[("fortified|liqueur", 0.75, False), ("sweetener", 0.25, True), ("bitters", ("dash", 2), False)],
                    dilution=0.2),
    "spritz": dict(name="Spritz", glass="large wine glass over ice", method="Build over ice: liqueur first, then the sparkling wine, then a splash of soda. Stir gently once.",
                   base=("sparkling",), slots=[("liqueur|fortified", 1.5, False), ("club_soda", 1.0, False), ("juice", 1.0, True)], dilution=0.0),
    "flip": dict(name="Flip", glass="small coupe or Nick & Nora", method="Dry-shake without ice for 10 s, then shake hard with ice and strain.",
                 base=("spirit",), slots=[("liqueur", 1.0, False), ("dairy_cream", 1.0, False), ("sweetener", 0.25, True)], dilution=0.2),
    "toddy": dict(name="Toddy", glass="warm mug", method="Warm the mug with hot water, then build everything in it and stir until the sweetener dissolves.",
                  base=("spirit",), slots=[("sweetener_warm", 0.5, False), ("sour", 0.5, False), ("hot", 4.0, False)], dilution=0.0),
    "tiki": dict(name="Punch", glass="tiki mug or double rocks glass filled with crushed ice", method="Shake with a handful of crushed ice, then pour everything (unstrained) into the glass.",
                 base=("spirit",), slots=[("juice", 1.5, False), ("sour", 0.75, False), ("sweetener", 0.5, False), ("liqueur", 0.5, True)],
                 dilution=0.2),
    "mule": dict(name="Mule", glass="copper mug or highball over ice", method="Squeeze in the citrus, add the spirit and ice, top with ginger beer.",
                 base=("spirit",), slots=[("sour", 0.5, False), ("ginger_beer", 4.0, False), ("sweetener", 0.25, True)], dilution=0.0),
}
SLOT_POOLS = {"egg_white": ["egg_white"], "club_soda": ["club_soda"], "ginger_beer": ["ginger_beer"],
              "dairy_cream": ["heavy_cream", "whole_milk", "coconut_cream"],
              "sweetener_warm": ["honey_syrup", "maple_syrup", "demerara_syrup", "cinnamon_syrup", "ginger_syrup", "vanilla_syrup"]}
ABV = {"spirit": 0.40, "liqueur": 0.25, "fortified": 0.17, "sparkling": 0.12, "beer": 0.05}
SPIRIT_ABV = {"sake": 0.15, "absinthe": 0.60}
SEASONINGS = {"cinnamon_stick", "nutmeg", "star_anise", "clove", "cardamom", "black_pepper", "chili_salt_rim", "salt_rim",
              "jalapeno", "ginger_slice", "mint_sprig", "basil_leaf", "rosemary_sprig", "thyme_sprig", "sage_leaf",
              "lavender", "cocoa_dust", "coffee_beans", "toasted_coconut", "vanilla_bean", "smoked_paprika", "edible_flower"}
DEFAULT_SEEDS = ["lemon", "honey", "orange", "ginger"]


def _frac(x: float) -> str:
    whole, part = int(x), x - int(x)
    sym = {0.25: "¼", 0.5: "½", 0.75: "¾", 0.125: "⅛", 0.375: "⅜", 0.625: "⅝", 0.875: "⅞"}
    best = min(sym, key=lambda f: abs(f - part)) if part > 0.06 else None
    if best is not None and abs(best - part) > 0.06:
        return f"{x:.2f}".rstrip("0").rstrip(".")
    if part > 0.94:
        whole, best = whole + 1, None
    return (str(whole) if whole else "") + (sym[best] if best is not None else "") or "0"


class Recommender:
    def __init__(self, data_path: Path = DATA):
        d = np.load(data_path, allow_pickle=False)
        self.names = [str(n) for n in d["ingr_names"]]
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.comp_names = [str(c) for c in d["comp_names"]]
        self.comps: dict[int, set[int]] = {}
        for i, c in d["ic"]:
            self.comps.setdefault(int(i), set()).add(int(c))
        self.comp_freq: dict[int, int] = {}
        for cs in self.comps.values():
            for c in cs:
                self.comp_freq[c] = self.comp_freq.get(c, 0) + 1
        self.pair: dict[int, dict[int, float]] = {}
        for a, b, s in zip(d["pair_a"], d["pair_b"], d["pair_s"]):
            a, b, s = int(a), int(b), float(s)
            self.pair.setdefault(a, {})[b] = max(s, self.pair.get(a, {}).get(b, 0.0))
            self.pair.setdefault(b, {})[a] = max(s, self.pair.get(b, {}).get(a, 0.0))
        self.emb = d["emb"].astype(np.float32)
        self.has_emb = d["has_emb"]
        self.vocab = sorted(self.idx, key=len, reverse=True)
        self.single_vocab = [v for v in self.vocab if "_" not in v]
        self.keys = list(CATALOG)
        self.items = [self._profile_catalog(CATALOG[k]) for k in self.keys]
        self.cat_sim = self._catalog_matrix()

    # ---------------------------------------------------------------- profiles & similarity
    def _resolve(self, name: str) -> int | None:
        """FlavorGraph index for a name, trying simple variants (fresh_x, x_juice, plural...)."""
        for cand in (name, name.rstrip("s"), re.sub(r"^(fresh|ground|dried|whole|ripe|sweet|toasted)_", "", name),
                     re.sub(r"_(juice|zest|peel|puree|nectar|syrup|leaf|leaves|sprig|stick|powder)$", "", name)):
            if cand in self.idx:
                return self.idx[cand]
        return None

    def _chem_of(self, idx: int | None) -> set[int]:
        if idx is None:
            return set()
        if idx in self.comps:
            return self.comps[idx]
        nm = self.names[idx]                       # bottled product without data: try its base food
        base = re.sub(r"^(fresh|ground|dried|whole|light|dark|white|red|sweet)_|_(juice|zest|peel|syrup|nectar|liqueur|brandy|wine)$", "", nm)
        j = self.idx.get(base)
        return self.comps.get(j, set()) if j is not None else set()

    def _profile(self, node: str | None, chem: list[str]) -> dict:
        ni = self._resolve(node) if node else None
        cset: set[int] = set()
        for c in chem:
            cset |= self._chem_of(self._resolve(c))
        vecs = [self.emb[i] for i in [ni] + [self._resolve(c) for c in chem] if i is not None and self.has_emb[i]]
        v = None
        if vecs:
            v = np.mean(vecs, 0); v /= np.linalg.norm(v) + 1e-9
        pnodes = {i for i in [ni] + [self._resolve(c) for c in chem] if i is not None}
        return dict(node=ni, chem=cset, emb=v, pnodes=pnodes)

    def _profile_catalog(self, c: dict) -> dict:
        p = self._profile(c["node"], c["chem"]); p["key"] = c["key"]; return p

    def _signals(self, a: dict, b: dict) -> tuple[float | None, float | None, float | None]:
        chem = None
        if a["chem"] and b["chem"]:
            chem = len(a["chem"] & b["chem"]) / np.sqrt(len(a["chem"]) * len(b["chem"]))
        pair = 0.0
        for x in a["pnodes"]:
            px = self.pair.get(x, {})
            for y in b["pnodes"]:
                if x == y:
                    pair = max(pair, 1.0)
                elif y in px:
                    pair = max(pair, px[y])
        emb = float(a["emb"] @ b["emb"]) if a["emb"] is not None and b["emb"] is not None else None
        return chem, pair, emb

    @staticmethod
    def _pct(vals: list[float | None]) -> list[float | None]:
        ok = [v for v in vals if v is not None]
        if not ok:
            return vals
        arr = np.sort(np.array(ok))
        return [None if v is None else float(np.searchsorted(arr, v, "right") / len(arr)) for v in vals]

    def _affinity(self, seed: dict, items: list[dict]) -> np.ndarray:
        sig = [self._signals(it, seed) for it in items]
        chem, pair, emb = (self._pct([s[k] for s in sig]) for k in range(3))
        out = np.zeros(len(items))
        for i in range(len(items)):
            num = den = 0.0
            for w, v in ((W_CHEM, chem[i]), (W_PAIR, pair[i]), (W_EMB, emb[i])):
                if v is not None:
                    num += w * v; den += w
            out[i] = num / den if den else 0.0
            if seed["node"] is not None and seed["node"] in items[i]["pnodes"]:
                out[i] = 1.0                               # the item *is* the seed
        return out

    def _catalog_matrix(self) -> np.ndarray:
        n = len(self.items); M = np.zeros((n, n))
        for j, it in enumerate(self.items):
            M[:, j] = self._affinity(it, self.items)
        return (M + M.T) / 2

    def shared_compounds(self, a: dict, b: dict, k: int = 3) -> tuple[int, list[str]]:
        s = a["chem"] & b["chem"]
        def nice(c):
            n = self.comp_names[c].replace("_", " ")
            return 0 if re.fullmatch(r"[A-Za-z][a-z \-]+", n) else 1
        ranked = sorted(s, key=lambda c: (nice(c), self.comp_freq.get(c, 0)))
        names = [self.comp_names[c].replace("_", " ") for c in ranked if len(self.comp_names[c]) < 26]
        return len(s), names[:k]

    # ---------------------------------------------------------------- prompt parsing
    def parse(self, prompt: str) -> dict:
        text = prompt.lower().replace("&", " and ")
        toks = re.findall(r"[a-z][a-z'\-]*", text)
        seeds, themes, tags, styles, forced, excluded, unknown = [], [], set(), {}, set(), set(), []
        parsed_tags = []
        i, neg = 0, False
        while i < len(toks):
            matched = False
            for n in (3, 2, 1):
                if i + n > len(toks):
                    continue
                gram = "_".join(toks[i:i + n]); word = " ".join(toks[i:i + n])
                tgt = None
                if word in SPIRIT_ALIASES or gram in SPIRIT_ALIASES:
                    keys = SPIRIT_ALIASES.get(word) or SPIRIT_ALIASES[gram]
                    (excluded if neg else forced).update(keys); tgt = "catalog"
                elif not neg and (gram in THEMES or gram in ALIASES):
                    th = gram if gram in THEMES else ALIASES[gram]
                    if th in themes:
                        i += n; matched = True; break
                    themes.append(th); s, t, st = THEMES[th]
                    seeds += [(x, 1.0, th) for x in s]; tags |= set(t); parsed_tags.append(set(t))
                    for rank, sname in enumerate(st):
                        styles[sname] = styles.get(sname, 0) + (3 - rank)
                    tgt = "theme"
                elif not neg and gram in STYLE_WORDS:
                    styles[STYLE_WORDS[gram]] = styles.get(STYLE_WORDS[gram], 0) + 6; tgt = "style"
                elif (n == 1 and gram in WORD_NODES) or ((n > 1 or gram not in STOP) and len(gram) > 2
                                                          and self._resolve(gram) is not None):
                    node = WORD_NODES.get(gram, gram)
                    if neg:   # "no lime": drop every catalog item that is / tastes of it
                        excluded |= {k for k in self.keys if CATALOG[k]["node"] in (gram, node)
                                     or gram in CATALOG[k]["chem"] or node in CATALOG[k]["chem"]}
                        tgt = "excluded"
                    else:
                        seeds.append((node, 1.6, "you")); tgt = "ingredient"
                elif neg and (gram in THEMES or gram in ALIASES or gram in STYLE_WORDS):
                    tgt = "skipped"
                if tgt:
                    i += n; matched = True; neg = False
                    break
            if matched:
                continue
            w = toks[i]
            if w in NEGATORS:
                neg = True
            elif w not in STOP and len(w) > 3:
                close = difflib.get_close_matches(w, list(THEMES) + list(ALIASES) + list(SPIRIT_ALIASES), n=1, cutoff=0.82)
                if close and close[0] != w:
                    toks[i] = close[0]; continue           # retry the corrected (misspelled) word
                close = difflib.get_close_matches(w, self.single_vocab, n=1, cutoff=0.88)
                if close and close[0] != w:
                    toks[i] = close[0]; continue
                unknown.append(w)
            i += 1
        if not seeds and not forced:
            seeds = [(x, 0.8, "default") for x in DEFAULT_SEEDS]
        return dict(seeds=seeds, themes=themes, tags=tags, theme_tags=parsed_tags, styles=styles, forced=forced - excluded,
                    excluded=excluded, unknown=unknown)

    # ---------------------------------------------------------------- scoring
    def score_items(self, parsed: dict) -> np.ndarray:
        groups = self.seed_groups(parsed)
        agg = np.zeros(len(self.items)); wsum = 0.0
        for src, (w, profs) in groups.items():
            g = np.mean([self._affinity(p, self.items) for p in profs], 0)
            agg += w * g; wsum += w
        aff = agg / wsum if wsum else np.full(len(self.items), 0.5)
        if parsed["theme_tags"]:
            # fraction of the requested themes this item is described by (so "smoky autumn" wants both)
            cov = np.array([np.mean([1.0 if CATALOG[k]["tags"] & t else 0.0 for t in parsed["theme_tags"]]) for k in self.keys])
            aff = 0.62 * aff + 0.38 * cov
        named = {nm for nm, _, src in parsed["seeds"] if src == "you"}
        for j, k in enumerate(self.keys):
            c = CATALOG[k]
            hits = {c["node"]} | (set(c["chem"][:1]) if c["role"] != "garnish" else set())
            if named & hits and k not in parsed["excluded"]:
                aff[j] = max(aff[j], 1.3)                    # you named it and it is drinkable: use it
        for j, k in enumerate(self.keys):
            if k in parsed["excluded"]:
                aff[j] = -1.0
            elif k in parsed["forced"]:
                aff[j] = 1.5
        return aff

    def seed_groups(self, parsed: dict) -> dict:
        """{source: (weight, [profiles])}: one vote per theme, 1.6 per ingredient you named."""
        groups: dict = {}
        for name, w, src in parsed["seeds"]:
            prof = self._profile(name, [name])
            if prof["node"] is None:
                continue
            key = src if src != "you" else "you:" + name
            groups.setdefault(key, [w, []])[1].append(prof)
        return {k: (v[0], v[1]) for k, v in groups.items()}

    # ---------------------------------------------------------------- recipe assembly
    def _pool(self, role: str) -> list[int]:
        if role in SLOT_POOLS:
            return [self.keys.index(k) for k in SLOT_POOLS[role]]
        roles = role.split("|")
        return [j for j, k in enumerate(self.keys) if CATALOG[k]["role"] in roles]

    def _pick(self, role, score, chosen, used):
        best, bj = -9.0, None
        for j in self._pool(role):
            if j in used or score[j] < 0:
                continue
            compat = np.mean([self.cat_sim[j, c] for c in chosen]) if chosen else 0.5
            s = 0.62 * score[j] + 0.38 * compat
            if s > best:
                best, bj = s, j
        return bj, best

    def _build(self, style: str, base_j: int, score: np.ndarray, forced: set) -> dict | None:
        T = TEMPLATES[style]
        chosen, used, parts = [base_j], {base_j}, [(base_j, 2.0 if style not in ("spritz", "flip", "toddy") else (3.0 if style == "spritz" else 1.5))]
        for role, amt, optional in T["slots"]:
            j, s = self._pick(role, score, chosen, used)
            if j is None:
                if optional:
                    continue
                return None
            if optional and s < 0.62 and self.keys[j] not in forced and score[j] < 1.2:
                continue
            if style == "sour" and role == "liqueur":       # a liqueur sweetens too: pull back the syrup
                parts = [(pj, 0.5 if CATALOG[self.keys[pj]]["role"] == "sweetener" else pa) for pj, pa in parts]
            chosen.append(j); used.add(j); parts.append((j, amt))
        # garnishes: best overall + best seasoning (seasonings encouraged)
        gar = [j for j in self._pool("garnish") if score[j] >= 0]
        def gscore(j):
            return 0.55 * score[j] + 0.45 * np.mean([self.cat_sim[j, c] for c in chosen])
        gar.sort(key=lambda j: (score[j] >= 1.2, gscore(j)), reverse=True)   # garnishes you named first
        first = gar[0]
        season = next((j for j in gar if self.keys[j] in SEASONINGS and j != first), None)
        garn = [first] + ([season] if season is not None and self.keys[first] not in SEASONINGS else [])
        if self.keys[first] in SEASONINGS:                   # also give a fruit/citrus garnish
            other = next((j for j in gar if self.keys[j] not in SEASONINGS), None)
            if other is not None and gscore(other) > 0.5:
                garn.append(other)
        core = [j for j, _ in parts]
        quality = float(np.mean([min(score[j], 1.0) for j in core]) * 0.6 +
                        np.mean([self.cat_sim[a, b] for a in core for b in core if a < b]) * 0.4)
        return dict(style=style, parts=parts, garnish=garn, quality=quality)

    def _format(self, rec: dict, parsed: dict, score: np.ndarray, servings: int) -> dict:
        T = TEMPLATES[rec["style"]]
        ings, vol, alc = [], 0.0, 0.0
        for j, amt in rec["parts"]:
            c = CATALOG[self.keys[j]]
            if isinstance(amt, tuple):
                n = amt[1] * servings
                ings.append(dict(item=c["label"], key=c["key"], role=c["role"], amount=f"{n} dashes", oz=None, ml=None))
                continue
            if c["key"] == "egg_white":
                ings.append(dict(item="Egg white", key=c["key"], role="dairy",
                                 amount=f"{servings} egg white{'s' if servings > 1 else ''} (~1 oz each)", oz=None, ml=None))
                vol += 1.0; continue
            oz = amt * servings; ml = int(round(oz * 30 / 5) * 5)
            ings.append(dict(item=c["label"], key=c["key"], role=c["role"], amount=f"{_frac(oz)} oz ({ml} ml)", oz=oz, ml=ml))
            vol += amt
            alc += amt * SPIRIT_ABV.get(c["key"], ABV.get(c["role"], 0.0))
        total = vol * (1 + T["dilution"])
        garnish = [dict(item=CATALOG[self.keys[j]]["label"], key=self.keys[j], prep=CATALOG[self.keys[j]]["prep"],
                        seasoning=self.keys[j] in SEASONINGS) for j in rec["garnish"]]
        base = CATALOG[self.keys[rec["parts"][0][0]]]
        base_short = base["label"].split(" (")[0].replace("Blanco ", "")
        def short(lbl):
            lbl = re.sub(r"^(Fresh|Hot|Tart|Light|Dry) ", "", lbl.split(" (")[0])
            lbl = re.sub(r" (wedge|wheel|twist|peel|slice|sprig|leaf|stick|ribbon|beans|bean|powder|rim)$", "", lbl, flags=re.I)
            return re.sub(r" (juice|syrup|purée|liqueur|water|cream|brewed)$", "", lbl, flags=re.I)
        flav = [j for j, _ in rec["parts"][1:] + [(g, 0) for g in rec["garnish"]]
                if CATALOG[self.keys[j]]["role"] not in ("mixer", "sour", "dairy", "bitters")
                and not set(short(CATALOG[self.keys[j]]["label"]).lower().split()) & set(base_short.lower().split())]
        flavor = max(flav, key=lambda j: score[j], default=None)
        adj = parsed["themes"][0].title() if parsed["themes"] else ""
        fl = short(CATALOG[self.keys[flavor]]["label"]) if flavor is not None else ""
        name = " ".join(w for w in [adj, fl, base_short, T["name"]] if w).title()
        return dict(name=re.sub(r"\b(\w+) \1\b", r"\1", name, flags=re.I), style=rec["style"], glass=T["glass"], method=T["method"],
                    ingredients=ings, garnish=garnish, servings=servings,
                    volume=f"{_frac(total * servings)} oz ({int(round(total * servings * 30 / 5) * 5)} ml) after dilution",
                    abv=round(100 * alc / total, 1) if total else 0.0, score=round(rec["quality"], 3),
                    why=self._why(rec, parsed))

    def _why(self, rec: dict, parsed: dict) -> list[str]:
        notes = []
        idxs = [j for j, _ in rec["parts"]] + rec["garnish"]
        best = []
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                n, ex = self.shared_compounds(self.items[idxs[a]], self.items[idxs[b]])
                if n:
                    best.append((n, idxs[a], idxs[b], ex))
        for n, a, b, ex in sorted(best, reverse=True)[:2]:
            notes.append(f"{CATALOG[self.keys[a]]['label']} + {CATALOG[self.keys[b]]['label']}: share {n} flavor compounds"
                         + (f" (e.g. {', '.join(ex)})" if ex else ""))
        its = [self.items[j] for j in idxs]
        for src, (_, profs) in self.seed_groups(parsed).items():
            if src == "default":
                continue
            A = np.array([self._affinity(p, its) for p in profs])          # seeds x recipe items
            k = int(A.mean(0).argmax()); s = int(A[:, k].argmax())
            seed = self.names[profs[s]["node"]].replace("_", " ")
            what = f"'{src}'" if not src.startswith("you:") else f"your {src[4:].replace('_', ' ')}"
            notes.append(f"{CATALOG[self.keys[idxs[k]]]['label']} carries {what} (closest to {seed})")
        return notes[:5]

    # ---------------------------------------------------------------- public API
    def recommend(self, prompt: str, servings: int = 1, n: int = 3) -> dict:
        servings = max(1, min(int(servings), 50))
        parsed = self.parse(prompt)
        score = self.score_items(parsed)
        st = dict(sour=2.0, highball=1.6, stirred=1.4, tiki=1.0, flip=0.8, spritz=0.9, mule=0.9, toddy=0.6)
        for k, v in parsed["styles"].items():
            st[k] = st.get(k, 0) + v
        forced_bases = [self.keys.index(k) for k in parsed["forced"] if CATALOG[k]["role"] in ("spirit", "sparkling")]
        cands = []
        for style, sw in sorted(st.items(), key=lambda kv: -kv[1])[:5]:
            base_role = TEMPLATES[style]["base"][0]
            pool = [j for j in self._pool(base_role) if score[j] >= 0]
            if forced_bases:
                fb = [j for j in forced_bases if CATALOG[self.keys[j]]["role"] == base_role]
                if not fb:
                    continue
                pool = fb
            pool.sort(key=lambda j: -score[j])
            for b in pool[:4]:
                rec = self._build(style, b, score, parsed["forced"])
                if rec:
                    rec["rank"] = rec["quality"] + 0.06 * sw + 0.25 * min(score[b], 1.0)
                    cands.append(rec)
        cands.sort(key=lambda r: -r["rank"])
        picked, bases, styles = [], set(), {}
        for r in cands:
            b = r["parts"][0][0]
            if (b in bases and not forced_bases) or styles.get(r["style"], 0) >= 2:
                continue
            if any(r["style"] == p["style"] and b == p["parts"][0][0] for p in picked):
                continue
            picked.append(r); bases.add(b); styles[r["style"]] = styles.get(r["style"], 0) + 1
            if len(picked) == n:
                break
        top = np.argsort(-score)
        return dict(prompt=prompt,
                    understood=dict(themes=parsed["themes"], ingredients=sorted({s for s, _, src in parsed["seeds"] if src == "you"}),
                                    spirits=sorted(CATALOG[k]["label"] for k in parsed["forced"]),
                                    excluded=sorted(CATALOG[k]["label"] for k in parsed["excluded"]),
                                    styles=sorted(parsed["styles"], key=lambda s: -parsed["styles"][s]),
                                    ignored=parsed["unknown"]),
                    top_matches=[CATALOG[self.keys[j]]["label"] for j in top[:8] if score[j] > 0],
                    drinks=[self._format(r, parsed, score, servings) for r in picked])
