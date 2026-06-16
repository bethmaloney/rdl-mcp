"""RDL style and layout read operations."""

import logging
from typing import Any, Dict, List, Optional

from .reader import _detect_row_type
from .xml_utils import get_namespace, parse_rdl
from .columns import _parse_dimension

logger = logging.getLogger(__name__)


def _get_textbox_style(textbox, ns: str) -> Dict[str, Optional[str]]:
    """Extract color/alignment properties from a Textbox's Style element."""
    style = textbox.find(f"{ns}Style")
    if style is None:
        return {}
    result: Dict[str, Optional[str]] = {}
    for tag, key in (
        (f"{ns}Color", "text_color"),
        (f"{ns}BackgroundColor", "background_color"),
        (f"{ns}TextAlign", "alignment"),
        (f"{ns}FontWeight", "font_weight"),
        (f"{ns}FontSize", "font_size"),
        (f"{ns}FontFamily", "font_family"),
    ):
        elem = style.find(tag)
        if elem is not None and elem.text:
            result[key] = elem.text
    return result


def _get_textrun_format(textbox, ns: str) -> Optional[str]:
    """Return the Format string from the first TextRun in *textbox*, if any."""
    fmt = textbox.find(f".//{ns}TextRun/{ns}Style/{ns}Format")
    return fmt.text if fmt is not None and fmt.text else None


def get_column_styles(filepath: str) -> Dict[str, Any]:
    """Return effective style properties for every column in the Tablix.

    For each column the response includes header and data cell properties:
    text_color, background_color, alignment, format, font_weight,
    font_size, font_family.
    """
    root = parse_rdl(filepath)
    ns = get_namespace(root)

    tablix = root.find(f".//{ns}Tablix")
    if tablix is None:
        return {"columns": [], "error": "No Tablix found"}

    # widths
    tablix_cols = tablix.findall(f".//{ns}TablixColumns/{ns}TablixColumn")
    widths: List[str] = []
    for col in tablix_cols:
        w = col.find(f"{ns}Width")
        widths.append(w.text if w is not None else "")

    # rows
    tablix_rows = tablix.findall(f".//{ns}TablixBody/{ns}TablixRows/{ns}TablixRow")
    header_cells: List = []
    data_cells: List = []

    for row in tablix_rows:
        cells = row.findall(f"{ns}TablixCells/{ns}TablixCell")
        rt = _detect_row_type(cells, ns)
        if rt == "header" and not header_cells:
            header_cells = cells
        elif rt == "data" and not data_cells:
            data_cells = cells

    num_cols = max(len(widths), len(header_cells), len(data_cells))
    columns = []
    for idx in range(num_cols):
        col_info: Dict[str, Any] = {
            "index": idx,
            "width": widths[idx] if idx < len(widths) else "",
            "header": {},
            "data": {},
        }

        if idx < len(header_cells):
            tb = header_cells[idx].find(f".//{ns}Textbox")
            if tb is not None:
                col_info["header"] = _get_textbox_style(tb, ns)

        if idx < len(data_cells):
            tb = data_cells[idx].find(f".//{ns}Textbox")
            if tb is not None:
                col_info["data"] = _get_textbox_style(tb, ns)
                fmt = _get_textrun_format(tb, ns)
                if fmt:
                    col_info["data"]["format"] = fmt

        columns.append(col_info)

    return {"columns": columns}


def get_table_styles(filepath: str) -> Dict[str, Any]:
    """Return table-level style properties (border, background, font defaults).

    Reads the Style element directly on the Tablix element, if present.
    """
    root = parse_rdl(filepath)
    ns = get_namespace(root)

    tablix = root.find(f".//{ns}Tablix")
    if tablix is None:
        return {"table_styles": {}, "error": "No Tablix found"}

    tablix_name = tablix.get("Name", "")
    style = tablix.find(f"{ns}Style")
    table_style: Dict[str, Any] = {}

    if style is not None:
        for tag, key in (
            (f"{ns}Color", "text_color"),
            (f"{ns}BackgroundColor", "background_color"),
            (f"{ns}FontWeight", "font_weight"),
            (f"{ns}FontSize", "font_size"),
            (f"{ns}FontFamily", "font_family"),
            (f"{ns}Border", "border"),
        ):
            elem = style.find(tag)
            if elem is not None and elem.text:
                table_style[key] = elem.text

    return {"table_name": tablix_name, "table_styles": table_style}


def _page_dim(page, tag: str, ns: str) -> float:
    """Helper: parse a page dimension element, returning 0.0 if absent."""
    elem = page.find(tag) if page is not None else None
    return _parse_dimension(elem.text) if (elem is not None and elem.text) else 0.0


def get_layout_diagnostics(filepath: str) -> Dict[str, Any]:
    """Return layout diagnostics for the report.

    Includes:
    - page_width, page_height
    - left_margin, right_margin, top_margin, bottom_margin
    - printable_width  (page_width - left_margin - right_margin)
    - tablix_width     (sum of all column widths)
    - tablix_fits      (tablix_width <= printable_width)
    - overflow_inches  (max(0, tablix_width - printable_width))
    - column_count
    """
    root = parse_rdl(filepath)
    ns = get_namespace(root)

    page = root.find(f".//{ns}Page")
    page_width_in = _page_dim(page, f"{ns}PageWidth", ns)
    page_height_in = _page_dim(page, f"{ns}PageHeight", ns)
    left_margin_in = _page_dim(page, f"{ns}LeftMargin", ns)
    right_margin_in = _page_dim(page, f"{ns}RightMargin", ns)
    top_margin_in = _page_dim(page, f"{ns}TopMargin", ns)
    bottom_margin_in = _page_dim(page, f"{ns}BottomMargin", ns)

    tablix = root.find(f".//{ns}Tablix")
    tablix_width_in = 0.0
    column_count = 0

    if tablix is not None:
        tablix_cols = tablix.findall(f".//{ns}TablixColumns/{ns}TablixColumn")
        column_count = len(tablix_cols)
        for col in tablix_cols:
            w = col.find(f"{ns}Width")
            if w is not None and w.text:
                tablix_width_in += _parse_dimension(w.text)

    printable_width_in = page_width_in - left_margin_in - right_margin_in
    tablix_fits = tablix_width_in <= printable_width_in + 1e-6
    overflow_in = max(0.0, tablix_width_in - printable_width_in)

    return {
        "page_width": f"{page_width_in:.4f}in",
        "page_height": f"{page_height_in:.4f}in",
        "left_margin": f"{left_margin_in:.4f}in",
        "right_margin": f"{right_margin_in:.4f}in",
        "top_margin": f"{top_margin_in:.4f}in",
        "bottom_margin": f"{bottom_margin_in:.4f}in",
        "printable_width": f"{printable_width_in:.4f}in",
        "tablix_width": f"{tablix_width_in:.4f}in",
        "tablix_fits": tablix_fits,
        "overflow_inches": round(overflow_in, 4),
        "column_count": column_count,
    }
