#!/usr/bin/env python3
import click
from pathlib import Path
from app.tts.webui import WebUI
from config import MODEL_PATH, DEVICE, HOST, PORT, DEBUG

@click.group()
def cli():
    """Fish-Speech TTS 命令行工具"""
    pass

@cli.command()
@click.option('--text', '-t', help='要转换的文本')
@click.option('--output', '-o', help='输出文件路径')
@click.option('--reference', '-r', help='参考音频路径', default=None)
def tts(text, output, reference):
    """直接运行TTS转换"""
    from app.tts.inference_engine import TTSInferenceEngine
    
    engine = TTSInferenceEngine(MODEL_PATH, DEVICE)
    audio_data, sr = engine.tts(
        text,
        reference_audio=reference
    )
    
    # 保存音频
    import soundfile as sf
    sf.write(output, audio_data, sr)
    click.echo(f"已保存到: {output}")

@cli.command()
@click.option('--host', default=HOST, help='服务器主机名')
@click.option('--port', default=PORT, help='服务器端口')
@click.option('--share', is_flag=True, help='是否公开分享')
def webui(host, port, share):
    """启动Web界面"""
    ui = WebUI(MODEL_PATH, DEVICE)
    ui.launch(
        server_name=host,
        server_port=port,
        share=share,
        debug=DEBUG
    )

@cli.command()
def download():
    """下载模型文件"""
    from huggingface_hub import snapshot_download
    
    click.echo("正在下载Fish-Speech模型...")
    repo_id = "fishaudio/fish-speech"
    cache_dir = MODEL_PATH
    
    snapshot_download(
        repo_id=repo_id,
        cache_dir=cache_dir,
        local_dir=cache_dir
    )
    click.echo(f"模型已下载到: {cache_dir}")

if __name__ == '__main__':
    cli()