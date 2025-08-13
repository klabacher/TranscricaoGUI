from flask import Blueprint, jsonify, request, render_template, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from . import services
from .models import db, Batch, Transcription

# Cria um 'Blueprint', que é como um mini-aplicativo para agrupar nossas rotas
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Rota principal que renderiza o frontend."""
    return render_template('index.html')

@bp.route('/api/get_transcription_models', methods=['GET'])
def get_models():
    """Retorna a lista de modelos de transcrição disponíveis."""
    models = services.get_available_models()
    return jsonify(models)

@bp.route('/api/upload', methods=['POST'])
def upload_files_route():
    """Rota para fazer o upload de novos ficheiros para análise."""
    if 'files[]' not in request.files:
        return jsonify({"error": "Nenhum ficheiro enviado"}), 400

    files = request.files.getlist('files[]')
    batch_name = request.form.get('batchName') or f"Lote de {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    model_id = request.form.get('modelId') # O serviço vai lidar com o default

    try:
        # A lógica pesada foi movida para o service
        message, batch_id = services.create_and_process_batch(files, batch_name, model_id)
        return jsonify({"message": message, "batch_id": batch_id}), 202
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Erro no upload: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500


@bp.route('/api/dashboard_data', methods=['GET'])
def get_dashboard_data():
    """Rota para buscar dados para o dashboard."""
    batch_id_filter = request.args.get('batch_id')
    data = services.get_dashboard_data_from_db(batch_id_filter)
    return jsonify(data)

@bp.route('/api/batches', methods=['GET'])
def get_batches():
    """Retorna uma lista de todos os lotes processados."""
    batches = Batch.query.order_by(Batch.created_at.desc()).all()
    return jsonify([b.to_dict() for b in batches])


@bp.route('/api/batch/<int:batch_id>/details', methods=['GET'])
def get_batch_details(batch_id):
    """Retorna os detalhes e ficheiros de um lote específico."""
    transcriptions = Transcription.query.filter_by(batch_id=batch_id).order_by(Transcription.id).all()
    if not transcriptions:
        # Verifica se o lote ao menos existe
        batch = Batch.query.get(batch_id)
        if not batch:
             return jsonify({"error": "Lote não encontrado."}), 404
        return jsonify([]) # Lote existe mas está vazio
        
    return jsonify([t.to_dict_details() for t in transcriptions])


@bp.route('/api/transcription/<int:transcription_id>', methods=['GET'])
def get_transcription_text(transcription_id):
    """Retorna o texto transcrito e a análise de um ficheiro específico."""
    transcription = Transcription.query.get(transcription_id)
    if not transcription:
        return jsonify({"error": "Análise não encontrada."}), 404

    analysis_json = {}
    if transcription.analysis:
        analysis_json = transcription.analysis.to_dict()

    response_data = {
        "transcript_text": transcription.transcript_text or "Conteúdo não disponível.",
        "analysis": analysis_json
    }
    return jsonify(response_data)