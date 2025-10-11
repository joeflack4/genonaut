This was one of the logs when I was seeding the DB. it shows some errors, but i think they were recovered from and it completed successfully. But i think maybe something went wrong and the quality wasn't as good because of these. It might have something to do with discarded users and job data, and gen jobs not matching up with content items. I'm not sure if this is fixed or not.

Original log:
```
/Users/joeflack4/virtualenvs/genonaut/bin/python -X pycache_prefix=/Users/joeflack4/Library/Caches/JetBrains/PyCharm2025.2/cpython-cache /Applications/PyCharm.app/Contents/plugins/python-ce/helpers/pydev/pydevd.py --multiprocess --qt-support=auto --client 127.0.0.1 --port 59589 --file /Users/joeflack4/projects/genonaut/genonaut/db/demo/seed_data_gen/__main__.py generate --database-url postgresql://genonaut_admin:chocolateRainbows858@localhost:5432/genonaut_demo --target-rows-users 1000 --target-rows-content-items 5000 --target-rows-content-items-auto 10000 
Connected to: <socket.socket fd=3, family=2, type=1, proto=0, laddr=('127.0.0.1', 59590), raddr=('127.0.0.1', 59589)>.
Connected to pydev debugger (build 252.23892.515)
2025-09-24 16:06:10,233 - __main__ - INFO - Starting synthetic data generation CLI
2025-09-24 16:06:10,233 - __main__ - INFO - Using validated database URL: postgresql://genonaut_admin:chocolateRainbows858@localhost:5432/genonaut_demo
2025-09-24 16:06:10,234 - __main__ - INFO - Configuration loaded: batch_size_users=1000 batch_size_content_items=2000 batch_size_content_items_auto=2000 batch_size_generation_jobs=5000 target_rows_users=1000 target_rows_content_items=5000 target_rows_content_items_auto=10000 max_workers=4 prompt_min_general_phrases=0 prompt_max_general_phrases=10 prompt_min_domain_phrases=4 prompt_max_domain_phrases=30 images_dir='io/storage/images/' admin_user_uuid='121e194b-4caa-4b81-ad4f-86ca3919d5b9'
2025-09-24 16:06:10,257 - __main__ - INFO - Database session established
2025-09-24 16:06:10,257 - genonaut.db.demo.seed_data_gen.generator - INFO - Starting synthetic data generation
Starting synthetic data generation...
2025-09-24 16:06:10,323 - genonaut.db.demo.seed_data_gen.bulk_inserter - INFO - Current wal_buffers: 4MB
2025-09-24 16:06:10,326 - genonaut.db.demo.seed_data_gen.bulk_inserter - INFO - Setting wal_buffers to 64MB using ALTER SYSTEM...
2025-09-24 16:06:10,328 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - wal_buffers has been changed via ALTER SYSTEM. The new setting will take effect after the next PostgreSQL restart.
2025-09-24 16:06:10,328 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - For optimal performance, consider restarting PostgreSQL now and re-running the seed data generation.
2025-09-24 16:06:10,328 - genonaut.db.demo.seed_data_gen.bulk_inserter - INFO - Bulk insert optimizations applied successfully

1. Generating Users...
2025-09-24 16:06:10,780 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: stevensonlouis
2025-09-24 16:06:10,787 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: daviskelly
2025-09-24 16:06:11,109 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: robert14
2025-09-24 16:06:11,220 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: mcconnelldana
2025-09-24 16:06:11,435 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: erik57
2025-09-24 16:06:11,522 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: farrellmichael
2025-09-24 16:06:11,575 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: shaneolson
2025-09-24 16:06:11,578 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: gloriacarter
2025-09-24 16:06:11,622 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: fmartinez
2025-09-24 16:06:11,717 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: adam56
2025-09-24 16:06:11,760 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: mmiller
2025-09-24 16:06:11,886 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: orodriguez
2025-09-24 16:06:11,980 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: wmiller
2025-09-24 16:06:12,045 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: david10
2025-09-24 16:06:12,091 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: johnsonjulia
2025-09-24 16:06:12,283 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: iarnold
2025-09-24 16:06:12,307 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: wcastro
2025-09-24 16:06:12,368 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: ashleybaker
2025-09-24 16:06:12,410 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: kholland
2025-09-24 16:06:12,497 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Username conflict: charles51
2025-09-24 16:06:12,578 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Removed 20 users due to username conflicts: stevensonlouis, daviskelly, robert14, mcconnelldana, erik57, farrellmichael, shaneolson, gloriacarter, fmartinez, adam56...
users: 980/1000 (98.0%)
users: 1000/1000 (100.0%)
✓ users: 1000/1000 (100.0%)
2025-09-24 16:06:12,601 - genonaut.db.demo.seed_data_gen.generator - INFO - Generated 1000 users with 20 conflicts resolved

2. Generating Content Items...

   Generating content_items...
content_items: 2000/5000 (40.0%)
content_items: 4000/5000 (80.0%)
content_items: 5000/5000 (100.0%)
✓ content_items: 5000/5000 (100.0%)

   Generating content_items_auto...
2025-09-24 16:06:15,286 - genonaut.db.demo.seed_data_gen.generator - INFO - Generated 5000 content_items
content_items_auto: 2000/10000 (20.0%)
content_items_auto: 4000/10000 (40.0%)
content_items_auto: 6000/10000 (60.0%)
content_items_auto: 8000/10000 (80.0%)
content_items_auto: 10000/10000 (100.0%)
✓ content_items_auto: 10000/10000 (100.0%)

3. Generating Generation Jobs...
   Creating completed jobs for all content items...
2025-09-24 16:06:20,586 - genonaut.db.demo.seed_data_gen.generator - INFO - Generated 10000 content_items_auto
completed generation_jobs: 5000/15000 (33.3%)
completed generation_jobs: 10000/15000 (66.7%)
completed generation_jobs: 15000/15000 (100.0%)
✓ completed generation_jobs: 15000/15000 (100.0%)
   Creating 306 additional jobs for status distribution...
additional generation_jobs: 306/306 (100.0%)
✓ additional generation_jobs: 306/306 (100.0%)
   Linking jobs to content items...
2025-09-24 16:06:23,853 - genonaut.db.demo.seed_data_gen.generator - INFO - Generated 15306 total generation jobs (15000 completed, 306 additional)
2025-09-24 16:06:25,295 - genonaut.db.demo.seed_data_gen.generator - INFO - Updated 15298 jobs with content_items references
2025-09-24 16:06:25,383 - genonaut.db.demo.seed_data_gen.bulk_inserter - WARNING - Could not restore normal settings: (psycopg2.errors.InFailedSqlTransaction) current transaction is aborted, commands ignored until end of transaction block

[SQL: SET synchronous_commit = ON]
(Background on this error at: https://sqlalche.me/e/20/2j85)
2025-09-24 16:06:25,384 - genonaut.db.demo.seed_data_gen.generator - ERROR - Data generation failed after 15.13 seconds: (psycopg2.errors.ForeignKeyViolation) insert or update on table "generation_jobs" violates foreign key constraint "generation_jobs_result_content_id_fkey"
DETAIL:  Key (result_content_id)=(10957) is not present in table "content_items".

[SQL: 
            UPDATE generation_jobs
            SET result_content_id = (
                SELECT id FROM content_items_auto
                WHERE content_items_auto.creator_id = generation_jobs.user_id
                AND generation_jobs.status = 'completed'
                AND generation_jobs.result_content_id IS NULL
                LIMIT 1
            )
            WHERE generation_jobs.status = 'completed'
            AND generation_jobs.result_content_id IS NULL
        ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)

============================================================
SYNTHETIC DATA GENERATION COMPLETE
============================================================

Table Counts:
  users: 2,000 records
  content_items: 10,000 records
  content_items_auto: 10,000 records
  generation_jobs: 15,306 records

Conflicts Resolved:
  users: 20 conflicts

Total Execution Time: 15.13 seconds
Generation Rate: 2466 records/second
============================================================
2025-09-24 16:06:25,393 - __main__ - ERROR - Synthetic data generation failed: (psycopg2.errors.ForeignKeyViolation) insert or update on table "generation_jobs" violates foreign key constraint "generation_jobs_result_content_id_fkey"
DETAIL:  Key (result_content_id)=(10957) is not present in table "content_items".

[SQL: 
            UPDATE generation_jobs
            SET result_content_id = (
                SELECT id FROM content_items_auto
                WHERE content_items_auto.creator_id = generation_jobs.user_id
                AND generation_jobs.status = 'completed'
                AND generation_jobs.result_content_id IS NULL
                LIMIT 1
            )
            WHERE generation_jobs.status = 'completed'
            AND generation_jobs.result_content_id IS NULL
        ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
Traceback (most recent call last):
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
    cursor.execute(statement, parameters)
psycopg2.errors.ForeignKeyViolation: insert or update on table "generation_jobs" violates foreign key constraint "generation_jobs_result_content_id_fkey"
DETAIL:  Key (result_content_id)=(10957) is not present in table "content_items".


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/joeflack4/projects/genonaut/genonaut/db/demo/seed_data_gen/__main__.py", line 189, in main
    generator.generate_all_data()
  File "/Users/joeflack4/projects/genonaut/genonaut/db/demo/seed_data_gen/generator.py", line 45, in generate_all_data
    self._generate_generation_jobs(user_ids, content_items_data, content_items_auto_data)
  File "/Users/joeflack4/projects/genonaut/genonaut/db/demo/seed_data_gen/generator.py", line 205, in _generate_generation_jobs
    self._update_job_content_references()
  File "/Users/joeflack4/projects/genonaut/genonaut/db/demo/seed_data_gen/generator.py", line 269, in _update_job_content_references
    auto_updates = self.bulk_inserter.update_generation_jobs_with_content_ids("content_items_auto")
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/projects/genonaut/genonaut/db/demo/seed_data_gen/bulk_inserter.py", line 119, in update_generation_jobs_with_content_ids
    result = self.session.execute(query)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2365, in execute
    return self._execute_internal(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/orm/session.py", line 2260, in _execute_internal
    result = conn.execute(
             ^^^^^^^^^^^^^
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1419, in execute
    return meth(
           ^^^^^
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1641, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1846, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1986, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 2355, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/joeflack4/virtualenvs/genonaut/lib/python3.11/site-packages/sqlalchemy/engine/default.py", line 951, in do_execute
    cursor.execute(statement, parameters)
sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) insert or update on table "generation_jobs" violates foreign key constraint "generation_jobs_result_content_id_fkey"
DETAIL:  Key (result_content_id)=(10957) is not present in table "content_items".

[SQL: 
            UPDATE generation_jobs
            SET result_content_id = (
                SELECT id FROM content_items_auto
                WHERE content_items_auto.creator_id = generation_jobs.user_id
                AND generation_jobs.status = 'completed'
                AND generation_jobs.result_content_id IS NULL
                LIMIT 1
            )
            WHERE generation_jobs.status = 'completed'
            AND generation_jobs.result_content_id IS NULL
        ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
2025-09-24 16:06:25,406 - __main__ - INFO - Database session closed
Error: (psycopg2.errors.ForeignKeyViolation) insert or update on table "generation_jobs" violates foreign key constraint "generation_jobs_result_content_id_fkey"
DETAIL:  Key (result_content_id)=(10957) is not present in table "content_items".

[SQL: 
            UPDATE generation_jobs
            SET result_content_id = (
                SELECT id FROM content_items_auto
                WHERE content_items_auto.creator_id = generation_jobs.user_id
                AND generation_jobs.status = 'completed'
                AND generation_jobs.result_content_id IS NULL
                LIMIT 1
            )
            WHERE generation_jobs.status = 'completed'
            AND generation_jobs.result_content_id IS NULL
        ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)

Process finished with exit code 1
```