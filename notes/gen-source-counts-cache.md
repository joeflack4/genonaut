# Caching of counts "by gen source"
## Preamble
We have a concept of "generation source". There are 2 dimensions, and 2 vals in each dimension:

Dimension 1: auto (content_items_auto table) vs manually generated (content_items table)
Dimension 2: User vs community (all users; AKA all rows in table)

You can see these refrenced in their own way in the Gallery page, e.g. in the options sidebar:

```
Filter by gen source
- Your gens
- Your auto-gens
- Community gens
- Community auto-gens
```

There are also counts for each of these categories that will display if you hover over the (i) icon where it says 
"n pages showing n results matching filters."

When you hover over that, it does a query which gets the counts, and then displays them. But it's a bit slow.

We'd like to cache the counts in some table. You could call it: counts_gen_source_stats

Here, we should store the totals for auto-gens vs regular gens for the total of the community, and also by each user.

These should be cached every hour. You can use a celery worker to do that. There's a way to set up configuration for 
that, and it is described in some recent work that was done for another stats table. You can read this to see how it's 
done: `notes/celery-beat-independent-worker--mvp-tag-cardinality-stats.md`

## General instructions
Read this, think about it, do any background reading / research you need, and then create a list of checkbox tasks in 
this document, in the Tasks section. Execute on the tasks, doing as many as you can without human intervention (
preferably all at once). Then, you can give a final report in the "Reports" section.  

## Tasks

## Reports
