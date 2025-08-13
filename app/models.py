from . import db
from datetime import datetime
import json

class Batch(db.Model):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    transcriptions = db.relationship('Transcription', backref='batch', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() + 'Z', # Padrão ISO 8601
            'file_count': len(self.transcriptions)
        }

class Transcription(db.Model):
    __tablename__ = 'transcriptions'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(255), nullable=False, default='Na Fila')
    transcript_text = db.Column(db.Text, nullable=True)
    audio_hash = db.Column(db.String(64), nullable=True) # Hash SHA-256
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    analysis = db.relationship('Analysis', backref='transcription', uselist=False, cascade="all, delete-orphan")

    def to_dict_details(self):
        # Extrai o progresso do status, se houver
        progress = None
        if self.status == 'Concluído':
            progress = 100
        elif '(API):' in self.status and '%' in self.status:
            try:
                progress_str = self.status.split('(API):')[1].strip().replace('%', '')
                progress = int(progress_str)
            except (ValueError, IndexError):
                progress = 0
                
        return {
            'id': self.id,
            'filename': self.filename,
            'status': self.status,
            'progress': progress
        }

class Analysis(db.Model):
    __tablename__ = 'analyses'
    id = db.Column(db.Integer, primary_key=True)
    sentiment = db.Column(db.String(50))
    topic = db.Column(db.String(100))
    summary = db.Column(db.Text)
    full_analysis_json = db.Column(db.Text) # Armazena o JSON completo como texto
    transcription_id = db.Column(db.Integer, db.ForeignKey('transcriptions.id', ondelete='CASCADE'), unique=True, nullable=False)

    def to_dict(self):
        return json.loads(self.full_analysis_json) if self.full_analysis_json else {}