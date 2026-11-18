# App features: required and supported features

Some projects need client support that older apps don't have. Older apps don't
fail loudly: they show a fallback (eg. a placeholder image instead of a vector
overlay) and still accept answers. **App features** let a project declare what
it needs, so a client that can't show it explains why instead of letting the
contributor start.

- A **feature** is a key in `AppFeatureEnum` (`apps/common/models.py`).
- A resource (project, tutorial, …) has **required features**:
  `requiredFeatures` in firebase, derived by the backend from its configuration.
- A client has **supported features**: a list bundled in each release, which can
  be overridden per release from the admin.
- The client blocks the resource when a required feature is missing.
  **Unknown keys count as missing**, so an old app also blocks features added
  after it was released.

> Apps released before this check ignore `requiredFeatures`. To stop them, use
> the update prompt's minimum supported version (App info in the admin).

## When to add a feature

Add one when an older client would **silently** show or record the project
wrongly. Eg:

- A new layer or imagery the client must render to answer correctly
  (`PROJECT_COMPLETENESS_VECTOR_LAYER`, `PROJECT_VALIDATE_PRE_EVENT_IMAGERY`).
- A new answer option or interaction that older clients would map to a wrong
  answer.

Not needed when:

- Older clients ignore the new field and the result is still correct.
- It's a new project type. Clients already hide project types they don't know.

## Naming

- `UPPER_SNAKE_CASE`, prefixed by area: `PROJECT_<TYPE>_…`, `TUTORIAL_…`,
  `MAPPING_…`, `USER_GROUP_…`.
- The **value is the same as the name**. It is stored in firebase and compared
  by clients as is, and GraphQL exposes the name
  (`test_feature_values_are_names` checks this).
- **Never rename or remove a feature.** Released apps and firebase data use the
  keys. If a feature becomes obsolete, stop requiring it and leave the key.
- The label is shown to contributors in the app ("This version doesn't
  support: …"), so write it for them.

## Adding a feature for a project type

Example: Validate projects with pre and post event imagery.

### 1. Backend: add the key

`apps/common/models.py`:

```python
class AppFeatureEnum(models.TextChoices):
    ...
    PROJECT_VALIDATE_PRE_EVENT_IMAGERY = (
        "PROJECT_VALIDATE_PRE_EVENT_IMAGERY",
        "Validate project with pre and post event imagery",
    )
```

Then:

```bash
# The release's "supported features" uses these as choices
./manage.py makemigrations common
# CI checks that the schema is up to date. Clients generate types from it.
./manage.py graphql_schema
```

### 2. Backend: derive it from the project configuration

Override `get_required_features()` in the project type class
(`project_types/<type>/project.py`). Return every feature the configuration
needs. The base class returns `[]`.

```python
class ValidateProject(...):
    @typing.override
    def get_required_features(self):
        features = []
        if self.project_type_specifics.pre_event_tile_server_property:
            features.append(AppFeatureEnum.PROJECT_VALIDATE_PRE_EVENT_IMAGERY)
        return features
```

Do the same in the tutorial class (`project_types/<type>/tutorial.py`) when the
tutorial uses the feature too. See `tile_map_service/completeness/` for an
example of both.

Derive it; don't add a field for project managers to set. Forgetting it is the
exact failure this prevents.

`requiredFeatures` is pushed with the project on create and update, so nothing
else is needed in the push.

### 3. Backend: tests and fixtures

- Add a case to `apps/project/tests/required_features_test.py`.
- The e2e tests compare the project and tutorial in firebase with
  `assets/tests/projects/<type>/project_data.json5` (`mapswipe-assets` repo).
  If the fixture's configuration uses the feature, add
  `requiredFeatures: ['<KEY>']` to `expected_project_data` and
  `expected_tutorial_data`.

### 4. Clients: support it

In each client that implements the feature:

- **mapswipe-mobile**:
  1. Point the `backend` submodule to a commit with the new schema and run
     `pnpm generate:type`.
  2. Implement the feature.
  3. Add the key to `SUPPORTED_FEATURES` in `constants/features.ts`.
- **mapswipe-web**: same check, with its own supported list.

Only add the key once the feature fully works in that client.

### 5. Release, in this order

1. Release the clients that support the feature.
2. Deploy the backend.
3. Push `requiredFeatures` for projects and tutorials already in firebase:

   ```bash
   ./manage.py push_required_features --dry-run
   ./manage.py push_required_features
   ```

4. Only then create projects that use the feature.

Projects created before step 4 still work: clients without the feature show
"Update needed" or "Not supported" instead of letting contributors start.

## Overriding a release's supported features

Admin → App infos → platform → release → **Supported features**.

- **Empty** (default): the app uses the list bundled in that version.
- **Any selected**: the selection **replaces** the bundled list for that
  version. Select **every** feature that version should support, not only the
  changed one.

Use it to:

- **Withdraw** a feature from a release where it turned out broken.
- **Grant** a feature to a release that already handled it before the key
  existed.
- Tell older apps **which version to update to**: when a newer release lists
  the missing features, the app says "Update MapSwipe to 3.2.0 to open this"
  instead of a generic message.

Saving the app info pushes it to firebase (`v2/appInfo/{platform}`).

## Requiring features on other resources

Features aren't limited to projects. To check them on another resource:

1. **mapswipe-firebase**: add `requiredFeatures` (a list of strings, not the
   enum, so unknown keys never fail validation) to its definition and
   regenerate.
2. **mapswipe-backend**: derive and push it with the resource, and extend
   `push_required_features` if existing data needs a backfill.
3. **Clients**: call `useFeatureSupport(resource.requiredFeatures)` (mobile)
   and block the resource when `isSupported` is false.
   `FeatureUnsupportedNotice` shows the reason and the update button.

## Checklist

- [ ] Key added to `AppFeatureEnum` (value = name, area prefix, label for contributors)
- [ ] `makemigrations` and `graphql_schema`
- [ ] `get_required_features()` in the project (and tutorial) class
- [ ] Test case and e2e fixtures (`mapswipe-assets`)
- [ ] Clients that support it: implemented and key added to their supported list
- [ ] Released in order: clients → backend → `push_required_features` → new projects
