import os
import numpy as np
import subprocess
import torch
import torchaudio
from pathlib import Path
from pydub import AudioSegment

from lib.conf import voice_formats
from lib.models import models

class VoiceExtractor:
    def __init__(self, session, models_dir, voice_file, voice_name):
        self.wav_file = None
        self.session = session
        self.voice_file = voice_file
        self.voice_name = voice_name
        self.models_dir = models_dir
        self.samplerate = models['fish-speech']['internal']['samplerate']
        self.output_dir = self.session['voice_dir']
        
    def _validate_format(self):
        """验证音频格式"""
        file_extension = os.path.splitext(self.voice_file)[1].lower()
        if file_extension in voice_formats:
            msg = '输入文件格式有效'
            return True, msg
        error = f'不支持的文件格式: {file_extension}. 支持的格式: {", ".join(voice_formats)}'
        return False, error

    def _convert_to_wav(self):
        """转换音频到WAV格式"""
        try:
            audio = AudioSegment.from_file(self.voice_file)
            self.wav_file = os.path.join(self.output_dir, f"{self.voice_name}.wav")
            audio.export(self.wav_file, format='wav')
            msg = '音频转换成功'
            return True, msg
        except Exception as e:
            error = f'音频转换失败: {e}'
            return False, error

    def _normalize_audio(self):
        """规范化音频"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', self.wav_file,
                '-ar', str(self.samplerate),
                '-ac', '1',  # 转换为单声道
                '-filter:a', 'loudnorm=I=-14:TP=-3:LRA=7',
                self.wav_file
            ]
            subprocess.run(cmd, check=True)
            return True, '音频规范化成功'
        except Exception as e:
            return False, f'音频规范化失败: {e}'

    def extract_voice(self):
        """处理音频流程"""
        success = False
        msg = None
        try:
            # 验证格式
            success, msg = self._validate_format()
            if success:
                # 转换为WAV
                success, msg = self._convert_to_wav()
                if success:
                    # 规范化
                    success, msg = self._normalize_audio()
        except Exception as e:
            msg = f'处理失败: {e}'
            raise ValueError(msg)
        return success, msg