"""Serialize structured USTX documents to OpenUtau YAML text."""
from __future__ import annotations

from typing import Any

import yaml

from src.domain.models.Project import Project
from src.ustx.builder import UstxDocumentBuilder
from src.ustx.models.document import UstxDocument
from src.ustx.models.yaml_types import UstxDumper


def build_document(project: Project) -> dict[str, Any]:
    """Build a USTX document mapping from a domain project.

    This helper preserves compatibility with callers and tests that expect a
    plain nested mapping. Prefer :func:`build_ustx_document` when working with
    typed models directly.

    Args:
        project: Parsed domain project.

    Returns:
        Nested mapping representing the USTX file contents.
    """
    return build_ustx_document(project).to_mapping()


def build_ustx_document(project: Project) -> UstxDocument:
    """Build a typed USTX document from a domain project.

    Args:
        project: Parsed domain project.

    Returns:
        Structured USTX document model.
    """
    return UstxDocumentBuilder.from_project(project)


def serialize_document(document: UstxDocument) -> str:
    """Serialize a structured USTX document to YAML text.

    Args:
        document: Typed USTX document model.

    Returns:
        YAML text including the leading newline used by legacy export.
    """
    body = yaml.dump(
        document.to_mapping(),
        Dumper=UstxDumper,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )
    return f'\n{body}'


def serialize(project: Project) -> str:
    """Serialize a domain project to USTX YAML text.

    Args:
        project: Parsed domain project.

    Returns:
        YAML text including the leading newline used by legacy export.
    """
    return serialize_document(build_ustx_document(project))
