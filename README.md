# RandNLA Community Graph

An interactive map of the Randomized Numerical Linear Algebra research
community: people are nodes, edges are relationships backed by tracked papers
and advising records, and the closeness metric is a tunable weighted
combination of factors.

## Quick start

```bash
python3 build.py           # compile data/*.yaml -> site/data.js
xdg-open site/index.html   # or just open it in a browser; no server needed
```

In the app:

- **Click a node** for a person's photo, affiliation, website, advisors,
  students, tracked papers, and connections ranked by closeness. **Click an
  edge** for the joint papers, advising relation, and the factor-by-factor
  breakdown of the closeness score.
- **Sliders** re-weight the closeness metric live (the layout follows); a
  threshold slider hides weak edges. The "right" metric is not settled, so it
  is tunable rather than baked in.
- **Advising view** shows only advisor→student edges, with arrows.
- Search, a legend by research area (click to fade), zoom/pan, node dragging
  (drag pins, double-click unpins).

## Data model — all human-readable YAML in `data/`

| File | Contents |
|---|---|
| `people.yaml` | One entry per person: `id`, `name`, `affiliation`, `area` (color group), optional `website`, `photo`, `topics`, `notes`. |
| `papers.yaml` | Papers with ≥ 2 in-graph authors. Every paper generates/strengthens the coauthorship edge between each pair of its authors. |
| `advising.yaml` | Directed records `advisor → student`, `kind: phd \| postdoc`. Drives the advising factor and the arrows. |
| `connections.yaml` | Curated edge annotations: free-text `notes`/`links` plus the `collaboration` factor. An entry also guarantees the edge exists. |
| `workshops.yaml` | Workshop rosters (the original provenance of the node set; feeds the shared-workshops factor). |
| `config.yaml` | The metric (factor definitions, defaults), area groups, build options. |

`build.py` validates cross-references (unknown ids, duplicate edges/papers,
bad factor values fail the build), dedupes papers by normalized title, and
compiles everything to `site/data.js`.

### The closeness metric

Each edge's score is `sum_f weight[f] * min(value[f], max[f]) / max[f]`:

- `coauthor` — number of tracked joint papers (computed from `papers.yaml`,
  capped at 8).
- `advising` — 1.0 for a PhD advisor tie, 0.7 for postdoc (computed from
  `advising.yaml`).
- `collaboration` — curated 0–2 for non-paper collaboration.
- `shared_workshops`, `same_institution`, `co_organized` — computed.

Default weights are starting points; the UI tunes them per-session.

## Provenance and caveats

- The node set began as the union of the BIRS 23w5108 (Banff 2023) and ICERM
  RandNLA (Feb 2026) participant lists plus a dozen hand-added core figures;
  attendees with no discovered ties were later pruned (their names remain in
  git history / the workshop pages).
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
build.py           YAML -> site/data.js compiler + validator
data/*.yaml        the data (source of truth, hand-editable)
site/index.html    the app (open directly; D3 is vendored in site/lib/)
site/app.js
site/style.css
site/data.js       generated - do not edit
```
