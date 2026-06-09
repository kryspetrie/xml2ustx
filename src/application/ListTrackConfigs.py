"""List track_config ids from a config file (for OpenUtau and CLI)."""
import sys

import yaml


def list_groove_preset_ids(config_path: str) -> list[str]:
    with open(config_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not data or 'groove_presets' not in data:
        return []
    ids: list[str] = []
    for entry in data['groove_presets']:
        if isinstance(entry, dict) and 'id' in entry:
            ids.append(str(entry['id']))
    return ids


def list_swing_preset_ids(config_path: str) -> list[str]:
    with open(config_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not data or 'swing_presets' not in data:
        return []
    ids: list[str] = []
    for entry in data['swing_presets']:
        if isinstance(entry, dict) and 'id' in entry:
            ids.append(str(entry['id']))
    return ids


def list_track_config_ids(config_path: str) -> list[str]:
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "track_config" not in data:
        return []
    ids: list[str] = []
    for entry in data["track_config"]:
        if isinstance(entry, dict) and "id" in entry:
            ids.append(str(entry["id"]))
    return ids


def main(config_path: str) -> int:
    try:
        for track_id in list_track_config_ids(config_path):
            print(track_id)
        return 0
    except OSError as e:
        print(f"Failed to read config: {e}", file=sys.stderr)
        return 1
    except yaml.YAMLError as e:
        print(f"Invalid YAML: {e}", file=sys.stderr)
        return 1
