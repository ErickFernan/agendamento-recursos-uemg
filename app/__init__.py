import os
from flask import Flask, jsonify, request
from flask_cors import CORS
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

    # Habilita requisições de outros domínios em todas as rotas
    CORS(app)
    
    # Carrega as configurações do arquivo config.py (classe Config) da raiz
    app.config.from_object('config.Config')

    # Força o Flask a não escapar caracteres acentuados no JSON
    app.json.ensure_ascii = False

    # Inicializa as extensões vinculando-as à instância do app atual
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # ==========================================
    # CUSTOMIZAÇÃO DE ERROS DO JWT (TOKEN) E LOGS
    # ==========================================
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        logger.warning(f"401 - Tentativa de acesso sem token JWT válido. Detalhe: {error_string}")
        return jsonify({
            "erro": "Acesso não autorizado.",
            "detalhes": "O Token de acesso está ausente ou o cabeçalho Authorization está incorreto."
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        usuario_id = jwt_payload.get('sub', 'Desconhecido')
        logger.info(f"401 - Token expirado recusado. Usuário ID: {usuario_id}")
        return jsonify({
            "erro": "Token expirado.",
            "detalhes": "Seu tempo de sessão acabou. Por favor, faça login novamente."
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        logger.warning(f"401 - Tentativa de acesso com token JWT adulterado/inválido: {error_string}")
        return jsonify({
            "erro": "Token inválido.",
            "detalhes": "O token fornecido foi adulterado ou não é reconhecido pelo servidor."
        }), 401

    # Configuração do Loguru
    # Cria a pasta 'logs' automaticamente se ela não existir
    try:
        os.makedirs('logs', exist_ok=True)
        # Configura para salvar em arquivo, criando um novo arquivo a cada 10MB
        logger.add("logs/api.log", rotation="10 MB", retention="30 days", level="INFO")
    except Exception:
        pass
    logger.info("Iniciando a API de Agendamentos da UEMG...")

    # ==========================================
    # TRATAMENTO GLOBAL DE ERROS HTTP
    # ==========================================
    @app.errorhandler(404)
    def rota_nao_encontrada(e):
        logger.warning(f"404 - Rota não encontrada: {request.method} {request.path}")
        return jsonify({"erro": "Rota não encontrada. Verifique a URL e tente novamente."}), 404

    @app.errorhandler(405)
    def metodo_nao_permitido(e):
        logger.warning(f"405 - Método {request.method} não permitido na rota: {request.path}")
        return jsonify({"erro": "Método HTTP não permitido para esta rota."}), 405

    @app.errorhandler(500)
    def erro_interno_servidor(e):
        logger.error(f"500 - Erro interno crítico no servidor: {request.path}")
        return jsonify({"erro": "Erro interno no servidor."}), 500

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
        },
        # Adiciona o suporte ao botão "Authorize" no Swagger UI
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Insira o token JWT aqui no formato: Bearer {seu_token}"
            }
        }
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # Contexto da aplicação (importações de rotas e modelos vão aqui)
    with app.app_context():
        # Importaremos os modelos aqui para o Alembic detectá-los nas migrations depois
        from app import models

        from app.routes.unidades_routes import unidades_bp
        from app.routes.usuarios_routes import usuarios_bp
        from app.routes.auth_routes import auth_bp
        from app.routes.recursos_routes import recursos_bp
        from app.routes.categorias_routes import categorias_bp
        from app.routes.agendamentos_routes import agendamentos_bp

        app.register_blueprint(unidades_bp, url_prefix='/api')
        app.register_blueprint(usuarios_bp, url_prefix='/api')
        app.register_blueprint(auth_bp, url_prefix='/api')
        app.register_blueprint(recursos_bp, url_prefix='/api')
        app.register_blueprint(categorias_bp, url_prefix='/api')
        app.register_blueprint(agendamentos_bp, url_prefix='/api')
        
        # Rota de Health Check (Teste rápido de integridade)
        @app.route('/health')
        def health_check():
            """
            Verifica a integridade da API
            ---
            tags:
              - Sistema
            responses:
              200:
                description: API online e operando perfeitamente
            """
            return jsonify({
                "status": "online", 
                "mensagem": "API de Gestão da UEMG operando com sucesso!"
            }), 200

    return app
