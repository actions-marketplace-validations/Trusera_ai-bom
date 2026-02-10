"""Configuration file discovery and loading for AI-BOM.

Supports .ai-bom.yml or .ai-bom.yaml configuration files that can be
placed in the project root or specified via --config CLI flag.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILENAMES = [".ai-bom.yml", ".ai-bom.yaml"]


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """Search for a config file starting from the given directory.

    Searches for .ai-bom.yml or .ai-bom.yaml in the start directory,
    then walks up parent directories until found or root is reached.

    Args:
        start_dir: Directory to start searching from. Defaults to CWD.

    Returns:
        Path to the config file if found, None otherwise.
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    while True:
        for filename in DEFAULT_CONFIG_FILENAMES:
            config_path = current / filename
            if config_path.is_file():
                logger.debug("Found config file: %s", config_path)
                return config_path

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load configuration from a YAML file.

    If no path is specified, searches for config file automatically.

    Args:
        path: Explicit path to config file. If None, auto-discovers.

    Returns:
        Configuration dictionary. Empty dict if no config found.
    """
    if path is None:
        path = find_config_file()

    if path is None:
        return {}

    if not path.is_file():
        logger.warning("Config file not found: %s", path)
        return {}

    try:
        content = path.read_text(encoding="utf-8")
        config = yaml.safe_load(content) or {}
        if not isinstance(config, dict):
            logger.warning("Config file must contain a YAML mapping, got %s", type(config).__name__)
            return {}
        logger.debug("Loaded config from %s: %s", path, config)
        return config
    except yaml.YAMLError as e:
        logger.warning("Failed to parse config file %s: %s", path, e)
        return {}
    except OSError as e:
        logger.warning("Failed to read config file %s: %s", path, e)
        return {}


def merge_config_with_cli(
    config: dict[str, Any],
    cli_args: dict[str, Any],
) -> dict[str, Any]:
    """Merge config file values with CLI arguments.

    CLI arguments always take precedence over config file values.
    Only config values for keys not explicitly set on CLI are used.

    Args:
        config: Configuration from .ai-bom.yml
        cli_args: Arguments from CLI (only non-None values override)

    Returns:
        Merged configuration dictionary.
    """
    merged = dict(config)
    for key, value in cli_args.items():
        if value is not None:
            merged[key] = value
    return merged
