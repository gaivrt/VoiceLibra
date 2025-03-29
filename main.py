# main.py
import os
import click
from pathlib import Path
from flask import Flask
from app.routes import setup_routes
from app.tts.inference_engine import TTSInferenceEngine
from config import (
    BASE_DIR, UPLOADS_DIR, OUTPUTS_DIR, 
    MODELS_DIR, MODEL_PATH, DEVICE
)

def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__)
    
    # 配置
    app.config['UPLOAD_FOLDER'] = str(UPLOADS_DIR)
    app.config['OUTPUTS_DIR'] = str(OUTPUTS_DIR)
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
    
    # 确保必要目录存在
    UPLOADS_DIR.mkdir(exist_ok=True)
    OUTPUTS_DIR.mkdir(exist_ok=True)
    MODELS_DIR.mkdir(exist_ok=True)
    
    # 初始化TTS引擎
    app.tts_engine = TTSInferenceEngine(MODEL_PATH, DEVICE)
    
    # 设置路由
    setup_routes(app)
    
    return app

@click.command()
@click.option('--host', default='0.0.0.0', help='服务器主机名')
@click.option('--port', default=5000, help='服务器端口')
@click.option('--debug', is_flag=True, help='开启调试模式')
def main(host, port, debug):
    """VoiceLibra 命令行入口"""
    app = create_app()
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()