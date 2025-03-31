import requests
import ormsgpack
import os
import json
import io
import wave
from typing import Optional, List, Dict, Union
from tqdm import tqdm

# 确保输出目录存在
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 默认配置
DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8080,
    "max_retries": 3,
    "timeout": 60,
    "streaming": False
}

class TTSClient:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.base_url = f"http://{self.config['host']}:{self.config['port']}/v1/tts"
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from file or use defaults"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        return DEFAULT_CONFIG

    def check_server(self) -> bool:
        """Check if TTS server is running"""
        try:
            response = requests.get(f"http://{self.config['host']}:{self.config['port']}/", 
                                  timeout=5)
            return response.status_code == 200
        except:
            return False

    def synthesize(self, 
                  text: str,
                  reference_audios: Optional[List[str]] = None,
                  reference_texts: Optional[List[str]] = None,
                  output_format: str = "wav",
                  streaming: bool = None) -> bytes:
        """
        Synthesize speech using Fish-Speech TTS API
        
        Args:
            text: Text to synthesize
            reference_audios: List of paths to reference audio files
            reference_texts: List of texts corresponding to reference audios
            output_format: Output audio format (wav/mp3)
            streaming: Whether to use streaming mode
        """
        if not self.check_server():
            raise ConnectionError(
                f"\n 无法连接到 Fish-Speech TTS 服务器 ({self.base_url} )。\n"
                "请确保已经运行以下命令启动服务器:\n"
                "python -m tools.api_server \\\n"
                "    --listen 0.0.0.0:8080 \\\n"
                "    --llama-checkpoint-path checkpoints/fish-speech-1.5 \\\n"
                "    --decoder-checkpoint-path checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth \\\n"
                "    --decoder-config-name firefly_gan_vq"
            )

        # Prepare payload
        payload = {
            "text": text,
            "format": output_format,
            "streaming": streaming if streaming is not None else self.config["streaming"]
        }

        # Add references if provided
        if reference_audios:
            references = []
            for i, audio_path in enumerate(reference_audios):
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()
                references.append({
                    "audio": audio_bytes,
                    "text": reference_texts[i] if reference_texts and i < len(reference_texts) else ""
                })
            payload["references"] = references
            
            # Use MessagePack for requests with audio data
            headers = {"Content-Type": "application/msgpack"}
            data = ormsgpack.packb(payload, option=ormsgpack.OPT_SERIALIZE_PYDANTIC)
            response = requests.post(self.base_url, data=data, headers=headers, 
                                  timeout=self.config["timeout"])
        else:
            # Use JSON for simple requests
            response = requests.post(self.base_url, json=payload, 
                                  timeout=self.config["timeout"])

        if response.status_code != 200:
            raise RuntimeError(f"TTS API 调用失败 ({response.status_code}): {response.text}")
            
        return response.content

    def split_into_sentences(self, text: str) -> list:
        """将文本分割成句子"""
        # 定义句子结束标记
        end_marks = ['。', '！', '？', '!', '?', '.']
        # 定义不应该分割的情况(如 Mr. Dr. 等)
        exceptions = ['Mr.', 'Mrs.', 'Dr.', 'Ph.D.', 'etc.', 'e.g.', 'i.e.']
        
        sentences = []
        current_sentence = ""
        
        i = 0
        while i < len(text):
            char = text[i]
            current_sentence += char
            
            # 检查是否是句子结束
            if char in end_marks:
                # 检查是否是例外情况
                is_exception = False
                for exc in exceptions:
                    if text[max(0, i-len(exc)+1):i+1] == exc:
                        is_exception = True
                        break
                
                # 如果不是例外，则添加到结果中
                if not is_exception:
                    current_sentence = current_sentence.strip()
                    if current_sentence:
                        sentences.append(current_sentence)
                    current_sentence = ""
            
            i += 1
        
        # 处理最后一个句子
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences

    def synthesize_long_text(self, 
                            text: str,
                            reference_audios: Optional[List[str]] = None,
                            reference_texts: Optional[List[str]] = None,
                            output_format: str = "wav",
                            streaming: bool = None,
                            progress_callback = None) -> List[bytes]:
        """
        将长文本分句后逐句合成
        
        Args:
            text: 要合成的文本
            reference_audios: 参考音频文件路径列表
            reference_texts: 参考音频对应的文本列表
            output_format: 输出音频格式
            streaming: 是否使用流式模式
            progress_callback: 进度回调函数
        
        Returns:
            音频数据列表
        """
        sentences = self.split_into_sentences(text)
        audio_segments = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            try:
                audio_data = self.synthesize(
                    text=sentence,
                    reference_audios=reference_audios,
                    reference_texts=reference_texts,
                    output_format=output_format,
                    streaming=streaming
                )
                audio_segments.append(audio_data)
                
                # 报告进度
                if progress_callback:
                    progress = (i + 1) / len(sentences) * 100
                    progress_callback(f"正在合成第 {i+1}/{len(sentences)} 句 ({progress:.1f}%)")
                    
            except Exception as e:
                print(f"Warning: Failed to synthesize sentence: {sentence[:50]}... Error: {str(e)}")
                continue
                
        return audio_segments

# Create global client instance
tts_client = TTSClient()

def test_voice_clone(reference_audio_path: str, reference_text: str = None) -> bytes:
    """Test voice cloning with a sample sentence"""
    test_text = "这是一个测试音频，用于确认声音克隆的效果。"
    return tts_client.synthesize(
        text=test_text,
        reference_audios=[reference_audio_path],
        reference_texts=[reference_text] if reference_text else None
    )

def synthesize_text(text: str, 
                   reference_audio_path: str = None, 
                   reference_text: str = None, 
                   output_format: str = "wav") -> bytes:
    """Synthesize speech from text"""
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if len(text) > 1000:  # 如果文本较长，使用分句合成
        segments = tts_client.synthesize_long_text(
            text=text,
            reference_audios=[reference_audio_path] if reference_audio_path else None,
            reference_texts=[reference_text] if reference_text else None,
            output_format=output_format
        )
        # 合并音频片段
        with io.BytesIO() as outfile:
            with wave.open(outfile, 'wb') as wf:
                first_segment = True
                # 创建进度条
                pbar = tqdm(total=len(segments), desc="合并音频片段")
                for audio_data in segments:
                    with wave.open(io.BytesIO(audio_data), 'rb') as infile:
                        if first_segment:
                            wf.setnchannels(infile.getnchannels())
                            wf.setsampwidth(infile.getsampwidth())
                            wf.setframerate(infile.getframerate())
                            first_segment = False
                        wf.writeframes(infile.readframes(infile.getnframes()))
                    pbar.update(1)  # 更新进度条
                pbar.close()  # 关闭进度条
            return outfile.getvalue()
    else:  # 短文本直接合成
        return tts_client.synthesize(
            text=text,
            reference_audios=[reference_audio_path] if reference_audio_path else None,
            reference_texts=[reference_text] if reference_text else None,
            output_format=output_format
        )