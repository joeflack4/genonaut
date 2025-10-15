# ComfyUI Mock server
I want to create a **mock ComfyUI HTTP server** for more realistic integration testing. At the very least, we will need to:

1. Create a simple Flask/FastAPI server that mimics ComfyUI's API endpoints:
   - `POST /prompt` � return mock `prompt_id`
   - `GET /history/{prompt_id}` � return mock workflow status
   - `GET /queue` � return mock queue status
   - `GET /object_info` � return mock model info
   - `POST /interrupt` � accept cancellation requests

2. Start this server during test setup (e.g., in a pytest fixture)

3. Configure tests to use a URL represented by `COMFYUI_MOCK_URL` instead of the real ComfyUI URL. Add this env var to 
env/ .env and env.example, and ensure it is being used here.

4. Simulate generation: When a job is posted, we'll copy `test/_infra/mock_services/comfyui/input/kernie_512x768.jpg` 
into `test/_infra/mock_services/comfyui/output/`, assigning it with a new filename. We'll pretend that file is the result of the job. We can also do this 
if we want to simulate multiple jobs running concurrently, giving each one a different filename. During the test 
teardown phase, you can remove all of the files in `test/_infra/mock_services/comfyui/output/`

5. Once this is all added, create a bunch of tests around this. We can take inspiration from the existing tests which 
mock the ComfyUI server using `unittest.mock.Mock` and `patch` to mock the `ComfyUIClient` class in tests; perhaps we'll
want to create a new test for each one of the tests that use that mock, using our new server instead. Put these files in
`test/integrations/comfy_ui/`. For any test files that you create here, name them with the pattern 
`test_comfyui_mock_server_*.py`. 

6. I think it is advisable that we have a set of tests in (5) that work without the usage of celery and Redis. However, 
this is also a good opportunity to test that as well--to test that the test DB, and test instance of Redis work in 
concert with the test mock ComfyUI web server. So we should also make a suite of tests like in step (5) that will also 
use this infrastructure. I realize that this particular task is a lot of work. Might want to break the implementation 
of these tests into multiple phases. Note that we have a lot set up for this already, given that we have test-specific 
redis and celery env vars in `env/.env`, e.g. `REDIS_URL_TEST`.

---

I've created a directory `test/_infra/mock_services/comfyui/` where you can do this work. I also added `server.py` in 
that dir for this, but possibly you will want to split this work up into multiple files; I'm not sure. 

Before you start on this work, read `notes/cui-mock-q1.md` as it has useful background context.

Also before you start, create a new file `notes/cui-mock-tasks.md`. Write down all of the tasks you need in order to 
complete this work as checkboxes.

Make sure to `follow notes/routines/iteration.md` as applicable.

Once you've done all that reading and have written your list of tasks, begin execution on them.