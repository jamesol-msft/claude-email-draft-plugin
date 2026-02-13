#!/usr/bin/env python3
"""
Verify Agent 365 Email Draft Plugin Setup

Checks:
- MCP proxy installed
- Skill file installed
- Token file exists and valid
- Claude Desktop configured

Usage:
    python verify_setup.py
"""
import json
import os
import platform
import sys
from pathlib import Path


def get_claude_config_path():
    """Get Claude Desktop config path for current OS"""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None
        return Path(appdata) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def check_file(path, name):
    """Check if file exists"""
    if path and path.exists():
        size = path.stat().st_size
        print(f"[OK] {name}")
        print(f"   Location: {path}")
        print(f"   Size: {size:,} bytes")
        return True
    else:
        print(f"[ERROR] {name} NOT FOUND")
        if path:
            print(f"   Expected: {path}")
        return False


def check_token(path):
    """Verify token file format"""
    if not path or not path.exists():
        print(f"[WARN]  Token file NOT FOUND")
        if path:
            print(f"   Expected: {path}")
        print(f"   This is OK if using mock mode")
        return None  # Not an error, might be using mock mode

    try:
        with open(path) as f:
            token = json.load(f)

        required = ["access_token", "token_type"]
        missing = [f for f in required if f not in token]

        if missing:
            print(f"[ERROR] Token file invalid - missing fields: {missing}")
            print(f"   Location: {path}")
            return False

        # Check if it's a mock token
        if token.get("access_token") == "mock_token_for_testing":
            print(f"[MOCK] Mock token detected")
            print(f"   Location: {path}")
            print(f"   Note: Using fake data for testing")
            return True

        # Check expiration if present
        if "expires_at" in token:
            import time
            expires_at = token["expires_at"]
            time_left = expires_at - time.time()

            if time_left <= 0:
                print(f"[WARN]  Token EXPIRED")
                print(f"   Location: {path}")
                print(f"   Expired: {int(-time_left / 60)} minutes ago")
                print(f"   Action: Run get_agent365_token.py to refresh")
                return False
            else:
                print(f"[OK] Token valid")
                print(f"   Location: {path}")
                print(f"   Expires in: {int(time_left / 60)} minutes")
                return True
        else:
            print(f"[OK] Token file valid")
            print(f"   Location: {path}")
            return True

    except json.JSONDecodeError as e:
        print(f"[ERROR] Token file invalid JSON: {e}")
        print(f"   Location: {path}")
        return False
    except Exception as e:
        print(f"[ERROR] Token file error: {e}")
        print(f"   Location: {path}")
        return False


def check_claude_config():
    """Check Claude Desktop configuration"""
    config_path = get_claude_config_path()

    if not config_path:
        print(f"[ERROR] Cannot determine Claude config path")
        return False

    if not config_path.exists():
        print(f"[ERROR] Claude Desktop config NOT FOUND")
        print(f"   Expected: {config_path}")
        print(f"   Action: Run setup.py to create config")
        return False

    try:
        with open(config_path) as f:
            config = json.load(f)

        if "mcpServers" not in config:
            print(f"[ERROR] Claude Desktop config missing mcpServers section")
            print(f"   Location: {config_path}")
            print(f"   Action: Run setup.py to add MCP server")
            return False

        if "agent365-proxy" not in config["mcpServers"]:
            print(f"[ERROR] Claude Desktop config missing agent365-proxy server")
            print(f"   Location: {config_path}")
            print(f"   Action: Run setup.py to add MCP server")
            return False

        server_config = config["mcpServers"]["agent365-proxy"]

        # Check mock mode
        mock_mode = server_config.get("env", {}).get("AGENT365_MOCK_MODE") == "true"

        if mock_mode:
            print(f"[OK] Claude Desktop configured (MOCK MODE)")
        else:
            print(f"[OK] Claude Desktop configured")

        print(f"   Location: {config_path}")
        print(f"   MCP Server: agent365-proxy")

        if "args" in server_config and len(server_config["args"]) > 0:
            print(f"   Proxy script: {server_config['args'][0]}")

        if mock_mode:
            print(f"   [MOCK] Mock mode enabled - will use fake data")

        return True

    except json.JSONDecodeError as e:
        print(f"[ERROR] Claude Desktop config invalid JSON: {e}")
        print(f"   Location: {config_path}")
        return False
    except Exception as e:
        print(f"[ERROR] Claude Desktop config error: {e}")
        print(f"   Location: {config_path}")
        return False


def main():
    print("================================================================")
    print("                                                              ")
    print("  [VERIFY] Agent 365 Email Draft Plugin - Setup Verification        ")
    print("                                                              ")
    print("================================================================")
    print()

    checks = []
    home = Path.home()

    # Check 1: MCP Proxy
    print("[1]  MCP Proxy")
    proxy_path = home / "agent365_mcp_proxy.py"
    checks.append(check_file(proxy_path, "MCP Proxy"))
    print()

    # Check 2: Skill File
    print("[2]  Skill File")
    skill_path = home / ".claude" / "skills" / "email-draft" / "SKILL.md"
    checks.append(check_file(skill_path, "Skill File"))
    print()

    # Check 3: Token File (optional - might be using mock mode)
    print("[3]  Agent 365 Token")
    token_path = home / ".agent365" / "auth-token.json"
    token_result = check_token(token_path)
    if token_result is not None:
        checks.append(token_result)
    print()

    # Check 4: Claude Config
    print("[4]  Claude Desktop Configuration")
    checks.append(check_claude_config())
    print()

    # Summary
    print("=" * 64)
    passed = sum(1 for c in checks if c)
    total = len(checks)

    if passed == total:
        print(f"[OK] All checks passed! ({passed}/{total})")
        print()
        print("[SUCCESS] Setup is complete!")
        print()
        print("[NEXT] Next steps:")
        print("  1. Restart Claude Desktop/CLI to load the MCP server")
        print("  2. Test the skill: /email-draft show me unread messages")
        print()
        sys.exit(0)
    else:
        print(f"[WARN]  Setup incomplete: {passed}/{total} checks passed")
        print()
        print("[FIX] To fix issues:")
        print("  1. Run: python setup.py")
        print("  2. Follow the instructions for token setup")
        print("  3. Run this script again to verify")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
