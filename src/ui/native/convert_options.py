"""Build NativeUiOptions from convert form state with validation."""
from __future__ import annotations

from pathlib import Path

from src.application.ConfigParser import parse as parse_config
from src.application.ConfigPaths import resolve_config_file
from src.application.models.NativeUiOptions import NativeUiOptions
from src.application.openutau_launcher import is_valid_openutau_path
from src.ui.native.constants import INPUT_EXTENSIONS
from src.ui.native.models.convert_form_state import ConvertFormState


def build_native_ui_options(
    state: ConvertFormState,
    config_file: str | None,
    *,
    openutau_path: str | None = None,
) -> NativeUiOptions:
    """Validate form state and produce CLI-equivalent native UI options.

    Args:
        state: Convert tab form snapshot.
        config_file: Active config path, or ``None`` for bundled default.

    Returns:
        Options ready for :func:`src.application.JobBuilder.build_native`.

    Raises:
        ValueError: When inputs fail validation.
    """
    config_path = config_file or str(resolve_config_file(None))
    openutau = openutau_path.strip() if openutau_path else None
    project_name = state.project_name.strip() or 'New Project'

    if state.open_in_openutau:
        if not openutau:
            raise ValueError('Set the OpenUtau path in File → Set OpenUtau path… before opening in OpenUtau.')
        if not is_valid_openutau_path(openutau):
            raise ValueError(f'OpenUtau executable not found: {openutau}')

    track_config_id, voices, pans, volumes, tracks = _resolve_track_settings(state, config_path)
    _validate_rhythm_settings(state, config_path)

    if state.batch_mode:
        input_dir = state.input_path.strip()
        if not input_dir:
            raise ValueError('Select an input directory.')
        if not Path(input_dir).is_dir():
            raise ValueError('Input directory does not exist.')
        return NativeUiOptions(
            input_dir=input_dir,
            config_file=config_file,
            project_name=project_name,
            track_config_id=track_config_id,
            voice_config_ids=voices,
            pans=pans,
            volumes=volumes,
            tracks=tracks,
            debug=state.debug,
            open_in_openutau=state.open_in_openutau,
            openutau_path=openutau,
            swing_preset_id=state.swing_preset_id,
            groove_preset_id=state.groove_preset_id,
            rhythm_disabled=state.rhythm_disabled,
            force_swing=state.force_swing,
            force_groove=state.force_groove,
        )

    files = list(state.input_files)
    if not files:
        single = state.input_path.strip()
        if single:
            files = [single]
    if not files:
        raise ValueError('Add at least one input file.')

    for file_path in files:
        path = Path(file_path)
        if not path.is_file():
            raise ValueError(f'Input file not found: {file_path}')
        if path.suffix.lower() not in INPUT_EXTENSIONS:
            raise ValueError(f'Unsupported input file: {file_path}')

    output_files = None
    if not state.auto_output:
        out = state.output_path.strip()
        if not out:
            raise ValueError('Set an output file or enable auto output path.')
        if len(files) == 1:
            output_files = [out if out.lower().endswith('.ustx') else out + '.ustx']
        else:
            raise ValueError(
                'Manual output path only works for a single input file. '
                'Enable auto output for batch conversion.')

    return NativeUiOptions(
        input_files=files,
        output_files=output_files,
        config_file=config_file,
        project_name=project_name,
        track_config_id=track_config_id,
        voice_config_ids=voices,
        pans=pans,
        volumes=volumes,
        tracks=tracks,
        debug=state.debug,
        open_in_openutau=state.open_in_openutau,
        openutau_path=openutau,
        swing_preset_id=state.swing_preset_id,
        groove_preset_id=state.groove_preset_id,
        rhythm_disabled=state.rhythm_disabled,
        force_swing=state.force_swing,
        force_groove=state.force_groove,
    )


def _validate_rhythm_settings(state: ConvertFormState, config_path: str) -> None:
    config = parse_config(config_path)
    swing_id = state.swing_preset_id or ''
    groove_id = state.groove_preset_id or ''
    if swing_id and not any(preset.preset_id == swing_id for preset in config.swing_presets):
        raise ValueError(f"Unknown swing preset '{swing_id}' in config.")
    if groove_id and not any(preset.preset_id == groove_id for preset in config.groove_presets):
        raise ValueError(f"Unknown groove preset '{groove_id}' in config.")


def _resolve_track_settings(
        state: ConvertFormState,
        config_path: str) -> tuple[str | None, list[str] | None, list[float] | None, list[float] | None, list[str] | None]:
    if not state.use_custom_tracks:
        preset = state.track_preset_id or None
        return preset, None, None, None, None

    if not state.custom_tracks:
        raise ValueError('Add at least one custom track row.')

    config = parse_config(config_path)
    names: list[str] = []
    voices: list[str] = []
    pans: list[float] = []
    volumes: list[float] = []

    for row in state.custom_tracks:
        if row.voice_id not in config.voice_config_map:
            raise ValueError(f"Unknown voice id '{row.voice_id}' in config.")
        names.append(row.name)
        voices.append(row.voice_id)
        pans.append(row.pan)
        volumes.append(row.volume)

    return None, voices, pans, volumes, names
