import os
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from loguru import logger
from werkzeug.security import generate_password_hash
from app.models import db, Usuario, Unidade
from app.schemas.usuario_schema import UsuarioSchema
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt

usuarios_bp = Blueprint('usuarios', __name__)

# ==========================================
# INSTÂNCIAS DOS SCHEMAS
# ==========================================
usuario_schema = UsuarioSchema(session=db.session) 
usuario_schema_put = UsuarioSchema(session=db.session, exclude=("senha",))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# ROTAS CRUD
# ==========================================

@usuarios_bp.route('/usuarios', methods=['POST'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'post_usuario.yml'))
@jwt_required()
def criar_usuario():
    """
    Cria um novo usuário.
    Autorização: Apenas Administradores podem criar novos usuários.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de criar usuário. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    json_data = request.get_json()
    
    erros = usuario_schema.validate(json_data)
    if erros:
        logger.warning(f"Tentativa de criar usuário com dados inválidos: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400
    
    unidade = db.session.get(Unidade,json_data['unidade_id'])
    if not unidade:
        return jsonify({"erro": "A unidade informada não existe."}), 404

    try:
        hash_seguro = generate_password_hash(json_data['senha'])
        
        novo_usuario = Usuario(
            nome=json_data['nome'],
            email=json_data['email'],
            senha_hash=hash_seguro,
            unidade_id=json_data['unidade_id']
        )
        
        db.session.add(novo_usuario)
        db.session.commit()

        logger.info(f"Usuário '{novo_usuario.email}' criado com sucesso!")
        
        return jsonify({
            "mensagem": "Usuário criado com sucesso!", 
            "usuario": usuario_schema.dump(novo_usuario)
        }), 201

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade: e-mail {json_data.get('email')} já cadastrado.")
        return jsonify({"erro": "Este e-mail já está em uso por outro usuário."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao criar usuário: {str(e)}") 
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500
    

@usuarios_bp.route('/usuarios', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'get_usuarios.yml'))
@jwt_required()
def listar_usuarios():
    """
    Retorna uma lista com todos os usuários.
    Autorização: Apenas Administradores podem visualizar a lista completa de usuários.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de listar usuários. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    try:
        usuarios = Usuario.query.all()
        resultado = UsuarioSchema(many=True).dump(usuarios)
        logger.info(f"Listagem de usuários solicitada. Total retornado: {len(usuarios)}")
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao listar usuários: {str(e)}")
        return jsonify({"erro": "Erro ao buscar usuários.", "detalhes": str(e)}), 500

@usuarios_bp.route('/usuarios/<int:id>', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'get_usuario_by_id.yml'))
@jwt_required()
def buscar_usuario_por_id(id):
    """
    Retorna os detalhes de um usuário específico pelo ID.
    Autorização: Administradores ou o próprio dono do perfil.
    """
    claims = get_jwt()
    is_admin = 'admin' in claims.get('perfis', [])
    is_owner = str(claims.get('sub')) == str(id)

    if not is_admin and not is_owner:
        logger.warning(
            f"Tentativa negada de acessar perfil do usuário {id}. ID Solicitante: {claims.get('sub')}"
        )
        return jsonify({"erro": "Acesso negado. Você só pode visualizar o seu próprio perfil."}), 403

    try:
        usuario = db.session.get(Usuario, id)
        if not usuario:
            logger.warning(f"Busca por usuário inexistente. ID: {id}")
            return jsonify({"erro": "Usuário não encontrado."}), 404

        return jsonify(usuario_schema.dump(usuario)), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao buscar usuário ID {id}: {str(e)}")
        return jsonify({"erro": "Erro ao buscar usuário.", "detalhes": str(e)}), 500


@usuarios_bp.route('/usuarios/<int:id>', methods=['PUT'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'put_usuario.yml'))
@jwt_required()
def atualizar_usuario_total(id):
    """
    Atualiza todos os dados cadastrais do usuário.
    Autorização: O próprio usuário pode se atualizar, ou um Administrador.
    """
    claims = get_jwt()
    is_admin = 'admin' in claims.get('perfis', [])
    is_owner = str(id) == claims.get('sub')

    if not is_admin and not is_owner:
        logger.warning(f"Tentativa negada de PUT no usuário {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Você só pode alterar seu próprio cadastro."}), 403

    usuario = db.session.get(Usuario, id)
    if not usuario:
        logger.warning(f"Tentativa de atualização (PUT) em usuário inexistente. ID: {id}")
        return jsonify({"erro": "Usuário não encontrado."}), 404

    json_data = request.get_json()
    
    erros = usuario_schema_put.validate(json_data)
    if erros:
        logger.warning(f"Dados inválidos recebidos no PUT para o usuário {id}: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    if 'unidade_id' in json_data:
        unidade = db.session.get(Unidade,json_data['unidade_id'])
        if not unidade:
             return jsonify({"erro": "A unidade informada não existe."}), 404

    try:
        email_antigo = usuario.email
        
        usuario.nome = json_data['nome']
        usuario.email = json_data['email']
        usuario.unidade_id = json_data['unidade_id']
        
        db.session.commit()
        logger.info(f"Usuário ID {id} atualizado com sucesso via PUT. ('{email_antigo}' -> '{usuario.email}')")
        return jsonify({"mensagem": "Usuário atualizado com sucesso!", "usuario": usuario_schema.dump(usuario)}), 200
    
    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade: e-mail {json_data.get('email')} já em uso (PUT usuário {id}).")
        return jsonify({"erro": "Este e-mail já está em uso por outro usuário."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PUT do usuário {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@usuarios_bp.route('/usuarios/<int:id>', methods=['PATCH'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'patch_usuario.yml'))
@jwt_required()
def atualizar_usuario_parcial(id):
    """
    Atualiza dados parciais de um usuário.
    Autorização: O próprio usuário pode se atualizar, ou um Administrador.
    """
    claims = get_jwt()
    is_admin = 'admin' in claims.get('perfis', [])
    is_owner = str(id) == claims.get('sub')

    if not is_admin and not is_owner:
        logger.warning(f"Tentativa negada de PATCH no usuário {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Você só pode alterar seu próprio cadastro."}), 403

    usuario = db.session.get(Usuario, id)
    if not usuario:
         logger.warning(f"Tentativa de atualização parcial (PATCH) em usuário inexistente. ID: {id}")
         return jsonify({"erro": "Usuário não encontrado."}), 404

    json_data = request.get_json()
    
    erros = usuario_schema.validate(json_data, partial=True)
    if erros:
         logger.warning(f"Dados inválidos recebidos no PATCH para o usuário {id}: {erros}")
         return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    if 'unidade_id' in json_data:
         unidade = db.session.get(Unidade,json_data['unidade_id'])
         if not unidade:
              return jsonify({"erro": "A nova unidade informada não existe."}), 404

    try:
        if 'nome' in json_data: usuario.nome = json_data['nome']
        if 'email' in json_data: usuario.email = json_data['email']
        if 'unidade_id' in json_data: usuario.unidade_id = json_data['unidade_id']
        
        if 'senha' in json_data:
             usuario.senha_hash = generate_password_hash(json_data['senha'])
             logger.info(f"Senha do usuário ID {id} atualizada via PATCH.")
             
        db.session.commit()
        logger.info(f"Usuário ID {id} atualizado parcialmente com sucesso via PATCH.")
        return jsonify({"mensagem": "Usuário atualizado com sucesso!", "usuario": usuario_schema.dump(usuario)}), 200
        
    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade: e-mail {json_data.get('email')} já em uso (PATCH usuário {id}).")
        return jsonify({"erro": "Este e-mail já está em uso por outro usuário."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PATCH do usuário {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@usuarios_bp.route('/usuarios/<int:id>', methods=['DELETE'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'delete_usuario.yml'))
@jwt_required()
def deletar_usuario(id):
    """
    Remove um usuário do sistema.
    Autorização: Apenas Administradores podem deletar usuários.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de deletar o usuário {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    usuario = db.session.get(Usuario, id)
    if not usuario:
        logger.warning(f"Tentativa de exclusão (DELETE) em usuário inexistente. ID: {id}")
        return jsonify({"erro": "Usuário não encontrado."}), 404

    try:
        email_deletado = usuario.email
        db.session.delete(usuario)
        db.session.commit()
        logger.info(f"Usuário '{email_deletado}' (ID {id}) deletado com sucesso.")
        return jsonify({"mensagem": "Usuário deletado com sucesso!"}), 200
    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Tentativa de deletar usuário com agendamentos vinculados. ID: {id}")
        return jsonify({"erro": "Não é possível deletar este usuário pois existem agendamentos vinculados a ele."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao tentar deletar o usuário {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@usuarios_bp.route('/usuarios/<int:id>/resetar-senha', methods=['PATCH'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'resetar_senha.yml'))
@jwt_required()
def resetar_senha(id):
    """
    Endpoint especializado para redefinição de senhas.
    Autorização: Apenas Administradores podem forçar o reset de senha de outros usuários.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de resetar senha do usuário {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Apenas administradores podem redefinir senhas."}), 403

    usuario = db.session.get(Usuario, id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    
    json_data = request.get_json()
    nova_senha = json_data.get('nova_senha')

    if not nova_senha or len(nova_senha) < 6:
        return jsonify({"erro": "A nova senha deve ter no mínimo 6 caracteres."}), 400

    try:
        usuario.senha_hash = generate_password_hash(nova_senha)
        db.session.commit()
        
        logger.info(f"Senha do usuário ID {id} redefinida com sucesso por um admin.")
        return jsonify({"mensagem": "Senha atualizada com sucesso!"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao resetar senha do usuário {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500
    