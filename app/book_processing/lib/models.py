# Fish-Speech默认设置
default_fish_speech_settings = {
    'temperature': 0.7,
    'top_p': 0.7,
    'repetition_penalty': 1.2,
    'speed': 1.0,
    'voices': {
        'female': 'models/fish-speech/voices/female',
        'male': 'models/fish-speech/voices/male'
    },
    'samplerate': 24000,
    'use_deepspeed': False
}

# 模型默认设置
default_tts_engine = 'fish-speech'
default_fine_tuned = 'internal'

# 模型配置映射
models = {
    'fish-speech': {
        'internal': {
            'files': ['text2semantic.pth', 'firefly-gan-vq-fsq-8x1024-21hz-generator.pth'],
            'repo': 'models/fish-speech-1.5',
            'samplerate': 24000,
            'voice': 'female',
        }
    }
}