import os
import shutil
import base64
import wave
import subprocess
import gradio as gr
import io

from debug_log import log_message, log_error, log_file_status
from parser import convert_to_epub, parse_epub, get_first_paragraph
from tts_fish import synthesize_text, test_voice_clone, TTSClient

# 创建全局TTS客户端实例
tts_client = TTSClient()

def test_voice_cloning(reference_audio):
    """Test voice cloning with a sample sentence"""
    if not reference_audio:
        return "请先上传参考音频文件。", None
    try:
        audio_bytes = test_voice_clone(reference_audio.name)
        # Save temporary wav file for preview
        temp_file = "output/voice_test.wav"
        os.makedirs("output", exist_ok=True)
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)
        return "克隆声音测试完成！请听下面的音频预览：", temp_file
    except Exception as e:
        return f"声音克隆测试失败: {str(e)}", None

def test_chapter_synthesis(state, reference_audio, chapter_index):
    """Test synthesize first paragraph of selected chapter"""
    if not state or "chapters" not in state:
        return "请先上传并解析电子书。", None
    
    chapters = state["chapters"]
    if not (0 <= chapter_index < len(chapters)):
        return "无效的章节索引。", None
        
    chapter = chapters[chapter_index]
    first_para = get_first_paragraph(chapter["text"])
    if not first_para:
        return "无法获取章节内容。", None
        
    try:
        ref_path = reference_audio.name if reference_audio else None
        audio_bytes = synthesize_text(first_para, ref_path)
        # Save temporary wav file
        temp_file = f"output/chapter_{chapter_index+1}_test.wav"
        os.makedirs("output", exist_ok=True)
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)
        return f"章节 {chapter_index+1} 第一段合成完成！请听下面的音频预览：", temp_file
    except Exception as e:
        return f"章节测试合成失败: {str(e)}", None

def parse_book(file_obj):
    """
    Gradio event function to parse the uploaded book file into chapters.
    Returns (preview_html, state_dict).
    """
    if file_obj is None:
        return gr.update(value="No file uploaded."), {}
    # Determine original file path
    input_path = file_obj.name
    orig_name = getattr(file_obj, "orig_name", None)
    # Convert to EPUB if needed
    try:
        epub_path = convert_to_epub(input_path)
    except Exception as e:
        # Return error message in preview if conversion fails
        err_msg = f"<p style='color:red'><strong>Error:</strong> {str(e)}</p>"
        return gr.update(value=err_msg), {}
    # Parse EPUB to chapters
    try:
        book_title, chapters = parse_epub(epub_path)
    except Exception as e:
        err_msg = f"<p style='color:red'><strong>Failed to parse book:</strong> {str(e)}</p>"
        return gr.update(value=err_msg), {}
    # Save chapter list in state
    state = {
        "chapters": chapters,
        "book_title": book_title,
        "orig_name": orig_name if orig_name else os.path.basename(input_path)
    }
    # Generate preview HTML of chapter titles
    preview_lines = []
    for idx, ch in enumerate(chapters, start=1):
        title = ch["title"]
        # maybe limit length of title displayed
        if len(title) > 60:
            title_display = title[:57] + "..."
        else:
            title_display = title
        preview_lines.append(f"{idx}. {title_display}")
    preview_html = "<p><strong>Chapters Detected:</strong></p>\n" + "<br>".join(preview_lines)
    return gr.update(value=preview_html), state

def convert_to_audio(state, reference_audio, output_format, start_chapter, end_chapter):
    """
    Gradio event function to convert parsed chapters to audiobook.
    Uses Fish-Speech TTS for each chapter and ffmpeg to merge with metadata.
    """
    try:
        log_message("Starting convert_to_audio function")
        if not state or "chapters" not in state:
            log_message("No chapters found in state")
            yield "No chapters to convert. Please upload and parse a book first.", None, None
            return
            
        chapters = state["chapters"]
        book_title = state.get("book_title", "Audiobook")
        orig_name = state.get("orig_name", "output")
        total_chapters = len(chapters)

        # Validate chapter range
        start_chapter = max(1, min(int(start_chapter), total_chapters))
        end_chapter = max(start_chapter, min(int(end_chapter), total_chapters))
        
        # Get selected chapters
        selected_chapters = chapters[start_chapter-1:end_chapter]
        selected_total = len(selected_chapters)
        
        log_message(f"Processing book: {book_title}, chapters {start_chapter}-{end_chapter} of {total_chapters}, format: {output_format}")
        
        if selected_total == 0:
            log_message("No chapters found in selected range")
            yield "No chapters found in the selected range.", None, None
            return
            
        # Create output directory if not exists
        out_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(out_dir, exist_ok=True)
        log_message(f"Output directory: {out_dir}")

        # Generate audio for selected chapters
        chapter_files = []
        for idx, ch in enumerate(selected_chapters, start=1):
            chapter_title = ch["title"]
            chapter_text = ch["text"]
            
            progress_html = f"""
            <div style='padding: 10px; border: 1px solid #ccc; border-radius: 5px;'>
                <h4>正在处理章节 {start_chapter+idx-1}/{end_chapter} (进度: {idx}/{selected_total})</h4>
                <p>{chapter_title}</p>
                <div style='width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px;'>
                    <div style='width: {(idx-1)*100/selected_total}%; height: 100%; background: #4CAF50; border-radius: 10px;'></div>
                </div>
            </div>
            """
            yield progress_html, None, None
            
            try:
                # 合成文本
                audio_bytes = synthesize_text(chapter_text, reference_audio.name if reference_audio else None)
                
                # 保存章节音频
                chap_file = os.path.join(out_dir, f"temp_chapter_{start_chapter+idx-1:03d}.wav")
                with open(chap_file, "wb") as f:
                    f.write(audio_bytes)
                
                chapter_files.append((chapter_title, chap_file))
                
            except Exception as e:
                error_html = f"""
                <div style='padding: 15px; border: 1px solid #dc3545; border-radius: 5px;'>
                    <h3 style='color: #dc3545;'>❌ 合成失败</h3>
                    <p>章节 {start_chapter+idx-1}: {chapter_title}</p>
                    <p>错误: {str(e)}</p>
                </div>
                """
                yield error_html, None, None
                return

        # 显示合并进度
        merge_html = f"""
        <div style='padding: 10px; border: 1px solid #ccc; border-radius: 5px;'>
            <h4>正在合并音频文件...</h4>
            <div style='width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px;'>
                <div style='width: 100%; height: 100%; background: #4CAF50; border-radius: 10px;'></div>
            </div>
        </div>
        """
        yield merge_html, None, None
        
        # Prepare metadata file for chapters
        metadata_path = os.path.join(out_dir, "chapters.txt")
        supports_chapters = output_format.lower() in ["m4b", "m4a", "mp4", "mov", "webm"]
        chapter_durations_ms = []
        total_duration_ms = 0
        for (title, chap_file) in chapter_files:
            # Get duration in ms using wave module (since we saved as wav)
            try:
                w = wave.open(chap_file, 'rb')
                frames = w.getnframes()
                rate = w.getframerate()
                w.close()
                # integer milliseconds
                duration_ms = int(frames * 1000 / rate)
            except Exception:
                duration_ms = 0
            chapter_durations_ms.append(duration_ms)
        if supports_chapters:
            with open(metadata_path, "w", encoding="utf-8") as mf:
                mf.write(";FFMETADATA1\n")
                # Write global metadata
                mf.write(f"title={book_title if book_title else orig_name}\n")
                # Optionally, set album or artist metadata
                mf.write(f"artist=FishSpeech TTS\n")
                # Generate chapter metadata entries
                start_ms = 0
                for idx, (title, chap_file) in enumerate(chapter_files, start=1):
                    end_ms = start_ms + (chapter_durations_ms[idx-1] - 1 if chapter_durations_ms[idx-1] > 0 else 0)
                    mf.write("[CHAPTER]\n")
                    mf.write("TIMEBASE=1/1000\n")
                    mf.write(f"START={start_ms}\n")
                    mf.write(f"END={end_ms}\n")
                    chapter_title = title or f"Chapter {idx}"
                    # Escape any special characters in title if needed
                    chapter_title = chapter_title.replace("\n", " ").strip()
                    mf.write(f"title={chapter_title}\n")
                    start_ms = end_ms + 1
        # Create file list for ffmpeg concat
        list_path = os.path.join(out_dir, "chapters_list.txt")
        with open(list_path, "w", encoding="utf-8") as lf:
            for _, chap_file in chapter_files:
                # ffmpeg concat requires paths properly escaped/quoted
                lf.write(f"file '{chap_file}'\n")
        # Determine final output file name and path
        base_name = os.path.splitext(orig_name)[0]
        final_file_name = f"{base_name}.{output_format.lower()}"
        final_path = os.path.join(out_dir, final_file_name)
        
        log_message(f"Final output file will be: {final_path}")
        
        # 在开始合并前显示进度
        yield f"所有章节已合成。正在合并为有声书: {final_file_name}...", None, None
        
        # 在开始合并前删除可能存在的旧文件
        if os.path.exists(final_path):
            try:
                os.remove(final_path)
            except Exception as e:
                yield f"<p style='color:orange'>警告：无法删除旧文件: {str(e)}</p>", None, None
    
        # Construct ffmpeg command for merging
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path]
        if os.path.exists(metadata_path):
            cmd += ["-i", metadata_path, "-map_metadata", "1"]
        
        # Choose codec based on output format
        fmt = output_format.lower()
        if fmt in ["m4b", "m4a", "mp4", "mov"]:
            # Use AAC codec for MP4/M4A/M4B
            cmd += ["-c:a", "aac", "-b:a", "128k"]
        elif fmt == "mp3":
            cmd += ["-c:a", "libmp3lame", "-b:a", "192k"]
        elif fmt == "flac":
            cmd += ["-c:a", "flac"]
        elif fmt == "wav":
            # PCM for WAV
            cmd += ["-c:a", "pcm_s16le"]
        elif fmt == "aac":
            # AAC ADTS format
            cmd += ["-c:a", "aac", "-b:a", "128k"]
        else:
            # default to codec copy if unknown, though ideally never here
            cmd += ["-c", "copy"]
        cmd += [final_path]
        
        # 将命令输出到日志，方便调试
        cmd_str = " ".join(cmd)
        log_message(f"FFmpeg command: {cmd_str}")
        yield f"<p>执行命令: <code>{cmd_str}</code></p>", None, None
        
        # 使用直接的subprocess.run而不是Popen，简化逻辑
        try:
            log_message("Starting FFmpeg process")
            process = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                check=False  # 不自动抛出异常
            )
            
            log_message(f"FFmpeg returned with code: {process.returncode}")
            
            # 检查是否成功
            if process.returncode == 0:
                # 验证文件状态
                file_status = log_file_status(final_path)
                
                # 确认文件存在且可读
                if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
                    # 尝试读取确保文件完整
                    try:
                        with open(final_path, 'rb') as f:
                            f.seek(0)
                            
                        log_message("✅ Successfully verified output file")
                        
                        # 成功生成，显示结果 - 使用yield而不是return确保流程完整
                        success_html = f"""
                        <div style='padding: 15px; border: 1px solid #28a745; border-radius: 5px; margin: 10px 0;'>
                            <h3 style='color: #28a745; margin-bottom: 10px;'>✅ 音频转换完成</h3>
                            <p>文件路径: {os.path.basename(final_path)}</p>
                            <p><strong>👉 请点击下方按钮下载有声书</strong></p>
                        </div>
                        """
                        log_message("Yielding success message")
                        yield success_html, None, final_path
                        log_message("Yield complete")
                        return
                    except Exception as e:
                        log_error(f"File access error: {str(e)}", e)
                        yield f"<p style='color:red'>文件访问错误: {str(e)}</p>", None, None
                else:
                    log_error(f"Output file not found or empty: {final_path}")
                    yield f"<p style='color:red'>错误: FFmpeg运行成功但找不到输出文件: {final_path}</p>", None, None
            else:
                # 命令执行失败
                stderr = process.stderr
                log_error(f"FFmpeg error: {stderr}")
                yield f"<p style='color:red'>FFmpeg错误: {stderr}</p>", None, None
                
        except Exception as e:
            log_error(f"Error running FFmpeg: {str(e)}", e)
            yield f"<p style='color:red'>运行错误: {str(e)}</p>", None, None
        
    except Exception as e:
        log_error(f"Unexpected error in convert_to_audio: {str(e)}", e)
        yield f"<p style='color:red'>处理过程中出现未知错误: {str(e)}</p>", None, None

def create_ui():
    """Construct and return the Gradio Blocks interface."""
    with gr.Blocks(title="Ebook to Audiobook Converter") as demo:
        gr.Markdown("# E-book to Audiobook Converter (Fish-Speech TTS)")
        with gr.Row():
            book_file = gr.File(label="上传电子书", file_types=['.epub', '.pdf', '.mobi', '.txt', '.html', '.rtf', '.chm', '.lit', '.pdb', '.fb2', '.odt', '.cbr', '.cbz', '.prc', '.lrf', '.pml', '.snb', '.cbc', '.rb', '.tcr'])
            ref_audio = gr.File(label="参考音频 (可选)", file_types=['audio'])
        
        with gr.Row():
            parse_btn = gr.Button("预览章节")
            test_voice_btn = gr.Button("测试克隆声音")
            
        chapters_preview = gr.HTML(label="章节预览")
        
        with gr.Row():
            chapter_index = gr.Number(label="测试章节索引", value=0, minimum=0, step=1)
            test_chapter_btn = gr.Button("测试章节合成")
            
        preview_status = gr.Markdown("")
        preview_audio = gr.Audio(label="音频预览", type="filepath")
        
        with gr.Row():
            start_chapter = gr.Number(label="起始章节", value=1, minimum=1, step=1)
            end_chapter = gr.Number(label="结束章节", value=1, minimum=1, step=1)
        
        output_format = gr.Dropdown(label="输出格式", choices=["m4b","mp3","wav","aac","flac"], value="m4b")
        convert_btn = gr.Button("转换为有声书")
        progress = gr.HTML(label="进度")
        audio_output = gr.HTML(label="音频预览")
        download_output = gr.File(label="下载有声书", interactive=False)
        
        # Setup interactions
        state = gr.State()
        parse_btn.click(fn=parse_book, 
                       inputs=book_file, 
                       outputs=[chapters_preview, state])
                       

        def update_chapter_range(state):
            if state and "chapters" in state:
                total_chapters = len(state["chapters"])
                return gr.update(maximum=total_chapters), gr.update(value=total_chapters, maximum=total_chapters)
            return gr.update(), gr.update()
        
        parse_btn.click(fn=update_chapter_range,
                       inputs=state,
                       outputs=[start_chapter, end_chapter])

        test_voice_btn.click(fn=test_voice_cloning,
                           inputs=ref_audio,
                           outputs=[preview_status, preview_audio])
                           

        test_chapter_btn.click(fn=test_chapter_synthesis,
                             inputs=[state, ref_audio, chapter_index],
                             outputs=[preview_status, preview_audio])
                             
        convert_btn.click(fn=convert_to_audio, 
                         inputs=[state, ref_audio, output_format, start_chapter, end_chapter], 
                         outputs=[progress, audio_output, download_output],
                         show_progress="full")  # 启用完整进度显示
    return demo
