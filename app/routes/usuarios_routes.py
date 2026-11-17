import os
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from loguru import logger
from werkzeug.security import generate_password_hash
from app.models import db, Usuario, Unidade
from app.schemas.usuario_schema import UsuarioSchema
from sqlalchemy.exc import IntegrityError

usuarios_bp = Blueprint('usuarios', __name__)

# ==========================================
# INSTÂNCIAS DOS SCHEMAS (Padrão Oficial)
# ==========================================
# 1. Padrão para POST, GET e PATCH (Exige tudo ou permite validação parcial)
usuario_schema = UsuarioSchema(session=db.session) 

# 2. Padrão para o PUT (Ignora completamente a senha, exige o resto)
# Semanticamente, a senha não faz parte de uma atualização cadastral padrão
usuario_schema_put = UsuarioSchema(session=db.session, exclude=("senha",))

# Descobre o caminho exato da pasta 'app' dinamicamente
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# ROTAS CRUD
# ==========================================

@usuarios_bp.route('/usuarios', methods=['POST'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'post_usuario.yml'))
def criar_usuario():
    """
    Cria um novo usuário. A senha recebida em texto plano será convertida 
    em um hash seguro antes de ser salva no banco de dados.
    """
    json_data = request.get_json()
    
    # Valida os dados usando a instância padrão do schema
    erros = usuario_schema.validate(json_data)
    if erros:
        logger.warning(f"Tentativa de criar usuário com dados inválidos: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400
    
    # Valida se a unidade vinculada realmente existe no banco
    unidade = Unidade.query.get(json_data['unidade_id'])
    if not unidade:
        return jsonify({"erro": "A unidade informada não existe."}), 404

    try:
        # Gerando o Hash da senha
        hash_seguro = generate_password_hash(json_data['senha'])
        
        novo_usuario = Usuario(
            nome=json_data['nome'],
            email=json_data['email'],
            senha_hash=hash_seguro, # Salvamos o hash, NUNCA a senha pura!
            unidade_id=json_data['unidade_id']
        )
        
        db.session.add(novo_usuario)
        db.session.commit()

        logger.info(f"Usuário '{novo_usuario.email}' criado com sucesso!")
        
        # Retorna os dados criados (o schema ocultará o hash da senha automaticamente)
        return jsonify({
            "mensagem": "Usuário criado com sucesso!", 
            "usuario": usuario_schema.dump(novo_usuario)
        }), 201

    except IntegrityError:
        # Erro de banco de dados, geralmente causado por violação da restrição UNIQUE no e-mail
        db.session.rollback()
        logger.warning(f"Conflito de integridade: e-mail {json_data.get('email')} já cadastrado.")
        return jsonify({"erro": "Este e-mail já está em uso por outro usuário."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao criar usuário: {str(e)}") 
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500
    

@usuarios_bp.route('/usuarios', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'get_usuarios.yml'))
def listar_usuarios():
    """
    Retorna uma lista com todos os usuários.
    """
    try:
        usuarios = Usuario.query.all()
        # O usuario_schema.dump já vai esconder automaticamente o senha_hash!
        resultado = UsuarioSchema(many=True).dump(usuarios)
        logger.info(f"Listagem de usuários solicitada. Total retornado: {len(usuarios)}")
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao listar usuários: {str(e)}")
        return jsonify({"erro": "Erro ao buscar usuários.", "detalhes": str(e)}), 500


@usuarios_bp.route('/usuarios/<int:id>', methods=['PUT'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'put_usuario.yml'))
def atualizar_usuario_total(id):
    """
    Atualiza todos os dados cadastrais do usuário (substitui o recurso inteiro).
    A senha foi excluída da validação desta rota por motivos de segurança e semântica.
    """
    usuario = Usuario.query.get(id)
    if not usuario:
        logger.warning(f"Tentativa de atualização (PUT) em usuário inexistente. ID: {id}")
        return jsonify({"erro": "Usuário não encontrado."}), 404

    json_data = request.get_json()
    
    # Usa a instância específica para PUT, que ignora a presença do campo 'senha' no JSON
    erros = usuario_schema_put.validate(json_data)
    
    if erros:
        logger.warning(f"Dados inválidos recebidos no PUT para o usuário {id}: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    # Verifica se a nova unidade informada no JSON existe no banco
    if 'unidade_id' in json_data:
        unidade = Unidade.query.get(json_data['unidade_id'])
        if not unidade:
             return jsonify({"erro": "A unidade informada não existe."}), 404

    try:
        email_antigo = usuario.email
        
        # Atualiza os dados cadastrais
        usuario.nome = json_data['nome']
        usuario.email = json_data['email']
        usuario.unidade_id = json_data['unidade_id']
        
        # Opcional: Se a equipe desejar permitir atualização de senha no PUT também
        # (não é recomendado semanticamente, mas está mapeado caso necessário)
        # if 'senha' in json_data:
        #      usuario.senha_hash = generate_password_hash(json_data['senha'])
        
        db.session.commit()
        logger.info(f"Usuário ID {id} atualizado com sucesso via PUT. ('{email_antigo}' -> '{usuario.email}')")
        return jsonify({"mensagem": "Usuário atualizado com sucesso!", "usuario": usuario_schema.dump(usuario)}), 200
    
    except IntegrityError:
        # Disparado caso o novo e-mail já pertença a outro usuário
        db.session.rollback()
        logger.warning(f"Conflito de integridade: e-mail {json_data.get('email')} já em uso (PUT usuário {id}).")
        return jsonify({"erro": "Este e-mail já está em uso por outro usuário."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PUT do usuário {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@usuarios_bp.route('/usuarios/<int:id>', methods=['PATCH'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'patch_usuario.yml'))
def atualizar_usuario_parcial(id):
    """
    Atualiza dados parciais de um usuário. Ideal para alterar campos individuais.
    """
    usuario = Usuario.query.get(id)
    if not usuario:
         logger.warning(f"Tentativa de atualização parcial (PATCH) em usuário inexistente. ID: {id}")
         return jsonify({"erro": "Usuário não encontrado."}), 404

    json_data = request.get_json()
    
    # Usa a instância padrão, mas diz ao Marshmallow que a validação é parcial
    # (ou seja, campos não enviados não gerarão erro)
    erros = usuario_schema.validate(json_data, partial=True)
    
    if erros:
         logger.warning(f"Dados inválidos recebidos no PATCH para o usuário {id}: {erros}")
         return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    if 'unidade_id' in json_data:
         unidade = Unidade.query.get(json_data['unidade_id'])
         if not unidade:
              return jsonify({"erro": "A nova unidade informada não existe."}), 404

    try:
        # Atualiza apenas os campos presentes no JSON
        if 'nome' in json_data: usuario.nome = json_data['nome']
        if 'email' in json_data: usuario.email = json_data['email']
        if 'unidade_id' in json_data: usuario.unidade_id = json_data['unidade_id']
        
        # Se uma nova senha for enviada, ela também será convertida em hash
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
def deletar_usuario(id):
    """
    Remove um usuário do sistema. Falhará caso o usuário tenha agendamentos vinculados.
    """
    usuario = Usuario.query.get(id)
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
        # O banco bloqueia a exclusão se existirem registros dependentes (ex: agendamentos)
        db.session.rollback()
        logger.warning(f"Tentativa de deletar usuário com agendamentos vinculados. ID: {id}")
        return jsonify({"erro": "Não é possível deletar este usuário pois existem agendamentos vinculados a ele."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao tentar deletar o usuário {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@usuarios_bp.route('/usuarios/<int:id>/resetar-senha', methods=['PATCH'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'usuarios', 'resetar_senha.yml'))
def resetar_senha(id):
    """
    Endpoint especializado para redefinição de senhas (ex: fluxo de 'Esqueci minha senha' 
    ou reset administrativo).
    """
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    
    json_data = request.get_json()
    nova_senha = json_data.get('nova_senha')

    # Validação manual simples, pois não estamos usando o schema completo aqui
    if not nova_senha or len(nova_senha) < 6:
        return jsonify({"erro": "A nova senha deve ter no mínimo 6 caracteres."}), 400

    try:
        # TODO: Implementar lógica de negócio futura.
        # Exemplos: Exigir um token enviado por e-mail, verificar se o usuário
        # que está fazendo a requisição tem permissão de Admin, etc.
        
        usuario.senha_hash = generate_password_hash(nova_senha)
        db.session.commit()
        
        logger.info(f"Senha do usuário ID {id} redefinida com sucesso (via rota de reset).")
        return jsonify({"mensagem": "Senha atualizada com sucesso!"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao resetar senha do usuário {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500
    