import os
import json
import threading
from datetime import datetime
import requests
import time
import librosa
import io
import hashlib
from werkzeug.utils import secure_filename
from flask import current_app

# Imports do Google
import vertexai
from google.cloud import speech
from vertexai.generative_models import GenerativeModel

# Imports locais
from .models import db, Batch, Transcription, Analysis
from config import Config

# --- INICIALIZAÇÃO DE SERVIÇOS EXTERNOS ---
try:
    vertexai.init(project=Config.PROJECT_ID, location=Config.LOCATION)
    print("Vertex AI inicializado com sucesso.")
except Exception as e:
    print(f"AVISO: Não foi possível inicializar a Vertex AI. Verifique a autenticação gcloud. Erro: {e}")


# --- LÓGICA DE TRANSCRIÇÃO ---

def transcribe_via_api(file_path, filename, model_id, entry_id):
    """Orquestra a transcrição usando a API externa."""
    print(f"Redirecionando '{filename}' para a API de transcrição externa no modelo '{model_id}'...")
    
    # Etapa 1: Enviar o job para a API
    try:
        with open(file_path, 'rb') as f:
            files = {'files': (filename, f, 'audio/ogg')}
            payload = {'model_id': model_id, 'session_id': str(entry_id), 'language': 'pt'}
            response = requests.post(f"{Config.PUBLIC_URL_API}/jobs", files=files, data=payload, timeout=30)
            response.raise_for_status()
        
        job_info = response.json().get('jobs_created', [])
        if not job_info:
            raise ValueError("A API não retornou um ID de job válido.")
        job_id = job_info[0]['job_id']
        print(f"Job criado na API com sucesso. ID: {job_id}")

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Falha ao conectar ou enviar job para a API de transcrição: {e}")
    except Exception as e:
        raise ValueError(f"Erro ao processar resposta da criação de job da API: {e}")

    # Etapa 2: Monitorar (poll) o status do job
    while True:
        try:
            status_response = requests.get(f"{Config.PUBLIC_URL_API}/jobs/{job_id}", timeout=10)
            status_response.raise_for_status()
            job_status = status_response.json()
            
            status = job_status.get('status')
            progress = job_status.get('progress', 0)

            # Atualiza o status no banco de dados local
            transcription = Transcription.query.get(entry_id)
            if transcription:
                transcription.status = f"A transcrever (API): {progress}%"
                db.session.commit()

            if status == 'completed':
                print(f"Job {job_id} concluído na API.")
                break
            elif status in ['failed', 'cancelled']:
                error_details = job_status.get('debug_log', ['Erro desconhecido na API.'])[-1]
                raise RuntimeError(f"Job na API falhou ou foi cancelado. Detalhe: {error_details}")
            
            time.sleep(5)

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Falha ao verificar status do job na API: {e}")

    # Etapa 3: Baixar o resultado
    try:
        download_response = requests.get(f"{Config.PUBLIC_URL_API}/jobs/{job_id}/download", params={"text_type": "transcription_dialogue_markdown"}, timeout=30)
        download_response.raise_for_status()
        full_dialogue = download_response.text

        download_simple_response = requests.get(f"{Config.PUBLIC_URL_API}/jobs/{job_id}/download", params={"text_type": "transcription_raw"}, timeout=30)
        download_simple_response.raise_for_status()
        analysis_input = download_simple_response.text

        return full_dialogue, analysis_input

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Falha ao baixar resultado da API: {e}")

def transcribe_with_google_chirp(file_path):
    """Função específica para o modelo Chirp da Google."""
    try:
        client = speech.SpeechClient()
        _, sr = librosa.load(file_path, sr=None)
        print(f"Taxa de amostragem detetada para Chirp: {sr}Hz")

        with io.open(file_path, "rb") as audio_file:
            content = audio_file.read()
        
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            auto_decoding_config={}, model="chirp", language_codes=["pt-BR"],
            features=speech.RecognitionFeatures(
                enable_automatic_punctuation=True, enable_speaker_diarization=True,
                min_speaker_count=1, max_speaker_count=2
            ),
        )
        
        print(f"A enviar para o Google Chirp...")
        recognizer_path = f"projects/{Config.PROJECT_ID}/locations/global/recognizers/_"
        request_chirp = speech.RecognizeRequest(config=config, audio=audio, recognizer=recognizer_path)
        response = client.recognize(request=request_chirp)

        if not response.results:
            raise ValueError("A API de transcrição Google não retornou resultados.")

        result = response.results[-1]
        if not result.alternatives or not result.alternatives[0].words:
            return result.alternatives[0].transcript, result.alternatives[0].transcript

        words_info = result.alternatives[0].words
        full_transcript = ""
        current_speaker = None
        for word in words_info:
            if word.speaker != current_speaker:
                current_speaker = word.speaker
                full_transcript += f"\n\n**Interveniente {current_speaker}:** "
            full_transcript += word.word + " "
        return full_transcript.strip(), result.alternatives[0].transcript
    except Exception as e:
        print(f"Erro no agente de transcrição Google Chirp: {e}")
        return f"Erro na transcrição com Google: {e}", None


# --- LÓGICA DE ANÁLISE COM IA ---

def run_ai_analysis_pipeline(transcript_text):
    """Pipeline de Agentes de Análise com Gemini."""
    if not transcript_text:
        return {"error": "Texto para análise está vazio."}

    model = GenerativeModel("gemini-1.5-flash-preview-0514")
    prompt = f"""
    Você é um sistema de múltiplos agentes de IA para análise de conversas. Analise a seguinte transcrição e retorne um objeto JSON.

    **Transcrição:**
    ---
    {transcript_text}
    ---

    **Tarefas dos Agentes:**
    1.  **Agente de Identificação:** Identifique o "Operador" e o "Aluno". Se não for claro, use "Interveniente 1" e "Interveniente 2".
    2.  **Agente de Resumo:** Crie um resumo executivo conciso da conversa.
    3.  **Agente de Sentimento:** Analise o sentimento geral do Aluno ("Positivo", "Negativo", "Neutro").
    4.  **Agente de Tópicos:** Qual é o tópico principal da conversa em 2-3 palavras?
    5.  **Agente de Ação:** Identifique até 3 itens de ação claros. Se não houver, retorne uma lista vazia.

    **Formato de Saída Obrigatório (APENAS JSON):**
    {{
      "speaker_identification": {{"operator": "...", "student": "..."}},
      "summary": "...",
      "sentiment": "...",
      "main_topic": "...",
      "action_items": []
    }}
    """

    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip()
        # Limpa o texto para garantir que é um JSON válido
        start_index = json_text.find('{')
        end_index = json_text.rfind('}') + 1
        if start_index == -1 or end_index == 0:
            raise ValueError("Nenhum JSON encontrado na resposta da IA.")
        return json.loads(json_text[start_index:end_index])
    except Exception as e:
        print(f"Erro no pipeline de análise com IA: {e}")
        return {"error": f"Falha na análise da IA: {e}"}


# --- PIPELINE DE PROCESSAMENTO PRINCIPAL ---

def process_file_pipeline_thread_target(app, entry_id, file_path, filename, file_type, model_id):
    """Função alvo da thread que garante o contexto da aplicação."""
    with app.app_context():
        process_file_pipeline(entry_id, file_path, filename, file_type, model_id)

def process_file_pipeline(entry_id, file_path, filename, file_type, model_id):
    """Orquestrador do pipeline de processamento para cada ficheiro."""
    print(f"Iniciando pipeline para '{filename}' (ID: {entry_id}) com o modelo '{model_id}'")
    full_dialogue = None
    analysis_input = None
    
    try:
        # --- ETAPA 1: TRANSCRIÇÃO OU LEITURA ---
        transcription = Transcription.query.get(entry_id)
        if not transcription:
            print(f"ERRO: Transcrição com ID {entry_id} não encontrada no pipeline.")
            return

        if file_type == 'audio':
            transcription.status = f"Aguardando na fila para o modelo '{model_id}'..."
            db.session.commit()
            
            if model_id == 'google_chirp':
                full_dialogue, analysis_input = transcribe_with_google_chirp(file_path)
            else:
                full_dialogue, analysis_input = transcribe_via_api(file_path, filename, model_id, entry_id)
        elif file_type == 'text':
            with open(file_path, 'r', encoding='utf-8') as f:
                analysis_input = f.read()
            full_dialogue = f"**Texto do Ficheiro:**\n\n{analysis_input}"
        
        if analysis_input is None:
            raise ValueError(full_dialogue or "Falha ao obter texto para análise.")

        # --- ETAPA 2: ANÁLISE COM IA ---
        transcription.transcript_text = full_dialogue
        transcription.status = 'A Analisar com IA...'
        db.session.commit()
        
        analysis_result = run_ai_analysis_pipeline(analysis_input)
        if "error" in analysis_result:
             raise ValueError(analysis_result["error"])

        # --- ETAPA 3: SALVAR RESULTADOS ---
        new_analysis = Analysis(
            transcription_id=entry_id,
            sentiment=analysis_result.get("sentiment"),
            topic=analysis_result.get("main_topic"),
            summary=analysis_result.get("summary"),
            full_analysis_json=json.dumps(analysis_result, ensure_ascii=False)
        )
        db.session.add(new_analysis)
        
        transcription.status = 'Concluído'
        db.session.commit()
        print(f"Pipeline concluído com sucesso para '{filename}'.")

    except Exception as e:
        error_message = f"Erro no pipeline: {e}"
        print(error_message)
        transcription = Transcription.query.get(entry_id)
        if transcription:
            transcription.status = error_message
            transcription.transcript_text = full_dialogue or str(e)
            db.session.commit()
    finally:
        # Limpeza do ficheiro temporário
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Ficheiro temporário removido: {filename}")


# --- FUNÇÕES DE SERVIÇO PARA AS ROTAS ---

def get_available_models():
    """Busca modelos da API externa e adiciona os locais."""
    try:
        response = requests.get(f"{Config.PUBLIC_URL_API}/models", timeout=5)
        if response.status_code == 200:
            api_models = response.json().get('available_models', [])
            # Garante que o Chirp não seja duplicado
            if 'google_chirp' in api_models:
                api_models.remove('google_chirp')
            return api_models + ['google_chirp']
    except requests.exceptions.RequestException as e:
        print(f"AVISO: Não foi possível contactar a API de transcrição. Erro: {e}")
    return ['google_chirp'] # Retorna o fallback

def create_and_process_batch(files, batch_name, model_id):
    """Cria um novo lote, salva os ficheiros e inicia o processamento em threads."""
    ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac', '.ogg', '.txt'}
    
    # Define o modelo padrão
    if not model_id:
        api_models = get_available_models()
        whisper_models = [m for m in api_models if 'whisper' in m.lower()]
        if whisper_models:
            model_id = whisper_models[0]
        elif api_models:
            model_id = api_models[0]
        else:
            model_id = 'google_chirp' # Fallback final
    
    # Cria o lote no banco de dados
    new_batch = Batch(name=batch_name)
    db.session.add(new_batch)
    db.session.flush() # Para obter o ID do lote antes do commit

    files_processed_count = 0
    for file in files:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue

        # Salva o ficheiro temporariamente
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(new_batch.id))
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, filename)
        file.seek(0)
        file.save(file_path)

        file_type = 'audio' if ext != '.txt' else 'text'
        
        # Cria a entrada de transcrição no banco
        new_transcription = Transcription(
            filename=filename,
            batch_id=new_batch.id
        )
        db.session.add(new_transcription)
        db.session.flush() # Para obter o ID da transcrição
        
        # Inicia o processamento em uma nova thread
        # Passamos a instância da app para a thread ter o contexto correto
        thread = threading.Thread(
            target=process_file_pipeline_thread_target,
            args=(current_app._get_current_object(), new_transcription.id, file_path, filename, file_type, model_id)
        )
        thread.start()
        files_processed_count += 1
    
    if files_processed_count == 0:
        db.session.rollback() # Desfaz a criação do lote se nenhum ficheiro for válido
        raise ValueError("Nenhum ficheiro válido (.wav, .mp3, .flac, .ogg, .txt) encontrado na seleção.")

    db.session.commit() # Salva tudo no banco de dados
    
    message = f"Lote '{batch_name}' recebido. {files_processed_count} ficheiros enviados para o pipeline com o modelo '{model_id}'."
    return message, new_batch.id

def get_dashboard_data_from_db(batch_id_filter=None):
    """Prepara os dados para o dashboard a partir do banco de dados."""
    query = db.session.query(
        Transcription.id,
        Batch.name.label('batch_name'),
        Analysis.sentiment,
        Analysis.topic,
        Analysis.summary
    ).join(Analysis, Transcription.id == Analysis.transcription_id)\
     .join(Batch, Transcription.batch_id == Batch.id)\
     .filter(Transcription.status == 'Concluído')

    if batch_id_filter and batch_id_filter != 'all':
        query = query.filter(Batch.id == int(batch_id_filter))

    results = query.order_by(Transcription.upload_date.desc()).all()
    
    # Converte o resultado (uma lista de Tuplas Nomeadas) em uma lista de dicionários
    return [row._asdict() for row in results]