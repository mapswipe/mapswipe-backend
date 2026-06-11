---
status: accepted
date: 2026-06-09
deciders: [MapSwipe Governance Team (Katherine Kinzer)]
---

# 0001. Keep Locate as a separate project type and rename it to "Locate Objects"

## Context and Problem Statement

MapSwipe has a long-standing `Find` project type with the display label "Find
Features" and a newer `Locate` project type — not yet released to production —
that was introduced with the label "Locate Features". While testing `Locate` on
staging, the MapSwipe governance team and other stakeholders found the two names
easy to confuse and the on-device views hard to tell apart. The resemblance is
specific: on the mobile client, `Find` presents a 2×3 grid of imagery tiles,
whereas `Locate` presents a single tile with a 2×2 / 4×4 / 8×8 sub-grid overlaid
(its `sub_grid_size`), and
that overlaid grid looks similar to — though not identical to — `Find`'s tile
layout. The two also answer different questions — `Find` records *whether* a
feature exists in a tile, while `Locate` records *where* within the tile it is —
and `Locate` uses a different tap convention, but a volunteer cannot tell any of
that apart at a glance. Both being raster tile-map-service types, they also share
the same backend primitives, which reinforced the impression that they were
near-duplicates.

This prompted the question of whether `Locate` and `Find` should be merged into a
single project type, or whether the confusion should be resolved another way. The
discussion drew in HOT (Kshitij Sharma, implementing the feature), Toggle Corp
engineering (Ankit Mehta), and several community members, with the MapSwipe
governance team making the final call. The full thread is recorded in [MapSwipe
Slack](https://mapswipe.slack.com/archives/C0770LYH4N7/p1778240364512639).

## Considered Options

- **Option 1 — Merge `Locate` into `Find`.** Collapse the two into one project
  type, eliminating the naming and UI overlap entirely.
- **Option 2 — Keep both, rename the `Locate` label to "Locate Objects".**
  Change only the human-readable display label; leave the project type, its
  enum value, and its code identifier unchanged.
- **Option 3 — Do nothing.** Keep "Locate Features" and accept the confusion.

## Decision Outcome

Chosen: **Option 2** — keep `Locate` and `Find` as separate project types and
rename the `Locate` display label from "Locate Features" to "Locate Objects".

Merging (Option 1) was seriously weighed — the implementer initially favoured
shipping `Locate` as a `Find` variant that can sub-divide tiles — but was
rejected for two independent reasons.

**The deciding factor was user interaction and data quality.** `Locate` uses a
different tap convention from `Find` (a single tap marks a single feature, a
double tap marks multiple). Overloading one project type with two interaction
models risks confusing volunteers who have used `Find` for years and degrading
the data they produce; the governance team judged this the overriding concern.

**The engineering recommendation reinforced it:** `Locate` and `Find` differ
significantly in how a project is configured, how a task answer is shaped, and
how results are exported, so merging would force one model onto the other (or a
conditional union) and add ongoing maintenance and regression risk for no
functional gain:

- **Result shape.** A `Locate` task answer is a *list* of values
  (`FbProjectLocateMappingResult.results: dict[str, list[int]]`) — one entry per
  sub-grid partition — whereas a `Find` task answer is a single scalar
  (the generic `FbMappingResult.results: dict[str, int]`). There is no
  Find-specific result model.
- **Project configuration.** `LocateProjectProperty` adds `sub_grid_size`,
  `custom_options`, and `export_meta_key`/`export_meta_value`;
  `FindProjectProperty` is an empty pass-through of the shared base and adds
  none of these.
- **Export pipeline.** `Locate` exports add a `task_partition_index` column and
  aggregate one row per `(task, partition)`, so a single task can yield several
  output rows; `Find` exports omit that column and produce one row per task.
  The two also derive their result-value `*_count`/`*_share` columns from
  different option sets (Locate's configured custom options vs Find's fixed
  `0/1/2/3` fallback).

Renaming the label resolves the naming confusion at low cost — a state-only
migration plus any client-side label updates (see Consequences) — without
changing behaviour: the project type's enum value (`9`), its code identifier
(`LOCATE` / the `locate` module), the GraphQL `ProjectTypeEnum` value, and the
Firebase contract are all unchanged. Only the display label changes, which
clients resolve from the enum at GraphQL query time (the `AppEnumCollection`
query returns each project type's `key` and `label`).

Among the names floated in the thread — keeping "Locate Features", or "Find+
Features", "Tag Features", "Label Features", or "Locate Objects" — the governance
team chose "Locate Objects": different enough from "Find Features" to remove the
naming collision while still describing what the task does.

This decision is already implemented in code — `apps/project/models.py` now
labels `LOCATE` as "Locate Objects", with the accompanying
`0012_alter_project_project_type.py` migration (commit `349956d`). Because
`Locate` has not yet been released to production, the rename lands before any
production data or released client depends on the old label.

## Consequences

- **Good:** removes the "Find Features" vs "Locate Features" collision in the
  dashboards and the project-creation UI.
- **Good:** no data or behaviour change. The stored value stays `9`, so the
  Firebase contract and the GraphQL enum value are unaffected and no data
  migration is needed. Because `Locate` is still pre-production, the rename also
  lands before any production projects or released clients depend on the old
  label.
- **Cost (accepted):** the rename is cosmetic and does **not** address the
  underlying resemblance in *interaction*. `Locate` keeps a `Find`-like sub-grid
  view but a different tap convention, so a volunteer can still open it expecting
  `Find` and tap wrongly. As raised in the discussion, a separate project type
  changes only a few words on the project card, not the in-task experience —
  closing that gap needs a UI/UX signal, not just a label.
- **Cost (accepted):** terminology is now mixed. The `Locate` custom-option
  defaults still read "Single Feature" / "Multiple Features", and the sibling
  type is still "Find Features", so "feature" language persists around a type
  now branded "objects". Aligning that wording was deliberately left out of
  this change.
- **Cost:** changing the label alters the field's choices, which Django captures
  in migration state, so a state-only `AlterField` migration is required — it
  updates the stored choice label, not the database column — and CI's
  `makemigrations --check` enforces that it be committed. Separately, any client
  that hardcodes the literal string "Locate Features" must be updated.
- **Revisit if:** `Locate` and `Find` converge — both on the interaction model
  (taps) and on the data-structure/export — so the reasons for keeping them apart
  no longer hold (for example, if `Locate` drops sub-grid partitioning and adopts
  Find's tap convention), at which point merging the two types becomes viable
  again; or if confusion between the two persists — in staging review now, or with
  users once `Locate` ships — indicating the fix needs to reach the in-task UI
  rather than just the label.

## Pros and Cons of the Options

### Option 1 — Merge `Locate` into `Find`

- Good: eliminates the naming and UI overlap at the root; one fewer project type
  to maintain.
- Bad: overloads one project type with two different tap conventions, risking
  poor data from volunteers who expect `Find`'s interaction — the governance
  team's overriding concern.
- Bad: forces the partitioned list-result model and the `sub_grid_size` /
  `custom_options` / `export_meta_*` configuration onto a type that has none of
  them, or introduces conditional branching across storage, the Firebase
  contract, and the export pipeline.
- Bad: breaking change to an established, in-use project type and its exports.

### Option 2 — Keep both, rename the label (chosen)

- Good: resolves the naming confusion with a display-only change; no data,
  enum, code-identifier, or Firebase changes.
- Bad: cosmetic only — leaves the mobile-UI similarity and the residual
  "feature" wording unaddressed. A deeper rename (the `locate` code identifier
  and the "Single Feature" / "Multiple Features" custom-option defaults) was
  possible but deliberately scoped out, as it would churn code and the
  Firebase/GraphQL contract for no functional gain.

### Option 3 — Do nothing

- Good: zero effort.
- Bad: leaves the confusion the governance team explicitly flagged unresolved.
