# app/tts/utils/schema.py
from pydantic import BaseModel, Field
from typing import Literal, Optional, Annotated

class ServeTTSRequest(BaseModel):
    """TTS 请求模型"""
    text: str
    chunk_length: Annotated[int, Field(ge=100, le=300, strict=True)] = 200
    format: Literal["wav", "pcm"] = "wav"
    normalize: bool = True
    top_p: Annotated[float, Field(ge=0.1, le=1.0, strict=True)] = 0.7
    repetition_penalty: Annotated[float, Field(ge=0.9, le=2.0, strict=True)] = 1.2
    temperature: Annotated[float, Field(ge=0.1, le=1.0, strict=True)] = 0.7
    
    class Config:
        arbitrary_types_allowed = True