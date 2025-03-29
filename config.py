import os
from pathlib import Path
import torch

# 基础路径配置
BASE_DIR = Path(__file__).parent.absolute()
MODELS_DIR = BASE_DIR / "models"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Fish-Speech模型配置
MODEL_PATH = MODELS_DIR / "fish-speech-1.5"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 音频处理配置
SAMPLE_RATE = 24000
MAX_WAV_LENGTH = 60  # 最大音频长度(秒)
AUDIO_FORMATS = [".wav", ".mp3", ".ogg", ".m4a", ".flac"]

# Web服务配置
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB

# Fish-Speech模型参数
MODEL_CONFIG = {
    "semantic_dim": 1024,
    "hidden_dim": 512,
    "n_layers": 8,
    "n_heads": 8,
    "codebook_size": 8192
}

# 默认推理参数
DEFAULT_INFERENCE_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.7,
    "repetition_penalty": 1.2
}

# 创建必要的目录
for dir_path in [MODELS_DIR, UPLOADS_DIR, OUTPUTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)