import torch
import tempfile
import os
import io
from pathlib import Path
import datetime

try:
    import whisper as openai_whisper
    from faster_whisper import WhisperModel
    from transformers import pipeline as hf_pipeline
    print("INFO: Bibliotecas de transcrição local carregadas com sucesso.")
except ImportError as e:
    print(f"AVISO: Bibliotecas de ML para transcrição local não encontradas: {e}.")
    print("AVISO: Apenas modelos de nuvem (como Google Chirp) funcionarão.")
    openai_whisper = None
    WhisperModel = None
    hf_pipeline = None

AVAILABLE_MODELS = {
    'google_chirp': {'impl': 'google_chirp', 'req_gpu': False},
    'openai_medium': {'impl': 'openai', 'model_name': 'medium', 'req_gpu': False},
    'openai_large-v3': {'impl': 'openai', 'model_name': 'large-v3', 'req_gpu': False},
    'faster_medium_fp16': {'impl': 'faster', 'model_name': 'medium', 'compute_type': 'float16', 'req_gpu': True},
    'faster_large-v3_fp16': {'impl': 'faster', 'model_name': 'large-v3', 'compute_type': 'float16', 'req_gpu': True},
    'faster_large-v3_int8': {'impl': 'faster', 'model_name': 'large-v3', 'compute_type': 'int8', 'req_gpu': False},
}

MODEL_CACHE = {}

def get_device() -> str:
    return 'cuda' if torch.cuda.is_available() else 'cpu'

def get_available_models_for_device() -> dict:
    device = get_device()
    if device == 'cpu':
        return {id: conf for id, conf in AVAILABLE_MODELS.items() if not conf.get('req_gpu', False)}
    return AVAILABLE_MODELS

def load_model(model_id: str, config: dict, device: str):
    cache_key = f"{model_id}_{device}"
    if cache_key in MODEL_CACHE:
        return MODEL_CACHE[cache_key]

    impl = config['impl']
    if impl == 'google_chirp':
        return None

    model_name = config['model_name']
    print(f"INFO: Carregando modelo local '{model_id}' para dispositivo '{device}'...")

    if impl == 'openai':
        model = openai_whisper.load_model(model_name, device=device)
    elif impl == 'faster':
        compute_type = config.get('compute_type', 'default')
        if device == 'cpu' and compute_type not in ['int8', 'float32']:
            compute_type = 'int8'
        model = WhisperModel(model_name, device=device, compute_type=compute_type)
    else:
        raise ValueError(f"Implementação de modelo desconhecida: {impl}")
    
    MODEL_CACHE[cache_key] = model
    return model

def run_local_transcription(model_id: str, config: dict, device: str, audio_path: str) -> dict:
    model = load_model(model_id, config, device)
    
    text_result, segments_result = "", []
    language = "pt"
    
    print(f"INFO: Executando transcrição com {model_id}...")
    if config['impl'] == 'openai':
        result = model.transcribe(audio_path, language=language, fp16=(device == 'cuda'))
        text_result = result.get('text', ' ')
        if 'segments' in result:
            segments_result = [{'start': s['start'], 'text': s['text'].strip()} for s in result['segments']]

    elif config['impl'] == 'faster':
        segments, _ = model.transcribe(audio_path, language=language)
        full_text_parts = []
        for segment in segments:
            full_text_parts.append(segment.text)
            segments_result.append({'start': segment.start, 'text': segment.text.strip()})
        text_result = "".join(full_text_parts).strip()
    
    else:
        raise NotImplementedError(f"A implementação '{config['impl']}' não está totalmente configurada para execução.")

    return {"text": text_result, "segments": segments_result}
