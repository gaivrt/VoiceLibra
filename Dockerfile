FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY requirements.txt .
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p uploads outputs models

# 设置环境变量
ENV MODEL_PATH=/app/models/fish-speech-1.5
ENV DEVICE=cuda

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "main.py"]