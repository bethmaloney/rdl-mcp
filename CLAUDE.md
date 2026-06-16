# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RDL MCP Server is a Model Context Protocol (MCP) server that enables AI assistants to read and modify SSRS (SQL Server Reporting Services) RDL files. It provides simple JSON-based tools instead of requiring direct XML manipulation of complex RDL structures.

## Build and Test Commands

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_rdl_mcp_server.py -v

# Run a specific test class
python3 -m pytest tests/test_rdl_mcp_server.py::TestColumnOperations -v

# Run a specific test
python3 -m pytest tests/test_rdl_mcp_server.py::TestColumnOperations::test_update_column_header -v

# Run the server directly (for testing)
python3 rdl_mcp_server.py

# Install with uv (preferred)
uvx rdl-mcp
```

## Architecture

The codebase follows a modular design with the main MCP server delegating to specialized modules:

- **`rdl_mcp_server.py`** - Entry point; calls `mcp.run()` to start the fastmcp server
- **`rdl_mcp/server.py`** - fastmcp `mcp` instance with `@mcp.tool` decorators for all tools; also exports `MCPServer` (a thin wrapper used by tests)
- **`rdl_mcp/reader.py`** - Read-only operations: `describe_rdl_report`, `get_rdl_datasets`, `get_rdl_parameters`, `get_rdl_columns`
- **`rdl_mcp/columns.py`** - Column modifications: add/remove/update header/width/format
- **`rdl_mcp/datasets.py`** - Dataset operations: add/remove fields, update stored procedures
- **`rdl_mcp/parameters.py`** - Parameter operations: add/update report parameters
- **`rdl_mcp/validation.py`** - RDL validation and field reference extraction
- **`rdl_mcp/xml_utils.py`** - Shared XML parsing utilities and namespace handling

## Key Constraints

- **fastmcp** - MCP transport is provided by the `fastmcp` library (declared in `pyproject.toml`)
- **Python 3.10+ compatibility** required
- **Tablix controls only** - Currently supports table-based reports, not Matrix or Chart controls
- **RDL 2016 namespace** - Uses `http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition`

## MCP Protocol

The server uses fastmcp for the MCP transport (stdio by default). Tool registration is done via `@mcp.tool` decorators in `rdl_mcp/server.py`. fastmcp automatically handles protocol negotiation, tool listing, and tool dispatch.

## Testing

Tests use pytest with fixtures that create temporary RDL files. The `_create_sample_report()` function in tests generates valid minimal RDL documents for testing. `TestFastMCPServer` verifies that all tools are correctly registered with the fastmcp instance.

**Requirements:**
- Write tests before implementing any changes
- All tests must pass after making changes (`python3 -m pytest tests/ -v`)
