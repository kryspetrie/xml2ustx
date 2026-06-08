"""Tempo and time-signature structures in an OpenUtau USTX project."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from src.domain.models.Tempo import Tempo
from src.domain.models.TimeSignature import TimeSignature


@dataclass(frozen=True)
class UstxTempo:
    """Tempo marker stored in a USTX project."""

    position: int
    bpm: int

    @classmethod
    def from_domain(cls, tempo: Tempo, tick_resolution: int) -> Self:
        """Build a USTX tempo marker from a domain tempo event."""
        return cls(
            position=int(tempo.position * tick_resolution),
            bpm=int(tempo.beats_per_minute),
        )

    def to_mapping(self) -> dict[str, int]:
        """Convert to a plain mapping suitable for YAML serialization."""
        return {'position': self.position, 'bpm': self.bpm}


@dataclass(frozen=True)
class UstxTimeSignature:
    """Time signature marker stored in a USTX project."""

    bar_position: int
    beat_per_bar: int
    beat_unit: int

    @classmethod
    def from_domain(cls, time_signature: TimeSignature, tick_resolution: int) -> Self:
        """Build a USTX time signature from a domain time signature event."""
        return cls(
            bar_position=int(time_signature.position * tick_resolution),
            beat_per_bar=time_signature.beat_per_bar,
            beat_unit=time_signature.beat_unit,
        )

    def to_mapping(self) -> dict[str, int]:
        """Convert to a plain mapping suitable for YAML serialization."""
        return {
            'bar_position': self.bar_position,
            'beat_per_bar': self.beat_per_bar,
            'beat_unit': self.beat_unit,
        }
