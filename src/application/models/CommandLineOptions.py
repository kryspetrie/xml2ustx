from typing import Optional, List


class CommandLineOptions:
    def __init__(self,
                 input_file: Optional[str],
                 input_dir: Optional[str],
                 output_file: Optional[str],
                 config_file: Optional[str],
                 project_name: Optional[str],
                 track_config_id: Optional[str],
                 voice_config_ids: List[str],
                 volumes: Optional[List[float]],
                 pans: Optional[List[float]],
                 tracks: Optional[List[str]],
                 debug: bool):
        self.input_file = input_file
        self.input_dir = input_dir
        self.output_file = output_file
        self.config_file = config_file
        self.project_name = project_name
        self.track_config_id = track_config_id
        self.voice_config_ids = voice_config_ids
        self.volumes = volumes
        self.pans = pans
        self.tracks = tracks
        self.debug = debug
