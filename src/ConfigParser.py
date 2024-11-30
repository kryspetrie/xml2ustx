import yaml
from typing import Dict, Tuple, List

from src.models.TrackConfig import TrackConfig
from src.models.Voice import Voice
from src.models.ApplicationConfig import ApplicationConfig


def __parse_voice_config_tuple(voice_config_dict: Dict) -> Tuple[str, Voice]:
    if 'id' not in voice_config_dict:
        raise RuntimeError("Bad voice config. Could not find id.")

    voice_id: str = voice_config_dict['id']
    singer: str = voice_config_dict['singer'] if 'singer' in voice_config_dict else None
    renderer: str = voice_config_dict['renderer'] if 'renderer' in voice_config_dict else None
    phonemizer: str = voice_config_dict['phonemizer'] if 'phonemizer' in voice_config_dict else None

    return voice_id, Voice(renderer=renderer, phonemizer=phonemizer, singer=singer)


def __parse_track_config_item(track_config_item_dict: Dict, voices: Dict[str, Voice]) -> TrackConfig:
    name: str = track_config_item_dict['track_name'] if 'track_name' in track_config_item_dict else None
    voice_id: str = track_config_item_dict['voice_id'] if 'voice_id' in track_config_item_dict else None
    pan: float = track_config_item_dict['pan'] if 'pan' in track_config_item_dict else 0.0
    volume: float = track_config_item_dict['volume'] if 'volume' in track_config_item_dict else 0.0

    if voice_id not in voices:
        raise RuntimeError(f'Voice id {voice_id} in track config was not found in voice config.')

    return TrackConfig(name=name, voice=voices[voice_id], pan=pan, volume=volume)


def __parse_track_config_tuple(track_config_dict: Dict, voices: Dict[str, Voice]) -> Tuple[str, List[TrackConfig]]:
    if 'id' not in track_config_dict:
        raise RuntimeError("Bad track config. Could not find id.")

    track_group_id: str = track_config_dict['id']

    if 'tracks' not in track_config_dict:
        raise RuntimeError(f'Back track config. No tracks found for id: {track_group_id}')

    track_configs: List[TrackConfig] = [__parse_track_config_item(it, voices) for it in track_config_dict['tracks']]

    return (track_group_id, track_configs)


def parse(file: str) -> ApplicationConfig:
    config_yaml = None
    with open(file) as stream:
        try:
            config_yaml = yaml.safe_load(stream)
        except yaml.YAMLError as exception:
            RuntimeError(exception)

    voice_configs_tuple = [__parse_voice_config_tuple(it) for it in config_yaml['voice_config']]
    voice_config_map = dict((id, voice) for id, voice in voice_configs_tuple)

    track_configs_tuple = [__parse_track_config_tuple(it, voice_config_map) for it in config_yaml['track_config']]
    track_config_map = dict((id, tracks) for id, tracks in track_configs_tuple)

    return ApplicationConfig(voice_config_map=voice_config_map, track_config_map=track_config_map)
