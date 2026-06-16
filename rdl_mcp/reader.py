"""RDL read operations - describe, get datasets, parameters, columns."""

import xml.etree.ElementTree as ET
import re
import logging
from typing import Dict, List, Any, Optional

from .xml_utils import parse_rdl, get_namespace

logger = logging.getLogger(__name__)


def describe_rdl_report(filepath: str) -> Dict[str, Any]:
    """Get a high-level summary of the report structure."""
    logger.info(f"Describing RDL report: {filepath}")

    root = parse_rdl(filepath)
    ns = get_namespace(root)

    # Count datasets
    datasets = []
    for dataset in root.findall(f'.//{ns}DataSet'):
        name = dataset.get('Name')
        query = dataset.find(f'{ns}Query')

        if query is not None:
            command_type = query.find(f'{ns}CommandType')
            command_text = query.find(f'{ns}CommandText')
            ds_info = {
                'name': name,
                'command_type': command_type.text if command_type is not None else 'Unknown',
                'command': command_text.text if command_text is not None else ''
            }
        else:
            ds_info = {
                'name': name,
                'command_type': 'Embedded',
                'command': ''
            }

        # Count fields
        fields = dataset.findall(f'.//{ns}Field')
        ds_info['field_count'] = len(fields)
        datasets.append(ds_info)

    # Count parameters
    parameters = root.findall(f'.//{ns}ReportParameter')
    param_count = len(parameters)

    # Count table columns
    tablix = root.find(f'.//{ns}Tablix')
    column_count = 0
    if tablix is not None:
        columns = tablix.findall(f'.//{ns}TablixColumn')
        column_count = len(columns)

    logger.info(f"Report summary: {len(datasets)} datasets, {param_count} parameters, {column_count} columns")

    return {
        'report_summary': {
            'datasets': len(datasets),
            'parameters': param_count,
            'table_columns': column_count
        },
        'datasets': datasets,
        'filepath': filepath
    }


def get_rdl_datasets(filepath: str, field_limit: int = 0, field_pattern: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed dataset information.

    Args:
        filepath: Path to the RDL file
        field_limit: Number of fields to return per dataset.
                    0 = no field details (only count),
                    -1 = all fields,
                    positive number = limit to that many fields
        field_pattern: Optional regex pattern to filter field names
    """
    root = parse_rdl(filepath)
    ns = get_namespace(root)

    datasets = []
    for dataset in root.findall(f'.//{ns}DataSet'):
        name = dataset.get('Name')
        query = dataset.find(f'{ns}Query')

        if query is not None:
            command_type = query.find(f'{ns}CommandType').text if query.find(f'{ns}CommandType') is not None else 'Unknown'
            command_text = query.find(f'{ns}CommandText').text if query.find(f'{ns}CommandText') is not None else ''
            datasource = query.find(f'{ns}DataSourceName').text if query.find(f'{ns}DataSourceName') is not None else ''

            query_params = []
            for qparam in query.findall(f'.//{ns}QueryParameter'):
                query_params.append({
                    'name': qparam.get('Name'),
                    'value': qparam.find(f'{ns}Value').text if qparam.find(f'{ns}Value') is not None else ''
                })
        else:
            command_type = 'Embedded'
            command_text = ''
            datasource = ''
            query_params = []
            logger.debug(f"Dataset '{name}' has no Query element (embedded dataset)")

        # Get all fields
        all_fields = []
        for field in dataset.findall(f'.//{ns}Field'):
            field_name = field.get('Name')
            data_field = field.find(f'{ns}DataField').text if field.find(f'{ns}DataField') is not None else ''
            rd_ns = '{http://schemas.microsoft.com/SQLServer/reporting/reportdesigner}'
            type_name_elem = field.find(f'.//{rd_ns}TypeName')
            type_name = type_name_elem.text if type_name_elem is not None else 'Unknown'

            all_fields.append({
                'name': field_name,
                'data_field': data_field,
                'type': type_name
            })

        # Apply field pattern filter
        if field_pattern:
            try:
                # Limit pattern length to prevent ReDoS (CWE-1333)
                if len(field_pattern) > 200:
                    logger.warning("field_pattern too long, ignoring")
                    filtered_fields = all_fields
                else:
                    pattern_re = re.compile(field_pattern, re.IGNORECASE)
                    filtered_fields = [f for f in all_fields if pattern_re.search(f['name'])]
            except re.error as e:
                logger.warning(f"Invalid field_pattern regex, error: {e}")
                filtered_fields = all_fields
        else:
            filtered_fields = all_fields

        dataset_info = {
            'name': name,
            'datasource': datasource,
            'command_type': command_type,
            'command_text': command_text,
            'query_parameters': query_params,
            'field_count': len(all_fields)
        }

        if field_limit != 0:
            if field_limit == -1:
                dataset_info['fields'] = filtered_fields
                dataset_info['fields_truncated'] = False
            else:
                dataset_info['fields'] = filtered_fields[:field_limit]
                dataset_info['fields_truncated'] = len(filtered_fields) > field_limit

        datasets.append(dataset_info)

    return {'datasets': datasets}


def get_rdl_parameters(filepath: str) -> Dict[str, Any]:
    """Get report parameters."""
    root = parse_rdl(filepath)
    ns = get_namespace(root)

    parameters = []
    for param in root.findall(f'.//{ns}ReportParameter'):
        name = param.get('Name')
        data_type = param.find(f'{ns}DataType').text if param.find(f'{ns}DataType') is not None else 'Unknown'
        prompt = param.find(f'{ns}Prompt').text if param.find(f'{ns}Prompt') is not None else ''

        param_info = {
            'name': name,
            'data_type': data_type,
            'prompt': prompt
        }

        # Check for default value
        default_values = param.find(f'{ns}DefaultValue')
        if default_values is not None:
            values = default_values.findall(f'{ns}Values/{ns}Value')
            if values:
                param_info['default_values'] = [v.text for v in values if v.text]

        # Check for valid values
        valid_values = param.find(f'{ns}ValidValues')
        if valid_values is not None:
            # Check for DataSetReference (dropdown from query)
            ds_ref = valid_values.find(f'{ns}DataSetReference')
            if ds_ref is not None:
                param_info['valid_values_dataset'] = ds_ref.find(f'{ns}DataSetName').text if ds_ref.find(f'{ns}DataSetName') is not None else ''

            # Check for static ParameterValues
            param_values = valid_values.findall(f'{ns}ParameterValues/{ns}ParameterValue')
            if param_values:
                param_info['valid_values'] = []
                for pv in param_values:
                    value = pv.find(f'{ns}Value').text if pv.find(f'{ns}Value') is not None else ''
                    label = pv.find(f'{ns}Label').text if pv.find(f'{ns}Label') is not None else value
                    param_info['valid_values'].append({'value': value, 'label': label})

        parameters.append(param_info)

    return {'parameters': parameters}


def get_rdl_columns(filepath: str) -> Dict[str, Any]:
    """Get table columns with their headers, widths, field bindings, and formatting.

    Each column entry includes:
      - header_textbox_name: Name attribute of the header-row Textbox (used for report styling/layout)
      - data_textbox_name:   Name attribute of the data-row Textbox (used by SSRS as the CSV/text export column header)
    These names differ — callers looking up a textbox in the XML should use the appropriate one.
    """
    root = parse_rdl(filepath)
    ns = get_namespace(root)

    tablix = root.find(f'.//{ns}Tablix')
    if tablix is None:
        return {'columns': [], 'error': 'No Tablix found'}

    # Get column widths
    tablix_columns = tablix.findall(f'.//{ns}TablixColumns/{ns}TablixColumn')
    widths = []
    for col in tablix_columns:
        width = col.find(f'{ns}Width')
        widths.append(width.text if width is not None else '')

    # Find all rows
    tablix_rows = tablix.findall(f'.//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow')

    # Detect row types
    header_row = None
    data_row = None
    footer_row = None

    for row_idx, row in enumerate(tablix_rows):
        cells = row.findall(f'{ns}TablixCells/{ns}TablixCell')
        row_type = _detect_row_type(cells, ns)

        if row_type == 'header' and header_row is None:
            header_row = row
        elif row_type == 'data' and data_row is None:
            data_row = row
        elif row_type == 'footer' and footer_row is None:
            footer_row = row

    columns = []

    # Get header text
    if header_row is not None:
        header_cells = header_row.findall(f'{ns}TablixCells/{ns}TablixCell')
        for col_idx, cell in enumerate(header_cells):
            textbox = cell.find(f'.//{ns}Textbox')
            header_text = ''
            header_textbox_name = ''

            if textbox is not None:
                header_textbox_name = textbox.get('Name', '')
                value = textbox.find(f'.//{ns}Value')
                if value is not None and value.text:
                    header_text = value.text
                    if header_text.startswith('='):
                        if 'Fields!' in header_text:
                            try:
                                field_name_extracted = header_text.split('Fields!')[1].split('.')[0].split(')')[0]
                                header_text = field_name_extracted
                            except IndexError:
                                pass

            columns.append({
                'index': col_idx,
                'header': header_text,
                'width': widths[col_idx] if col_idx < len(widths) else '',
                'header_textbox_name': header_textbox_name
            })

    # Get data bindings
    if data_row is not None:
        data_cells = data_row.findall(f'{ns}TablixCells/{ns}TablixCell')
        for col_idx, cell in enumerate(data_cells):
            if col_idx < len(columns):
                textbox = cell.find(f'.//{ns}Textbox')
                if textbox is not None:
                    columns[col_idx]['data_textbox_name'] = textbox.get('Name', '')
                    value = textbox.find(f'.//{ns}Value')
                    if value is not None and value.text:
                        binding = value.text
                        columns[col_idx]['field_binding'] = binding
                        if binding.startswith('=') and 'Fields!' in binding:
                            try:
                                field_name = binding.split('Fields!')[1].split('.')[0]
                                columns[col_idx]['field_name'] = field_name
                            except IndexError:
                                pass

                    # Get format
                    format_elem = textbox.find(f'.//{ns}Format')
                    if format_elem is not None and format_elem.text:
                        columns[col_idx]['format'] = format_elem.text

    return {'columns': columns}


def _detect_row_type(cells: List[ET.Element], ns: str) -> str:
    """Detect if a row is a header, data, or footer row."""
    static_count = 0
    data_binding_count = 0
    aggregate_count = 0

    for cell in cells:
        textbox = cell.find(f'.//{ns}Textbox')
        if textbox is not None:
            value = textbox.find(f'.//{ns}Value')
            if value is not None and value.text:
                text = value.text.strip()
                if text.startswith('='):
                    if any(func in text for func in ['Sum(', 'Count(', 'Avg(', 'Min(', 'Max(', 'First(']):
                        aggregate_count += 1
                    else:
                        data_binding_count += 1
                else:
                    static_count += 1

    total = static_count + data_binding_count + aggregate_count
    if total == 0:
        return 'empty'

    if aggregate_count > 0 and aggregate_count >= data_binding_count:
        return 'footer'
    if static_count > data_binding_count:
        return 'header'
    return 'data'
