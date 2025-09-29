# New playwright tests
I'd like to ensure that we have good frontend test coverage. Perhaps we do, but I don't know if we've covered all the 
bases.

- [ ] Iterate through each page of the frontend
  - [ ] For each page, consider all of the UI elements that, when engaged with by the user (e.g. click), result in some 
  state change. For all such element interactions, ensure that there is a playwright test that covers the interaction 
  and tests for the expected outcome. If there is a test that already exists that covers this--great, no need to add a 
  new one. But if not, then create a new test.
- [ ] Ensure all tests pass successfully before marking this task complete.
