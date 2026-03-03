"""Converter registry — maps tool keys to ManimConverter instances."""

from manim_converters.base import ManimConverter  # noqa: F401

CONVERTER_REGISTRY: dict[str, ManimConverter] = {}


def register_converter(tool_key):
    """Decorator to register a converter class for a tool key."""
    def decorator(cls):
        CONVERTER_REGISTRY[tool_key] = cls()
        return cls
    return decorator


def get_converter(tool_key):
    """Return the converter instance for a tool key, or None."""
    return CONVERTER_REGISTRY.get(tool_key)


def get_available_scenes(tool_key):
    """Return list of scene dicts available for a tool."""
    conv = get_converter(tool_key)
    return conv.supported_scenes() if conv else []


# Import converters module to trigger all @register_converter decorators
from manim_converters import converters  # noqa: F401, E402
