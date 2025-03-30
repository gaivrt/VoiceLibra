# 电子书转有声书项目

本项目将电子书自动转换为有声书，使用 **Fish-Speech** 文本转语音（TTS）引擎，支持章节拆分和章节元数据。项目提供了基于 **Gradio** 的网页界面，方便上传电子书和参考音频并生成有声书文件。

## 项目特点

-   **多格式电子书输入**：支持 `.epub`, `.pdf`, `.mobi`, `.txt`, `.html`, `.rtf`, `.chm`, `.lit`, `.pdb`, `.fb2`, `.odt`, `.cbr`, `.cbz`, `.prc`, `.lrf`, `.pml`, `.snb`, `.cbc`, `.rb`, `.tcr` 等格式作为输入（通过调用 **Calibre** 将各种格式统一转换为 `EPUB` 进行解析）。对于 `EPUB` 和 `MOBI` 格式，将优先利用其章节结构。
-   **高质量语音合成**：集成 **Fish-Speech TTS** 引擎，通过本地API服务进行文本转语音。支持上传参考音频进行**声音克隆**，可合成指定音色（支持中、英、日等多语言）。
-   **章节划分输出**：按照原电子书章节生成音频，每章节单独合成语音。在最终输出时，利用 **FFmpeg** 将所有章节音频合并为一个音频文件，并嵌入章节元数据（章节名称和时间点），便于在支持章节的播放器中跳转。
-   **多种输出格式**：支持输出为常见有声书/音频格式，包括 `m4b` (Audiobook格式), `mp3`, `wav`, `aac`, `flac` 等。对于 `M4B` 等 MP4 容器，将嵌入章节信息供播放器识别。
-   **简洁的Web界面**：提供基于 **Gradio** 的用户界面，可直接在浏览器中操作：
    -   上传电子书文件（或提供本地路径）
    -   （可选）上传参考音频文件以克隆声音
    -   选择输出音频格式
    -   预览章节拆分情况
    -   点击转换后显示实时进度条
    -   每章节生成完毕后，即刻在界面提供音频播放器播放预览
    -   转换完成后提供最终合并的有声书文件供下载

## 部署与运行

### 环境要求

-   Python 3.10 及以上
-   NVIDIA GPU 环境（建议）用于运行 Fish-Speech 模型，加速语音合成（CPU 也可运行但速度较慢）
-   已安装 [Calibre](https://calibre-ebook.com/) 软件（用于电子书格式转换，确保命令行工具 `ebook-convert` 可用）
-   已安装 [FFmpeg](https://ffmpeg.org/)（用于音频合并和格式转换）
-   已安装并启动 **Fish-Speech** 本地 API 服务：
    -   请参考 [Fish-Speech 项目](https://github.com/fishaudio/fish-speech) 获取模型文件并启动 API 服务。例如，按照官方文档下载 Fish-Speech 模型权重，然后运行：
        ```bash
        python -m tools.api_server --listen 0.0.0.0:8080 --llama-checkpoint-path <路径到模型检查点> --decoder-checkpoint-path <路径到声码器权重> --decoder-config-name firefly_gan_vq
        ```
    -   确认 Fish-Speech 服务在本地 `127.0.0.1:8080` 运行（默认 API 地址为 `http://127.0.0.1:8080/v1/tts`）。

### 安装依赖

1.  克隆本项目代码。
2.  安装 Python 依赖：
    ```bash
    pip install -r requirements.txt
    ```
3.  请确保 `Calibre` 和 `FFmpeg` 已正确安装，并启动 `Fish-Speech` 本地服务。

### 启动应用

运行主程序以启动 Gradio 网页界面：

```bash
python main.py
```

启动后，终端会输出本地访问地址（默认 `http://127.0.0.1:7860`）。在浏览器中打开该地址即可看到界面。

## 使用方法

1.  **上传电子书**：在界面左侧，上传电子书文件（支持上文列出的大多数格式）。
2.  **预览章节**：上传后点击 “**Preview Chapters**” 按钮，程序会解析电子书并显示检测到的章节列表。您可以预览章节标题，确认章节划分是否正确。
3.  **（可选）上传参考音频**：上传一段参考音频文件（如 `.wav`, `.mp3` 等），如您希望合成的语音与某人的声音相似。参考音频应为10~30秒的清晰录音，无背景噪音。当前版本中，参考音频需搭配对应的文本才能更好地克隆声音（如果缺少文本，本项目会仍然尝试零样本克隆）。
4.  **选择输出格式**：选择输出音频格式。例如选择 `m4b` 将输出适合有声书的 M4B 文件（支持章节跳转）；选择 `mp3` 等则输出普通音频文件。
5.  **开始转换**：点击 “**Convert to Audio**” 按钮开始转换。界面将显示每个章节的合成进度。当某章节语音合成完成时，该章节的音频播放器会出现在页面中，您可以即时播放预览。
6.  **下载结果**：所有章节处理完成后，程序会自动使用 `FFmpeg` 合并音频并插入章节元数据。完成后，界面将显示 “Conversion completed!” 字样，并提供最终合成的有声书文件供下载（界面底部的下载控件）。点击下载链接保存最终的有声书音频文件。

## 运行示例

假设您有一本名为 `example.epub` 的电子书，以及一段您自己的声音录音 `voice.wav` 想用于有声书的讲述：

1.  启动本项目界面。
2.  上传 `example.epub` 和 `voice.wav` 文件。
3.  点击 “**Preview Chapters**” 确认章节无误。
4.  选择输出格式为 `m4b`。
5.  点击 “**Convert to Audio**” 开始转换。
6.  转换过程中将逐章显示进度，例如 “Synthesizing chapter 1/10: Introduction”。
7.  完成后，下载得到 `example.m4b` 文件。用支持有声书的 App 打开，可以看到章节信息与您上传的录音音色合成的语音。

## 注意事项

-   确保电子书语言与合成语言一致。**Fish-Speech** 模型支持多语言，无需额外指定语言，但若电子书中含多种语言，可能影响合成效果。
-   首次运行 **Fish-Speech TTS** 模型时会有模型加载时间，请耐心等待 API 服务就绪（可能需要数分钟）。
-   如果转换过程中发生错误（如 TTS 服务未响应或 `FFmpeg` 合并失败），界面将显示错误信息。请根据提示检查 `Fish-Speech` 服务是否在运行、输入文件是否有效等。
-   本项目生成的音频仅供个人学习或辅助使用，请遵守相关版权法规，不要用于未经授权的内容传播。

## 文件结构

-   `main.py`：入口脚本，启动 Gradio 应用。
-   `parser.py`：电子书解析模块，负责调用 `Calibre` 将输入转换为 `EPUB` 并提取章节文本。
-   `tts_fish.py`：TTS 合成模块，封装对 `Fish-Speech` 本地 API 的调用，实现文本到语音的转换（支持参考音频进行声音克隆）。
-   `ui.py`：界面逻辑模块，定义 Gradio 界面布局和交互功能，包括文件上传、章节预览、转换进度和结果展示。
-   `requirements.txt`：Python 依赖列表。
-   `README.md`：项目说明文档（本文件）。

## 部分代码实现细节

-   **章节提取**：通过 `ebooklib` 解析 `EPUB` 文件，提取章节标题和正文。如果电子书无明显章节（例如纯文本文件），则视整个内容为单一章节。
-   **语音合成**：对每个章节文本调用 `Fish-Speech` 的 `/v1/tts` 接口。若提供参考音频，则通过 `MessagePack` 请求发送音频数据和文本实现零样本声音克隆；否则直接使用默认合成声音。每章音频先以 `WAV` 格式保存。
-   **章节合并**：所有章节音频生成后，使用 `FFmpeg` 的 `concat` 功能合并。对于 MP4 容器格式（`m4b`/`m4a`/`mp4` 等），在合并时附加章节元数据文件，使输出文件包含章节信息。对于 `mp3` 等不支持章节的格式，则简单串联输出。
-   **Gradio 界面**：采用 `gr.File` 组件上传文件，`gr.Dropdown` 选择格式，`gr.Button` 触发动作。通过 `gr.HTML` 动态显示章节列表和进度信息，并使用内嵌的 HTML5 `<audio>` 标签实现章节音频的在线播放预览。最终输出使用 `gr.File` 提供可下载链接。

## 致谢

本项目基于开源工具 `Calibre` 和 `FFmpeg`，以及 `Fish-Speech TTS` 模型的强大能力。感谢这些开源项目的贡献者。