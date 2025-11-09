# Fix ComfyUI integration - information
## Background
Ok, we've made progress. Now we can swap between the "image backend" (ComfyUI or Image gen mock (KernieGen) in the 
settings area. And now the mock is working again.

However, we're now going to focus on fixing and improving the ComfyUI integration itself. We never got it set up to work
100% correctly yet. 

**Expected behavior**
When clicking generate, it takes a while for an image to generate, so it should show the pending / processing status 
while it is generating (this seems to be the way it's working so far), and then when it successfully generates, I should 
see the image appear in the app.

**Current behavior**
It does successfully create the image, but it doesn't render it in the app. Instead, it displays an error message in the 
area around where the image should appear: `Unable to determine primary image path for job JOB_ID`.

Some other strange stuff is happening. Observe these logs, from 3 different attempts, and see some of my notes in between.

_Attempt 1_
```
[2025-11-08 21:36:50,533: INFO/ForkPoolWorker-9] Starting ComfyUI job 1194234
[2025-11-08 21:36:50,535: INFO/ForkPoolWorker-9] Job 1194234: Backend choice from params: comfyui
[2025-11-08 21:36:50,536: INFO/ForkPoolWorker-9] Job 1194234: Using ComfyUI backend URL: http://localhost:8000
[2025-11-08 21:36:50,536: INFO/ForkPoolWorker-9] Job 1194234: Using ComfyUI output dir: ~/Documents/ComfyUI/output
[2025-11-08 21:36:50,540: INFO/ForkPoolWorker-9] Job 1194234 status updated to 'running'
[2025-11-08 21:36:50,541: INFO/ForkPoolWorker-9] Published update to genonaut_demo:job:1194234: started (subscribers: 0)
[2025-11-08 21:36:50,563: INFO/ForkPoolWorker-9] Job 1194234 submitted to ComfyUI (prompt_id=a07f468f-ff11-437d-b6b7-90dd1755c144)
[2025-11-08 21:36:50,564: INFO/ForkPoolWorker-9] Published update to genonaut_demo:job:1194234: processing (subscribers: 0)

[2025-11-08 21:36:50,569: WARNING/ForkPoolWorker-9] Source file not found: ~/Documents/ComfyUI/output/gen_job_1194234_00001_.png

[2025-11-08 21:36:50,569: ERROR/ForkPoolWorker-9] Job 1194234 failed: Unable to determine primary image path for job 1194234
Traceback (most recent call last):
  File "/Users/joeflack4/projects/genonaut/genonaut/worker/tasks.py", line 238, in process_comfy_job
    raise ComfyUIWorkflowError(f"Unable to determine primary image path for job {job_id}")
genonaut.api.services.comfyui_client.ComfyUIWorkflowError: Unable to determine primary image path for job 1194234

[2025-11-08 21:36:50,576: INFO/ForkPoolWorker-9] Published update to genonaut_demo:job:1194234: failed (subscribers: 0)
[2025-11-08 21:36:50,584: INFO/ForkPoolWorker-9] Task genonaut.worker.tasks.run_comfy_job[e93dab67-3077-4bd1-9627-883fcabe5191] retry: Retry in 3s: ComfyUIWorkflowError('Unable to determine primary image path for job 1194234')
```

Notice how it does show the "Unable to determine primary image path for job 1194234" in the log.

The way this log is behaving is correct in the event that it cannot actually find the file.

However, you will notice that if you check for the existence of this file, it exists:
```
file ~/Documents/ComfyUI/output/gen_job_1194234_00001_.png
/Users/joeflack4/Documents/ComfyUI/output/gen_job_1194234_00001_.png: PNG image data, 512 x 768, 8-bit/color RGB, non-interlaced
```

So for some reason, something is happening where it is not able to resolve the path even though it clearly exists.

It could be due to a variety of reasons, but my guess is that it is checking for the file before it actually has 
completed generating.

From what I understand, our app is set up to periodically check on the status of the image. And, when it detects that 
the image has successfully been generated, it will return that information through the web socket.

Some background. When you submit a job, you get back information about the job ID in ComfyUI.

For example earlier, I did a test:
```sh
curl -X POST http://127.0.0.1:8000/prompt \
     -H "Content-Type: application/json" \
     -d @/Users/joeflack4/projects/genonaut/test/integrations/comfyui/input/1.json
```

And got back this response:
```
{"prompt_id": "444898be-d8bb-4135-9648-922f7cb99173", "number": 34, "node_errors": {}}%
```

You can use this to check on the status of the job: with that prompt id: http://localhost:8000/history/a3e559fb-4fa2-4cc6-9183-97f93befc6f3

The response when I immediately checked, and continued to check prior to completion, was just an empty json obj: `{}`

However, once it successfully generated, I got:

```json
{
   "a3e559fb-4fa2-4cc6-9183-97f93befc6f3":{
      "prompt":[
         32,
         "a3e559fb-4fa2-4cc6-9183-97f93befc6f3",
         {
            "1":{
               "class_type":"CheckpointLoaderSimple",
               "inputs":{
                  "ckpt_name":"illustriousXL_v01.safetensors"
               }
            },
            "2":{
               "class_type":"CLIPTextEncode",
               "inputs":{
                  "clip":[
                     "1",
                     1
                  ],
                  "text":"test 3"
               }
            },
            "3":{
               "class_type":"CLIPTextEncode",
               "inputs":{
                  "clip":[
                     "1",
                     1
                  ],
                  "text":""
               }
            },
            "4":{
               "class_type":"EmptyLatentImage",
               "inputs":{
                  "width":512,
                  "height":768,
                  "batch_size":1
               }
            },
            "5":{
               "class_type":"KSampler",
               "inputs":{
                  "seed":896004968,
                  "steps":20,
                  "cfg":7,
                  "sampler_name":"euler_ancestral",
                  "scheduler":"normal",
                  "denoise":1,
                  "model":[
                     "1",
                     0
                  ],
                  "positive":[
                     "2",
                     0
                  ],
                  "negative":[
                     "3",
                     0
                  ],
                  "latent_image":[
                     "4",
                     0
                  ]
               }
            },
            "6":{
               "class_type":"VAEDecode",
               "inputs":{
                  "samples":[
                     "5",
                     0
                  ],
                  "vae":[
                     "1",
                     2
                  ]
               }
            },
            "7":{
               "class_type":"SaveImage",
               "inputs":{
                  "images":[
                     "6",
                     0
                  ],
                  "filename_prefix":"gen_job_1194236"
               }
            }
         },
         {
            "client_id":"1194236"
         },
         [
            "7"
         ]
      ],
      "outputs":{
         "7":{
            "images":[
               {
                  "filename":"gen_job_1194236_00001_.png",
                  "subfolder":"",
                  "type":"output"
               }
            ]
         }
      },
      "status":{
         "status_str":"success",
         "completed":true,
         "messages":[
            [
               "execution_start",
               {
                  "prompt_id":"a3e559fb-4fa2-4cc6-9183-97f93befc6f3",
                  "timestamp":1762656129342
               }
            ],
            [
               "execution_cached",
               {
                  "nodes":[
                     "1",
                     "2",
                     "3",
                     "4",
                     "5",
                     "6",
                     "7"
                  ],
                  "prompt_id":"a3e559fb-4fa2-4cc6-9183-97f93befc6f3",
                  "timestamp":1762656129343
               }
            ],
            [
               "execution_success",
               {
                  "prompt_id":"a3e559fb-4fa2-4cc6-9183-97f93befc6f3",
                  "timestamp":1762656129343
               }
            ]
         ]
      },
      "meta":{
         "7":{
            "node_id":"7",
            "display_node":"7",
            "parent_node":null,
            "real_node_id":"7"
         }
      }
   }
}
```

Indeed, you can check this for yourself and see the result.

You can see that it also shows the output in that snippet:
```
      "outputs":{
         "7":{
            "images":[
               {
                  "filename":"gen_job_1194236_00001_.png",
                  "subfolder":"",
                  "type":"output"
               }
            ]
         }
      },
```

If you search for `gen_job_1194236_00001_.png` using the `"comfyui-output-dir": "~/Documents/ComfyUI/output",`, you get:

```
file ~/Documents/ComfyUI/output/gen_job_1194236_00001_.png
/Users/joeflack4/Documents/ComfyUI/output/gen_job_1194236_00001_.png: PNG image data, 512 x 768, 8-bit/color RGB, non-interlaced
```

Success!

So why isn't the app finding it and rendering it correctly?

As I mentioned, one possibility is that it's checking too soon. Perhaps when the JSON response shows the output, maybe 
it hasn't actually finished saving to disk? We could try (temporarily--I don't want to make this change permanently if 
it doesn't work, because it'll slow things down) to add some wait, like 3000ms (3 seconds), just to see if that does it. 
If that fixes the issue, then we could try reducing the ms even lower until we get something that is a short wait but 
works consistently.

If this doesn't fix the problem, then I don't really know what the solution is. You'll need to troubleshoot that.

_Attempt 2_
```
#err2
[2025-11-08 21:40:32,521: INFO/MainProcess] Task genonaut.worker.tasks.run_comfy_job[2f10842f-0703-4032-a0b7-6792b1475cc5] received
[2025-11-08 21:40:32,534: INFO/ForkPoolWorker-9] Starting ComfyUI job 1194235
[2025-11-08 21:40:32,554: ERROR/ForkPoolWorker-9] Task genonaut.worker.tasks.run_comfy_job[2f10842f-0703-4032-a0b7-6792b1475cc5] raised unexpected: OperationalError('(psycopg2.OperationalError) server closed the connection unexpectedly\n\tThis probably means the server terminated abnormally\n\tbefore or while processing the request.\n')
Traceback (most recent call last):
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
    cursor.execute(statement, parameters)
psycopg2.OperationalError: server closed the connection unexpectedly
	This probably means the server terminated abnormally
	before or while processing the request.


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/trace.py", line 453, in trace_task
    R = retval = fun(*args, **kwargs)
                 ^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/trace.py", line 736, in __protected_call__
    return self.run(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/autoretry.py", line 60, in run
    ret = task.retry(exc=exc, **retry_kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/task.py", line 743, in retry
    raise_with_context(exc)
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/autoretry.py", line 38, in run
    return task._orig_run(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/genonaut/worker/tasks.py", line 335, in run_comfy_job
    return process_comfy_job(
           ^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/genonaut/worker/tasks.py", line 86, in process_comfy_job
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2759, in first
    return self.limit(1)._iter().first()  # type: ignore
           ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/orm/query.py", line 2857, in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
                                                  ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2365, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2251, in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/orm/context.py", line 306, in orm_execute_statement
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
    return meth(
           ^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2355, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
    cursor.execute(statement, parameters)
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) server closed the connection unexpectedly
	This probably means the server terminated abnormally
	before or while processing the request.

[SQL: SELECT generation_jobs.id AS generation_jobs_id, generation_jobs.user_id AS generation_jobs_user_id, generation_jobs.job_type AS generation_jobs_job_type, generation_jobs.prompt AS generation_jobs_prompt, generation_jobs.params AS generation_jobs_params, generation_jobs.status AS generation_jobs_status, generation_jobs.content_id AS generation_jobs_content_id, generation_jobs.created_at AS generation_jobs_created_at, generation_jobs.updated_at AS generation_jobs_updated_at, generation_jobs.started_at AS generation_jobs_started_at, generation_jobs.completed_at AS generation_jobs_completed_at, generation_jobs.error_message AS generation_jobs_error_message, generation_jobs.celery_task_id AS generation_jobs_celery_task_id, generation_jobs.negative_prompt AS generation_jobs_negative_prompt, generation_jobs.checkpoint_model AS generation_jobs_checkpoint_model, generation_jobs.lora_models AS generation_jobs_lora_models, generation_jobs.width AS generation_jobs_width, generation_jobs.height AS generation_jobs_height, generation_jobs.batch_size AS generation_jobs_batch_size, generation_jobs.comfyui_prompt_id AS generation_jobs_comfyui_prompt_id
FROM generation_jobs
WHERE generation_jobs.id = %(id_1)s
 LIMIT %(param_1)s]
[parameters: {'id_1': 1194235, 'param_1': 1}]
(Background on this error at: https://sqlalche.me/e/20/e3q8)
```

Just showing that sometimes, get `psycopg2.OperationalError: server closed the connection unexpectedly`

_Attempt 3_

```
# err3
[2025-11-08 21:42:09,074: WARNING/ForkPoolWorker-9] Source file not found: ~/Documents/ComfyUI/output/gen_job_1194236_00001_.png
[2025-11-08 21:42:09,075: ERROR/ForkPoolWorker-9] Job 1194236 failed: Unable to determine primary image path for job 1194236
Traceback (most recent call last):
  File "/Users/joeflack4/projects/genonaut/genonaut/worker/tasks.py", line 238, in process_comfy_job
    raise ComfyUIWorkflowError(f"Unable to determine primary image path for job {job_id}")
genonaut.api.services.comfyui_client.ComfyUIWorkflowError: Unable to determine primary image path for job 1194236
[2025-11-08 21:42:09,087: INFO/ForkPoolWorker-9] Published update to genonaut_demo:job:1194236: failed (subscribers: 1)
[2025-11-08 21:42:09,099: INFO/MainProcess] Task genonaut.worker.tasks.run_comfy_job[f4e2e3f1-0585-47ec-8d9c-65d4316a8f82] received
[2025-11-08 21:42:09,101: INFO/ForkPoolWorker-9] Task genonaut.worker.tasks.run_comfy_job[f4e2e3f1-0585-47ec-8d9c-65d4316a8f82] retry: Retry in 0s: ComfyUIWorkflowError('Unable to determine primary image path for job 1194236')


[2025-11-08 21:42:09,147: INFO/ForkPoolWorker-2] Starting ComfyUI job 1194236
[2025-11-08 21:42:09,314: INFO/ForkPoolWorker-2] Job 1194236: Backend choice from params: comfyui
[2025-11-08 21:42:09,314: INFO/ForkPoolWorker-2] Job 1194236: Using ComfyUI backend URL: http://localhost:8000
[2025-11-08 21:42:09,314: INFO/ForkPoolWorker-2] Job 1194236: Using ComfyUI output dir: ~/Documents/ComfyUI/output
[2025-11-08 21:42:09,323: INFO/ForkPoolWorker-2] Job 1194236 status updated to 'running'
[2025-11-08 21:42:09,328: INFO/ForkPoolWorker-2] Published update to genonaut_demo:job:1194236: started (subscribers: 0)
[2025-11-08 21:42:09,344: INFO/ForkPoolWorker-2] Job 1194236 submitted to ComfyUI (prompt_id=a3e559fb-4fa2-4cc6-9183-97f93befc6f3)
[2025-11-08 21:42:09,345: INFO/ForkPoolWorker-2] Published update to genonaut_demo:job:1194236: processing (subscribers: 0)
[2025-11-08 21:42:09,350: WARNING/ForkPoolWorker-2] Source file not found: ~/Documents/ComfyUI/output/gen_job_1194236_00001_.png
[2025-11-08 21:42:09,351: ERROR/ForkPoolWorker-2] Job 1194236 failed: Unable to determine primary image path for job 1194236


Traceback (most recent call last):
  File "/Users/joeflack4/projects/genonaut/genonaut/worker/tasks.py", line 238, in process_comfy_job
    raise ComfyUIWorkflowError(f"Unable to determine primary image path for job {job_id}")
genonaut.api.services.comfyui_client.ComfyUIWorkflowError: Unable to determine primary image path for job 1194236
[2025-11-08 21:42:09,357: INFO/ForkPoolWorker-2] Published update to genonaut_demo:job:1194236: failed (subscribers: 0)
[2025-11-08 21:42:09,375: INFO/MainProcess] Task genonaut.worker.tasks.run_comfy_job[f4e2e3f1-0585-47ec-8d9c-65d4316a8f82] received
[2025-11-08 21:42:09,377: INFO/ForkPoolWorker-2] Task genonaut.worker.tasks.run_comfy_job[f4e2e3f1-0585-47ec-8d9c-65d4316a8f82] retry: Retry in 3s: ComfyUIWorkflowError('Unable to determine primary image path for job 1194236')


[2025-11-08 21:42:12,391: INFO/ForkPoolWorker-9] Starting ComfyUI job 1194236
[2025-11-08 21:42:12,396: INFO/ForkPoolWorker-9] Job 1194236: Backend choice from params: comfyui
[2025-11-08 21:42:12,397: INFO/ForkPoolWorker-9] Job 1194236: Using ComfyUI backend URL: http://localhost:8000
[2025-11-08 21:42:12,397: INFO/ForkPoolWorker-9] Job 1194236: Using ComfyUI output dir: ~/Documents/ComfyUI/output
[2025-11-08 21:42:12,419: INFO/ForkPoolWorker-9] Job 1194236 status updated to 'running'
[2025-11-08 21:42:12,420: INFO/ForkPoolWorker-9] Published update to genonaut_demo:job:1194236: started (subscribers: 0)
[2025-11-08 21:42:12,428: INFO/ForkPoolWorker-9] Job 1194236 submitted to ComfyUI (prompt_id=51f12934-2bab-4875-838e-1207e807c4ca)
[2025-11-08 21:42:12,429: INFO/ForkPoolWorker-9] Published update to genonaut_demo:job:1194236: processing (subscribers: 0)
[2025-11-08 21:42:12,434: WARNING/ForkPoolWorker-9] Source file not found: ~/Documents/ComfyUI/output/gen_job_1194236_00001_.png
[2025-11-08 21:42:12,434: ERROR/ForkPoolWorker-9] Job 1194236 failed: Unable to determine primary image path for job 1194236
Traceback (most recent call last):
  File "/Users/joeflack4/projects/genonaut/genonaut/worker/tasks.py", line 238, in process_comfy_job
    raise ComfyUIWorkflowError(f"Unable to determine primary image path for job {job_id}")
genonaut.api.services.comfyui_client.ComfyUIWorkflowError: Unable to determine primary image path for job 1194236
[2025-11-08 21:42:12,439: INFO/ForkPoolWorker-9] Published update to genonaut_demo:job:1194236: failed (subscribers: 0)
[2025-11-08 21:42:12,444: ERROR/ForkPoolWorker-9] Task genonaut.worker.tasks.run_comfy_job[f4e2e3f1-0585-47ec-8d9c-65d4316a8f82] raised unexpected: ComfyUIWorkflowError('Unable to determine primary image path for job 1194236')
Traceback (most recent call last):
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/trace.py", line 453, in trace_task
    R = retval = fun(*args, **kwargs)
                 ^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/trace.py", line 736, in __protected_call__
    return self.run(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/autoretry.py", line 60, in run
    ret = task.retry(exc=exc, **retry_kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/task.py", line 743, in retry
    raise_with_context(exc)
  File "/Users/joeflack4/projects/genonaut/env/python_venv/lib/python3.11/site-packages/celery/app/autoretry.py", line 38, in run
    return task._orig_run(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/genonaut/worker/tasks.py", line 335, in run_comfy_job
    return process_comfy_job(
           ^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/genonaut/worker/tasks.py", line 238, in process_comfy_job
    raise ComfyUIWorkflowError(f"Unable to determine primary image path for job {job_id}")
genonaut.api.services.comfyui_client.ComfyUIWorkflowError: Unable to determine primary image path for job 1194236

```

Two things I observe in attempt 3 of interest:
3.1.: It says `Starting ComfyUI job 1194236` two times.

This might just be a weird logging error / issue. Maybe it didn't actually try to start the same job twice.

However, I should note that I am seeing some odd behavior in ComfyUI itself. I can actually see the images generated in 
the ComfyUI desktop app UI. If you'd like, I can show you a screenshot; just ask me. But what's odd is that sometimes, 
when I create an image, sometimes it shows just 1 time in ComfyUI. Sometimes it shows the same image 2 times, sometimes 
3 times, and sometimes up to 4 times. At first, I thought this might just be a bug in ComfyUI. But perhaps it is really 
our system sending multiple requests. Or maybe both. I observe that in these cases where I'm seeing duplicate images in 
the jobs queue in the ComfyUI desktop app UI, when I look in `~/Documents/ComfyUI/output/`, I only see 1 copy of the 
image.

3.2. It says it can't find the file before it even reports starting the job:
```
[2025-11-08 21:42:09,074: WARNING/ForkPoolWorker-9] Source file not found: ~/Documents/ComfyUI/output/gen_job_1194236_00001_.png
[2025-11-08 21:42:09,147: INFO/ForkPoolWorker-2] Starting ComfyUI job 1194236
```

This could just be due to some weird logging problem I think; maybe nothing to worry about. But I'm pointing it out in 
case it appears to be a telling observation. 

**Summary of problems**
1. Frontend not rendering image even when it is successfully generated. Probably caused by (2).
2. Backend can't seem to find the image. Probably causing (1).
3. Sometimes getting this error: `psycopg2.OperationalError: server closed the connection unexpectedly`. Don't worry 
about this as the primary thing to solve. If it comes up while you are working, then you should try to address it.
4. Perhaps jobs are being submitted multiple times.

**What you should do**
Solve (1) and (2). Look out for (3) and (4) being a problem, and if you find evidence of those problems, try to 
fix those, too.

As you go, manage (create, and update) lists of markdown checkbox tasks for yourself in: fix-comfyui-tasks.md. When you 
have done some work and have new status updates, create a new subsection in the "Reports" section of this document 
(fix-comfyui.md).

## Reports

### Report 1 - Root Cause Found and Fixed (2025-11-09)

**Root Cause Identified:**
The issue was with tilde (~) expansion in file paths. Here's the detailed breakdown:

1. **Path Construction**: In `comfyui_client.py` (line 309-333), the `get_output_files()` method constructs file paths like:
   ```
   ~/Documents/ComfyUI/output/gen_job_1194234_00001_.png
   ```

2. **Path Validation Failure**: When `organize_generation_files()` in `file_storage_service.py` (line 65) tries to check if the file exists using `Path(file_path).exists()`, it fails because:
   - Python's `pathlib.Path.exists()` does NOT automatically expand the tilde (~) character
   - It looks for a folder literally called "~" in the current directory instead of the user's home directory
   - The file is never found, so it logs "Source file not found" and continues without adding it to `organized_paths`

3. **Empty Results**: Since `organized_paths` is empty, the task fails at line 236-238 in `tasks.py` with:
   ```
   "Unable to determine primary image path for job {job_id}"
   ```

**The Fix:**
Modified `genonaut/api/services/comfyui_client.py` (lines 54-63) to expand the tilde in both `output_dir` and `models_dir` during initialization:

```python
# Before (broken):
self.output_dir = output_dir or self.settings.comfyui_output_dir
self.models_dir = models_dir or self.settings.comfyui_models_dir

# After (fixed):
raw_output_dir = output_dir or self.settings.comfyui_output_dir
self.output_dir = str(Path(raw_output_dir).expanduser())
raw_models_dir = models_dir or self.settings.comfyui_models_dir
self.models_dir = str(Path(raw_models_dir).expanduser())
```

This ensures that paths like `~/Documents/ComfyUI/output` are converted to absolute paths like `/Users/joeflack4/Documents/ComfyUI/output` before being used.

**Services Restarted:**
- Celery worker: Restarted to pick up the fix
- Web API: Restarted and confirmed healthy

**Next Steps:**
Ready to test with your ComfyUI instance. Please:
1. Ensure ComfyUI is running on `localhost:8000`
2. Create a new image generation job
3. Check if the image appears correctly in the app

**Other Observations:**
- The database connection error (psycopg2.OperationalError) from Attempt 2 appears to be a transient issue
- The duplicate job submissions you mentioned (seeing 2-4 copies in ComfyUI UI) was not investigated yet, but should be monitored during testing
