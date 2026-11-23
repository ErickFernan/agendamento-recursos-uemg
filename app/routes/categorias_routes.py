import os
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from loguru import logger
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt
from app.models import db, CategoriaRecurso
from app.schemas.categoria_schema import CategoriaRecursoSchema

categorias_bp = Blueprint('categorias', __name__)

categoria_schema = CategoriaRecursoSchema()
categorias_schema = CategoriaRecursoSchema(many=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@categorias_bp.route('/categorias', methods=['POST'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'categorias', 'post_categoria.yml'))
@jwt_required()
def criar_categoria():
    """
    Cria uma nova categoria de recurso.
    Autorização: Apenas Administradores.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de criar categoria. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erro": "Corpo da requisição JSON é obrigatório."}), 400

    erros = categoria_schema.validate(json_data)
    if erros:
        logger.warning(f"Tentativa de criar categoria com dados inválidos: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    try:
        nova_categoria = CategoriaRecurso(
            nome=json_data['nome'],
            descricao=json_data.get('descricao')
        )
        db.session.add(nova_categoria)
        db.session.commit()

        logger.info(f"Categoria '{nova_categoria.nome}' criada com sucesso!")
        return jsonify({
            "mensagem": "Categoria criada com sucesso!",
            "categoria": categoria_schema.dump(nova_categoria)
        }), 201

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade ao tentar criar categoria: {json_data.get('nome')}")
        return jsonify({"erro": "Já existe uma categoria com este nome."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao criar categoria: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@categorias_bp.route('/categorias', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'categorias', 'get_categorias.yml'))
@jwt_required()
def listar_categorias():
    """
    Lista todas as categorias de recursos cadastradas.
    Autorização: Qualquer usuário autenticado.
    """
    try:
        categorias = db.session.scalars(db.select(CategoriaRecurso)).all()
        resultado = categorias_schema.dump(categorias)
        logger.info(f"Listagem de categorias solicitada. Total retornado: {len(categorias)}")
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao listar categorias: {str(e)}")
        return jsonify({"erro": "Erro ao buscar categorias.", "detalhes": str(e)}), 500


@categorias_bp.route('/categorias/<int:id>', methods=['GET'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'categorias', 'get_categoria_by_id.yml'))
@jwt_required()
def buscar_categoria_por_id(id):
    """
    Busca uma categoria específica pelo ID.
    Autorização: Qualquer usuário autenticado.
    """
    try:
        categoria = db.session.get(CategoriaRecurso, id)
        if not categoria:
            logger.warning(f"Busca por categoria inexistente. ID: {id}")
            return jsonify({"erro": "Categoria não encontrada."}), 404

        return jsonify(categoria_schema.dump(categoria)), 200
    except Exception as e:
        logger.error(f"Erro interno crítico ao buscar categoria ID {id}: {str(e)}")
        return jsonify({"erro": "Erro ao buscar categoria.", "detalhes": str(e)}), 500


@categorias_bp.route('/categorias/<int:id>', methods=['PUT'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'categorias', 'put_categoria.yml'))
@jwt_required()
def atualizar_categoria_total(id):
    """
    Atualiza todos os campos de uma categoria existente.
    Autorização: Apenas Administradores.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de PUT na categoria {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    categoria = db.session.get(CategoriaRecurso, id)
    if not categoria:
        logger.warning(f"Tentativa de atualização (PUT) em categoria inexistente. ID: {id}")
        return jsonify({"erro": "Categoria não encontrada."}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erro": "Corpo da requisição JSON é obrigatório."}), 400

    erros = categoria_schema.validate(json_data)
    if erros:
        logger.warning(f"Dados inválidos recebidos no PUT para a categoria {id}: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    try:
        nome_antigo = categoria.nome
        categoria.nome = json_data['nome']
        categoria.descricao = json_data.get('descricao')

        db.session.commit()
        logger.info(f"Categoria ID {id} atualizada via PUT. ('{nome_antigo}' -> '{categoria.nome}')")
        return jsonify({
            "mensagem": "Categoria atualizada com sucesso!",
            "categoria": categoria_schema.dump(categoria)
        }), 200

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade ao atualizar (PUT) a categoria {id}")
        return jsonify({"erro": "Já existe uma categoria com este nome."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PUT da categoria {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@categorias_bp.route('/categorias/<int:id>', methods=['PATCH'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'categorias', 'patch_categoria.yml'))
@jwt_required()
def atualizar_categoria_parcial(id):
    """
    Atualiza parcialmente os campos de uma categoria existente.
    Autorização: Apenas Administradores.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de PATCH na categoria {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    categoria = db.session.get(CategoriaRecurso, id)
    if not categoria:
        logger.warning(f"Tentativa de atualização (PATCH) em categoria inexistente. ID: {id}")
        return jsonify({"erro": "Categoria não encontrada."}), 404

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erro": "Corpo da requisição JSON é obrigatório."}), 400

    erros = categoria_schema.validate(json_data, partial=True)
    if erros:
        logger.warning(f"Dados inválidos recebidos no PATCH para a categoria {id}: {erros}")
        return jsonify({"erro": "Dados inválidos", "detalhes": erros}), 400

    try:
        if 'nome' in json_data:
            categoria.nome = json_data['nome']
        if 'descricao' in json_data:
            categoria.descricao = json_data['descricao']

        db.session.commit()
        logger.info(f"Categoria ID {id} atualizada parcialmente via PATCH.")
        return jsonify({
            "mensagem": "Categoria atualizada parcialmente com sucesso!",
            "categoria": categoria_schema.dump(categoria)
        }), 200

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Conflito de integridade ao atualizar (PATCH) a categoria {id}")
        return jsonify({"erro": "Já existe uma categoria com este nome."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico no PATCH da categoria {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500


@categorias_bp.route('/categorias/<int:id>', methods=['DELETE'])
@swag_from(os.path.join(BASE_DIR, 'docs', 'categorias', 'delete_categoria.yml'))
@jwt_required()
def deletar_categoria(id):
    """
    Remove uma categoria do sistema.
    Autorização: Apenas Administradores.
    """
    claims = get_jwt()
    if 'admin' not in claims.get('perfis', []):
        logger.warning(f"Tentativa negada de DELETE na categoria {id}. ID Solicitante: {claims.get('sub')}")
        return jsonify({"erro": "Acesso negado. Requer privilégios de administrador."}), 403

    categoria = db.session.get(CategoriaRecurso, id)
    if not categoria:
        logger.warning(f"Tentativa de exclusão (DELETE) em categoria inexistente. ID: {id}")
        return jsonify({"erro": "Categoria não encontrada."}), 404

    try:
        nome_deletado = categoria.nome
        db.session.delete(categoria)
        db.session.commit()
        logger.info(f"Categoria '{nome_deletado}' (ID {id}) deletada com sucesso.")
        return jsonify({"mensagem": "Categoria deletada com sucesso!"}), 200

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Tentativa de deletar categoria com recursos vinculados barrada. ID: {id}")
        return jsonify({"erro": "Não é possível deletar esta categoria pois existem recursos vinculados a ela."}), 409
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro interno crítico ao deletar a categoria {id}: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor.", "detalhes": str(e)}), 500
    