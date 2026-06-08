"""Note-level structures in an OpenUtau USTX voice part."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Self

from src.domain.models.Note import Note
from src.ustx.models.yaml_types import FlowMap, QuotedStr


@dataclass(frozen=True)
class UstxPitchPoint:
    """Single control point on a note pitch curve."""

    x: int
    y: int
    shape: str

    def to_yaml(self) -> FlowMap:
        """Render as a flow-style YAML mapping."""
        return FlowMap({'x': self.x, 'y': self.y, 'shape': self.shape})


@dataclass(frozen=True)
class UstxPitchCurve:
    """Pitch curve attached to a note."""

    data: tuple[UstxPitchPoint, ...]
    snap_first: bool = True

    DEFAULT_POINTS: ClassVar[tuple[UstxPitchPoint, ...]] = (
        UstxPitchPoint(x=-40, y=0, shape='io'),
        UstxPitchPoint(x=25, y=0, shape='io'),
    )

    @classmethod
    def default(cls) -> Self:
        """Return the default pitch curve used for exported notes."""
        return cls(data=cls.DEFAULT_POINTS, snap_first=True)

    def to_mapping(self) -> dict[str, Any]:
        """Convert to a plain mapping suitable for YAML serialization."""
        return {
            'data': [point.to_yaml() for point in self.data],
            'snap_first': self.snap_first,
        }


@dataclass(frozen=True)
class UstxVibrato:
    """Default vibrato envelope applied to exported notes."""

    length: int = 0
    period: int = 175
    depth: int = 25
    fade_in: int = 10
    fade_out: int = 10
    shift: int = 0
    drift: int = 0

    @classmethod
    def default(cls) -> Self:
        """Return the default vibrato settings used for exported notes."""
        return cls()

    def to_yaml(self) -> FlowMap:
        """Render as a flow-style YAML mapping."""
        return FlowMap({
            'length': self.length,
            'period': self.period,
            'depth': self.depth,
            'in': self.fade_in,
            'out': self.fade_out,
            'shift': self.shift,
            'drift': self.drift,
        })


@dataclass(frozen=True)
class UstxNote:
    """Single note entry inside a USTX voice part."""

    position: int
    duration: int
    tone: int
    lyric: str
    pitch: UstxPitchCurve
    vibrato: UstxVibrato
    note_expressions: tuple[Any, ...] = ()
    phoneme_expressions: tuple[Any, ...] = ()
    phoneme_overrides: tuple[Any, ...] = ()

    @staticmethod
    def sanitize_lyric(lyric: str | None) -> str:
        """Normalize lyric text the same way the legacy string export did."""
        if lyric is None:
            return ''
        return lyric.replace('\n', '').replace('"', '')

    @classmethod
    def from_domain(
            cls,
            note: Note,
            tick_resolution: int,
            default_lyric: str) -> Self:
        """Build a USTX note from a domain :class:`~src.domain.models.Note.Note`."""
        lyric = (
            note.lyric
            if note.lyric is not None and note.lyric.strip() != ''
            else default_lyric
        )
        return cls(
            position=int(note.position * tick_resolution),
            duration=int(note.duration * tick_resolution),
            tone=note.tone,
            lyric=cls.sanitize_lyric(lyric),
            pitch=UstxPitchCurve.default(),
            vibrato=UstxVibrato.default(),
        )

    def to_mapping(self) -> dict[str, Any]:
        """Convert to a plain mapping suitable for YAML serialization."""
        return {
            'position': self.position,
            'duration': self.duration,
            'tone': self.tone,
            'lyric': QuotedStr(self.lyric),
            'pitch': self.pitch.to_mapping(),
            'vibrato': self.vibrato.to_yaml(),
            'note_expressions': list(self.note_expressions),
            'phoneme_expressions': list(self.phoneme_expressions),
            'phoneme_overrides': list(self.phoneme_overrides),
        }
