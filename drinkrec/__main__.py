"""Command line:  python3 -m drinkrec "smoky autumn with maple" --servings 4 [--json]"""
import argparse, json
from .engine import Recommender


def show(out):
    u = out["understood"]
    bits = [f"themes: {', '.join(u['themes'])}" if u["themes"] else "",
            f"ingredients: {', '.join(x.replace('_', ' ') for x in u['ingredients'])}" if u["ingredients"] else "",
            f"spirits: {', '.join(u['spirits'])}" if u["spirits"] else "",
            f"without: {', '.join(u['excluded'])}" if u["excluded"] else ""]
    print("Understood ->", "; ".join(b for b in bits if b) or "nothing specific, using a balanced default")
    for n, d in enumerate(out["drinks"], 1):
        print(f"\n{n}. {d['name']}   ({d['servings']} serving{'s' if d['servings'] > 1 else ''}, ~{d['abv']}% ABV)")
        print(f"   Glass: {d['glass']}")
        for i in d["ingredients"]:
            print(f"   - {i['amount']:<18} {i['item']}")
        for g in d["garnish"]:
            print(f"   + garnish: {g['prep']}")
        print(f"   Method: {d['method']}")
        for w in d["why"]:
            print(f"   why: {w}")


def main():
    ap = argparse.ArgumentParser(description="FlavorGraph drink recommender (offline)")
    ap.add_argument("prompt", nargs="+")
    ap.add_argument("--servings", type=int, default=1)
    ap.add_argument("-n", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    out = Recommender().recommend(" ".join(a.prompt), servings=a.servings, n=a.n)
    print(json.dumps(out, indent=2, ensure_ascii=False) if a.json else "", end="") if a.json else show(out)


if __name__ == "__main__":
    main()
