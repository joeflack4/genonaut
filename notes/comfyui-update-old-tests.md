i'm looking at TestComfyUIIntegration. These are the old mock classes that I thought
were just doing mocks and NOT actually relying on ComfyUI to be running, but I see  these lines:

```
          if not self.client.health_check():
              pytest.skip("ComfyUI is not running on localhost:8000. Please start
  ComfyUI to run this test.")
```

but yet, if i close comfyui, i run the tests, and they pass. so it looks like it is not relying on ComfyUI to be running.

Can you look through these older tests, the one with the pattern `test_comfyui_mock_class*.py`, and confirm? And update 
this error message if so, perhaps.

Note that I moved all the comfyui related files into a single dir: `test/integrations/comfyui/`