"""
VoiceLibra 电子书处理模块
基于Fish-Speech的TTS引擎实现电子书到有声书的转换
"""

from .functions import convert_ebook, convert_ebook_batch
from .models import models, default_tts_engine, default_fine_tuned, default_fish_speech_settings

__version__ = "1.0.0"
__all__ = [
    "convert_ebook",
    "convert_ebook_batch",
    "models",
    "default_tts_engine",
    "default_fine_tuned",
    "default_fish_speech_settings"
]