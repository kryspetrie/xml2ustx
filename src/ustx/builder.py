"""Build structured USTX documents from domain projects."""
from __future__ import annotations

from src.domain.models.Event import Event
from src.domain.models.Project import Project
from src.domain.models.TimeSignature import TimeSignature
from src.ustx.UstxTempoInterpolation import interpolate_tempos
from src.ustx.models.document import (
    DEFAULT_CACHE_DIR,
    DEFAULT_OUTPUT_DIR,
    USTX_VERSION,
    UstxDocument,
)
from src.ustx.models.expression import UstxExpressionCatalog
from src.ustx.models.part import UstxVoicePart
from src.ustx.models.timing import UstxTempo, UstxTimeSignature
from src.ustx.models.track import UstxTrackHeader


class UstxDocumentBuilder:
    """Construct :class:`~src.ustx.models.document.UstxDocument` instances."""

    @staticmethod
    def from_project(project: Project) -> UstxDocument:
        """Convert a parsed domain project into a structured USTX document.

        Args:
            project: Parsed MusicXML (or other supported input) project model.

        Returns:
            A fully populated USTX document ready for YAML serialization.
        """
        time_signatures: list[TimeSignature] = project.find_unique_time_signatures()
        tempo_events: list[Event] = project.find_unique_tempos_and_changes()
        tempos = interpolate_tempos(tempo_events)

        voice_parts: list[UstxVoicePart] = []
        for index, track in enumerate(project.tracks):
            if not UstxVoicePart.track_has_notes(track):
                continue
            voice_parts.append(
                UstxVoicePart.from_domain(
                    track=track,
                    track_number=index,
                    tick_resolution=project.tick_resolution,
                    default_lyric=project.default_lyric,
                )
            )

        return UstxDocument(
            name=project.name,
            output_dir=DEFAULT_OUTPUT_DIR,
            cache_dir=DEFAULT_CACHE_DIR,
            ustx_version=USTX_VERSION,
            resolution=project.tick_resolution,
            expressions=UstxExpressionCatalog.load_default(),
            tracks=tuple(UstxTrackHeader.from_domain(track) for track in project.tracks),
            tempos=tuple(
                UstxTempo.from_domain(tempo, project.tick_resolution) for tempo in tempos
            ),
            time_signatures=tuple(
                UstxTimeSignature.from_domain(time_signature, project.tick_resolution)
                for time_signature in time_signatures
            ),
            voice_parts=tuple(voice_parts),
            wave_parts=(),
        )
