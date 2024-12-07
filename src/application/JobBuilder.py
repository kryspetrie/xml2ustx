from typing import List

from src.application.models.UiOptions import UiOptions
from src.Utils import dumps
from src.application.ApplicationConfig import ApplicationConfig
from src.application.models.CommandLineOptions import CommandLineOptions
from src.application.ConfigParser import parse as parse_config
from src.domain.models.Job import Job
from src.domain.models.TrackConfig import TrackConfig

# Job defaults, when not specified
DEFAULT_CONFIG_FILE = './config.yml'
DEFAULT_OUTPUT_FILE = './converted.ustx'
DEFAULT_PROJECT_NAME = 'New Project'
DEFAULT_LYRIC = 'doo'


def build_cli(options: CommandLineOptions) -> Job:

    # load application config from the file
    application_config: ApplicationConfig = parse_config(
        DEFAULT_CONFIG_FILE if options.config_file is None else options.config_file)

    track_configs: List[TrackConfig] = []

    # Track config id takes precedence for parsed settings
    if options.track_config_id is not None:
        if options.track_config_id not in application_config.track_config_map:
            raise RuntimeError(f'Track config {options.track_config_id} not found in {options.config_file}')
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
                    raise RuntimeError(f'Did not find voice id {voice_id} in {options.config_file}')
                voice = application_config.voice_config_map[voice_id]

            track_config: TrackConfig = TrackConfig(name=track, voice=voice, pan=pan, volume=volume)
            track_configs.append(track_config)

    # If we still do not have a track config, make a generic one
    if track_configs is None or len(track_configs) == 0:
        voice = application_config.default_voice_config()
        track_configs = [TrackConfig(name='New Track', voice=voice, pan=0, volume=0)]

    # Load defaults if needed
    project_name = options.project_name if options.project_name is not None else DEFAULT_PROJECT_NAME
    output_file = options.output_file if options.output_file is not None else DEFAULT_OUTPUT_FILE
    default_lyric = application_config.default_lyric if application_config.default_lyric is not None else DEFAULT_LYRIC

    # Build a job from our configuration
    job: Job = Job(
        input_file=options.input_file,
        output_file=output_file,
        name=project_name,
        track_configs=track_configs,
        default_lyric=default_lyric,
        debug=options.debug)

    # print debug information
    if options.debug:
        print(f'Running job with the following config:\n{dumps(job)}\n')

    return job


def build_ui(options: UiOptions):

    # load application config from the file
    application_config: ApplicationConfig = parse_config(DEFAULT_CONFIG_FILE)

    # Load the specified track config, otherwise use the default options
    track_configs: List[TrackConfig] = application_config.default_track_config()
    if options.track_config_id is not None:
        if options.track_config_id not in application_config.track_config_map:
            raise RuntimeError(f'Track config {options.track_config_id} not found in {DEFAULT_CONFIG_FILE}')
        track_configs = application_config.track_config_map[options.track_config_id]

    return Job(
        input_file=options.input_file,
        output_file=None,
        name=DEFAULT_PROJECT_NAME,
        track_configs=track_configs,
        default_lyric=DEFAULT_LYRIC,
        debug=False)
