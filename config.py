import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

class Config:
    """Classe de configuração central da aplicação."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'uma-chave-secreta-bem-forte-e-aleatoria')

    # --- Configuração do Banco de Dados ---
    # Usa a variável de ambiente DATABASE_URL; se não existir, usa um SQLite local.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Configurações de APIs e Serviços Externos ---
    PUBLIC_URL_GUI = os.getenv("PUBLIC_URL_GUI")
    PUBLIC_URL_API = os.getenv("PUBLIC_URL_API", "http://127.0.0.1:8000")
    PROJECT_ID = os.getenv("PROJECT_ID", "transcricao-467718")
    LOCATION = os.getenv("LOCATION", "us-central1")

    # --- Configuração de Pastas ---
    UPLOAD_FOLDER = 'uploads'