"""YAML serialization helpers for OpenUtau USTX export."""
from __future__ import annotations

from typing import Any

import yaml


class FlowMap(dict[str, Any]):
    """Mapping rendered in YAML flow style (``{x: 1, y: 2}``).

    OpenUtau expects compact flow mappings for pitch points and vibrato settings.
    """


class QuotedStr(str):
    """String rendered with YAML double quotes.

    Lyrics are always double-quoted in legacy USTX files.
    """


class UstxDumper(yaml.SafeDumper):
    """PyYAML dumper configured for OpenUtau USTX formatting."""


def _flow_map_representer(dumper: yaml.Dumper, data: FlowMap) -> yaml.nodes.Node:
    """Render :class:`FlowMap` instances using flow style."""
    return dumper.represent_mapping('tag:yaml.org,2002:map', data, flow_style=True)


def _quoted_str_representer(dumper: yaml.Dumper, data: QuotedStr) -> yaml.nodes.Node:
    """Render :class:`QuotedStr` instances with double quotes."""
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data), style='"')


yaml.add_representer(FlowMap, _flow_map_representer, Dumper=UstxDumper)
yaml.add_representer(QuotedStr, _quoted_str_representer, Dumper=UstxDumper)
