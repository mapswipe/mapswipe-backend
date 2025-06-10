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

## Questions

- Should user be able to edit client_id?
- Should we cache request/response from community dashboard queries?
