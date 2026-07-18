#!/usr/bin/env python3
"""Replace each person's freeform `topics` with vocabulary tags from the
tagging agent's output (topics_assign.yaml in the scratchpad or next to this
script; newest wins). Validates tags against data/topics.yaml."""

import yaml
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
SEARCH_DIRS = [
    Path(__file__).resolve().parent,
    Path("/tmp/claude-1000/-home-tyler-Documents-Research-Code-NLA-graph/"
         "8d642458-d1ef-41eb-a9e6-4922b217af4b/scratchpad"),
]


class Dumper(yaml.SafeDumper):
    pass


def str_rep(dumper, s):
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", s)


Dumper.add_representer(str, str_rep)


def main():
    candidates = [d / "topics_assign.yaml" for d in SEARCH_DIRS
                  if (d / "topics_assign.yaml").exists()]
    if not candidates:
        print("topics_assign.yaml not found")
        return 1
    src = max(candidates, key=lambda c: c.stat().st_mtime)
    doc = yaml.safe_load(src.read_text()) or {}
    assignments = doc.get("assignments") or {}
    proposed = doc.get("proposed") or {}

    vocab = {t["id"] for t in yaml.safe_load((DATA / "topics.yaml").read_text())}
    people = yaml.safe_load((DATA / "people.yaml").read_text())

    tagged = untouched = 0
    bad = []
    for p in people:
        tags = assignments.get(p["id"])
        if not tags:
            untouched += 1
            continue
        good = [t for t in tags if t in vocab]
        bad += [f"{p['id']}: {t}" for t in tags if t not in vocab]
        p["topics"] = good
        tagged += 1

    header = (
        "# One entry per person. id is referenced by the other data files.\n"
        "# area: research-area group for node colors (see config.yaml node_groups).\n"
        "# topics: tag ids from topics.yaml (drives the topic filter).\n"
        "# Keep affiliations written consistently - the same_institution factor is\n"
        "# computed by exact (case-insensitive) match.\n"
        "# Optional keys: website, photo (direct image URL), notes.\n"
    )
    (DATA / "people.yaml").write_text(
        header + yaml.dump(people, Dumper=Dumper, allow_unicode=True,
                           sort_keys=False, width=88))
    print(f"tagged {tagged}, untouched {untouched} (from {src})")
    if bad:
        print(f"  dropped unknown tags: {bad}")
    if proposed:
        print(f"  agent-proposed new topics (not applied): {proposed}")
    return 0


if __name__ == "__main__":
    main()
