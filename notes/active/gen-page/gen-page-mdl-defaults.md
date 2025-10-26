# Generation page - model defaults
## Intro
I'd like to display some default values for checkpoint and lora models on the generation page.

Right now, we're just working on the demo, so I'm going to pre-seed some values. In the future, we will pull this 
information from the file system, an online data store, some sophisticated registry, or some combination of that.

We're going to want to make 2 new SqlAlchemy models for 2 new tables:

1. Checkpoint models
2. Lora models

The seed data for this will for now be locatd in the following files:
1. Checkpoint models: `genonaut/db/demo/seed_data_static/models_checkpoints.csv`
2. Lora models: `genonaut/db/demo/seed_data_static/models_loras.csv`

## Database updates
For the database fields, use the columns in those files. And also add an ID field (UUID), and last_created and 
last_updated datetime fields.

If possible, see if there is a way you can make it such that when data is inserted into the database, if there is a path
present, but no filename, then the filename should be the final part of the path (e.g. MODEL.safetensors). If there is a
filename (either with the inserted data, or as the result of inference from the path), but 'name' is null, then set the 
name of the model as the filename, sans the extension (e.g. MODEL). 'path' should be the only field that is not 
nullable. And it should also be unique. Filename and name should also be unique.

The following fields should be 'array' types:
- tags
- trigger_words
- compatible_architectures
- optimal_checkpoints

The 'version' field should be string, not integer.

The 'metadata' field should be JSONB.

The 'rating' field should be a float between 0 and 1.

Ideally, for populating the filename and name field if they are missing, it'd be great if this can be some kind of 
automatic postgres operation. And it'd be great if somehow we could define that statically in the SqlAlchemy model 
classes themselves. I don't want to have to set this up by creating a manual migration file. Do NOT create a manual 
migration file (please read: `genonaut/db/migrations/AGENTS.md`). So if we can't have PostgreSQL automatically do this, 
then set it up so that when we use Python to run the insertions against the DB, populating these field values can happen
at the Python level.   

Indexing:
- Standard indexing for: name, path, rating, architecture, family
- GIN indexes (for finding the presence of words): all array and JSONB fields in these tables
- GiST indexes (for search) for the following fields: description

After you finish setting up the models, do an automatic migration on the demo database: 
`make migrate-prep; make migrate-demo`. If there are any issues, come to me and let me help.

## Seeding
Next, make sure that the database seeding script has a separate function purely for seeding data from 
`genonaut/db/demo/seed_data_static/`. Set it up so that if there is any TSV or CSV found there that has the same name as
a table name, it will read that file, and for each row in it, insert a row into the DB in the corresponding table.

Make sure the normal database seeding script does this somewhere. Near the beginning of the script, before it creates 
synthetic data is probably a good place. And also make sure that the CLI has an additional arg that can be called which 
makes it so that we can run a command to ONLy insert the call the function that seeds the `seed_data_static/` data. 
Then, add a makefile command (in the same location in the makefile as the other synthetic data commands) that calls 
this command; a name something like 'seed-data-synthetic'. After you have that set up, run it, and please ensure that 
the data is indeed in the DB.

## API
Make sure that the API server is updated with routs and everything else for dealing with these 2 new tables / models.

## Frontend
Ensure that the "Image Generation" page is set up to query for the list of these models and checkpoints. 

Sort lora and checkpoint models by rating, descending.

## Testing
Add testing at all phases. Use TDD.

Add some playwright tests to ensure that at least 1 checkpoint and 1 lora model is displayed on the page.

## High level tasks
1. Make a document: `notes/gen-page-mdl-defaults-tasks.md`, where you put a phased checklist of your tasks.
2. Use the routine: `notes/routines/iteration.`md for this work.
3. Start execution on those tasks, phase by phase.
