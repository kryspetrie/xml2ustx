"""Track header structures in an OpenUtau USTX project."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from src.domain.models.Track import Track


@dataclass(frozen=True)
class UstxRendererSettings:
    """Renderer configuration block for DiffSinger-backed tracks."""

    renderer: str = 'DIFFSINGER'

    def to_mapping(self) -> dict[str, str]:
        """Convert to a plain mapping suitable for YAML serialization."""
        return {'renderer': self.renderer}


@dataclass(frozen=True)
class UstxTrackHeader:
    """Mixer and voice settings for a single project track."""

    mute: bool
    solo: bool
    volume: float
    pan: float
    phonemizer: str | None = None
    renderer_settings: UstxRendererSettings | None = None
    singer: str | None = None
    track_name: str | None = None

    @staticmethod
    def legacy_name(value: str | None) -> str:
        """Convert a track or part name using legacy export semantics.

        The original string-template exporter wrote Python ``None`` as the
        literal text ``None``, which YAML loaders typically read as the string
        ``"None"``.
        """
        if value is None:
            return 'None'
        return value

    @classmethod
    def from_domain(cls, track: Track) -> Self:
        """Build a USTX track header from a domain :class:`~src.domain.models.Track.Track`."""
        renderer_settings = None
        if track.voice.renderer is not None:
            renderer_settings = UstxRendererSettings()

        track_name = None
        # Legacy export always emitted track_name because of a truthiness bug.
        if track.name is not None or track.name != '':
            track_name = cls.legacy_name(track.name)

        return cls(
            mute=False,
            solo=False,
            volume=track.volume,
            pan=track.pan,
            phonemizer=track.voice.phonemizer,
            renderer_settings=renderer_settings,
            singer=track.voice.singer,
            track_name=track_name,
        )

    def to_mapping(self) -> dict[str, Any]:
        """Convert to a plain mapping suitable for YAML serialization."""
        mapping: dict[str, Any] = {
            'mute': self.mute,
            'solo': self.solo,
            'volume': self.volume,
            'pan': self.pan,
        }
        if self.phonemizer is not None:
            mapping['phonemizer'] = self.phonemizer
        if self.renderer_settings is not None:
            mapping['renderer_settings'] = self.renderer_settings.to_mapping()
        if self.singer is not None:
            mapping['singer'] = self.singer
        if self.track_name is not None:
            mapping['track_name'] = self.track_name
        return mapping
