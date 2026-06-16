#!/usr/bin/env python3
"""
MCP Server for RDL (Report Definition Language) Report Editing
Provides high-level tools for reading and modifying SSRS/RDL reports
"""

from rdl_mcp.server import MCPServer, mcp


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == '__main__':
    main()

