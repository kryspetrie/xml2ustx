"""Form state for the convert tab (view-model layer)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CustomTrackRow:
    """One row of custom per-track settings."""

    name: str
    voice_id: str
    pan: float = 0.0
    volume: float = 0.0


@dataclass
class ConvertFormState:
    """Snapshot of convert-tab inputs used to build a conversion job."""

    batch_mode: bool = False
    input_path: str = ''
    input_files: list[str] = field(default_factory=list)
    auto_output: bool = True
    output_path: str = ''
    project_name: str = 'New Project'
    track_preset_id: str | None = 'default'
    use_custom_tracks: bool = False
    custom_tracks: list[CustomTrackRow] = field(default_factory=list)
    debug: bool = False
    open_in_openutau: bool = False
