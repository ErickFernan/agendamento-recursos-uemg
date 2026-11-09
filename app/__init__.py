from flask import Flask
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

    # Contexto da aplicação (importações de rotas e modelos vão aqui)
    with app.app_context():
        # Importaremos os modelos aqui para o Alembic detectá-los nas migrations depois
        # from app.models import ...
        
        # Rota de Health Check (Teste rápido de integridade)
        @app.route('/health')
        def health_check():
            return {
                "status": "online", 
                "mensagem": "API de Gestão da UEMG operando com sucesso!"
            }, 200

    return app