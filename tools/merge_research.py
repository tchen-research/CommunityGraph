#!/usr/bin/env python3
"""Merge research_[A-D].yaml (agent outputs) into the data/ directory:
- website/photo -> people.yaml
- papers -> papers.yaml (deduped by normalized title, authors unioned)
- advising -> appended to advising.yaml (deduped against existing records)
Safe to re-run; it rebuilds people.yaml/papers.yaml from scratch each time and
only appends genuinely-new advising records."""

import re
import sys
from pathlib import Path

import yaml

# Research files are searched for next to this script first, then in the
# session scratchpad the agents originally wrote to.
SEARCH_DIRS = [
    Path(__file__).resolve().parent,
    Path("/tmp/claude-1000/-home-tyler-Documents-Research-Code-NLA-graph/"
         "8d642458-d1ef-41eb-a9e6-4922b217af4b/scratchpad"),
]
DATA = Path(__file__).resolve().parent.parent / "data"


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


class Dumper(yaml.SafeDumper):
    pass


def str_rep(dumper, s):
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", s)


Dumper.add_representer(str, str_rep)


def main():
    people = yaml.safe_load((DATA / "people.yaml").read_text())
    by_id = {p["id"]: p for p in people}
    existing_adv = yaml.safe_load((DATA / "advising.yaml").read_text()) or []
    adv_pairs = {(r["advisor"], r["student"]) for r in existing_adv}
    adv_keys = {(r["advisor"], r["student"], r["kind"]) for r in existing_adv}

    papers = {}          # norm title -> paper dict
    new_adv = []
    stats = {"files": 0, "people": 0, "websites": 0, "photos": 0,
             "papers_seen": 0, "adv_seen": 0, "skipped": []}

    names = sorted({p.name for d in SEARCH_DIRS for p in d.glob("research_*.yaml")})
    if not names:
        print("  no research_*.yaml files found")
    for name in names:
        letter = name.removeprefix("research_").removesuffix(".yaml")
        candidates = [d / name for d in SEARCH_DIRS if (d / name).exists()]
        # newest wins: agents keep rewriting the scratchpad copy while tools/
        # holds point-in-time snapshots
        f = max(candidates, key=lambda c: c.stat().st_mtime)
        try:
            doc = yaml.safe_load(f.read_text()) or {}
        except yaml.YAMLError as e:
            print(f"  ERROR: research_{letter}.yaml is invalid YAML: {e}")
            continue
        stats["files"] += 1
        for entry in doc.get("people", []) or []:
            pid = entry.get("id")
            if pid not in by_id:
                stats["skipped"].append(f"{letter}: unknown person {pid}")
                continue
            stats["people"] += 1
            p = by_id[pid]
            if entry.get("website") and not p.get("website"):
                p["website"] = entry["website"].strip()
                stats["websites"] += 1
            if entry.get("photo") and not p.get("photo"):
                p["photo"] = entry["photo"].strip()
                stats["photos"] += 1
            for r in entry.get("advising", []) or []:
                a, s, k = r.get("advisor"), r.get("student"), r.get("kind")
                stats["adv_seen"] += 1
                if a not in by_id or s not in by_id or k not in ("phd", "postdoc"):
                    stats["skipped"].append(f"{letter}: bad advising {a}->{s} ({k})")
                    continue
                if (s, a) in adv_pairs:
                    stats["skipped"].append(
                        f"{letter}: advising {a}->{s} conflicts with existing {s}->{a} - kept existing")
                    continue
                if (a, s, k) in adv_keys:
                    continue
                adv_keys.add((a, s, k))
                adv_pairs.add((a, s))
                new_adv.append({"advisor": a, "student": s, "kind": k})
            for paper in entry.get("papers", []) or []:
                title = (paper.get("title") or "").strip()
                if not title:
                    continue
                stats["papers_seen"] += 1
                authors = [x for x in (paper.get("authors") or [])]
                bad = [x for x in authors if x not in by_id]
                if bad:
                    stats["skipped"].append(f"{letter}: paper '{title[:40]}' unknown authors {bad}")
                    authors = [x for x in authors if x in by_id]
                authors = list(dict.fromkeys(authors))
                if len(authors) < 2:
                    stats["skipped"].append(f"{letter}: paper '{title[:40]}' has <2 known authors")
                    continue
                key = norm_title(title)
                if key in papers:
                    ex = papers[key]
                    ex["authors"] = list(dict.fromkeys(ex["authors"] + authors))
                    for field in ("year", "venue", "url", "note"):
                        if not ex.get(field) and paper.get(field):
                            ex[field] = paper[field]
                else:
                    rec = {"title": title, "year": paper.get("year"),
                           "venue": paper.get("venue"), "url": paper.get("url"),
                           "authors": authors}
                    if paper.get("note"):
                        rec["note"] = paper["note"]
                    papers[key] = {k: v for k, v in rec.items() if v}

    # ---- write people.yaml -------------------------------------------------
    header = (
        "# One entry per person. id is referenced by the other data files.\n"
        "# area: research-area group for node colors (see config.yaml node_groups).\n"
        "# Keep affiliations written consistently - the same_institution factor is\n"
        "# computed by exact (case-insensitive) match.\n"
        "# Optional keys: website, photo (direct image URL), topics (list), notes.\n"
    )
    (DATA / "people.yaml").write_text(
        header + yaml.dump(people, Dumper=Dumper, allow_unicode=True,
                           sort_keys=False, width=88))

    # ---- write papers.yaml -------------------------------------------------
    plist = sorted(papers.values(), key=lambda p: (p.get("year") or 0, p["title"]))
    (DATA / "papers.yaml").write_text(
        "# Papers with >= 2 in-graph authors; these generate the coauthorship\n"
        "# edges/factor. `authors` lists ids from people.yaml that are on the\n"
        "# paper (outside coauthors are not tracked; use `note` when that\n"
        "# matters). Collected from DBLP/homepages by research agents, "
        "July 2026.\n"
        + yaml.dump(plist, Dumper=Dumper, allow_unicode=True,
                    sort_keys=False, width=88))

    # ---- append new advising -----------------------------------------------
    if new_adv:
        new_adv.sort(key=lambda r: (r["advisor"], r["student"]))
        lines = ["", "# --- added from the research agents (July 2026) ---"]
        for r in new_adv:
            lines.append(f"- {{advisor: {r['advisor']}, student: {r['student']}, kind: {r['kind']}}}")
        with open(DATA / "advising.yaml", "a") as f:
            f.write("\n".join(lines) + "\n")

    print(f"merged {stats['files']} files: {stats['people']} person entries, "
          f"{stats['websites']} websites, {stats['photos']} photos, "
          f"{len(plist)} unique papers (from {stats['papers_seen']}), "
          f"{len(new_adv)} new advising (from {stats['adv_seen']})")
    if stats["skipped"]:
        print(f"  {len(stats['skipped'])} skipped/warnings:")
        for s in stats["skipped"][:40]:
            print(f"    - {s}")
        if len(stats["skipped"]) > 40:
            print(f"    ... and {len(stats['skipped']) - 40} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
