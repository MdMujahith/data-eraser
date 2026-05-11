"""Load and validate YAML configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from privacy_toolkit.config.schemas import BrokersFile, UserProfileConfig
from privacy_toolkit.core.exceptions import ConfigError
from privacy_toolkit.core.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_BROKERS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "brokers.sample.yaml"
_DEFAULT_PROFILE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "profile.sample.yaml"


def load_brokers(path: Optional[Path] = None) -> BrokersFile:
    """Load and validate a brokers YAML file.

    Args:
        path: Override path; falls back to ``data/brokers.sample.yaml``.

    Returns:
        Validated :class:`BrokersFile`.

    Raises:
        :class:`ConfigError`: If the file is missing or invalid.
    """
    resolved = path or _DEFAULT_BROKERS_PATH
    if not resolved.exists():
        raise ConfigError(f"Brokers config not found: {resolved}")
    try:
        raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        return BrokersFile.model_validate(raw or {})
    except (yaml.YAMLError, ValidationError) as exc:
        raise ConfigError(f"Invalid brokers config at {resolved}: {exc}") from exc


def load_user_profile(path: Optional[Path] = None) -> Optional[UserProfileConfig]:
    """Load and validate a user profile YAML file.

    Returns ``None`` if no profile file exists (user hasn't set one up yet).
    """
    resolved = path or _DEFAULT_PROFILE_PATH
    if not resolved.exists():
        logger.info("No user profile found at %s — run `privacy-toolkit init` to create one.", resolved)
        return None
    try:
        raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
        return UserProfileConfig.model_validate(raw or {})
    except (yaml.YAMLError, ValidationError) as exc:
        raise ConfigError(f"Invalid profile config at {resolved}: {exc}") from exc


def save_user_profile(profile: UserProfileConfig, path: Path) -> None:
    """Serialise and write a user profile to YAML.

    Args:
        profile: The profile to save.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(profile.model_dump(exclude_none=True), default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )
    logger.info("Profile saved to %s", path)
