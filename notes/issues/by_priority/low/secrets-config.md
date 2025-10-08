# Considering: not sure I wanna do yet
## Context
Proposed during the config / env refactor 2025/10/08. But I haven't yet set up a secret system.

## Secret Management
Have a setup that supports .env and also a secrets manager.

### Local Development
- Secrets live in `.env`.
- Never committed to version control.
- Environment variables can override config values at runtime.

### Cloud Deployment
- Secrets are stored in **AWS Secrets Manager** or **AWS SSM Parameter Store**.
- Application retrieves them through a configurable `SecretProvider` abstraction:

```python
class SecretProvider:
    def get(self, name: str) -> str: ...

class EnvProvider(SecretProvider):
    def get(self, name): return os.getenv(name)

class AwsProvider(SecretProvider):
    def get(self, name):
        # later: integrate boto3 SSM or Secrets Manager
        pass
```

Configured via:
```
SECRETS_BACKEND=env  # or aws
```

Secrets never appear in JSON configs.