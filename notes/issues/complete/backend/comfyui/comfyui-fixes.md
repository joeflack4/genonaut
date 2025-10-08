# MockComfyUIServer updates
I'd like to make some updates to the `MockComfyUIServer` I noticed that it doesn't return a response pattern that I would 
expect. And it's possible that the actual ComfyUI code in the web API backend is set up correctly. So you should check 
and also ensure that is the case.

## Request/response cycle
Below are actual real examples of what it's like to interact with the ComfyUI web API. Make sure that our backend is set
up to match this, and that `MockComfyUIServer` mimics this.

### 1. Example POST
```sh
curl -X POST http://127.0.0.1:8000/prompt \
     -H "Content-Type: application/json" \
     -d @/Users/joeflack4/projects/genonaut/test/integrations/comfyui/input/1.json
```

### 2. Example response
```json
{"prompt_id": "1434a7a1-7412-41ca-b625-16e1fe56e524", "number": 0, "node_errors": {}}%
```



### 3. Check on status
#### GET http://localhost:8000/history/1434a7a1-7412-41ca-b625-16e1fe56e524

#### Response if ComfyUI is still running / generating the image
Just returns an empty object:
```json
{}
```

So in order to check completion status, will need to keep polling. This is how the whole image generation workflow is 
set up already.

Note that I'm not sure if the `MockComfyUIServer` returns this response as an alternative to "successful generation". 
I think you should update the `MockComfyUIServer` client so that it waits at least 0.5 seconds before successfully 
"creating" the image. In the meantime, see if you can have a test that does a submission and checks in less than 0.5 
seconds and indeed gets back `{}`. And then make sure to have the test check > 0.5 seconds to get the actual result.

#### Response when completed
```json
{
   "1434a7a1-7412-41ca-b625-16e1fe56e524":{
      "prompt":[
         0,
         "1434a7a1-7412-41ca-b625-16e1fe56e524",
         {
            "1":{
               "class_type":"CheckpointLoaderSimple",
               "inputs":{
                  "ckpt_name":"illustriousXL_v01.safetensors"
               }
            },
            "2":{
               "class_type":"LoraLoader",
               "inputs":{
                  "model":[
                     "1",
                     0
                  ],
                  "clip":[
                     "1",
                     1
                  ],
                  "lora_name":"char/maomaoIllustrious.safetensors",
                  "strength_model":0.8,
                  "strength_clip":0.8
               }
            },
            "3":{
               "class_type":"LoraLoader",
               "inputs":{
                  "model":[
                     "2",
                     0
                  ],
                  "clip":[
                     "2",
                     1
                  ],
                  "lora_name":"misc/styles/Ghibli_MK2_style_illustV1.safetensors",
                  "strength_model":0.6,
                  "strength_clip":0.6
               }
            },
            "4":{
               "class_type":"CLIPTextEncode",
               "inputs":{
                  "clip":[
                     "3",
                     1
                  ],
                  "text":"masterpiece, detailed anime scene, character smiling softly, cozy room, mixing herbs with mortar and pestle, sitting at desk"
               }
            },
            "5":{
               "class_type":"CLIPTextEncode",
               "inputs":{
                  "clip":[
                     "3",
                     1
                  ],
                  "text":"low quality, blurry, extra fingers"
               }
            },
            "6":{
               "class_type":"EmptyLatentImage",
               "inputs":{
                  "width":832,
                  "height":1216,
                  "batch_size":1
               }
            },
            "7":{
               "class_type":"KSampler",
               "inputs":{
                  "seed":123456,
                  "steps":28,
                  "cfg":5.5,
                  "sampler_name":"euler",
                  "scheduler":"normal",
                  "denoise":1,
                  "model":[
                     "3",
                     0
                  ],
                  "positive":[
                     "4",
                     0
                  ],
                  "negative":[
                     "5",
                     0
                  ],
                  "latent_image":[
                     "6",
                     0
                  ]
               }
            },
            "8":{
               "class_type":"VAEDecode",
               "inputs":{
                  "samples":[
                     "7",
                     0
                  ],
                  "vae":[
                     "1",
                     2
                  ]
               }
            },
            "9":{
               "class_type":"SaveImage",
               "inputs":{
                  "images":[
                     "8",
                     0
                  ],
                  "filename_prefix":"sdxl_anime"
               }
            }
         },
         {
            "client_id":"7a232450-b089-419d-86d5-a1ee09c6995d"
         },
         [
            "9"
         ]
      ],
      "outputs":{
         "9":{
            "images":[
               {
                  "filename":"sdxl_anime_00005_.png",
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
                  "prompt_id":"1434a7a1-7412-41ca-b625-16e1fe56e524",
                  "timestamp":1760036086769
               }
            ],
            [
               "execution_cached",
               {
                  "nodes":[
                     
                  ],
                  "prompt_id":"1434a7a1-7412-41ca-b625-16e1fe56e524",
                  "timestamp":1760036086773
               }
            ],
            [
               "execution_success",
               {
                  "prompt_id":"1434a7a1-7412-41ca-b625-16e1fe56e524",
                  "timestamp":1760036181587
               }
            ]
         ]
      },
      "meta":{
         "9":{
            "node_id":"9",
            "display_node":"9",
            "parent_node":null,
            "real_node_id":"9"
         }
      }
   }
}
```

Note these parts of the above example which are of particular importance to us: (i) status, (ii) outpath:
```
      "outputs":{
         "9":{
            "images":[
               {
                  "filename":"sdxl_anime_00005_.png",
                  "subfolder":"",
                  "type":"output"
               }
            ]
         }
      },
      "status":{
         "status_str":"success",
```

It doesn't seem like `MockComfyUIServer` is set up correctly for this (and I'm not sure about the actual backend either
). For example, I submitted a job to the mock, and in the frontend, I saw the error "Unable to determine primary image 
path for job 1193910", and I saw in the celery worker log that it couldn't find an image at 
"/Users/joeflack4/Documents/ComfyUI/output/gen_job_1193910_00037_.png". It looks like it's hard coding for this. But 
that's not right. The `MockComfyUIServer` moves a file from an `input/` dir into an `output/` dir. The path to the file 
that it creates when doing this operation is the path that it should return. 

## Overall workflow for executing this task
1. Create a notes/comfyui-fixes-tasks.md, where you write a (possibly multi-phased) checklist of tasks that you need to 
do to complete everything.
2. Read and follow instructions in: notes/routines/iteration.md and follow those practices for completing these tasks.