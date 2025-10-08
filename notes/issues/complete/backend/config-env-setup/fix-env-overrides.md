# Fix .env overrides of configs
We recently set things up so that we start the web API, and it needs to set some properties. It will reach for some 
configuration files to get values for that. It loads base.json for all environments. But there are different 
environments, by LOCATION-TYPE. for example, local-demo. You can see this in config/ and env/. You'll see 
local-demo.json and .env/local-demo.

Right now, these properites are currently being read and set correctly from the config files. But I can see that the 
overrides are not working. For example, I have local-demo.json which has `"comfyui-url": "http://localhost:8000",`. But, 
I'm actually trying to override that. In .env.local-demo, I have `COMFYUI_URL=http://localhost:8189`. The way we have 
things set up, the app is supposed to understand that these are the same variable, and it is supposed to use that one 
instead. And also I'm noticing that it doesn't recognize and override if the variable is present in env/.env either.

This is the original load order that was supposed to be set up:

**Load Order (lowest → highest precedence)**
1. `config/base.json`
2. `config/{ENV_TARGET}.json` (more on `ENV_TARGET` will be discussed in the makefile section / elsewhere)
3. `env/.env.shared`
4. `env/.env.{ENV_TARGET}`
5. process env (CI, shell)
6. local `env/.env` (developer overrides, optional)

Can you please fix the web API so that it is indeed following this load order?

And please add some tests to ensure that this is happening correctly. You can add some example test input files to a new
input/ dir where you feel it would be apprporiate somewhere in `test/api` or one of its subdirs.

Make sure those tests and all the backend tests (`make test`) continue to pass after you make this fix.