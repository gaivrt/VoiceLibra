import torch
import torchaudio
import numpy as np
from pathlib import Path
import torch.nn as nn
import torch.nn.functional as F
import torchaudio.transforms as T

def load_audio(file_path: str, target_sr: int = 24000) -> torch.Tensor:
    """加载音频文件并转换采样率
    
    Args:
        file_path: 音频文件路径
        target_sr: 目标采样率
        
    Returns:
        音频张量 [1, T]
    """
    waveform, sr = torchaudio.load(file_path)
    if sr != target_sr:
        waveform = torchaudio.transforms.Resample(sr, target_sr)(waveform)
    return waveform

def save_audio(waveform: torch.Tensor, file_path: str, sample_rate: int = 24000):
    """保存音频文件
    
    Args:
        waveform: 音频张量 [1, T]或[T]
        file_path: 保存路径
        sample_rate: 采样率
    """
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    torchaudio.save(file_path, waveform, sample_rate)

def normalize_audio(waveform: torch.Tensor, target_db: float = -14.0) -> torch.Tensor:
    """将音频规范化到目标分贝
    
    Args:
        waveform: 输入音频张量
        target_db: 目标分贝值
        
    Returns:
        规范化后的音频张量
    """
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
        
    # 计算当前RMS
    rms = torch.sqrt(torch.mean(waveform ** 2))
    current_db = 20 * torch.log10(rms)
    
    # 计算增益
    gain = 10 ** ((target_db - current_db) / 20)
    
    # 应用增益
    return waveform * gain

class LogMelSpectrogram(nn.Module):
    def __init__(
        self,
        sample_rate=44100,
        n_fft=2048,
        win_length=2048,
        hop_length=512,
        f_min=0,
        f_max=22050,
        n_mels=160,
        center=False,
    ):
        super().__init__()
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.win_length = win_length
        self.hop_length = hop_length
        self.f_min = f_min
        self.f_max = f_max
        self.n_mels = n_mels
        self.center = center
        
        self.mel_spectrogram = T.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=n_fft,
            win_length=win_length,
            hop_length=hop_length,
            f_min=f_min,
            f_max=f_max,
            n_mels=n_mels,
            center=center,
        )

    def forward(self, audio):
        mel = self.mel_spectrogram(audio.squeeze(1))
        log_mel = torch.log(torch.clamp(mel, min=1e-5))
        return log_mel