#!/usr/bin/env python3
"""
Setup script for Agent 365 Email Draft Plugin

Automates installation of:
- MCP proxy server
- Claude Code skill
- Claude Desktop configuration

Usage:
    python setup.py              # Interactive setup
    python setup.py --mock       # Setup with mock mode for testing
"""
import json
import os
import platform
import shutil
import sys
from pathlib import Path


def get_claude_config_path():
    """Get Claude Desktop config path for current OS"""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            print("[ERROR] APPDATA environment variable not found")
            sys.exit(1)
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def main():
    print("=" * 64)
    print()
    print("  Agent 365 Email Draft Plugin Setup")
    print()
    print("=" * 64)
    print()

    # Check if running with --mock flag
    mock_mode = "--mock" in sys.argv

    # 1. Copy MCP proxy
    home = Path.home()
    proxy_src = Path(__file__).parent / "agent365_mcp_proxy.py"

    if not proxy_src.exists():
        print(f"[ERROR] Error: agent365_mcp_proxy.py not found at {proxy_src}")
        sys.exit(1)

    proxy_dst = home / "agent365_mcp_proxy.py"

    print(f"[INSTALL] Step 1/3: Installing MCP Proxy")
    print(f"   Source: {proxy_src}")
    print(f"   Target: {proxy_dst}")

    try:
        shutil.copy(proxy_src, proxy_dst)
        print("   [OK] MCP proxy installed")
    except Exception as e:
        print(f"   [ERROR] Failed to copy proxy: {e}")
        sys.exit(1)

    print()

    # 2. Copy skill
    skill_src = Path(__file__).parent / "skills" / "email-draft" / "SKILL.md"

    if not skill_src.exists():
        print(f"[ERROR] Error: SKILL.md not found at {skill_src}")
        sys.exit(1)

    skill_dst = home / ".claude" / "skills" / "email-draft" / "SKILL.md"

    print(f"[INSTALL] Step 2/3: Installing Skill")
    print(f"   Source: {skill_src}")
    print(f"   Target: {skill_dst}")

    try:
        skill_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(skill_src, skill_dst)
        print("   [OK] Skill installed")
    except Exception as e:
        print(f"   [ERROR] Failed to copy skill: {e}")
        sys.exit(1)

    print()

    # 3. Configure Claude Desktop
    config_path = get_claude_config_path()
    print(f"[CONFIG]  Step 3/3: Configuring Claude Desktop")
    print(f"   Config: {config_path}")

    # Load existing config or create new
    config = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            print("   [FILE] Existing config found, will merge")
        except json.JSONDecodeError:
            print("   [WARN]  Existing config is invalid, creating new")
            config = {}
    else:
        print("   [FILE] Creating new config")
        config_path.parent.mkdir(parents=True, exist_ok=True)

    # Add MCP server
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Use forward slashes for cross-platform compatibility
    proxy_path_str = str(proxy_dst).replace("\\", "/")
    token_path_str = str(home / ".agent365" / "auth-token.json").replace("\\", "/")

    mcp_config = {
        "command": "python",
        "args": [proxy_path_str],
        "env": {
            "AGENT365_TOKEN_PATH": token_path_str
        }
    }

    # Add mock mode if requested
    if mock_mode:
        mcp_config["env"]["AGENT365_MOCK_MODE"] = "true"
        print("   [MOCK] Mock mode enabled")

    config["mcpServers"]["agent365-proxy"] = mcp_config

    # Save config
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print("   [OK] Claude Desktop configured")
    except Exception as e:
        print(f"   [ERROR] Failed to write config: {e}")
        sys.exit(1)

    print()

    # 4. Token setup instructions
    print("=" * 64)
    print("  Installation Complete!")
    print("=" * 64)
    print()

    if mock_mode:
        print("[MOCK MODE] No token needed, plugin will use fake data")
        print()
    else:
        print("[!] IMPORTANT: Token Setup Required")
        print("=" * 64)
        print("The MCP server is configured, but you need an Agent 365 token.")
        print()
        print("If you have get_agent365_token.py:")
        print("  python get_agent365_token.py")
        print()
        print("Or create a mock token for testing:")
        token_dir = home / ".agent365"
        token_file = token_dir / "auth-token.json"
        print(f"  mkdir -p {token_dir}")
        print(f"  cat > {token_file} << 'EOF'")
        print("  {")
        print('    "access_token": "mock_token_for_testing",')
        print('    "token_type": "Bearer",')
        print('    "expires_in": 3600,')
        print('    "expires_at": 9999999999')
        print("  }")
        print("  EOF")
        print("=" * 64)
        print()

    print("[NEXT] Next steps:")
    print("  1. Generate Agent 365 token (see above) OR use mock mode")
    print("  2. Restart Claude Desktop/CLI to load the MCP server")
    print("  3. Test with: /email-draft show me unread messages")
    print()
    print("[TIP] Run 'python verify_setup.py' to check if everything is configured correctly")
    print()

if __name__ == "__main__":
    main()
