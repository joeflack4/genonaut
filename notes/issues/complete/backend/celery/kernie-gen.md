# KernieGen - The ComfyUI mock server 
I just changed `COMFYUI_URL` in `.env` to override what is in the config file for local-demo. Now it points to the mock comfyui server 
url (aka kernie-gen). I started the mock server. it's be running on that port. I then restarted my api-server.

But, I want to the "image generation" page and clicked "generate". I would at least expect to see some activity in the
"kernie-gen" server logs--but nothing.

Can you figure out why, and explain it in a document called: "notes/kernie-gen-tasks.md". In that, explain what you 
found, and propose a list of tasks to address the issue. If there are any questions, create 
`notes/kernie-gen-questions.md`, for any questions that you need me to answer.
