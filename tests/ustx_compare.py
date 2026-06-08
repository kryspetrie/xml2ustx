"""Helpers for comparing USTX YAML documents in tests."""
from __future__ import annotations

import copy
from typing import Any

import yaml


def load_ustx_document(text: str) -> dict[str, Any]:
    """Parse USTX YAML text into a Python mapping.

    Args:
        text: Raw USTX file contents.

    Returns:
        Parsed document root mapping.

    Raises:
        AssertionError: If the parsed root is not a mapping.
    """
    document = yaml.safe_load(text)
    if not isinstance(document, dict):
        raise AssertionError('USTX root must be a mapping')
    return document


def normalize_ustx_document(document: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy export quirks for stable semantic comparison.

    Args:
        document: Parsed USTX document mapping.

    Returns:
        Deep copy of the document with legacy ``None`` representations normalized.
    """
    normalized = copy.deepcopy(document)
    if isinstance(normalized.get('ustx_version'), str):
        normalized['ustx_version'] = float(normalized['ustx_version'])

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in list(value.items()):
                if item is None and key in {'name', 'track_name'}:
                    value[key] = 'None'
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(normalized)
    return normalized


def assert_ustx_documents_equal(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    """Assert two parsed USTX documents are semantically equivalent.

    Args:
        actual: Parsed document produced by the exporter under test.
        expected: Parsed golden/reference document.

    Raises:
        AssertionError: If the normalized documents differ.
    """
    assert normalize_ustx_document(actual) == normalize_ustx_document(expected)
