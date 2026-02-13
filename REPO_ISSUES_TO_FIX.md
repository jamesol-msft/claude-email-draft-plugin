# Repository Issues to Fix

## Testing Status: ❌ Does Not Work As-Is

Attempted to use the skill with: `/email-draft show me unread messages`

**Result**: MCP tools not available
```
Error: No such tool available: mcp__agent365_proxy__search_messages
```

---

## Critical Issues Blocking "Works As-Is" Status

### Issue 1: Missing Token Generation Script ⚠️ CRITICAL

**Problem**: `get_agent365_token.py` is referenced throughout documentation but **not included in repository**.

**References**:
- `README.md` line 20-22: "Use the Agent 365 CLI to authenticate"
- `SETUP.md` line 17-27: "python get_agent365_token.py"
- `TOKEN_CONFIGURATION.md` line 82-95: Detailed usage of this script

**Impact**:
- Users cannot generate authentication tokens
- Setup cannot be completed without this file
- Repository is not self-contained

**Required Fix**:
1. **Option A**: Add `get_agent365_token.py` to repository
2. **Option B**: Document exact steps to obtain this file from Agent 365
3. **Option C**: Create a stub/template version with clear instructions

**Recommended Action**: Add the token generation script to the repo, or if it's proprietary to Agent 365, update all documentation to clearly state:
- Where to get it (specific URL or command)
- Alternative authentication methods
- Mock token format for testing

---

### Issue 2: MCP Server Configuration Not Automated

**Problem**: User must manually edit `claude_desktop_config.json` after installation.

**Current Process**:
1. Install files
2. Manually find config file location (varies by OS)
3. Manually edit JSON
4. Manually update paths with correct username
5. Restart Claude Desktop

**Impact**:
- High friction for installation
- Easy to make mistakes (typos, wrong paths)
- Not "works as-is"

**Recommended Fix**:
Add a setup script: `setup.py` or `install.sh`/`install.bat`

**Example `setup.py`**:
```python
#!/usr/bin/env python3
"""
Setup script for Agent 365 Email Draft Plugin
"""
import json
import os
import platform
import shutil
from pathlib import Path

def get_claude_config_path():
    """Get Claude Desktop config path for current OS"""
    system = platform.system()
    if system == "Windows":
        return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

def main():
    print("🚀 Agent 365 Email Draft Plugin Setup\n")

    # 1. Copy MCP proxy
    home = Path.home()
    proxy_src = Path("agent365_mcp_proxy.py")
    proxy_dst = home / "agent365_mcp_proxy.py"

    print(f"📦 Copying MCP proxy to {proxy_dst}")
    shutil.copy(proxy_src, proxy_dst)
    print("   ✅ Done\n")

    # 2. Copy skill
    skill_src = Path("skills/email-draft/SKILL.md")
    skill_dst = home / ".claude" / "skills" / "email-draft" / "SKILL.md"

    print(f"📦 Copying skill to {skill_dst}")
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(skill_src, skill_dst)
    print("   ✅ Done\n")

    # 3. Configure Claude Desktop
    config_path = get_claude_config_path()
    print(f"⚙️  Configuring Claude Desktop: {config_path}")

    # Load existing config or create new
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        print("   📄 Existing config found")
    else:
        config = {}
        config_path.parent.mkdir(parents=True, exist_ok=True)
        print("   📄 Creating new config")

    # Add MCP server
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Use forward slashes for cross-platform compatibility
    proxy_path_str = str(proxy_dst).replace("\\", "/")
    token_path_str = str(home / ".agent365" / "auth-token.json").replace("\\", "/")

    config["mcpServers"]["agent365-proxy"] = {
        "command": "python",
        "args": [proxy_path_str],
        "env": {
            "AGENT365_TOKEN_PATH": token_path_str
        }
    }

    # Save config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print("   ✅ MCP server configured\n")

    # 4. Token setup instructions
    print("⚠️  IMPORTANT: Token Setup Required")
    print("=" * 60)
    print("The MCP server is configured, but you need an Agent 365 token.")
    print()
    print("If you have get_agent365_token.py:")
    print("  python get_agent365_token.py")
    print()
    print("Or create a mock token for testing:")
    print("  mkdir -p ~/.agent365")
    print("  cat > ~/.agent365/auth-token.json << 'EOF'")
    print("  {")
    print('    "access_token": "mock_token_for_testing",')
    print('    "token_type": "Bearer",')
    print('    "expires_in": 3600,')
    print('    "expires_at": 9999999999')
    print("  }")
    print("  EOF")
    print("=" * 60)
    print()

    print("✅ Setup complete!")
    print()
    print("Next steps:")
    print("  1. Generate Agent 365 token (see above)")
    print("  2. Restart Claude Desktop/CLI")
    print("  3. Test with: /email-draft show me unread messages")

if __name__ == "__main__":
    main()
```

**Benefits**:
- One command setup: `python setup.py`
- Cross-platform (Windows/Mac/Linux)
- Automatic path detection
- Safe config merging (preserves existing settings)
- Clear next steps

---

### Issue 3: Skill File Location Mismatch

**Problem**: Setup documentation references wrong skill file name.

**SETUP.md line 117**:
```bash
copy skill.md "%USERPROFILE%\.claude\skills\email-draft\"
```

**Actual file location**: `skills/email-draft/SKILL.md` (not `skill.md`)

**Impact**: Copy command fails, skill not installed

**Required Fix**: Update all references to use correct path:
```bash
copy skills\email-draft\SKILL.md "%USERPROFILE%\.claude\skills\email-draft\"
```

**Files to update**:
- `README.md`
- `SETUP.md`

---

### Issue 4: No Testing/Verification Script

**Problem**: No way to verify setup is correct before attempting to use.

**Current situation**:
- User installs files
- User configures manually
- User tries to use skill
- **Fails silently if MCP server not configured**
- User doesn't know what went wrong

**Recommended Fix**: Add `verify_setup.py`

**Example**:
```python
#!/usr/bin/env python3
"""
Verify Agent 365 Email Draft Plugin Setup
"""
import json
import sys
from pathlib import Path

def check_file(path, name):
    """Check if file exists"""
    if path.exists():
        print(f"✅ {name}: {path}")
        return True
    else:
        print(f"❌ {name} NOT FOUND: {path}")
        return False

def check_token(path):
    """Verify token file format"""
    if not path.exists():
        print(f"❌ Token file NOT FOUND: {path}")
        return False

    try:
        with open(path) as f:
            token = json.load(f)

        required = ["access_token", "token_type", "expires_at"]
        missing = [f for f in required if f not in token]

        if missing:
            print(f"❌ Token missing fields: {missing}")
            return False

        print(f"✅ Token file valid: {path}")
        return True
    except Exception as e:
        print(f"❌ Token file invalid: {e}")
        return False

def main():
    print("🔍 Verifying Agent 365 Email Draft Plugin Setup\n")

    checks = []

    # Check 1: MCP Proxy
    proxy_path = Path.home() / "agent365_mcp_proxy.py"
    checks.append(check_file(proxy_path, "MCP Proxy"))

    # Check 2: Skill File
    skill_path = Path.home() / ".claude" / "skills" / "email-draft" / "SKILL.md"
    checks.append(check_file(skill_path, "Skill File"))

    # Check 3: Token File
    token_path = Path.home() / ".agent365" / "auth-token.json"
    checks.append(check_token(token_path))

    # Check 4: Claude Config
    import platform
    import os
    if platform.system() == "Windows":
        config_path = Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    elif platform.system() == "Darwin":
        config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        config_path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)

            if "mcpServers" in config and "agent365-proxy" in config["mcpServers"]:
                print(f"✅ Claude Desktop configured with agent365-proxy")
                checks.append(True)
            else:
                print(f"❌ Claude Desktop config missing agent365-proxy server")
                checks.append(False)
        except Exception as e:
            print(f"❌ Claude Desktop config invalid: {e}")
            checks.append(False)
    else:
        print(f"❌ Claude Desktop config NOT FOUND: {config_path}")
        checks.append(False)

    # Summary
    print(f"\n{'=' * 60}")
    if all(checks):
        print("✅ All checks passed! Setup is complete.")
        print("\nNext step: Restart Claude Desktop/CLI")
    else:
        print(f"❌ Setup incomplete: {sum(checks)}/{len(checks)} checks passed")
        print("\nRun: python setup.py")
    print('=' * 60)

    sys.exit(0 if all(checks) else 1)

if __name__ == "__main__":
    main()
```

---

### Issue 5: No Mock Token for Testing

**Problem**: Cannot test plugin without real Agent 365 account.

**Impact**:
- Developers can't test locally
- CI/CD pipelines can't run tests
- Higher barrier to contribution

**Recommended Fix**: Add mock token support

**Add to `agent365_mcp_proxy.py`**:
```python
# Around line 50, add:
MOCK_MODE = os.environ.get("AGENT365_MOCK_MODE") == "true"

if MOCK_MODE:
    logger.warning("⚠️  MOCK MODE ENABLED - Using fake data for testing")
```

**Then in each MCP tool handler**:
```python
def search_messages(self, query: str, top: int = 10):
    if MOCK_MODE:
        return self._mock_search_messages(query, top)

    # Real implementation...

def _mock_search_messages(self, query: str, top: int):
    """Return mock email data for testing"""
    return [
        {
            "id": "AAMkAGI2T-MOCK-001",
            "from": {"name": "Charles Lamanna", "address": "charles.lamanna@microsoft.com"},
            "subject": "Q4 Budget Review - Mock Data",
            "receivedDateTime": "2025-02-10T15:30:00Z",
            "bodyPreview": "This is mock email data for testing..."
        },
        # ... more mock emails
    ]
```

**Usage**:
```bash
# Test without real token
AGENT365_MOCK_MODE=true python agent365_mcp_proxy.py
```

---

### Issue 6: Dependencies Not Specified

**Problem**: `requirements.txt` missing from repository.

**Current situation**:
- README says "pip install mcp requests"
- No version pinning
- No dependency tree documentation

**Recommended Fix**: Add `requirements.txt`

```txt
# requirements.txt
mcp>=1.26.0
requests>=2.32.0
```

**Also add `setup.py` for pip install**:
```python
from setuptools import setup, find_packages

setup(
    name="claude-email-draft-plugin",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.26.0",
        "requests>=2.32.0",
    ],
    entry_points={
        "console_scripts": [
            "agent365-proxy=agent365_mcp_proxy:main",
        ],
    },
)
```

**Installation becomes**:
```bash
pip install -e .
```

---

## Summary of Required Changes

### Must Have (Blocking "Works As-Is")

1. ✅ **Add `setup.py`** - Automated installation
2. ✅ **Add `get_agent365_token.py`** or document where to get it
3. ✅ **Fix skill file path** in documentation
4. ✅ **Add `requirements.txt`** for dependencies

### Should Have (Better UX)

5. ✅ **Add `verify_setup.py`** - Setup validation
6. ✅ **Add mock mode** to MCP proxy for testing

### Documentation Updates

7. ✅ Update README.md with simplified install: `python setup.py`
8. ✅ Add "Quick Start in 30 seconds" section
9. ✅ Update SETUP.md to reference setup script
10. ✅ Add TESTING.md with mock mode instructions

---

## Recommended Repository Structure

```
claude-email-draft-plugin/
├── agent365_mcp_proxy.py          # MCP server (add mock mode)
├── get_agent365_token.py          # NEW: Token generation script
├── setup.py                       # NEW: Automated setup
├── verify_setup.py                # NEW: Setup validation
├── requirements.txt               # NEW: Python dependencies
├── skills/
│   └── email-draft/
│       └── SKILL.md               # Skill definition
├── docs/
│   ├── README.md                  # Overview (update)
│   ├── SETUP.md                   # Installation (update)
│   ├── TESTING.md                 # NEW: Testing guide
│   ├── TROUBLESHOOTING.md
│   ├── TOKEN_CONFIGURATION.md
│   └── IMPLEMENTATION_COMPLETE.md
├── tests/                         # NEW: Test suite
│   ├── test_proxy.py
│   ├── test_search.py
│   └── test_mock_mode.py
├── .gitignore                     # Add .agent365/
├── LICENSE
└── claude_desktop_config.json     # Example config
```

---

## Testing Checklist

After fixes, verify "Works As-Is" status:

### Setup Test
- [ ] `python setup.py` completes without errors
- [ ] `python verify_setup.py` shows all checks passing
- [ ] MCP proxy file in home directory
- [ ] Skill file in `.claude/skills/email-draft/`
- [ ] Claude config updated with MCP server

### Mock Mode Test (No Token Required)
- [ ] `AGENT365_MOCK_MODE=true python agent365_mcp_proxy.py` starts
- [ ] `/email-draft show me unread messages` returns mock data
- [ ] Draft generation works with mock profile matching

### Real Token Test (With Agent 365 Account)
- [ ] `python get_agent365_token.py` generates token
- [ ] Token file created in `~/.agent365/auth-token.json`
- [ ] `/email-draft show me unread messages` returns real emails
- [ ] Draft creation works and appears in Outlook

---

## Priority for Push to Repo

### P0 (Critical - Blocks Usage)
1. Add `setup.py` or update docs with exact manual steps
2. Add/document `get_agent365_token.py`
3. Fix skill file path in all documentation

### P1 (Important - Poor UX Without)
4. Add `requirements.txt`
5. Add `verify_setup.py`

### P2 (Nice to Have)
6. Add mock mode to MCP proxy
7. Add test suite
8. Restructure documentation

---

## Immediate Action Items

1. **Determine token script availability**
   - Is `get_agent365_token.py` available from Agent 365?
   - Can it be included in this repo?
   - If not, what's the exact alternative?

2. **Create setup automation**
   - Implement `setup.py` as shown above
   - Test on Windows, Mac, Linux

3. **Update all documentation**
   - Fix skill file paths
   - Add setup script instructions
   - Add verification steps

4. **Test end-to-end**
   - Fresh clone
   - Run setup script
   - Verify skill works
   - Document any remaining issues

---

**Current Status**: ❌ Repository does not work "as-is" without manual configuration and missing files.

**Target Status**: ✅ Repository works "as-is" after running `python setup.py` and having an Agent 365 token (or mock mode enabled).
