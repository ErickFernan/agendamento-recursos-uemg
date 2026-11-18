import os
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from loguru import logger
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from app.models import Usuario
from app.schemas.auth_schema import LoginSchema

auth_bp = Blueprint('auth', __name__)
login_schema = LoginSchema()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@auth_bp.route('/login', methods=['POST'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'auth', 'post_login.yml'))
def login():
    """
    Rota de Autenticação. Verifica credenciais e devolve o JWT.
    """
    json_data = request.get_json()
    erros = login_schema.validate(json_data)
    
    if erros:
        logger.warning(f"Tentativa de login com formato inválido: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    email = json_data['email']
    senha_digitada = json_data['senha']

    try:
        usuario = Usuario.query.filter_by(email=email).first()

        # AQUI ACONTECE A MÁGICA: check_password_hash faz o trabalho sujo
        # Se o usuário não existir, ou se a senha moída for diferente, barra o acesso.
        if not usuario or not check_password_hash(usuario.senha_hash, senha_digitada):
            logger.warning(f"Falha de autenticação para o e-mail: {email}")
            return jsonify({"erro": "E-mail ou senha incorretos."}), 401

        # Extrai os nomes de todos os perfis associados a este usuário
        lista_perfis = [perfil.nome for perfil in usuario.perfis]
        # Se não houver nenhum perfil, define 'aluno' por precaução
        if not lista_perfis:
            lista_perfis = ['aluno']
        # Cria o token JWT. O "identity" é a informação principal guardada dentro do token.
        # Vamos converter o ID para string pois é a melhor prática para o identity.
        token_acesso = create_access_token(
            identity=str(usuario.id),
            additional_claims={
                "perfis": lista_perfis,  # Agora passamos uma lista!
                "nome": usuario.nome
            }
        )
        
        logger.info(f"Login bem-sucedido para o usuário: {email} (ID: {usuario.id})")
        
        return jsonify({
            "mensagem": "Login realizado com sucesso!",
            "access_token": token_acesso,
            "usuario": {
                "id": usuario.id,
                "nome": usuario.nome,
                "unidade_id": usuario.unidade_id
            }
        }), 200

    except Exception as e:
        logger.error(f"Erro interno no login: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500
    