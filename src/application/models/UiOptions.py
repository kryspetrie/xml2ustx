from typing import Optional


class UiOptions:
    def __init__(self, input_file: str, track_config_id: Optional[str]):
        self.input_file = input_file
        self.track_config_id = track_config_id
