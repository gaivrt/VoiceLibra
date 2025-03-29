# app/tts/utils/text.py
def split_text(text: str, max_length: int = 200) -> list:
    """将长文本分割成适合TTS处理的片段
    
    Args:
        text: 输入文本
        max_length: 每个片段的最大长度
        
    Returns:
        分割后的文本片段列表
    """
    # 按标点分割
    delimiters = '.。!！?？'
    parts = []
    current = []
    length = 0
    
    for char in text:
        current.append(char)
        length += 1
        
        if char in delimiters:
            if length >= max_length:
                parts.append(''.join(current))
                current = []
                length = 0
                
    if current:
        parts.append(''.join(current))
        
    return parts