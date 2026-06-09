"""Voice part structures in an OpenUtau USTX project."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from src.domain.models.Note import Note
from src.domain.models.Track import Track
from src.ustx.models.curve import UstxCurve
from src.ustx.models.note import UstxNote
from src.ustx.models.track import UstxTrackHeader


@dataclass(frozen=True)
class UstxVoicePart:
    """Lyrics and notes for one vocal track in a USTX project."""

    name: str
    comment: str
    track_no: int
    position: int
    notes: tuple[UstxNote, ...]
    curves: tuple[UstxCurve, ...] = ()

    @classmethod
    def from_domain(
            cls,
            track: Track,
            track_number: int,
            tick_resolution: int,
            default_lyric: str,
            dyn_curve: UstxCurve | None = None) -> Self:
        """Build a USTX voice part from a domain track that contains notes."""
        notes = tuple(
            UstxNote.from_domain(note_event, tick_resolution, default_lyric)
            for note_event in track.events
            if isinstance(note_event, Note)
        )
        curves = (dyn_curve,) if dyn_curve is not None else ()
        return cls(
            name=UstxTrackHeader.legacy_name(track.name),
            comment='',
            track_no=track_number,
            position=0,
            notes=notes,
            curves=curves,
        )

    @staticmethod
    def track_has_notes(track: Track) -> bool:
        """Return ``True`` when the track contains at least one note event."""
        if track.events is None:
            return False
        return any(isinstance(event, Note) for event in track.events)

    def to_mapping(self) -> dict[str, Any]:
        """Convert to a plain mapping suitable for YAML serialization."""
        mapping: dict[str, Any] = {
            'name': self.name,
            'comment': self.comment,
            'track_no': self.track_no,
            'position': self.position,
            'notes': [note.to_mapping() for note in self.notes],
        }
        if self.curves:
            mapping['curves'] = [curve.to_mapping() for curve in self.curves]
        return mapping
