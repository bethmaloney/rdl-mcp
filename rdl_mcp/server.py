"""MCP Server for RDL file operations."""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from . import batch
from . import columns
from . import datasets
from . import parameters
from . import reader
from . import styles
from . import validation

logger = logging.getLogger(__name__)

mcp = FastMCP("rdl-mcp-server")


# ---------------------------------------------------------------------------
# Existing read tools
# ---------------------------------------------------------------------------

@mcp.tool
def describe_rdl_report(filepath: str) -> Dict[str, Any]:
    """Get a high-level summary of the RDL report structure."""
    return reader.describe_rdl_report(filepath)


@mcp.tool
def get_rdl_datasets(filepath: str, field_limit: int = 0,
                     field_pattern: Optional[str] = None) -> Dict[str, Any]:
    """Get all datasets with their fields, queries, and stored procedures."""
    return reader.get_rdl_datasets(filepath, field_limit, field_pattern)


@mcp.tool
def get_rdl_parameters(filepath: str) -> Dict[str, Any]:
    """Get all report parameters with their types and values."""
    return reader.get_rdl_parameters(filepath)


@mcp.tool
def get_rdl_columns(filepath: str) -> Dict[str, Any]:
    """Get table columns with headers, widths, bindings, and textbox names.

    Each column includes header_textbox_name (header-row Textbox Name, used for layout/styling)
    and data_textbox_name (data-row Textbox Name, used by SSRS as the CSV/text export column header).
    """
    return reader.get_rdl_columns(filepath)


@mcp.tool
def validate_rdl(filepath: str) -> Dict[str, Any]:
    """Validate RDL XML structure and field references."""
    return validation.validate_rdl(filepath)


# ---------------------------------------------------------------------------
# Existing column mutation tools
# ---------------------------------------------------------------------------

@mcp.tool
def update_column_header(filepath: str, old_header: str, new_header: str) -> Dict[str, Any]:
    """Update a column header text."""
    return columns.update_column_header(filepath, old_header, new_header)


@mcp.tool
def update_column_width(filepath: str, column_index: int, new_width: str) -> Dict[str, Any]:
    """Update a column width."""
    return columns.update_column_width(filepath, column_index, new_width)


@mcp.tool
def update_column_format(filepath: str, column_index: int, format_string: str) -> Dict[str, Any]:
    """Update the format string for a column."""
    return columns.update_column_format(filepath, column_index, format_string)


@mcp.tool
def update_column_colors(filepath: str, column_index: int,
                         text_color: Optional[str] = None,
                         background_color: Optional[str] = None,
                         header_text_color: Optional[str] = None,
                         header_background_color: Optional[str] = None) -> Dict[str, Any]:
    """Update text and background colors for a column's data and/or header cells."""
    return columns.update_column_colors(filepath, column_index, text_color, background_color,
                                        header_text_color, header_background_color)


@mcp.tool
def add_column(filepath: str, column_index: int, header_text: str,
               field_binding: str, width: str = "1in",
               format_string: Optional[str] = None,
               footer_expression: Optional[str] = None) -> Dict[str, Any]:
    """Add a new column to the report table."""
    return columns.add_column(filepath, column_index, header_text, field_binding,
                              width, format_string, footer_expression)


@mcp.tool
def remove_column(filepath: str, column_index: int,
                  auto_adjust_page_width: bool = True) -> Dict[str, Any]:
    """Remove a column from the report table."""
    return columns.remove_column(filepath, column_index, auto_adjust_page_width)


# ---------------------------------------------------------------------------
# Existing dataset / parameter tools
# ---------------------------------------------------------------------------

@mcp.tool
def update_stored_procedure(filepath: str, dataset_name: str, new_sproc: str) -> Dict[str, Any]:
    """Update the stored procedure for a dataset."""
    return datasets.update_stored_procedure(filepath, dataset_name, new_sproc)


@mcp.tool
def add_dataset_field(filepath: str, dataset_name: str, field_name: str,
                      data_field: str, type_name: str) -> Dict[str, Any]:
    """Add a new field to a dataset."""
    return datasets.add_dataset_field(filepath, dataset_name, field_name, data_field, type_name)


@mcp.tool
def remove_dataset_field(filepath: str, dataset_name: str, field_name: str) -> Dict[str, Any]:
    """Remove a field from a dataset."""
    return datasets.remove_dataset_field(filepath, dataset_name, field_name)


@mcp.tool
def add_parameter(filepath: str, name: str, data_type: str, prompt: str) -> Dict[str, Any]:
    """Add a new report parameter."""
    return parameters.add_parameter(filepath, name, data_type, prompt)


@mcp.tool
def update_parameter(filepath: str, name: str, prompt: Optional[str] = None,
                     default_value: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing report parameter."""
    return parameters.update_parameter(filepath, name, prompt, default_value)


# ---------------------------------------------------------------------------
# New batch + style + layout tools
# ---------------------------------------------------------------------------

@mcp.tool
def update_table_batch(
    filepath: str,
    updates: List[Dict[str, Any]],
    backup: bool = False,
) -> Dict[str, Any]:
    """Apply multiple column updates (width/header/colors/format/alignment) in one atomic write.

    All changes are applied in-memory first; if any update fails the file is
    not written (all-or-none).  Returns a mutation-response envelope including
    a machine-readable before/after diff.

    Each element of *updates* is a dict with ``column_index`` (int, required)
    and any of: ``width``, ``header``, ``format_string``, ``text_color``,
    ``background_color``, ``header_text_color``, ``header_background_color``,
    ``alignment``, ``header_alignment``.

    Set ``backup=True`` to save a timestamped ``.bak`` file before writing.
    """
    return batch.update_table_batch(filepath, updates, backup=backup)


@mcp.tool
def preview_table_batch(
    filepath: str,
    updates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Preview what update_table_batch would do without modifying the file.

    Returns the same diff structure as update_table_batch with dry_run=True.
    The file is never written.
    """
    return batch.preview_table_batch(filepath, updates)


@mcp.tool
def get_column_styles(filepath: str) -> Dict[str, Any]:
    """Get effective style properties for every column (colors, format, alignment)."""
    return styles.get_column_styles(filepath)


@mcp.tool
def get_table_styles(filepath: str) -> Dict[str, Any]:
    """Get table-level style properties (border, background, font defaults)."""
    return styles.get_table_styles(filepath)


@mcp.tool
def get_layout_diagnostics(filepath: str) -> Dict[str, Any]:
    """Get layout diagnostics: page size, margins, tablix width, and overflow/fit status."""
    return styles.get_layout_diagnostics(filepath)


# ---------------------------------------------------------------------------
# MCPServer wrapper (backward-compatible)
# ---------------------------------------------------------------------------

class MCPServer:
    """Thin wrapper around RDL operations, kept for backward compatibility."""

    def describe_rdl_report(self, filepath: str) -> Dict[str, Any]:
        return reader.describe_rdl_report(filepath)

    def get_rdl_datasets(self, filepath: str, field_limit: int = 0,
                         field_pattern: Optional[str] = None) -> Dict[str, Any]:
        return reader.get_rdl_datasets(filepath, field_limit, field_pattern)

    def get_rdl_parameters(self, filepath: str) -> Dict[str, Any]:
        return reader.get_rdl_parameters(filepath)

    def get_rdl_columns(self, filepath: str) -> Dict[str, Any]:
        return reader.get_rdl_columns(filepath)

    def validate_rdl(self, filepath: str) -> Dict[str, Any]:
        return validation.validate_rdl(filepath)

    def update_column_header(self, filepath: str, old_header: str, new_header: str) -> Dict[str, Any]:
        return columns.update_column_header(filepath, old_header, new_header)

    def update_column_width(self, filepath: str, column_index: int, new_width: str) -> Dict[str, Any]:
        return columns.update_column_width(filepath, column_index, new_width)

    def update_column_format(self, filepath: str, column_index: int, format_string: str) -> Dict[str, Any]:
        return columns.update_column_format(filepath, column_index, format_string)

    def update_column_colors(self, filepath: str, column_index: int,
                             text_color: Optional[str] = None,
                             background_color: Optional[str] = None,
                             header_text_color: Optional[str] = None,
                             header_background_color: Optional[str] = None) -> Dict[str, Any]:
        return columns.update_column_colors(filepath, column_index, text_color, background_color,
                                            header_text_color, header_background_color)

    def add_column(self, filepath: str, column_index: int, header_text: str,
                   field_binding: str, width: str = "1in",
                   format_string: Optional[str] = None,
                   footer_expression: Optional[str] = None) -> Dict[str, Any]:
        return columns.add_column(filepath, column_index, header_text, field_binding,
                                  width, format_string, footer_expression)

    def remove_column(self, filepath: str, column_index: int,
                      auto_adjust_page_width: bool = True) -> Dict[str, Any]:
        return columns.remove_column(filepath, column_index, auto_adjust_page_width)

    def update_stored_procedure(self, filepath: str, dataset_name: str, new_sproc: str) -> Dict[str, Any]:
        return datasets.update_stored_procedure(filepath, dataset_name, new_sproc)

    def add_dataset_field(self, filepath: str, dataset_name: str, field_name: str,
                          data_field: str, type_name: str) -> Dict[str, Any]:
        return datasets.add_dataset_field(filepath, dataset_name, field_name, data_field, type_name)

    def remove_dataset_field(self, filepath: str, dataset_name: str, field_name: str) -> Dict[str, Any]:
        return datasets.remove_dataset_field(filepath, dataset_name, field_name)

    def add_parameter(self, filepath: str, name: str, data_type: str, prompt: str) -> Dict[str, Any]:
        return parameters.add_parameter(filepath, name, data_type, prompt)

    def update_parameter(self, filepath: str, name: str, prompt: Optional[str] = None,
                         default_value: Optional[str] = None) -> Dict[str, Any]:
        return parameters.update_parameter(filepath, name, prompt, default_value)

    # --- new tools ---

    def update_table_batch(self, filepath: str, updates: List[Dict[str, Any]],
                           backup: bool = False) -> Dict[str, Any]:
        return batch.update_table_batch(filepath, updates, backup=backup)

    def preview_table_batch(self, filepath: str, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        return batch.preview_table_batch(filepath, updates)

    def get_column_styles(self, filepath: str) -> Dict[str, Any]:
        return styles.get_column_styles(filepath)

    def get_table_styles(self, filepath: str) -> Dict[str, Any]:
        return styles.get_table_styles(filepath)

    def get_layout_diagnostics(self, filepath: str) -> Dict[str, Any]:
        return styles.get_layout_diagnostics(filepath)

    def _extract_field_references_with_context(self, expression: str, default_dataset: str) -> Dict[str, Any]:
        return validation.extract_field_references_with_context(expression, default_dataset)

    def _extract_field_references(self, expression: str):
        return validation.extract_field_references(expression)


def run_server():
    """Run the MCP server."""
    mcp.run()


