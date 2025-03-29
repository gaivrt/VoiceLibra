# app/tts/utils/vq_manager.py
import torch
import numpy as np
from loguru import logger

class VQManager:
    """管理 VQ 编码和解码过程"""
    
    def __init__(self, encoder, device="cuda"):
        self.encoder = encoder
        self.device = device
        self.sample_rate = 44100  # 默认采样率
        
    def encode_reference(self, reference_audio):
        """
        从参考音频提取声音特征
        
        Args:
            reference_audio: 参考音频数据
            
        Returns:
            编码的声音特征(提示标记)
        """
        if reference_audio is None:
            logger.info("无参考音频提供，将使用随机音色")
            return None
            
        # 将音频数据转换为张量
        audio_tensor = torch.FloatTensor(reference_audio).to(self.device)
        if audio_tensor.dim() == 1:
            audio_tensor = audio_tensor.unsqueeze(0).unsqueeze(0)
        
        # 获取音频长度
        audio_length = torch.tensor([audio_tensor.shape[2]], 
                                   device=self.device, 
                                   dtype=torch.long)
        
        # 使用编码器提取特征
        with torch.no_grad():
            try:
                # 这里的encode方法对应FireflyArchitecture.encode
                prompt_tokens = self.encoder.encode(audio_tensor, audio_length)[0][0]
                logger.info(f"成功提取声音特征: {prompt_tokens.shape}")
                return prompt_tokens
            except Exception as e:
                logger.error(f"特征提取失败: {e}")
                return None