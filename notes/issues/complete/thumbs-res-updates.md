Can you update the grid thumbnail sizes dropdown? instead of the list of current resolutiosn that it has, can you use these instead?

The label should continue to be WIDTHxHEIGHT

Also, add a popOver so that when the user hovers over the dropdown item for 1+ second, it displays a little tooltip like:

```
Width: WIDTH
Height: HEIGHT
```

| Scale | Width | Height | % of Base |
| ----- | ----- | ------ | --------- |
| 100%  | 512   | 768    | 100 %     |
| 90%   | 460   | 691    | ~90 %     |
| 80%   | 410   | 614    | ~80 %     |
| 70%   | 358   | 538    | ~70 %     |
| 60%   | 307   | 461    | ~60 %     |
| 50%   | 256   | 384    | 50 %      |

I want this to be the list that shows up in the dropdown, but I wonder--perhaps this will have ramifications elsewhere 
in the codebase (frontend, backend, or tests), so if needed, please make updates there as well.