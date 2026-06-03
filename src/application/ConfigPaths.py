"""Resolve config file paths for CLI and bundled sidecar use."""
import os
from src.resources.Resources import get_resource_path

DEFAULT_CONFIG_FILE = get_resource_path("config.yml")
CONFIG_ENV_VAR = "XML2USTX_CONFIG"


def resolve_config_file(cli_path: str | None) -> str:
    """Config from --config_file, then XML2USTX_CONFIG, then bundled default."""
    if cli_path is not None:
        return cli_path
    env_path = os.environ.get(CONFIG_ENV_VAR)
    if env_path:
        return env_path
    return str(DEFAULT_CONFIG_FILE)
