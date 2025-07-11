# TODO

## Project and Tutorial

- [ ] Add field validations when attaching tutorial to project
- [ ] Define relationship between project and tutorial (do we avoid graphs)
    - Can tutorial.reference_project be equal to project.tutorial

## Base Tutorial

- [ ] Implement validation for state transition
- [ ] Update Tutorial
    - [ ] What fields can be updated depending on the state and referenced project?
- [ ] Archive Tutorial
    - [ ] Add validation when attaching tutorial that it's published
    - [ ] Add validation for state transitions
- [ ] Publish Tutorial

# Base Project
- [ ] Implement validation for state transition
- [ ] Update Project
    - [ ] What fields can be updated depending on the state and attached project?

## Project Types
- [ ] Implement Validate
- [ ] Update Completeness to support vector tiles and rendering

## Misc

- [ ] Implement "project topic, region, number, organization" fields
- [ ] Do we change "look_for" field?
- [ ] Implement "teams" and "visibility" in project
- [ ] Cleanup "marked as deleted" project assets
- [ ] Calculate bounding box, centroid and area for projects
- [ ] Should we create a internal user "mapswipe bot"
- [ ] Optimize docker images
- [ ] Check for N+1 issues
- [ ] Cache endpoints for community dashboard
- [ ] Check for "unique together" fields
- [ ] Check if we need to remove indexing for old_id
- [ ] Add validations in db models, pydantic models, serializers
- [ ] Implement other types for validate project
- [ ] Add validations between tutorial and project
    - Their type should match
- [ ] Add validations for usable project / usable tutorial
- [ ] Add validations for uploaded asset
- [ ] Refactor validate project creation (old codebase)
- [ ] Handle image block in tutorials
- [ ] Tutorial edits?
- [ ] Remove urls from the database (generate while syncing with firebase)

## Questions

- [ ] Should users be able to edit client_id? We should write a documentation on client_id behavior.
- [ ] Should we cache request/response from community dashboard queries?
