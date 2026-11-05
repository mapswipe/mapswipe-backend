---
status: accepted
date: 2026-06-02
deciders: [Safar, Navin, Sushil]
---

# 0002. Use `aoi_geometry` as the single source of project AOI data

## Context and Problem Statement

A project's area of interest (AOI) is stored in four places today.

1. **Legacy fields on `Project`** (`apps/project/models.py`):
   - `centroid` (point)
   - `bbox` (polygon)
   - `total_area` (float)

   A code comment on `Project` already says to remove them and use `aoi_geometry` instead.
   There is **no** `geometry` or `area` field on `Project`.
2. **`Project.aoi_geometry`**: a one-to-one link to a `Geometry` row. `Geometry` has
   `geometry`, `centroid`, `bbox` and `total_area`.
3. **`Project.aoi_geometry_input_asset`**: a link to the `ProjectAsset` the user uploaded
   (the AOI GeoJSON file).
4. **`AREA_OF_INTEREST` export asset**: a `ProjectAsset` with export type
   `ProjectAssetExportTypeEnum.AREA_OF_INTEREST`. The public API shows it as
   `ProjectType.export_area_of_interest`. It only exists for projects imported from the
   old database.

How the data flows today:

- When a project is updated, the serializer reads the input asset, builds `aoi_geometry`
  from it, and also writes the same values into `Project.centroid`, `Project.bbox` and
  `Project.total_area`.
- Projects imported from the old database get `aoi_geometry` built from the old `geom`
  column. They have **no** input asset.
- Some projects have no AOI file at all, so they have no input asset and no
  `aoi_geometry`:
  - Validate projects whose object source is `OBJECT_GEOJSON_URL` or `TASKING_MANAGER`
  - Validate Image projects

Problems this causes:

1. The same AOI data lives in up to four places (legacy `Project` fields,
   `aoi_geometry`, `aoi_geometry_input_asset`, `AREA_OF_INTEREST` export), and the
   copies can drift apart.
2. The public API gives more than one field for the same AOI data (for example
   `total_area` and `aoi_geometry.total_area`, or `aoi_geometry_input_asset` and
   `export_area_of_interest`).
3. Frontends (Manager Dashboard, Website, Community Dashboard) use different rules to pick
   which copy to read.
4. We keep writing the legacy `Project` fields even though `aoi_geometry` replaces them.
5. The Community Dashboard contribution filter still reads `Project.centroid`
   (`apps/community_dashboard/graphql/types.py`).

## Considered Options

1. **`aoi_geometry` is the single source; delete legacy fields** (chosen).
2. **`aoi_geometry_input_asset` is the single source.** Rejected: imported projects have
   `aoi_geometry` but no input asset, so they would lose their AOI.
3. **Keep legacy `Project` fields and keep them in sync with `aoi_geometry`.** Rejected:
   two copies of the same data will drift, and every writer must remember to update both.

## Decision Outcome

`Project.aoi_geometry` is the single place to read a project's AOI (shape, centroid,
bbox, area). `aoi_geometry_input_asset` is the file the user uploaded, and `aoi_geometry`
is built from it. We will remove the legacy `Project.centroid`, `Project.bbox` and
`Project.total_area` fields, and the `AREA_OF_INTEREST` export.

**We will not delete `aoi_geometry`.** Only the three legacy fields on `Project` are
removed.

### Decision spine

| # | Decision | Why | Rejected alternatives |
| - | -------- | --- | --------------------- |
| 1 | `Project.aoi_geometry` is the only place to read AOI shape, centroid, bbox and area. | It is the one copy every project can have, including imported projects with no uploaded file. | Using the input asset as the source to read from (imported projects have none). |
| 2 | `aoi_geometry_input_asset` is the uploaded file. `aoi_geometry` is always built from it when it exists. | Keeps the original upload, and gives one clear rule for how `aoi_geometry` is made. | Letting users or code edit `aoi_geometry` by hand. |
| 3 | Stop writing `Project.centroid`, `Project.bbox` and `Project.total_area`, then delete them. | Removes a duplicate copy that can drift. | Keeping them in sync forever. |
| 4 | Before deleting the legacy fields, every project that needs an AOI must have `aoi_geometry`. This includes Validate projects without an AOI file. | If we delete the fields first, these projects lose their location on maps and in stats. | Deleting first and fixing projects later. |
| 5 | The Community Dashboard contribution filter reads `aoi_geometry.centroid`. | It is the last main reader of `Project.centroid`. | Keeping a separate centroid calculation just for the dashboard. |
| 6 | Deprecate the `AREA_OF_INTEREST` export and `export_area_of_interest`. Move their data into input assets. | It is an older copy of the same AOI (place 4 in Context). | Keeping the export next to the input asset. |
| 7 | Public APIs do not list project assets. They show only `aoi_geometry_input_asset` (with its own public type) and `aoi_geometry`. | The asset list has internal details that public users do not need. | Showing all assets and letting clients filter them. |

## Migration Strategy

### Phase 1: Both old and new work (current state)

- `aoi_geometry_input_asset` and `aoi_geometry` exist and are filled for new projects that
  have an AOI file.
- The legacy `Project` fields are still written and read.
- `ProjectType.total_area` is already marked deprecated in GraphQL.

### Phase 2: Fill the gaps

- **Validate without an AOI file and Validate Image:** make sure these projects get an
  `aoi_geometry` (and, if we decide so, an input asset).
- **Imported projects:** for each `AREA_OF_INTEREST` export asset, create an
  `aoi_geometry_input_asset` from the export file. Use the `aoi_geometry` they already
  have if the file is missing or cannot be read.
- **Check:** every project that had a value in `Project.centroid` now has
  `aoi_geometry.centroid`. Compare counts and values before moving on.

### Phase 3: Move readers to `aoi_geometry`

- Community Dashboard contribution filter: `Project.centroid` → `aoi_geometry.centroid`.
- `projects_centroid.geojson` export (`apps/project/exports/overall_stats.py`): use only
  `aoi_geometry` and remove the `_centroid` workaround.
- Public API: add a public type for `aoi_geometry_input_asset`. Stop listing project assets.
- Deprecate `export_area_of_interest` and the `AREA_OF_INTEREST` enum value.
- Check the Manager Dashboard, Website and Community Dashboard against the new fields.

### Phase 4: Remove

- Stop writing the legacy fields in the project serializer (`ProjectUpdateSerializer.update` area in `apps/project/serializers.py`).
- Remove `ProjectType.total_area` from GraphQL.
- Delete `Project.centroid`, `Project.bbox`, `Project.total_area` with a migration.
- Remove the `AREA_OF_INTEREST` export code.

## Consequences

### Positive

- One place to read AOI data, so copies can no longer drift apart.
- Simpler public API: one AOI shape (`aoi_geometry`), not up to four.
- The old `AREA_OF_INTEREST` export mechanism goes away.
- Internal asset details stay out of the public API.

### Negative

- We must migrate old `AREA_OF_INTEREST` export data.
- Frontends must switch to `aoi_geometry` / `aoi_geometry_input_asset`.
- Reading centroid/bbox now needs a join to `Geometry`. This may make some list queries a
  bit slower.

### Residual risks (accepted)

- **Hidden readers.** Some code or frontend may still read the legacy fields in ways we
  have not found. Phase 3 checks lower this risk, but cannot remove it.
- **Manager Dashboard.** It may depend on the current serialized AOI payload.
- **Incomplete migration.** Some old export files may not convert cleanly to input assets.
- **Backup and restore.** Restore may break if asset links are not kept correctly.
