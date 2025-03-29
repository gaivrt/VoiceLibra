# app/tts/inference_engine.py
import torch
import numpy as np
import time
import os
import gc
from pathlib import Path
import queue
import threading
from typing import Generator, List, Optional, Union, Dict, Any, Tuple
from dataclasses import asdict
from loguru import logger

from .utils.text import split_text, clean_text
from .utils.schema import ServeTTSRequest, ServeReferenceAudio
from .utils.reference_loader import ReferenceLoader
from .utils.vq_manager import VQManager
from .models import load_model

class TTSInferenceEngine(ReferenceLoader, VQManager):
    """文本转语音推理引擎，支持声音克隆"""
    
    def __init__(
        self,
        checkpoint_path,
        device="cuda",
        precision=torch.float16,
        compile=False,
        cache_dir=None
    ):
        """初始化 TTS 推理引擎

        Args:
            checkpoint_path: 模型检查点路径
            device: 使用设备，如'cuda'或'cpu'
            precision: 浮点精度，如torch.float16
            compile: 是否使用torch.compile优化模型
            cache_dir: 缓存目录，用于存储音频特征
        """
        ReferenceLoader.__init__(self)
        
        # 配置设备和精度
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.precision = precision
        self.compile = compile
        self.cache_dir = cache_dir
        
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"启用特征缓存: {cache_dir}")
        
        # 加载模型
        logger.info(f"从 {checkpoint_path} 加载模型...")
        self.models = load_model(checkpoint_path, self.device, self.precision)
        
        # 初始化VQ管理器
        VQManager.__init__(self, self.models["vqgan"], self.device)
        
        # 设置tokenizer
        self.tokenizer = self.models.get("tokenizer")
        
        # 用于异步处理的队列和线程管理
        self.llama_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread = None
        self._start_worker_thread()
        
        # 参考音频缓存
        self.reference_cache = {}
        self.max_cache_size = 50  # 最大缓存音色数量
        
        # 记录初始化完成
        logger.info(f"TTS引擎初始化完成，设备: {self.device}, 精度: {self.precision}")
        
    def _start_worker_thread(self):
        """启动工作线程进行异步处理"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
    
    def _worker_loop(self):
        """工作线程循环，处理队列中的任务"""
        while not self._stop_event.is_set():
            try:
                task, callback = self.llama_queue.get(timeout=0.1)
                result = self._process_task(task)
                if callback:
                    callback(result)
                self.llama_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"工作线程处理任务时出错: {e}")
    
    def _process_task(self, task):
        """处理单个任务"""
        # 任务处理逻辑，可以根据需要扩展
        return task()
    
    def shutdown(self):
        """安全关闭引擎"""
        logger.info("正在关闭TTS引擎...")
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        # 清理缓存
        self.reference_cache.clear()
        # 显式调用垃圾回收
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("TTS引擎已关闭")
    
    def get_cached_reference(self, reference_id):
        """获取缓存的参考音频特征"""
        return self.reference_cache.get(reference_id)
    
    def add_reference_to_cache(self, reference_id, features):
        """添加参考音频特征到缓存"""
        # 如果缓存已满，删除最早加入的项
        if len(self.reference_cache) >= self.max_cache_size:
            oldest_key = next(iter(self.reference_cache))
            del self.reference_cache[oldest_key]
        
        self.reference_cache[reference_id] = features
        logger.debug(f"添加音色到缓存: {reference_id}")
    
    def preprocess_text(self, text):
        """预处理文本"""
        # 清理文本
        text = clean_text(text)
        
        if not text or text.isspace():
            raise ValueError("文本不能为空")
            
        return text
    
    def encode_text(self, text):
        """将文本编码为token IDs"""
        if not self.tokenizer:
            logger.warning("未找到tokenizer，无法编码文本")
            return []
            
        try:
            token_ids = self.tokenizer.encode(text)
            return token_ids
        except Exception as e:
            logger.error(f"编码文本时出错: {e}")
            return []
    
    def tts(self, text, reference_audio=None, options=None) -> Tuple[np.ndarray, int]:
        """
        文本转语音的主要方法，支持声音克隆
        
        Args:
            text: 输入文本
            reference_audio: 参考音频路径或二进制数据（用于音色克隆）
            options: 附加选项字典
            
        Returns:
            (audio_data, sample_rate): 生成的音频数据和采样率
        """
        start_time = time.time()
        
        # 创建请求对象
        options = options or {}
        request = ServeTTSRequest(text=text, **options)
        
        # 预处理文本
        try:
            processed_text = self.preprocess_text(text)
        except ValueError as e:
            logger.error(f"文本预处理失败: {e}")
            # 返回一个空的音频数组
            return np.zeros(0, dtype=np.float32), 44100
        
        # 处理参考音频
        prompt_tokens = None
        if reference_audio:
            if request.reference_id and request.use_memory_cache == "on":
                # 尝试从缓存中获取
                prompt_tokens = self.get_cached_reference(request.reference_id)
                if prompt_tokens is not None:
                    logger.info(f"使用缓存的音色特征: {request.reference_id}")
                    
            if prompt_tokens is None:
                # 处理参考音频并提取特征
                try:
                    audio_data = self.process_reference(reference_audio)
                    if audio_data is not None:
                        prompt_tokens = self.encode_reference(audio_data)
                        
                        # 缓存特征
                        if prompt_tokens is not None and request.reference_id and request.use_memory_cache == "on":
                            self.add_reference_to_cache(request.reference_id, prompt_tokens)
                except Exception as e:
                    logger.error(f"处理参考音频时出错: {e}")
        
        # 标记是否使用参考音频
        using_reference = prompt_tokens is not None
        
        # 分割长文本
        try:
            chunks = split_text(processed_text, request.chunk_length)
            if not chunks:
                raise ValueError("文本分割后为空")
        except Exception as e:
            logger.error(f"分割文本时出错: {e}")
            return np.zeros(0, dtype=np.float32), 44100
        
        # 生成语义tokens
        try:
            with torch.no_grad():
                # 设置随机种子
                if request.seed is not None:
                    torch.manual_seed(request.seed)
                
                # 使用text2semantic模型生成语义tokens
                semantic_tokens = self.models["text2semantic"].generate(
                    text=processed_text,
                    prompt_tokens=prompt_tokens,
                    temperature=request.temperature, 
                    top_p=request.top_p,
                    repetition_penalty=request.repetition_penalty,
                    max_new_tokens=request.max_new_tokens
                )
                
                if semantic_tokens is None or semantic_tokens.shape[0] == 0:
                    raise ValueError("生成的语义tokens为空")
                
                logger.debug(f"生成的语义tokens形状: {semantic_tokens.shape}")
                
                # 使用VQGAN解码成音频
                audio_data, audio_lengths = self.models["vqgan"].decode(
                    indices=semantic_tokens.unsqueeze(0),
                    feature_lengths=torch.tensor([semantic_tokens.shape[0]], 
                                                device=self.device)
                )
                
                # 从张量转换为numpy数组
                audio_np = audio_data.squeeze().cpu().numpy()
                
                # 规范化音频
                if request.normalize:
                    audio_np = audio_np / (np.abs(audio_np).max() + 1e-7)
                
        except Exception as e:
            logger.error(f"生成音频时出错: {e}")
            return np.zeros(0, dtype=np.float32), 44100
        
        end_time = time.time()
        logger.info(f"TTS处理完成，用时: {end_time - start_time:.2f}秒, " +
                   f"文本长度: {len(processed_text)}, " +
                   f"使用参考音频: {using_reference}")
        
        # 获取VQGAN的采样率
        sample_rate = getattr(self.models["vqgan"].spec_transform, "sample_rate", 44100)
        
        return audio_np, sample_rate
    
    def tts_streaming(self, text, reference_audio=None, options=None) -> Generator[np.ndarray, None, None]:
        """
        流式文本转语音，适用于长文本
        
        Args:
            text: 输入文本
            reference_audio: 参考音频路径（用于音色克隆）
            options: 附加选项字典
            
        Yields:
            生成的音频数据片段
        """
        # 创建请求对象
        options = options or {}
        request = ServeTTSRequest(text=text, streaming=True, **options)
        
        # 预处理文本
        processed_text = self.preprocess_text(text)
        
        # 处理参考音频
        prompt_tokens = None
        if reference_audio:
            # 处理参考音频并提取特征
            audio_data = self.process_reference(reference_audio)
            if audio_data is not None:
                prompt_tokens = self.encode_reference(audio_data)
        
        # 分割长文本
        chunks = split_text(processed_text, request.chunk_length)
        
        # 对每个块单独处理
        for i, chunk in enumerate(chunks):
            if not chunk or chunk.isspace():
                continue
                
            logger.info(f"处理文本块 {i+1}/{len(chunks)}: {chunk[:30]}...")
            
            try:
                with torch.no_grad():
                    # 生成语义tokens
                    semantic_tokens = self.models["text2semantic"].generate(
                        text=chunk,
                        prompt_tokens=prompt_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        repetition_penalty=request.repetition_penalty,
                        max_new_tokens=min(request.max_new_tokens, 256)  # 限制每块的token数
                    )
                    
                    # 使用VQGAN解码成音频
                    audio_data, _ = self.models["vqgan"].decode(
                        indices=semantic_tokens.unsqueeze(0),
                        feature_lengths=torch.tensor([semantic_tokens.shape[0]], 
                                                    device=self.device)
                    )
                    
                    # 从张量转换为numpy数组
                    audio_np = audio_data.squeeze().cpu().numpy()
                    
                    # 规范化音频
                    if request.normalize:
                        audio_np = audio_np / (np.abs(audio_np).max() + 1e-7)
                    
                    # 产出当前块的音频
                    yield audio_np
                    
                    # 注意：第一个块之后我们已经有参考音色了
                    if i == 0 and prompt_tokens is None:
                        # 使用第一个生成的音频作为参考
                        prompt_tokens = self.encode_reference(audio_np)
                    
            except Exception as e:
                logger.error(f"处理文本块 {i+1} 时出错: {e}")
                yield np.zeros(1024, dtype=np.float32)  # 出错时返回短的静音
    
    def batch_process(self, texts, reference_audio=None, options=None) -> List[np.ndarray]:
        """
        批量处理多个文本
        
        Args:
            texts: 文本列表
            reference_audio: 参考音频路径（所有文本使用同一音色）
            options: 附加选项字典
            
        Returns:
            生成的音频数据列表
        """
        results = []
        for i, text in enumerate(texts):
            logger.info(f"批处理文本 {i+1}/{len(texts)}")
            try:
                audio, sr = self.tts(text, reference_audio, options)
                results.append(audio)
            except Exception as e:
                logger.error(f"批处理文本 {i+1} 时出错: {e}")
                results.append(np.zeros(0, dtype=np.float32))
        
        return results
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.shutdown()