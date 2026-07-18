# Maintenance scripts

One-time / occasional scripts. The app itself only needs `../build.py`.

- `merge.py` — (historical) built the initial `people.yaml`/`workshops.yaml`
  from the raw rosters (`banff_raw.yaml`, `icerm_raw.yaml`).
- `add_areas.py` — (historical) stamped the `area` field onto people.yaml.
- `merge_research.py` — folds research-agent output files
  (`research_A.yaml` … `research_D.yaml`) into `data/`: websites/photos into
  people.yaml, papers into papers.yaml (deduped by title), new advising
  records appended to advising.yaml. Looks for the research files next to
  itself first, then in the original session scratchpad. Safe to re-run.
- `prune.py` — removes people with no ties at all (edits people.yaml and
  workshop attendee lists). Run AFTER merge_research.py. `KEEP` protects ids.
- `drive.js` — headless smoke test (needs `npm i puppeteer-core` and a local
  server on :8741): clicks a node, an edge, moves a slider, checks panels.

## Resume state (July 17, 2026)

Four research agents were collecting per-person data (website, photo,
joint papers, advising) in batches A–D covering ~106 core people. If their
`research_[A-D].yaml` files are found (scratchpad or this directory):

```bash
python3 tools/merge_research.py   # fold into data/
python3 build.py                  # recompile; check its warnings
python3 tools/prune.py            # then remove still-isolated people
python3 build.py
```

If the research files are gone, re-run the collection: the agent brief was
"for each person: homepage URL, direct photo URL, advising relations within
the roster, joint papers with roster members (DBLP-first, at least one paper
per coauthor pair, cap ~12/person, exclude the 36-author 2026 Simons report)".
