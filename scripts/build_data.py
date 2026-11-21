"""Compress the FlavorGraph release (vendor/FlavorGraph) into drinkrec/data/flavorgraph.npz.

Keeps every ingredient (so any food in a prompt can steer the result), the ingredient->flavor-compound
links (chemical similarity), the ingredient<->ingredient pairing scores, and the 300-d ingredient
embeddings shipped in the FlavorGraph repo. Run once; the app only needs the .npz afterwards.
    python3 scripts/build_data.py [path/to/FlavorGraph]
"""
import csv, pickle, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FG = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "vendor" / "FlavorGraph"

ingr, comp = {}, {}                         # node_id -> name
for r in csv.DictReader(open(FG / "input" / "nodes_191120.csv")):
    if not r["name"]:
        continue
    (ingr if r["node_type"] == "ingredient" else comp)[int(r["node_id"])] = r["name"]

ingr_ids = sorted(ingr); comp_ids = sorted(comp)
ii = {n: i for i, n in enumerate(ingr_ids)}; ci = {n: i for i, n in enumerate(comp_ids)}

ic, pairs = [], []
for r in csv.DictReader(open(FG / "input" / "edges_191120.csv")):
    a, b, t = int(r["id_1"]), int(r["id_2"]), r["edge_type"]
    if t in ("ingr-fcomp", "ingr-dcomp"):
        ing, cmp_ = (a, b) if a in ii else (b, a)
        if ing in ii and cmp_ in ci:
            ic.append((ii[ing], ci[cmp_]))
    elif t == "ingr-ingr" and a in ii and b in ii:
        pairs.append((ii[a], ii[b], float(r["score"])))

emb_raw = pickle.load(open(FG / "output" / "kitchenette_embeddings.pkl", "rb"))
names = [ingr[n] for n in ingr_ids]
emb = np.zeros((len(names), 300), np.float16); has_emb = np.zeros(len(names), bool)
for i, nm in enumerate(names):
    if nm in emb_raw:
        v = np.asarray(emb_raw[nm], np.float32); emb[i] = v / (np.linalg.norm(v) + 1e-9); has_emb[i] = True

ic = np.array(sorted(set(ic)), np.int32); pairs = np.array(pairs, np.float64)
out = ROOT / "drinkrec" / "data" / "flavorgraph.npz"; out.parent.mkdir(parents=True, exist_ok=True)
np.savez_compressed(out,
    ingr_names=np.array(names), comp_names=np.array([comp[c] for c in comp_ids]),
    ic=ic, pair_a=pairs[:, 0].astype(np.int32), pair_b=pairs[:, 1].astype(np.int32),
    pair_s=pairs[:, 2].astype(np.float32), emb=emb, has_emb=has_emb)
print(out, f"{out.stat().st_size/1e6:.1f} MB", len(names), "ingredients", len(comp_ids), "compounds",
      len(ic), "ingr-compound links", len(pairs), "pairings", int(has_emb.sum()), "embeddings")
