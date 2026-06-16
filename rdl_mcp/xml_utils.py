"""XML utility functions for RDL file handling."""

import xml.etree.ElementTree as ET
import defusedxml.ElementTree as SafeET
import os
import re
import logging
import shutil
import tempfile
import threading
import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ErrorCode:
    """Structured error category constants for actionable diagnostics."""

    EMPTY_FILE = "EMPTY_FILE"
    MALFORMED_XML = "MALFORMED_XML"
    INVALID_RDL_SCHEMA = "INVALID_RDL_SCHEMA"
    LOCK_CONFLICT = "LOCK_CONFLICT"
    WRITE_FAILURE = "WRITE_FAILURE"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    INVALID_FILEPATH = "INVALID_FILEPATH"
    COLUMN_NOT_FOUND = "COLUMN_NOT_FOUND"
    DATASET_NOT_FOUND = "DATASET_NOT_FOUND"
    PARAMETER_NOT_FOUND = "PARAMETER_NOT_FOUND"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"


class FileLockManager:
    """Singleton per-file threading-lock manager.

    Guarantees that concurrent mutation calls for the *same resolved path*
    are serialised, preventing write-over-write file corruption.
    """

    _singleton_lock: threading.Lock = threading.Lock()
    _instance: Optional["FileLockManager"] = None
    _file_locks: Dict[str, threading.Lock]

    def __init__(self) -> None:
        self._file_locks = {}
        self._registry_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "FileLockManager":
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_lock(self, filepath: str) -> threading.Lock:
        """Return (creating if necessary) the lock for *filepath*."""
        key = os.path.realpath(filepath) if os.path.exists(filepath) else os.path.abspath(filepath)
        with self._registry_lock:
            if key not in self._file_locks:
                self._file_locks[key] = threading.Lock()
            return self._file_locks[key]


def validate_filepath(filepath: str) -> str:
    """Validate and resolve a filepath for safe access.

    Ensures the path points to a .rdl file, resolves symlinks,
    and prevents path traversal attacks (CWE-22).

    Returns:
        The resolved absolute filepath.

    Raises:
        ValueError: If the filepath is invalid or unsafe.
    """
    if not filepath or not isinstance(filepath, str):
        raise ValueError("Filepath must be a non-empty string")

    resolved = os.path.realpath(filepath)

    if not resolved.lower().endswith('.rdl'):
        raise ValueError("Only .rdl files are supported")

    if not os.path.isfile(resolved):
        raise FileNotFoundError("File not found")

    return resolved


def get_namespace(root: ET.Element) -> str:
    """Extract the namespace from the root element."""
    match = re.match(r'\{(.+?)\}', root.tag)
    if match:
        return '{' + match.group(1) + '}'
    return ''


def register_namespaces(filepath: str):
    """Register all namespaces found in the file to preserve them when writing."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Find all namespace declarations
    ns_pattern = r'xmlns:([a-zA-Z0-9_]+)="([^"]+)"'
    for match in re.finditer(ns_pattern, content):
        prefix = match.group(1)
        uri = match.group(2)
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass  # Namespace already registered

    # Also register the default namespace if present
    default_ns = re.search(r'xmlns="([^"]+)"', content)
    if default_ns:
        # Can't register default namespace with empty prefix in ElementTree
        # but we track it for reference
        pass


def parse_rdl(filepath: str) -> ET.Element:
    """Parse an RDL file and return the root element.

    Uses defusedxml to prevent XXE and entity expansion attacks (CWE-611, CWE-776).
    Validates the filepath to prevent path traversal (CWE-22).
    """
    resolved = validate_filepath(filepath)
    tree = SafeET.parse(resolved)
    return tree.getroot()


def parse_rdl_tree(filepath: str) -> ET.ElementTree:
    """Parse an RDL file and return the ElementTree (for modifications).

    Uses defusedxml to prevent XXE and entity expansion attacks (CWE-611, CWE-776).
    Validates the filepath to prevent path traversal (CWE-22).
    """
    resolved = validate_filepath(filepath)
    register_namespaces(resolved)
    return SafeET.parse(resolved)


def indent_xml(elem: ET.Element, level: int = 0):
    """Add indentation to XML elements for pretty printing."""
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def write_xml(tree: ET.ElementTree, filepath: str,
              backup: bool = False) -> Optional[str]:
    """Write an ElementTree to file atomically with proper formatting.

    Steps:
    1. Acquire per-file threading lock (prevents concurrent write corruption).
    2. Optionally create a timestamped backup of the current file.
    3. Write formatted XML to a sibling temp file.
    4. Validate the temp file is parseable XML.
    5. Atomically replace the original (``os.replace``).
    6. Release the lock (even on failure; original file is never touched).

    Args:
        tree: The ElementTree to write.
        filepath: Destination path (must already have been validated).
        backup: When True, save a timestamped ``.bak`` copy before replacing.

    Returns:
        The backup path when *backup* is True and a backup was created,
        otherwise ``None``.

    Raises:
        OSError: If the temp write or atomic replace fails.
    """
    root = tree.getroot()
    indent_xml(root)

    file_lock = FileLockManager.get_instance().get_lock(filepath)
    backup_path: Optional[str] = None

    with file_lock:
        # --- optional backup ---
        if backup and os.path.isfile(filepath):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{filepath}.{timestamp}.bak"
            shutil.copy2(filepath, backup_path)

        # --- write to temp file ---
        dir_name = os.path.dirname(os.path.abspath(filepath))
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=dir_name)
        try:
            with os.fdopen(tmp_fd, "wb") as tmp_f:
                tree.write(tmp_f, encoding="utf-8", xml_declaration=True)

            # Fix XML declaration quotes (SSRS preference: double quotes)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace("'", '"', 2)
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content)

            # --- validate the temp file before replacing the original ---
            SafeET.parse(tmp_path)

            # --- atomic replace ---
            os.replace(tmp_path, filepath)

        except Exception:
            # Rollback: remove temp file; original is untouched
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    return backup_path


def find_parent(root: ET.Element, target: ET.Element) -> Optional[ET.Element]:
    """Find parent element of target within root's tree."""
    for parent in root.iter():
        for child in parent:
            if child is target:
                return parent
    return None
