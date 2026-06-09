"""Job builder for XML to USTX conversion."""
from pathlib import Path
from typing import List

from src.application.models.NativeUiOptions import NativeUiOptions
from src.application.ApplicationConfig import ApplicationConfig
from src.application.models.CommandLineOptions import CommandLineOptions
from src.application.ConfigParser import parse as parse_config
from src.application.ConfigPaths import resolve_config_file
from src.domain.models.Job import Job
from src.domain.models.TrackConfig import TrackConfig
from src.domain.rhythm_config import RhythmConfig

# Job defaults, when not specified
DEFAULT_PROJECT_NAME = 'New Project'
DEFAULT_LYRIC = 'doo'


def to_output_file(input_file: str) -> str:
    """Convert input file path to output .ustx file path."""
    input_path = Path(input_file)
    return f'{input_path.parent.as_posix()}/{input_path.stem}.ustx'


def output_file_or_default(options: CommandLineOptions) -> str | None:
    """Get output file or default based on options."""
    output_file = options.output_file
    if options.input_file is not None and options.output_file is None:
        output_file = to_output_file(options.input_file)
    return output_file


def get_output_files_from_input(input_files: list[str]) -> list[str]:
    """Get output files from input files list."""
    return [to_output_file(file) for file in input_files]


def get_input_files_from_dir(input_dir: str) -> list[str]:
    """Get input files from directory."""
    file_type_globs = ['*.xml', '*.musicxml', '*.mxl', '*.midi']
    input_dir_path = Path(input_dir)
    paths = []
    for glob in file_type_globs:
        found = list(input_dir_path.glob(glob))
        paths.extend(found)
    return [str(path) for path in paths]


def build_cli(options: CommandLineOptions) -> Job:
    """Build the command-line interface for the application."""
    # load application config from the file
    config_file = resolve_config_file(options.config_file)
    application_config: ApplicationConfig = parse_config(config_file)

    track_configs: List[TrackConfig] = []

    # Track config id takes precedence for parsed settings
    if options.track_config_id is not None:
        if options.track_config_id not in application_config.track_config_map:
            raise RuntimeError(f'Track config {options.track_config_id} not found in {config_file}')
        track_configs = application_config.track_config_map[options.track_config_id]

    # Otherwise use the voice data
    if track_configs is None or len(track_configs) == 0:
        track_configs = []
        len_tracks: int = len(options.tracks) if options.tracks is not None else 0
        len_volumes: int = len(options.volumes) if options.volumes is not None else 0
        len_pans: int = len(options.pans) if options.pans is not None else 0
        len_voices: int = len(options.voice_config_ids) if options.voice_config_ids is not None else 0
        track_configs_to_create: int = max(len_tracks, len_volumes, len_pans, len_voices)
        for i in range(track_configs_to_create):
            pan = 0
            volume = 0
            track = f'Track {i+1}'
            voice = application_config.default_voice_config()

            if i < len_pans:
                pan = options.pans[i]

            if i < len_volumes:
                volume = options.volumes[i]

            if i < len_tracks:
                track = options.tracks[i]

            if i < len_voices:
                voice_id: str = options.voice_config_ids[i]
                if voice_id not in application_config.voice_config_map:
                    raise RuntimeError(f'Did not find voice id {voice_id} in {config_file}')
                voice = application_config.voice_config_map[voice_id]

            track_config: TrackConfig = TrackConfig(name=track, voice=voice, pan=pan, volume=volume)
            track_configs.append(track_config)

    # If we still do not have a track config, make a generic one
    if track_configs is None or len(track_configs) == 0:
        voice = application_config.default_voice_config()
        track_configs = [TrackConfig(name='New Track', voice=voice, pan=0, volume=0)]

    # Load defaults if needed
    project_name = options.project_name if options.project_name is not None else DEFAULT_PROJECT_NAME
    default_lyric = application_config.default_lyric if application_config.default_lyric is not None else DEFAULT_LYRIC
    output_file = output_file_or_default(options)

    input_files: list[str] = []
    output_files: list[str] = []
    if options.input_dir:
        input_files = get_input_files_from_dir(options.input_dir)
        output_files = get_output_files_from_input(input_files)
    if options.input_file:
        input_files.append(options.input_file)
        output_files.append(output_file)

    # Build a job from our configuration
    job: Job = Job(
        input_files=input_files,
        output_files=output_files,
        name=project_name,
        track_configs=track_configs,
        default_lyric=default_lyric,
        rhythm_config=application_config.rhythm_config,
        debug=options.debug)

    return job


def _build_track_configs(
        application_config: ApplicationConfig,
        track_config_id: str | None,
        voice_config_ids: list[str] | None,
        volumes: list[float] | None,
        pans: list[float] | None,
        tracks: list[str] | None,
        config_file: str) -> List[TrackConfig]:
    track_configs: List[TrackConfig] = []
    if track_config_id is not None:
        if track_config_id not in application_config.track_config_map:
            raise RuntimeError(f'Track config {track_config_id} not found in {config_file}')
        return application_config.track_config_map[track_config_id]

    len_tracks = max(
        len(tracks or []),
        len(volumes or []),
        len(pans or []),
        len(voice_config_ids or []),
    )
    for i in range(len_tracks):
        pan = pans[i] if pans and i < len(pans) else 0
        volume = volumes[i] if volumes and i < len(volumes) else 0
        track = tracks[i] if tracks and i < len(tracks) else f'Track {i + 1}'
        voice = application_config.default_voice_config()
        if voice_config_ids and i < len(voice_config_ids):
            voice_id = voice_config_ids[i]
            if voice_id not in application_config.voice_config_map:
                raise RuntimeError(f'Did not find voice id {voice_id} in {config_file}')
            voice = application_config.voice_config_map[voice_id]
        track_configs.append(TrackConfig(name=track, voice=voice, pan=pan, volume=volume))

    if not track_configs:
        voice = application_config.default_voice_config()
        track_configs = [TrackConfig(name='New Track', voice=voice, pan=0, volume=0)]
    return track_configs


def build_native(options: NativeUiOptions) -> Job:
    """Build a conversion job from native UI options (CLI-equivalent)."""
    config_file = resolve_config_file(options.config_file)
    application_config: ApplicationConfig = parse_config(config_file)
    track_configs = _build_track_configs(
        application_config,
        options.track_config_id,
        options.voice_config_ids,
        options.volumes,
        options.pans,
        options.tracks,
        config_file,
    )
    default_lyric = application_config.default_lyric or DEFAULT_LYRIC
    project_name = options.project_name or DEFAULT_PROJECT_NAME

    if options.input_dir:
        input_files = get_input_files_from_dir(options.input_dir)
        output_files = get_output_files_from_input(input_files)
    else:
        input_files = list(options.input_files)
        if not input_files:
            raise RuntimeError('No input files selected.')
        if options.output_files and len(options.output_files) == len(input_files):
            output_files = list(options.output_files)
        else:
            output_files = get_output_files_from_input(input_files)

    return Job(
        input_files=input_files,
        output_files=output_files,
        name=project_name,
        track_configs=track_configs,
        default_lyric=default_lyric,
        rhythm_config=_build_rhythm_config(options, application_config),
        debug=options.debug,
    )


def _build_rhythm_config(options: NativeUiOptions, application_config) -> RhythmConfig:
    return RhythmConfig.from_presets(
        application_config.swing_presets,
        application_config.groove_presets,
        swing_preset_id=options.swing_preset_id or '',
        groove_preset_id=options.groove_preset_id or '',
        rhythm_disabled=options.rhythm_disabled,
        force_swing=options.force_swing,
        force_groove=options.force_groove,
    )

