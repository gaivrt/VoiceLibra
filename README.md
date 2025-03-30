# VoiceLibra - 电子书转有声书项目
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Fish-Speech](https://img.shields.io/badge/TTS-Fish--Speech-orange)](https://github.com/fishaudio/fish-speech)
[![Gradio](https://img.shields.io/badge/UI-Gradio-brightgreen)](https://gradio.app/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📖 项目简介

VoiceLibra 是一个将电子书自动转换为有声书的智能工具。它使用 **Fish-Speech** TTS引擎提供高质量的语音合成，支持智能章节拆分，并生成包含完整章节元数据的有声书文件。项目提供了基于 **Gradio** 的直观Web界面，让转换过程变得简单易用。

### ✨ 主要特性

- 🔄 **多格式支持**：支持20+种电子书格式输入 (epub/pdf/mobi等)
- 🎯 **智能解析**：自动识别章节结构，智能分割内容
- 🗣️ **高质量TTS**：集成Fish-Speech引擎，支持多语言
- 🎤 **声音克隆**：支持上传参考音频实现声音克隆
- 📑 **元数据支持**：在有声书中保留完整章节信息
- 🎵 **多格式输出**：支持m4b/mp3/wav等多种音频格式
- 🌐 **Web界面**：提供友好的Gradio操作界面

## 🚀 快速开始

### 环境要求

- Python >= 3.10
- NVIDIA GPU（推荐，但CPU也可运行）
- [Calibre](https://calibre-ebook.com/)
- [FFmpeg](https://ffmpeg.org/)
- [Fish-Speech](https://github.com/fishaudio/fish-speech) API服务

### 安装步骤

1. 克隆项目：
```bash
git clone https://github.com/yourusername/VoiceLibra.git
cd VoiceLibra
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动Fish-Speech服务：
```bash
python -m tools.api_server --listen 0.0.0.0:8080 --llama-checkpoint-path <model_path> --decoder-checkpoint-path <decoder_path> --decoder-config-name firefly_gan_vq
```

4. 启动应用：
```bash
python main.py
```

访问 http://127.0.0.1:7860 即可看到界面

## 💡 使用指南

### 基本流程

1. **准备文件**
   - 上传电子书文件（支持epub/pdf/mobi等）
   - (可选) 上传参考音频进行声音克隆

2. **预览配置**
   - 点击"预览章节"检查章节划分
   - 选择输出音频格式(m4b/mp3等)
   - 调整其他参数（如有）

3. **开始转换**
   - 点击"转换为有声书"
   - 等待转换完成，期间可预览各章节
   - 下载最终的有声书文件

### 高级功能

- **声音克隆**：上传10-30秒的清晰录音，搭配对应文本效果更佳
- **章节定制**：支持手动调整章节划分
- **元数据定制**：可自定义章节标题和时间点

## 🔧 技术架构

### 核心模块

- **解析引擎** (parser.py)
  - 基于ebooklib的EPUB解析
  - 智能章节识别算法
  - 文本预处理优化

- **语音引擎** (tts_fish.py)
  - Fish-Speech API集成
  - 声音克隆处理
  - 多语言支持

- **界面模块** (ui.py)
  - Gradio交互界面
  - 实时进度显示
  - 音频预览功能

### 数据流

```
电子书文件 -> 解析引擎 -> 章节文本 -> TTS引擎 -> 音频片段 -> 音频合并 -> 有声书
```

## 📝 开发指南

### 项目结构
```
VoiceLibra/
├── main.py          # 程序入口
├── parser.py        # 解析模块
├── tts_fish.py      # TTS接口
├── ui.py           # 界面逻辑
├── config.json     # 配置文件
└── requirements.txt # 依赖清单
```

### 扩展开发

- **添加新格式**：扩展parser.py中的格式支持
- **自定义TTS**：修改tts_fish.py实现其他TTS接口
- **界面定制**：通过ui.py调整Gradio界面

## ⚠️ 注意事项

- 建议使用GPU进行语音合成，CPU下速度较慢
- 电子书应与TTS模型语言匹配以获得最佳效果
- 首次运行时模型加载需等待数分钟
- 请遵守版权法规，仅用于个人学习用途

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 👥 参与贡献

欢迎提交Issue和Pull Request！

## 🙏 致谢

感谢以下开源项目：
- [Fish-Speech](https://github.com/fishaudio/fish-speech)
- [Gradio](https://gradio.app/)
- [Calibre](https://calibre-ebook.com/)
- [FFmpeg](https://ffmpeg.org/)