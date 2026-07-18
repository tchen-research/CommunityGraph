#!/usr/bin/env python3
"""Remove people who have no edges at all (no papers, advising, curated
connection, or co-organizer tie). Updates people.yaml and the attendee lists
in workshops.yaml. Prints the removed names. KEEP protects ids from pruning."""

import yaml
from pathlib import Path

DATA = Path("/home/tyler/Documents/Research Code/NLA_graph/data")
KEEP: set[str] = set()  # ids to keep even if isolated


class Dumper(yaml.SafeDumper):
    pass


def str_rep(dumper, s):
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", s)


Dumper.add_representer(str, str_rep)


def main():
    people = yaml.safe_load((DATA / "people.yaml").read_text())
    papers = yaml.safe_load((DATA / "papers.yaml").read_text()) or []
    advising = yaml.safe_load((DATA / "advising.yaml").read_text()) or []
    connections = yaml.safe_load((DATA / "connections.yaml").read_text()) or []

    connected = set()
    for p in papers:
        if len(p.get("authors") or []) >= 2:
            connected.update(p["authors"])
    for r in advising:
        connected.update((r["advisor"], r["student"]))
    for c in connections:
        connected.update(c.get("between") or [])

    removed = [p for p in people if p["id"] not in connected and p["id"] not in KEEP]
    kept = [p for p in people if p["id"] in connected or p["id"] in KEEP]

    header_p = (
        "# One entry per person. id is referenced by the other data files.\n"
        "# area: research-area group for node colors (see config.yaml node_groups).\n"
        "# Keep affiliations written consistently - the same_institution factor is\n"
        "# computed by exact (case-insensitive) match.\n"
        "# Optional keys: website, photo (direct image URL), topics (list), notes.\n"
    )
    (DATA / "people.yaml").write_text(
        header_p + yaml.dump(kept, Dumper=Dumper, allow_unicode=True,
                             sort_keys=False, width=88))

    print(f"kept {len(kept)}, removed {len(removed)}:")
    for p in sorted(removed, key=lambda x: x["name"]):
        print(f"  - {p['name']} ({p['affiliation']})")


if __name__ == "__main__":
    main()
