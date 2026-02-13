#!/usr/bin/env python3
"""
Agent 365 MCP Proxy Server

A Model Context Protocol (MCP) server that proxies email operations to Microsoft Agent 365.
Implements JSON-RPC 2.0 over stdio transport, translating MCP tool calls to Agent 365 API requests.

Architecture:
    Claude Desktop → [stdin/stdout JSON-RPC] → agent365_mcp_proxy.py → [HTTPS] → Agent 365 Mail Server

Features:
    - 3 email tools: search_messages, get_message, create_draft
    - Token authentication from local agent365-cli token file
    - SSE and JSON response parsing
    - Retry logic with exponential backoff
    - 90s timeout for long-running operations
    - All logging to stderr (stdout reserved for JSON-RPC)

Requirements:
    - Python 3.8+
    - requests library
    - Microsoft Agent 365 token in ~/.agent365/auth-token.json or %LOCALAPPDATA%\\Microsoft.Agents.A365.DevTools.Cli\\auth-token.json

Usage:
    # Run as MCP server (stdio transport)
    python agent365_mcp_proxy.py

    # Test individual calls (echo JSON-RPC to stdin)
    echo '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05"}}' | python agent365_mcp_proxy.py

Author: WorkIQ Skills Team
Version: 1.0.0
License: MIT
"""

import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests

# Configure logging to stderr (CRITICAL: stdout must only contain JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Constants
AGENT365_MAIL_SERVER_URL = "https://agent365.svc.cloud.microsoft/agents/servers/Mail"
TOKEN_PATHS = [
    Path.home() / ".agent365" / "auth-token.json",  # Linux/Mac path
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft.Agents.A365.DevTools.Cli" / "auth-token.json" if os.environ.get("LOCALAPPDATA") else None  # Windows path
]
REQUEST_TIMEOUT = 90  # 90 seconds (Agent 365 search can take 60-90s)
MAX_RETRIES = 1  # Retry network errors once
RETRY_BACKOFF = 5  # 5 second backoff between retries

# Fix import for Windows path
import os


class Agent365MCPProxy:
    """
    MCP Server that proxies email operations to Microsoft Agent 365.

    Implements the Model Context Protocol (JSON-RPC 2.0 over stdio) and forwards
    tool calls to Agent 365 Mail Server via HTTPS.
    """

    def __init__(self):
        """Initialize the proxy server and load authentication token."""
        self.server_info = {
            "name": "agent365-mail-proxy",
            "version": "1.0.0"
        }
        self.protocol_version = "2024-11-05"
        self.token = self._load_token()
        logger.info(f"Agent365MCPProxy initialized with {len(self.tools)} tools")

    @property
    def tools(self) -> List[Dict[str, Any]]:
        """
        Define the 3 MCP tools exposed by this proxy.

        Returns:
            List of tool definitions with names, descriptions, and input schemas
        """
        return [
            {
                "name": "search_messages",
                "description": "Search for email messages using natural language queries. Supports searching by sender, subject, keywords, date range, and more. Returns a list of matching messages with basic metadata.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query (e.g., 'emails from Sarah about budget', 'unread messages from last week')"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10, max: 50)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_message",
                "description": "Retrieve full details of a specific email message by its ID. Returns the complete message including subject, sender, recipients, body content, and metadata.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Message ID from search results (e.g., 'AAMkAGI2T...')"
                        }
                    },
                    "required": ["id"]
                }
            },
            {
                "name": "create_draft",
                "description": "Create a draft email message in the user's mailbox. The draft is saved to the Drafts folder where the user can review, edit, and send it. Does not send automatically.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address (e.g., 'john.doe@contoso.com')"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line"
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body content (plain text or HTML)"
                        },
                        "cc": {
                            "type": "string",
                            "description": "Optional CC recipient email address",
                            "default": ""
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            }
        ]

    def _load_token(self) -> str:
        """
        Load Agent 365 authentication token from local token file.

        Searches for token in standard locations:
            - ~/.agent365/auth-token.json (Linux/Mac)
            - %LOCALAPPDATA%\\Microsoft.Agents.A365.DevTools.Cli\\auth-token.json (Windows)

        Returns:
            str: Bearer token for Agent 365 API

        Raises:
            FileNotFoundError: If token file not found in any standard location
            ValueError: If token file format is invalid
        """
        # Try each token path
        for token_path in TOKEN_PATHS:
            if token_path and token_path.exists():
                logger.info(f"Loading token from {token_path}")
                with open(token_path, 'r') as f:
                    token_data = json.load(f)

                # Extract token from nested structure
                # Format: {"Tokens": {"<tenant-id>": {"AccessToken": "...", "ExpiresOn": "..."}}}
                if "Tokens" in token_data:
                    # Get first tenant token
                    tenant_tokens = list(token_data["Tokens"].values())
                    if tenant_tokens:
                        token_info = tenant_tokens[0]
                        access_token = token_info.get("AccessToken")
                        expires_on = token_info.get("ExpiresOn")

                        if access_token:
                            # Check if token is expired
                            if expires_on:
                                expiry_timestamp = int(expires_on)
                                if expiry_timestamp < time.time():
                                    logger.warning(f"Token expired at {time.ctime(expiry_timestamp)}")
                                    logger.warning("Please refresh token with: python get_agent365_token.py")
                                else:
                                    logger.info(f"Token valid until {time.ctime(expiry_timestamp)}")

                            return access_token

                raise ValueError(f"Invalid token format in {token_path}")

        # No token found in any location
        raise FileNotFoundError(
            "Agent 365 token not found. Please authenticate with: python get_agent365_token.py\n"
            f"Expected locations: {[str(p) for p in TOKEN_PATHS if p]}"
        )

    def _call_agent365(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forward tool call to Agent 365 Mail Server via HTTPS.

        Implements retry logic with exponential backoff for network errors.
        Parses both JSON and Server-Sent Events (SSE) response formats.

        Args:
            tool_name: Name of the tool to call (e.g., "searchMessages")
            arguments: Tool arguments as dictionary

        Returns:
            dict: Tool result from Agent 365

        Raises:
            Exception: If request fails after retries or Agent 365 returns error
        """
        # Map MCP tool names to Agent 365 tool names
        tool_name_mapping = {
            "search_messages": "searchMessages",
            "get_message": "getMessage",
            "create_draft": "createDraft"
        }
        agent365_tool_name = tool_name_mapping.get(tool_name, tool_name)

        # Build JSON-RPC request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": agent365_tool_name,
                "arguments": arguments
            }
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        logger.info(f"Calling Agent 365: {agent365_tool_name} with args: {json.dumps(arguments, indent=2)}")

        # Retry logic with exponential backoff
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.post(
                    AGENT365_MAIL_SERVER_URL,
                    headers=headers,
                    json=mcp_request,
                    timeout=REQUEST_TIMEOUT
                )

                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")

                if response.status_code == 200:
                    # Check if response is empty
                    if not response.text:
                        logger.error("Empty response from Agent 365")
                        return {"error": "Empty response from Agent 365"}

                    # Parse response (supports both JSON and SSE formats)
                    result = self._parse_response(response)
                    return result

                elif response.status_code == 401:
                    logger.error("Unauthorized: Token expired or invalid")
                    return {
                        "error": "Authentication failed. Please refresh token with: python get_agent365_token.py"
                    }

                else:
                    logger.error(f"Agent 365 error: {response.status_code} - {response.text[:200]}")
                    return {
                        "error": f"Agent 365 returned status {response.status_code}",
                        "details": response.text[:200]
                    }

            except requests.exceptions.Timeout:
                logger.error(f"Request timeout after {REQUEST_TIMEOUT}s (attempt {attempt + 1}/{MAX_RETRIES + 1})")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying after {RETRY_BACKOFF}s backoff...")
                    time.sleep(RETRY_BACKOFF)
                else:
                    return {
                        "error": f"Request timeout after {REQUEST_TIMEOUT}s. Agent 365 may be slow or unavailable."
                    }

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error: {str(e)} (attempt {attempt + 1}/{MAX_RETRIES + 1})")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying after {RETRY_BACKOFF}s backoff...")
                    time.sleep(RETRY_BACKOFF)
                else:
                    return {
                        "error": f"Network error after {MAX_RETRIES + 1} attempts: {str(e)}"
                    }

        return {"error": "Max retries exceeded"}

    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse Agent 365 response (supports both JSON and SSE formats).

        Agent 365 may return responses in two formats:
            1. JSON: Standard JSON-RPC response with "result" field
            2. SSE: Server-Sent Events with "data: " lines containing JSON

        Args:
            response: HTTP response from Agent 365

        Returns:
            dict: Parsed result or error
        """
        # Check if response is Server-Sent Events format
        content_type = response.headers.get('Content-Type', '')
        if 'text/event-stream' in content_type:
            # Parse SSE format: look for "data: " lines
            lines = response.text.split('\n')
            for line in lines:
                if line.startswith('data: '):
                    data_json = line[6:]  # Remove 'data: ' prefix
                    try:
                        result = json.loads(data_json)
                        # Extract the tool result from MCP response
                        if "result" in result:
                            result_data = result["result"]
                            # Check if it's an error result
                            if isinstance(result_data, dict) and result_data.get("isError"):
                                # Extract error message from content
                                content = result_data.get("content", [])
                                error_messages = [c.get("text", "") for c in content if c.get("type") == "text"]
                                logger.error(f"Agent 365 error: {' | '.join(error_messages)}")
                                return {"error": " | ".join(error_messages)}
                            return result_data
                        else:
                            # Return entire result if no "result" field
                            return result
                    except json.JSONDecodeError:
                        continue

            logger.error("Failed to parse SSE response")
            return {
                "error": "Failed to parse SSE response",
                "response_preview": response.text[:200]
            }

        # Try normal JSON parsing
        try:
            result = response.json()
            # Extract the tool result from MCP response
            if "result" in result:
                result_data = result["result"]
                # Check if it's an error result
                if isinstance(result_data, dict) and result_data.get("isError"):
                    # Extract error message from content
                    content = result_data.get("content", [])
                    error_messages = [c.get("text", "") for c in content if c.get("type") == "text"]
                    logger.error(f"Agent 365 error: {' | '.join(error_messages)}")
                    return {"error": " | ".join(error_messages)}
                return result_data
            else:
                return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            return {
                "error": "Failed to parse JSON response",
                "response_preview": response.text[:200]
            }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming JSON-RPC request.

        Supports MCP protocol methods:
            - initialize: Server initialization and capability exchange
            - tools/list: List available tools
            - tools/call: Execute a tool

        Args:
            request: JSON-RPC request object

        Returns:
            dict: JSON-RPC response object
        """
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params", {})

        logger.info(f"Handling request: {method} (id={request_id})")

        try:
            if method == "initialize":
                # Return server capabilities and info
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": self.protocol_version,
                        "serverInfo": self.server_info,
                        "capabilities": {
                            "tools": {}  # We provide tools
                        }
                    }
                }

            elif method == "tools/list":
                # Return list of available tools
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": self.tools
                    }
                }

            elif method == "tools/call":
                # Execute tool call
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                # Validate tool name
                valid_tools = [tool["name"] for tool in self.tools]
                if tool_name not in valid_tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}. Available tools: {valid_tools}"
                        }
                    }

                # Forward to Agent 365
                logger.info(f"Calling tool: {tool_name}")
                result = self._call_agent365(tool_name, arguments)

                # Check if result is an error
                if "error" in result:
                    logger.error(f"Tool call failed: {result['error']}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": result["error"],
                            "data": result.get("details")
                        }
                    }

                logger.info(f"Tool call successful: {tool_name}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }

            else:
                # Unknown method
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

        except Exception as e:
            logger.error(f"Error handling request: {str(e)}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    def run(self):
        """
        Run the MCP server in stdio transport mode.

        Reads JSON-RPC requests from stdin (one per line) and writes responses to stdout.
        All logging goes to stderr to keep stdout clean for JSON-RPC protocol.
        """
        logger.info("Agent365MCPProxy server starting (stdio transport)")
        logger.info(f"Listening for JSON-RPC requests on stdin...")

        try:
            # Read requests from stdin line by line
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON-RPC request
                    request = json.loads(line)

                    # Handle request
                    response = self.handle_request(request)

                    # Write JSON-RPC response to stdout (one line)
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON input: {str(e)}")
                    # Send error response
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error: Invalid JSON"
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {str(e)}", exc_info=True)


def main():
    """Main entry point for the MCP proxy server."""
    try:
        proxy = Agent365MCPProxy()
        proxy.run()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
