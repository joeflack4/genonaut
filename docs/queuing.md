## Queuing: Celery + Redis for Async Tasks

Genonaut uses Celery with Redis for asynchronous task processing, primarily for image generation jobs via ComfyUI integration.

### Prerequisites

1. **Redis Server**: Install and start Redis
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis

   # Docker
   docker run -d -p 6379:6379 redis:latest
   ```

2. **Environment Variables**: Already configured in `.env` (see env/.env for Redis URLs and namespaces)

### Set up
There is a configuration example currently in `env/redis.conf.example`. Use this as a template to create 
`env/redis.conf`, and be sure to set a real password. 

### Running Workers

Start a Celery worker to process async tasks:

```bash
# Development environment
make celery-dev              # Start Celery worker for dev

# Demo/Test environments
make celery-demo             # Start Celery worker for demo
make celery-test             # Start Celery worker for test
```

**Typical Workflow:**
```bash
# Terminal 1: Start API server
make api-dev

# Terminal 2: Start Celery worker
make celery-dev

# Terminal 3: (Optional) Start Flower monitoring dashboard
make flower-dev              # Access at http://localhost:5555
```

### Flower Monitoring Dashboard

Monitor your Celery workers and tasks in real-time:

```bash
make flower-dev              # Development (http://localhost:5555)
make flower-demo             # Demo
make flower-test             # Test
```

Flower provides:
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Task retry and revoke capabilities

### Redis Management

Useful Redis commands for development:

```bash
# View keys in Redis
make redis-keys-dev          # List all keys in dev DB
make redis-info-dev          # Show Redis DB size

# Clear Redis data (use with caution!)
make redis-flush-dev         # Flush dev Redis DB (DB 4)
make redis-flush-demo        # Flush demo Redis DB (DB 2)
make redis-flush-test        # Flush test Redis DB (DB 3)
```

### How It Works

1. **Job Creation**: When you create a generation job via API, it's queued in Celery
2. **Worker Processing**: Celery worker picks up the job and processes it asynchronously
3. **Status Updates**: Job status is updated in the database (pending → running → completed/failed)
4. **Task ID**: Each job has a `celery_task_id` for tracking and cancellation

**Example API Usage:**
```bash
# Create a generation job (returns immediately with job_id)
curl -X POST http://localhost:8001/api/v1/generation-jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-id",
    "job_type": "image",
    "prompt": "a beautiful sunset over mountains",
    "width": 832,
    "height": 1216
  }'

# Check job status
curl http://localhost:8001/api/v1/generation-jobs/{job_id}

# Cancel a job
curl -X POST http://localhost:8001/api/v1/generation-jobs/{job_id}/cancel
```

### Troubleshooting

**Worker won't start:**
- Ensure Redis is running: `redis-cli ping` (should return "PONG")
- Check environment variables in `.env`
- Verify Python virtual environment is activated

**Jobs stuck in pending:**
- Ensure Celery worker is running
- Check worker logs for errors
- Verify Redis connection: `redis-cli -n 4 KEYS '*'` (for dev)

**Clear stuck jobs:**
```bash
make redis-flush-dev         # Clear all Redis data for dev
```

## WebSocket Real-Time Updates

Genonaut provides WebSocket endpoints for real-time job status updates. Clients can connect to monitor generation job progress and receive instant notifications when jobs complete.

### WebSocket Endpoints

**Monitor a single job:**
```
ws://localhost:8001/ws/jobs/{job_id}
```

**Monitor multiple jobs:**
```
ws://localhost:8001/ws/jobs?job_ids=123,456,789
```

### Message Format

The WebSocket server sends JSON messages for job status updates:

```json
{
  "job_id": 123,
  "status": "started|processing|completed|failed",
  "timestamp": "2025-10-03T12:00:00Z"
}
```

**Status-specific fields:**

- `processing`: May include `"progress": 50` (percentage)
- `completed`: Includes `"content_id": 456` and `"output_paths": [...]`
- `failed`: Includes `"error": "error message"`

### Example Client Usage

**JavaScript/Browser:**
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/jobs/123');

ws.onopen = () => {
  console.log('Connected to job 123');
};

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);

  switch (update.status) {
    case 'started':
      console.log('Job started!');
      break;
    case 'processing':
      console.log(`Processing... ${update.progress || 0}%`);
      break;
    case 'completed':
      console.log('Completed! Content ID:', update.content_id);
      console.log('Image paths:', update.output_paths);
      break;
    case 'failed':
      console.error('Failed:', update.error);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
};

// Keep connection alive with ping/pong
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

**Python:**
```python
import asyncio
import websockets
import json

async def monitor_job(job_id):
    uri = f"ws://localhost:8001/ws/jobs/{job_id}"

    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Job {data['job_id']}: {data['status']}")

            if data['status'] == 'completed':
                print(f"Content ID: {data['content_id']}")
                break
            elif data['status'] == 'failed':
                print(f"Error: {data['error']}")
                break

# Run the monitor
asyncio.run(monitor_job(123))
```

### Connection Health

The WebSocket server supports ping/pong messages to keep connections alive:

```javascript
// Send ping
ws.send(JSON.stringify({ type: 'ping' }));

// Server responds with pong
// { "type": "pong" }
```

### Requirements

- Redis must be running for pub/sub messaging
- Celery worker must be running to publish job updates
- WebSocket connections are stateful - reconnect if disconnected