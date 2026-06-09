"""Parse score dynamics into USTX automation data."""
from __future__ import annotations

from dataclasses import dataclass

import music21

DYN_MIN = -240
DYN_MAX = 120
DYN_DEFAULT = 0
VOL_MIN = 0
VOL_MAX = 200


@dataclass(frozen=True)
class DynamicBreakpoint:
    """A single dynamics automation point in quarter-note beats."""

    position: float
    dyn_value: int
    vol_value: int


def scalar_to_dyn(scalar: float) -> int:
    """Map a music21 volume scalar (0–1) to the USTX ``dyn`` curve range."""
    value = int(round((scalar - 0.55) * 400))
    return max(DYN_MIN, min(DYN_MAX, value))


def scalar_to_vol(scalar: float) -> int:
    """Map a music21 volume scalar (0–1) to the USTX ``vol`` expression range."""
    value = int(round(scalar * VOL_MAX))
    return max(VOL_MIN, min(VOL_MAX, value))


def parse_dynamics(flattened: music21.stream.Stream) -> list[DynamicBreakpoint]:
    """Collect dynamics and hairpin breakpoints from a flattened score stream."""
    breakpoints: list[DynamicBreakpoint] = []
    current_dyn = DYN_DEFAULT
    current_vol = scalar_to_vol(0.55)

    for event in flattened:
        if isinstance(event, music21.dynamics.Dynamic):
            scalar = _dynamic_scalar(event)
            current_dyn = scalar_to_dyn(scalar)
            current_vol = scalar_to_vol(scalar)
            breakpoints.append(
                DynamicBreakpoint(event.offset, current_dyn, current_vol),
            )
            continue

        if isinstance(event, music21.dynamics.Crescendo):
            start_dyn = current_dyn
            end_dyn = min(DYN_MAX, start_dyn + 40)
            _append_hairpin(
                breakpoints,
                event,
                start_dyn,
                end_dyn,
                scalar_to_vol(0.55),
                scalar_to_vol(0.75),
            )
            current_dyn = end_dyn
            current_vol = scalar_to_vol(0.75)
            continue

        if isinstance(event, music21.dynamics.Diminuendo):
            start_dyn = current_dyn
            end_dyn = max(DYN_MIN, start_dyn - 40)
            _append_hairpin(
                breakpoints,
                event,
                start_dyn,
                end_dyn,
                scalar_to_vol(0.75),
                scalar_to_vol(0.45),
            )
            current_dyn = end_dyn
            current_vol = scalar_to_vol(0.45)

    return _dedupe_breakpoints(breakpoints)


def nearest_vol_at_position(
        breakpoints: list[DynamicBreakpoint],
        position: float) -> int | None:
    """Return the nearest ``vol`` value at or before ``position``."""
    if not breakpoints:
        return None

    best: DynamicBreakpoint | None = None
    for point in breakpoints:
        if point.position <= position + 0.001:
            if best is None or point.position >= best.position:
                best = point
    return best.vol_value if best is not None else None


def _dynamic_scalar(dynamic: music21.dynamics.Dynamic) -> float:
    scalar = getattr(dynamic, 'volumeScalar', None)
    if scalar is not None:
        return float(scalar)

    value = (dynamic.value or 'mf').strip().lower()
    mapped = music21.dynamics.dynamicStrToScalar.get(value)
    if mapped is not None:
        return float(mapped)
    return 0.55


def _append_hairpin(
        breakpoints: list[DynamicBreakpoint],
        spanner: music21.dynamics.Crescendo | music21.dynamics.Diminuendo,
        start_dyn: int,
        end_dyn: int,
        start_vol: int,
        end_vol: int) -> None:
    start_position, end_position = _spanner_positions(spanner)
    if end_position <= start_position:
        end_position = start_position + max(spanner.quarterLength, 0.25)

    breakpoints.append(DynamicBreakpoint(start_position, start_dyn, start_vol))
    breakpoints.append(DynamicBreakpoint(end_position, end_dyn, end_vol))


def _spanner_positions(
        spanner: music21.dynamics.Crescendo | music21.dynamics.Diminuendo) -> tuple[float, float]:
    elements = list(spanner.getSpannedElements())
    if not elements:
        return float(spanner.offset), float(spanner.offset)

    start_position = float(min(element.offset for element in elements))
    end_position = float(
        max(element.offset + element.quarterLength for element in elements)
    )
    return start_position, end_position


def _dedupe_breakpoints(breakpoints: list[DynamicBreakpoint]) -> list[DynamicBreakpoint]:
    if not breakpoints:
        return []

    ordered = sorted(breakpoints, key=lambda point: point.position)
    deduped: list[DynamicBreakpoint] = []
    for point in ordered:
        if deduped and deduped[-1].position == point.position:
            deduped[-1] = point
            continue
        deduped.append(point)
    return deduped
