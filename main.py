import argparse
from typing import List, Optional

import jsonpickle

from src.ConfigParser import parse as parse_config
from src.ProjectParser import parse as parse_project
from src.models.ApplicationConfig import ApplicationConfig
from src.models.JobConfig import JobConfig
from src.models.Project import Project
from src.models.TrackConfig import TrackConfig
from src.ustx.UstxExport import export

CONFIG_FILE_PATH = "./config.yml"

PROGRAM_DESCRIPTION = \
    'CLI application Transform MusicXML (*.mxl, *.xml, *.musicxml, *.midi)' + \
    ' into OpenUTAU *.ustx for Singing Voice Synthesis'


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=PROGRAM_DESCRIPTION)
    parser.add_argument('input_file', type=str,
                        help='Input file to convert: [*.xml, *.musicxml, *.mxl, *.midi]')
    parser.add_argument('output_file', type=str,
                        help='Output file to create - example: outfile.ustx')
    parser.add_argument('--project_name', type=str, default='My Project', required=False,
                        help='Name of the project, stored in the output file metadata')
    parser.add_argument('--config_file', type=str, default=CONFIG_FILE_PATH, required=False,
                        help='Path to the config.yml file you want to use')
    parser.add_argument('--track_config', type=str, default=None, required=False,
                        help='Track config to use for this conversion, from config.yml')
    parser.add_argument('--voice', type=str, default=[], required=False, action='append',
                        help='Voice id used for each track, from config.yml')
    parser.add_argument('--pan', type=float, default=[], required=False, action='append',
                        help='Pan setting used for each track (-100.0 to 100.0)')
    parser.add_argument('--volume', type=float, default=[], required=False, action='append',
                        help='Volume setting used for each track (-10.0 to 10.0)')
    parser.add_argument('--track', type=str, default=[], required=False, action='append',
                        help='Name used for each track')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Print debug information')
    return parser


def main():
    args = build_cli_parser().parse_args()

    input_file: str = args.input_file
    output_file: str = args.output_file
    project_name: str = args.project_name
    config_file: str = args.config_file
    track_config_id: Optional[str] = args.track_config
    voice_config_ids: List[str] = args.voice
    volumes: List[float] = args.volume
    pans: List[float] = args.volume
    tracks: List[str] = args.track
    debug: bool = args.debug

    if debug:
        print(f'Parsed the following arguments from the CLI: \n{dumps(args)}\n')

    # load application config from the file
    application_config: ApplicationConfig = parse_config(config_file)

    track_configs: List[TrackConfig] = []

    # Track config id takes precedence for parsed settings
    if track_config_id is not None:
        if track_config_id not in application_config.track_config_map:
            raise RuntimeError(f'Track config {track_config_id} not found in {config_file}')
        track_configs = application_config.track_config_map[track_config_id]

    # Otherwise use the voice data
    if len(track_configs) == 0:
        len_tracks: int = len(tracks)
        len_volumes: int = len(volumes)
        len_pans: int = len(pans)
        len_voices: int = len(voice_config_ids)
        track_configs_to_create: int = max(len_tracks, len_volumes, len_pans, len_voices)
        for i in range(track_configs_to_create):
            pan = 0
            volume = 0
            track = f'Track {i+1}'
            voice = application_config.voice_config_map['default']

            if i < len_pans:
                pan = pans[i]

            if i < len_volumes:
                volume = volumes[i]

            if i < len_tracks:
                track = tracks[i]

            if i < len_voices:
                voice_id: str = voice_config_ids[i]
                if voice_id not in application_config.voice_config_map:
                    raise RuntimeError(f'Did not find voice id {voice_id} in {config_file}')
                voice = application_config.voice_config_map[voice_id]

            track_config: TrackConfig = TrackConfig(name=track, voice=voice, pan=pan, volume=volume)
            track_configs.append(track_config)

    # If we still do not have a track config, make a generic one
    if len(track_configs) == 0:
        voice = application_config.voice_config_map['default']
        track_configs = [TrackConfig(name='New Track', voice=voice, pan=0, volume=0)]

    # Build a job from our configuration
    job: JobConfig = JobConfig(
        input_file=input_file,
        output_file=output_file,
        name=project_name,
        track_configs=track_configs,
        default_lyric=application_config.default_lyric)

    # print debug information
    if debug:
        print(f'Running job with the following config:\n{dumps(job)}\n')

    # Parse the job into a project context
    project: Project = parse_project(job)

    if (debug):
        print(f'Parsed the following project:\n{dumps(project)}\n')

    # Export the project as a USTX file
    export(project, job.output_file)


def dumps(obj):
    return jsonpickle.dumps(obj, indent=2, unpicklable=False)


if __name__ == '__main__':
    main()


