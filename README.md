# VoiceLibra

基于 Fish-Speech 的电子书语音合成系统，支持将电子书转换为自然的中文语音。

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ 功能特点

- 🎯 基于 Fish-Speech 的高质量中文语音合成
- 🎤 支持参考音频克隆声音
- 🌐 提供 Web 界面和 REST API 接口
- 📚 支持多种格式电子书批量转换 (EPUB, PDF, TXT)
- 🛠 智能的文本预处理和语音后处理
- 🚀 GPU 加速支持
- 🔄 异步任务处理
- 📊 实时转换进度监控

## 🔧 系统要求

- Python 3.8 或更高版本
- CUDA 11.4+ (推荐，支持 CPU 运行)
- 8GB+ RAM
- 10GB+ 磁盘空间 (包含模型)

## 📦 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/VoiceLibra.git
cd VoiceLibra
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 下载模型：
```bash
python run.py download
```

## 🚀 快速开始

### Web 界面

启动 Web 服务：
```bash
python run.py webui
```

可选参数：
- `--host`: 服务器主机名 (默认: 0.0.0.0)
- `--port`: 服务器端口 (默认: 5000)
- `--debug`: 调试模式 (默认: False)
- `--share`: 公开分享 (默认: False)

访问 `http://localhost:5000` 使用 Web 界面。

### REST API

主要接口：

- `GET /api/health` - 健康检查
- `POST /api/upload` - 上传电子书
- `GET /api/status/<job_id>` - 获取任务状态
- `GET /api/download/<file_id>` - 下载生成的音频

完整 API 文档请访问 `http://localhost:5000/api/docs`

### 命令行工具

1. 基础文本转语音：
```bash
python run.py tts --text "要转换的文本" --output output.wav
```

2. 声音克隆：
```bash
python run.py tts --text "要转换的文本" --output output.wav --reference voice.wav
```

3. 电子书批量转换：
```bash
python run.py convert --input book.epub --output-dir ./outputs
```

## ⚙️ 配置说明

配置文件位于 `config.py`：

```python
# 基础配置
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"

# 模型配置
MODEL_PATH = MODELS_DIR / "fish-speech-1.5"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 音频配置
SAMPLE_RATE = 24000
MAX_WAV_LENGTH = 1200  # 秒
AUDIO_FORMATS = ["wav", "mp3", "ogg"]
```

## 🔍 高级功能

### 批量处理 API

```python
from app.book_processing.lib import convert_ebook_batch

args = {
    'ebook_list': ['book1.epub', 'book2.epub'],
    'language': 'zho',     # 中文
    'device': 'cuda',      # 使用GPU
    'output_format': 'mp3',
    'chunk_size': 1000,    # 分块大小
    'parallel': True       # 并行处理
}

convert_ebook_batch(args)
```

### 自定义文本预处理

支持自定义文本预处理规则，详见 `app/book_processing/lib/functions.py`

## 📝 注意事项

- 推荐使用 CUDA 加速，CPU 推理较慢
- 参考音频建议：
  - 时长：5-30 秒
  - 格式：24kHz WAV
  - 内容：清晰的单人说话声音
- 大文件处理建议：
  - 使用异步任务模式
  - 适当调整 chunk_size
  - 监控系统资源使用

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📚 相关资源

- [Fish-Speech 项目](https://github.com/fishaudio/fish-speech)
- [项目文档](docs/index.md)
- [常见问题](docs/faq.md)
- [更新日志](CHANGELOG.md)

## 🌟 致谢

- Fish-Speech 团队提供的优秀基础模型
- 所有贡献者和用户的支持