#!/usr/bin/env python3
"""
Agent 365 Token Generator

This script helps you obtain an authentication token for the Agent 365 API.

Usage:
    python get_agent365_token.py              # Interactive token generation
    python get_agent365_token.py --mock       # Create mock token for testing

Prerequisites:
    - Agent 365 CLI installed (or direct API access)
    - Microsoft 365 account with Agent 365 permissions

Note: This script requires the Agent 365 CLI or API credentials.
If you don't have access to Agent 365, use --mock for testing.
"""

import json
import sys
import os
from pathlib import Path


def create_mock_token(token_path: Path):
    """Create a mock token for testing (no real API access)"""
    print("Creating mock token for testing...")
    print()

    token_data = {
        "access_token": "mock_token_for_testing",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": 9999999999
    }

    # Create directory if it doesn't exist
    token_path.parent.mkdir(parents=True, exist_ok=True)

    # Write token file
    with open(token_path, 'w') as f:
        json.dump(token_data, f, indent=2)

    # Set restrictive permissions (user read/write only)
    if os.name != 'nt':  # Unix-like systems
        os.chmod(token_path, 0o600)

    print(f"✅ Mock token created: {token_path}")
    print()
    print("⚠️  WARNING: This is a mock token for testing only.")
    print("   The MCP server will not be able to access real emails.")
    print()
    print("To get a real token:")
    print("  1. Install Agent 365 CLI from Microsoft")
    print("  2. Run: agent365 auth login")
    print("  3. Copy the token from Agent 365 CLI token file")
    print()


def get_real_token():
    """Get a real token from Agent 365 CLI or API"""
    print("🔑 Agent 365 Token Generation")
    print("=" * 60)
    print()
    print("This script requires the Agent 365 CLI or API access.")
    print()
    print("Option 1: Use Agent 365 CLI (Recommended)")
    print("  1. Install Agent 365 CLI:")
    print("     https://agent365.microsoft.com/docs/cli")
    print()
    print("  2. Authenticate:")
    print("     agent365 auth login")
    print()
    print("  3. The CLI will save the token to:")
    print("     Windows: %LOCALAPPDATA%\\Microsoft.Agents.A365.DevTools.Cli\\auth-token.json")
    print("     Mac/Linux: ~/.agent365/auth-token.json")
    print()
    print("  4. Copy the token file to the default location:")
    print("     cp <source> ~/.agent365/auth-token.json")
    print()
    print("Option 2: Direct API Access (Advanced)")
    print("  1. Register an Azure AD application")
    print("  2. Grant permissions: Mail.Read, Mail.ReadWrite")
    print("  3. Implement OAuth2 flow to obtain token")
    print("  4. Save token in the format shown in TOKEN_CONFIGURATION.md")
    print()
    print("Option 3: Use Mock Token (Testing Only)")
    print("  python get_agent365_token.py --mock")
    print()
    print("=" * 60)
    print()

    # Try to find existing token from Agent 365 CLI
    possible_paths = [
        Path.home() / ".agent365" / "auth-token.json",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft.Agents.A365.DevTools.Cli" / "auth-token.json",
    ]

    for path in possible_paths:
        if path.exists():
            print(f"✅ Found existing token: {path}")
            print()

            # Ask if user wants to copy it
            response = input("Copy this token to default location? [y/N]: ").strip().lower()
            if response == 'y':
                dest = Path.home() / ".agent365" / "auth-token.json"
                dest.parent.mkdir(parents=True, exist_ok=True)

                with open(path) as f:
                    token_data = json.load(f)

                with open(dest, 'w') as f:
                    json.dump(token_data, f, indent=2)

                print(f"✅ Token copied to: {dest}")
                return

    print("⚠️  No existing token found.")
    print("   Please follow Option 1 or Option 2 above to obtain a token.")
    print()


def main():
    # Parse arguments
    mock_mode = "--mock" in sys.argv

    # Determine token path
    token_path = Path.home() / ".agent365" / "auth-token.json"

    if mock_mode:
        create_mock_token(token_path)
    else:
        get_real_token()


if __name__ == "__main__":
    main()
