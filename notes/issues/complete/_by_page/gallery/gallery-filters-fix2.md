# More filter fixes
The filters are working better now. But they are not perfect. Right now, I am judging whether or not they are working 
by looking to see if at least "n" changes ("n" and "n2" in the "n pages showing n2 results matching filters.") when I 
toggle off single filters or combinations of filters. I am not sure the underlying cause for these issues, but I can 
give you various examples of things not working. Note: This is me operating on the currently running 'demo' api server. 
It might be a good idea for you to verify this yourself--that the issue exists on 'demo', either before you write any 
new tests, or after you write them. I'm not sure if the issue exists in the backend, the frontend, or both. You could 
try querying the backend with these different combinations of filters and see what kind of response you get. Maybe 
you'll find that it's just a backend issue. But if those queries look good, then you should look at fixing the frontend.
 
## Problem cases:
FYI, right now when all filters are "on", it shows: "47,001 pages showing 1,175,018 results matching filters."
Here are the combos I have seen that do not work. By "do not work", I mean that I start with a state where all of the 
toggles are "on" (all content is being shown), and then I turn 1 or more of them off.
1. Turn "Your gens" off
2. Turn "Your auto-gens" off
3. Turn "Community gens" off
4. Turn "Community auto-gens" off
For (1) through (4), the result is the same each time. It still shows: "47,001 pages showing 1,175,018 results matching 
5. filters.", and I notice no change in the page's rendering.
5. Turn "Your gens" and "Community auto-gens" off
6. Turn "Your auto-gens" and "Community gens" off
 
## Cases that are actually OK:
If I do these combinations, I can see that the n pages/results change, and the page starts to render differently.
1. Turning all 4 toggles off
2. "Your gens" + "Your auto-gens" off
3. "Your gens" + "Community gens" off
4. "Your auto-gens" + "Community auto-gens" off
5. "Community gens" + "Community auto-gens" off

## Action plan
- Please create a new multi-phased list of tasks in: `notes/gallery-filters-fix3.md`
- And follow `notes/routines/iteration.md` to complete these tasks.
