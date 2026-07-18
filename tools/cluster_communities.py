#!/usr/bin/env python3
"""Detect collaboration communities (weighted Louvain over the closeness
scores at their default weights) and write data/clusters.yaml, which build.py
folds into the app as the "collaboration community" coloring.

Re-run after substantial data changes:  python3 tools/cluster_communities.py
Requires networkx. Community labels below are hand-named; adjust after
re-running if membership shifts.
"""
import json
from collections import Counter
from pathlib import Path

import networkx as nx
import yaml

ROOT = Path(__file__).resolve().parent.parent

raw = (ROOT / "docs" / "data.js").read_text()
D = json.loads(raw[raw.index("=") + 1:].rstrip().rstrip(";"))

weights = {f["id"]: f["default_weight"] for f in D["factors"]}
maxes = {f["id"]: f["max"] for f in D["factors"]}

G = nx.Graph()
for p in D["people"]:
    G.add_node(p["id"])
for e in D["edges"]:
    s = sum(weights[f] * min(v, maxes[f]) / maxes[f]
            for f, v in e["factors"].items() if f in weights)
    if s > 0:
        G.add_edge(e["source"], e["target"], weight=s)

comms = sorted(nx.community.louvain_communities(G, weight="weight", seed=7),
               key=len, reverse=True)
print(f"{len(comms)} communities, modularity "
      f"{nx.community.modularity(G, comms, weight='weight'):.3f}")

# Hand-curated names for the communities found at seed=7 on the July 2026
# data. Matching is by strongest-anchor membership so the names survive small
# membership shifts; falls back to a generic label.
ANCHOR_LABELS = [
    ("james-demmel", "Berkeley, HPC & software"),
    ("misha-kilmer", "Inverse problems & regularization"),
    ("deanna-needell", "Stochastic iterative & UT Austin"),
    ("petros-drineas", "TCS foundations & sketching"),
    ("joel-tropp", "Low-rank & approximation theory"),
    ("david-woodruff", "Trace estimation & matvec queries"),
    ("valeria-simoncini", "Matrix equations & Krylov theory"),
    ("haim-avron", "IBM & Minnesota orbit"),
]

out_comms, assignments = [], {}
used = set()
for i, c in enumerate(comms):
    label = next((lbl for a, lbl in ANCHOR_LABELS if a in c and lbl not in used),
                 f"Community {i + 1}")
    used.add(label)
    cid = f"c{i}"
    out_comms.append({"id": cid, "label": label})
    for n in sorted(c):
        assignments[n] = cid
    names = [p["name"] for p in D["people"] if p["id"] in c]
    print(f"  {cid} ({len(c):3d}) {label}: {', '.join(sorted(names)[:4])}, ...")

isolated = [p["id"] for p in D["people"] if p["id"] not in assignments]
for pid in isolated:
    assignments[pid] = out_comms[0]["id"]
if isolated:
    print(f"  note: {len(isolated)} people had no edges; assigned to c0")

(ROOT / "data" / "clusters.yaml").write_text(
    "# Collaboration communities detected by tools/cluster_communities.py\n"
    "# (weighted Louvain, default metric weights, seed 7). Used by the app's\n"
    "# 'color by collaboration community' mode. Regenerate after data changes.\n"
    + yaml.safe_dump({"communities": out_comms,
                      "assignments": assignments},
                     sort_keys=False, allow_unicode=True, width=88))
print("wrote data/clusters.yaml")
