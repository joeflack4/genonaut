# Fix "Image Generation" page errors
We currently have a nice setup on our image generation page, but it is not erroring gracefully when an error occurs 
after pressing the "Generate" button. 

The page just becomes blank. And hitting the back button doesn't do anything; effectively a "white scren of death".

Tasks:
1. Fix the exception itself
2. Add an error boundary so that we don't get this white screen of death

## 1. Fix the exception itself
err log:
```
Uncaught ReferenceError: useRef is not defined
    at GenerationProgress (GenerationProgress.tsx:95:30)
    at Object.react_stack_bottom_frame (react-dom_client.js?v=6e96e4bf:17422:20)
    at renderWithHooks (react-dom_client.js?v=6e96e4bf:4204:24)
    at updateFunctionComponent (react-dom_client.js?v=6e96e4bf:6617:21)
    at beginWork (react-dom_client.js?v=6e96e4bf:7652:20)
    at runWithFiberInDEV (react-dom_client.js?v=6e96e4bf:1483:72)
    at performUnitOfWork (react-dom_client.js?v=6e96e4bf:10866:98)
    at workLoopSync (react-dom_client.js?v=6e96e4bf:10726:43)
    at renderRootSync (react-dom_client.js?v=6e96e4bf:10709:13)
    at performWorkOnRoot (react-dom_client.js?v=6e96e4bf:10357:46)
```

## 2. Add an error boundary so that we don't get this white screen of death
This warning shows up in my console. I think if you read this and follow the instructions, this should fix the white 
screen of death problem.

```
GenerationPage.tsx:68 An error occurred in the <GenerationProgress> component.
Consider adding an error boundary to your tree to customize error handling behavior.
Visit https://react.dev/link/error-boundaries to learn more about error boundaries.
```
