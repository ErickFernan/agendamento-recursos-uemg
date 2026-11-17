import os
from flask import Flask
from flasgger import Swagger
from loguru import logger
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# Instanciando as extensões globalmente (mas sem vinculá-las ao app ainda)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    # Cria a instância principal do Flask
    app = Flask(__name__)
    
    # Carrega as configurações do arquivo config.py (classe Config) da raiz
    app.config.from_object('config.Config')

    # Força o Flask a não escapar caracteres acentuados no JSON
    app.json.ensure_ascii = False

    # Inicializa as extensões vinculando-as à instância do app atual
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Configuração do Loguru
    # Cria a pasta 'logs' automaticamente se ela não existir
    os.makedirs('logs', exist_ok=True)
    
    # Configura para salvar em arquivo, criando um novo arquivo a cada 10MB
    logger.add("logs/api.log", rotation="10 MB", retention="30 days", level="INFO")
    logger.info("Iniciando a API de Agendamentos da UEMG...")

    # Configuração do Swagger
    swagger_config = {
        "headers": [],
        "specs": [{"endpoint": 'apispec', "route": '/apispec.json', "rule_filter": lambda rule: True, "model_filter": lambda tag: True}],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }
    
    swagger_template = {
        "info": {
            "title": "API de Agendamento UEMG",
            "description": "Documentação interativa da API de recursos e agendamentos.",
            "version": "1.0.0"
        }
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # Contexto da aplicação (importações de rotas e modelos vão aqui)
    with app.app_context():
        # Importaremos os modelos aqui para o Alembic detectá-los nas migrations depois
        from app import models

        from app.routes.unidades_routes import unidades_bp
        app.register_blueprint(unidades_bp, url_prefix='/api')
        
        # Rota de Health Check (Teste rápido de integridade)
        @app.route('/health')
        def health_check():
            return {
                "status": "online", 
                "mensagem": "API de Gestão da UEMG operando com sucesso!"
            }, 200

    return app