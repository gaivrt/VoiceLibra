import os
import shutil
import base64
import wave
import subprocess
import gradio as gr
import io

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

def convert_to_audio(state, reference_audio, output_format):
    """
    Gradio event function to convert parsed chapters to audiobook.
    Uses Fish-Speech TTS for each chapter and ffmpeg to merge with metadata.
    """
    if not state or "chapters" not in state:
        yield "No chapters to convert. Please upload and parse a book first.", None, None
        return
    chapters = state["chapters"]
    book_title = state.get("book_title", "Audiobook")
    orig_name = state.get("orig_name", "output")
    total_chapters = len(chapters)
    if total_chapters == 0:
        yield "No text found in the book to convert.", None, None
        return
    # Create output directory if not exists
    out_dir = "output"
    os.makedirs(out_dir, exist_ok=True)
    # Clean up previous temp chapter files
    for fname in os.listdir(out_dir):
        if fname.startswith("temp_chapter_"):
            try:
                os.remove(os.path.join(out_dir, fname))
            except:
                pass
    # Determine reference audio and text if provided
    ref_path = None
    ref_text = None
    if reference_audio is not None:
        ref_path = reference_audio.name
        # If there's a separate text to accompany reference audio, we could ask user (not implemented, use empty or could derive via STT if needed)
        ref_text = ""
    # Generate audio for each chapter
    chapter_files = []
    for idx, ch in enumerate(chapters, start=1):
        chapter_title = ch["title"]
        chapter_text = ch["text"]
        
        # 使用新的分句合成方法
        yield f"合成章节 {idx}/{total_chapters}: {chapter_title}", None, None
        try:
            # 创建一个闭包函数来处理进度回调
            def progress_handler(msg):
                yield f"{msg}", None, None
            
            # 使用新的长文本合成方法
            audio_segments = tts_client.synthesize_long_text(
                text=chapter_text,
                reference_audios=[ref_path] if ref_path else None,
                reference_texts=[ref_text] if ref_text else None,
                output_format="wav",
                progress_callback=progress_handler
            )
            
            # 保存音频片段
            chap_file = os.path.join(out_dir, f"temp_chapter_{idx:03d}.wav")
            
            # 合并音频片段
            with wave.open(chap_file, 'wb') as outfile:
                first_segment = True
                for audio_data in audio_segments:
                    with wave.open(io.BytesIO(audio_data)) as infile:
                        if first_segment:
                            # 设置输出文件参数
                            outfile.setnchannels(infile.getnchannels())
                            outfile.setsampwidth(infile.getsampwidth())
                            outfile.setframerate(infile.getframerate())
                            first_segment = False
                        # 写入音频数据
                        outfile.writeframes(infile.readframes(infile.getnframes()))
            
            chapter_files.append((chapter_title, chap_file))
            
        except Exception as e:
            err_html = f"<p style='color:red'><strong>TTS合成失败:</strong> {str(e)}</p>"
            yield err_html, None, None
            return
    # All chapters synthesized, now merge into final output
    yield "All chapters synthesized. Merging into final audiobook...", None, None
    # Prepare metadata file for chapters (for formats that support chapters)
    metadata_path = None
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
        metadata_path = os.path.join(out_dir, "chapters.txt")
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
    # Construct ffmpeg command for merging
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path]
    if metadata_path:
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
    # Run ffmpeg to create final file
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode('utf-8', errors='ignore')
        yield f"<p style='color:red'><strong>FFmpeg merge failed:</strong> {err}</p>", None, None
        return
    # Optionally, cleanup individual chapter files to save space (skip for now)
    # Prepare HTML with audio players for each chapter
    players_html = "<h3>Chapters Audio Preview:</h3>\n"
    for idx, (title, chap_file) in enumerate(chapter_files, start=1):
        # Read audio data and base64 encode
        try:
            with open(chap_file, "rb") as f:
                audio_data = f.read()
            # Determine MIME type by extension (assuming wav here)
            mime = "audio/wav"
            if chap_file.endswith(".mp3"):
                mime = "audio/mpeg"
            elif chap_file.endswith(".flac"):
                mime = "audio/flac"
            elif chap_file.endswith(".aac"):
                mime = "audio/aac"
            elif chap_file.endswith(".wav"):
                mime = "audio/wav"
            b64_audio = base64.b64encode(audio_data).decode('utf-8')
            audio_tag = f"<audio controls src='data:{mime};base64,{b64_audio}'></audio>"
        except Exception as e:
            audio_tag = "<em>[Audio data unavailable]</em>"
        safe_title = title or f"Chapter {idx}"
        players_html += f"<p><strong>Chapter {idx}: {safe_title}</strong><br>{audio_tag}</p>\n"
    # Provide download link for final file via Gradio File component
    return "Conversion completed!", players_html, final_path

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
                       

        test_voice_btn.click(fn=test_voice_cloning,
                           inputs=ref_audio,
                           outputs=[preview_status, preview_audio])
                           

        test_chapter_btn.click(fn=test_chapter_synthesis,
                             inputs=[state, ref_audio, chapter_index],
                             outputs=[preview_status, preview_audio])
                             
        convert_btn.click(fn=convert_to_audio, 
                         inputs=[state, ref_audio, output_format], 
                         outputs=[progress, audio_output, download_output])
    return demo
