"""Top-level OpenUtau USTX project document model."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ustx.models.expression import UstxExpressionCatalog
from src.ustx.models.part import UstxVoicePart
from src.ustx.models.timing import UstxTempo, UstxTimeSignature
from src.ustx.models.track import UstxTrackHeader

USTX_VERSION: float = 0.6
DEFAULT_OUTPUT_DIR: str = 'Vocal'
DEFAULT_CACHE_DIR: str = 'UCache'


@dataclass(frozen=True)
class UstxDocument:
    """Complete in-memory representation of an OpenUtau ``.ustx`` project file."""

    name: str
    output_dir: str
    cache_dir: str
    ustx_version: float
    resolution: int
    expressions: UstxExpressionCatalog
    tracks: tuple[UstxTrackHeader, ...]
    tempos: tuple[UstxTempo, ...]
    time_signatures: tuple[UstxTimeSignature, ...]
    voice_parts: tuple[UstxVoicePart, ...]
    wave_parts: tuple[Any, ...] = ()

    def to_mapping(self) -> dict[str, Any]:
        """Convert the document to a nested mapping for YAML serialization.

        Key order matches the legacy string-concatenation exporter so text
        output remains stable across refactors.
        """
        document: dict[str, Any] = {
            'name': self.name,
            'output_dir': self.output_dir,
            'cache_dir': self.cache_dir,
            'ustx_version': self.ustx_version,
            'resolution': self.resolution,
            'expressions': self.expressions.to_mapping(),
            'tracks': [track.to_mapping() for track in self.tracks],
        }

        if self.tempos:
            document['tempos'] = [tempo.to_mapping() for tempo in self.tempos]

        if self.time_signatures:
            document['time_signatures'] = [
                time_signature.to_mapping() for time_signature in self.time_signatures
            ]

        document['voice_parts'] = [part.to_mapping() for part in self.voice_parts]
        document['wave_parts'] = list(self.wave_parts)
        return document
