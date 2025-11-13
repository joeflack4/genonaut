Tasks
- [ ] **Frontend integration
  - [ ] Create `frontend/tests/e2e/setup/ensure-test-db.js`
  - [ ] Integrate into Playwright globalSetup
  - [ ] Note: E2E tests already documented to require `make init-test` as prerequisite

Why we deferred this
  - Create `frontend/tests/e2e/setup/ensure-test-db.js` - **Not needed: developers run `make init-test` before E2E tests**
  - Integrate into Playwright globalSetup - **Not needed: existing documentation covers this**