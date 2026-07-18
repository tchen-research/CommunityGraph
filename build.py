#!/usr/bin/env python3
"""Compile the human-readable YAML files in data/ into site/data.js.

Usage:
    python3 build.py

Reads   data/config.yaml       metric factors, node groups
        data/people.yaml       one entry per person (with area/website/photo)
        data/papers.yaml       papers with >= 2 in-graph authors -> coauthor edges
        data/advising.yaml     directed advisor -> student relations
        data/connections.yaml  curated edge annotations (notes/links/collaboration)

Writes  docs/data.js           window.GRAPH_DATA = {...} consumed by the app

The build validates cross-references (unknown ids, duplicate edges/papers,
out-of-range values fail the build) and computes the derived factors declared
with `kind: computed` in config.
"""

import datetime
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "docs" / "data.js"

errors: list[str] = []
warnings: list[str] = []


def load(name, default, required=True):
    path = DATA / name
    if not path.exists():
        if required:
            errors.append(f"missing data file: {path}")
        return default
    with open(path) as f:
        return yaml.safe_load(f) or default


def pair_key(a, b):
    return tuple(sorted((a, b)))


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


ADVISING_VALUE = {"phd": 1.0, "postdoc": 0.7}


def main():
    config = load("config.yaml", {})
    people = load("people.yaml", [])
    topics = load("topics.yaml", [], required=False)
    topic_ids = {t["id"] for t in topics}
    papers_in = load("papers.yaml", [], required=False)
    advising_in = load("advising.yaml", [], required=False)
    connections = load("connections.yaml", [])

    factors = config.get("factors", [])
    curated_ids = [f["id"] for f in factors if f.get("kind") == "curated"]
    groups = config.get("node_groups", [])
    group_ids = {g["id"] for g in groups}

    # ---- people ------------------------------------------------------------
    by_id = {}
    for p in people:
        pid = p.get("id")
        if not pid:
            errors.append(f"person without id: {p.get('name', p)}")
            continue
        if pid in by_id:
            errors.append(f"duplicate person id: {pid}")
            continue
        if not p.get("name"):
            errors.append(f"person {pid} has no name")
        if p.get("area") and p["area"] not in group_ids:
            warnings.append(f"person {pid}: unknown area '{p['area']}'")
        if topic_ids:
            for t in p.get("topics") or []:
                if t not in topic_ids:
                    warnings.append(f"person {pid}: topic '{t}' not in topics.yaml")
        by_id[pid] = p

    # ---- papers ------------------------------------------------------------
    papers = []          # deduped, in output order
    by_title = {}        # normalized title -> index into papers
    pair_papers = {}     # (a, b) -> [paper index]
    for raw in papers_in:
        title = raw.get("title")
        if not title:
            errors.append(f"paper without title: {raw}")
            continue
        authors = [a for a in (raw.get("authors") or [])]
        unknown = [a for a in authors if a not in by_id]
        if unknown:
            errors.append(f"paper '{title[:50]}': unknown author ids {unknown}")
            continue
        authors = list(dict.fromkeys(authors))  # dedupe, keep order
        if len(authors) < 2:
            warnings.append(f"paper '{title[:50]}': fewer than 2 known authors, skipped")
            continue
        key = norm_title(title)
        if key in by_title:
            # same paper reported twice (e.g. by two research batches): merge authors
            existing = papers[by_title[key]]
            merged = list(dict.fromkeys(existing["authors"] + authors))
            existing["authors"] = merged
            continue
        by_title[key] = len(papers)
        papers.append({
            "title": title.strip(),
            "year": raw.get("year"),
            "venue": raw.get("venue", ""),
            "url": raw.get("url", ""),
            "note": raw.get("note", ""),
            "authors": authors,
        })
    for idx, paper in enumerate(papers):
        auth = paper["authors"]
        for i, a in enumerate(auth):
            for b in auth[i + 1:]:
                pair_papers.setdefault(pair_key(a, b), []).append(idx)

    # ---- advising ----------------------------------------------------------
    advising = []
    seen_adv = set()
    pair_advising = {}
    for rec in advising_in:
        a, s, kind = rec.get("advisor"), rec.get("student"), rec.get("kind")
        if a not in by_id or s not in by_id:
            errors.append(f"advising {a} -> {s}: unknown id")
            continue
        if a == s:
            errors.append(f"advising self-loop: {a}")
            continue
        if kind not in ADVISING_VALUE:
            errors.append(f"advising {a} -> {s}: kind must be one of {list(ADVISING_VALUE)}")
            continue
        if (a, s, kind) in seen_adv:
            continue
        seen_adv.add((a, s, kind))
        advising.append({"advisor": a, "student": s, "kind": kind})
        pair_advising.setdefault(pair_key(a, s), []).append(advising[-1])

    # ---- curated edge annotations ------------------------------------------
    known_edge_keys = {"between", "notes", "links"} | set(curated_ids)
    edges = {}

    def blank_edge(key):
        return {
            "source": key[0],
            "target": key[1],
            "factors": {fid: 0 for fid in curated_ids},
            "notes": "",
            "links": [],
        }

    for c in connections:
        between = c.get("between") or []
        if len(between) != 2:
            errors.append(f"connection needs exactly 2 people: {c}")
            continue
        a, b = between
        if a == b:
            errors.append(f"self-loop connection: {a}")
            continue
        missing = [x for x in (a, b) if x not in by_id]
        if missing:
            errors.append(f"connection {a} - {b}: unknown id(s) {missing}")
            continue
        key = pair_key(a, b)
        if key in edges:
            errors.append(f"duplicate connection: {a} - {b}")
            continue
        for k in c:
            if k not in known_edge_keys:
                warnings.append(f"connection {a} - {b}: unknown key '{k}' (typo?)")
        e = blank_edge(key)
        for f in factors:
            if f.get("kind") != "curated":
                continue
            v = c.get(f["id"], 0) or 0
            if not (0 <= v <= f["max"]):
                errors.append(f"connection {a} - {b}: {f['id']}={v} outside 0..{f['max']}")
            e["factors"][f["id"]] = v
        e["notes"] = (c.get("notes") or "").strip()
        e["links"] = c.get("links", []) or []
        edges[key] = e

    # ---- edges implied by papers / advising --------------------------------
    for key in pair_papers:
        edges.setdefault(key, blank_edge(key))
    for key in pair_advising:
        edges.setdefault(key, blank_edge(key))

    # ---- computed factors --------------------------------------------------
    for key, e in edges.items():
        a, b = e["source"], e["target"]
        jp = pair_papers.get(key, [])
        adv = pair_advising.get(key, [])
        for f in factors:
            if f.get("kind") != "computed":
                continue
            rule = f.get("compute")
            if rule == "papers":
                e["factors"][f["id"]] = len(jp)
            elif rule == "advising":
                e["factors"][f["id"]] = max(
                    (ADVISING_VALUE[r["kind"]] for r in adv), default=0)
            elif rule == "same_institution":
                aff_a = (by_id[a].get("affiliation") or "").strip().lower()
                aff_b = (by_id[b].get("affiliation") or "").strip().lower()
                e["factors"][f["id"]] = 1 if aff_a and aff_a == aff_b else 0
            else:
                errors.append(f"unknown compute rule '{rule}' for factor {f['id']}")
        e["paper_ids"] = jp
        e["advising"] = adv

    # ---- report ------------------------------------------------------------
    for msg in warnings:
        print(f"  warning: {msg}")
    if errors:
        for msg in errors:
            print(f"  ERROR: {msg}", file=sys.stderr)
        print(f"\nbuild failed with {len(errors)} error(s)", file=sys.stderr)
        return 1

    connected = set()
    for e in edges.values():
        connected.add(e["source"])
        connected.add(e["target"])
    isolated = sorted(set(by_id) - connected)
    if isolated:
        print(f"  note: {len(isolated)} people with no edges "
              f"(prune candidates): {', '.join(isolated)}")

    # ---- emit --------------------------------------------------------------
    default_group = groups[0]["id"] if groups else "default"
    person_papers = {}
    for idx, paper in enumerate(papers):
        for a in paper["authors"]:
            person_papers.setdefault(a, []).append(idx)

    out = {
        "title": config.get("title", "Community Graph"),
        "subtitle": config.get("subtitle", "").strip(),
        "generated": datetime.date.today().isoformat(),
        "factors": [
            {
                "id": f["id"],
                "label": f.get("label", f["id"]),
                "kind": f.get("kind", "curated"),
                "compute": f.get("compute", ""),
                "max": f["max"],
                "default_weight": f.get("default_weight", 1.0),
                "description": (f.get("description") or "").strip(),
            }
            for f in factors
        ],
        "groups": [{"id": g["id"], "label": g.get("label", g["id"])} for g in groups],
        "topics": [{"id": t["id"], "label": t.get("label", t["id"])} for t in topics],
        "papers": papers,
        "advising": advising,
        "people": [
            {
                "id": pid,
                "name": p.get("name", pid),
                "affiliation": p.get("affiliation", ""),
                "website": p.get("website", ""),
                "photo": p.get("photo", ""),
                "topics": p.get("topics", []) or [],
                "notes": (p.get("notes") or "").strip(),
                "group": p.get("area") if p.get("area") in group_ids else default_group,
                "papers": person_papers.get(pid, []),
            }
            for pid, p in sorted(by_id.items(), key=lambda kv: kv[1].get("name", ""))
        ],
        "edges": sorted(edges.values(), key=lambda e: (e["source"], e["target"])),
    }

    OUT.write_text(
        "// Generated by build.py - do not edit by hand; edit data/*.yaml instead.\n"
        "window.GRAPH_DATA = " + json.dumps(out, indent=1, ensure_ascii=False) + ";\n"
    )
    print(
        f"wrote {OUT.relative_to(ROOT)}: {len(out['people'])} people, "
        f"{len(out['edges'])} edges, {len(papers)} papers, "
        f"{len(advising)} advising relations"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
