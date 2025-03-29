import gc
import numpy as np
import os
import torch
import torchaudio
import threading

from fastapi import FastAPI
from pathlib import Path
from lib.models import *
from lib.conf import voices_dir, models_dir, default_audio_proc_format

torch.backends.cudnn.benchmark = True

app = FastAPI()
lock = threading.Lock()
loaded_tts = {}

class TTSManager:
    def __init__(self, session, is_gui_process):   
        self.session = session
        self.is_gui_process = is_gui_process
        self.params = {}
        self.model_path = None
        self._build()

    def _build(self):
        tts_key = None
        self.params['tts'] = None
        self.params['sample_rate'] = models[FISH_SPEECH]['internal']['samplerate']
        self.model_path = models[FISH_SPEECH]['internal']['repo']
        
        msg = f"Loading Fish-Speech model, please wait..."
        print(msg)
        
        if self.model_path in loaded_tts:
            self.params['tts'] = loaded_tts[self.model_path]
        else:
            # 这里实现Fish-Speech模型加载逻辑
            pass
        
        if self.params['tts'] is not None:
            loaded_tts[self.model_path] = self.params['tts']

    def _tensor_type(self, audio_data):
        if isinstance(audio_data, torch.Tensor):
            return audio_data
        elif isinstance(audio_data, np.ndarray):  
            return torch.from_numpy(audio_data).float()
        elif isinstance(audio_data, list):  
            return torch.tensor(audio_data, dtype=torch.float32)
        else:
            raise TypeError(f"Unsupported type for audio_data: {type(audio_data)}")

    def convert_sentence_to_audio(self):
        try:
            # Fish-Speech基础参数
            params = {
                "temperature": float(self.session.get("temperature", 0.7)),
                "top_p": float(self.session.get("top_p", 0.7)),
                "repetition_penalty": float(self.session.get("repetition_penalty", 1.2))
            }
            
            # 调用Fish-Speech进行推理
            audio_data = self.params['tts'].tts(
                text=self.params['sentence'],
                **params
            )
            
            if audio_data is not None:
                audio_tensor = self._tensor_type(audio_data)
                torchaudio.save(
                    self.params['sentence_audio_file'], 
                    audio_tensor.unsqueeze(0).cpu(), 
                    self.params['sample_rate'], 
                    format=default_audio_proc_format
                )
                
                if self.session['device'] == 'cuda':
                    torch.cuda.empty_cache()
                    
                if os.path.exists(self.params['sentence_audio_file']):
                    return True
                    
            error = f"Cannot create {self.params['sentence_audio_file']}"
            print(error)
            return False
            
        except Exception as e:
            error = f'convert_sentence_to_audio(): {e}'
            raise ValueError(error)
            return False