"""RDL MCP Server - Model Context Protocol server for RDL file operations."""

from .server import MCPServer, mcp, run_server
from .validation import validate_rdl, extract_field_references, extract_field_references_with_context
from .reader import describe_rdl_report, get_rdl_datasets, get_rdl_parameters, get_rdl_columns
from .columns import add_column, remove_column, update_column_format, update_column_header, update_column_width
from .datasets import add_dataset_field, remove_dataset_field, update_stored_procedure
from .parameters import add_parameter, update_parameter

__version__ = '1.0.0'

__all__ = [
    'MCPServer',
    'mcp',
    'run_server',
    'validate_rdl',
    'extract_field_references',
    'extract_field_references_with_context',
    'describe_rdl_report',
    'get_rdl_datasets',
    'get_rdl_parameters',
    'get_rdl_columns',
    'add_column',
    'remove_column',
    'update_column_format',
    'update_column_header',
    'update_column_width',
    'add_dataset_field',
    'remove_dataset_field',
    'update_stored_procedure',
    'add_parameter',
    'update_parameter',
]
