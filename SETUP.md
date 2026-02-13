# Agent 365 Email Draft Plugin Setup

## Overview

This guide walks you through setting up the Agent 365 Email Draft Plugin for Claude Code. The plugin enables Claude to search your emails, analyze threads, and generate draft replies using your personal writing style.

## Prerequisites

- Python 3.8 or higher
- Claude Code CLI installed
- Agent 365 account with email access
- Network connectivity to Agent 365 API

## Installation Steps

### 1. Get Agent 365 Token

First, authenticate with Agent 365 to obtain an access token:

```bash
python get_agent365_token.py
```

This will:
- Open your browser for authentication
- Save the token to `~/.agent365/auth-token.json`
- Token is valid for 1 hour

**Expected output:**
```
Token saved to: C:/Users/<username>/.agent365/auth-token.json
```

### 2. Install Python Dependencies

Install the required Python packages:

```bash
pip install mcp requests
```

**Required packages:**
- `mcp` - Model Context Protocol SDK
- `requests` - HTTP client for Agent 365 API

### 3. Copy MCP Proxy

Copy the MCP proxy script to your home directory:

**Windows:**
```bash
copy agent365_mcp_proxy.py %USERPROFILE%\agent365_mcp_proxy.py
```

**Mac/Linux:**
```bash
cp agent365_mcp_proxy.py ~/agent365_mcp_proxy.py
```

### 4. Configure Claude Code

Add the Agent 365 proxy to your Claude Code configuration:

#### 4.1 Locate Config File

Find your `claude_desktop_config.json` file:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

#### 4.2 Edit Config File

Open the config file and add the `agent365-proxy` server:

```json
{
  "mcpServers": {
    "agent365-proxy": {
      "command": "python",
      "args": [
        "C:/Users/<username>/agent365_mcp_proxy.py"
      ],
      "env": {
        "AGENT365_TOKEN_PATH": "C:/Users/<username>/.agent365/auth-token.json"
      }
    }
  }
}
```

**Important:** Replace `<username>` with your actual username!

#### 4.3 Path Configuration

Update the paths to match your system:

**Windows example:**
```json
"args": ["C:/Users/jamesol/agent365_mcp_proxy.py"],
"AGENT365_TOKEN_PATH": "C:/Users/jamesol/.agent365/auth-token.json"
```

**Mac/Linux example:**
```json
"args": ["/Users/jamesol/agent365_mcp_proxy.py"],
"AGENT365_TOKEN_PATH": "/Users/jamesol/.agent365/auth-token.json"
```

### 5. Copy Skill

Install the email-draft skill for Claude Code:

**Windows:**
```bash
mkdir "%USERPROFILE%\.claude\skills\email-draft"
copy skill.md "%USERPROFILE%\.claude\skills\email-draft\"
```

**Mac/Linux:**
```bash
mkdir -p ~/.claude/skills/email-draft
cp skill.md ~/.claude/skills/email-draft/
```

### 6. Restart Claude Code

Close and reopen Claude Code CLI to load the new configuration.

**Verify the proxy is loaded:**
```bash
claude-code
> /help
```

You should see `email-draft` listed in available skills.

## Testing

### Test 1: Search Messages

Search for recent unread emails:

```bash
claude-code
> /email-draft --search "recent unread"
```

**Expected output:**
- List of 5-10 unread emails
- Email subjects, senders, dates
- No errors

### Test 2: Get Message Details

Retrieve a specific email by ID:

```bash
> /email-draft --get "AAMkAGEwMDEw..."
```

**Expected output:**
- Full email content
- Thread information
- Metadata (sender, recipients, date)

### Test 3: Create Draft

Generate a draft reply:

```bash
> /email-draft --draft "reply to Sarah's question about Q4 budget"
```

**Expected output:**
- Draft created in Outlook Drafts folder
- Success message with draft ID
- Preview of generated content

## Troubleshooting

### Proxy Not Starting

**Symptoms:**
- Claude Code shows "MCP server error"
- `/email-draft` skill not available

**Solutions:**

1. **Check Python path:**
   ```bash
   python --version
   ```
   Should be 3.8+. If not found, update config to use `python3`:
   ```json
   "command": "python3"
   ```

2. **Verify token file exists:**
   ```bash
   ls ~/.agent365/auth-token.json
   ```
   If missing, re-run `python get_agent365_token.py`

3. **Check proxy logs:**

   **Windows:**
   ```bash
   type %APPDATA%\Claude\logs\agent365-proxy.log
   ```

   **Mac/Linux:**
   ```bash
   tail -f ~/.config/Claude/logs/agent365-proxy.log
   ```

4. **Test proxy standalone:**
   ```bash
   echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python ~/agent365_mcp_proxy.py
   ```
   Should output list of 3 tools.

### Token Expired

**Symptoms:**
- "401 Unauthorized" errors
- "Token expired" messages

**Solution:**

Agent 365 tokens expire after 1 hour. Refresh the token:

```bash
python get_agent365_token.py
```

Then restart Claude Code to reload the token.

**Pro tip:** Set up a cron job (Mac/Linux) or scheduled task (Windows) to refresh tokens automatically every 50 minutes.

### No Emails Returned

**Symptoms:**
- Search returns empty results
- "No messages found" errors

**Solutions:**

1. **Verify email access:**
   - Log into Agent 365 web interface
   - Check that email data is synced
   - Ensure account has proper permissions

2. **Check network connectivity:**
   ```bash
   ping api.agent365.com
   ```

3. **Try broader search:**
   Instead of: `"recent unread from Sarah"`
   Try: `"recent"`

4. **Check search syntax:**
   Valid search queries:
   - `"recent"` - Last 30 days
   - `"unread"` - Unread messages
   - `"from:sarah@example.com"` - Specific sender
   - `"subject:budget"` - Subject contains keyword

### Draft Creation Fails

**Symptoms:**
- "Failed to create draft" errors
- Draft not appearing in Outlook

**Solutions:**

1. **Verify draft permissions:**
   - Ensure Agent 365 has Outlook write access
   - Check if drafts folder exists

2. **Check email format:**
   - Draft requires valid email addresses in `to` field
   - Subject and body are optional but recommended

3. **Test with minimal draft:**
   ```bash
   > /email-draft --draft "to:test@example.com,subject:Test,body:Test message"
   ```

### Permission Errors

**Symptoms:**
- "Access denied" when starting proxy
- "Permission denied" for token file

**Solutions:**

**Windows:**
```bash
icacls "%USERPROFILE%\.agent365\auth-token.json" /grant %USERNAME%:F
```

**Mac/Linux:**
```bash
chmod 600 ~/.agent365/auth-token.json
chown $USER ~/.agent365/auth-token.json
```

### MCP Package Not Found

**Symptoms:**
- `ModuleNotFoundError: No module named 'mcp'`

**Solution:**

Ensure you're using the correct Python environment:

```bash
# Check which Python Claude Code is using
which python

# Install mcp in that environment
python -m pip install mcp requests

# If using virtual environment
source venv/bin/activate
pip install mcp requests
```

## Advanced Configuration

### Custom Token Location

To use a different token location, update the config:

```json
{
  "mcpServers": {
    "agent365-proxy": {
      "env": {
        "AGENT365_TOKEN_PATH": "/custom/path/to/token.json"
      }
    }
  }
}
```

### Multiple Agent 365 Accounts

To use multiple accounts, create separate proxy instances:

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

### Logging Configuration

Enable debug logging by setting environment variable:

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

## Security Notes

### Token Security

- **Never commit tokens to git** - Add `.agent365/` to `.gitignore`
- **Tokens expire after 1 hour** - Refresh regularly
- **Keep tokens private** - Only readable by your user (chmod 600)

### Network Security

- All communication uses HTTPS
- Tokens transmitted via Authorization header
- No email content cached locally

## Getting Help

### Check System Status

1. **Proxy status:**
   ```bash
   ps aux | grep agent365_mcp_proxy
   ```

2. **Claude Code logs:**
   Check `~/.config/Claude/logs/` for errors

3. **Test token validity:**
   ```bash
   python -c "import json; print(json.load(open('~/.agent365/auth-token.json')))"
   ```

### Common Error Codes

| Error | Meaning | Solution |
|-------|---------|----------|
| 401 | Token expired | Re-run `get_agent365_token.py` |
| 403 | Insufficient permissions | Check Agent 365 account settings |
| 404 | Message not found | Verify message ID is correct |
| 429 | Rate limited | Wait 60 seconds and retry |
| 500 | Agent 365 server error | Check status.agent365.com |

### Contact Support

If issues persist:
1. Collect logs from `~/.config/Claude/logs/agent365-proxy.log`
2. Note the error message and timestamp
3. Contact support with reproduction steps

## Uninstall

To remove the plugin:

1. **Remove from Claude config:**
   Delete the `agent365-proxy` section from `claude_desktop_config.json`

2. **Remove proxy script:**
   ```bash
   rm ~/agent365_mcp_proxy.py
   ```

3. **Remove skill:**
   ```bash
   rm -rf ~/.claude/skills/email-draft
   ```

4. **Remove token (optional):**
   ```bash
   rm -rf ~/.agent365
   ```

5. **Restart Claude Code**

## Next Steps

Once setup is complete:

1. **Explore the skill:**
   ```bash
   > /email-draft --help
   ```

2. **Try example workflows:**
   - Search for important emails
   - Analyze long email threads
   - Generate draft replies

3. **Customize style profiles:**
   Edit `~/.claude/skills/email-draft/skill.md` to add your writing style

4. **Integrate with workflows:**
   Combine with other Claude skills for powerful automation

## Resources

- **Agent 365 Documentation:** https://docs.agent365.com
- **MCP Protocol Spec:** https://modelcontextprotocol.io
- **Claude Code Skills:** https://claude.ai/code/skills

## Appendix: File Locations

### Windows

| File | Location |
|------|----------|
| Config | `%APPDATA%\Claude\claude_desktop_config.json` |
| Token | `%USERPROFILE%\.agent365\auth-token.json` |
| Proxy | `%USERPROFILE%\agent365_mcp_proxy.py` |
| Skill | `%USERPROFILE%\.claude\skills\email-draft\skill.md` |
| Logs | `%APPDATA%\Claude\logs\agent365-proxy.log` |

### Mac

| File | Location |
|------|----------|
| Config | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Token | `~/.agent365/auth-token.json` |
| Proxy | `~/agent365_mcp_proxy.py` |
| Skill | `~/.claude/skills/email-draft/skill.md` |
| Logs | `~/Library/Logs/Claude/agent365-proxy.log` |

### Linux

| File | Location |
|------|----------|
| Config | `~/.config/Claude/claude_desktop_config.json` |
| Token | `~/.agent365/auth-token.json` |
| Proxy | `~/agent365_mcp_proxy.py` |
| Skill | `~/.claude/skills/email-draft/skill.md` |
| Logs | `~/.config/Claude/logs/agent365-proxy.log` |
