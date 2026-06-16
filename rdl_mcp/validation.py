"""RDL validation logic and expression parsing."""

import xml.etree.ElementTree as ET
import defusedxml.ElementTree as SafeET
import re
import logging
from typing import Dict, List, Any, Optional

from .xml_utils import get_namespace, find_parent, validate_filepath

logger = logging.getLogger(__name__)


def extract_field_references_with_context(expression: str, default_dataset: str) -> Dict[str, List[str]]:
    """Extract field names from an RDL expression, grouped by their dataset context.

    Handles patterns like:
    - =Fields!FieldName.Value -> default_dataset
    - =Sum(Fields!FieldName.Value) -> default_dataset
    - =Lookup(Fields!Key.Value, Fields!Key2.Value, Fields!Result.Value, "OtherDataset")
      -> Key belongs to default_dataset, Key2 and Result belong to "OtherDataset"
    - =First(Fields!Field.Value, "OtherDataset") -> Field belongs to "OtherDataset"
    - =Sum(Fields!Field.Value, "OtherDataset") -> Field belongs to "OtherDataset"

    Returns:
        Dict mapping dataset name to list of field names referenced from that dataset.
    """
    if not expression or not expression.strip().startswith('='):
        return {}

    result: Dict[str, List[str]] = {}
    handled_positions: set = set()

    # 1. Handle Lookup/LookupSet/MultiLookup functions
    lookup_pattern = r'(Lookup|LookupSet|MultiLookup)\s*\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*"([^"]+)"\s*\)'

    for match in re.finditer(lookup_pattern, expression, re.IGNORECASE):
        source_expr = match.group(2)
        dest_expr = match.group(3)
        result_expr = match.group(4)
        target_dataset = match.group(5)

        # Source expression fields belong to the default dataset
        source_start = match.start(2)
        for field_match in re.finditer(r'Fields!(\w+)', source_expr):
            field = field_match.group(1)
            pos = source_start + field_match.start()
            handled_positions.add(pos)
            if default_dataset not in result:
                result[default_dataset] = []
            if field not in result[default_dataset]:
                result[default_dataset].append(field)

        # Dest and result expression fields belong to the target dataset
        dest_start = match.start(3)
        result_start = match.start(4)
        for field_match in re.finditer(r'Fields!(\w+)', dest_expr):
            field = field_match.group(1)
            pos = dest_start + field_match.start()
            handled_positions.add(pos)
            if target_dataset not in result:
                result[target_dataset] = []
            if field not in result[target_dataset]:
                result[target_dataset].append(field)

        for field_match in re.finditer(r'Fields!(\w+)', result_expr):
            field = field_match.group(1)
            pos = result_start + field_match.start()
            handled_positions.add(pos)
            if target_dataset not in result:
                result[target_dataset] = []
            if field not in result[target_dataset]:
                result[target_dataset].append(field)

    # 2. Handle aggregate functions with dataset scope
    aggregate_pattern = r'(Sum|Count|First|Last|Min|Max|Avg|CountDistinct|StDev|StDevP|Var|VarP|CountRows|RunningValue|Previous)\s*\(\s*([^,)]+?)(?:\s*,\s*"([^"]+)")?\s*\)'

    for match in re.finditer(aggregate_pattern, expression, re.IGNORECASE):
        field_expr = match.group(2)
        scope_dataset = match.group(3)

        target_ds = scope_dataset if scope_dataset else default_dataset

        expr_start = match.start(2)
        for field_match in re.finditer(r'Fields!(\w+)', field_expr):
            field = field_match.group(1)
            pos = expr_start + field_match.start()

            if pos in handled_positions:
                continue

            handled_positions.add(pos)
            if target_ds not in result:
                result[target_ds] = []
            if field not in result[target_ds]:
                result[target_ds].append(field)

    # 3. Find all other field references that haven't been handled
    for match in re.finditer(r'Fields!(\w+)', expression):
        if match.start() in handled_positions:
            continue

        field = match.group(1)
        if default_dataset not in result:
            result[default_dataset] = []
        if field not in result[default_dataset]:
            result[default_dataset].append(field)

    return result


def extract_field_references(expression: str) -> List[str]:
    """Extract all field names referenced in an RDL expression (without dataset context)."""
    if not expression or not expression.strip().startswith('='):
        return []

    pattern = r'Fields!(\w+)'
    matches = re.findall(pattern, expression)
    return list(set(matches))


def validate_rdl(filepath: str) -> Dict[str, Any]:
    """Validate RDL XML structure and field references in expressions."""
    try:
        resolved = validate_filepath(filepath)
        tree = SafeET.parse(resolved)
        root = tree.getroot()
        ns = get_namespace(root)

        issues = []
        warnings = []

        # Check for datasets and build field map
        datasets = root.findall(f'.//{ns}DataSet')
        if not datasets:
            issues.append('No datasets found')
            return {'valid': False, 'issues': issues}

        # Build a map of dataset name -> set of field names
        dataset_fields: Dict[str, set] = {}
        for dataset in datasets:
            name = dataset.get('Name', 'Unknown')
            query = dataset.find(f'{ns}Query')
            if query is None:
                fields = dataset.findall(f'.//{ns}Field')
                if not fields:
                    issues.append(f'Dataset "{name}" has no Query element and no Fields')

            field_names = set()
            for field in dataset.findall(f'.//{ns}Field'):
                field_name = field.get('Name')
                if field_name:
                    field_names.add(field_name)
            dataset_fields[name] = field_names

        # Check for at least one Tablix
        tablixes = root.findall(f'.//{ns}Tablix')
        if not tablixes:
            issues.append('No Tablix (table) found')

        # Validate field references in each Tablix
        for tablix in tablixes:
            tablix_name = tablix.get('Name', 'Unknown')
            dataset_name_elem = tablix.find(f'{ns}DataSetName')

            if dataset_name_elem is None or not dataset_name_elem.text:
                warnings.append(f'Tablix "{tablix_name}" has no DataSetName specified')
                continue

            dataset_name = dataset_name_elem.text

            if dataset_name not in dataset_fields:
                issues.append(f'Tablix "{tablix_name}" references unknown dataset "{dataset_name}"')
                continue

            invalid_refs: List[Dict[str, Any]] = []

            def validate_expression(expression: str, location: str):
                """Validate field references in an expression."""
                if not expression:
                    return

                fields_by_dataset = extract_field_references_with_context(expression, dataset_name)

                for ref_dataset, fields in fields_by_dataset.items():
                    if ref_dataset not in dataset_fields:
                        for field_name in fields:
                            invalid_refs.append({
                                'field': field_name,
                                'expression': expression[:100] + ('...' if len(expression) > 100 else ''),
                                'location': location,
                                'dataset': ref_dataset,
                                'error': f'references unknown dataset "{ref_dataset}"'
                            })
                    else:
                        valid_fields_for_dataset = dataset_fields[ref_dataset]
                        for field_name in fields:
                            if field_name not in valid_fields_for_dataset:
                                invalid_refs.append({
                                    'field': field_name,
                                    'expression': expression[:100] + ('...' if len(expression) > 100 else ''),
                                    'location': location,
                                    'dataset': ref_dataset
                                })

            processed_value_ids = set()

            # Check GroupExpressions
            for group_expr in tablix.findall(f'.//{ns}GroupExpression'):
                validate_expression(group_expr.text, 'GroupExpression')

            # Check SortExpressions
            for sort_expr in tablix.findall(f'.//{ns}SortExpression/{ns}Value'):
                processed_value_ids.add(id(sort_expr))
                validate_expression(sort_expr.text, 'SortExpression')

            # Check all Value elements
            for value_elem in tablix.findall(f'.//{ns}Value'):
                if id(value_elem) in processed_value_ids:
                    continue

                expression = value_elem.text
                if expression and expression.strip().startswith('='):
                    parent = value_elem
                    textbox_name = None
                    for _ in range(10):
                        parent = find_parent(tablix, parent)
                        if parent is None:
                            break
                        if parent.tag == f'{ns}Textbox':
                            textbox_name = parent.get('Name')
                            break

                    validate_expression(expression, textbox_name or 'unknown location')

            # Deduplicate invalid refs
            seen_field_dataset = set()
            unique_invalid_refs = []
            for ref in invalid_refs:
                key = (ref['field'], ref.get('dataset', dataset_name))
                if key not in seen_field_dataset:
                    seen_field_dataset.add(key)
                    unique_invalid_refs.append(ref)

            # Add issues for invalid field references
            for ref in unique_invalid_refs:
                location = ref.get('location') or 'unknown location'
                ref_dataset = ref.get('dataset', dataset_name)

                if ref_dataset in dataset_fields:
                    available = dataset_fields[ref_dataset]
                    available_str = f'Available fields: {", ".join(sorted(available)[:10])}{"..." if len(available) > 10 else ""}'
                else:
                    available_str = f'Dataset "{ref_dataset}" does not exist'

                if ref.get('error'):
                    issues.append(
                        f'Tablix "{tablix_name}": Expression {ref["error"]} '
                        f'(field "{ref["field"]}" in {location})'
                    )
                else:
                    issues.append(
                        f'Tablix "{tablix_name}": Field "{ref["field"]}" not found in dataset "{ref_dataset}" '
                        f'(referenced in {location}). {available_str}'
                    )

        if issues:
            result = {'valid': False, 'issues': issues}
        else:
            result = {'valid': True, 'message': 'RDL structure is valid'}

        if warnings:
            result['warnings'] = warnings

        return result

    except ET.ParseError as e:
        return {'valid': False, 'issues': [f'XML Parse Error: {str(e)}']}
    except Exception as e:
        return {'valid': False, 'issues': [f'Error: {str(e)}']}
