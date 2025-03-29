import os
import platform

# 基础路径配置
models_dir = os.path.abspath('models')
ebooks_dir = os.path.abspath('ebooks')
voices_dir = os.path.abspath('voices')
tmp_dir = os.path.abspath('tmp')
tmp_expire = 7  # days

# 环境变量设置
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['TORCH_HOME'] = models_dir

# Fish-Speech相关配置
NATIVE = 'native'
FULL_DOCKER = 'full_docker'
debug_mode = True

# 音频处理设置
default_audio_proc_format = 'wav'
voice_formats = ['.wav', '.mp3', '.ogg', '.m4a', '.flac']

# UI配置
max_custom_voices = 10  # 最大自定义语音数量
max_custom_models = 5   # 最大自定义模型数量
max_tts_in_memory = 2  # 内存中最大TTS模型数量

# 性能配置
interface_concurrency_limit = 1
interface_host = '0.0.0.0'
interface_port = 7860
max_upload_size = 100  # MB