# Agent 365 Email Draft Plugin Troubleshooting Guide

## Quick Diagnostics

Run these commands to quickly identify issues:

```bash
# 1. Check Python version
python --version
# Expected: Python 3.8 or higher

# 2. Check MCP package installed
python -c "import mcp; print('MCP OK')"
# Expected: "MCP OK"

# 3. Check token exists
ls ~/.agent365/auth-token.json
# Expected: File path printed

# 4. Check token valid JSON
cat ~/.agent365/auth-token.json | python -m json.tool
# Expected: Formatted JSON output

# 5. Test proxy standalone
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python ~/agent365_mcp_proxy.py
# Expected: List of 3 tools
```

If any of these fail, see the relevant section below.

---

## Installation Issues

### Python Version Too Old

**Symptoms:**
```
SyntaxError: f-string expression part cannot include a backslash
```

**Cause:** Python < 3.8

**Solution:**
```bash
# Check version
python --version

# Install Python 3.11 (recommended)
# Windows: Download from python.org
# Mac: brew install python@3.11
# Linux: sudo apt install python3.11

# Update Claude config to use correct Python
# Edit claude_desktop_config.json:
"command": "python3.11"
```

### MCP Package Not Found

**Symptoms:**
```
ModuleNotFoundError: No module named 'mcp'
```

**Cause:** MCP package not installed in correct Python environment

**Solution:**
```bash
# Find which Python Claude uses
which python  # Mac/Linux
where python  # Windows

# Install in that environment
python -m pip install mcp requests

# Verify installation
python -c "import mcp; print(mcp.__version__)"
```

### Permission Denied During Installation

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/usr/local/lib/python3.11/site-packages'
```

**Solution:**
```bash
# Install in user directory
pip install --user mcp requests

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows
pip install mcp requests
```

---

## Configuration Issues

### Proxy Not Starting

**Symptoms:**
- Claude Code shows "MCP server error"
- `/email-draft` skill unavailable
- No logs in `~/.config/Claude/logs/`

**Diagnosis:**

1. **Check Claude config syntax:**
   ```bash
   cat ~/.config/Claude/claude_desktop_config.json | python -m json.tool
   ```
   Should output valid JSON. If error, fix JSON syntax.

2. **Check proxy path exists:**
   ```bash
   ls ~/agent365_mcp_proxy.py
   ```
   If missing, copy proxy file to home directory.

3. **Check Python executable:**
   ```bash
   which python  # Mac/Linux
   where python  # Windows
   ```
   Update config to match this path.

4. **Test proxy manually:**
   ```bash
   python ~/agent365_mcp_proxy.py
   ```
   Should start and wait for stdin. Press Ctrl+C to exit.

**Common Fixes:**

**Wrong Python path:**
```json
{
  "mcpServers": {
    "agent365-proxy": {
      "command": "python3",  // Try "python3" or full path
      "args": ["C:/Users/jamesol/agent365_mcp_proxy.py"]
    }
  }
}
```

**Wrong proxy path:**
```bash
# Find proxy location
find ~ -name "agent365_mcp_proxy.py"

# Update config with correct path
"args": ["C:/Users/jamesol/agent365_mcp_proxy.py"]
```

**Missing environment variables:**
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

### Claude Config Not Found

**Symptoms:**
- Cannot find `claude_desktop_config.json`
- Config changes not taking effect

**Solution:**

**Windows:**
```bash
# Config should be at:
%APPDATA%\Claude\claude_desktop_config.json

# If missing, create it:
mkdir "%APPDATA%\Claude"
type nul > "%APPDATA%\Claude\claude_desktop_config.json"
```

**Mac:**
```bash
# Config should be at:
~/Library/Application Support/Claude/claude_desktop_config.json

# If missing, create it:
mkdir -p ~/Library/Application\ Support/Claude
touch ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Linux:**
```bash
# Config should be at:
~/.config/Claude/claude_desktop_config.json

# If missing, create it:
mkdir -p ~/.config/Claude
touch ~/.config/Claude/claude_desktop_config.json
```

### Config Changes Not Taking Effect

**Symptoms:**
- Updated config but proxy still not loading
- Old settings still active

**Solution:**

1. **Restart Claude Code completely:**
   - Close all Claude windows
   - Kill any remaining processes:
     ```bash
     # Mac/Linux
     killall Claude

     # Windows
     taskkill /IM Claude.exe /F
     ```
   - Reopen Claude Code

2. **Verify config location:**
   ```bash
   # Check you're editing the right file
   # Mac/Linux
   ls -l ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Windows
   dir %APPDATA%\Claude\claude_desktop_config.json
   ```

3. **Check config syntax:**
   ```bash
   python -m json.tool < ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
   Invalid JSON will cause config to be ignored.

---

## Authentication Issues

### Token File Not Found

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: '~/.agent365/auth-token.json'
```

**Solution:**

1. **Generate token:**
   ```bash
   python get_agent365_token.py
   ```

2. **Verify token created:**
   ```bash
   ls -l ~/.agent365/auth-token.json
   ```

3. **Check path in config matches:**
   ```bash
   # Check configured path
   grep AGENT365_TOKEN_PATH ~/.config/Claude/claude_desktop_config.json

   # Should match actual token location
   ```

### Token Expired

**Symptoms:**
```
401 Unauthorized: Token has expired
```

**Solution:**

Agent 365 tokens expire after 1 hour. Refresh token:

```bash
# Generate new token
python get_agent365_token.py

# Verify token created
cat ~/.agent365/auth-token.json

# Restart Claude Code
```

**Prevent this:** Set up auto-refresh cron job:

```bash
# Mac/Linux - edit crontab
crontab -e

# Add this line to refresh token every 50 minutes
*/50 * * * * cd /path/to/workiq && python get_agent365_token.py

# Windows - create scheduled task
schtasks /create /tn "Agent365TokenRefresh" /tr "python C:\path\to\get_agent365_token.py" /sc minute /mo 50
```

### Invalid Token Format

**Symptoms:**
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solution:**

1. **Check token file:**
   ```bash
   cat ~/.agent365/auth-token.json
   ```

2. **If corrupted, regenerate:**
   ```bash
   rm ~/.agent365/auth-token.json
   python get_agent365_token.py
   ```

3. **Verify token structure:**
   ```bash
   python -c "import json; token = json.load(open('~/.agent365/auth-token.json')); print('Valid token' if 'access_token' in token else 'Invalid token')"
   ```

### Authentication Loop

**Symptoms:**
- `get_agent365_token.py` opens browser repeatedly
- Never completes authentication

**Solution:**

1. **Check firewall/antivirus:**
   - Allow Python to accept incoming connections
   - Temporarily disable to test

2. **Check port 8080 available:**
   ```bash
   # Mac/Linux
   lsof -i :8080

   # Windows
   netstat -ano | findstr :8080
   ```
   If in use, update `get_agent365_token.py` to use different port.

3. **Try manual authentication:**
   ```bash
   # Copy auth URL from script output
   # Open in browser manually
   # Copy code from redirect URL
   # Paste when prompted
   ```

---

## Runtime Issues

### Proxy Crashes on Startup

**Symptoms:**
- Proxy starts then immediately exits
- No tools available in Claude

**Diagnosis:**

1. **Check proxy logs:**
   ```bash
   # Mac/Linux
   tail -f ~/.config/Claude/logs/agent365-proxy.log

   # Windows
   type %APPDATA%\Claude\logs\agent365-proxy.log
   ```

2. **Run proxy with debug output:**
   ```bash
   AGENT365_LOG_LEVEL=DEBUG python ~/agent365_mcp_proxy.py
   ```

**Common Causes:**

**Missing dependencies:**
```bash
pip install mcp requests
```

**Python version too old:**
```bash
python --version  # Must be 3.8+
```

**Import errors:**
```bash
python -c "import mcp, requests, json, sys; print('All imports OK')"
```

### Tools Not Appearing

**Symptoms:**
- Proxy starts successfully
- `/email-draft` skill not available
- No tools when running `/tools list`

**Solution:**

1. **Verify proxy loaded:**
   ```bash
   # Check Claude logs
   grep agent365 ~/.config/Claude/logs/*.log
   ```

2. **Test tools/list:**
   ```bash
   echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python ~/agent365_mcp_proxy.py
   ```
   Should output 3 tools: `search_messages`, `get_message`, `create_draft`

3. **Check skill installed:**
   ```bash
   ls ~/.claude/skills/email-draft/skill.md
   ```

4. **Restart Claude Code:**
   - Close completely
   - Reopen
   - Wait 10 seconds for MCP servers to initialize

### Proxy Hangs/Freezes

**Symptoms:**
- Proxy process running but not responding
- Claude shows "waiting for response..."
- Timeout after 30+ seconds

**Solution:**

1. **Kill stuck process:**
   ```bash
   # Mac/Linux
   ps aux | grep agent365_mcp_proxy
   kill -9 <PID>

   # Windows
   tasklist | findstr agent365
   taskkill /PID <PID> /F
   ```

2. **Check network connectivity:**
   ```bash
   ping api.agent365.com
   curl https://api.agent365.com/v1/health
   ```

3. **Check token not expired:**
   ```bash
   python -c "import json, time; token = json.load(open('~/.agent365/auth-token.json')); print('Valid' if token['expires_at'] > time.time() else 'Expired')"
   ```

4. **Restart Claude Code**

---

## API Call Issues

### No Emails Returned

**Symptoms:**
- Search returns empty results
- "No messages found" error

**Diagnosis:**

1. **Test directly with Agent 365:**
   ```bash
   curl https://api.agent365.com/v1/mail/searchMessages \
     -H "Authorization: Bearer $(python -c 'import json; print(json.load(open("~/.agent365/auth-token.json"))["access_token"])')" \
     -H "Content-Type: application/json" \
     -d '{"query": "recent"}'
   ```

2. **Check account has email access:**
   - Log into Agent 365 web interface
   - Verify emails are synced
   - Check permissions

**Solutions:**

**Broaden search query:**
```bash
# Instead of specific query
> /email-draft --search "from:sarah@example.com unread subject:budget"

# Try simpler query
> /email-draft --search "recent"
```

**Check search syntax:**
```bash
# Valid queries
"recent"              # Last 30 days
"unread"              # Unread only
"from:email@example.com"  # Specific sender
"subject:keyword"     # Subject contains
"has:attachment"      # Has attachments
```

### Message Not Found

**Symptoms:**
```
404 Not Found: Message ID does not exist
```

**Solution:**

1. **Verify message ID format:**
   ```bash
   # Should start with AAMkAGE...
   # Example: AAMkAGEwMDEwOTkwLTUzNGYtNGM...
   ```

2. **Search for message first:**
   ```bash
   > /email-draft --search "from:sender@example.com"
   # Copy ID from results
   > /email-draft --get "AAMkAGE..."
   ```

3. **Check message not deleted:**
   - Verify message still exists in Outlook
   - Deleted messages return 404

### Draft Creation Fails

**Symptoms:**
```
Failed to create draft: 403 Forbidden
```

**Solution:**

1. **Check write permissions:**
   - Verify Agent 365 has Outlook write access
   - Check account permissions in Agent 365 admin

2. **Verify draft format:**
   ```bash
   # Minimal draft (works)
   > /email-draft --draft "to:test@example.com,subject:Test,body:Test message"

   # With multiple recipients
   > /email-draft --draft "to:user1@example.com;user2@example.com,subject:Test"
   ```

3. **Check recipient addresses valid:**
   ```bash
   # Invalid addresses cause 400 Bad Request
   "to:invalid-email"  # ❌
   "to:user@example.com"  # ✅
   ```

### Rate Limiting

**Symptoms:**
```
429 Too Many Requests: Rate limit exceeded
```

**Solution:**

Wait 60 seconds before retrying. Agent 365 rate limits:
- 60 requests per minute per user
- 1000 requests per hour per user

**Prevent this:**
- Batch operations when possible
- Add delays between requests
- Cache results locally

---

## Performance Issues

### Slow Response Times

**Symptoms:**
- Requests take 10-30 seconds
- Frequent timeouts

**Diagnosis:**

1. **Check network latency:**
   ```bash
   ping api.agent365.com
   # Should be <100ms
   ```

2. **Check Agent 365 status:**
   - Visit status.agent365.com
   - Check for outages/incidents

3. **Test proxy overhead:**
   ```bash
   time echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python ~/agent365_mcp_proxy.py
   # Should be <2 seconds
   ```

**Solutions:**

**Use specific searches:**
```bash
# Slow - searches all mail
"budget"

# Fast - searches recent mail only
"recent budget"

# Faster - searches specific sender
"from:sarah@example.com budget"
```

**Reduce result count:**
```bash
# Returns 50+ emails (slow)
"recent"

# Returns 10 emails (fast)
"recent" --limit 10
```

### Memory Leaks

**Symptoms:**
- Proxy memory usage grows over time
- System slowdown
- Proxy crashes after many requests

**Solution:**

1. **Restart proxy:**
   - Close Claude Code
   - Kill proxy process
   - Reopen Claude Code

2. **Check for updates:**
   ```bash
   pip install --upgrade mcp requests
   ```

3. **Monitor memory:**
   ```bash
   # Mac/Linux
   ps aux | grep agent365_mcp_proxy

   # Windows
   tasklist | findstr agent365
   ```

---

## Logging and Debugging

### Enable Debug Logging

Add to Claude config:

```json
{
  "mcpServers": {
    "agent365-proxy": {
      "env": {
        "AGENT365_TOKEN_PATH": "C:/Users/jamesol/.agent365/auth-token.json",
        "AGENT365_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

Restart Claude Code, then check logs:

```bash
# Mac/Linux
tail -f ~/.config/Claude/logs/agent365-proxy.log

# Windows
type %APPDATA%\Claude\logs\agent365-proxy.log
```

### View Request/Response

Add verbose logging to proxy:

```python
# In agent365_mcp_proxy.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Logs will show
# DEBUG: Request: {"method": "tools/call", ...}
# DEBUG: Response: {"result": {...}}
```

### Test Tools Manually

```bash
# List tools
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python ~/agent365_mcp_proxy.py

# Search messages
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"search_messages","arguments":{"query":"recent"}},"id":2}' | python ~/agent365_mcp_proxy.py

# Get message
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_message","arguments":{"message_id":"AAMkAGE..."}},"id":3}' | python ~/agent365_mcp_proxy.py

# Create draft
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"create_draft","arguments":{"to":"test@example.com","subject":"Test","body":"Test message"}},"id":4}' | python ~/agent365_mcp_proxy.py
```

---

## Error Codes Reference

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check request format, valid JSON |
| 401 | Unauthorized | Token expired, run `get_agent365_token.py` |
| 403 | Forbidden | Insufficient permissions, check Agent 365 access |
| 404 | Not Found | Message ID invalid or deleted |
| 429 | Rate Limited | Wait 60 seconds, reduce request rate |
| 500 | Server Error | Agent 365 issue, check status.agent365.com |
| 502 | Bad Gateway | Network issue, check connectivity |
| 503 | Service Unavailable | Agent 365 maintenance, try later |
| 504 | Gateway Timeout | Slow response, retry request |

---

## Platform-Specific Issues

### Windows

**Path separators:**
```json
// Use forward slashes, not backslashes
"args": ["C:/Users/jamesol/agent365_mcp_proxy.py"]  // ✅
"args": ["C:\\Users\\jamesol\\agent365_mcp_proxy.py"]  // ❌
```

**Python not in PATH:**
```bash
# Find Python location
where python

# Use full path in config
"command": "C:/Users/jamesol/AppData/Local/Programs/Python/Python311/python.exe"
```

**Permission errors:**
```bash
# Run as administrator
icacls "%USERPROFILE%\.agent365" /grant %USERNAME%:F
```

### Mac

**Python 2 vs 3:**
```bash
# Mac ships with Python 2.7
python --version  # Python 2.7

# Use Python 3
python3 --version  # Python 3.x

# Update config
"command": "python3"
```

**Config location:**
```bash
# Note: "Application Support" has a space
~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Gatekeeper blocks proxy:**
```bash
# If "cannot verify developer"
xattr -d com.apple.quarantine ~/agent365_mcp_proxy.py
```

### Linux

**Python not installed:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Fedora/RHEL
sudo dnf install python3 python3-pip
```

**SELinux blocks proxy:**
```bash
# Temporarily disable
sudo setenforce 0

# Or add exception
sudo chcon -t bin_t ~/agent365_mcp_proxy.py
```

---

## Getting Help

### Collect Diagnostic Info

Before reporting issues, collect:

1. **System info:**
   ```bash
   python --version
   pip list | grep mcp
   uname -a  # Mac/Linux
   systeminfo  # Windows
   ```

2. **Config:**
   ```bash
   cat ~/.config/Claude/claude_desktop_config.json
   ```

3. **Logs:**
   ```bash
   tail -100 ~/.config/Claude/logs/agent365-proxy.log
   ```

4. **Token status:**
   ```bash
   python -c "import json, time; token = json.load(open('~/.agent365/auth-token.json')); print('Expires in', int((token['expires_at'] - time.time()) / 60), 'minutes')"
   ```

### Test Checklist

Run through this checklist:

- [ ] Python 3.8+ installed
- [ ] MCP package installed (`python -c "import mcp"`)
- [ ] Token file exists (`ls ~/.agent365/auth-token.json`)
- [ ] Token not expired (check `expires_at`)
- [ ] Config file valid JSON
- [ ] Proxy path correct in config
- [ ] Token path correct in config
- [ ] Skill installed (`ls ~/.claude/skills/email-draft`)
- [ ] Claude Code restarted
- [ ] Proxy starts manually (`python ~/agent365_mcp_proxy.py`)
- [ ] Network connectivity (`ping api.agent365.com`)

### Contact Support

If issues persist:

1. **Include diagnostic info** (see above)
2. **Describe steps to reproduce**
3. **Include error messages**
4. **Note when issue started**

**Support channels:**
- GitHub Issues: https://github.com/agent365/mcp-proxy/issues
- Email: support@agent365.com
- Slack: agent365.slack.com

---

## Common Workflows

### Fresh Install Test

```bash
# 1. Generate token
python get_agent365_token.py

# 2. Verify token
cat ~/.agent365/auth-token.json | python -m json.tool

# 3. Install dependencies
pip install mcp requests

# 4. Copy proxy
cp agent365_mcp_proxy.py ~/

# 5. Test proxy standalone
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python ~/agent365_mcp_proxy.py

# 6. Configure Claude (edit claude_desktop_config.json)

# 7. Install skill
mkdir -p ~/.claude/skills/email-draft
cp skill.md ~/.claude/skills/email-draft/

# 8. Restart Claude

# 9. Test skill
claude-code
> /email-draft --search "recent"
```

### Daily Maintenance

```bash
# Refresh token (do this every hour)
python get_agent365_token.py

# Check proxy status
ps aux | grep agent365_mcp_proxy

# View recent logs
tail -20 ~/.config/Claude/logs/agent365-proxy.log

# Test connectivity
curl https://api.agent365.com/v1/health
```

### Troubleshooting Flow

```
Issue?
├─ Proxy not starting?
│  ├─ Check Python version
│  ├─ Check dependencies installed
│  └─ Check config syntax
│
├─ Tools not appearing?
│  ├─ Check proxy loaded (logs)
│  ├─ Check skill installed
│  └─ Restart Claude
│
├─ Authentication error?
│  ├─ Check token exists
│  ├─ Check token not expired
│  └─ Regenerate token
│
├─ No results returned?
│  ├─ Check search query
│  ├─ Check network connectivity
│  └─ Check Agent 365 status
│
└─ Slow/timeout?
   ├─ Check network latency
   ├─ Use specific searches
   └─ Check Agent 365 status
```

---

## Prevention Tips

### Avoid Common Mistakes

1. **Use forward slashes in paths** (even on Windows)
2. **Refresh token every hour** (set up automation)
3. **Restart Claude after config changes**
4. **Test proxy standalone before using in Claude**
5. **Use specific search queries** (not "everything")
6. **Check logs when things break** (don't guess)
7. **Keep dependencies updated** (`pip install --upgrade`)

### Monitoring

Set up monitoring to catch issues early:

```bash
# Check token expiration daily
0 9 * * * python ~/check_token_expiry.py

# Test proxy health hourly
0 * * * * echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python ~/agent365_mcp_proxy.py > /dev/null || echo "Proxy down!" | mail -s "Alert" admin@example.com

# Clean old logs weekly
0 0 * * 0 find ~/.config/Claude/logs -mtime +7 -delete
```

---

## See Also

- **SETUP.md** - Installation guide
- **TOKEN_CONFIGURATION.md** - Token path setup
- **Agent 365 Docs** - https://docs.agent365.com
- **MCP Protocol** - https://modelcontextprotocol.io
