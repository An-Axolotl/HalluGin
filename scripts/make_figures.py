"""Make README figures: flavor-compound similarity graphs for example prompts.
    python3 scripts/make_figures.py      (needs matplotlib + networkx)
"""
import sys
from pathlib import Path
import itertools
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from drinkrec.catalog import CATALOG
from drinkrec.engine import Recommender

ROLE_COL = {"spirit": "#b5562f", "liqueur": "#d98b3a", "fortified": "#8e3b5a", "sparkling": "#d9b83a", "beer": "#a07a3a",
            "sour": "#6aa84f", "sweetener": "#c27ba0", "juice": "#e69138", "mixer": "#6fa8dc", "hot": "#7f6000",
            "dairy": "#bcbcbc", "bitters": "#5b3a29", "garnish": "#38761d"}
EXAMPLES = [("cozy winter warmer", 0), ("something tropical for the beach", 0), ("smoky autumn with maple", 0),
            ("basil strawberry spritz", 0)]

r = Recommender()


def chem_cos(a, b):
    A, B = r.items[a]["chem"], r.items[b]["chem"]
    return len(A & B) / np.sqrt(len(A) * len(B)) if A and B else 0.0


def figure(prompt, k, out):
    d = r.recommend(prompt, 1)["drinks"][k]
    keys = [i["key"] for i in d["ingredients"]] + [g["key"] for g in d["garnish"]]
    idx = [r.keys.index(x) for x in keys]
    labels = [CATALOG[x]["label"].split(" (")[0] for x in keys]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.4), gridspec_kw=dict(width_ratios=[1.25, 1]))
    G = nx.Graph()
    for a, b in itertools.combinations(range(len(idx)), 2):
        n, ex = r.shared_compounds(r.items[idx[a]], r.items[idx[b]], 2)
        if n:
            G.add_edge(a, b, n=n, c=chem_cos(idx[a], idx[b]), ex=ex)
    G.add_nodes_from(range(len(idx)))
    pos = nx.circular_layout(G)
    ws = [G[u][v]["c"] for u, v in G.edges]
    mx = max(ws) if ws else 1
    nx.draw_networkx_edges(G, pos, ax=ax1, width=[0.5 + 7 * w / mx for w in ws],
                           edge_color=[plt.cm.YlOrBr(0.25 + 0.75 * w / mx) for w in ws])
    best = sorted(G.edges, key=lambda e: -G.edges[e]["n"])[:3]
    txt = "Most shared compounds:\n" + "\n".join(
        f"{labels[u]} + {labels[v]}: {G.edges[u, v]['n']}  (e.g. {', '.join(G.edges[u, v]['ex'])})" for u, v in best)
    ax1.text(0, -1.62, txt, ha="center", va="top", fontsize=9, family="monospace",
             bbox=dict(boxstyle="round,pad=0.4", fc="#faf6f1", ec="#ddd"))
    nx.draw_networkx_nodes(G, pos, ax=ax1, node_size=1500, edgecolors="white", linewidths=2,
                           node_color=[ROLE_COL[CATALOG[x]["role"]] for x in keys])
    for i, (x, y) in pos.items():
        ax1.text(x * 1.32, y * 1.22 + (0.05 if y >= 0 else -0.05), labels[i], ha="center", va="center", fontsize=10, weight="bold")
    roles = sorted({CATALOG[x]["role"] for x in keys})
    ax1.legend(handles=[plt.Line2D([], [], marker="o", ls="", ms=10, color=ROLE_COL[ro], label=ro) for ro in roles],
               loc="upper center", ncol=len(roles), frameon=False, bbox_to_anchor=(0.5, 1.0), fontsize=9)
    ax1.set_title("Shared flavor compounds (FlavorGraph)\nedge width = compound-set cosine similarity", fontsize=11, pad=34)
    ax1.set_xlim(-1.7, 1.7); ax1.set_ylim(-1.45, 1.45); ax1.axis("off")
    M = np.array([[chem_cos(a, b) if a != b else np.nan for b in idx] for a in idx])
    im = ax2.imshow(M, cmap="YlOrBr", vmin=0, vmax=np.nanmax(M))
    ax2.set_xticks(range(len(idx)), labels, rotation=40, ha="right", fontsize=9)
    ax2.set_yticks(range(len(idx)), labels, fontsize=9)
    for a in range(len(idx)):
        for b in range(len(idx)):
            if a != b:
                ax2.text(b, a, f"{M[a, b]:.2f}", ha="center", va="center", fontsize=7,
                         color="white" if M[a, b] > 0.6 * np.nanmax(M) else "black")
    fig.colorbar(im, ax=ax2, fraction=0.046, label="chemical similarity")
    ax2.set_title("Pairwise chemical similarity", fontsize=11)
    recipe = ", ".join(f"{i['amount'].split(' (')[0]} {i['item'].split(' (')[0]}" for i in d["ingredients"])
    fig.suptitle(f"“{prompt}”  →  {d['name']}\n{recipe}  +  {', '.join(g['item'] for g in d['garnish'])}",
                 fontsize=12.5, weight="bold")
    fig.tight_layout(); fig.savefig(out, dpi=120, facecolor="white", bbox_inches="tight", pad_inches=0.3); plt.close(fig)
    print(out)


for n, (p, k) in enumerate(EXAMPLES):
    figure(p, k, ROOT / "images" / f"graph_{n + 1}_{p.split()[0] if p.split()[0] != 'something' else 'tropical'}.png")
