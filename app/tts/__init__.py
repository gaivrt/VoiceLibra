# app/tts/__init__.py
from .inference_engine import TTSInferenceEngine
from .webui import WebUI
from .utils.schema import ServeTTSRequest

__version__ = "1.0.0"
__all__ = ["TTSInferenceEngine", "WebUI", "ServeTTSRequest"]