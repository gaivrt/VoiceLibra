# app/tts/webui.py
import os
import gradio as gr
import numpy as np
from pathlib import Path

from .inference_engine import TTSInferenceEngine

# 全局变量
ENGINE = None

def initialize_engine(checkpoint_path, device="cuda"):
    """初始化 TTS 引擎"""
    global ENGINE
    if ENGINE is None:
        ENGINE = TTSInferenceEngine(checkpoint_path, device)
    return ENGINE

def text_to_speech(text, reference_audio=None, temperature=0.7, top_p=0.7, repetition_penalty=1.2):
    """TTS 转换函数"""
    global ENGINE
    if ENGINE is None:
        raise ValueError("TTS 引擎未初始化")
    
    # 调用引擎进行推理
    options = {
        "temperature": temperature,
        "top_p": top_p,
        "repetition_penalty": repetition_penalty
    }
    
    audio_data, sample_rate = ENGINE.tts(text, reference_audio, options)
    
    return sample_rate, audio_data

def create_demo(checkpoint_path, device="cuda"):
    """创建 Gradio 演示界面"""
    # 初始化引擎
    initialize_engine(checkpoint_path, device)
    
    # 创建 Gradio 界面
    with gr.Blocks() as demo:
        gr.Markdown("# VoiceLibra TTS 系统 - 支持声音克隆")
        
        with gr.Row():
            with gr.Column():
                text_input = gr.Textbox(
                    label="输入文本",
                    placeholder="请输入要转换为语音的文本...",
                    lines=5
                )
                
                with gr.Row():
                    reference_audio = gr.Audio(
                        label="参考音频（用于声音克隆）", 
                        type="filepath"
                    )
                
                with gr.Accordion("高级选项", open=False):
                    temperature = gr.Slider(
                        label="温度", 
                        minimum=0.1, 
                        maximum=1.0, 
                        value=0.7, 
                        step=0.05
                    )
                    top_p = gr.Slider(
                        label="Top P", 
                        minimum=0.1, 
                        maximum=1.0, 
                        value=0.7, 
                        step=0.05
                    )
                    repetition_penalty = gr.Slider(
                        label="重复惩罚", 
                        minimum=0.9, 
                        maximum=2.0, 
                        value=1.2, 
                        step=0.05
                    )
                
                submit_btn = gr.Button("生成语音")
            
            with gr.Column():
                output_audio = gr.Audio(label="生成的语音")
                
                gr.Markdown("""
                ### 声音克隆使用说明
                1. 上传5-30秒的清晰语音样本
                2. 输入您想要合成的文本
                3. 点击"生成语音"按钮
                4. 如果不上传参考音频，将使用随机声音
                """)
                
        # 设置事件处理
        submit_btn.click(
            fn=text_to_speech,
            inputs=[text_input, reference_audio, temperature, top_p, repetition_penalty],
            outputs=[output_audio]
        )
        
        # 添加示例
        gr.Examples(
            examples=[
                ["你好，这是一个测试文本，用于演示语音合成功能。", None],
                ["Hello, this is a test for voice cloning technology.", None]
            ],
            inputs=[text_input, reference_audio],
        )
    
    return demo

if __name__ == "__main__":
    # 本地测试运行
    checkpoint_path = os.environ.get("MODEL_PATH", "models/fish-speech-1.5")
    device = os.environ.get("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    
    demo = create_demo(checkpoint_path, device)
    demo.launch()