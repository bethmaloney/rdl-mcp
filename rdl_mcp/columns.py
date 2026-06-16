"""RDL column operations - add, remove, update columns."""

import re
import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional

from .xml_utils import parse_rdl_tree, get_namespace, write_xml
from .reader import _detect_row_type

logger = logging.getLogger(__name__)


def add_column(filepath: str, column_index: int, header_text: str,
               field_binding: str, width: str = "1in",
               format_string: Optional[str] = None,
               footer_expression: Optional[str] = None) -> Dict[str, Any]:
    """Add a new column to the report table at a specified position."""
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    tablix = root.find(f'.//{ns}Tablix')
    if tablix is None:
        return {'success': False, 'message': 'No Tablix found in report'}

    # Get current columns to determine insert position
    tablix_columns = tablix.find(f'.//{ns}TablixBody/{ns}TablixColumns')
    if tablix_columns is None:
        return {'success': False, 'message': 'No TablixColumns found'}

    current_columns = tablix_columns.findall(f'{ns}TablixColumn')
    num_columns = len(current_columns)

    # Handle -1 for end position
    if column_index == -1:
        column_index = num_columns

    if column_index < 0 or column_index > num_columns:
        return {'success': False, 'message': f'Invalid column index {column_index}. Must be 0-{num_columns}'}

    # Create new TablixColumn
    new_tablix_col = ET.Element(f'{ns}TablixColumn')
    width_elem = ET.SubElement(new_tablix_col, f'{ns}Width')
    width_elem.text = width

    # Insert column definition
    tablix_columns.insert(column_index, new_tablix_col)

    # Add TablixMember to column hierarchy
    col_hierarchy = tablix.find(f'.//{ns}TablixColumnHierarchy/{ns}TablixMembers')
    if col_hierarchy is not None:
        new_member = ET.Element(f'{ns}TablixMember')
        col_hierarchy.insert(column_index, new_member)

    # Add cells to each row
    tablix_rows = tablix.findall(f'.//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow')

    for row_idx, row in enumerate(tablix_rows):
        cells = row.find(f'{ns}TablixCells')
        if cells is None:
            continue

        existing_cells = cells.findall(f'{ns}TablixCell')
        row_type = _detect_row_type(existing_cells, ns)

        # Create appropriate cell based on row type
        new_cell = _create_table_cell(
            ns, row_type, row_idx, column_index,
            header_text, field_binding, format_string, footer_expression
        )

        cells.insert(column_index, new_cell)

    # Update Tablix width
    _update_tablix_width(tablix, ns)

    write_xml(tree, filepath)

    return {
        'success': True,
        'message': f'Added column "{header_text}" at position {column_index}'
    }


def remove_column(filepath: str, column_index: int,
                  auto_adjust_page_width: bool = True) -> Dict[str, Any]:
    """Remove a column from the report table.

    Args:
        filepath: Path to the RDL file
        column_index: Zero-based index of the column to remove
        auto_adjust_page_width: If True (default), shrink the page width to fit
                               the remaining columns plus margins
    """
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    tablix = root.find(f'.//{ns}Tablix')
    if tablix is None:
        return {'success': False, 'message': 'No Tablix found in report'}

    # Get column definitions
    tablix_columns = tablix.find(f'.//{ns}TablixBody/{ns}TablixColumns')
    if tablix_columns is None:
        return {'success': False, 'message': 'No TablixColumns found'}

    columns = tablix_columns.findall(f'{ns}TablixColumn')
    if column_index < 0 or column_index >= len(columns):
        return {'success': False, 'message': f'Invalid column index {column_index}'}

    # Remove column definition
    tablix_columns.remove(columns[column_index])

    # Remove from column hierarchy
    col_hierarchy = tablix.find(f'.//{ns}TablixColumnHierarchy/{ns}TablixMembers')
    if col_hierarchy is not None:
        members = col_hierarchy.findall(f'{ns}TablixMember')
        if column_index < len(members):
            col_hierarchy.remove(members[column_index])

    # Remove cells from each row
    tablix_rows = tablix.findall(f'.//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow')
    for row in tablix_rows:
        cells = row.find(f'{ns}TablixCells')
        if cells is not None:
            cell_list = cells.findall(f'{ns}TablixCell')
            if column_index < len(cell_list):
                cells.remove(cell_list[column_index])

    # Update Tablix width
    tablix_width = _update_tablix_width(tablix, ns)

    # Optionally adjust page width
    if auto_adjust_page_width:
        _update_page_width(root, ns, tablix_width)

    write_xml(tree, filepath)

    return {'success': True, 'message': f'Removed column at index {column_index}'}


def update_column_colors(filepath: str, column_index: int,
                         text_color: Optional[str] = None,
                         background_color: Optional[str] = None,
                         header_text_color: Optional[str] = None,
                         header_background_color: Optional[str] = None) -> Dict[str, Any]:
    """Update text and background colors for a column's data and/or header cells.

    Args:
        filepath: Path to the RDL file
        column_index: Zero-based index of the column to update
        text_color: Text color for data cells (e.g., 'Red', '#FF0000')
        background_color: Background color for data cells
        header_text_color: Text color for header cell
        header_background_color: Background color for header cell
    """
    colors = (text_color, background_color, header_text_color, header_background_color)
    if all(c is None for c in colors):
        return {'success': False, 'message': 'At least one color parameter must be provided'}

    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    tablix = root.find(f'.//{ns}Tablix')
    if tablix is None:
        return {'success': False, 'message': 'No Tablix found in report'}

    tablix_rows = tablix.findall(f'.//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow')

    updated_rows = []

    for row in tablix_rows:
        cells = row.findall(f'{ns}TablixCells/{ns}TablixCell')
        row_type = _detect_row_type(cells, ns)

        if row_type not in ('header', 'data'):
            continue

        if row_type == 'data':
            t_color = text_color
            bg_color = background_color
        else:
            t_color = header_text_color
            bg_color = header_background_color

        if t_color is None and bg_color is None:
            continue

        if column_index >= len(cells):
            return {'success': False, 'message': f'Column index {column_index} out of range'}

        cell = cells[column_index]
        textbox = cell.find(f'.//{ns}Textbox')
        if textbox is None:
            continue

        # Find or create Style element as a direct child of Textbox
        style = textbox.find(f'{ns}Style')
        if style is None:
            style = ET.Element(f'{ns}Style')
            textbox.insert(0, style)

        if t_color is not None:
            color_elem = style.find(f'{ns}Color')
            if color_elem is None:
                color_elem = ET.SubElement(style, f'{ns}Color')
            color_elem.text = t_color

        if bg_color is not None:
            bg_elem = style.find(f'{ns}BackgroundColor')
            if bg_elem is None:
                bg_elem = ET.SubElement(style, f'{ns}BackgroundColor')
            bg_elem.text = bg_color

        updated_rows.append(row_type)

    if not updated_rows:
        return {'success': False, 'message': 'No matching rows found to update'}

    write_xml(tree, filepath)

    parts = []
    if text_color is not None or background_color is not None:
        parts.append('data row colors updated')
    if header_text_color is not None or header_background_color is not None:
        parts.append('header row colors updated')

    return {'success': True, 'message': f'Column {column_index} colors updated: {", ".join(parts)}'}


def update_column_format(filepath: str, column_index: int, format_string: str) -> Dict[str, Any]:
    """Update the format string for a column."""
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    tablix = root.find(f'.//{ns}Tablix')
    if tablix is None:
        return {'success': False, 'message': 'No Tablix found in report'}

    # Find the data row
    tablix_rows = tablix.findall(f'.//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow')

    for row in tablix_rows:
        cells = row.findall(f'{ns}TablixCells/{ns}TablixCell')
        row_type = _detect_row_type(cells, ns)

        if row_type == 'data':
            if column_index >= len(cells):
                return {'success': False, 'message': f'Column index {column_index} out of range'}

            cell = cells[column_index]
            textbox = cell.find(f'.//{ns}Textbox')

            if textbox is None:
                return {'success': False, 'message': f'No textbox found in column {column_index}'}

            # Find or create the Format element in TextRun/Style
            text_run = textbox.find(f'.//{ns}TextRun')
            if text_run is None:
                return {'success': False, 'message': 'No TextRun found in textbox'}

            style = text_run.find(f'{ns}Style')
            if style is None:
                style = ET.SubElement(text_run, f'{ns}Style')

            format_elem = style.find(f'{ns}Format')
            if format_elem is None:
                format_elem = ET.SubElement(style, f'{ns}Format')

            format_elem.text = format_string

            write_xml(tree, filepath)
            return {'success': True, 'message': f'Updated format for column {column_index} to "{format_string}"'}

    return {'success': False, 'message': 'No data row found'}


def update_column_header(filepath: str, old_header: str, new_header: str) -> Dict[str, Any]:
    """Update a column header text."""
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    # Find and update the header
    for value_elem in root.findall(f'.//{ns}Value'):
        if value_elem.text == old_header:
            value_elem.text = new_header
            write_xml(tree, filepath)
            return {'success': True, 'message': f'Updated header from "{old_header}" to "{new_header}"'}

    return {'success': False, 'message': f'Header "{old_header}" not found'}


def update_column_width(filepath: str, column_index: int, new_width: str) -> Dict[str, Any]:
    """Update a column width."""
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    tablix = root.find(f'.//{ns}Tablix')
    if tablix is None:
        return {'success': False, 'message': 'No Tablix found'}

    columns = tablix.findall(f'.//{ns}TablixBody/{ns}TablixColumns/{ns}TablixColumn')

    if column_index < 0 or column_index >= len(columns):
        return {'success': False, 'message': f'Invalid column index {column_index}'}

    width_elem = columns[column_index].find(f'{ns}Width')
    if width_elem is None:
        width_elem = ET.SubElement(columns[column_index], f'{ns}Width')

    width_elem.text = new_width

    # Update total Tablix width
    _update_tablix_width(tablix, ns)

    write_xml(tree, filepath)
    return {'success': True, 'message': f'Updated column {column_index} width to {new_width}'}


def _data_textbox_name(field_binding: str, fallback: str) -> str:
    """Return the field name from a Fields!X.Value expression, or fallback."""
    m = re.search(r'Fields!(\w+)\.Value', field_binding)
    return m.group(1) if m else fallback


def _create_table_cell(ns: str, row_type: str, row_idx: int,
                       col_idx: int, header_text: str, field_binding: str,
                       format_string: Optional[str], footer_expression: Optional[str]) -> ET.Element:
    """Create a new TablixCell element."""
    cell = ET.Element(f'{ns}TablixCell')
    contents = ET.SubElement(cell, f'{ns}CellContents')

    generic_name = f'Textbox_r{row_idx}_c{col_idx}'
    if row_type == 'data':
        textbox_name = _data_textbox_name(field_binding, generic_name)
    else:
        textbox_name = generic_name
    textbox = ET.SubElement(contents, f'{ns}Textbox')
    textbox.set('Name', textbox_name)

    paragraphs = ET.SubElement(textbox, f'{ns}Paragraphs')
    paragraph = ET.SubElement(paragraphs, f'{ns}Paragraph')
    text_runs = ET.SubElement(paragraph, f'{ns}TextRuns')
    text_run = ET.SubElement(text_runs, f'{ns}TextRun')
    value = ET.SubElement(text_run, f'{ns}Value')

    # Set value based on row type
    if row_type == 'header':
        value.text = header_text
    elif row_type == 'data':
        value.text = field_binding
        if format_string:
            style = ET.SubElement(text_run, f'{ns}Style')
            format_elem = ET.SubElement(style, f'{ns}Format')
            format_elem.text = format_string
    elif row_type == 'footer':
        if footer_expression:
            value.text = footer_expression
        else:
            value.text = ''

    return cell


def _parse_dimension(dimension_str: str) -> float:
    """Parse a dimension string (e.g., '2in', '5cm') to inches."""
    if not dimension_str:
        return 0.0
    try:
        if dimension_str.endswith('in'):
            return float(dimension_str[:-2])
        elif dimension_str.endswith('cm'):
            return float(dimension_str[:-2]) / 2.54
        elif dimension_str.endswith('mm'):
            return float(dimension_str[:-2]) / 25.4
        elif dimension_str.endswith('pt'):
            return float(dimension_str[:-2]) / 72.0
        else:
            return float(dimension_str)
    except ValueError:
        return 0.0


def _update_tablix_width(tablix: ET.Element, ns: str) -> float:
    """Recalculate and update the Tablix width based on column widths.

    Returns the calculated total width in inches.
    """
    columns = tablix.findall(f'.//{ns}TablixBody/{ns}TablixColumns/{ns}TablixColumn')

    total_width = 0.0
    for col in columns:
        width_elem = col.find(f'{ns}Width')
        if width_elem is not None and width_elem.text:
            total_width += _parse_dimension(width_elem.text)

    # Update Tablix Width element
    width_elem = tablix.find(f'{ns}Width')
    if width_elem is not None:
        width_elem.text = f'{total_width:.2f}in'

    return total_width


def _update_page_width(root: ET.Element, ns: str, tablix_width: float):
    """Update the page width to fit the tablix plus margins."""
    page = root.find(f'.//{ns}Page')
    if page is None:
        return

    # Get margins
    left_margin_elem = page.find(f'{ns}LeftMargin')
    right_margin_elem = page.find(f'{ns}RightMargin')

    left_margin = _parse_dimension(left_margin_elem.text if left_margin_elem is not None else '0in')
    right_margin = _parse_dimension(right_margin_elem.text if right_margin_elem is not None else '0in')

    # Calculate new page width
    new_page_width = tablix_width + left_margin + right_margin

    # Update PageWidth element
    page_width_elem = page.find(f'{ns}PageWidth')
    if page_width_elem is not None:
        page_width_elem.text = f'{new_page_width:.2f}in'
