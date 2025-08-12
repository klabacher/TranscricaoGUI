import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, abort, send_file, Response
from flask_cors import CORS
from sqlalchemy import create_engine, text
from werkzeug.utils import secure_filename
import threading
import io
import pandas as pd
import hashlib
import librosa

# --- Imports da Google Cloud e Vertex AI ---
from google.cloud import speech
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
import vertexai
# CORREÇÃO: O nome da classe é GenerativeModel, não GeneQrativeModel
from vertexai.generative_models import GenerativeModel, Part

# --- IMPORTAÇÃO DO NOSSO NOVO MOTOR DE TRANSCRIÇÃO ---
import transcription_engine

# --- Configuração Inicial e Carregamento de Variáveis ---
load_dotenv()

PROJECT_ID = "transcricao-467718" 
LOCATION = "us-central1"

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    print(f"AVISO: Não foi possível inicializar a Vertex AI. Verifique a autenticação gcloud. Erro: {e}")


UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# CORREÇÃO: Aponta para a pasta 'templates' para o Flask encontrar o index.html
app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
engine = create_engine(f'sqlite:///{db_path}')

# --- FUNÇÕES DE PROCESSAMENTO DE IA (AGENTES) ---

def transcribe_with_google_chirp(file_path):
    """Função específica para o modelo Chirp da Google, mantida para compatibilidade."""
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
        
        print(f"A enviar '{os.path.basename(file_path)}' para o Google Chirp...")
        request_chirp = speech.RecognizeRequest(config=config, audio=audio, recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_")
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

def run_ai_analysis_pipeline(transcript_text):
    """Pipeline de Agentes de Análise com Gemini (sem alterações)."""
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
        start_index = json_text.find('{')
        end_index = json_text.rfind('}') + 1
        if start_index == -1 or end_index == 0:
            raise ValueError("Nenhum JSON encontrado na resposta da IA.")
        return json.loads(json_text[start_index:end_index])
    except Exception as e:
        print(f"Erro no pipeline de análise com IA: {e}")
        return {"error": f"Falha na análise da IA: {e}"}

# --- PROCESSAMENTO EM BACKGROUND ---

def process_file_pipeline(entry_id, file_path, filename, file_type, model_id):
    """Orquestrador do pipeline de processamento para cada ficheiro."""
    print(f"Iniciando pipeline para '{filename}' (ID: {entry_id}) com o modelo '{model_id}'")
    full_dialogue = None
    analysis_input = None
    
    try:
        # --- ETAPA 1: TRANSCRIÇÃO OU LEITURA ---
        if file_type == 'audio':
            with engine.connect() as connection:
                connection.execute(text("UPDATE transcriptions SET status = :status WHERE id = :id"), {"status": f"A transcrever com {model_id}...", "id": entry_id})
                connection.commit()
            
            model_config = transcription_engine.AVAILABLE_MODELS.get(model_id)
            if not model_config:
                raise ValueError(f"Modelo de transcrição '{model_id}' não encontrado.")

            # --- Roteamento para o motor de transcrição correto ---
            if model_config['impl'] == 'google_chirp':
                full_dialogue, analysis_input = transcribe_with_google_chirp(file_path)
            else: # Usa o motor local (Whisper, Faster, etc.)
                device = transcription_engine.get_device()
                local_result = transcription_engine.run_local_transcription(model_id, model_config, device, file_path)
                analysis_input = local_result['text']
                # Formata o diálogo para exibição
                dialogue_lines = [f"**`[{str(datetime.timedelta(seconds=int(s.get('start',0))))}]`:** {s.get('text','').strip()}" for s in local_result['segments']]
                full_dialogue = "\n\n".join(dialogue_lines)

        elif file_type == 'text':
            with open(file_path, 'r', encoding='utf-8') as f:
                analysis_input = f.read()
            full_dialogue = f"**Texto do Ficheiro:**\n\n{analysis_input}"
        
        if analysis_input is None:
            raise ValueError(full_dialogue or "Falha ao obter texto para análise.")

        # --- ETAPA 2: ANÁLISE COM IA ---
        with engine.connect() as connection:
            connection.execute(text("UPDATE transcriptions SET transcript_text = :text, status = 'A Analisar com IA...' WHERE id = :id"), {"text": full_dialogue, "id": entry_id})
            connection.commit()
        
        analysis_result = run_ai_analysis_pipeline(analysis_input)
        if "error" in analysis_result:
             raise ValueError(analysis_result["error"])

        # --- ETAPA 3: SALVAR RESULTADOS ---
        with engine.connect() as connection:
            analysis_json = json.dumps(analysis_result, ensure_ascii=False)
            connection.execute(text("""
                INSERT INTO analyses (transcription_id, sentiment, topic, summary, full_analysis_json)
                VALUES (:transcription_id, :sentiment, :topic, :summary, :full_analysis_json)
            """), {
                "transcription_id": entry_id, "sentiment": analysis_result.get("sentiment"), "topic": analysis_result.get("main_topic"),
                "summary": analysis_result.get("summary"), "full_analysis_json": analysis_json
            })
            connection.execute(text("UPDATE transcriptions SET status = 'Concluído' WHERE id = :id"), {"id": entry_id})
            connection.commit()
            print(f"Pipeline concluído com sucesso para '{filename}'.")

    except Exception as e:
        error_message = f"Erro no pipeline: {e}"
        print(error_message)
        with engine.connect() as connection:
            connection.execute(text("UPDATE transcriptions SET status = :status, transcript_text = :text WHERE id = :id"), {"status": error_message, "text": (full_dialogue or str(e)), "id": entry_id})
            connection.commit()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Ficheiro temporário removido: {filename}")

# --- ROTAS DA API ---

@app.route('/api/get_transcription_models', methods=['GET'])
def get_models():
    """Nova rota para o frontend saber quais modelos estão disponíveis."""
    available_models = transcription_engine.get_available_models_for_device()
    return jsonify(list(available_models.keys()))

@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files: return jsonify({"error": "Nenhum ficheiro enviado"}), 400
    
    files = request.files.getlist('files[]')
    batch_name = request.form.get('batchName') or f"Lote de {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    model_id = request.form.get('modelId', 'google_chirp')
    
    ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.flac', '.ogg', '.txt'}
    files_to_process = [f for f in files if os.path.splitext(f.filename)[1].lower() in ALLOWED_EXTENSIONS]

    if not files_to_process: return jsonify({"error": "Nenhum ficheiro válido encontrado."}), 400

    try:
        with engine.connect() as connection:
            with connection.begin() as transaction:
                result = connection.execute(text("INSERT INTO batches (name, created_at) VALUES (:name, :created_at)"),
                                            {"name": batch_name, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                batch_id = result.lastrowid
                
                for file in files_to_process:
                    filename = secure_filename(file.filename)
                    ext = os.path.splitext(filename)[1].lower()
                    
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    file_type = 'audio' if ext != '.txt' else 'text'
                    
                    trans_result = connection.execute(text("""
                        INSERT INTO transcriptions (filename, upload_date, status, batch_id)
                        VALUES (:filename, :upload_date, 'Na Fila', :batch_id)
                    """), {"filename": filename, "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "batch_id": batch_id})
                    entry_id = trans_result.lastrowid
                    
                    thread = threading.Thread(target=process_file_pipeline, args=(entry_id, file_path, filename, file_type, model_id))
                    thread.start()
                
                transaction.commit()
    except Exception as e:
        print(f"Erro no upload: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500
        
    message = f"Lote '{batch_name}' recebido. {len(files_to_process)} ficheiros enviados para o pipeline."
    return jsonify({"message": message, "batch_id": batch_id}), 202

@app.route('/')
def index():
    return render_template('index.html')

# --- Outras rotas permanecem as mesmas ---
@app.route('/api/dashboard_data', methods=['GET'])
def get_dashboard_data():
    batch_id_filter = request.args.get('batch_id')
    params = {}
    where_clause = "WHERE t.status = 'Concluído'"
    if batch_id_filter and batch_id_filter != 'all':
        where_clause += " AND b.id = :batch_id"
        params['batch_id'] = batch_id_filter
    query = f"""
    SELECT t.id, b.name as batch_name, a.sentiment, a.topic, a.summary
    FROM transcriptions t 
    JOIN analyses a ON t.id = a.transcription_id 
    JOIN batches b ON t.batch_id = b.id 
    {where_clause} 
    ORDER BY t.upload_date DESC
    """
    with engine.connect() as connection:
        result = connection.execute(text(query), params)
        data = [dict(row) for row in result.mappings()]
    return jsonify(data)

@app.route('/api/batches', methods=['GET'])
def get_batches():
    query = "SELECT b.id, b.name, b.created_at, COUNT(t.id) as file_count FROM batches b LEFT JOIN transcriptions t ON b.id = t.batch_id GROUP BY b.id, b.name, b.created_at ORDER BY b.created_at DESC;"
    with engine.connect() as connection:
        result = connection.execute(text(query))
        batches = [dict(row) for row in result.mappings()]
    return jsonify(batches)

@app.route('/api/batch/<int:batch_id>/details', methods=['GET'])
def get_batch_details(batch_id):
    query = "SELECT id, filename, status FROM transcriptions WHERE batch_id = :batch_id ORDER BY id"
    with engine.connect() as connection:
        result = connection.execute(text(query), {"batch_id": batch_id})
        files = [dict(row) for row in result.mappings()]
    return jsonify(files)

@app.route('/api/transcription/<int:transcription_id>', methods=['GET'])
def get_transcription_text(transcription_id):
    query = "SELECT t.transcript_text, a.full_analysis_json FROM transcriptions t LEFT JOIN analyses a ON t.id = a.transcription_id WHERE t.id = :id"
    with engine.connect() as connection:
        result = connection.execute(text(query), {"id": transcription_id}).mappings().fetchone()
    
    if not result:
        return jsonify({"error": "Análise não encontrada."}), 404

    response_data = {
        "transcript_text": result.get("transcript_text", "Conteúdo não disponível."),
        "analysis": json.loads(result["full_analysis_json"]) if result.get("full_analysis_json") else None
    }
    return jsonify(response_data)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
        