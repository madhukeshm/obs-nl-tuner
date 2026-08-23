"""obs_tune — natural-language OBS Studio tuner backed by Claude or ChatGPT."""

__version__ = "1.1.0"

__all__ = ["OBSController", "OBSError", "__version__"]

from .obs_actions import OBSController, OBSError
