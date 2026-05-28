"""Platform registry — maps platform keys to Platform instances."""

from agent.platforms.base import Platform
from agent.platforms.deepseek import DeepSeekPlatform
from agent.platforms.doubao import DoubaoPlatform

# All available platforms
ALL: dict[str, Platform] = {
    "deepseek": DeepSeekPlatform(),
    "doubao": DoubaoPlatform(),
}


def get_platform(key: str) -> Platform:
    """Return the Platform instance for *key*. Raises KeyError if unknown."""
    if key not in ALL:
        raise KeyError(f"Unknown platform: {key}. Available: {list(ALL.keys())}")
    return ALL[key]


def resolve_platforms(keys: list[str] | None) -> list[Platform]:
    """Resolve a list of platform keys to Platform instances.

    If *keys* is empty or None, defaults to ``["deepseek"]``.
    """
    if not keys:
        keys = ["deepseek"]
    return [get_platform(k) for k in keys]
