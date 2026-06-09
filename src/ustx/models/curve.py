"""Automation curve structures in an OpenUtau USTX voice part."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from src.domain.dynamics_parser import DynamicBreakpoint


@dataclass(frozen=True)
class UstxCurve:
    """A parameter automation curve attached to a voice part."""

    abbr: str
    xs: tuple[int, ...]
    ys: tuple[int, ...]

    @classmethod
    def from_dyn_breakpoints(
            cls,
            breakpoints: list[DynamicBreakpoint],
            tick_resolution: int,
            part_position: int = 0) -> Self | None:
        """Build a ``dyn`` curve from parsed dynamics breakpoints."""
        if not breakpoints:
            return None

        xs: list[int] = []
        ys: list[int] = []
        for point in breakpoints:
            tick = int(point.position * tick_resolution) - part_position
            xs.append(tick)
            ys.append(point.dyn_value)

        if not xs:
            return None
        return cls(abbr='dyn', xs=tuple(xs), ys=tuple(ys))

    def to_mapping(self) -> dict[str, Any]:
        """Convert to a plain mapping suitable for YAML serialization."""
        return {
            'abbr': self.abbr,
            'xs': list(self.xs),
            'ys': list(self.ys),
        }
