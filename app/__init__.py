import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

# Inicializa as extensões sem vincular a uma aplicação específica ainda
db = SQLAlchemy()

def create_app(config_class=Config):
    """
    Cria e configura a aplicação Flask.
    Este padrão é conhecido como 'Application Factory'.
    """
    app = Flask(
        __name__,
        template_folder='../templates', # Aponta para a pasta de templates na raiz
        static_folder='../static'       # Aponta para a pasta static na raiz
    )

    # Carrega a configuração a partir do objeto importado
    app.config.from_object(config_class)
    
    # Cria a pasta de upload se ela não existir
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Habilita o CORS para toda a aplicação
    #CORS(app)

    # Vincula a instância do banco de dados com a aplicação
    db.init_app(app)

    # Importa e registra os blueprints (nossas rotas)
    from . import routes
    app.register_blueprint(routes.bp)
    
    with app.app_context():
        # Cria as tabelas do banco de dados se não existirem
        db.create_all()

    return app