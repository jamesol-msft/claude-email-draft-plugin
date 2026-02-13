# Local Setup Complete - Agent 365 Email Draft Plugin

## ✅ Setup Status

### Completed Steps

1. **Repository Cloned** ✓
   - Location: `C:\Users\jamesol\ClaudeCodePOCs\TODO\Auto-draft\claude-email-draft-plugin`
   - All files successfully downloaded from GitHub

2. **Python Dependencies Installed** ✓
   - Python version: 3.11.9 (requirement: 3.8+)
   - `mcp` package: v1.26.0 ✓
   - `requests` package: v2.32.4 ✓

3. **MCP Proxy Deployed** ✓
   - Source: `agent365_mcp_proxy.py`
   - Deployed to: `C:\Users\jamesol\agent365_mcp_proxy.py`
   - File size: 22,346 bytes

4. **Skill Installed** ✓
   - Source: `skills/email-draft/SKILL.md`
   - Deployed to: `C:\Users\jamesol\.claude\skills\email-draft\SKILL.md`
   - File size: 24,604 bytes
   - **Status: Skill is now available in Claude Code!** (confirmed in system)

### Files Deployed

| File | Location | Status |
|------|----------|--------|
| MCP Proxy | `~/agent365_mcp_proxy.py` | ✓ Ready |
| Skill Definition | `~/.claude/skills/email-draft/SKILL.md` | ✓ Active |

---

## ⚠️ Remaining Steps for Full Testing

### 1. Agent 365 Token Setup

The plugin requires an Agent 365 authentication token. The token setup script `get_agent365_token.py` is **not included** in this repository.

**You need to:**
- Obtain the `get_agent365_token.py` script from Agent 365
- Run it to authenticate and generate a token:
  ```bash
  python get_agent365_token.py
  ```
- This will create: `C:\Users\jamesol\.agent365\auth-token.json`

**Token details:**
- Valid for: 1 hour
- Format: JSON with JWT bearer token
- Location: `~/.agent365/auth-token.json`
- Security: Should be chmod 600 (user-only access)

### 2. Claude Desktop Configuration

To enable the MCP server, you need to configure Claude Desktop:

**Config file location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Recommended path: `C:\Users\jamesol\AppData\Roaming\Claude\claude_desktop_config.json`

**Add this configuration:**
```json
{
  "mcpServers": {
    "agent365-proxy": {
      "command": "python",
      "args": [
        "C:/Users/jamesol/agent365_mcp_proxy.py"
      ],
      "env": {
        "AGENT365_TOKEN_PATH": "C:/Users/jamesol/.agent365/auth-token.json"
      }
    }
  }
}
```

**After updating config:**
- Restart Claude Desktop/CLI to load the MCP server

---

## 🧪 Testing the Setup

### Quick Test: Verify Skill is Available

The skill is already loaded! You can verify by running:
```bash
/email-draft --help
```

### Test 1: Search Messages (requires token)

```bash
/email-draft --search "recent unread"
```

**Expected:**
- List of 5-10 unread emails
- Email subjects, senders, dates

**If fails:**
- Check token exists: `ls ~/.agent365/auth-token.json`
- Check token not expired (tokens last 1 hour)
- Verify MCP server is running in Claude Desktop config

### Test 2: Generate Draft Reply

```bash
/email-draft
```

Follow the interactive prompts to:
1. Search for an email
2. Select one from results
3. Review generated draft
4. Optionally publish to Outlook

---

## 📊 Architecture Overview

```
┌─────────────────┐
│  Claude Code    │  (You are here)
└────────┬────────┘
         │ MCP Protocol (JSON-RPC 2.0 over stdio)
         │
┌────────▼────────────────────────────────────┐
│  agent365_mcp_proxy.py                      │
│  - 3 tools: search, get, create_draft       │
│  - Token authentication                     │
│  - 90s timeout for long operations          │
└────────┬────────────────────────────────────┘
         │ HTTPS API calls
         │
┌────────▼──────────────────┐
│  Agent 365 Mail Server    │
│  agent365.svc.cloud...    │
└────────┬──────────────────┘
         │ Microsoft Graph API
         │
┌────────▼──────────────────┐
│  Microsoft 365 (Outlook)  │
│  Your email inbox         │
└───────────────────────────┘
```

---

## 🔍 What's Available Now

### Skill: /email-draft

**Description:**
Generate executive-style email drafts using real email context from your Microsoft 365 inbox.

**Usage modes:**

1. **Interactive** (recommended for first time):
   ```bash
   /email-draft
   ```

2. **Search first**:
   ```bash
   /email-draft --search "recent unread from john"
   ```

3. **Reply to specific email**:
   ```bash
   /email-draft --reply-to AAMkAGI2TGAA=
   ```

**Features:**
- Natural language email search
- Executive style profile matching (Charles Lamanna, Nirav Shah, Robert Bruckner, James Oleinik)
- Context-aware responses using full email threads
- One-click publishing to Outlook drafts

---

## 📚 Documentation Files

Available in the repository:

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start |
| `SETUP.md` | Detailed installation guide |
| `TROUBLESHOOTING.md` | Common issues and solutions |
| `TOKEN_CONFIGURATION.md` | Token management and security |
| `IMPLEMENTATION_COMPLETE.md` | Technical details |

---

## 🔧 Troubleshooting

### Issue: Skill not appearing

**Solution:** ✓ Already resolved! The skill is active in your Claude Code instance.

### Issue: "MCP server error" when using skill

**Cause:** MCP server not configured or token missing

**Solution:**
1. Add MCP server config to `claude_desktop_config.json` (see step 2 above)
2. Generate Agent 365 token: `python get_agent365_token.py`
3. Restart Claude Desktop/CLI

### Issue: "Token expired" (401 error)

**Cause:** Tokens expire after 1 hour

**Solution:**
```bash
python get_agent365_token.py
```
Then restart Claude Code to reload the token.

### Issue: Search returns no results

**Solutions:**
- Verify Agent 365 has access to your email
- Try broader search: just `"recent"` instead of complex queries
- Check network connectivity to Agent 365

---

## 🎯 Next Steps

### To start testing:

1. **Get Agent 365 token script**
   - Contact Agent 365 support or check their documentation
   - Run the script to generate your token

2. **Configure Claude Desktop**
   - Edit `claude_desktop_config.json` as shown above
   - Restart Claude Desktop/CLI

3. **Test the skill**
   - Run `/email-draft --help` to see options
   - Try searching for recent emails
   - Generate a test draft

### After successful testing:

- Customize executive style profiles in `SKILL.md`
- Set up automatic token refresh (see TOKEN_CONFIGURATION.md)
- Integrate with your email workflows

---

## 📦 Repository Information

- **Source:** https://github.com/jamesol-msft/claude-email-draft-plugin
- **License:** MIT
- **Version:** Production Ready (Wave 5)
- **Test Pass Rate:** 100% (35/35 scenarios)

---

## ✨ Summary

**What's working:**
- ✅ Repository cloned
- ✅ Python dependencies installed
- ✅ MCP proxy deployed to home directory
- ✅ Skill file installed and **active in Claude Code**

**What's needed for full functionality:**
- ⏳ Agent 365 authentication token
- ⏳ Claude Desktop MCP configuration
- ⏳ Claude Desktop restart

**Once you have the token and configure the MCP server, you're ready to use the plugin!**

For any issues, check `TROUBLESHOOTING.md` or the documentation files listed above.
