# Agent 365 Token Configuration Guide

## Overview

The Agent 365 MCP proxy requires an authentication token to access the Agent 365 API. This guide explains how to configure token paths for different scenarios.

## Default Token Location

By default, tokens are stored in the `.agent365` directory in your home folder:

| Platform | Default Path |
|----------|--------------|
| Windows | `C:\Users\<username>\.agent365\auth-token.json` |
| Mac | `/Users/<username>/.agent365/auth-token.json` |
| Linux | `/home/<username>/.agent365/auth-token.json` |

## Token File Format

The token file is a JSON document with the following structure:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "0.AXoA...",
  "expires_at": 1707868234.5678
}
```

### Fields

- `access_token` - JWT bearer token for API authentication
- `token_type` - Always "Bearer"
- `expires_in` - Token lifetime in seconds (typically 3600 = 1 hour)
- `refresh_token` - Token used to obtain new access tokens (not currently used)
- `expires_at` - Unix timestamp when token expires

## Configuring Token Path

### Method 1: Environment Variable (Recommended)

Set the token path in your Claude Code configuration:

```json
{
  "mcpServers": {
    "agent365-proxy": {
      "command": "python",
      "args": ["C:/Users/jamesol/agent365_mcp_proxy.py"],
      "env": {
        "AGENT365_TOKEN_PATH": "C:/Users/jamesol/.agent365/auth-token.json"
      }
    }
  }
}
```

**Advantages:**
- Explicit configuration
- Easy to change without modifying proxy code
- Supports multiple token locations

### Method 2: Proxy Default

If `AGENT365_TOKEN_PATH` is not set, the proxy falls back to:

```python
# Windows
Path.home() / ".agent365" / "auth-token.json"

# Mac/Linux
Path.home() / ".agent365" / "auth-token.json"
```

**Advantages:**
- Zero configuration for default setup
- Works out of the box

## Token Generation

### Using get_agent365_token.py

The standard method to obtain a token:

```bash
python get_agent365_token.py
```

**What it does:**
1. Opens browser for Microsoft authentication
2. Waits for you to sign in and consent
3. Exchanges authorization code for token
4. Saves token to `~/.agent365/auth-token.json`
5. Sets file permissions to user-only (chmod 600)

**Output:**
```
Opening browser for authentication...
Waiting for authorization code...
Token saved to: C:/Users/jamesol/.agent365/auth-token.json
```

### Manual Token Creation

For automation or CI/CD, you can create tokens manually:

```python
import json
from pathlib import Path

token_data = {
    "access_token": "your_token_here",
    "token_type": "Bearer",
    "expires_in": 3600,
    "expires_at": 1707868234.5678
}

token_path = Path.home() / ".agent365" / "auth-token.json"
token_path.parent.mkdir(parents=True, exist_ok=True)
token_path.write_text(json.dumps(token_data, indent=2))
token_path.chmod(0o600)  # Unix only
```

## Multiple Accounts

To use multiple Agent 365 accounts, configure separate token paths:

```json
{
  "mcpServers": {
    "agent365-work": {
      "command": "python",
      "args": ["C:/Users/jamesol/agent365_proxy_work.py"],
      "env": {
        "AGENT365_TOKEN_PATH": "C:/Users/jamesol/.agent365/work-token.json"
      }
    },
    "agent365-personal": {
      "command": "python",
      "args": ["C:/Users/jamesol/agent365_proxy_personal.py"],
      "env": {
        "AGENT365_TOKEN_PATH": "C:/Users/jamesol/.agent365/personal-token.json"
      }
    }
  }
}
```

**Usage:**
```bash
# Generate work token
python get_agent365_token.py --output ~/.agent365/work-token.json

# Generate personal token
python get_agent365_token.py --output ~/.agent365/personal-token.json
```

## Token Security

### File Permissions

**Unix/Mac:**
```bash
chmod 600 ~/.agent365/auth-token.json
```

This ensures only your user can read/write the token file.

**Windows:**
```powershell
icacls "%USERPROFILE%\.agent365\auth-token.json" /inheritance:r /grant:r "%USERNAME%:F"
```

### Best Practices

1. **Never commit tokens to git:**
   ```bash
   echo ".agent365/" >> .gitignore
   ```

2. **Rotate tokens regularly:**
   ```bash
   # Refresh token every hour
   0 * * * * python get_agent365_token.py
   ```

3. **Use environment-specific tokens:**
   - Development: `~/.agent365/dev-token.json`
   - Staging: `~/.agent365/staging-token.json`
   - Production: `~/.agent365/prod-token.json`

4. **Store tokens in secure locations:**
   - Avoid network drives
   - Use encrypted filesystems
   - Consider secrets management tools (e.g., Azure Key Vault, HashiCorp Vault)

### Token Encryption (Advanced)

For extra security, encrypt tokens at rest:

```python
from cryptography.fernet import Fernet
import json
from pathlib import Path

# Generate encryption key (store this securely!)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt token
token_data = json.dumps({"access_token": "..."})
encrypted_token = cipher.encrypt(token_data.encode())

# Save encrypted token
Path("~/.agent365/auth-token.enc").write_bytes(encrypted_token)

# Decrypt when loading
encrypted_token = Path("~/.agent365/auth-token.enc").read_bytes()
token_data = json.loads(cipher.decrypt(encrypted_token))
```

## Token Lifecycle

### Token Expiration

Agent 365 tokens expire after **1 hour** (3600 seconds).

**Check token expiration:**
```python
import json
import time
from pathlib import Path

token_path = Path.home() / ".agent365" / "auth-token.json"
token = json.loads(token_path.read_text())

expires_at = token.get("expires_at", 0)
time_left = expires_at - time.time()

if time_left > 0:
    print(f"Token expires in {int(time_left / 60)} minutes")
else:
    print("Token expired!")
```

### Automatic Refresh

The proxy automatically handles expired tokens:

1. **Detection:** Checks `expires_at` before each API call
2. **Warning:** Logs warning if token expires in <5 minutes
3. **Error:** Returns `401 Unauthorized` if token expired
4. **Resolution:** User must run `get_agent365_token.py` to refresh

**Future enhancement:** Automatic token refresh using `refresh_token` field.

### Manual Refresh

Force token refresh:

```bash
# Delete old token
rm ~/.agent365/auth-token.json

# Generate new token
python get_agent365_token.py
```

## Troubleshooting

### Token File Not Found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\jamesol\\.agent365\\auth-token.json'
```

**Solution:**
```bash
# Verify token exists
ls ~/.agent365/auth-token.json

# If missing, generate new token
python get_agent365_token.py
```

### Invalid Token Format

**Error:**
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solution:**
```bash
# Check token file is valid JSON
cat ~/.agent365/auth-token.json | python -m json.tool

# If corrupted, regenerate
python get_agent365_token.py
```

### Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'C:\\Users\\jamesol\\.agent365\\auth-token.json'
```

**Solution (Windows):**
```powershell
icacls "%USERPROFILE%\.agent365\auth-token.json" /grant %USERNAME%:F
```

**Solution (Mac/Linux):**
```bash
chmod 600 ~/.agent365/auth-token.json
chown $USER ~/.agent365/auth-token.json
```

### Token Expired

**Error:**
```
401 Unauthorized: Token has expired
```

**Solution:**
```bash
python get_agent365_token.py
```

Then restart Claude Code to reload the token.

### Wrong Token Path

**Error:**
```
Token file not found at: /custom/path/token.json
```

**Solution:**

Verify the path in your Claude config matches the actual token location:

```bash
# Check configured path
cat ~/.config/Claude/claude_desktop_config.json | grep AGENT365_TOKEN_PATH

# Check actual token location
find ~ -name "auth-token.json"
```

Update config to use correct path.

## Advanced Scenarios

### CI/CD Integration

For automated testing, use service principal tokens:

```bash
# Set token via environment
export AGENT365_TOKEN_PATH=/secrets/agent365-token.json

# Or pass as command-line arg
python agent365_mcp_proxy.py --token /secrets/agent365-token.json
```

### Docker Deployment

Mount token as volume:

```dockerfile
FROM python:3.11-slim

COPY agent365_mcp_proxy.py /app/
WORKDIR /app

# Token mounted at runtime
ENV AGENT365_TOKEN_PATH=/secrets/auth-token.json

CMD ["python", "agent365_mcp_proxy.py"]
```

Run with mounted token:
```bash
docker run -v ~/.agent365:/secrets myproxy
```

### Kubernetes Deployment

Store token as secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: agent365-token
type: Opaque
data:
  auth-token.json: <base64-encoded-token>
```

Mount in pod:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: agent365-proxy
spec:
  containers:
  - name: proxy
    image: myproxy:latest
    env:
    - name: AGENT365_TOKEN_PATH
      value: /secrets/auth-token.json
    volumeMounts:
    - name: token
      mountPath: /secrets
      readOnly: true
  volumes:
  - name: token
    secret:
      secretName: agent365-token
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT365_TOKEN_PATH` | No | `~/.agent365/auth-token.json` | Path to token file |
| `AGENT365_API_BASE` | No | `https://api.agent365.com/v1` | Agent 365 API base URL |
| `AGENT365_TOKEN_REFRESH` | No | `false` | Enable automatic token refresh (future) |
| `AGENT365_LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Testing Token Configuration

### Test Script

```python
#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def test_token_config():
    # Get configured path
    token_path = os.getenv("AGENT365_TOKEN_PATH")
    if not token_path:
        token_path = Path.home() / ".agent365" / "auth-token.json"

    print(f"Token path: {token_path}")

    # Check file exists
    if not Path(token_path).exists():
        print("❌ Token file not found")
        sys.exit(1)

    print("✅ Token file exists")

    # Check readable
    try:
        with open(token_path) as f:
            token = json.load(f)
    except Exception as e:
        print(f"❌ Cannot read token: {e}")
        sys.exit(1)

    print("✅ Token file readable")

    # Check required fields
    required = ["access_token", "token_type", "expires_at"]
    for field in required:
        if field not in token:
            print(f"❌ Missing field: {field}")
            sys.exit(1)

    print("✅ Token has required fields")

    # Check expiration
    import time
    expires_at = token["expires_at"]
    time_left = expires_at - time.time()

    if time_left <= 0:
        print(f"⚠️  Token expired {int(-time_left / 60)} minutes ago")
    else:
        print(f"✅ Token valid for {int(time_left / 60)} minutes")

    print("\n🎉 Token configuration OK!")

if __name__ == "__main__":
    test_token_config()
```

**Usage:**
```bash
python test_token_config.py
```

## Summary

| Scenario | Token Path Configuration |
|----------|--------------------------|
| Default setup | Use `~/.agent365/auth-token.json` (automatic) |
| Custom location | Set `AGENT365_TOKEN_PATH` in Claude config |
| Multiple accounts | Use separate token files with different env vars |
| CI/CD | Mount token as volume/secret |
| Security | chmod 600, encrypt at rest, rotate regularly |

## See Also

- **SETUP.md** - Full installation guide
- **TROUBLESHOOTING.md** - Common issues and solutions
- **Agent 365 Auth Docs** - https://docs.agent365.com/auth
