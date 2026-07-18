# RandNLA Community Graph

An interactive map of the Randomized Numerical Linear Algebra research
community: people are nodes, edges are relationships backed by tracked papers
and advising records, and the closeness metric is a tunable weighted
combination of factors.

> **Disclaimer.** This project — the roster, papers, advising records, topic
> tags, photos, and the app itself — was generated with Claude (Anthropic).
> The data was scraped and curated by AI from public sources (DBLP, Google
> Scholar, personal homepages, workshop pages) and, despite verification
> passes, may contain errors, omissions, and stale affiliations. Edge weights
> reflect *tracked* papers only. Treat it as a map, not a record: verify
> against primary sources before relying on anything here.

**Live site:** https://research.chen.pw/CommunityGraph

## Quick start

```bash
python3 build.py           # compile data/*.yaml -> docs/data.js
xdg-open docs/index.html   # or just open it in a browser; no server needed
```

The site is served by GitHub Pages from the `docs/` folder on `main`
(`docs/data.js` is generated but committed, so Pages needs no build step —
re-run `build.py` and commit after editing the data).

In the app:

- **Click a node** for a person's photo, affiliation, website, advisors,
  students, tracked papers, and connections ranked by closeness. **Click an
  edge** for the joint papers, advising relation, and the factor-by-factor
  breakdown of the closeness score.
- **Filter by topic**: free-text filter over topics, bios, and paper titles
  (e.g. "trace estimation", "Kaczmarz") — matching people stay, the rest
  fade.
- **Sliders** re-weight the closeness metric live (the layout follows); a
  threshold slider hides weak edges. The "right" metric is not settled, so it
  is tunable rather than baked in.
- **Advising view** shows only advisor→student edges, with arrows.
- **Two colorings**: curated research areas, or collaboration communities
  detected by weighted Louvain over the closeness graph
  (`tools/cluster_communities.py` → `data/clusters.yaml`; regenerate after
  substantial data changes — needs `networkx`). The communities track
  institutions and lineages as much as topics, which is part of the point.
- Person search, a clickable legend (fade groups), zoom/pan, node dragging
  (drag pins, double-click unpins).

## Data model — all human-readable YAML in `data/`

| File | Contents |
|---|---|
| `people.yaml` | One entry per person: `id`, `name`, `affiliation`, `area` (color group), optional `website`, `photo`, `topics`, `notes`. |
| `papers.yaml` | Papers with ≥ 2 in-graph authors. Every paper generates/strengthens the coauthorship edge between each pair of its authors. |
| `advising.yaml` | Directed records `advisor → student`, `kind: phd \| postdoc`. Drives the advising factor and the arrows. |
| `connections.yaml` | Curated edge annotations: free-text `notes`/`links` plus the `collaboration` factor. An entry also guarantees the edge exists. |
| `config.yaml` | The metric (factor definitions, defaults) and area groups. |

`build.py` validates cross-references (unknown ids, duplicate edges/papers,
bad factor values fail the build), dedupes papers by normalized title, and
compiles everything to `site/data.js`.

### The closeness metric

Each edge's score is `sum_f weight[f] * min(value[f], max[f]) / max[f]`:

- `coauthor` — number of tracked joint papers (computed from `papers.yaml`,
  capped at 10).
- `advising` — 1.0 for a PhD advisor tie, 0.7 for postdoc (computed from
  `advising.yaml`).
- `collaboration` — curated 0–2 for non-paper collaboration.
- `same_institution` — computed from matching affiliation strings.

Default weights are starting points; the UI tunes them per-session.

## Provenance and caveats

- The node set began as the union of the BIRS 23w5108 (Banff 2023) and ICERM
  RandNLA (Feb 2026) participant lists plus a dozen hand-added core figures;
  attendees with no discovered ties were later pruned. The rosters live on in
  `tools/workshops_archive.yaml` — the graph itself no longer uses workshop
  data.
- Papers were collected person-by-person (DBLP primarily, homepages second)
  by research agents in July 2026, with the brief "cover every coauthor pair,
  prefer representative papers" — it is a *representative* bibliography, not
  a complete one, and paper counts on edges reflect tracked papers only.
- Advising records were verified against the Mathematics Genealogy Project,
  theses, and homepages. The very-many-author 2026 Simons workshop report is
  deliberately excluded from papers.yaml.
- Photos hotlink to homepages/Google Scholar; a broken link simply hides the
  photo in the app.

## Extending to another community

Nothing RandNLA-specific lives in code: replace the `data/` directory (new
people/papers/advising, new `area` groups in config) and rebuild. New factors
are declared in `config.yaml`; a new computed rule needs a few lines in
`build.py`.

## Layout

```
build.py           YAML -> docs/data.js compiler + validator
data/*.yaml        the data (source of truth, hand-editable)
docs/index.html    the app (open directly; D3 is vendored in docs/lib/)
docs/app.js
docs/style.css
docs/data.js       generated - do not edit by hand (but committed for Pages)
```
