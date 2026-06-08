"""Options for the native Qt UI (parity with CLI)."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NativeUiOptions:
    """Conversion settings from the native desktop UI."""

    input_files: List[str] = field(default_factory=list)
    input_dir: Optional[str] = None
    output_files: Optional[List[str]] = None
    config_file: Optional[str] = None
    project_name: str = "New Project"
    track_config_id: Optional[str] = None
    voice_config_ids: Optional[List[str]] = None
    pans: Optional[List[float]] = None
    volumes: Optional[List[float]] = None
    tracks: Optional[List[str]] = None
    debug: bool = False
    open_in_openutau: bool = False
    openutau_path: Optional[str] = None
