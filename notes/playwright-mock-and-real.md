# Playwright tests: Run some tests off of an actual test database and web API server
# Intro
The main objective is to split the playwright tests such that some of them run off of mocks (the extreme edge cases, as 
you say), but most of them run off of an actual running web API instance running off the test db.

This will involve looking at the existing tests, see which ones are being skipped because of mocking difficulties, and 
changing them to use the real web API instead. Then, even for the ones that are passing, we should take a look at them 
and see if it makes sense to duplicate some of them so that we have 1 version of them running on the mock, and another 
version running off the actual API, or just entirely moving them to rely on the API.

One of our first tasks will be to update the test data in test/db/input/rdbms_init. We'll want a makefile command that 
calls a python CLI to do this. It can probably be put inside test/db/utils.py, but a CLI should be added to that file 
that includes a way to call that function specifically. That function should then update the TSV files with data that 
is currently in the demo database. We can set it up to do special treatment for the following tables: we should iterate 
over users. Query the user table, sorted by username. Then, iterate over users, and for each user, query to get any of 
its rows in content_items and content_items_auto. Keep iterating over users until the total number of content_items is 
=1,000, and content_items_auto also >=1,000. Then, for all other tables, also just grab the first 1,000 rows. Then, take
what we queried for all these tables, and write them as TSVs. If you think that 1,000 rows is not sufficient for our 
testing purposes, you can increase the number. I just don't want it to be too big, because I intend to commit these rows
to Git. So I don't really want these files to be greater than 25-50MB each. Ideally they should be smaller than that.

Then, we will need to update the playwright test suite so that when it runs, it first instantiates a test database (if 
it doesn't already exist), and starts up the test server (if it isn't already running). Ideally we would do this as part
of the scripting that runs from the npm run command for running these tests (the one that is triggered by make 
frontend-test-e2e , rather than starting the db/server as part of the frontend-test-e2e makefile command.

Once that DB and web API are running, we can then begin to write / migrate over our tests to use the real API.

And of course, at the end of the test suite, it should shut down that test API web server, and also delete the test 
database. I'm also thinking of some failsafes here. Don't want to accidentally delete the wrong test database. So maybe 
ensure that: (i) when removing/deleting the ensure that the database name ends with "_test". And also, perhaps we will 
want to do this using a sqlite database, rather than PostgreSQL, which will house our actual production databases.

## Thoughts and plans

### **Why This Approach Makes Sense**

The current mock-based approach has hit a complexity wall, especially for the unified gallery API with its complex query parameter combinations. The "navigates to next page correctly" test exemplifies this - we spent significant effort trying to match URL patterns like `/api/v1/content/unified?page=2&page_size=10&content_types=regular,auto&creator_filter=all&user_id=121e194b-4caa-4b81-ad4f-86ca3919d5b9&sort_field=created_at&sort_order=desc`, and still couldn't get page navigation working reliably.

### **Benefits of Real API Approach**
- **Eliminates Mock Pattern Complexity**: No more regex pattern matching for complex URLs
- **Tests Real Integration**: Catches actual SQL query issues, serialization problems, API contract mismatches
- **Simplified Test Maintenance**: Tests become more straightforward and less brittle
- **Better Coverage**: Tests the full stack including database queries, API serialization, network requests
- **Realistic Data Relationships**: Tests with proper foreign key constraints and data relationships

### **Strategic Test Categories**

#### **Real API Tests (Majority)**
- Basic pagination (page 1 → page 2 with 10+ items per page)
- Content type filtering (regular vs auto content)
- Creator filtering (user vs community content)
- Search functionality with actual text matching
- Basic statistics and counts
- User authentication and authorization
- Standard CRUD operations

#### **Mock Tests (Edge Cases Only)**
- Extreme pagination scenarios (page 50,000 of 1,000,000 records)
- Network failure simulation (timeouts, 500 errors, connection drops)
- Specific error response handling (malformed JSON, unexpected status codes)
- Rate limiting scenarios
- Very large dataset simulations that would be impractical to seed

### **Technical Implementation Strategy**

#### **Database Setup**
Using SQLite for tests is smart - it's:
- **File-based**: Easy to create/delete safely
- **Fast**: No network overhead for tests
- **Portable**: Works consistently across environments
- **Safe**: Won't accidentally affect production PostgreSQL

#### **Test Server Lifecycle**
The npm script approach is ideal:
- **Isolated**: Test server runs on different port (e.g., 8002)
- **Automated**: Start/stop handled by test runner
- **Parallel-Safe**: Multiple test runs won't conflict
- **Clean**: Guaranteed cleanup even if tests fail

#### **Data Seeding Strategy**
1,000 rows per table is a good balance for realistic pagination testing without bloating git repository. The user-based iteration approach ensures realistic data distribution and relationships.

### **Migration Priority**

#### **Phase 1: Infrastructure Setup**
Set up the test database seeding, server lifecycle, and convert one simple test to validate the approach.

#### **Phase 2: Convert High-Value Tests**
Start with tests that are currently failing due to mock complexity:
- "navigates to next page correctly"
- "content type toggles update pagination correctly"
- "large dataset pagination performance" (simplified version)

#### **Phase 3: Bulk Migration**
Convert remaining tests that would benefit from real API testing.

#### **Phase 4: Optimization**
Keep only truly necessary mocks and optimize test performance.

## Task list

### **Phase 1: Infrastructure Setup**

### **Protect existing backend tests**
Our plans are to update the TSVs in: `test/db/input/rdbms_init/`. However, once we do this, a lot of the backend tests 
will break. So as a temporary measure, let's copy the current state of these files into `test/db/input/rdbms_init/v1/`,
and update all of the references that are currently pointing to `test/db/input/rdbms_init/`, and instead point them to 
this new directory. But for our playwright tests, they will use `test/db/input/rdbms_init/`. 
- [ ] Copy `test/db/input/rdbms_init/` into `test/db/input/rdbms_init/v1/`
- [ ] Update current references to point to that directory

We will update the backend tests to use the new TSV files at a later date.

#### **Database and Data Preparation**
- [ ] Create Python CLI function in `test/db/utils.py` for seeding test data from demo database
- [ ] Implement user-based iteration logic to get ~1,000 rows from content_items and content_items_auto
- [ ] Add logic to extract first 1,000 rows from all other tables
- [ ] Create TSV export functionality that writes to `test/db/input/rdbms_init/`
- [ ] Add size validation to ensure TSV files stay under 25-50MB each
- [ ] Create makefile command to run the test data seeding CLI
- [ ] Test the data export process against demo database

#### **Test Database Infrastructure**
- [ ] Modify database initialization scripts to support SQLite for testing
- [ ] Create test database naming convention with "_test" suffix safety check
- [ ] Implement test database creation/deletion with proper safeguards
- [ ] Add environment variable detection to prevent accidentally using production database
- [ ] Create database connection logic that can switch between PostgreSQL (prod) and SQLite (test)

#### **Test Server Lifecycle**
- [ ] Create test server startup script that uses SQLite test database
- [ ] Implement server health check endpoint for test readiness verification
- [ ] Add test server port configuration (e.g., 8002) to avoid conflicts
- [ ] Modify npm test script to auto-start test server before running E2E tests
- [ ] Implement graceful server shutdown and database cleanup after tests
- [ ] Add process management to prevent orphaned test servers
- [ ] Create fallback cleanup script for manual test server termination

#### **Playwright Configuration Updates**
- [ ] Create new Playwright configuration for real API tests
- [ ] Add environment detection to switch between mock and real API modes
- [ ] Implement base URL configuration for test server (http://localhost:8002)
- [ ] Add test isolation strategy to prevent test data contamination
- [ ] Create helper functions for real API test setup

### **Phase 2: Test Migration and Validation**

#### **Convert First Test for Validation**
- [ ] Choose simple test to convert as proof-of-concept (e.g., basic gallery listing)
- [ ] Remove mock API setup and use real API calls
- [ ] Verify test passes with real API and seeded database
- [ ] Document patterns and helper functions for future test conversions
- [ ] Create test utilities for common real API operations

#### **Convert Priority Failing Tests**
- [ ] Convert "navigates to next page correctly" test to use real API
- [ ] Verify pagination actually works with sufficient test data (20+ items)
- [ ] Remove complex mock URL pattern matching logic
- [ ] Test page 1 → page 2 navigation with real content updates
- [ ] Convert "content type toggles update pagination correctly" test
- [ ] Verify content filtering works with real database queries
- [ ] Update assertions to work with real API response timing

#### **Simplified Large Dataset Test**
- [ ] Create realistic "large dataset pagination" test using available 1,000 test records
- [ ] Test pagination with 100 pages (10 items per page) instead of millions
- [ ] Verify deep pagination works correctly (e.g., page 50 of 100)
- [ ] Keep extreme scenario testing (page 50,000) as mock-only test

### **Phase 3: Comprehensive Migration**

#### **Audit and Categorize Existing Tests**
- [ ] Review all existing E2E tests and categorize as "real API candidate" vs "mock-only"
- [ ] Identify tests currently skipped due to mock complexity
- [ ] Document which tests would benefit from real API vs keeping as mocks
- [ ] Create migration plan with estimated effort for each test

#### **Bulk Test Conversion**
- [ ] Convert authentication and user management tests to real API
- [ ] Convert CRUD operation tests (create, read, update, delete content)
- [ ] Convert search and filtering tests to use real database queries
- [ ] Convert statistics and counting tests to use real aggregations
- [ ] Update error handling tests that can be tested with real API

#### **Real API Test Utilities**
- [ ] Create helper functions for common test operations (login, create content, etc.)
- [ ] Implement test data factories for creating specific test scenarios
- [ ] Add database state verification utilities for asserting side effects
- [ ] Create cleanup utilities for maintaining test isolation

### **Phase 4: Optimization and Cleanup**

#### **Performance Optimization**
- [ ] Optimize test database seeding for faster test startup
- [ ] Implement test data caching to avoid rebuilding database on each run
- [ ] Add parallel test execution support with database isolation
- [ ] Optimize test server startup time

#### **Mock Strategy Refinement**
- [ ] Identify truly necessary mock tests (extreme edge cases, network failures)
- [ ] Simplify remaining mock patterns to be more maintainable
- [ ] Document clear guidelines for when to use mocks vs real API
- [ ] Remove unnecessary mock complexity from converted tests

#### **Documentation and Maintenance**
- [ ] Document the hybrid testing approach and when to use each method
- [ ] Create troubleshooting guide for test database and server issues
- [ ] Add CI/CD integration considerations for real API testing
- [ ] Create maintenance procedures for keeping test data up-to-date
