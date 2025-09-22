# Plan to fix tests using the wrong database

## Problem

The API integration tests are writing to the demo database instead of the test database. This is likely because the tests are connecting to a hardcoded `localhost:8000` where a demo server is running, instead of spinning up a temporary test server.

## Plan

1.  **Analyze `test/api/integration/test_api_endpoints.py`:**
    *   Examine the `api_client` fixture and how it's used.
    *   Identify how the `API_BASE_URL` is determined.

2.  **Implement a test server fixture:**
    *   Create a new pytest fixture, for example, `test_api_server`.
    *   This fixture will:
        *   Find a random available port.
        *   Start a `uvicorn` process in the background to run the FastAPI application.
        *   The FastAPI application will be configured to use the test database (`API_ENVIRONMENT=test`).
        *   Yield the base URL of the test server (e.g., `http://localhost:xxxx`).
        *   After the tests are finished, it will terminate the `uvicorn` process.

3.  **Update the `api_client` fixture:**
    *   Modify the `api_client` fixture to accept the `test_api_server` fixture as an argument.
    *   The `api_client` will then use the URL provided by the `test_api_server` fixture as its `base_url`.

4.  **Verify the fix:**
    *   Run the `test-api` make target.
    *   Before running the tests, get a count of the rows in the `content_items` table in the `genonaut_demo` database.
    *   After the tests have run, get the count of the rows in the `content_items` table in the `genonaut_demo` database again.
    *   Confirm that the number of rows has not changed.
