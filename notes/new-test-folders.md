Recently, I see that /test-results/ and /test-output/ was added. However, I don't want these in the root of the 
repository. Can you put them somewhere more appropriate?

For any backend tests that need such output, they should go in a folder called output/ in an appropriate subdir in 
test/ (wherever they are needed). Or if they are shared by multiple test modules, then they can go in test/output/.

For any frontend tests (playwright e2e, and vitest unit), they should go in the appropriate folder inside of frontend/. 
I see that there is frontend/src/test/. These are probably the best place to put an output/ folder for these tests.

As for test-results, I think honestly it would make sense to put this inside of the appropriate test/output folder.

If of course you think that these folders and some of their files should be committed, let me know,b ut I don't think 
so.

Also, frontend/ has (i) playwright-report/ and (ii) playwright-report-real-api/. I think that these should also both go 
in a test output folder. And actually, I think that (ii) should go inside of (i).

Go ahead and move pick new paths/locations for these directories, move them there, and ensure that all references are 
updated. It may be that you have to update certain commands (like the npm run commands) to point to these new locations.
