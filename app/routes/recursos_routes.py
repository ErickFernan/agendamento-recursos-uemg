import os
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from loguru import logger
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt

from app.models import db, Recurso, Unidade, CategoriaRecurso
from app.schemas.recurso_schema import RecursoSchema

recursos_bp = Blueprint('recursos', __name__)

# ==========================================
# INSTÂNCIAS DOS SCHEMAS (Padrão Oficial)
# ==========================================
recurso_schema = RecursoSchema(session=db.session)
recursos_schema = RecursoSchema(many=True)

# Descobre o caminho exato da pasta 'app' dinamicamente
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ==========================================
# ROTAS CRUD
# ==========================================

@recursos_bp.route('/recursos', methods=['POST'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'recursos', 'post_recurso.yml'))
@jwt_required()
def criar_recurso():
    """
    Cria um novo recurso (sala, laboratório, quadra, equipamento).
    Autorização: Apenas Administradores.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de criar recurso. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erro": "Corpo da requisição JSON é obrigatório."}), 400

    erros = recurso_schema.validate(json_data)
    if erros:
        logger.warning(f"Tentativa de criar recurso com dados inválidos: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    # Valida integridade das chaves estrangeiras antes de inserir
    unidade = db.session.get(Unidade,json_data['unidade_id'])
    if not unidade:
        return jsonify({"erro": "A unidade informada não existe."}), 404

    categoria = db.session.get(CategoriaRecurso,json_data['categoria_id'])
    if not categoria:
        return jsonify({"erro": "A categoria informada não existe."}), 404

    try:
        novo_recurso = Recurso(
            nome=json_data['nome'],
            capacidade=json_data['capacidade'],
            unidade_id=json_data['unidade_id'],
            categoria_id=json_data['categoria_id']
        )

        db.session.add(novo_recurso)
        db.session.commit()

        logger.info(f"Recurso '{novo_recurso.nome}' (ID {novo_recurso.id}) criado com sucesso!")
        return jsonify({
            "mensagem": "Recurso criado com sucesso!",
            "recurso": recurso_schema.dump(novo_recurso)
        }), 201

    except IntegrityError:
        db.session.rollback()
        logger.warning(
            f"Conflito de integridade: recurso '{json_data.get('nome')}' já existe na unidade {json_data.get('unidade_id')}."
        )
        return jsonify({"erro": "Já existe um recurso com este nome nesta unidade."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao criar recurso: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@recursos_bp.route('/recursos', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'recursos', 'get_recursos.yml'))
@jwt_required()
def listar_recursos():
    """
    Lista todos os recursos cadastrados.
    Suporta filtros opcionais via query params: ?unidade_id=1&categoria_id=2
    Autorização: Qualquer usuário autenticado.
    """
    try:
        query = Recurso.query

        unidade_id = request.args.get('unidade_id', type=int)
        categoria_id = request.args.get('categoria_id', type=int)

        if unidade_id is not None:
            query = query.filter_by(unidade_id=unidade_id)
        if categoria_id is not None:
            query = query.filter_by(categoria_id=categoria_id)

        recursos = query.all()
        resultado = recursos_schema.dump(recursos)

        logger.info(f"Listagem de recursos solicitada. Total retornado: {len(recursos)}")
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao listar recursos: {str(e)}")
        return jsonify({"erro": "Erro ao buscar recursos.", "detalhes": str(e)}), 500


@recursos_bp.route('/recursos/<int:id>', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'recursos', 'get_recurso_by_id.yml'))
@jwt_required()
def buscar_recurso_por_id(id):
    """
    Retorna os detalhes de um recurso específico pelo ID.
    Autorização: Qualquer usuário autenticado.
    """
    try:
        recurso = db.session.get(Recurso, id)
        if not recurso:
            logger.warning(f"Busca por recurso inexistente. ID: {id}")
            return jsonify({"erro": "Recurso não encontrado."}), 404

        return jsonify(recurso_schema.dump(recurso)), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao buscar recurso ID {id}: {str(e)}")
        return jsonify({"erro": "Erro ao buscar recurso.", "detalhes": str(e)}), 500


@recursos_bp.route('/recursos/<int:id>', methods=['PUT'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'recursos', 'put_recurso.yml'))
@jwt_required()
def atualizar_recurso_total(id):
    """
    Atualiza todos os campos de um recurso existente.
    Autorização: Apenas Administradores.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de PUT no recurso {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    recurso = db.session.get(Recurso, id)
    if not recurso:
        logger.warning(f"Tentativa de atualização (PUT) em recurso inexistente. ID: {id}")
        return jsonify({"erro": "Recurso não encontrado."}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erro": "Corpo da requisição JSON é obrigatório."}), 400

    erros = recurso_schema.validate(json_data)
    if erros:
        logger.warning(f"Dados inválidos recebidos no PUT para o recurso {id}: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    if not db.session.get(Unidade,json_data['unidade_id']):
        return jsonify({"erro": "A unidade informada não existe."}), 404

    if not db.session.get(CategoriaRecurso,json_data['categoria_id']):
        return jsonify({"erro": "A categoria informada não existe."}), 404

    try:
        recurso.nome = json_data['nome']
        recurso.capacidade = json_data['capacidade']
        recurso.unidade_id = json_data['unidade_id']
        recurso.categoria_id = json_data['categoria_id']

        db.session.commit()
        logger.info(f"Recurso ID {id} atualizado com sucesso via PUT.")
        return jsonify({
            "mensagem": "Recurso atualizado com sucesso!",
            "recurso": recurso_schema.dump(recurso)
        }), 200

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade no PUT do recurso {id}: nome duplicado na unidade.")
        return jsonify({"erro": "Já existe um recurso com este nome nesta unidade."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PUT do recurso {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@recursos_bp.route('/recursos/<int:id>', methods=['PATCH'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'recursos', 'patch_recurso.yml'))
@jwt_required()
def atualizar_recurso_parcial(id):
    """
    Atualiza campos específicos de um recurso existente.
    Autorização: Apenas Administradores.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de PATCH no recurso {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    recurso = db.session.get(Recurso, id)
    if not recurso:
        logger.warning(f"Tentativa de atualização parcial (PATCH) em recurso inexistente. ID: {id}")
        return jsonify({"erro": "Recurso não encontrado."}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erro": "Corpo da requisição JSON é obrigatório."}), 400

    erros = recurso_schema.validate(json_data, partial=True)
    if erros:
        logger.warning(f"Dados inválidos recebidos no PATCH para o recurso {id}: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    if 'unidade_id' in json_data and not db.session.get(Unidade,json_data['unidade_id']):
        return jsonify({"erro": "A nova unidade informada não existe."}), 404

    if 'categoria_id' in json_data and not db.session.get(CategoriaRecurso,json_data['categoria_id']):
        return jsonify({"erro": "A nova categoria informada não existe."}), 404

    try:
        if 'nome' in json_data:
            recurso.nome = json_data['nome']
        if 'capacidade' in json_data:
            recurso.capacidade = json_data['capacidade']
        if 'unidade_id' in json_data:
            recurso.unidade_id = json_data['unidade_id']
        if 'categoria_id' in json_data:
            recurso.categoria_id = json_data['categoria_id']

        db.session.commit()
        logger.info(f"Recurso ID {id} atualizado parcialmente com sucesso via PATCH.")
        return jsonify({
            "mensagem": "Recurso atualizado com sucesso!",
            "recurso": recurso_schema.dump(recurso)
        }), 200

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade no PATCH do recurso {id}: nome duplicado na unidade.")
        return jsonify({"erro": "Já existe um recurso com este nome nesta unidade."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PATCH do recurso {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@recursos_bp.route('/recursos/<int:id>', methods=['DELETE'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'recursos', 'delete_recurso.yml'))
@jwt_required()
def deletar_recurso(id):
    """
    Remove um recurso do sistema. Falhará caso existam agendamentos vinculados.
    Autorização: Apenas Administradores.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de deletar o recurso {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    recurso = db.session.get(Recurso, id)
    if not recurso:
        logger.warning(f"Tentativa de exclusão (DELETE) em recurso inexistente. ID: {id}")
        return jsonify({"erro": "Recurso não encontrado."}), 404

    try:
        nome_deletado = recurso.nome
        db.session.delete(recurso)
        db.session.commit()
        logger.info(f"Recurso '{nome_deletado}' (ID {id}) deletado com sucesso.")
        return jsonify({"mensagem": "Recurso deletado com sucesso!"}), 200
    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Tentativa de deletar recurso com agendamentos vinculados. ID: {id}")
        return jsonify({"erro": "Não é possível deletar este recurso pois existem agendamentos vinculados a ele."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao tentar deletar o recurso {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500

    