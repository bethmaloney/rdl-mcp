# RDL MCP Server

mcp-name: io.github.bethmaloney/rdl-mcp

[![PyPI](https://img.shields.io/pypi/v/rdl-mcp.svg)](https://pypi.org/project/rdl-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

Edit SSRS reports using AI assistants instead of wrestling with 2000+ lines of XML. This [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server gives Claude, Copilot, and other AI tools simple commands to read and modify RDL files.

## What It Does

**Read reports:**
- `describe_rdl_report` - Get report structure overview
- `get_rdl_datasets` - View datasets, fields, and stored procedures (supports field limiting and filtering)
- `get_rdl_parameters` - List all report parameters
- `get_rdl_columns` - See column headers, widths, and bindings

**Modify reports:**
- `update_column_header` / `update_column_width` - Change columns
- `add_column` / `remove_column` - Add or remove columns
- `update_column_format` - Change number/date formatting
- `update_column_colors` - Change the colors for the column header and the data rows
- `update_stored_procedure` - Swap stored procedures
- `add_dataset_field` / `remove_dataset_field` - Manage dataset fields
- `add_parameter` / `update_parameter` - Manage parameters
- `validate_rdl` - Validate XML after changes

**Why it's better than editing XML:**
- AI sees clean JSON instead of verbose XML namespaces
- One-line commands instead of error-prone string manipulation
- Automatic validation catches errors before they break reports
- Built on [fastmcp](https://github.com/jlowin/fastmcp) for a robust, standards-compliant MCP transport

## Installation

**Requirements:**
- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (Python package manager and tool runner)

**Installing uv:**
- **macOS/Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows:** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Alternative (all platforms):** `pip install uv` or see [installation docs](https://docs.astral.sh/uv/getting-started/installation/)

**Note:** `uvx` (included with `uv`) automatically handles the Python environment and dependencies. No manual Python package installation needed!

### Quick Start

<details>
<summary><b>Claude Desktop</b></summary>

Edit config file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "rdl-mcp": {
      "command": "uvx",
      "args": ["rdl-mcp"]
    }
  }
}
```
</details>

<details>
<summary><b>GitHub Copilot (VSCode)</b></summary>

Add to VSCode settings (`.vscode/mcp.json` in your workspace or user settings):

```json
{
  "servers": {
    "rdlMcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["rdl-mcp"]
    }
  }
}
```

**Note:** Requires VSCode with Copilot Chat extension installed.
</details>


**After installation:** Restart your AI assistant and try: `"Describe the structure of my report.rdl file"`

## Usage

Just ask your AI assistant in natural language:

- "What datasets does this report use?"
- "Make the Account Number column 2 inches wide"
- "Format the Amount column as currency with 2 decimals"
- "Add a new Amount column that shows the sum in the footer"
- "Add a Status column but leave the footer blank"
- "Update the main dataset to use the V2 stored procedure and add the TaxAmount field"
- "Remove the obsolete Status column"
- "Add a Year parameter to filter the report"

The AI assistant will use the appropriate MCP tools automatically.

## Example: Editing vs. XML

**Without MCP** (manually editing XML):
```xml
<!-- Find this in 2000+ lines -->
<TablixCell><CellContents><Textbox><Paragraphs>
  <Paragraph><TextRuns><TextRun>
    <Value>Old Header</Value>
  </TextRun></TextRuns></Paragraph>
</Paragraphs></Textbox></CellContents></TablixCell>
```

**With MCP** (one command):
```python
update_column_header(filepath="report.rdl",
                     old_header="Old Header",
                     new_header="New Header")
```

## API Reference

<details>
<summary>View all available tools</summary>

### Reading Tools

- **`describe_rdl_report(filepath)`** - Report structure summary
- **`get_rdl_datasets(filepath, field_limit?, field_pattern?)`** - Datasets with fields and stored procedures
  - `field_limit`: 0 = counts only (default), -1 = all fields, N = limit to N fields
  - `field_pattern`: Optional regex to filter field names
- **`get_rdl_parameters(filepath)`** - All parameters with configurations
- **`get_rdl_columns(filepath)`** - Column headers, widths, bindings, and textbox names
  - `header_textbox_name`: Name of the header-row Textbox (used for layout/styling)
  - `data_textbox_name`: Name of the data-row Textbox (used by SSRS as the CSV/text export column header)

### Editing Tools

- **`update_column_header(filepath, old_header, new_header)`** - Change column text
- **`update_column_width(filepath, column_index, new_width)`** - Modify width (e.g. "2.5in")
- **`update_column_format(filepath, column_index, format_string)`** - Change format (e.g. "#,0.00", "dd/MM/yyyy", "C2")
- **`add_column(filepath, column_index, header_text, field_binding, width?, format_string?, footer_expression?)`** - Add column
  - `footer_expression`: Optional expression for footer/total row - e.g. "=Sum(Fields!Amount.Value)", "=Count(Fields!ID.Value)", "Total:", or leave empty
  - The data-row textbox is automatically named after the field (e.g. `=Fields!Ship_Date.Value` → `Name="Ship_Date"`) so SSRS CSV/text exports use the correct column header
- **`remove_column(filepath, column_index)`** - Remove column
- **`update_stored_procedure(filepath, dataset_name, new_sproc)`** - Change dataset sproc
- **`add_dataset_field(filepath, dataset_name, field_name, data_field, type_name)`** - Add field to dataset
- **`remove_dataset_field(filepath, dataset_name, field_name)`** - Remove field from dataset
- **`add_parameter(filepath, name, data_type, prompt)`** - Add new parameter
- **`update_parameter(filepath, name, prompt?, default_value?)`** - Update parameter
- **`validate_rdl(filepath)`** - Validate XML structure

All tools return `{success: bool, message?: string, error?: string}` or structured data.

</details>

## Limitations & Roadmap

**Current limitations:**
- Tablix (table) controls only - no Matrix or Chart support yet
- Works best with standard report layouts
- Some complex RDL features may still need manual XML editing

**Planned features:**
- Column reordering, grouping, and sorting configuration
- Expression builder helpers
- Dataset field management

## Troubleshooting

**Server not appearing?**
- Check absolute path in config is correct
- Verify Python 3.10+: `python3 --version`
- Restart your MCP client

**Permission errors?**
- Make script executable: `chmod +x rdl_mcp_server.py`
- Check RDL file read/write permissions



## Releasing a New Version

This server is published to [PyPI](https://pypi.org/project/rdl-mcp/) and the [MCP Registry](https://registry.modelcontextprotocol.io/). To release a new version:

1. **Update version numbers** in both files:

   `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

   `server.json`:
   ```json
   {
     "version": "0.2.0",
     "packages": [
       {
         "version": "0.2.0"
       }
     ]
   }
   ```

2. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Release v0.2.0: Add feature description"
   ```

3. **Create and push a git tag**:
   ```bash
   git tag v0.2.0
   git push origin main --tags
   ```

4. **Automated publishing**: The GitHub Actions workflows automatically:
   - Build and publish to PyPI (users can install via `uvx rdl-mcp`)
   - Validate `server.json` against the MCP schema
   - Publish to the MCP Registry (server appears in registry search)
   - Update downstream registries (like GitHub's MCP marketplace)

## Contributing

PRs welcome! Priority areas:
- Better column detection for complex layouts
- More editing operations (reordering, grouping, etc.)

Requirements: Python 3.10+, fastmcp

1. Fork repo
2. Create feature branch
3. Make changes + tests
4. Submit PR

## License

MIT License - see [LICENSE](LICENSE) file for details.

This means you're free to use, modify, and distribute this software for any purpose, commercial or non-commercial.
