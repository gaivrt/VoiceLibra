# app/tts/utils/reference_loader.py
import os
import numpy as np
import soundfile as sf
from loguru import logger
from typing import Callable, Dict, List, Optional, Union

class ReferenceLoader:
    """加载和处理参考音频样本"""
    
    def __init__(self):
        self.reference_cache = {}
    
    def load_audio(self, file_path, target_sr=44100):
        """
        加载音频文件并转换为指定采样率
        
        Args:
            file_path: 音频文件路径或二进制数据
            target_sr: 目标采样率
        
        Returns:
            音频数据 numpy 数组
        """
        if isinstance(file_path, bytes):
            # 处理二进制音频数据
            import io
            with io.BytesIO(file_path) as buffer:
                audio, sr = sf.read(buffer)
        else:
            # 处理文件路径
            audio, sr = sf.read(file_path)
            
        # 转换为单声道
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
            
        # 转换采样率(如果需要)
        if sr != target_sr:
            import librosa
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
            
        return audio.astype(np.float32)
    
    def process_reference(self, reference_path):
        """
        处理参考音频
        
        Args:
            reference_path: 参考音频路径
            
        Returns:
            处理后的音频数据
        """
        # 检查缓存
        if reference_path in self.reference_cache:
            return self.reference_cache[reference_path]
            
        # 加载和处理
        try:
            audio_data = self.load_audio(reference_path)
            self.reference_cache[reference_path] = audio_data
            return audio_data
        except Exception as e:
            logger.error(f"处理参考音频失败: {e}")
            return None