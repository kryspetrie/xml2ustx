import argparse

from src.Utils import dumps
from src.application.models.CommandLineOptions import CommandLineOptions
from src.application.Strings import PROGRAM_DESCRIPTION


def parse() -> CommandLineOptions:
    # Build the parser
    parser = argparse.ArgumentParser(description=PROGRAM_DESCRIPTION)
    parser.add_argument('input_file', type=str,
                        help='Input file to convert: [*.xml, *.musicxml, *.mxl, *.midi]')
    parser.add_argument('output_file', type=str,
                        help='Output file to create - example: outfile.ustx')
    parser.add_argument('--project_name', type=str, default='My Project', required=False,
                        help='Name of the project, stored in the output file metadata')
    parser.add_argument('--config_file', type=str, required=False,
                        help='Path to the config.yml file you want to use')
    parser.add_argument('--track_config', type=str, default=None, required=False,
                        help='Track config to use for this conversion, from config.yml')
    parser.add_argument('--voice', type=str, required=False, action='append',
                        help='Voice id used for each track, from config.yml')
    parser.add_argument('--pan', type=float, required=False, action='append',
                        help='Pan setting used for each track (-100.0 to 100.0)')
    parser.add_argument('--volume', type=float, required=False, action='append',
                        help='Volume setting used for each track (-10.0 to 10.0)')
    parser.add_argument('--track', type=str, required=False, action='append',
                        help='Name used for each track')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Print debug information')

    # Actually parse the provided args
    args = parser.parse_args()

    # rewrite the outfile to adhere to output format
    output_file: str = args.output_file
    if not output_file.lower().endswith(".ustx"):
        output_file = output_file + ".ustx"

    # Return the options as an defined object
    options = CommandLineOptions(
        input_file=args.input_file,
        output_file=output_file,
        config_file=args.config_file,
        project_name=args.project_name,
        track_config_id=args.track_config,
        voice_config_ids=args.voice,
        volumes=args.volume,
        pans=args.pan,
        tracks=args.track,
        debug=args.debug)

    if args.debug:
        print(f'Parsed the following arguments from the CLI: \n{dumps(args)}\n')

    return options
