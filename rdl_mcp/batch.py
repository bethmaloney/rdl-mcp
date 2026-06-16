"""RDL batch update operations - apply multiple column changes transactionally."""

import copy
import logging
import uuid
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from .reader import _detect_row_type
from .xml_utils import get_namespace, parse_rdl_tree, write_xml
from .columns import _parse_dimension, _update_tablix_width

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_create_textbox_style(textbox: ET.Element, ns: str) -> ET.Element:
    """Return the direct-child Style element of *textbox*, creating if absent."""
    style = textbox.find(f"{ns}Style")
    if style is None:
        style = ET.Element(f"{ns}Style")
        textbox.insert(0, style)
    return style


def _set_style_child(style: ET.Element, ns: str, tag: str, value: str):
    """Set (or create) a child element *tag* under *style* to *value*."""
    elem = style.find(tag)
    if elem is None:
        elem = ET.SubElement(style, tag)
    elem.text = value


def _get_textbox_color_props(textbox: ET.Element, ns: str) -> Dict[str, Optional[str]]:
    """Return current color + alignment props from a Textbox's Style."""
    style = textbox.find(f"{ns}Style")
    if style is None:
        return {}
    result: Dict[str, Optional[str]] = {}
    for tag, key in (
        (f"{ns}Color", "text_color"),
        (f"{ns}BackgroundColor", "background_color"),
        (f"{ns}TextAlign", "alignment"),
    ):
        elem = style.find(tag)
        if elem is not None and elem.text:
            result[key] = elem.text
    return result


def _get_textrun_format(textbox: ET.Element, ns: str) -> Optional[str]:
    fmt_elem = textbox.find(f".//{ns}TextRun/{ns}Style/{ns}Format")
    return fmt_elem.text if fmt_elem is not None and fmt_elem.text else None


def _get_column_width(tablix: ET.Element, ns: str, col_idx: int) -> Optional[str]:
    cols = tablix.findall(f".//{ns}TablixBody/{ns}TablixColumns/{ns}TablixColumn")
    if col_idx < len(cols):
        w = cols[col_idx].find(f"{ns}Width")
        return w.text if w is not None else None
    return None


def _get_column_header(tablix: ET.Element, ns: str, col_idx: int) -> Optional[str]:
    for row in tablix.findall(f".//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow"):
        cells = row.findall(f"{ns}TablixCells/{ns}TablixCell")
        if _detect_row_type(cells, ns) == "header":
            if col_idx < len(cells):
                v = cells[col_idx].find(f".//{ns}Value")
                return v.text if v is not None else None
    return None


def _snapshot_column(tablix: ET.Element, ns: str, col_idx: int) -> Dict[str, Any]:
    """Capture current state of a column for diff generation."""
    snap: Dict[str, Any] = {
        "width": _get_column_width(tablix, ns, col_idx),
        "header": _get_column_header(tablix, ns, col_idx),
    }
    for row in tablix.findall(f".//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow"):
        cells = row.findall(f"{ns}TablixCells/{ns}TablixCell")
        rt = _detect_row_type(cells, ns)
        if rt not in ("header", "data"):
            continue
        if col_idx >= len(cells):
            continue
        tb = cells[col_idx].find(f".//{ns}Textbox")
        if tb is None:
            continue
        prefix = "header_" if rt == "header" else ""
        for prop, val in _get_textbox_color_props(tb, ns).items():
            snap[f"{prefix}{prop}"] = val
        if rt == "data":
            fmt = _get_textrun_format(tb, ns)
            if fmt:
                snap["format"] = fmt
    return snap


def _apply_single_update(tablix: ET.Element, ns: str, update: Dict[str, Any]) -> List[str]:
    """Apply one column-update dict to *tablix* in-memory.

    Returns a list of human-readable error strings (empty means success).
    """
    errors: List[str] = []
    col_idx: int = update["column_index"]

    # --- width ---
    if "width" in update and update["width"] is not None:
        cols = tablix.findall(f".//{ns}TablixBody/{ns}TablixColumns/{ns}TablixColumn")
        if col_idx < 0 or col_idx >= len(cols):
            errors.append(f"Column index {col_idx} out of range for width update")
        else:
            w = cols[col_idx].find(f"{ns}Width")
            if w is None:
                w = ET.SubElement(cols[col_idx], f"{ns}Width")
            w.text = update["width"]

    # --- header + cell colors/alignment per row type ---
    for row in tablix.findall(f".//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow"):
        cells = row.findall(f"{ns}TablixCells/{ns}TablixCell")
        rt = _detect_row_type(cells, ns)
        if rt not in ("header", "data"):
            continue
        if col_idx >= len(cells):
            errors.append(f"Column index {col_idx} out of range for row type '{rt}'")
            continue
        tb = cells[col_idx].find(f".//{ns}Textbox")
        if tb is None:
            continue

        if rt == "header":
            # update header text
            if "header" in update and update["header"] is not None:
                v = tb.find(f".//{ns}Value")
                if v is not None:
                    v.text = update["header"]
            # header colors
            style = _get_or_create_textbox_style(tb, ns)
            if "header_text_color" in update and update["header_text_color"] is not None:
                _set_style_child(style, ns, f"{ns}Color", update["header_text_color"])
            if "header_background_color" in update and update["header_background_color"] is not None:
                _set_style_child(style, ns, f"{ns}BackgroundColor", update["header_background_color"])
            if "header_alignment" in update and update["header_alignment"] is not None:
                _set_style_child(style, ns, f"{ns}TextAlign", update["header_alignment"])

        elif rt == "data":
            style = _get_or_create_textbox_style(tb, ns)
            if "text_color" in update and update["text_color"] is not None:
                _set_style_child(style, ns, f"{ns}Color", update["text_color"])
            if "background_color" in update and update["background_color"] is not None:
                _set_style_child(style, ns, f"{ns}BackgroundColor", update["background_color"])
            if "alignment" in update and update["alignment"] is not None:
                _set_style_child(style, ns, f"{ns}TextAlign", update["alignment"])
            # format_string goes in TextRun/Style/Format
            if "format_string" in update and update["format_string"] is not None:
                text_run = tb.find(f".//{ns}TextRun")
                if text_run is None:
                    errors.append(f"No TextRun found in column {col_idx} data cell")
                    continue
                tr_style = text_run.find(f"{ns}Style")
                if tr_style is None:
                    tr_style = ET.SubElement(text_run, f"{ns}Style")
                fmt_elem = tr_style.find(f"{ns}Format")
                if fmt_elem is None:
                    fmt_elem = ET.SubElement(tr_style, f"{ns}Format")
                fmt_elem.text = update["format_string"]

    return errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def update_table_batch(
    filepath: str,
    updates: List[Dict[str, Any]],
    backup: bool = False,
) -> Dict[str, Any]:
    """Apply multiple column updates transactionally in a single write.

    All updates are applied in-memory first.  If any update produces an error
    the entire operation is aborted (all-or-none) and the file is not written.
    On success the file is written atomically (temp-validate-replace).

    Args:
        filepath: Path to the RDL file.
        updates: List of column-update dicts.  Each dict must contain
                 ``column_index`` (int) plus any of:
                 ``width``, ``header``, ``format_string``,
                 ``text_color``, ``background_color``,
                 ``header_text_color``, ``header_background_color``,
                 ``alignment`` (data cell), ``header_alignment`` (header cell).
        backup:  When True, save a timestamped ``.bak`` copy before writing.

    Returns:
        Mutation-response envelope with keys:
        ``success``, ``mutation_id``, ``diff``, ``integrity_checks``,
        ``backup_path``, ``message``.
    """
    mutation_id = str(uuid.uuid4())

    if not updates:
        return {
            "success": False,
            "mutation_id": mutation_id,
            "message": "No updates provided",
            "diff": [],
        }

    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    tablix = root.find(f".//{ns}Tablix")
    if tablix is None:
        return {
            "success": False,
            "mutation_id": mutation_id,
            "message": "No Tablix found in report",
            "error_code": "INVALID_RDL_SCHEMA",
            "diff": [],
        }

    # Capture before-state for diff
    col_indices = list({u["column_index"] for u in updates if "column_index" in u})
    before_state = {idx: _snapshot_column(tablix, ns, idx) for idx in col_indices}

    # Validate all updates before touching the tree (all-or-none)
    cols_count = len(tablix.findall(f".//{ns}TablixBody/{ns}TablixColumns/{ns}TablixColumn"))
    pre_errors: List[str] = []
    for u in updates:
        if "column_index" not in u:
            pre_errors.append("Update missing required 'column_index' field")
            continue
        idx = u["column_index"]
        if not isinstance(idx, int) or idx < 0 or idx >= cols_count:
            pre_errors.append(
                f"column_index {idx} is out of range (report has {cols_count} columns)"
            )

    if pre_errors:
        return {
            "success": False,
            "mutation_id": mutation_id,
            "message": "; ".join(pre_errors),
            "error_code": "COLUMN_NOT_FOUND",
            "diff": [],
        }

    # Apply all updates in-memory
    all_errors: List[str] = []
    for u in updates:
        errs = _apply_single_update(tablix, ns, u)
        all_errors.extend(errs)

    if all_errors:
        # Abort – do NOT write; return fresh (unmodified) tree to GC
        return {
            "success": False,
            "mutation_id": mutation_id,
            "message": "; ".join(all_errors),
            "error_code": "INVALID_RDL_SCHEMA",
            "diff": [],
        }

    # Recalculate Tablix width after width changes
    _update_tablix_width(tablix, ns)

    # Atomic write with optional backup
    try:
        backup_path = write_xml(tree, filepath, backup=backup)
    except OSError as exc:
        return {
            "success": False,
            "mutation_id": mutation_id,
            "message": f"Write failed: {exc}",
            "error_code": "WRITE_FAILURE",
            "diff": [],
        }

    # Capture after-state for diff
    after_tree = parse_rdl_tree(filepath)
    after_root = after_tree.getroot()
    after_tablix = after_root.find(f".//{ns}Tablix")
    diff = []
    for idx in sorted(col_indices):
        after_snap = _snapshot_column(after_tablix, ns, idx) if after_tablix is not None else {}
        before_snap = before_state[idx]
        changes: Dict[str, Any] = {}
        all_keys = set(before_snap) | set(after_snap)
        for key in all_keys:
            bv = before_snap.get(key)
            av = after_snap.get(key)
            if bv != av:
                changes[key] = {"before": bv, "after": av}
        if changes:
            diff.append({"column_index": idx, "changes": changes})

    return {
        "success": True,
        "mutation_id": mutation_id,
        "message": f"Applied {len(updates)} update(s) across {len(col_indices)} column(s)",
        "diff": diff,
        "integrity_checks": {"xml_valid": True},
        "backup_path": backup_path,
    }


def preview_table_batch(
    filepath: str,
    updates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Preview what *update_table_batch* would do without writing any changes.

    Returns the same diff structure as ``update_table_batch`` but with
    ``dry_run: true`` and no file modification.
    """
    mutation_id = str(uuid.uuid4())

    if not updates:
        return {
            "dry_run": True,
            "mutation_id": mutation_id,
            "message": "No updates provided",
            "diff": [],
        }

    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    tablix = root.find(f".//{ns}Tablix")
    if tablix is None:
        return {
            "dry_run": True,
            "mutation_id": mutation_id,
            "message": "No Tablix found in report",
            "error_code": "INVALID_RDL_SCHEMA",
            "diff": [],
        }

    cols_count = len(tablix.findall(f".//{ns}TablixBody/{ns}TablixColumns/{ns}TablixColumn"))
    col_indices = list({u["column_index"] for u in updates if "column_index" in u})

    # Validate indices
    pre_errors: List[str] = []
    for u in updates:
        if "column_index" not in u:
            pre_errors.append("Update missing required 'column_index' field")
            continue
        idx = u["column_index"]
        if not isinstance(idx, int) or idx < 0 or idx >= cols_count:
            pre_errors.append(
                f"column_index {idx} is out of range (report has {cols_count} columns)"
            )
    if pre_errors:
        return {
            "dry_run": True,
            "mutation_id": mutation_id,
            "message": "; ".join(pre_errors),
            "error_code": "COLUMN_NOT_FOUND",
            "diff": [],
        }

    # Deep-copy the tablix so we can apply changes without touching the real tree
    tablix_copy = copy.deepcopy(tablix)
    before_state = {idx: _snapshot_column(tablix_copy, ns, idx) for idx in col_indices}

    all_errors: List[str] = []
    for u in updates:
        errs = _apply_single_update(tablix_copy, ns, u)
        all_errors.extend(errs)

    if all_errors:
        return {
            "dry_run": True,
            "mutation_id": mutation_id,
            "message": "; ".join(all_errors),
            "error_code": "INVALID_RDL_SCHEMA",
            "diff": [],
        }

    # Build diff from the copied tree
    diff = []
    for idx in sorted(col_indices):
        after_snap = _snapshot_column(tablix_copy, ns, idx)
        before_snap = before_state[idx]
        changes: Dict[str, Any] = {}
        all_keys = set(before_snap) | set(after_snap)
        for key in all_keys:
            bv = before_snap.get(key)
            av = after_snap.get(key)
            if bv != av:
                changes[key] = {"before": bv, "after": av}
        if changes:
            diff.append({"column_index": idx, "changes": changes})

    return {
        "dry_run": True,
        "mutation_id": mutation_id,
        "message": f"Preview: {len(updates)} update(s) across {len(col_indices)} column(s) — file NOT modified",
        "diff": diff,
    }
